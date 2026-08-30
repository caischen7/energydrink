#!/usr/bin/env python3
"""Price response and revenue forecasting on the PDI cluster panel.

Reads data/bq/derived/price_panel.csv (built by build_price_panel.py) and,
when present, Google Trends series merged into public/data/flavor_explorer.json.

WHAT THIS ANSWERS, AND WHAT IT CANNOT
-------------------------------------
It answers: within a cluster, when the fixed-weight price index moves, what
happens to volume and revenue the same month and the months after - and does
knowing price improve an out-of-sample revenue forecast over not knowing it.

It does NOT answer "what should we charge". That is a causal question about a
price we would set, and this is observational convenience-panel data in which
price is chosen by retailers in response to demand. The elasticities below are
descriptive co-movements with controls, not the causal object a pricing
decision needs. Anywhere the output says "elasticity" it means that, and the
verdict says so in words.

THE FOUR THINGS THAT MAKE THIS HONEST
-------------------------------------
0. DIVISION BIAS COMES FIRST. Price is revenue/units, so a naive volume-on-price
   regression puts the same measurement on both sides with opposite signs and
   returns a negative number even when the truth is zero. Every specification
   below except the cross-half one is contaminated by it and is reported only as
   the contrast. The cross-half specification pairs price from one store-half
   with quantity from the other, so their errors are independent and the
   mechanical term cancels. Together the two BRACKET the co-movement: naive
   inflated away from zero, cross-half attenuated toward it.

1. PRICE SERIES. Models run on `price_index`, the fixed-weight Laspeyres series,
   not on `price_unitvalue`. A unit-value series moves with mix - a shift from
   12oz to 24oz reads as a price rise with nothing repriced - and regressing
   volume on it manufactures a spurious POSITIVE elasticity, because months with
   more large-format sales look both dearer and bigger. Both series are loaded
   and their divergence is reported, because that gap is the size of the trap.

2. THE ENDOGENEITY IS NAMED, NOT HIDDEN. Retailers cut price into strength and
   promote in season, so OLS of log volume on log price is biased toward zero or
   positive. Three specifications are reported side by side rather than one
   "answer": raw, within-cluster (cluster fixed effects absorb the level
   differences between a $2 12oz cluster and a $4 24oz one), and within-cluster
   plus month-of-year and distribution controls. If the coefficient swings
   across those three, that swing IS the finding.

3. VALIDATION IS EXPANDING-WINDOW, NEVER RANDOM. Train on everything up to month
   T, predict T+h, walk forward. Random k-fold on a panel lets the model learn
   2024 to predict 2022, which for a forecasting claim is leakage wearing a
   lab coat.

4. BASELINES DECIDE. Three, all trivial, all hard to beat on 84 monthly points:
       persistence     next log-revenue = this one
       drift           persistence plus this cluster's mean historical change
       seasonal-naive  same month last year
   A price model that cannot beat seasonal-naive has learned nothing about
   price, whatever its R-squared. The verdict prints either way.

    python data/scripts/price_models.py
    python data/scripts/price_models.py --scheme size
    python data/scripts/price_models.py --write     # into the dashboard aggregate

stdlib only.
"""
import argparse
import collections
import csv
import json
import math
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(ROOT, "data/bq/derived/price_panel.csv")
EXPLORER = os.path.join(ROOT, "public/data/flavor_explorer.json")
AGG = os.path.join(ROOT, "public/data/dashboard.json")

# A cluster needs enough months to fit and still hold out. 36 leaves 24 to train
# on before the first forecast at a 12-month test tail.
MIN_MONTHS = 36
# Below this the fixed-weight basket speaks for too little of the cluster to
# stand in for its price.
MIN_MATCHED = 0.50
HORIZON = 1


# ------------------------------------------------------------------ algebra --
def solve(A, b):
    """Gaussian elimination with partial pivoting. Small systems only."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            continue
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r == c:
                continue
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]


def ols(X, y, lam=1e-6):
    """Ridge-stabilised least squares. lam is tiny - it prevents a singular
    matrix when two dummies are collinear, not a real regularisation choice."""
    n, d = len(X), len(X[0])
    Xb = [[1.0] + list(r) for r in X]
    d1 = d + 1
    A = [[sum(Xb[i][a] * Xb[i][c] for i in range(n)) + (lam if a == c and a > 0 else 0.0)
          for c in range(d1)] for a in range(d1)]
    bv = [sum(Xb[i][a] * y[i] for i in range(n)) for a in range(d1)]
    return solve(A, bv)


def ols_cluster_se(X, y, groups, k=1, lam=1e-6):
    """Coefficient k and its CLUSTER-ROBUST standard error.

    Point estimates without uncertainty were the gap that let two cross-half
    fits (-3.30 and -0.99) look like a broken design when they were in fact
    one noisy design: their confidence intervals overlap heavily. Errors are
    correlated within a cluster across months, so the clustering dimension is
    the cluster, not the observation - the naive SE would be far too small.

    CR0 sandwich: (X'X)^-1 (sum_g X_g' u_g u_g' X_g) (X'X)^-1.
    """
    w = ols(X, y, lam)
    n, d = len(X), len(X[0]) + 1
    Xb = [[1.0] + list(r) for r in X]
    resid = [y[i] - sum(w[j] * Xb[i][j] for j in range(d)) for i in range(n)]
    XtX = [[sum(Xb[i][a] * Xb[i][b] for i in range(n)) for b in range(d)] for a in range(d)]
    inv = [[0.0] * d for _ in range(d)]
    for c in range(d):
        e = [1.0 if i == c else 0.0 for i in range(d)]
        col = solve([row[:] for row in XtX], e)
        for i in range(d):
            inv[i][c] = col[i]
    byg = collections.defaultdict(list)
    for i in range(n):
        byg[groups[i]].append(i)
    meat = [[0.0] * d for _ in range(d)]
    for idxs in byg.values():
        sc = [sum(Xb[i][a] * resid[i] for i in idxs) for a in range(d)]
        for a in range(d):
            for b in range(d):
                meat[a][b] += sc[a] * sc[b]
    var_kk = sum(inv[k][p] * meat[p][q] * inv[q][k] for p in range(d) for q in range(d))
    return w[k], math.sqrt(max(var_kk, 0.0)), len(byg)


def predict(w, x):
    return w[0] + sum(w[i + 1] * v for i, v in enumerate(x))


def r2(y, yhat):
    m = sum(y) / len(y)
    ss = sum((a - m) ** 2 for a in y)
    return 1 - sum((a - b) ** 2 for a, b in zip(y, yhat)) / ss if ss else 0.0


# ---------------------------------------------------------------- the panel --
def _f(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def load_panel(scheme):
    rows = [r for r in csv.DictReader(open(PANEL)) if r["scheme"] == scheme]
    by = collections.defaultdict(dict)
    for r in rows:
        try:
            idx = float(r["price_index"]) if r["price_index"] else None
        except ValueError:
            idx = None
        by[r["cluster"]][r["month"]] = {
            "rev": float(r["rev"]), "units": float(r["units"]),
            "stores": int(r["stores"]), "skus": int(r["skus"]),
            "uv": float(r["price_unitvalue"]),
            "idx": idx,
            "idx_a": _f(r.get("price_index_a")),
            "idx_b": _f(r.get("price_index_b")),
            "units_a": _f(r.get("units_a")) or 0.0,
            "units_b": _f(r.get("units_b")) or 0.0,
            "matched": float(r["matched_share"]),
            # TRANSACTION-based discount rate, not the quantity-based one.
            # disc_rate = discounted_units/units puts QUANTITY in the
            # denominator, so it carries the same measurement error u that
            # creates the division bias - using it as a control re-imports the
            # contamination the store-split exists to remove. disc_txn_rate has
            # a transaction denominator and is clean. Both are kept in the panel
            # so the contrast can be inspected.
            "disc": _f(r.get("disc_txn_rate")) or float(r["disc_rate"]),
            "disc_qty": float(r["disc_rate"]),
            "dist": _f(r.get("dist_points")) or float(r["stores"]),
            "stores_active": _f(r.get("stores_active")) or 0.0,
        }
    return by


def usable(series):
    """Months where every modelled quantity exists and the basket is deep enough."""
    return {m: d for m, d in series.items()
            if d["idx"] and d["idx"] > 0 and d["units"] > 0 and d["rev"] > 0
            and d["stores"] > 0 and d["matched"] >= MIN_MATCHED}


def rows_for(series, search=None):
    """One row per cluster-month with the regressors, in month order."""
    ms = sorted(usable(series))
    out = []
    for i, m in enumerate(ms):
        d = series[m]
        prev = series[ms[i - 1]] if i else None
        out.append({
            "m": m,
            "lp": math.log(d["idx"]),
            # PER ACTIVE STORE. The PDI store panel grows 3.89x across
            # 2019-2025 (5,148 -> 20,022 active stores), and 2019 alone is a
            # 2.2x expansion, so raw units mostly measure coverage. Revenue
            # grew 3.52x while revenue per active store grew only 1.58x:
            # roughly two thirds of PDI's apparent growth is panel expansion.
            # Modelling raw units regresses coverage on price.
            "lq": math.log(d["units"] / d["stores_active"]) if d.get("stores_active")
            else math.log(d["units"]),
            "lr": math.log(d["rev"]),
            # Distribution points normalised by panel-active stores. The raw
            # per-GTIN store count is an OUTCOME of price - cut price, win
            # doors - so controlling on it conditions on a collider. Dividing by
            # the month's active-store base removes panel drift, which is the
            # part of it that is genuinely exogenous.
            "lstores": math.log(d["dist"] / d["stores_active"])
            if d.get("stores_active") else math.log(d["dist"] or d["stores"]),
            "disc": d["disc"],
            "moy": int(m[5:7]),
            "d_lp": math.log(d["idx"] / prev["idx"]) if prev and prev["idx"] else None,
            "d_lq": math.log(d["units"] / prev["units"]) if prev else None,
            "d_lr": math.log(d["rev"] / prev["rev"]) if prev else None,
            "search": (search or {}).get(m),
            # Cross-half pair: price from store-half A, quantity from half B.
            # These two share no quantity term, which is the entire point.
            "lp_a": math.log(d["idx_a"]) if d.get("idx_a") else None,
            "lp_b": math.log(d["idx_b"]) if d.get("idx_b") else None,
            "lq_a": (math.log(d["units_a"] / (d["stores_active"] or 1))
                     if d.get("units_a") else None),
            "lq_b": (math.log(d["units_b"] / (d["stores_active"] or 1))
                     if d.get("units_b") else None),
        })
    return out


# ------------------------------------------------------------- elasticities --
def elasticities(panel):
    """Three specifications, reported together. The spread between them is the
    result; a single number here would be false precision."""
    pooled = []
    for cluster, series in panel.items():
        rs = rows_for(series)
        if len(rs) < MIN_MONTHS:
            continue
        for r in rs:
            pooled.append((cluster, r))
    if not pooled:
        return None

    # (a) raw pooled levels
    X = [[r["lp"]] for _c, r in pooled]
    y = [r["lq"] for _c, r in pooled]
    raw = ols(X, y)[1]

    # (b) within-cluster: demean both sides by cluster, which absorbs a cluster
    #     fixed effect exactly and removes the between-cluster comparison that
    #     is really format, not price response
    mp = collections.defaultdict(list)
    mq = collections.defaultdict(list)
    for c, r in pooled:
        mp[c].append(r["lp"])
        mq[c].append(r["lq"])
    mpc = {c: sum(v) / len(v) for c, v in mp.items()}
    mqc = {c: sum(v) / len(v) for c, v in mq.items()}
    Xw = [[r["lp"] - mpc[c]] for c, r in pooled]
    yw = [r["lq"] - mqc[c] for c, r in pooled]
    within = ols(Xw, yw)[1]

    # (c) within + distribution + month-of-year. Distribution is the big one:
    #     a cluster gaining stores sells more at any price.
    ms = collections.defaultdict(list)
    for c, r in pooled:
        ms[c].append(r["lstores"])
    msc = {c: sum(v) / len(v) for c, v in ms.items()}
    Xf, yf = [], []
    for c, r in pooled:
        moy = [1.0 if r["moy"] == k else 0.0 for k in range(2, 13)]
        Xf.append([r["lp"] - mpc[c], r["lstores"] - msc[c], r["disc"]] + moy)
        yf.append(r["lq"] - mqc[c])
    full = ols(Xf, yf)
    # (d) CROSS-HALF: price from one store-half, quantity from the other.
    #
    # This is the specification that matters, and the reason is arithmetic
    # rather than economic. Everywhere above, price is revenue/units, so
    # ln p = ln r - ln q carries -u for whatever measurement noise u sits in
    # quantity, while the left-hand side carries +u. That alone drives the
    # coefficient toward
    #     -Var(u) / (Var(ln p*) + Var(u))
    # with no economics in it at all: a true elasticity of ZERO can print as
    # -0.3 to -1.3. Fixed effects cannot remove it, because it is not an omitted
    # variable - it is the same measurement appearing on both sides.
    #
    # Splitting stores into two halves gives price and quantity independent
    # measurement errors, so the mechanical term vanishes. What remains is
    # classical measurement error in the regressor, which attenuates TOWARD
    # zero. So the naive and cross-half numbers BRACKET the descriptive
    # co-movement: naive is inflated away from zero, cross-half is attenuated
    # toward it. The gap between them is a direct estimate of the artifact.
    def cross(price_key, qty_key):
        Xc, yc, gc, kept = [], [], [], 0
        pm = collections.defaultdict(list)
        qm = collections.defaultdict(list)
        for c, r in pooled:
            if r.get(price_key) is None or r.get(qty_key) is None:
                continue
            pm[c].append(r[price_key])
            qm[c].append(r[qty_key])
        pmc = {c: sum(v) / len(v) for c, v in pm.items()}
        qmc = {c: sum(v) / len(v) for c, v in qm.items()}
        for c, r in pooled:
            if r.get(price_key) is None or r.get(qty_key) is None or c not in pmc:
                continue
            moy = [1.0 if r["moy"] == k else 0.0 for k in range(2, 13)]
            Xc.append([r[price_key] - pmc[c], r["lstores"] - msc[c], r["disc"]] + moy)
            yc.append(r[qty_key] - qmc[c])
            gc.append(c)
            kept += 1
        if kept < 60:
            return None, None, kept
        b, se, ng = ols_cluster_se(Xc, yc, gc, k=1)
        return b, se, kept

    ab, se_ab, n_ab = cross("lp_a", "lq_b")
    ba, se_ba, n_ba = cross("lp_b", "lq_a")
    both = [v for v in (ab, ba) if v is not None]

    return {
        "n": len(pooled),
        "clusters": len({c for c, _ in pooled}),
        "raw": round(raw, 3),
        "within": round(within, 3),
        "controlled": round(full[1], 3),
        "beta_stores": round(full[2], 3),
        "beta_disc": round(full[3], 3),
        "cross_ab": None if ab is None else round(ab, 3),
        "cross_ba": None if ba is None else round(ba, 3),
        "se_ab": None if se_ab is None else round(se_ab, 3),
        "se_ba": None if se_ba is None else round(se_ba, 3),
        "cross": None if not both else round(sum(both) / len(both), 3),
        "cross_n": max(n_ab, n_ba),
        "division_bias": (None if not both
                          else round(full[1] - sum(both) / len(both), 3)),
    }


# ---------------------------------------------------------------- forecasts --
FEATS = ["d_lp", "d_lstores", "disc", "d_lq_lag"]


def design(rs, i, with_price):
    """Regressors for predicting month i's log-revenue change from month i-1.
    Everything here is known at i-1, which is what makes it a forecast."""
    prev, cur = rs[i - 1], rs[i]
    if None in (prev["d_lp"], prev["d_lq"], cur["d_lr"]):
        return None
    x = [prev["d_lstores"] if "d_lstores" in prev else 0.0, prev["disc"], prev["d_lq"]]
    if with_price:
        x = [prev["d_lp"]] + x
    return x, cur["d_lr"]


def add_lags(rs):
    for i, r in enumerate(rs):
        p = rs[i - 1] if i else None
        r["d_lstores"] = (r["lstores"] - p["lstores"]) if p else None
    return rs


def expanding(rs, with_price, min_train=24):
    """Train on everything before month i, predict i. Walk forward."""
    add_lags(rs)
    preds, truth, base_p, base_d, base_s = [], [], [], [], []
    for i in range(min_train, len(rs)):
        tr = []
        for j in range(1, i):
            d = design(rs, j, with_price)
            if d and None not in d[0]:
                tr.append(d)
        te = design(rs, i, with_price)
        if len(tr) < 12 or not te or None in te[0]:
            continue
        w = ols([t[0] for t in tr], [t[1] for t in tr])
        preds.append(predict(w, te[0]))
        truth.append(te[1])
        base_p.append(0.0)                                   # persistence
        hist = [t[1] for t in tr]
        base_d.append(sum(hist) / len(hist))                 # drift
        # seasonal-naive: the same month last year's change
        sn = next((rs[k]["d_lr"] for k in range(i - 12, i - 11)
                   if 0 <= k < len(rs) and rs[k]["d_lr"] is not None), 0.0)
        base_s.append(sn)
    return preds, truth, base_p, base_d, base_s


def mae(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) if a else float("inf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheme", default="family", choices=["family", "size", "brand"])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--panel", help="override the panel CSV (used by the self-test)")
    args = ap.parse_args()

    global PANEL
    if args.panel:
        PANEL = args.panel
    if not os.path.exists(PANEL):
        sys.exit(f"No {PANEL}.\nRun: python data/scripts/build_price_panel.py "
                 "(needs BQ_TOKEN; ~$0.55)")

    panel = load_panel(args.scheme)
    print(f"scheme        {args.scheme}")
    print(f"clusters      {len(panel)}")

    print(f"months usable {sum(len(usable(s)) for s in panel.values()):,}")

    # How badly does mix move? Correlate each cluster's unit-value change against
    # its fixed-weight change. A low correlation means the two series disagree
    # about when prices moved, and the unit-value one is the wrong one.
    div = []
    for series in panel.values():
        ms = sorted(usable(series))
        for a, b in zip(ms, ms[1:]):
            u0, u1 = series[a]["uv"], series[b]["uv"]
            i0, i1 = series[a]["idx"], series[b]["idx"]
            if u0 > 0 and i0 > 0:
                div.append((math.log(u1 / u0), math.log(i1 / i0)))
    if len(div) > 30:
        du = [x for x, _ in div]
        di = [y for _, y in div]
        mu, mi = sum(du) / len(du), sum(di) / len(di)
        cov = sum((x - mu) * (y - mi) for x, y in div)
        sx = math.sqrt(sum((x - mu) ** 2 for x in du))
        sy = math.sqrt(sum((y - mi) ** 2 for y in di))
        r = cov / (sx * sy) if sx and sy else 0.0
        print(f"unit-value vs fixed-weight monthly change: r = {r:.3f} over {len(div):,} pairs"
              + ("   <- they disagree; mix is doing the moving" if r < 0.7 else ""))

    el = elasticities(panel)
    if not el:
        sys.exit("No cluster has enough usable months. Check matched_share in the panel.")
    print(f"\nPRICE-VOLUME CO-MOVEMENT  (n={el['n']:,} cluster-months, "
          f"{el['clusters']} clusters)")
    print(f"  raw pooled                       {el['raw']:+.3f}")
    print(f"  within cluster                   {el['within']:+.3f}")
    print(f"  within + distribution + season   {el['controlled']:+.3f}")
    print(f"     distribution coefficient      {el['beta_stores']:+.3f}")
    print(f"     discount-rate coefficient     {el['beta_disc']:+.3f}")
    swing = abs(el["raw"] - el["controlled"])
    print(f"  spread across specifications      {swing:.3f}"
          + ("   <- unstable; treat the number as a direction, not a magnitude"
             if swing > 0.5 else ""))

    if el.get("cross") is None:
        print("\n  CROSS-HALF UNAVAILABLE. The panel has no price_index_a/b columns, so\n"
              "  every number above still has price = revenue/units on one side and\n"
              "  quantity on the other. They are NOT elasticities - a true value of\n"
              "  zero prints here as roughly -0.3 to -1.3. Rebuild the panel with\n"
              "  build_price_panel.py to get the store-split columns.")
    else:
        print(f"\n  CROSS-HALF (price from one store-half, quantity from the other)")
        ci = []
        for nm, b, se in (("A price -> B units", el["cross_ab"], el.get("se_ab")),
                          ("B price -> A units", el["cross_ba"], el.get("se_ba"))):
            if se:
                lo, hi = b - 1.96 * se, b + 1.96 * se
                ci.append((lo, hi))
                print(f"    {nm:<28}{b:+.3f}   SE {se:.3f}   "
                      f"95% CI [{lo:+.2f}, {hi:+.2f}]")
            else:
                print(f"    {nm:<28}{b:+.3f}")
        print(f"    mean                        {el['cross']:+.3f}   (n={el['cross_n']:,})")

        # Two independent halves of the SAME stores should agree. Whether they
        # do is the design's own falsification test, and it is only answerable
        # with standard errors: point estimates of -3.30 and -0.99 look like a
        # broken design until you see their intervals overlap.
        if len(ci) == 2:
            lo = max(ci[0][0], ci[1][0])
            hi = min(ci[0][1], ci[1][1])
            if lo <= hi:
                print(f"    the two halves AGREE: their intervals overlap on "
                      f"[{lo:+.2f}, {hi:+.2f}]")
            else:
                print("    the two halves DISAGREE beyond sampling error — the split is\n"
                      "    not exchangeable and the estimate should not be used")
            width = max(c[1] - c[0] for c in ci)
            if width > 2.0:
                print(f"    BUT the interval spans {width:.1f} in elasticity units. That is\n"
                      "    too wide to act on: it does not exclude zero, an inelastic\n"
                      "    response, or a highly elastic one. Report this as 'not\n"
                      "    identified at this grain', not as an elasticity.")
        print("    Neither number is causal: retailers set price in response to demand.")

    print("\nFORECASTING log-revenue change, expanding window, h=1")
    print(f"{'cluster':<24}{'n':>5}{'price':>9}{'no-price':>10}{'persist':>9}"
          f"{'drift':>8}{'seas':>8}   verdict")
    wins = beats = 0
    per = {}
    for cluster, series in sorted(panel.items()):
        rs = rows_for(series)
        if len(rs) < MIN_MONTHS:
            continue
        p, t, bp, bd, bs = expanding(rs, True)
        q, _t2, _a, _b, _c = expanding(rs, False)
        if len(t) < 8:
            continue
        m_price, m_none = mae(t, p), mae(t, q[:len(t)] if q else p)
        m_p, m_d, m_s = mae(t, bp), mae(t, bd), mae(t, bs)
        best_base = min(m_p, m_d, m_s)
        ok = m_price < best_base
        better_than_noprice = m_price < m_none
        wins += ok
        beats += better_than_noprice
        per[cluster] = {"n": len(t), "price": round(m_price, 4),
                        "no_price": round(m_none, 4), "persistence": round(m_p, 4),
                        "drift": round(m_d, 4), "seasonal": round(m_s, 4),
                        "beats_baseline": ok, "price_helps": better_than_noprice}
        print(f"{cluster[:23]:<24}{len(t):>5}{m_price:>9.4f}{m_none:>10.4f}"
              f"{m_p:>9.4f}{m_d:>8.4f}{m_s:>8.4f}   "
              + ("beats baselines" if ok else "no better than trivial"))

    n = len(per)
    print(f"\n{wins}/{n} clusters beat every trivial baseline; "
          f"{beats}/{n} improve when price is included.")
    if not n:
        print("Nothing had enough usable months to score.")
    elif wins == 0:
        print("VERDICT: no usable forecasting signal at this granularity. That is a\n"
              "  result, not a failure - 84 monthly points per cluster can detect a\n"
              "  strong price response and not a weak one.")
    else:
        print("VERDICT: some clusters beat the baselines. Read that against how many\n"
              "  were tested before treating any single one as real.")

    out = {"scheme": args.scheme, "elasticity": el, "clusters": per,
           "beat_baseline": wins, "price_helps": beats, "tested": n,
           "note": ("Fixed-weight (Laspeyres) price index, not unit value, so the series "
                    "moves only when individual SKUs reprice. Expanding-window validation. "
                    "Coefficients are descriptive co-movements with controls, not causal "
                    "price effects: in this data retailers set price in response to demand, "
                    "so nothing here identifies what would happen if we set a price.")}
    if args.write:
        with open(AGG) as f:
            agg = json.load(f)
        agg.setdefault("audiences", {}).setdefault("opportunity", {})["price_model"] = out
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote price_model -> {AGG}")


if __name__ == "__main__":
    main()
