#!/usr/bin/env python3
"""Scrape Walmart.com energy-drink products + customer reviews into clean CSVs.

Stdlib only (no pip installs). Two backends:

  direct   — fetches walmart.com search/review pages and parses the embedded
             __NEXT_DATA__ JSON. Works from a normal residential connection;
             Walmart's bot protection (PerimeterX) blocks most datacenter /
             cloud IPs, so this will NOT work from a typical cloud container.
  serpapi  — uses SerpAPI's Walmart engines (search + product reviews).
             Works from anywhere but needs an API key in $SERPAPI_KEY
             (https://serpapi.com, engine=walmart / walmart_product_reviews).

Usage:
  python data/scripts/scrape_walmart.py                        # auto backend
  python data/scripts/scrape_walmart.py --backend serpapi
  python data/scripts/scrape_walmart.py --terms "Red Bull energy drink" \
      --max-products 20 --review-pages 3

Outputs (schema mirrors data/amazon/):
  data/walmart/products.csv   one row per product (price, rating, review count,
                              badges — incl. "N+ bought since yesterday", the
                              closest public proxy Walmart gives for purchases)
  data/walmart/reviews.csv    one row per customer review

Note on "purchase data": Walmart does not publish unit sales. The public
proxies captured here are review volume, star rating, bestseller badges and
the "bought since yesterday" counter shown on some listings.
"""

import argparse
import csv
import datetime as dt
import gzip
import io
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# Same brand terms as the Amazon corpus (see data/amazon/products.csv), plus a
# generic category query so Walmart's own bestsellers (Red Bull etc.) show up.
DEFAULT_TERMS = [
    "energy drink",
    "Alani Nu energy drink",
    "Celsius energy drink",
    "Ghost energy drink",
    "Monster energy drink",
]

# Copy of BRAND_ALIASES in build_clean_datasets.py (that module imports pandas
# at top level, and this script must stay stdlib-only).
BRAND_ALIASES = {
    "celsius": "Celsius", "celsiusofficial": "Celsius",
    "red bull": "Red Bull", "redbull": "Red Bull",
    "monster": "Monster", "monsterenergy": "Monster",
    "liquid i.v.": "Liquid I.V.", "liquid iv": "Liquid I.V.",
    "ghost": "Ghost",
    "bang": "Bang", "bangenergy": "Bang", "bang energy": "Bang",
    "alani nu": "Alani Nu", "alaninutrition": "Alani Nu", "alani": "Alani Nu",
    "rockstar": "Rockstar", "rockstarenergy": "Rockstar",
    "5-hour energy": "5-hour Energy", "5 hour energy": "5-hour Energy",
    "nos": "NOS",
    "reign": "Reign", "reignbodyfuel": "Reign",
    "zoa": "Zoa", "zoaenergy": "Zoa",
    "prime": "Prime", "drinkprime": "Prime",
    "g fuel": "G Fuel", "gfuel": "G Fuel",
    "advocare": "AdvoCare",
    "bloom nutrition": "Bloom Nutrition", "bloom": "Bloom Nutrition",
    "c4": "C4",
    "guru": "GURU",
    "liquid death": "Liquid Death",
    "pureboost": "Pureboost",
    "spylt": "Spylt",
    "xwerks": "Xwerks",
    "zipfizz": "Zipfizz",
}

# Longest-first so "red bull" wins over "bull" style collisions.
_TITLE_BRANDS = sorted(
    {alias: canon for alias, canon in BRAND_ALIASES.items()}.items(),
    key=lambda kv: -len(kv[0]),
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

PRODUCT_COLUMNS = [
    "item_id", "search_term", "title", "brand", "price_usd", "list_price_usd",
    "rating", "reviews_total", "seller", "sponsored", "badges",
    "bought_since_yesterday", "availability", "link", "scraped_at",
]
REVIEW_COLUMNS = [
    "item_id", "brand", "product_title", "search_term", "review_id",
    "review_title", "review_text", "rating", "review_date",
    "verified_purchase", "helpful_votes",
]


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def norm_brand(value):
    if not value:
        return None
    return BRAND_ALIASES.get(str(value).strip().lower(), str(value).strip())


def brand_from_title(title):
    low = (title or "").lower()
    for alias, canon in _TITLE_BRANDS:
        if alias in low:
            return canon
    return None


def find_key(obj, key):
    """Yield every value stored under `key` anywhere in a nested structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from find_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_key(v, key)


def first(iterable, default=None):
    for x in iterable:
        if x is not None:
            return x
    return default


def to_float(value):
    if value is None:
        return None
    m = re.search(r"[\d.]+", str(value).replace(",", ""))
    return float(m.group()) if m else None


def to_int(value):
    f = to_float(value)
    return int(f) if f is not None else None


def parse_review_date(value):
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return s  # keep raw rather than lose it


def polite_sleep(base):
    time.sleep(base + random.uniform(0, base))


def write_csv(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {path} ({len(rows)} rows)")


# --------------------------------------------------------------------------
# Direct backend — walmart.com __NEXT_DATA__
# --------------------------------------------------------------------------

class BlockedError(RuntimeError):
    pass


def http_get(url, extra_headers=None):
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    headers.update(extra_headers or {})
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                body = gzip.GzipFile(fileobj=io.BytesIO(body)).read()
            return body.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code in (403, 412, 429):
            raise BlockedError(
                f"HTTP {e.code} from {urllib.parse.urlsplit(url).netloc} — "
                "Walmart's bot protection is blocking this IP. Run from a "
                "residential connection, or use --backend serpapi with a "
                "SERPAPI_KEY."
            ) from e
        raise
    except (urllib.error.URLError, OSError) as e:
        raise BlockedError(
            f"Could not reach {urllib.parse.urlsplit(url).netloc} ({e}). "
            "This network can't reach walmart.com at all (e.g. a sandboxed "
            "cloud environment with a domain allowlist). Run this script "
            "from your own machine, or use --backend serpapi with a "
            "SERPAPI_KEY if serpapi.com is reachable."
        ) from e


def extract_next_data(html):
    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    if not m:
        if "px-captcha" in html or "Robot or human" in html:
            raise BlockedError(
                "Walmart served its 'Robot or human?' challenge — this IP is "
                "flagged. Run from a residential connection or use "
                "--backend serpapi."
            )
        raise RuntimeError("No __NEXT_DATA__ found — page layout may have changed.")
    return json.loads(m.group(1))


def direct_search(term, page, sleep):
    url = "https://www.walmart.com/search?" + urllib.parse.urlencode(
        {"q": term, "page": page}
    )
    data = extract_next_data(http_get(url))
    polite_sleep(sleep)

    # Products live under itemStacks[*].items[*]; rather than hard-coding the
    # full path (Walmart moves it), grab every dict that looks like a product.
    seen, items = set(), []
    for stack in find_key(data, "itemStacks"):
        for candidate in find_key(stack, "items"):
            if not isinstance(candidate, list):
                continue
            for it in candidate:
                if not isinstance(it, dict):
                    continue
                item_id = it.get("usItemId") or it.get("id")
                if not item_id or it.get("name") is None or item_id in seen:
                    continue
                seen.add(item_id)
                items.append(it)
    return items


def direct_product_row(it, term):
    raw = json.dumps(it)
    bought = re.search(r"([\d,]+\+?)\s*bought since yesterday", raw, re.I)
    price_info = it.get("priceInfo") or {}
    badges = sorted(
        {
            str(t)
            for t in find_key(it.get("badges") or it.get("badge") or {}, "text")
            if isinstance(t, str)
        }
    )
    title = it.get("name") or ""
    return {
        "item_id": it.get("usItemId") or it.get("id"),
        "search_term": term,
        "title": title,
        "brand": norm_brand(it.get("brand")) or brand_from_title(title),
        "price_usd": to_float(
            price_info.get("linePrice")
            or first(find_key(price_info, "price"))
        ),
        "list_price_usd": to_float(price_info.get("wasPrice")),
        "rating": to_float(it.get("averageRating") or it.get("rating")),
        "reviews_total": to_int(it.get("numberOfReviews") or it.get("reviews")),
        "seller": it.get("sellerName"),
        "sponsored": bool(it.get("isSponsoredFlag") or it.get("sponsoredProduct")),
        "badges": "; ".join(badges),
        "bought_since_yesterday": bought.group(1) if bought else None,
        "availability": it.get("availabilityStatusDisplayValue")
        or it.get("availabilityStatus"),
        "link": (
            "https://www.walmart.com" + it["canonicalUrl"]
            if it.get("canonicalUrl", "").startswith("/")
            else it.get("canonicalUrl")
        ),
        "scraped_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def direct_reviews(item_id, page, sleep):
    url = (
        f"https://www.walmart.com/reviews/product/{item_id}?"
        + urllib.parse.urlencode({"page": page, "sort": "submission-desc"})
    )
    data = extract_next_data(http_get(url))
    polite_sleep(sleep)

    reviews = []
    for block in find_key(data, "customerReviews"):
        if isinstance(block, list):
            reviews.extend(r for r in block if isinstance(r, dict))
    return reviews


def direct_review_row(r, product, term):
    verified = bool(
        r.get("verifiedPurchaser")
        or any(
            "verified" in str(b).lower()
            for b in find_key(r.get("badges") or [], "badgeType")
        )
        or any(
            "verified" in str(b).lower()
            for b in find_key(r.get("badges") or [], "id")
        )
    )
    return {
        "item_id": product["item_id"],
        "brand": product["brand"],
        "product_title": product["title"],
        "search_term": term,
        "review_id": r.get("reviewId") or r.get("id"),
        "review_title": r.get("reviewTitle") or r.get("title"),
        "review_text": r.get("reviewText") or r.get("text"),
        "rating": to_float(r.get("rating")),
        "review_date": parse_review_date(
            r.get("reviewSubmissionTime") or r.get("submissionTime")
        ),
        "verified_purchase": verified,
        "helpful_votes": to_int(r.get("positiveFeedback")),
    }


# --------------------------------------------------------------------------
# SerpAPI backend
# --------------------------------------------------------------------------

def serpapi_get(params, api_key):
    params = dict(params, api_key=api_key)
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def serpapi_search(term, page, api_key):
    data = serpapi_get({"engine": "walmart", "query": term, "page": page}, api_key)
    return data.get("organic_results") or []


def serpapi_product_row(it, term):
    offer = it.get("primary_offer") or {}
    title = it.get("title") or ""
    return {
        "item_id": it.get("us_item_id") or it.get("product_id"),
        "search_term": term,
        "title": title,
        "brand": brand_from_title(title),
        "price_usd": to_float(offer.get("offer_price") or it.get("price")),
        "list_price_usd": to_float(offer.get("min_price")),
        "rating": to_float(it.get("rating")),
        "reviews_total": to_int(it.get("reviews")),
        "seller": it.get("seller_name"),
        "sponsored": bool(it.get("sponsored")),
        "badges": "",
        "bought_since_yesterday": None,
        "availability": None,
        "link": it.get("product_page_url"),
        "scraped_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def serpapi_reviews(item_id, page, api_key):
    data = serpapi_get(
        {"engine": "walmart_product_reviews", "product_id": item_id, "page": page},
        api_key,
    )
    return data.get("reviews") or []


def serpapi_review_row(r, product, term):
    return {
        "item_id": product["item_id"],
        "brand": product["brand"],
        "product_title": product["title"],
        "search_term": term,
        "review_id": r.get("review_id") or r.get("id"),
        "review_title": r.get("title"),
        "review_text": r.get("text"),
        "rating": to_float(r.get("rating")),
        "review_date": parse_review_date(r.get("review_submission_time")),
        "verified_purchase": bool(r.get("verified_purchase")),
        "helpful_votes": to_int(r.get("positive_feedback")),
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--backend", choices=["auto", "direct", "serpapi"],
                    default="auto")
    ap.add_argument("--terms", nargs="+", default=DEFAULT_TERMS)
    ap.add_argument("--search-pages", type=int, default=2,
                    help="search result pages per term (default 2, ~40 items)")
    ap.add_argument("--max-products", type=int, default=25,
                    help="max products per term to keep (default 25)")
    ap.add_argument("--review-pages", type=int, default=3,
                    help="review pages per product, ~20 reviews each (default 3)")
    ap.add_argument("--sleep", type=float, default=2.5,
                    help="base delay between requests in seconds (default 2.5)")
    ap.add_argument("--out", default="data/walmart", help="output directory")
    args = ap.parse_args()

    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    backend = args.backend
    if backend == "auto":
        backend = "serpapi" if api_key else "direct"
    if backend == "serpapi" and not api_key:
        sys.exit("SERPAPI_KEY is not set — export it or use --backend direct.")
    print(f"Backend: {backend}")

    products, product_ids = [], set()
    for term in args.terms:
        kept = 0
        for page in range(1, args.search_pages + 1):
            if backend == "direct":
                raw_items = direct_search(term, page, args.sleep)
                rows = [direct_product_row(it, term) for it in raw_items]
            else:
                raw_items = serpapi_search(term, page, api_key)
                rows = [serpapi_product_row(it, term) for it in raw_items]
            for row in rows:
                if kept >= args.max_products:
                    break
                if not row["item_id"] or row["item_id"] in product_ids:
                    continue
                product_ids.add(row["item_id"])
                products.append(row)
                kept += 1
            print(f"  [{term}] page {page}: {len(rows)} items, kept {kept}")
            if kept >= args.max_products:
                break
    write_csv(os.path.join(args.out, "products.csv"), PRODUCT_COLUMNS, products)

    reviews, review_ids = [], set()
    for i, product in enumerate(products, 1):
        term = product["search_term"]
        got = 0
        for page in range(1, args.review_pages + 1):
            try:
                if backend == "direct":
                    raw = direct_reviews(product["item_id"], page, args.sleep)
                    rows = [direct_review_row(r, product, term) for r in raw]
                else:
                    raw = serpapi_reviews(product["item_id"], page, api_key)
                    rows = [serpapi_review_row(r, product, term) for r in raw]
            except BlockedError:
                raise
            except Exception as e:  # one bad product shouldn't kill the run
                print(f"  ! reviews failed for {product['item_id']}: {e}")
                break
            if not rows:
                break
            for row in rows:
                key = row["review_id"] or (
                    row["item_id"], row["review_text"], row["review_date"]
                )
                if key in review_ids:
                    continue
                review_ids.add(key)
                reviews.append(row)
                got += 1
        print(f"  [{i}/{len(products)}] {product['item_id']}: {got} reviews")
    write_csv(os.path.join(args.out, "reviews.csv"), REVIEW_COLUMNS, reviews)

    print("Done. Next: rerun `python data/scripts/build_dashboard_json.py` if "
          "you wire Walmart into the dashboard aggregate.")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit(f"BLOCKED: {e}")
