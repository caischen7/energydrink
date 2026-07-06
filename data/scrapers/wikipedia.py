#!/usr/bin/env python3
"""Scrape brand "interest" as monthly Wikipedia pageviews (Wikimedia REST API).

Wikimedia's Pageviews API is public, documented, and free (a descriptive
User-Agent is required by their policy — set in common.USER_AGENT).
Docs: https://wikimedia.org/api/rest_v1/  (metrics/pageviews/per-article)

Why this source: Amazon/IG/YouTube tell us where brands are *sold and talked
about*; Wikipedia pageviews are a clean, platform-neutral proxy for public
*curiosity* in a brand over time — a Google-Trends-style signal we can build
ourselves without a key. Keyed to the same canonical brands so it lines up with
combined/brand_summary.csv.

Outputs:
  data/wikipedia/brand_interest.csv   one row per (brand, month): brand, article, month, views
  data/wikipedia/brand_pages.csv      one row per brand: brand, article, total_views_12mo, avg_monthly_views

Run (needs outbound network):
    python data/scrapers/wikipedia.py
    WIKI_MONTHS=24 python data/scrapers/wikipedia.py
"""
import os
import sys
import time
import urllib.parse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (  # noqa: E402
    WIKI_ARTICLES, data_path, http_get_json, write_csv, _log,
)

REST = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        "en.wikipedia/all-access/user/{article}/monthly/{start}/{end}")


def _month_bounds(months_back):
    """(start, end) as YYYYMMDD00 strings spanning the last `months_back` full months."""
    today = date.today()
    # end = first day of the current month (Wikimedia is inclusive of the month
    # that the end timestamp falls in; using the 1st keeps us to complete months)
    y, m = today.year, today.month
    end = f"{y:04d}{m:02d}0100"
    sy, sm = y, m - months_back
    while sm <= 0:
        sm += 12
        sy -= 1
    start = f"{sy:04d}{sm:02d}0100"
    return start, end


def fetch_interest(months_back=12, pause=0.5):
    start, end = _month_bounds(months_back)
    interest_rows = []
    page_rows = []
    for brand, article in sorted(WIKI_ARTICLES.items()):
        art = urllib.parse.quote(article.replace(" ", "_"), safe="")
        url = REST.format(article=art, start=start, end=end)
        try:
            data = http_get_json(url)
        except Exception as e:  # a missing/renamed article shouldn't kill the run
            _log(f"  ! {brand} ({article}): {type(e).__name__} {e}")
            time.sleep(pause)
            continue
        items = data.get("items", [])
        total = 0
        for it in items:
            ts = str(it.get("timestamp", ""))  # YYYYMMDD00
            month = f"{ts[:4]}-{ts[4:6]}" if len(ts) >= 6 else None
            views = int(it.get("views") or 0)
            if month:
                interest_rows.append({
                    "brand": brand, "article": article,
                    "month": month, "views": views,
                })
                total += views
        n = len(items) or 1
        page_rows.append({
            "brand": brand, "article": article,
            "total_views_12mo": total,
            "avg_monthly_views": round(total / n),
        })
        _log(f"  {brand}: {total:,} views over {len(items)} months")
        time.sleep(pause)  # polite pacing
    return interest_rows, page_rows


def main():
    months = int(os.environ.get("WIKI_MONTHS", "12"))
    interest_rows, page_rows = fetch_interest(months_back=months)
    write_csv(
        data_path("wikipedia", "brand_interest.csv"),
        ["brand", "article", "month", "views"],
        sorted(interest_rows, key=lambda r: (r["brand"], r["month"])),
    )
    write_csv(
        data_path("wikipedia", "brand_pages.csv"),
        ["brand", "article", "total_views_12mo", "avg_monthly_views"],
        sorted(page_rows, key=lambda r: -r["total_views_12mo"]),
    )
    _log(f"Wikipedia done: {len(page_rows)} brands, {len(interest_rows)} brand-months.")


if __name__ == "__main__":
    main()
