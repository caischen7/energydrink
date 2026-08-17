#!/usr/bin/env python3
"""Collect Google Trends interest-over-time for the flavor taxonomy.

Runs anywhere with network access. It cannot run in the Claude Code container -
that environment's egress proxy answers 403 to CONNECT for trends.google.com -
so the intended home is the scheduled GitHub Action in
`.github/workflows/trends.yml`, which runs on GitHub's network and commits the
refreshed CSVs back. Nobody has to run anything by hand.

Providers, in the order `--provider auto` tries them:

  serpapi    Paid, documented, stable. Set SERPAPI_KEY. ~13 calls per refresh,
             which is negligible against any plan.
  pytrends   Free, unofficial, rate-limited and prone to breaking when Google
             changes its internals. Fine as a fallback; do not build a
             production dependency on it.

THE NORMALISATION TRAP, AND WHY THIS ALWAYS REFETCHES THE WHOLE WINDOW
----------------------------------------------------------------------
Google Trends does not return absolute search volume. It returns a 0-100 index
scaled so that the maximum *within the requested window* equals 100. That has a
consequence that quietly corrupts any incremental collector:

    Fetch 2019-2025 -> a 2021 peak reads 100.
    Fetch 2019-2026 -> if 2026 is bigger, that same 2021 point now reads 74.

So appending "just the new months" to an existing file splices together
segments on different scales, and the resulting series shows jumps that are
pure artifact. This collector therefore refetches the ENTIRE window every run
and rewrites the file. It costs a few extra API calls and removes a whole class
of silent error.

For the same reason, values are comparable within a term and meaningless across
terms: "coffee energy drink" at 80 is not twice "grape energy drink" at 40. The
model downstream only ever uses within-term change.

    python data/scrapers/google_trends.py --provider serpapi
    python data/scrapers/google_trends.py --dry-run      # show the plan, call nothing

stdlib only for the serpapi path; pytrends is imported lazily.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data/trends")

START = os.environ.get("TRENDS_START", "2019-01-01")
GEO = os.environ.get("TRENDS_GEO", "US")

# Filename (flavor family) -> search term. The family names must match
# FLAVOR_FAMILIES in classify_target_consumers.py, which is what makes a flavor
# mean the same thing on the search side and the sales side. "energy drink" is
# appended to every term on purpose: bare "watermelon" measures the fruit.
TERMS = {
    "Original":            "energy drink",
    "Berry":               "berry energy drink",
    "Citrus":              "citrus energy drink",
    "Sour & candy":        "sour energy drink",
    "Tropical":            "tropical energy drink",
    "Watermelon":          "watermelon energy drink",
    "Grape":               "grape energy drink",
    "Punch & mixed fruit": "fruit punch energy drink",
    "Peach & stone fruit": "peach energy drink",
    "Apple & pear":        "apple energy drink",
    "Coffee & cream":      "coffee energy drink",
    "Tea & botanical":     "tea energy drink",
    "Cola & soda":         "cola energy drink",
}


def today():
    return time.strftime("%Y-%m-%d")


def window():
    return f"{START} {today()}"


# ---------------------------------------------------------------- serpapi --
def fetch_serpapi(term, key):
    """SerpApi's google_trends engine. Returns [(YYYY-MM-DD, value), ...]."""
    q = urllib.parse.urlencode({
        "engine": "google_trends",
        "q": term,
        "data_type": "TIMESERIES",
        "geo": GEO,
        "date": window(),
        "api_key": key,
    })
    url = "https://serpapi.com/search.json?" + q
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 ** attempt * 5)
                continue
            raise
    else:
        return []

    if "error" in d:
        raise RuntimeError(f"serpapi: {d['error']}")

    out = []
    for pt in d.get("interest_over_time", {}).get("timeline_data", []):
        # SerpApi gives a human date plus a unix timestamp; the timestamp is
        # unambiguous, the display string is not.
        ts = pt.get("timestamp")
        if ts is None:
            continue
        day = time.strftime("%Y-%m-%d", time.gmtime(int(ts)))
        vals = pt.get("values") or []
        if not vals:
            continue
        v = vals[0].get("extracted_value")
        if v is None:
            continue
        out.append((day, float(v)))
    return out


# --------------------------------------------------------------- pytrends --
def fetch_pytrends(term):
    from pytrends.request import TrendReq          # imported lazily: optional dep
    py = TrendReq(hl="en-US", tz=0)
    py.build_payload([term], timeframe=window(), geo=GEO)
    df = py.interest_over_time()
    if df is None or df.empty:
        return []
    return [(str(idx.date()), float(row[term]))
            for idx, row in df.iterrows() if not row.get("isPartial", False)]


# ------------------------------------------------------------------ write --
def write(fam, term, rows):
    """Google's own export shape, so the existing loader reads it unchanged."""
    path = os.path.join(OUT_DIR, f"{fam}.csv")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Category: All categories"])
        w.writerow([])
        w.writerow(["Week", f"{term}: ({GEO})"])
        for day, v in rows:
            w.writerow([day, int(round(v))])
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["auto", "serpapi", "pytrends"], default="auto")
    ap.add_argument("--sleep", type=float, default=1.5)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("SERPAPI_KEY", "").strip()
    provider = args.provider
    if provider == "auto":
        provider = "serpapi" if key else "pytrends"
    if provider == "serpapi" and not key:
        sys.exit("SERPAPI_KEY is not set. Set it, or pass --provider pytrends.")

    print(f"provider {provider}   geo {GEO}   window {window()}   terms {len(TERMS)}")
    if args.dry_run:
        for fam, term in TERMS.items():
            print(f"  would fetch {term!r:<32} -> data/trends/{fam}.csv")
        print("\ndry run — nothing called, nothing written.")
        return

    ok, failed = 0, []
    for fam, term in TERMS.items():
        try:
            rows = fetch_serpapi(term, key) if provider == "serpapi" else fetch_pytrends(term)
        except Exception as e:                      # noqa: BLE001 - report and continue
            print(f"  FAIL {fam}: {type(e).__name__}: {e}")
            failed.append(fam)
            continue
        if not rows:
            print(f"  FAIL {fam}: no data returned")
            failed.append(fam)
            continue
        write(fam, term, rows)
        print(f"  ok   {fam:<22} {len(rows):>4} points  {rows[0][0]} -> {rows[-1][0]}")
        ok += 1
        time.sleep(args.sleep)

    print(f"\n{ok}/{len(TERMS)} written to data/trends/")
    if failed:
        print("failed: " + ", ".join(failed))
        # A partial refresh mixes windows across files, which is exactly the
        # normalisation problem this script exists to avoid.
        sys.exit(1)
    print("Next: python data/scripts/trends_model.py --source google --write")


if __name__ == "__main__":
    main()
