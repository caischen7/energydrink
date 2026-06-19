#!/usr/bin/env python3
"""
Pull Google Trends search-interest momentum for tracked energy-drink brands.

Why this exists: the dashboard's only "momentum" signal today is YouTube
mention-share, which can spike from a single viral video. Search volume is a
cleaner proxy for actual consumer demand. This loader is NOT wired into
build_dashboard_json.py yet — run it, eyeball the output, then fold
trends/google_trends.csv into the aggregate (see data/README.md).

Google rate-limits aggressively from datacenter/CI IPs, so this is meant to
be run from a normal residential/office connection (your machine or Cloud
Shell), not from this sandbox.

  pip install pytrends
  python data/scripts/fetch_google_trends.py
"""
import csv
import os
import time

from pytrends.request import TrendReq

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "trends", "google_trends.csv")

# pytrends caps at 5 terms per request; batch the tracked brands.
BRANDS = [
    "Red Bull", "Monster Energy", "Celsius energy drink", "Bang Energy",
    "Reign Total Body Fuel", "C4 Energy", "Alani Nu", "Ghost Energy",
    "Prime Energy", "5 hour Energy", "NOS energy drink", "Rockstar Energy",
    "Zoa Energy", "G Fuel", "Zipfizz",
]
TIMEFRAME = "today 5-y"
GEO = "US"


def batches(items, n):
    for i in range(0, len(items), n):
        yield items[i : i + n]


def main():
    pytrends = TrendReq(hl="en-US", tz=360)
    rows = []
    for batch in batches(BRANDS, 5):
        pytrends.build_payload(batch, timeframe=TIMEFRAME, geo=GEO)
        df = pytrends.interest_over_time()
        if df.empty:
            print(f"  ! no data for {batch}")
            continue
        for ts, row in df.iterrows():
            for brand in batch:
                rows.append((brand, ts.strftime("%Y-%m-%d"), int(row[brand])))
        time.sleep(2)  # be polite between batches

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["brand", "week", "interest_index"])
        w.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
