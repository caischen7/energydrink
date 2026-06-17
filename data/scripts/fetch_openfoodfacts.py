"""
Fetch nutrition + ingredient data for our tracked energy-drink brands from
Open Food Facts (open data, no API key). Writes data/nutrition/off_products.csv.

Open Food Facts coverage of US energy drinks is partial and caffeine is often
missing, so this AUGMENTS the curated data/nutrition/brand_nutrition.csv rather
than replacing it. Run where outbound HTTPS is allowed:

    pip install requests
    python data/scripts/fetch_openfoodfacts.py

Be a good citizen: OFF asks for a descriptive User-Agent and gentle rate limits.
"""
import os
import csv
import time
import requests

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "nutrition", "off_products.csv")

BRANDS = [
    "celsius", "red-bull", "monster", "bang", "alani-nu", "c4", "ghost",
    "rockstar", "nos", "reign", "prime", "zoa", "bloom-nutrition", "g-fuel",
    "guru", "advocare", "zipfizz",
]

API = "https://world.openfoodfacts.org/api/v2/search"
FIELDS = "code,product_name,brands,quantity,serving_size,nutriments,ingredients_text,categories_tags"
HEADERS = {"User-Agent": "energydrink-research/1.0 (github.com/caischen7/energydrink)"}


def fetch_brand(brand):
    params = {
        "brands_tags": brand,
        "fields": FIELDS,
        "page_size": 50,
        "sort_by": "unique_scans_n",
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("products", [])


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rows = []
    for brand in BRANDS:
        try:
            products = fetch_brand(brand)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {brand}: {e}")
            continue
        for p in products:
            n = p.get("nutriments", {}) or {}
            rows.append({
                "brand_query": brand,
                "code": p.get("code"),
                "product_name": p.get("product_name"),
                "brands": p.get("brands"),
                "quantity": p.get("quantity"),
                "serving_size": p.get("serving_size"),
                "caffeine_mg_100ml": n.get("caffeine_100g") or n.get("caffeine_value"),
                "sugars_g_100ml": n.get("sugars_100g"),
                "energy_kcal_100ml": n.get("energy-kcal_100g"),
                "ingredients_text": (p.get("ingredients_text") or "")[:500],
            })
        print(f"  {brand}: {len(products)} products")
        time.sleep(1.0)  # be gentle

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["brand_query"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
