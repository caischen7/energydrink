#!/usr/bin/env python3
"""
Pull quarterly revenue for the public energy-drink companies from SEC EDGAR.

Why this exists: Celsius (CELH) and Monster (MNST) are the only pure-ish plays in
the category that report publicly, and their filings are the one *free* source
that speaks to channel mix — club, e-commerce and international splits appear in
the MD&A because they are material to them. Every other channel source we have
either costs money or covers convenience only.

Run it from a machine with open network access. This repo's dev container blocks
sec.gov at the egress proxy, so it will fail there with a 403 on CONNECT — that
is the network policy, not a bug in this script.

    python data/scripts/fetch_sec_edgar.py                  # -> data/sec/*.csv
    python data/scripts/fetch_sec_edgar.py --out /tmp/sec

SEC asks for a descriptive User-Agent with a contact address and rate-limits to
10 requests/second; both are honoured below. Stdlib only.
"""
import argparse
import csv
import json
import os
import time
import urllib.request

UA = "Bogus Banana capstone research (caischen7@gmail.com)"
BASE = "https://data.sec.gov/api/xbrl/companyconcept"

COMPANIES = {
    "CELH": ("0001341766", "Celsius Holdings"),
    "MNST": ("0000865752", "Monster Beverage"),
    "KDP":  ("0001418135", "Keurig Dr Pepper"),   # Venom
    "PEP":  ("0000077476", "PepsiCo"),            # Rockstar, Mtn Dew
}

# XBRL tags vary by filer and by year; try them in order and keep the first hit.
REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        import gzip
        raw = gzip.decompress(raw)
    return json.loads(raw)


def quarterly(cik, tag):
    url = f"{BASE}/CIK{cik}/us-gaap/{tag}.json"
    try:
        d = get(url)
    except Exception:
        return []
    out = []
    for unit, rows in d.get("units", {}).items():
        if unit != "USD":
            continue
        for r in rows:
            # keep 10-Q/10-K facts that cover a single quarter (~90 days)
            if not r.get("start") or not r.get("end"):
                continue
            days = (_date(r["end"]) - _date(r["start"])).days
            if 80 <= days <= 100:
                out.append({"start": r["start"], "end": r["end"], "fy": r.get("fy"),
                            "fp": r.get("fp"), "form": r.get("form"),
                            "revenue_usd": r["val"], "tag": tag})
    # de-duplicate: the same quarter is restated across later filings
    best = {}
    for r in out:
        best[r["end"]] = r
    return sorted(best.values(), key=lambda r: r["end"])


def _date(s):
    import datetime
    return datetime.date.fromisoformat(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "sec"))
    args = ap.parse_args()
    outdir = os.path.normpath(args.out)
    os.makedirs(outdir, exist_ok=True)

    allrows = []
    for ticker, (cik, name) in COMPANIES.items():
        rows = []
        for tag in REVENUE_TAGS:
            rows = quarterly(cik, tag)
            time.sleep(0.15)                      # SEC rate limit: 10 req/s
            if rows:
                break
        for r in rows:
            r["ticker"] = ticker
            r["company"] = name
        print(f"{ticker:5} {name:20} {len(rows):3} quarters"
              + (f"  {rows[0]['end']} → {rows[-1]['end']}" if rows else "  (no data)"))
        allrows += rows

    if not allrows:
        raise SystemExit("no data returned — check network access to data.sec.gov")

    path = os.path.join(outdir, "quarterly_revenue.csv")
    cols = ["ticker", "company", "fy", "fp", "form", "start", "end", "revenue_usd", "tag"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)
    print(f"\nwrote {len(allrows)} rows -> {path}")
    print("Next: read the latest 10-Q MD&A for channel commentary — the XBRL facts "
          "carry revenue but not the club/e-commerce split, which is narrative text.")


if __name__ == "__main__":
    main()
