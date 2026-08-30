#!/usr/bin/env python3
"""Subtract PDI's own panel growth from the White Space matrix's growth badges.

THE PROBLEM
-----------
Each matrix cell shows a two-year growth rate to 2025, computed from PDI
convenience revenue. PDI's store panel is not fixed: it held 16,211 active
stores on average in 2023 and 19,064 in 2025, a coverage CAGR of 8.44%/yr over
exactly the window those badges cover. Every cell therefore carries roughly
+8.4pp that reflects PDI signing up stores rather than anyone buying more.

The effect is not cosmetic. Of 90 cells with a growth figure, 48 currently read
as growing. Net of panel growth only 34 do - 14 cells flip from growth to
decline - and the median cell goes from +2.0%/yr to -6.4%/yr.

THE CORRECTION, AND ITS LIMIT
-----------------------------
Log growth rates are additive, so subtracting the coverage rate is exact to
first order:

    g_net ~= g_observed - g_coverage

It is a UNIFORM correction. Coverage growth is common to the whole panel, so
this removes the average effect, not the cell-specific one: a flavor that
expanded into newly-added stores faster than average is still overstated, and
one that did not is understated. Doing better needs the growth recomputed on a
fixed store panel, which the GTIN x month rollup cannot reconstruct - it would
need store-level detail the aggregate deliberately does not carry.

So `cagr` is left untouched and `cagr_net` is written alongside it, with the
rate and window recorded. The page shows net and says what was subtracted.

    python data/scripts/net_of_panel_growth.py
    python data/scripts/net_of_panel_growth.py --write

stdlib only. Idempotent - it always recomputes from `cagr`, never from itself.
"""
import argparse
import collections
import csv
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(ROOT, "data/bq/derived/price_panel.csv")
AGG = os.path.join(ROOT, "public/data/dashboard.json")

# The window the matrix badges cover: "the 2-year rate to 2025".
FROM_YEAR, TO_YEAR, YEARS = "2023", "2025", 2


def coverage_cagr():
    per_year = collections.defaultdict(set)
    for r in csv.DictReader(open(PANEL)):
        v = r.get("stores_active")
        if v and v not in ("", "0"):
            per_year[r["month"][:4]].add(int(v))
    if FROM_YEAR not in per_year or TO_YEAR not in per_year:
        sys.exit("price_panel.csv does not cover the badge window")
    a = sum(per_year[FROM_YEAR]) / len(per_year[FROM_YEAR])
    b = sum(per_year[TO_YEAR]) / len(per_year[TO_YEAR])
    return a, b, ((b / a) ** (1 / YEARS) - 1) * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    a, b, rate = coverage_cagr()
    print(f"panel-active stores  {FROM_YEAR} {a:,.0f} -> {TO_YEAR} {b:,.0f}")
    print(f"coverage CAGR        {rate:.2f}%/yr over the same window as the badges\n")

    with open(AGG) as f:
        agg = json.load(f)
    O = agg["audiences"]["opportunity"]

    cells = [c for r in O["matrix"] for c in r["row"] if c.get("cagr") is not None]
    before = [c["cagr"] for c in cells]
    for c in cells:
        c["cagr_net"] = round(c["cagr"] - rate, 2)
    after = [c["cagr_net"] for c in cells]

    gp, gn = sum(1 for x in before if x > 0), sum(1 for x in after if x > 0)
    print(f"{'':<22}{'observed':>10}{'net':>10}")
    print(f"{'median cell':<22}{statistics.median(before):>9.1f}%{statistics.median(after):>9.1f}%")
    print(f"{'cells reading GROWTH':<22}{gp:>10}{gn:>10}")
    print(f"{'flip to decline':<22}{'':>10}{gp - gn:>10}")

    if args.write:
        O["panel_growth"] = {
            "rate": round(rate, 2), "from": FROM_YEAR, "to": TO_YEAR,
            "stores_from": round(a), "stores_to": round(b),
            "note": (f"PDI's store panel grew {rate:.1f}%/yr over the same window these "
                     f"growth figures cover ({a:,.0f} to {b:,.0f} active stores). That is "
                     "coverage, not demand, so it is subtracted. The correction is uniform: "
                     "it removes the average panel effect, not each cell's own exposure to "
                     "it, which would need a fixed-store-panel recomputation this aggregate "
                     "cannot support."),
        }
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote cagr_net on {len(cells)} cells + panel_growth -> {AGG}")


if __name__ == "__main__":
    main()
