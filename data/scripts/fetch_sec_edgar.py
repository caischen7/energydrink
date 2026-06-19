#!/usr/bin/env python3
"""
Pull real quarterly revenue for the two pure-play public energy-drink
companies from SEC EDGAR's free public XBRL API.

Why this exists: every other "growth" signal on the dashboard is social
(mentions, search interest) or retail-panel (dollar share), all of which are
estimates. SEC filings are the one source that's a forward-looking, audited,
citable number straight from the company. Celsius Holdings (CELH) and
Monster Beverage (MNST) both file real quarterly revenue; Red Bull is
private and doesn't file with the SEC, so this can't cover the full
category, but it gives a hard "is this segment still growing" check for the
two names it does cover.

This loader is NOT wired into build_dashboard_json.py yet — run it, eyeball
the output, then fold sec/quarterly_revenue.csv into the aggregate (see
data/README.md).

SEC EDGAR requires a descriptive User-Agent identifying the requester and
rate-limits to ~10 requests/second; this sandbox has no outbound network at
all, so run this from a normal residential/office connection.

  python data/scripts/fetch_sec_edgar.py
"""
import csv
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "sec", "quarterly_revenue.csv")

# SEC requires a real contact in the User-Agent, not a generic one.
USER_AGENT = "energydrink-dashboard-research contact@example.com"

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

COMPANIES = {
    "Celsius Holdings": "CELH",
    "Monster Beverage": "MNST",
}

# Most companies tag total revenue under one of these GAAP concepts,
# depending on filing vintage.
REVENUE_TAGS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
]


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def find_cik(ticker, ticker_map):
    for entry in ticker_map:
        if entry["ticker"].upper() == ticker.upper():
            return entry["cik_str"]
    raise ValueError(f"ticker {ticker} not found in SEC ticker list")


def quarterly_revenue_rows(company, facts):
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in REVENUE_TAGS:
        if tag not in us_gaap:
            continue
        for unit_rows in us_gaap[tag]["units"].values():
            for row in unit_rows:
                # 10-Q quarterly figures only; 10-K annuals double-count the
                # same quarters and aren't comparable in a quarter-over-quarter
                # trend line.
                if row.get("form") != "10-Q":
                    continue
                yield (
                    company,
                    row.get("fy"),
                    row.get("fp"),
                    row.get("end"),
                    row.get("val"),
                )
        return  # first matching tag wins; don't double-count across tags


def main():
    ticker_map_raw = fetch_json(TICKERS_URL)
    ticker_map = list(ticker_map_raw.values()) if isinstance(ticker_map_raw, dict) else ticker_map_raw

    rows = []
    for company, ticker in COMPANIES.items():
        cik = find_cik(ticker, ticker_map)
        facts = fetch_json(FACTS_URL.format(cik=cik))
        rows.extend(quarterly_revenue_rows(company, facts))
        time.sleep(0.5)  # stay well under the SEC rate limit

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["company", "fiscal_year", "fiscal_period", "period_end", "revenue_usd"])
        w.writerows(sorted(rows))
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
