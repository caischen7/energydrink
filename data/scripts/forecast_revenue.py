#!/usr/bin/env python3
"""Forecast audience REVENUE to 2030, and let the back-test pick the method.

Why revenue rather than share
-----------------------------
The existing projection forecasts each audience's SHARE and multiplies by
Mintel's market total. That has a structural problem: shares are normalised to
100%, so they are zero-sum by construction. One audience cannot be revised
without moving every other, and "young adults lose 8.9 points" is then just the
arithmetic mirror of "women gain 9.2" rather than an independent finding.

Forecasting dollars directly removes that coupling. Each audience gets its own
curve, fitted to its own history, and the results are allowed to disagree with
the market total - which is informative, because the size of the disagreement
is a check on the whole exercise.

Why the method is chosen by back-test
-------------------------------------
The current approach is damped linear extrapolation, and docs/ASSUMPTIONS.md
records it as assumption S2, marked "Yes - failed": fit 2017-21, predict 2025,
mean absolute error 5.1pp with 9pp misses on both women and gym. The stated fix
is "rebuilding on a saturating curve rather than damped linear".

So rather than assert a replacement, this fits four candidates and scores them
all on held-out years:

    linear        ordinary least squares on dollars
    damped        linear with the 15%/yr damping the current method uses
    cagr          constant growth rate, compounding
    logistic      saturating S-curve, fitted by grid search on the ceiling

The back-test trains on everything up to a cut year and predicts the rest. The
winner is whichever has the lowest mean absolute percentage error out of sample,
per audience - not one method imposed on all of them. Audiences behave
differently: an incumbent near saturation and a challenger compounding off a
small base should not share a functional form.

Input is data/bq/derived/audience_revenue_series.csv, itself derived from
Euromonitor Passport brand shares x Mintel market size. Passport's Alani Nu
rows are split across two owners (Congo Brands to 2024, Celsius Holdings from
2025) and are summed before use - taking either row alone loses half the
history.

    python data/scripts/forecast_revenue.py
    python data/scripts/forecast_revenue.py --write

stdlib only.
"""
import argparse
import csv
import json
import math
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data/bq/derived/audience_revenue_series.csv")
AGG = os.path.join(ROOT, "public/data/dashboard.json")

TARGET = 2030
CUT = 2023          # back-test: train <= CUT, predict > CUT
MARKET_2030 = 38600.52


# ------------------------------------------------------------- methods ----
def linear(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
    a = my - b * mx
    return lambda x: a + b * x


def damped(xs, ys, k=0.85):
    """Linear slope, damped k per year beyond the last observation."""
    f = linear(xs, ys)
    x1 = max(xs)
    slope = f(x1) - f(x1 - 1)
    y1 = ys[xs.index(x1)]

    def g(x):
        if x <= x1:
            return f(x)
        return y1 + sum(slope * k ** i for i in range(1, int(x - x1) + 1))
    return g


def cagr(xs, ys):
    x0, x1 = min(xs), max(xs)
    y0, y1 = ys[xs.index(x0)], ys[xs.index(x1)]
    if y0 <= 0 or y1 <= 0 or x1 == x0:
        return linear(xs, ys)
    r = (y1 / y0) ** (1 / (x1 - x0))
    return lambda x: y1 * r ** (x - x1)


def logistic(xs, ys):
    """Saturating curve. Ceiling found by grid search, then a linear fit on the
    logit - enough for a 7-point series and honest about being a fit, not a
    theory of the market."""
    ymax = max(ys)
    best, bestsse = None, float("inf")
    for mult in [m / 20 for m in range(21, 81)]:          # ceiling 1.05x .. 4x peak
        L = ymax * mult
        pts = [(x, math.log(y / (L - y))) for x, y in zip(xs, ys) if 0 < y < L]
        if len(pts) < 3:
            continue
        f = linear([p[0] for p in pts], [p[1] for p in pts])
        sse = sum((y - L / (1 + math.exp(-f(x)))) ** 2 for x, y in zip(xs, ys))
        if sse < bestsse:
            bestsse, best = sse, (L, f)
    if not best:
        return linear(xs, ys)
    L, f = best
    return lambda x: L / (1 + math.exp(-max(-30, min(30, f(x)))))


METHODS = {"linear": linear, "damped": damped, "cagr": cagr, "logistic": logistic}


# ------------------------------------------------------------ backtest ----
def mape(actual, pred):
    pairs = [(a, p) for a, p in zip(actual, pred) if a > 0]
    if not pairs:
        return float("inf")
    return sum(abs(p - a) / a for a, p in pairs) / len(pairs) * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    series = defaultdict(dict)
    for r in csv.DictReader(open(SRC)):
        series[r["audience"]][int(r["year"])] = float(r["audience_usd_m"])

    print(f"back-test: train <= {CUT}, predict {CUT+1}..2025   (MAPE, out of sample)\n")
    print(f"{'audience':<30}" + "".join(f"{m:>11}" for m in METHODS) + f"{'winner':>12}")

    out, total_2030 = {}, 0.0
    for aud, ys in sorted(series.items(), key=lambda kv: -max(kv[1].values())):
        yrs = sorted(ys)
        tr = [y for y in yrs if y <= CUT]
        te = [y for y in yrs if y > CUT]
        # Women only enter Passport in 2021 (Celsius scales, Alani Nu appears),
        # so a 2023 cut leaves three training points. Excluding it for that
        # reason would drop the single audience the whole question is about;
        # it is kept and the thin history is reported instead of hidden.
        if len(tr) < 3 or not te:
            continue
        thin = len(tr) < 4
        scores = {}
        for name, fn in METHODS.items():
            try:
                f = fn(tr, [ys[y] for y in tr])
                scores[name] = mape([ys[y] for y in te], [f(y) for y in te])
            except Exception:                       # noqa: BLE001
                scores[name] = float("inf")
        win = min(scores, key=scores.get)
        print(f"{aud:<30}" + "".join(f"{scores[m]:>10.1f}%" for m in METHODS) + f"{win:>12}"
              + ("   ← only 3 training points" if thin else ""))

        # refit the winner on the full history, then project
        f = METHODS[win](yrs, [ys[y] for y in yrs])
        proj = max(0.0, f(TARGET))
        err = scores[win] / 100
        out[aud] = {
            "method": win,
            "mape": round(scores[win], 1),
            "n_years": len(yrs),
            "thin_history": thin,
            "y2025": round(ys[max(yrs)], 1),
            "y2030": round(proj, 1),
            "lo": round(proj * (1 - err), 1),
            "hi": round(proj * (1 + err), 1),
            "growth_pct": round((proj / ys[max(yrs)] - 1) * 100, 1) if ys[max(yrs)] else None,
            "all_scores": {m: (None if scores[m] == float("inf") else round(scores[m], 1))
                           for m in scores},
        }
        total_2030 += proj

    print(f"\n{'audience':<30}{'2025 $M':>10}{'2030 $M':>10}{'growth':>9}   90%-ish range")
    for aud, d in sorted(out.items(), key=lambda kv: -kv[1]["y2030"]):
        print(f"{aud:<30}{d['y2025']:>10,.0f}{d['y2030']:>10,.0f}{d['growth_pct']:>8.0f}%"
              f"   {d['lo']:,.0f} – {d['hi']:,.0f}  ({d['method']}, MAPE {d['mape']}%)")

    # The payoff: what the dollar model implies for share, next to the published
    # share-based split. Agreement is not guaranteed - the two were built from
    # opposite directions, one normalised to 100% and one not - so the gap is a
    # real check rather than a formality.
    # Published shares are of the WHOLE market; the model covers four audiences.
    # Renormalising the published split over the same four puts both on one base
    # - without that step the comparison is rigged, not informative.
    with open(AGG) as f:
        pub_auds = json.load(f)["audiences"]["demand"]["future"]["auds"]
    pub_raw = {a["name"]: a["share"] for a in pub_auds if a["name"] in out}
    pub_tot = sum(pub_raw.values())
    PUBLISHED_2030 = {k: v / pub_tot * 100 for k, v in pub_raw.items()} if pub_tot else {}

    print(f"\n{'audience':<30}{'implied share':>14}{'published':>11}{'gap':>8}")
    for aud, d in sorted(out.items(), key=lambda kv: -kv[1]["y2030"]):
        imp = d["y2030"] / total_2030 * 100
        pub = PUBLISHED_2030.get(aud)
        d["implied_share_2030"] = round(imp, 1)
        d["published_share_2030"] = pub
        if pub is None:
            print(f"{aud:<30}{imp:>13.1f}%{'-':>11}{'-':>8}")
        else:
            d["share_gap_pp"] = round(imp - pub, 1)
            print(f"{aud:<30}{imp:>13.1f}%{pub:>10.1f}%{imp - pub:>+7.1f}pp")
    print("(implied share is of the modelled audiences only, which is also what the\n"
          " published split covers - so the two are on the same base.)")

    covered = sum(d["y2025"] for d in out.values())
    print(f"\nmodelled audiences, 2030 total   ${total_2030:,.0f}M")
    print(f"Mintel's whole-market forecast    ${MARKET_2030:,.0f}M")
    print(f"these audiences are {covered/26947.3*100:.0f}% of the 2025 market, so the totals "
          f"are not meant to match;\nthe gap is the unmodelled tail (Others, private label, "
          f"unmapped brands).")

    if args.write:
        with open(AGG) as f:
            agg = json.load(f)
        agg["audiences"]["demand"]["revenue_forecast"] = {
            "target": TARGET, "cut": CUT, "audiences": out,
            "total_2030": round(total_2030, 1),
            "market_2030": MARKET_2030,
            "note": ("Dollars forecast per audience rather than shares normalised to 100%, so "
                     "audiences are not forced to trade points against each other. Method chosen "
                     "per audience by out-of-sample MAPE across linear, damped-linear, CAGR and "
                     "logistic; the range is that MAPE applied to the projection."),
        }
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote revenue_forecast -> {AGG}")


if __name__ == "__main__":
    main()
