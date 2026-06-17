"""
Pull Google Trends search interest for energy-drink brands + category terms,
to give the dashboard a TRUE search-momentum signal (the dashboard ships with a
content-volume proxy derived from our own data; this upgrades it).

Writes data/trends/google_trends.csv  (date, term, interest 0-100).

    pip install pytrends pandas
    python data/scripts/fetch_google_trends.py

Note: pytrends is an unofficial wrapper; Google rate-limits aggressively from
datacenter IPs, so run it from a residential connection or add backoff. Google
Trends values are RELATIVE interest (0-100), not absolute volume.
"""
import os
import time

import pandas as pd
from pytrends.request import TrendReq

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "trends", "google_trends.csv")

# Compare within small batches (Trends normalizes within a request of <=5 terms).
BRAND_BATCHES = [
    ["Celsius energy", "Monster energy", "Red Bull", "Alani Nu", "Prime energy"],
    ["Ghost energy", "C4 energy", "Bang energy", "Rockstar energy", "Reign energy"],
]
CATEGORY_TERMS = ["energy drink", "sugar free energy drink", "gut health soda", "protein energy drink"]
TIMEFRAME = "today 3-y"
GEO = "US"


def pull(terms):
    py = TrendReq(hl="en-US", tz=360)
    py.build_payload(terms, timeframe=TIMEFRAME, geo=GEO)
    df = py.interest_over_time()
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    return df.reset_index().melt(id_vars="date", var_name="term", value_name="interest")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    frames = []
    for batch in BRAND_BATCHES + [CATEGORY_TERMS]:
        try:
            frames.append(pull(batch))
            print(f"  ok: {batch}")
        except Exception as e:  # noqa: BLE001
            print(f"  ! {batch}: {e}")
        time.sleep(5)  # backoff to dodge rate limits

    if not frames:
        print("no data pulled (likely rate-limited); try again from a residential IP")
        return
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(out)} rows, {out['term'].nunique()} terms)")


if __name__ == "__main__":
    main()
