#!/usr/bin/env python3
"""Scrape energy-drink product + nutrition data from Open Food Facts.

Open Food Facts is a free, open (ODbL-licensed) crowdsourced food database with
a documented public API — no key, no auth, ToS-friendly for this kind of use.
Docs: https://openfoodfacts.github.io/openfoodfacts-server/api/

Why this source: our existing Amazon `products.csv` has price + rating but *no*
nutrition. OFF fills the gap the market keeps asking about in the reviews/
comments corpus (sugar, caffeine, "clean"): every row here carries sugar and
caffeine per 100 ml plus a Nutri-Score, keyed to the same canonical brands.

Output (same spirit/shape as data/amazon/products.csv, one row per product):
  data/openfoodfacts/products.csv
    code, product_name, brand, brand_raw, quantity, serving_size,
    sugars_100g, caffeine_mg_100g, energy_kcal_100g, nutriscore_grade,
    ingredients_text, countries, url, scraped_at

Run (needs outbound network — will not work inside a locked-down sandbox):
    python data/scrapers/openfoodfacts.py            # ~5 pages, category=energy-drinks
    OFF_PAGES=10 python data/scrapers/openfoodfacts.py
"""
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (  # noqa: E402
    data_path, http_get_json, match_known_brand, norm_brand, write_csv, _log,
)

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
FIELDS = [
    "code", "product_name", "brands", "quantity", "serving_size",
    "nutriments", "nutriscore_grade", "ingredients_text", "countries",
    "url",
]


def _n(nutr, key):
    """Pull a numeric nutriment value, tolerating missing keys."""
    v = nutr.get(key)
    try:
        return round(float(v), 2) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def fetch_products(pages=5, page_size=100, pause=1.0):
    rows = []
    seen = set()
    for page in range(1, pages + 1):
        _log(f"OFF: page {page}/{pages} ...")
        data = http_get_json(SEARCH_URL, params={
            "action": "process",
            "tagtype_0": "categories",
            "tag_contains_0": "contains",
            "tag_0": "energy-drinks",
            "sort_by": "unique_scans_n",   # most-scanned (popular) first
            "page_size": page_size,
            "page": page,
            "json": 1,
            "fields": ",".join(FIELDS),
        })
        products = data.get("products", [])
        if not products:
            break
        for p in products:
            code = str(p.get("code") or "").strip()
            name = (p.get("product_name") or "").strip()
            if not code or code in seen or not name:
                continue
            seen.add(code)
            nutr = p.get("nutriments") or {}
            brand_raw = (p.get("brands") or "").strip()
            brand = norm_brand(brand_raw) or match_known_brand(f"{brand_raw} {name}")
            rows.append({
                "code": code,
                "product_name": name,
                "brand": brand or "",
                "brand_raw": brand_raw,
                "quantity": (p.get("quantity") or "").strip(),
                "serving_size": (p.get("serving_size") or "").strip(),
                "sugars_100g": _n(nutr, "sugars_100g"),
                "caffeine_mg_100g": _n(nutr, "caffeine_100g") or _n(nutr, "caffeine_value"),
                "energy_kcal_100g": _n(nutr, "energy-kcal_100g"),
                "nutriscore_grade": (p.get("nutriscore_grade") or "").strip().lower(),
                "ingredients_text": (p.get("ingredients_text") or "").strip().replace("\n", " "),
                "countries": (p.get("countries") or "").strip(),
                "url": (p.get("url") or "").strip(),
                "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
        time.sleep(pause)  # be polite to a free community API
    return rows


FIELDNAMES = [
    "code", "product_name", "brand", "brand_raw", "quantity", "serving_size",
    "sugars_100g", "caffeine_mg_100g", "energy_kcal_100g", "nutriscore_grade",
    "ingredients_text", "countries", "url", "scraped_at",
]


def main():
    pages = int(os.environ.get("OFF_PAGES", "5"))
    rows = fetch_products(pages=pages)
    out = data_path("openfoodfacts", "products.csv")
    write_csv(out, FIELDNAMES, rows)
    with_sugar = sum(1 for r in rows if r["sugars_100g"] is not None)
    branded = sum(1 for r in rows if r["brand"])
    _log(f"OFF done: {len(rows)} products, {branded} matched to a tracked brand, "
         f"{with_sugar} with sugar data.")


if __name__ == "__main__":
    main()
