#!/usr/bin/env python3
"""Put the Flavor Explorer's revenue levels on a per-active-store basis.

WHY
---
The PDI store panel grows 3.89x across 2019-2025 - 5,148 active stores in
2019-01 to 20,022 in 2025-12, with 2019 alone a 2.2x expansion. Category
revenue grew 3.52x over the same span while revenue per active store grew
1.58x, so roughly two thirds of the apparent growth is coverage rather than
demand.

The explorer plots monthly revenue LEVELS against search interest. On raw
dollars every flavor slopes up, because the panel is being filled in, and a
reader comparing that shape to a search curve is partly looking at PDI's sales
team. Dividing by the month's active-store count removes it.

WHAT THIS DOES AND DOES NOT CHANGE
----------------------------------
Adds `stores_active` (84 monthly values, aligned to `months`) to the payload so
the page can normalise client-side. It does NOT rewrite the revenue arrays:
the raw dollars stay exactly as measured, because for "how big is mango" the
measured total is the honest number and dividing a lifetime total by a store
count means nothing. What changes is the CHART and the CORRELATION, which are
about shape over time and are the two places coverage growth actively misleads.

The correlation is computed on month-over-month log change, where a smooth
coverage trend contributes little - but "little" is not "nothing", and it is
shared across every flavor, which is exactly the kind of common component that
manufactures agreement between two unrelated series.

Reads the store counts from data/bq/derived/price_panel.csv, which already
carries them, so this costs no BigQuery.

    python data/scripts/add_stores_to_explorer.py

stdlib only. Idempotent.
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(ROOT, "data/bq/derived/price_panel.csv")
TARGET = os.path.join(ROOT, "public/data/flavor_explorer.json")


def main():
    if not os.path.exists(PANEL):
        sys.exit(f"No {PANEL}. Run build_price_panel.py first (it carries the counts).")

    active = {}
    for r in csv.DictReader(open(PANEL)):
        v = r.get("stores_active")
        if v and v not in ("0", ""):
            active[r["month"]] = int(v)
    if not active:
        sys.exit("price_panel.csv has no stores_active column — rebuild it.")

    with open(TARGET) as f:
        payload = json.load(f)
    months = payload["months"]

    series = [active.get(m) for m in months]
    missing = [m for m, v in zip(months, series) if v is None]
    covered = [v for v in series if v]
    payload["stores_active"] = series
    payload["meta"]["coverage_ramp"] = (
        f"The PDI store panel grows from {min(covered):,} active stores to "
        f"{max(covered):,} across this window - {max(covered)/min(covered):.2f}x. "
        "Category revenue grew 3.52x over the same span while revenue per active "
        "store grew 1.58x, so about two thirds of the apparent growth is coverage "
        "rather than demand. The chart and the correlation are therefore computed "
        "per active store; the dollar totals are left as measured."
    )

    tmp = TARGET + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, TARGET)

    print(f"months               {len(months)}")
    print(f"store counts matched {len(covered)}"
          + (f"   MISSING {len(missing)}: {missing[:4]}" if missing else ""))
    print(f"range                {min(covered):,} -> {max(covered):,} "
          f"({max(covered)/min(covered):.2f}x)")
    print(f"wrote stores_active -> {TARGET}")


if __name__ == "__main__":
    main()
