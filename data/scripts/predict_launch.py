#!/usr/bin/env python3
"""Predictive model: will a launch still matter in year three?

Why a model at all
------------------
The site already forecasts the market (damped extrapolation, back-tested) and
simulates a launch (bootstrap over comparables). Neither DISCRIMINATES. The
simulator says what the range of outcomes looks like for a pocket; it cannot say
that this launch is more promising than that one, because every trial is drawn
from the same pool. That is the gap this fills.

Two outcomes, both measured three years after launch, both on ABSOLUTE bars:

  PRESENT    at least $10K of revenue in year 3. Base rate ~50%.
  MATTERS    at least $100K of revenue in year 3. Base rate ~7%.

The peak-relative "still at 10% of its own peak" rule used elsewhere on this
site is deliberately NOT the target here, and the first run showed exactly why:
against it, year-one revenue came out as the strongest feature with a NEGATIVE
coefficient - bigger first year, worse odds. That is not a finding, it is the
artifact already documented in add_survival.py. A target defined relative to a
SKU's own peak penalises products that peak early, and year-one revenue is
partly what sets the peak. The predictor and the outcome shared a term. Absolute
bars share nothing, so a positive coefficient means what it appears to mean.

Features, all observable BEFORE the outcome
-------------------------------------------
Leakage is the way a model like this flatters itself, so every feature is fixed
at launch or at the end of year one:

  r1        log1p of year-one revenue
  brand_rev log1p of the brand's revenue in the year BEFORE launch
  brand_n   how many SKUs that brand had selling the year before
  fam_rev   log1p of the flavor family's revenue the year before launch
  size_oz   pack size in ounces

Deliberately NOT included: anything derived from the outcome window, and any
target-encoded category (e.g. "this flavor's historical success rate"), which
leaks through the fold boundary unless it is recomputed inside each fold. With
30 positive events on the SCALED outcome there is not enough data to do that
safely, so it is left out rather than done badly.

How it is judged
----------------
Cross-validated AUC against two baselines that must be beaten to be worth
anything:

  * the base rate (AUC 0.5 by construction)
  * year-one revenue alone, which the survival work already showed is a usable
    gate. A five-feature model that cannot beat one number is not a model.

Also reported: Brier score for calibration, and a permutation importance so the
model is not a black box. With n in the hundreds and events in the tens, this is
a small-data problem and the honest output may well be "barely better than the
one-variable gate" - which is stated rather than hidden.

    python data/scripts/predict_launch.py
    python data/scripts/predict_launch.py --write

stdlib only.
"""
import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_survival import load, FIRST_COHORT, LAST_COMPLETE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGG = os.path.join(ROOT, "public/data/dashboard.json")

PRESENT_Y3 = 10_000    # "still on shelf": revenue in year three
MATTERS_Y3 = 100_000   # "still matters": revenue in year three
FOLDS = 5
SEED = 20260817

FEATURES = ["r1", "brand_rev", "brand_n", "fam_rev", "size_oz"]
NICE = {
    "r1": "Year-one revenue",
    "brand_rev": "Brand's revenue before launch",
    "brand_n": "Brand's SKU count before launch",
    "fam_rev": "Flavor family size before launch",
    "size_oz": "Pack size (oz)",
}


def build():
    """One row per launch whose year-three outcome is observable."""
    sk = [s for s in load()
          if FIRST_COHORT <= s["launch"] <= LAST_COMPLETE
          and s["first_seen"] >= FIRST_COHORT - 1
          and s["launch"] + 3 <= LAST_COMPLETE]

    # Context features: brand and flavor scale in each year, from every SKU we
    # have, not only the launch cohort.
    brand_rev = defaultdict(lambda: defaultdict(float))
    brand_n = defaultdict(lambda: defaultdict(int))
    fam_rev = defaultdict(lambda: defaultdict(float))
    for s in load():
        for y, v in s["rev"].items():
            if v <= 0:
                continue
            brand_rev[s["brand"]][y] += v
            brand_n[s["brand"]][y] += 1
            fam_rev[s["fam"]][y] += v

    rows = []
    for s in sk:
        ly = s["launch"]
        oz = 0.0
        for tok in (s["size"] or "").replace("OZ", " ").split():
            try:
                oz = float(tok)
                break
            except ValueError:
                continue
        r1 = s["rev"].get(ly, 0.0)
        y3 = s["rev"].get(ly + 3, 0.0)
        rows.append({
            "x": [
                math.log1p(r1),
                math.log1p(brand_rev[s["brand"]].get(ly - 1, 0.0)),
                float(brand_n[s["brand"]].get(ly - 1, 0)),
                math.log1p(fam_rev[s["fam"]].get(ly - 1, 0.0)),
                oz,
            ],
            "present": 1 if y3 >= PRESENT_Y3 else 0,
            "matters": 1 if y3 >= MATTERS_Y3 else 0,
            "r1": r1,
            "cohort": ly,
            "aud": s["aud"], "fam": s["fam"], "brand": s["brand"],
        })
    return rows


# ------------------------------------------------------------ logistic ----
def fit(X, y, l2=1.0, iters=4000, lr=0.08):
    """Plain gradient descent on standardised features. Small data, so L2 matters."""
    n, d = len(X), len(X[0])
    mu = [sum(r[j] for r in X) / n for j in range(d)]
    sd = [max(math.sqrt(sum((r[j] - mu[j]) ** 2 for r in X) / n), 1e-9) for j in range(d)]
    Z = [[(r[j] - mu[j]) / sd[j] for j in range(d)] for r in X]

    w = [0.0] * d
    b = math.log((sum(y) + 0.5) / (n - sum(y) + 0.5))
    for _ in range(iters):
        gw = [0.0] * d
        gb = 0.0
        for zi, yi in zip(Z, y):
            p = 1 / (1 + math.exp(-max(-30, min(30, b + sum(w[j] * zi[j] for j in range(d))))))
            e = p - yi
            gb += e
            for j in range(d):
                gw[j] += e * zi[j]
        b -= lr * gb / n
        for j in range(d):
            w[j] -= lr * (gw[j] / n + l2 * w[j] / n)
    return {"w": w, "b": b, "mu": mu, "sd": sd}


def predict(m, x):
    z = sum(m["w"][j] * (x[j] - m["mu"][j]) / m["sd"][j] for j in range(len(x)))
    return 1 / (1 + math.exp(-max(-30, min(30, m["b"] + z))))


def auc(y, p):
    """Rank-based AUC with ties handled by average rank."""
    pairs = sorted(zip(p, y))
    ranks, i = [0.0] * len(pairs), 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    pos = sum(1 for _, yi in pairs if yi == 1)
    neg = len(pairs) - pos
    if pos == 0 or neg == 0:
        return None
    s = sum(r for r, (_, yi) in zip(ranks, pairs) if yi == 1)
    return (s - pos * (pos + 1) / 2) / (pos * neg)


def folds(rows, k, seed):
    """Stratified by outcome so a rare-event fold is not all negatives."""
    rnd = seed
    def nxt():
        nonlocal rnd
        rnd = (1103515245 * rnd + 12345) % (1 << 31)
        return rnd / (1 << 31)
    idx = list(range(len(rows)))
    idx.sort(key=lambda i: nxt())
    out = [[] for _ in range(k)]
    for cls in (0, 1):
        c = [i for i in idx if rows[i]["_y"] == cls]
        for n, i in enumerate(c):
            out[n % k].append(i)
    return out


def auc_ci(y, p, boots=400, seed=7):
    """Bootstrap CI on AUC. With 30 events a point estimate implies a precision
    the data does not have; the interval is the honest version."""
    rnd = seed
    def nxt():
        nonlocal rnd
        rnd = (1103515245 * rnd + 12345) % (1 << 31)
        return rnd / (1 << 31)
    n = len(y)
    vals = []
    for _ in range(boots):
        idx = [int(nxt() * n) for _ in range(n)]
        a = auc([y[i] for i in idx], [p[i] for i in idx])
        if a is not None:
            vals.append(a)
    vals.sort()
    if len(vals) < 20:
        return None, None
    return (round(vals[int(len(vals) * 0.025)], 3),
            round(vals[int(len(vals) * 0.975)], 3))


def cv(rows, target):
    for r in rows:
        r["_y"] = r[target]
    fs = folds(rows, FOLDS, SEED)
    yy, pp, pp1 = [], [], []
    for f in range(FOLDS):
        te = set(fs[f])
        tr = [r for i, r in enumerate(rows) if i not in te]
        if len({r["_y"] for r in tr}) < 2:
            continue
        m = fit([r["x"] for r in tr], [r["_y"] for r in tr])
        m1 = fit([[r["x"][0]] for r in tr], [r["_y"] for r in tr])   # year-one only
        for i in fs[f]:
            yy.append(rows[i]["_y"])
            pp.append(predict(m, rows[i]["x"]))
            pp1.append(predict(m1, [rows[i]["x"][0]]))
    brier = sum((p - y) ** 2 for p, y in zip(pp, yy)) / len(yy)
    lo, hi = auc_ci(yy, pp)
    return {
        "n": len(rows), "events": sum(yy), "base": sum(yy) / len(yy) * 100,
        "auc": auc(yy, pp), "auc_lo": lo, "auc_hi": hi,
        "auc_r1_only": auc(yy, pp1), "brier": brier,
        "epv": round(sum(yy) / len(FEATURES), 1),
        "y": yy, "p": pp,
    }


def importance(rows, target):
    """Permutation importance: how much AUC is lost when one feature is shuffled."""
    for r in rows:
        r["_y"] = r[target]
    m = fit([r["x"] for r in rows], [r["_y"] for r in rows])
    y = [r["_y"] for r in rows]
    base = auc(y, [predict(m, r["x"]) for r in rows])
    out = []
    for j, name in enumerate(FEATURES):
        vals = [r["x"][j] for r in rows]
        shifted = vals[len(vals) // 3:] + vals[:len(vals) // 3]      # deterministic shuffle
        pj = [predict(m, [v if k != j else shifted[i] for k, v in enumerate(r["x"])])
              for i, r in enumerate(rows)]
        out.append({"feature": name, "label": NICE[name],
                    "drop": round((base - auc(y, pj)) * 100, 1),
                    "coef": round(m["w"][j], 3)})
    out.sort(key=lambda d: -d["drop"])
    return {"base_auc": round(base, 3), "features": out}


def calibration(res, bins=5):
    """Predicted vs actual, in bins. A model that ranks well can still be miscalibrated."""
    pairs = sorted(zip(res["p"], res["y"]))
    out = []
    step = max(1, len(pairs) // bins)
    for i in range(0, len(pairs), step):
        chunk = pairs[i:i + step]
        if len(chunk) < 5:
            continue
        out.append({"n": len(chunk),
                    "pred": round(sum(p for p, _ in chunk) / len(chunk) * 100, 1),
                    "actual": round(sum(y for _, y in chunk) / len(chunk) * 100, 1)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rows = build()
    print(f"launches with an observable year-3 outcome: {len(rows)} "
          f"(cohorts {min(r['cohort'] for r in rows)}-{max(r['cohort'] for r in rows)})")

    out = {"n": len(rows), "folds": FOLDS, "features": FEATURES,
           "labels": NICE, "present_y3": PRESENT_Y3, "matters_y3": MATTERS_Y3, "models": {}}

    for target, title in (("present", f"AT LEAST ${PRESENT_Y3:,} IN YEAR 3"),
                          ("matters", f"AT LEAST ${MATTERS_Y3:,} IN YEAR 3")):
        res = cv(rows, target)
        imp = importance(rows, target)
        cal = calibration(res)
        lift = (res["auc"] - 0.5) / max(res["auc_r1_only"] - 0.5, 1e-9)
        print(f"\n{title}")
        print(f"  events {res['events']}/{res['n']}  base rate {res['base']:.1f}%")
        print(f"  AUC  full model {res['auc']:.3f} [{res['auc_lo']}-{res['auc_hi']}]"
              f"   year-one only {res['auc_r1_only']:.3f}   (lift x{lift:.2f})")
        print(f"  events per variable {res['epv']}"
              + ("   << below 10, treat coefficients as indicative only" if res['epv'] < 10 else ""))
        print(f"  Brier {res['brier']:.4f}")
        print("  permutation importance (AUC points lost when shuffled):")
        for f in imp["features"]:
            print(f"    {f['label']:<34} {f['drop']:+5.1f}   coef {f['coef']:+.3f}")
        print("  calibration:")
        for c in cal:
            print(f"    predicted {c['pred']:5.1f}%   actual {c['actual']:5.1f}%   n={c['n']}")

        out["models"][target] = {
            "title": title,
            "n": res["n"], "events": res["events"], "base": round(res["base"], 1),
            "auc": round(res["auc"], 3), "auc_lo": res["auc_lo"], "auc_hi": res["auc_hi"],
            "auc_r1_only": round(res["auc_r1_only"], 3), "epv": res["epv"],
            "brier": round(res["brier"], 4),
            "importance": imp["features"], "calibration": cal,
        }

    if args.write:
        with open(AGG) as f:
            agg = json.load(f)
        agg["audiences"]["opportunity"]["predict"] = out
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote predict -> {AGG}")


if __name__ == "__main__":
    main()
