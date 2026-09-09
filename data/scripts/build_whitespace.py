#!/usr/bin/env python3
"""Whitespace engine: ten analyses over the committed corpus -> whitespace.json.

Feeds whitespace.html (ten tabs). Reads only committed data - the licensed
SKU-level BigQuery extracts stay untracked - and writes
public/data/whitespace.json, which nginx Basic Auth guards along with the rest
of public/data/.

THE REFRAME THIS PAGE IS BUILT ON
--------------------------------
flavor_forecast.py established that the TIME-SERIES direction is exhausted:
84 months x 14 families is ~28 independent origins at h=12, persistence beats
the regression at every horizon, and an exogenous attention block made it worse
(+3.1 / +8.6 / +14.1% MAE) rather than better.

The CROSS-SECTION is a different problem and is properly powered: 2,309 SKUs x
232 brands, each carrying revenue, store count, flavor family, size and an
audience label. So every analysis here asks "which attribute cells are
under-supplied relative to demand", never "what will sell next year".

THREE OF THE TEN CANNOT BE COMPUTED HERE, AND SAY SO RATHER THAN GUESSING
------------------------------------------------------------------------
There is no gcloud/bq client in this container, so anything needing a fresh
scan of pdi_daily_agg is scaffolded, not faked: it ships the exact SQL, the
dry-run cost, and an empty result set flagged status="blocked". A blocked panel
renders as a method card, never as numbers.

  7  cannibalization   needs store x SKU x week
  8  geographic        needs STORE_ID joined to geography
  10 nutrition         data/openfoodfacts/products.csv is GENERATED SAMPLE data
                       (see its README). Marked status="sample": the panel
                       renders the mechanism and refuses to draw conclusions.

THE TENURE CONFOUND, STATED ONCE AND INHERITED EVERYWHERE
---------------------------------------------------------
Velocity here is LIFETIME revenue per store, because the committed extract
carries no first-sale date. A SKU selling since 2016 accumulates more than an
identical one launched in 2024, so velocity is confounded with tenure. Two
things limit the damage and neither removes it:

  * the alive-only cut (last sale within ALIVE_MONTHS of the window end) drops
    the discontinued tail, which is where the worst of it sits;
  * comparisons are made WITHIN flavor family and within size wherever the
    question allows, so cohorts are closer in age.

The clean fix is one cheap column - MIN(DATE) per GTIN - and it is listed in
the "needs" block of every panel that inherits the confound. Do not read the
velocity numbers as a launch forecast until that lands.

    python data/scripts/build_whitespace.py
    python data/scripts/build_whitespace.py --report

stdlib only.
"""
import argparse
import collections
import csv
import json
import math
import os
import random
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGG = os.path.join(ROOT, "public/data/dashboard.json")
PANEL = os.path.join(ROOT, "data/bq/derived/price_panel.csv")
GNPD = os.path.join(ROOT, "data/bq/derived/gnpd_claim_trends.csv")
SOCIAL = os.path.join(ROOT, "data/bq/derived/flavor_social.csv")
MKT = os.path.join(ROOT, "data/market")
OFF = os.path.join(ROOT, "data/openfoodfacts/products.csv")
OUT = os.path.join(ROOT, "public/data/whitespace.json")

WINDOW_END = "2026-07"
ALIVE_MONTHS = 2       # last sale within 2 months of window end == still selling
MIN_STORES = 25        # below this, $/store is a ratio of two tiny numbers


# ------------------------------------------------------------------- helpers --
def month_diff(a, b):
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def load_skus():
    """2,309 SKUs with brand, flavor family, size, stores, revenue, audience."""
    d = json.load(open(AGG))
    auds = d["audiences"]["auds"]
    out = []
    for a in auds:
        for p in a.get("prod", []):
            if not p.get("st") or not p.get("r"):
                continue
            out.append({
                "desc": p.get("d") or "", "brand": p.get("b") or "",
                "flavor": p.get("fl") or "", "family": p.get("ff") or "Unspecified",
                "size": (p.get("sz") or "").strip(), "stores": int(p["st"]),
                "rev": float(p["r"]), "last": (p.get("last") or "")[:7],
                "aud": a["name"],
            })
    return d, out


def size_oz(s):
    m = re.search(r"([\d.]+)\s*OZ", s or "", re.I)
    if not m:
        return None
    try:
        v = float(m.group(1))
    except ValueError:
        return None
    return v if 1 < v < 64 else None


def size_bucket(s):
    oz = size_oz(s)
    if oz is None:
        return "unknown"
    if oz <= 8.9:
        return "shot/mini (<=8.9oz)"
    if oz <= 12.9:
        return "standard (9-12.9oz)"
    if oz <= 16.9:
        return "tall (13-16.9oz)"
    return "big (17oz+)"


def alive(p):
    return bool(p["last"]) and month_diff(p["last"], WINDOW_END) <= ALIVE_MONTHS


def pearson(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float("nan")


def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(rank(x), rank(y))


# ------------------------------------------------------------------- algebra --
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
    n, d = len(X), len(X[0])
    Xb = [[1.0] + list(r) for r in X]
    d1 = d + 1
    A = [[sum(Xb[i][a] * Xb[i][c] for i in range(n)) + (lam if a == c and a > 0 else 0.0)
          for c in range(d1)] for a in range(d1)]
    bv = [sum(Xb[i][a] * y[i] for i in range(n)) for a in range(d1)]
    return solve(A, bv)


def predict(w, x):
    return w[0] + sum(w[i + 1] * v for i, v in enumerate(x))


def auc(scores, labels):
    pairs = sorted(zip(scores, labels))
    pos = sum(labels)
    neg = len(labels) - pos
    if not pos or not neg:
        return float("nan")
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            if pairs[k][1]:
                rank_sum += avg
        i = j + 1
    return (rank_sum - pos * (pos + 1) / 2) / (pos * neg)


# ============================================================== 1. VELOCITY ==
def t1_velocity(skus):
    """Sells fast where stocked, but is not stocked. The CPG whitespace quadrant.

    Velocity is $/store, so it does not reward a SKU for merely being everywhere;
    distribution is the store count itself. The interesting quadrant is high
    velocity + low distribution: demand is proven and the shelf has not caught up.
    """
    live = [p for p in skus if alive(p) and p["stores"] >= MIN_STORES]
    for p in live:
        p["vel"] = p["rev"] / p["stores"]
    vmed = statistics.median(p["vel"] for p in live)
    smed = statistics.median(p["stores"] for p in live)

    quad = collections.Counter()
    for p in live:
        hv = p["vel"] >= vmed
        hd = p["stores"] >= smed
        p["quad"] = ("proven, under-distributed" if hv and not hd else
                     "scaled winners" if hv and hd else
                     "niche / fading" if not hv and not hd else
                     "wide but weak")
        quad[p["quad"]] += 1

    under = sorted([p for p in live if p["quad"] == "proven, under-distributed"],
                   key=lambda p: -p["vel"])[:25]
    # Cell view: which family x size cells hold the most under-distributed volume
    cells = collections.defaultdict(lambda: {"n": 0, "rev": 0.0, "vel": [], "stores": []})
    for p in live:
        k = (p["family"], size_bucket(p["size"]))
        c = cells[k]
        c["n"] += 1
        c["rev"] += p["rev"]
        c["vel"].append(p["vel"])
        c["stores"].append(p["stores"])
    cellrows = []
    for (fam, sz), c in cells.items():
        if c["n"] < 5 or sz == "unknown":
            continue
        cellrows.append({
            "family": fam, "size": sz, "n": c["n"],
            "med_vel": round(statistics.median(c["vel"]), 1),
            "med_stores": int(statistics.median(c["stores"])),
            "rev": round(c["rev"], 0),
        })
    cellrows.sort(key=lambda r: -r["med_vel"])
    return {
        "status": "ok",
        "n": len(live), "median_velocity": round(vmed, 1), "median_stores": int(smed),
        "quadrants": [{"label": k, "n": v} for k, v in quad.most_common()],
        "points": [{"x": p["stores"], "y": round(p["vel"], 2), "label": p["desc"][:60],
                    "brand": p["brand"], "family": p["family"], "quad": p["quad"]}
                   for p in sorted(live, key=lambda q: -q["rev"])[:600]],
        "under": [{"desc": p["desc"][:70], "brand": p["brand"], "family": p["family"],
                   "size": p["size"], "stores": p["stores"], "vel": round(p["vel"], 1),
                   "rev": round(p["rev"], 0)} for p in under],
        "cells": cellrows[:24],
        "needs": ["MIN(DATE) per GTIN to remove the tenure confound"],
    }


# ====================================================== 2. ATTRIBUTE DEMAND ==
def t2_attributes(skus):
    """Which ATTRIBUTES carry velocity, once brand scale is held constant.

    log velocity ~ flavor family + size bucket + audience + log(brand revenue).
    Brand scale is in the model deliberately: without it the flavor coefficients
    would mostly be reading "Red Bull is big". Scored out of sample on a random
    30% holdout against the intercept-only baseline, because a coefficient table
    from an unvalidated fit is decoration.
    """
    live = [p for p in skus if alive(p) and p["stores"] >= MIN_STORES]
    brand_rev = collections.defaultdict(float)
    for p in skus:
        brand_rev[p["brand"]] += p["rev"]

    fams = sorted({p["family"] for p in live})
    sizes = sorted({size_bucket(p["size"]) for p in live})
    auds = sorted({p["aud"] for p in live})
    # Drop one level of each block as the reference cell, or the one-hot columns
    # are collinear with the intercept and ridge silently splits the effect.
    fam_l, size_l, aud_l = fams[1:], sizes[1:], auds[1:]
    names = ([f"family: {f}" for f in fam_l] + [f"size: {s}" for s in size_l]
             + [f"audience: {a}" for a in aud_l] + ["log brand revenue"])

    def feat(p):
        return ([1.0 if p["family"] == f else 0.0 for f in fam_l]
                + [1.0 if size_bucket(p["size"]) == s else 0.0 for s in size_l]
                + [1.0 if p["aud"] == a else 0.0 for a in aud_l]
                + [math.log(brand_rev[p["brand"]] + 1)])

    X = [feat(p) for p in live]
    y = [math.log(p["rev"] / p["stores"]) for p in live]
    rng = random.Random(11)
    idx = list(range(len(X)))
    rng.shuffle(idx)
    cut = int(len(idx) * 0.7)
    tr, te = idx[:cut], idx[cut:]
    mu = [statistics.mean(X[i][j] for i in tr) for j in range(len(X[0]))]
    sd = [statistics.pstdev([X[i][j] for i in tr]) or 1.0 for j in range(len(X[0]))]
    z = lambda i: [(X[i][j] - mu[j]) / sd[j] for j in range(len(mu))]  # noqa: E731
    w = ridge([z(i) for i in tr], [y[i] for i in tr], 1.0)
    pred = [predict(w, z(i)) for i in te]
    truth = [y[i] for i in te]
    ybar = statistics.mean(y[i] for i in tr)
    sse = sum((a - b) ** 2 for a, b in zip(pred, truth))
    sst = sum((t - ybar) ** 2 for t in truth)
    r2 = 1 - sse / sst if sst else float("nan")
    mae_m = sum(abs(a - b) for a, b in zip(pred, truth)) / len(te)
    mae_b = sum(abs(ybar - t) for t in truth) / len(te)

    coefs = sorted(zip(names, w[1:]), key=lambda t: -abs(t[1]))
    # Residual whitespace: cells the model says should sell well, that carry few SKUs
    resid = collections.defaultdict(list)
    for i, p in enumerate(live):
        resid[(p["family"], size_bucket(p["size"]))].append(y[i] - predict(w, z(i)))
    gaps = [{"family": f, "size": s, "n": len(v), "mean_resid": round(statistics.mean(v), 3)}
            for (f, s), v in resid.items() if len(v) >= 6 and s != "unknown"]
    gaps.sort(key=lambda g: -g["mean_resid"])
    return {
        "status": "ok", "n": len(live), "n_train": len(tr), "n_test": len(te),
        "r2_oos": round(r2, 3), "mae_model": round(mae_m, 3), "mae_baseline": round(mae_b, 3),
        "beats_baseline": bool(mae_m < mae_b),
        "coefs": [{"name": n, "beta": round(b, 4)} for n, b in coefs[:16]],
        "gaps": gaps[:14],
        "needs": ["MIN(DATE) per GTIN to remove the tenure confound"],
    }


# ============================================================ 3. CLAIM SPACE ==
CLAIMS = [
    ("Sugar free / zero sugar", r"zero sugar|sugar ?free|no sugar|\bzs\b|diet"),
    ("Vitamin / fortified",     r"vitamin|b12|b-12|fortif|electrolyte"),
    ("Natural / organic",       r"organic|natural|clean|plant"),
    ("Focus / nootropic",       r"focus|nootropic|brain|cognit|clarity|alpha"),
    ("Protein / recovery",      r"protein|recovery|amino|bcaa|collagen"),
    ("Hydration",               r"hydrat|water|aqua"),
    ("Performance / pre-workout", r"pre.?workout|performance|pump|strength"),
    ("Tea / coffee base",       r"\btea\b|coffee|espresso|matcha|yerba"),
]
CLAIM_RX = [(n, re.compile(p, re.I)) for n, p in CLAIMS]

# GNPD claim -> the claim bucket above it belongs to. GNPD measures LAUNCH
# frequency (share of new products carrying a claim); PDI measures SALES. They
# are different questions, so the join is stated rather than implied.
GNPD_MAP = {
    "Sugar Free": "Sugar free / zero sugar",
    "No Added Sugar": "Sugar free / zero sugar",
    "Low/No/Reduced Calorie": "Sugar free / zero sugar",
    "Vitamin/Mineral Fortified": "Vitamin / fortified",
    "Functional - Brain & Nervous System": "Focus / nootropic",
    "Functional - Energy": "Performance / pre-workout",
    "Functional - Slimming": "Performance / pre-workout",
    "Organic": "Natural / organic",
    "Plant Based": "Natural / organic",
    "Vegan/No Animal Ingredients": "Natural / organic",
    "No Additives/Preservatives": "Natural / organic",
}


def t3_claims(skus):
    """Claims growing in NEW LAUNCHES (GNPD) against claims earning money (PDI).

    The gap is the whole point: a claim that is spreading fast across launches
    but holds a small share of revenue is either an early trend or a fashion
    nobody buys, and the two look identical here. This ranks them; it does not
    adjudicate them.
    """
    live = [p for p in skus if alive(p)]
    tot_rev = sum(p["rev"] for p in live)
    # COVERAGE FIRST. PDI descriptions are terse - the median is 41 characters and
    # the largest SKUs in the file are literally "MONSTER" and "RED BULL" - so a
    # claim token is present on only a small minority of them. Reporting
    # "sugar free is 0.2% of revenue" off that would report a DETECTION failure
    # as a market finding. Every share below is therefore computed within the
    # DETECTABLE subset, and the coverage figures say how small that subset is.
    any_rx = re.compile("|".join(f"(?:{p})" for _, p in CLAIMS), re.I)
    detect = [p for p in live if any_rx.search(p["desc"])]
    det_rev = sum(p["rev"] for p in detect)
    coverage = {
        "skus_detectable": len(detect), "skus_total": len(live),
        "sku_pct": round(100 * len(detect) / len(live), 1),
        "rev_detectable": round(det_rev, 0), "rev_total": round(tot_rev, 0),
        "rev_pct": round(100 * det_rev / tot_rev, 2),
    }
    rows = []
    for name, rx in CLAIM_RX:
        hit = [p for p in live if rx.search(p["desc"])]
        rows.append({
            "claim": name, "skus": len(hit),
            "sku_share_of_detected": round(100 * len(hit) / len(detect), 1) if detect else 0.0,
            "rev": round(sum(p["rev"] for p in hit), 0),
            "rev_share_of_detected": round(100 * sum(p["rev"] for p in hit) / det_rev, 1)
            if det_rev else 0.0,
            "med_vel": round(statistics.median([p["rev"] / p["stores"] for p in hit]), 1)
            if hit else 0.0,
        })
    gn = {}
    if os.path.exists(GNPD):
        for r in csv.DictReader(open(GNPD)):
            b = GNPD_MAP.get(r["claim"])
            if not b:
                continue
            gn.setdefault(b, []).append(float(r["delta_pp"]))
    for r in rows:
        d = gn.get(r["claim"])
        r["gnpd_delta_pp"] = round(max(d), 1) if d else None
    base = statistics.median([r["med_vel"] for r in rows if r["med_vel"]])
    for r in rows:
        r["vel_index"] = round(r["med_vel"] / base, 2) if base else None
    rows.sort(key=lambda r: -(r["gnpd_delta_pp"] or -99))
    return {
        "status": "ok", "n": len(live), "rows": rows, "coverage": coverage,
        "note": "GNPD measures share of NEW LAUNCHES carrying a claim; PDI measures "
                "sales. A positive delta with a low revenue share is an unproven bet, "
                "not a validated one.",
        "caveat": f"Claim tokens are detectable on only {coverage['sku_pct']}% of live "
                  f"SKUs and {coverage['rev_pct']}% of revenue, because PDI descriptions "
                  f"are terse. Shares here are WITHIN that detectable subset and "
                  f"understate every claim's true footprint. Ranking is usable; levels "
                  f"are not. A real claim map needs the GNPD product-level join.",
        "needs": ["GNPD product-level claim flags joined to GTIN, or a richer product "
                  "description source than PDI"],
    }


# ======================================================== 4. PRICE RESPONSE ==
def t4_elasticity():
    """Price response, POOLED - because per-family it is not identified.

    price = revenue/units, so noise in units enters the regressor as -u and the
    outcome as +u, and the naive slope is negative even at a TRUE elasticity of
    zero (see build_price_panel.py). The panel ships two disjoint halves of
    stores; pairing A-price with B-quantity makes the two measurement errors
    independent and the mechanical term cancels.

    THE FIRST VERSION OF THIS PANEL REPORTED PER-FAMILY ELASTICITIES AND THEY
    WERE NONSENSE - Watermelon -9.3, Coffee & cream +2.5. Each family carries
    only 72 usable 12-month changes, and the fixed-weight price index barely
    moves within one, so the slope is a ratio of a small covariance to a tiny
    variance. Pooling to 800-odd observations gives -0.67, which matches
    price_models.py's independently-built cross-half estimate of -0.668.

    So the pooled number is reported with its interval, the per-family numbers
    are kept ONLY as evidence of that instability, and the verdict follows
    price_models.py: at this grain the interval is too wide to act on.

    Series are 12-month log changes of units per ACTIVE store, which removes
    both the family trend and PDI's 3.89x store ramp.
    """
    if not os.path.exists(PANEL):
        return {"status": "blocked", "needs": ["data/bq/derived/price_panel.csv"]}
    rows = [r for r in csv.DictReader(open(PANEL)) if r["scheme"] == "family"]
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["cluster"]][r["month"]] = r

    def series(fam, col_p, col_q):
        ser = by[fam]
        xs, ys = [], []
        for m in sorted(ser):
            m0 = f"{int(m[:4]) - 1}-{m[5:7]}"
            if m0 not in ser:
                continue
            a, b = ser[m], ser[m0]
            try:
                p1, p0 = float(a[col_p] or 0), float(b[col_p] or 0)
                q1 = float(a[col_q] or 0) / float(a["stores_active"] or 1)
                q0 = float(b[col_q] or 0) / float(b["stores_active"] or 1)
            except (ValueError, ZeroDivisionError):
                continue
            if min(p1, p0, q1, q0) <= 0:
                continue
            xs.append(math.log(p1 / p0))
            ys.append(math.log(q1 / q0))
        return xs, ys

    def ols(xs, ys):
        """slope, standard error, n."""
        n = len(xs)
        if n < 12:
            return None
        mx, my = statistics.mean(xs), statistics.mean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        if den <= 0:
            return None
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
        a = my - b * mx
        rss = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys))
        se = math.sqrt(rss / (n - 2) / den) if n > 2 else float("nan")
        return b, se, n

    fams = [f for f in by if f != "Unspecified"]
    pooled = {}
    for key, (cp, cq) in {"a_to_b": ("price_index_a", "units_b"),
                          "b_to_a": ("price_index_b", "units_a"),
                          "naive": ("price_index", "units")}.items():
        X, Y = [], []
        for f in fams:
            xs, ys = series(f, cp, cq)
            X += xs
            Y += ys
        r = ols(X, Y)
        if r:
            b, se, n = r
            pooled[key] = {"beta": round(b, 3), "se": round(se, 3), "n": n,
                           "lo": round(b - 1.96 * se, 3), "hi": round(b + 1.96 * se, 3)}

    cross_mean = None
    if "a_to_b" in pooled and "b_to_a" in pooled:
        cross_mean = round((pooled["a_to_b"]["beta"] + pooled["b_to_a"]["beta"]) / 2, 3)

    per = []
    for f in fams:
        xa, ya = series(f, "price_index_a", "units_b")
        xb, yb = series(f, "price_index_b", "units_a")
        ra, rb = ols(xa, ya), ols(xb, yb)
        vals = [r[0] for r in (ra, rb) if r]
        if not vals:
            continue
        per.append({"family": f, "cross": round(statistics.mean(vals), 2),
                    "n": (ra or rb)[2]})
    per.sort(key=lambda r: r["cross"])
    spread = (per[-1]["cross"] - per[0]["cross"]) if len(per) > 1 else None

    # Do the two store-halves agree? If their 95% intervals do not overlap, the
    # cross-half design is telling you the specification is wrong, not that it
    # has found an elasticity. In THIS simple pooling they do not overlap
    # (A->B -1.93, B->A +0.04), because pooling raw across families omits the
    # cluster controls price_models.py carries. That file's better-specified
    # version gets -0.819 and -0.518, which DO overlap, and it is the reference.
    a, b = pooled.get("a_to_b"), pooled.get("b_to_a")
    halves_agree = bool(a and b and a["lo"] <= b["hi"] and b["lo"] <= a["hi"])
    ident = bool(cross_mean is not None and halves_agree
                 and a and b and a["hi"] < 0 and b["hi"] < 0)
    return {
        "status": "ok",
        "pooled": pooled, "cross_mean": cross_mean, "per_family": per,
        "per_family_spread": round(spread, 2) if spread is not None else None,
        "identified": ident, "halves_agree": halves_agree,
        "reference": {
            "source": "data/scripts/price_models.py",
            "a_to_b": -0.819, "b_to_a": -0.518, "mean": -0.668, "n": 738,
            "note": "Better specified than the pooling here - it carries cluster "
                    "controls, and its two halves AGREE on [-1.27, -0.37]. Prefer it. "
                    "Its own verdict is still 'not identified at this grain'.",
        },
        "verdict": ("Not identified at this grain. In this simple pooling the two "
                    "store-halves do not even agree with each other "
                    f"({a['beta'] if a else '?'} vs {b['beta'] if b else '?'}), and the "
                    "per-family estimates range over "
                    f"{round(spread, 1) if spread else '?'} elasticity units on 72 "
                    "observations each. price_models.py's better-specified version gets "
                    "halves that DO agree, at a mean of -0.668, and still concludes the "
                    "interval is too wide to act on. Read the sign, not the magnitude."),
        "note": "Per-family rows are shown as evidence of instability, NOT as estimates. "
                "Neither number is causal: retailers set price in response to demand.",
        "needs": ["a promotion instrument, or SKU x store x week, to identify this properly"],
    }


# =================================================== 5. STATED vs REVEALED ==
def t5_stated(skus):
    """Do Mintel's stated concept interest and motivations track real sales?

    Survey and POS are genuinely independent instruments, so agreement is
    evidence and disagreement is a finding. Matching is by keyword from the
    concept text onto SKU descriptions, which is crude - reported as a rank
    correlation over a handful of concepts, never as a point estimate.
    """
    ci = os.path.join(MKT, "concept_interest.csv")
    mo = os.path.join(MKT, "motivations.csv")
    if not os.path.exists(ci):
        return {"status": "blocked", "needs": ["data/market/concept_interest.csv"]}
    live = [p for p in skus if alive(p)]
    tot = sum(p["rev"] for p in live)

    CONCEPT_RX = [
        ("functional benefit", r"immun|hydrat|electrolyte|vitamin|collagen|brain|focus"),
        ("sugar free",         r"zero sugar|sugar ?free|no sugar|diet"),
        ("natural",            r"organic|natural|plant|clean"),
        ("protein",            r"protein|amino|bcaa"),
        ("tea or coffee",      r"\btea\b|coffee|matcha|yerba|espresso"),
        ("performance",        r"pre.?workout|performance|pump|strength|endur"),
    ]
    rows = []
    for r in csv.DictReader(open(ci)):
        txt = r["concept"].lower()
        for name, pat in CONCEPT_RX:
            if re.search(pat, txt):
                hit = [p for p in live if re.search(pat, p["desc"], re.I)]
                rows.append({
                    "concept": r["concept"][:80], "matched_as": name,
                    "interest_pct": float(r["interest_pct"]),
                    "rev_share": round(100 * sum(p["rev"] for p in hit) / tot, 2),
                    "skus": len(hit),
                })
                break
    # A rank correlation over four concepts is noise with a decimal point on it.
    # The first run of this panel returned rho = -0.949 on n=4 and that number
    # meant nothing. Six is still few; below that it is not reported at all.
    rho = (spearman([r["interest_pct"] for r in rows], [r["rev_share"] for r in rows])
           if len(rows) >= 6 else float("nan"))
    motiv = []
    if os.path.exists(mo):
        motiv = [{"factor": r["factor"], "top2box_pct": float(r["top2box_pct"])}
                 for r in csv.DictReader(open(mo))]
    detectable = sum(r["skus"] for r in rows)
    return {
        "status": "partial",
        "rows": rows, "motivations": motiv[:12],
        "spearman": None if rho != rho else round(rho, 3),
        "n": len(rows), "skus_matched": detectable,
        "note": "The survey side is real and is reported as measured. The SALES side is "
                "not comparable to it: concepts are matched by keyword onto PDI "
                "descriptions, which are terse (median 41 characters, and the largest "
                "SKUs in the file are literally 'MONSTER' and 'RED BULL'), so the "
                "revenue shares below are a floor set by what is detectable, not a "
                "measure of the concept's real footprint.",
        "caveat": f"Only {len(rows)} concepts matched at all. No rank correlation is "
                  "reported below six, and the one comparison this panel can honestly "
                  "make is between concepts, not between a concept and the market.",
        "needs": ["a product attribute source richer than PDI descriptions (GNPD "
                  "product-level, or manufacturer spec sheets) before stated interest "
                  "can be scored against revealed sales"],
    }


# ============================================================= 6. SURVIVAL ==
def t6_survival(skus):
    """Which SKUs are still selling at the end of the window, and what predicts it.

    NOT the year-3 $100K bar in predict_launch.py - that needs the untracked
    pdi_gtin_by_year.csv. The target here is SURVIVAL TO DATE: a last sale
    within ALIVE_MONTHS of the window end. It is a weaker question and is
    labelled as one.

    The obvious leak is guarded: lifetime revenue is a legitimate predictor
    (bigger SKUs survive) but a SKU that died early necessarily accumulated less,
    so revenue is partly the outcome. Scale features are therefore reported
    alongside a distribution-only model, and the gap between them is the honest
    read on how much of the AUC is circular.
    """
    pool = [p for p in skus if p["stores"] >= MIN_STORES]
    brand_rev = collections.defaultdict(float)
    brand_n = collections.Counter()
    for p in skus:
        brand_rev[p["brand"]] += p["rev"]
        brand_n[p["brand"]] += 1
    y = [1 if alive(p) else 0 for p in pool]

    def fit(featfn, label):
        X = [featfn(p) for p in pool]
        mu = [statistics.mean(c) for c in zip(*X)]
        sd = [statistics.pstdev(c) or 1.0 for c in zip(*X)]
        Z = [[(v - mu[j]) / sd[j] for j, v in enumerate(r)] for r in X]
        rng = random.Random(7)
        idx = list(range(len(Z)))
        rng.shuffle(idx)
        folds = 5
        scores = [0.0] * len(Z)
        for f in range(folds):
            te = set(idx[f::folds])
            tr = [i for i in idx if i not in te]
            w = [0.0] * (len(Z[0]) + 1)
            for _ in range(320):
                g = [0.0] * len(w)
                for i in tr:
                    z = 1 / (1 + math.exp(-max(-30, min(30, predict(w, Z[i])))))
                    e = z - y[i]
                    g[0] += e
                    for j, v in enumerate(Z[i]):
                        g[j + 1] += e * v
                lam = 1.0
                for j in range(len(w)):
                    pen = lam * w[j] if j else 0.0
                    w[j] -= 0.12 * (g[j] + pen) / len(tr)
            for i in te:
                scores[i] = predict(w, Z[i])
        return {"label": label, "auc": round(auc(scores, y), 3)}

    full = fit(lambda p: [math.log(p["rev"]), math.log(p["stores"]),
                          math.log(brand_rev[p["brand"]] + 1), brand_n[p["brand"]],
                          size_oz(p["size"]) or 12.0], "scale + brand + size")
    dist = fit(lambda p: [math.log(p["stores"])], "distribution only")
    brand = fit(lambda p: [math.log(brand_rev[p["brand"]] + 1), brand_n[p["brand"]]],
                "brand only")
    base = sum(y) / len(y)
    byfam = []
    for fam in sorted({p["family"] for p in pool}):
        sub = [p for p in pool if p["family"] == fam]
        if len(sub) < 20:
            continue
        byfam.append({"family": fam, "n": len(sub),
                      "survival_pct": round(100 * sum(1 for p in sub if alive(p)) / len(sub), 1)})
    byfam.sort(key=lambda r: -r["survival_pct"])
    return {
        "status": "ok", "n": len(pool), "base_rate": round(base, 3),
        "models": [full, dist, brand], "by_family": byfam,
        "note": "Target is survival to the window end, not year-3 revenue. Lifetime "
                "revenue is partly an outcome, so compare the full model against the "
                "distribution-only row before believing the AUC.",
        "needs": ["data/bq/pdi_gtin_by_year.csv for the year-3 $100K target"],
    }


# ====================================================== 7. CANNIBALIZATION ==
CANNIBAL_SQL = """-- Staggered difference-in-differences: when a brand adds a flavor to a STORE,
-- what happens to that brand's OTHER SKUs in the same store?
-- Whitespace that steals from your own shelf is not whitespace.
WITH first_seen AS (
  SELECT d.STORE_ID, m.BRAND, m.GTIN, MIN(d.DATE) AS launch
  FROM `PROJECT.energy_drinks.pdi_daily_agg` d
  JOIN `PROJECT.energy_drinks.pdi_master_gtin` m USING (GTIN)
  WHERE d.DATE BETWEEN '2019-01-01' AND '2025-12-31'
  GROUP BY 1,2,3
), weekly AS (
  SELECT d.STORE_ID, m.BRAND, m.GTIN,
         DATE_TRUNC(d.DATE, WEEK) AS wk,
         SUM(d.QUANTITY) AS units, SUM(d.TOTAL_REVENUE_AMOUNT) AS rev
  FROM `PROJECT.energy_drinks.pdi_daily_agg` d
  JOIN `PROJECT.energy_drinks.pdi_master_gtin` m USING (GTIN)
  WHERE d.DATE BETWEEN '2019-01-01' AND '2025-12-31'
  GROUP BY 1,2,3,4
)
SELECT w.STORE_ID, w.BRAND, w.wk, f.launch, w.GTIN, w.units, w.rev
FROM weekly w JOIN first_seen f USING (STORE_ID, BRAND, GTIN);
-- Estimate with Callaway-Sant'Anna (never two-way fixed effects: with staggered
-- adoption and heterogeneous effects, TWFE uses already-treated stores as
-- controls and the estimate can flip sign). Store x brand fixed effects; the
-- outcome is the incumbent SKUs' units, not the new SKU's."""

GEO_SQL = """-- Store-level flavor over/under-indexing. Which markets want what.
SELECT d.STORE_ID,
       m.FLAVOR, m.BRAND,
       SUM(d.QUANTITY)             AS units,
       SUM(d.TOTAL_REVENUE_AMOUNT) AS rev
FROM `PROJECT.energy_drinks.pdi_daily_agg` d
JOIN `PROJECT.energy_drinks.pdi_master_gtin` m USING (GTIN)
WHERE d.DATE BETWEEN '2024-01-01' AND '2025-12-31'
GROUP BY 1,2,3;
-- STORE_ID carries no geography in pdi_daily_agg, so this needs a store->market
-- crosswalk (banner, ZIP or DMA) before it can be mapped. data/osm/ holds
-- bottling candidates only, not the retail estate."""


def t7_cannibalization():
    return {
        "status": "blocked",
        "question": "When a brand adds a flavor to a store, what happens to its other "
                    "SKUs in that same store?",
        "model": "Staggered difference-in-differences (Callaway-Sant'Anna), store x brand "
                 "fixed effects, incumbent-SKU units as the outcome.",
        "needs": ["a store x SKU x week scan of pdi_daily_agg",
                  "no gcloud/bq client is installed in this container"],
        "cost": "~$0.35-0.55 per full scan of the 420 GB table - dry-run first",
        "sql": CANNIBAL_SQL,
    }


def t8_geographic():
    return {
        "status": "blocked",
        "question": "Which store clusters over-index on which flavors, so a launch can "
                    "be aimed at markets rather than at the whole chain?",
        "model": "Mixed-effects on store x flavor share residuals, or k-means over store "
                 "flavor vectors.",
        "needs": ["STORE_ID x flavor aggregation from pdi_daily_agg",
                  "a store -> market crosswalk (banner / ZIP / DMA); data/osm/ carries "
                  "bottling candidates only, not the retail estate"],
        "cost": "~$0.35-0.55 per full scan - dry-run first",
        "sql": GEO_SQL,
    }


# ================================================== 9. AUDIENCE x FLAVOR ==
def t9_matrix(skus):
    """Audience x flavor family, scored on revenue per SKU.

    Revenue per SKU is the headroom measure the opportunity page already uses:
    a cell with $25M across 33 SKUs is a better place to launch than one with
    $80M across 86, because the second is already fought over. This view adds
    the survival rate and the median store count per cell, which separate
    "nobody has tried it" from "people tried it and it died".
    """
    live = [p for p in skus if p["stores"] >= MIN_STORES]
    cells = collections.defaultdict(list)
    for p in live:
        cells[(p["aud"], p["family"])].append(p)
    auds = sorted({p["aud"] for p in live})
    fams = sorted({p["family"] for p in live})
    rows = []
    for (a, f), ps in cells.items():
        if len(ps) < 3:
            continue
        rev = sum(p["rev"] for p in ps)
        rows.append({
            "aud": a, "family": f, "skus": len(ps), "rev": round(rev, 0),
            "rev_per_sku": round(rev / len(ps), 0),
            "survival_pct": round(100 * sum(1 for p in ps if alive(p)) / len(ps), 1),
            "med_stores": int(statistics.median([p["stores"] for p in ps])),
        })
    rows.sort(key=lambda r: -r["rev_per_sku"])
    thin = [r for r in rows if r["skus"] <= 8 and r["survival_pct"] >= 60]
    thin.sort(key=lambda r: -r["rev_per_sku"])
    return {
        "status": "ok", "auds": auds, "families": fams, "rows": rows,
        "thin": thin[:15], "n": len(live),
        "note": "Extends the White Space Finder on the opportunity page by adding "
                "survival rate and median distribution per cell.",
    }


# ============================================================ 10. NUTRITION ==
def t10_nutrition():
    """Sugar x caffeine positioning. GATED: the committed file is sample data.

    data/openfoodfacts/products.csv is generated by generate_sample_data.py so
    the dashboard renders offline (its README says so). Fitting anything to it
    and reporting the result as a finding would be fabrication, so this panel
    ships the mechanism and the row count and refuses to draw a conclusion.
    """
    n = 0
    if os.path.exists(OFF):
        n = sum(1 for _ in csv.DictReader(open(OFF)))
    return {
        "status": "sample",
        "rows_in_sample": n,
        "question": "Which sugar x caffeine coordinates are crowded and which are empty, "
                    "once each point is weighted by real sales?",
        "model": "2-D kernel density over (sugar/100ml, caffeine/100ml) weighted by PDI "
                 "revenue; empty high-density-demand regions are the whitespace.",
        "needs": ["python data/scrapers/openfoodfacts.py where network is allowed "
                  "(this container's egress denies it), then rebuild"],
        "warning": "The committed CSV is GENERATED SAMPLE data. No numbers are reported "
                   "from it; doing so would fabricate a finding.",
    }


# ------------------------------------------------------------------- driver --
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(AGG):
        sys.exit(f"missing {AGG}")
    agg, skus = load_skus()

    panels = {
        "velocity": t1_velocity(skus),
        "attributes": t2_attributes(skus),
        "claims": t3_claims(skus),
        "elasticity": t4_elasticity(),
        "stated": t5_stated(skus),
        "survival": t6_survival(skus),
        "cannibalization": t7_cannibalization(),
        "geographic": t8_geographic(),
        "matrix": t9_matrix(skus),
        "nutrition": t10_nutrition(),
    }
    out = {
        "generated_at": agg.get("generated_at"),
        "window": agg["audiences"].get("window"),
        "coverage": "PDI convenience channel only, and roughly 8.6% of that channel. "
                    "Not total market.",
        "skus": len(skus),
        "alive_rule": f"last sale within {ALIVE_MONTHS} months of {WINDOW_END}",
        "min_stores": MIN_STORES,
        "panels": panels,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}  ({size/1024:.0f} KB, {len(skus)} SKUs)")
    for k, v in panels.items():
        print(f"  {k:18} {v['status']}")
    if args.report:
        print()
        for k, v in panels.items():
            if v["status"] == "ok":
                keys = [x for x in v if x not in ("status", "note", "needs")]
                print(f"{k}: {', '.join(f'{x}={v[x]}' for x in keys if not isinstance(v[x], (list, dict)))}")


if __name__ == "__main__":
    main()
