#!/usr/bin/env python3
"""Merge collected Google Trends series into public/data/flavor_explorer.json.

Runs after `data/scrapers/google_trends.py --set explorer`, which writes one CSV
per search term into data/trends/explorer/. This reduces those weekly series to
the monthly grid the sales side uses and writes them into the `trends` block of
the explorer payload.

WEEKLY -> MONTHLY, AND WHY AVERAGE RATHER THAN SUM
--------------------------------------------------
Trends values are an INDEX, not a count. Summing four weekly index values would
produce a number that rises purely with the number of weeks in the month and
means nothing. The monthly value is the mean of that month's weeks, which keeps
it on the same 0-100 scale as its inputs.

Months with fewer than two observed weeks are left null rather than averaged
from a single point - a partial first or last month otherwise shows up as a
spike or a cliff at the edge of the chart.

THE COMPARABILITY RULE THIS FILE ENFORCES
-----------------------------------------
Each term is fetched in its own request, so each series is scaled to its own
maximum. Values are therefore comparable WITHIN a term across time and
meaningless BETWEEN terms: "mango" at 80 is not twice "grape" at 40. The
explorer never plots two different terms' search lines against each other, and
the correlation it reports is computed on month-over-month CHANGE within one
term, where self-normalisation cancels out.

    python data/scripts/add_trends_to_explorer.py

stdlib only.
"""
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRENDS_DIR = os.path.join(ROOT, "data/trends/explorer")
TARGET = os.path.join(ROOT, "public/data/flavor_explorer.json")

MIN_WEEKS_PER_MONTH = 2


def load_series(path):
    """Google's own export shape: a couple of header lines, then date,value."""
    by_month = defaultdict(list)
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.reader(f):
            if not r or len(r) < 2:
                continue
            m = re.match(r"^(\d{4})-(\d{2})", r[0].strip())
            if not m:
                continue
            try:
                v = float(re.sub(r"[^\d.]", "", r[1]) or 0)
            except ValueError:
                continue
            by_month[f"{m.group(1)}-{m.group(2)}"].append(v)
    return {k: sum(v) / len(v) for k, v in by_month.items()
            if len(v) >= MIN_WEEKS_PER_MONTH}


def main():
    if not os.path.isdir(TRENDS_DIR):
        sys.exit(f"No {TRENDS_DIR}. Run the Refresh Google Trends action first —\n"
                 "this container cannot reach trends.google.com (403 on CONNECT).")

    with open(TARGET) as f:
        payload = json.load(f)
    months = payload["months"]

    wanted = {t for d in payload["terms"].values() for t in d["trend_terms"]}
    found, out = 0, {}
    for path in sorted(glob.glob(os.path.join(TRENDS_DIR, "*.csv"))):
        # Filename is the search phrase with spaces as underscores.
        term = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
        if term not in wanted:
            print(f"  skip (not a registered term): {term}")
            continue
        s = load_series(path)
        out[term] = [round(s[m], 1) if m in s else None for m in months]
        cov = sum(1 for v in out[term] if v is not None)
        print(f"  {term:<34}{cov:>4}/{len(months)} months")
        found += 1

    payload["trends"] = out
    payload["meta"]["trends_note"] = (
        "Google Trends, US, monthly mean of weekly index. Each term is scaled to "
        "its own maximum, so values compare within a term over time and never "
        "between terms.")
    tmp = TARGET + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, TARGET)
    print(f"\n{found} search series merged -> {TARGET}")


if __name__ == "__main__":
    main()
