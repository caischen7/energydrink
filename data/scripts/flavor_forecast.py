#!/usr/bin/env python3
"""Forecast which flavors gain share — a regression, scored against baselines.

Reads data/bq/derived/price_panel.csv (built by build_price_panel.py) and, when
present, Google Trends merged into public/data/flavor_explorer.json.

THE TARGET IS SHARE, AND THAT CHOICE DOES REAL WORK
---------------------------------------------------
The model predicts the change in a flavor's share of NAMED-flavor revenue, not
its dollars. Two reasons, both load-bearing:

  1. PDI's store panel grows 3.89x across this window (5,148 -> 20,022 active
     stores). In dollars every flavor slopes up and a model would spend its
     capacity learning PDI's sales team. A share is a ratio of two quantities
     measured on the same panel in the same month, so coverage cancels exactly -
     no per-store normalisation needed, and no residual.
  2. "Popular" is inherently relative. A flavor growing 5% while the category
     grows 20% is losing, and only a share says so.

"Unspecified" - 54% of category revenue, and mostly Red Bull's and Monster's
core lines whose descriptions name no flavor - is EXCLUDED from the modelled
set and from the denominator. It is a residual bucket, not a flavor, and
leaving it in would mean half the target variable was "did Monster have a good
month".

WHAT THE FEATURES ARE, AND THE ONE THE DATA ALREADY ARGUES AGAINST
------------------------------------------------------------------
Everything is known at the forecast origin t; nothing is read from the future.

  level         log share. Tests mean reversion: do big flavors decay?
  mom3, mom12   3- and 12-month share momentum. Tests persistence of a trend.
  d_skus12      12-month change in log SKU count. The supply-side bet:
                manufacturers launch into flavors they expect to grow, so SKU
                entry may LEAD share.
  d_price12     12-month change in the fixed-weight price index.
  disc, d_disc  promo depth and its change (transaction-based - the
                quantity-based rate carries the measurement error that creates
                division bias; see build_price_panel.py).
  age_off_peak  months since the flavor's own peak share. A decay clock.
  sin/cos       Fourier seasonality, k=1 only, DATED AT t+h. Dating it at t
                would put January's coefficient on April's target at h=3. Two
                parameters rather than eleven monthly dummies, because the
                number of independent origins does not support eleven.

On d_skus12 the panel is already sceptical: Peach & stone fruit went from 5
SKUs to 19 while its share fell from 1.93% to 0.41%. If SKU entry predicted
popularity that could not happen, so the coefficient is worth reading closely.

THE RESULT, UP FRONT
--------------------
The regression does not work, and the honest deliverable is what beat it.

  MAGNITUDE  persistence - assuming a flavor's share does not move - has the
             lowest out-of-sample error at every horizon tested (3, 6 and 12
             months). The regression is 24-30% worse. Flavor share behaves close
             to a random walk over a year.
  RANKING    trailing 12-month momentum orders flavors BETTER than the
             regression does (top-minus-bottom-third spread +0.229 vs +0.181 at
             h=12). The regression dilutes a real signal by mixing in features
             that do not carry one.

So the recommended rule is: rank by trailing 12-month share momentum, and
attach no magnitude to it. The regression is kept and reported because showing
what lost is what makes the winner credible - and because a reader who tries
this will otherwise build it themselves and believe it.

Momentum ranking is genuinely useful even so: out of sample its bottom third
realised roughly -17% share change at 12 months against +6% for its top third.
It is better at spotting flavors about to decline than winners about to run.

HOW IT IS SCORED
----------------
Expanding origin. Train on every (family, month) strictly before the origin,
predict every family at origin+h, walk forward. Never random k-fold: that
trains on 2024 to predict 2022.

Ridge, with features standardised on TRAINING-WINDOW moments only, recomputed
at every origin. Ridge is not scale-invariant, and this panel mixes a share
momentum with sd ~0.1 against a price change with sd ~0.03 - penalising raw
columns would silently crush the small ones and manufacture a null.

Four baselines, all trivial, all hard to beat:
    persistence   share does not move
    drift         this family's mean historical change
    momentum      the last h-month change simply continues
    seasonal      the same calendar change a year earlier
A model that cannot beat all four has learned nothing, and the verdict says so.

    python data/scripts/flavor_forecast.py
    python data/scripts/flavor_forecast.py --horizon 6
    python data/scripts/flavor_forecast.py --write

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

EXCLUDE = {"Unspecified"}
# Minimum TRAINING ROWS (family-months), not months. With 10 features, scoring
# an origin off 36 rows fits noise: the first version did exactly that and the
# model came out nearly twice as bad as persistence. 14 families per origin, so
# 280 rows is about 20 origins of history.
MIN_TRAIN_ROWS = 280
MIN_SHARE = 0.0005             # 0.05% - below this a share is rounding noise

FEATURES = ["level", "mom3", "mom12", "d_skus12", "d_price12",
            "disc", "d_disc", "age_off_peak", "sin", "cos"]


# ------------------------------------------------------------------ algebra --
def solve(A, b):
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


def ridge(X, y, lam):
    """Closed-form ridge. The intercept is never penalised."""
    n, d = len(X), len(X[0])
    Xb = [[1.0] + list(r) for r in X]
    d1 = d + 1
    A = [[sum(Xb[i][a] * Xb[i][c] for i in range(n)) + (lam if a == c and a > 0 else 0.0)
          for c in range(d1)] for a in range(d1)]
    bv = [sum(Xb[i][a] * y[i] for i in range(n)) for a in range(d1)]
    return solve(A, bv)


def apply(w, x):
    return w[0] + sum(w[i + 1] * v for i, v in enumerate(x))


# -------------------------------------------------------------------- panel --
def load():
    rows = [r for r in csv.DictReader(open(PANEL)) if r["scheme"] == "family"]
    rev = collections.defaultdict(dict)
    skus = collections.defaultdict(dict)
    price = collections.defaultdict(dict)
    disc = collections.defaultdict(dict)
    for r in rows:
        f, m = r["cluster"], r["month"]
        if f in EXCLUDE:
            continue
        rev[f][m] = float(r["rev"])
        skus[f][m] = int(r["skus"])
        try:
            price[f][m] = float(r["price_index"]) if r["price_index"] else None
        except ValueError:
            price[f][m] = None
        disc[f][m] = float(r["disc_txn_rate"] or 0)
    months = sorted({m for d in rev.values() for m in d})
    # Share of NAMED-flavor revenue: coverage cancels, and "popular" is relative.
    total = {m: sum(rev[f].get(m, 0.0) for f in rev) for m in months}
    share = {f: {m: (rev[f].get(m, 0.0) / total[m] if total[m] else 0.0) for m in months}
             for f in rev}
    return months, share, skus, price, disc


def build_rows(months, share, skus, price, disc, horizon):
    """One row per (family, origin). Every feature is known at the origin."""
    idx = {m: i for i, m in enumerate(months)}
    out = []
    for f in share:
        s = share[f]
        peak_val, peak_i = 0.0, 0
        for i, m in enumerate(months):
            if s[m] > peak_val:
                peak_val, peak_i = s[m], i
            j = i + horizon
            if j >= len(months):
                continue
            if i < 12 or s[m] < MIN_SHARE or s[months[j]] < MIN_SHARE:
                continue
            m3, m12 = months[i - 3], months[i - 12]
            if s[m3] < MIN_SHARE or s[m12] < MIN_SHARE:
                continue
            p_now, p_12 = price[f].get(m), price[f].get(m12)
            sk_now, sk_12 = skus[f].get(m, 0), skus[f].get(m12, 0)
            tgt_month = months[j]
            moy = int(tgt_month[5:7])
            out.append({
                "fam": f, "origin": m, "target_month": tgt_month, "i": i,
                "level": math.log(s[m]),
                "mom3": math.log(s[m] / s[m3]),
                "mom12": math.log(s[m] / s[m12]),
                "d_skus12": math.log((sk_now or 1) / (sk_12 or 1)),
                "d_price12": (math.log(p_now / p_12)
                              if p_now and p_12 and p_now > 0 and p_12 > 0 else 0.0),
                "disc": disc[f].get(m, 0.0),
                "d_disc": disc[f].get(m, 0.0) - disc[f].get(m12, 0.0),
                "age_off_peak": (i - peak_i) / 12.0,
                # Dated at the TARGET month, not the origin.
                "sin": math.sin(2 * math.pi * moy / 12),
                "cos": math.cos(2 * math.pi * moy / 12),
                "y": math.log(s[tgt_month] / s[m]),
                # baselines
                "b_drift_src": None,
                "b_mom": math.log(s[m] / s[months[max(0, i - horizon)]]),
                "b_seas": (math.log(s[months[min(len(months) - 1, i - 12 + horizon)]] / s[m12])
                           if i >= 12 else 0.0),
            })
    return out


def standardise(train, test, feats):
    """Moments from the TRAINING window only. Recomputed at every origin."""
    mu, sd = {}, {}
    for k in feats:
        v = [r[k] for r in train]
        mu[k] = sum(v) / len(v)
        s = statistics.pstdev(v)
        sd[k] = s if s > 1e-9 else 1.0
    z = lambda rs: [[(r[k] - mu[k]) / sd[k] for k in feats] for r in rs]  # noqa: E731
    return z(train), z(test)


def mae(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) if a else float("inf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=12, help="months ahead")
    ap.add_argument("--lam", type=float, default=1.0, help="ridge penalty (standardised)")
    ap.add_argument("--min-train", type=int, default=MIN_TRAIN_ROWS,
                    help="minimum training rows before an origin is scored")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(PANEL):
        sys.exit(f"No {PANEL}. Run build_price_panel.py first.")

    months, share, skus, price, disc = load()
    rows = build_rows(months, share, skus, price, disc, args.horizon)
    fams = sorted({r["fam"] for r in rows})
    print(f"horizon       {args.horizon} months")
    print(f"families      {len(fams)}  (Unspecified excluded as a residual bucket)")
    print(f"panel rows    {len(rows)}")
    if len(rows) < 100:
        sys.exit("too few rows to score")

    # ---- expanding origin -------------------------------------------------
    origins = sorted({r["i"] for r in rows})
    preds = {k: [] for k in ("model", "persist", "drift", "mom", "seas", "truth")}
    keep = []
    for o in origins:
        tr = [r for r in rows if r["i"] < o - args.horizon]   # embargo the overlap
        te = [r for r in rows if r["i"] == o]
        if len(tr) < args.min_train or not te:
            continue
        Xtr, Xte = standardise(tr, te, FEATURES)
        w = ridge(Xtr, [r["y"] for r in tr], args.lam)
        hist = collections.defaultdict(list)
        for r in tr:
            hist[r["fam"]].append(r["y"])
        for r, x in zip(te, Xte):
            preds["model"].append(apply(w, x))
            preds["persist"].append(0.0)
            h = hist.get(r["fam"], [])
            preds["drift"].append(sum(h) / len(h) if h else 0.0)
            preds["mom"].append(r["b_mom"])
            preds["seas"].append(r["b_seas"])
            preds["truth"].append(r["y"])
            keep.append(r)

    n = len(preds["truth"])
    if n < 40:
        sys.exit(f"only {n} out-of-sample predictions — not enough to score")
    scores = {k: mae(preds["truth"], preds[k])
              for k in ("model", "persist", "drift", "mom", "seas")}
    print(f"\nout-of-sample, expanding origin ({n} predictions, "
          f"{len({r['origin'] for r in keep})} origins)")
    for k in ("model", "persist", "drift", "mom", "seas"):
        print(f"  {k:<12}MAE {scores[k]:.4f}")
    best_base = min(k for k in scores if k != "model")
    bb = min((scores[k], k) for k in scores if k != "model")
    beats = scores["model"] < bb[0]
    print(f"  best baseline is {bb[1]} at {bb[0]:.4f}")
    print(f"  VERDICT: model {'BEATS' if beats else 'does NOT beat'} it"
          + ("" if beats else " — no usable signal at this horizon"))

    # ---- direction, which is what "popular" actually asks ------------------
    hit = sum(1 for p, t in zip(preds["model"], preds["truth"]) if (p > 0) == (t > 0))
    base_hit = sum(1 for t in preds["truth"] if t > 0)
    print(f"\n  direction called right {hit}/{n} = {hit/n*100:.1f}%")
    print(f"  always-say-'grows' would score {max(base_hit, n-base_hit)/n*100:.1f}%")

    # ---- RANKING SKILL, which is the question actually being asked --------
    # MAE asks "how close is the number". "Which flavors will be popular" asks
    # "is the ordering right", and a model can fail the first and pass the
    # second. Each origin's predictions are ranked and the realised outcome of
    # the top and bottom thirds compared. If picking the model's top third beat
    # picking at random, it is useful for shortlisting even though it loses on
    # magnitude.
    def rank_spread(scorer):
        """Mean realised outcome of the top third minus the bottom third."""
        byo = collections.defaultdict(list)
        for i, r in enumerate(keep):
            byo[r["origin"]].append((scorer(i, r), preds["truth"][i]))
        top, bottom = [], []
        for v in byo.values():
            if len(v) < 6:
                continue
            v.sort(key=lambda t: t[0], reverse=True)
            k = max(1, len(v) // 3)
            top += [t for _p, t in v[:k]]
            bottom += [t for _p, t in v[-k:]]
        if not top or not bottom:
            return None
        return (sum(top) / len(top), sum(bottom) / len(bottom),
                sum(top) / len(top) - sum(bottom) / len(bottom), len(top))

    print("\n  ranking skill — top third minus bottom third, realised")
    # Persistence predicts zero for every flavor, so it produces NO ordering and
    # cannot appear here. That is why it wins on MAE and is useless for the
    # question actually asked. Momentum is the honest control: it is trivial,
    # it does produce an ordering, and the model has to beat it to have earned
    # anything.
    res = {}
    for nm, sc in (("model", lambda i, r: preds["model"][i]),
                   ("momentum (control)", lambda i, r: r["b_mom"]),
                   ("drift (control)", lambda i, r: preds["drift"][i])):
        out_ = rank_spread(sc)
        if out_:
            res[nm] = out_
            t, b, sp, k = out_
            print(f"    {nm:<20}top {t:+.4f}  bottom {b:+.4f}  spread {sp:+.4f}  (n={k})")
    if "model" in res and "momentum (control)" in res:
        beat = res["model"][2] > res["momentum (control)"][2]
        print(f"    the model's ordering is {'BETTER' if beat else 'NO BETTER'} "
              f"than trivial momentum")

    # ---- what the model learned -------------------------------------------
    Xall, _ = standardise(rows, rows[:1], FEATURES)
    wfull = ridge(Xall, [r["y"] for r in rows], args.lam)
    print("\n  standardised coefficients (full fit, direction only):")
    for f, c in sorted(zip(FEATURES, wfull[1:]), key=lambda kv: -abs(kv[1])):
        print(f"    {f:<14}{c:+.4f}")

    # ---- the forward call, made with the rule that actually won -----------
    # Ranked by trailing 12-month share momentum, not by the regression. The
    # scoring above is why: momentum orders these better than the model does,
    # and persistence predicts the magnitude better than either. So the honest
    # deliverable is an ORDERING from momentum with no magnitude attached.
    lastm = months[-1]
    fwd = []
    for f in sorted(share):
        s = share[f]
        if s[lastm] < MIN_SHARE or s[months[-13]] < MIN_SHARE:
            continue
        fwd.append((math.log(s[lastm] / s[months[-13]]), f, s[lastm] * 100))
    fwd.sort(reverse=True)
    print(f"\n  FLAVORS RANKED BY 12-MONTH SHARE MOMENTUM as of {lastm}")
    print(f"  {'flavor':<24}{'share now':>11}{'12m momentum':>15}")
    for mom, f, cur in fwd:
        print(f"    {f[:22]:<22}{cur:>10.2f}%{(math.exp(mom)-1)*100:>+14.1f}%")
    print("\n  This is an ORDERING, not a forecast of levels. Momentum's top third\n"
          "  realised a materially better outcome than its bottom third out of\n"
          "  sample; no method tested here predicted the SIZE of the move better\n"
          "  than assuming no change at all.")

    # ---- the regression's own forecast, kept for comparison ---------------
    last = max(r["i"] for r in rows)
    latest = [r for r in rows if r["i"] == last]
    if latest:
        Xtr, Xte = standardise(rows, latest, FEATURES)
        w = ridge(Xtr, [r["y"] for r in rows], args.lam)
        fc = sorted(((apply(w, x), r) for r, x in zip(latest, Xte)), reverse=True)
        print(f"\n  For contrast, the REGRESSION's ordering from {latest[0]['origin']}"
              f"  (share change, {args.horizon}m)")
        for p, r in fc:
            cur = math.exp(r["level"]) * 100
            print(f"    {r['fam'][:22]:<24}{cur:>6.2f}%  ->  {cur*math.exp(p):>6.2f}%   "
                  f"{'+' if p>=0 else ''}{(math.exp(p)-1)*100:>6.1f}%")
        print("  Shown for comparison only — it lost to momentum on ranking and to\n"
              "  persistence on magnitude, so it is not the recommended rule.")

    if args.write:
        out = {
            "horizon": args.horizon, "n": n, "rows": len(rows),
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "beats_baseline": beats, "best_baseline": bb[1],
            "direction_accuracy": round(hit / n, 3),
            "coefficients": {f: round(c, 4) for f, c in zip(FEATURES, wfull[1:])},
            "forecast": [{"fam": r["fam"], "from": round(math.exp(r["level"]) * 100, 3),
                          "to": round(math.exp(r["level"] + p) * 100, 3),
                          "pct": round((math.exp(p) - 1) * 100, 1)} for p, r in fc],
            "note": ("Share of named-flavor revenue, so PDI's 3.89x panel growth cancels. "
                     "Expanding-origin validation with the overlapping window embargoed. "
                     "Ridge on training-window-standardised features."),
        }
        with open(AGG) as f:
            agg = json.load(f)
        agg.setdefault("audiences", {}).setdefault("opportunity", {})["flavor_forecast"] = out
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote flavor_forecast -> {AGG}")


if __name__ == "__main__":
    main()
