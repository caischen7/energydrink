#!/usr/bin/env python3
"""Predict flavor sales from search interest — pipeline, baselines, honest scoring.

Status
------
Google Trends is blocked by this container's egress proxy (403 on CONNECT), so
this runs today against the YouTube chatter series as a stand-in and switches to
real search data the moment CSVs land in `data/trends/`. Nothing else changes:
the panel, the model and the scoring are identical either way, which is the
point of building it now.

    python data/scripts/trends_model.py                 # uses whatever is available
    python data/scripts/trends_model.py --source youtube
    python data/scripts/trends_model.py --write

THE CONSTRAINT THAT MATTERS MORE THAN TRENDS ACCESS
---------------------------------------------------
Google Trends is weekly. The PDI data committed here is GTIN x YEAR. Joining
them means throwing away 51 of every 52 search observations, leaving seven
annual points per flavor - and a seven-point series cannot support a model no
matter how good the search data is.

So the granularity of the SALES side, not the availability of the search side,
is the binding limit. Two ways out, in order of value:

  MONTHLY PDI (recommended). `pdi_daily_agg` in BigQuery has the detail; one
  aggregation to flavor x month over 2019-2025 gives ~84 periods x 13 families
  ~= 1,000 panel rows, which is a real modelling dataset. It is a single query
  with a partition filter, not a full scan - dry-run it first.

  YEARLY (what runs today). 13 families x 7 years = 91 rows before lagging,
  ~78 after. Enough to test whether a relationship exists at all; not enough to
  deploy a forecast against. This script reports at whichever granularity it
  finds, and says which one it used.

HOW IT IS SCORED
----------------
Two rules that decide whether any of this means anything:

1. TIME-BASED VALIDATION, NEVER RANDOM K-FOLD. Random folds let the model train
   on 2024 and test on 2022, which for a forecasting question is leakage
   dressed up as validation. This uses a rolling origin: train on everything up
   to year T, predict T+1, walk forward.

2. BEATEN BASELINES OR IT IS WORTHLESS. Two, both trivial and both hard to
   beat on short series:
       persistence  next change = 0 (share stays put)
       drift        next change = this flavor's mean historical change
   A model that cannot beat persistence out-of-sample has learned nothing, and
   that verdict is printed rather than buried.

stdlib only.
"""
import argparse
import csv
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flavor_trends as FT  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRENDS_DIR = os.path.join(ROOT, "data/trends")
AGG = os.path.join(ROOT, "public/data/dashboard.json")


# ------------------------------------------------------------- interest ----
def load_google_trends():
    """Parse Google Trends 'multiTimeline' exports from data/trends/.

    Expected: one CSV per search term, named for the flavor family it belongs
    to (e.g. `Berry.csv`, `Sour & candy.csv`), in Google's own export format:

        Category: All categories

        Week,berry energy drink: (United States)
        2019-01-06,72

    Both Week and Month exports are handled. Values are Google's 0-100 relative
    index, which is comparable WITHIN a term but not across terms - so the model
    below only ever uses within-term change, never levels across families.
    """
    out = defaultdict(dict)
    for path in sorted(glob.glob(os.path.join(TRENDS_DIR, "*.csv"))):
        fam = os.path.splitext(os.path.basename(path))[0]
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
        for r in rows:
            m = re.match(r"^(\d{4})-(\d{2})(?:-(\d{2}))?$", r[0].strip())
            if not m or len(r) < 2:
                continue
            try:
                v = float(re.sub(r"[^\d.]", "", r[1]) or 0)
            except ValueError:
                continue
            year = int(m.group(1))
            out[fam].setdefault(year, []).append(v)
    # Annual mean of the weekly index, so a year is not driven by one spike.
    return {f: {y: sum(v) / len(v) for y, v in d.items()} for f, d in out.items()}


def load_youtube():
    """Fallback interest series: flavor mentions per year, as a share of the year."""
    counts, _ = FT.chatter()
    return {f: {y: sh.get(f, 0.0) for y, sh in FT.shares(counts).items()}
            for f in {f for d in counts.values() for f in d}}


# ---------------------------------------------------------------- panel ----
def panel(interest, sales_share, years):
    """One row per (flavor, year) with the lags a forecast is allowed to use."""
    rows = []
    for fam in sorted(set(interest) & {f for y in years for f in sales_share.get(y, {})}):
        for i in range(1, len(years) - 1):
            t0, t1, t2 = years[i - 1], years[i], years[i + 1]
            it0, it1 = interest[fam].get(t0), interest[fam].get(t1)
            s0 = sales_share.get(t0, {}).get(fam)
            s1 = sales_share.get(t1, {}).get(fam)
            s2 = sales_share.get(t2, {}).get(fam)
            if None in (it0, it1, s0, s1, s2):
                continue
            rows.append({
                "fam": fam, "year": t2,
                # features known at t1, predicting the change into t2
                "d_int": it1 - it0,
                "d_sales_prev": s1 - s0,
                "level": s1,
                "y": s2 - s1,
            })
    return rows


# ---------------------------------------------------------------- model ----
def ridge(X, y, lam=1.0):
    """Closed-form ridge via Gaussian elimination. Few features, so this is fine."""
    n, d = len(X), len(X[0])
    Xb = [[1.0] + r for r in X]
    d1 = d + 1
    A = [[sum(Xb[i][a] * Xb[i][b] for i in range(n)) + (lam if a == b and a > 0 else 0.0)
          for b in range(d1)] for a in range(d1)]
    bvec = [sum(Xb[i][a] * y[i] for i in range(n)) for a in range(d1)]
    for c in range(d1):
        piv = max(range(c, d1), key=lambda r: abs(A[r][c]))
        if abs(A[piv][c]) < 1e-12:
            continue
        A[c], A[piv] = A[piv], A[c]
        bvec[c], bvec[piv] = bvec[piv], bvec[c]
        for r in range(d1):
            if r == c:
                continue
            f = A[r][c] / A[c][c]
            for k in range(c, d1):
                A[r][k] -= f * A[c][k]
            bvec[r] -= f * bvec[c]
    return [bvec[i] / A[i][i] if abs(A[i][i]) > 1e-12 else 0.0 for i in range(d1)]


def apply(w, x):
    return w[0] + sum(w[i + 1] * v for i, v in enumerate(x))


FEATS = ["d_int", "d_sales_prev", "level"]


def rolling_origin(rows):
    """Train on every year before T, predict T. Never the other way round."""
    years = sorted({r["year"] for r in rows})
    preds = {"model": [], "persist": [], "drift": [], "truth": [], "year": []}
    for t in years[1:]:
        tr = [r for r in rows if r["year"] < t]
        te = [r for r in rows if r["year"] == t]
        if len(tr) < 12 or not te:
            continue
        w = ridge([[r[f] for f in FEATS] for r in tr], [r["y"] for r in tr])
        hist = defaultdict(list)
        for r in tr:
            hist[r["fam"]].append(r["y"])
        for r in te:
            preds["model"].append(apply(w, [r[f] for f in FEATS]))
            preds["persist"].append(0.0)
            h = hist.get(r["fam"], [])
            preds["drift"].append(sum(h) / len(h) if h else 0.0)
            preds["truth"].append(r["y"])
            preds["year"].append(t)
    return preds


def score(truth, pred):
    n = len(truth)
    mae = sum(abs(a - b) for a, b in zip(truth, pred)) / n
    rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(truth, pred)) / n)
    return {"n": n, "mae": round(mae, 4), "rmse": round(rmse, 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["auto", "google", "youtube"], default="auto")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    gt = load_google_trends() if args.source in ("auto", "google") else {}
    if gt:
        interest, src = gt, "google-trends"
    elif args.source == "google":
        sys.exit(f"No Google Trends CSVs found in {TRENDS_DIR} — see the docstring.")
    else:
        interest, src = load_youtube(), "youtube-chatter (stand-in)"

    sales_share = FT.shares(FT.sales())
    years = [y for y in range(FT.FIRST_YEAR, FT.LAST_YEAR + 1) if y in sales_share]
    rows = panel(interest, sales_share, years)

    print(f"interest source : {src}")
    print(f"sales grain     : YEARLY  ({len(years)} periods {years[0]}-{years[-1]})")
    print(f"panel rows      : {len(rows)}  ({len({r['fam'] for r in rows})} flavor families)")
    if len(rows) < 30:
        print("\nToo few rows to score. This is the granularity problem, not a code problem.")
        return

    p = rolling_origin(rows)
    if not p["truth"]:
        print("\nNot enough history for a rolling-origin split.")
        return

    m = score(p["truth"], p["model"])
    per = score(p["truth"], p["persist"])
    dr = score(p["truth"], p["drift"])

    print(f"\nout-of-sample, rolling origin ({m['n']} predictions)")
    print(f"  model        MAE {m['mae']:.4f}  RMSE {m['rmse']:.4f}")
    print(f"  persistence  MAE {per['mae']:.4f}  RMSE {per['rmse']:.4f}")
    print(f"  drift        MAE {dr['mae']:.4f}  RMSE {dr['rmse']:.4f}")

    best = min((per["mae"], "persistence"), (dr["mae"], "drift"))
    verdict = ("beats both baselines" if m["mae"] < best[0]
               else f"does NOT beat {best[1]} — no usable signal at this granularity")
    print(f"  verdict      {verdict}")

    w = ridge([[r[f] for f in FEATS] for r in rows], [r["y"] for r in rows])
    print("\n  coefficients (full fit, for direction only):")
    for f, c in zip(FEATS, w[1:]):
        print(f"    {f:<14} {c:+.4f}")

    out = {
        "source": src, "grain": "yearly", "years": years,
        "rows": len(rows), "families": len({r["fam"] for r in rows}),
        "model": m, "persistence": per, "drift": dr,
        "beats_baseline": m["mae"] < best[0],
        "verdict": verdict,
        "coefficients": {f: round(c, 4) for f, c in zip(FEATS, w[1:])},
        "note": (
            "Rolling-origin validation: trained only on years before the one predicted. "
            "Random k-fold would let the model train on 2024 to predict 2022, which for a "
            "forecasting question is leakage. Scored against persistence (share stays put) "
            "and drift (this flavor's mean historical change), both of which are hard to "
            "beat on a seven-point annual series."
        ),
    }
    if args.write:
        with open(AGG) as f:
            agg = json.load(f)
        agg["audiences"]["opportunity"]["trend_model"] = out
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote trend_model -> {AGG}")


if __name__ == "__main__":
    main()
