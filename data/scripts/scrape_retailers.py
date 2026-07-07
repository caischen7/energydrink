#!/usr/bin/env python3
"""Scrape energy-drink products (+ reviews where offered) from US grocery /
big-box retailers: Target, Trader Joe's, Publix, H-E-B, Costco, Whole Foods,
Kroger.

All free. Two backends:

  browser  — Playwright persistent-profile Chromium (same setup as the Walmart
             and Amazon scrapers: pip3 install playwright &&
             python3 -m playwright install chromium). It navigates each
             retailer's search page and harvests product/review objects from
             (a) the JSON/GraphQL responses the page fetches, (b) embedded
             __NEXT_DATA__-style payloads, and (c) schema.org ld+json Product
             markup — so it keeps working when a retailer reshuffles its HTML.
             Run from a residential IP; retailer bot-walls (Akamai/PerimeterX)
             block datacenter IPs.
  kroger   — Kroger's OFFICIAL free Products API (developer.kroger.com: create
             an app, free tier). Used automatically for the kroger retailer
             when KROGER_CLIENT_ID / KROGER_CLIENT_SECRET are exported;
             otherwise kroger falls back to the browser (heavily bot-walled —
             the API is strongly recommended). Prices require a store:
             pass --kroger-location <id> or --kroger-zip <zip>.

Usage (VS Code terminal on macOS):
  pip3 install playwright && python3 -m playwright install chromium   # once
  python3 data/scripts/scrape_retailers.py                      # all retailers
  python3 data/scripts/scrape_retailers.py --retailers target costco
  KROGER_CLIENT_ID=... KROGER_CLIENT_SECRET=... \\
      python3 data/scripts/scrape_retailers.py --retailers kroger --kroger-zip 10012
  python3 data/scripts/scrape_retailers.py --no-reviews --max-products 10

Outputs (one pair of CSVs with a `retailer` column, like data/combined/):
  data/retailers/products.csv
  data/retailers/reviews.csv    (Target / Costco / H-E-B expose reviews;
                                 Trader Joe's, Publix, Whole Foods and the
                                 Kroger API do not)

Runs are INCREMENTAL: existing rows are merged in, deduped on
(retailer, item_id) / (retailer, review_id), fresh rows win. --fresh overwrites.

Reality check per retailer (worth knowing before you run):
  target      solid — products + ratings from Target's search API responses,
              reviews from its reviews API when product pages are visited.
  traderjoes  products via the site's GraphQL; no customer reviews exist.
  heb         products from the site's embedded/XHR JSON; some ratings.
  costco      products + Bazaarvoice reviews; Akamai sometimes challenges —
              solve in the window once, the profile persists.
  wholefoods  best-effort — catalog has names/brands but prices need a store
              selection; expect sparse price data.
  publix      best-effort — publix.com is largely Instacart-backed; expect
              the thinnest results of the set.
  kroger      use the official API (free key) — the website itself is behind
              an aggressive bot-wall.

None of these publish unit sales; review counts / ratings are the demand
proxies, matching the Walmart/Amazon scrapers.
"""

import argparse
import base64
import csv
import datetime as dt
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

DEFAULT_TERMS = [
    "energy drink",
    "Alani Nu energy drink",
    "Celsius energy drink",
    "Ghost energy drink",
    "Monster energy drink",
]

# Copy of BRAND_ALIASES in build_clean_datasets.py (kept stdlib-only here).
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

_TITLE_BRANDS = sorted(BRAND_ALIASES.items(), key=lambda kv: -len(kv[0]))

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

PRODUCT_COLUMNS = [
    "retailer", "item_id", "search_term", "title", "brand", "price_usd",
    "list_price_usd", "rating", "reviews_total", "size", "availability",
    "link", "scraped_at",
]
REVIEW_COLUMNS = [
    "retailer", "item_id", "brand", "product_title", "search_term",
    "review_id", "review_title", "review_text", "rating", "review_date",
    "verified_purchase", "helpful_votes",
]

# Per-retailer adapters. id_keys are checked in order; url_template builds a
# product link when none is harvested; reviews=True means product pages are
# visited to capture the review API traffic.
RETAILERS = {
    "target": {
        "search_url": "https://www.target.com/s?searchTerm={q}",
        "id_keys": ("tcin",),
        "url_template": "https://www.target.com/p/-/A-{id}",
        "reviews": True,
        "host": "target.com",
    },
    "traderjoes": {
        "search_url": "https://www.traderjoes.com/home/search?q={q}&section=products",
        "id_keys": ("sku",),
        "url_template": "https://www.traderjoes.com/home/products/pdp/{id}",
        "reviews": False,
        "host": "traderjoes.com",
    },
    "publix": {
        "search_url": "https://www.publix.com/search?query={q}",
        "id_keys": ("productId", "product_id", "id"),
        "url_template": None,
        "reviews": False,
        "host": "publix.com",
    },
    "heb": {
        "search_url": "https://www.heb.com/search?q={q}",
        "id_keys": ("productId", "product_id", "sku", "id"),
        "url_template": "https://www.heb.com/product-detail/-/{id}",
        "reviews": True,
        "host": "heb.com",
    },
    "costco": {
        "search_url": "https://www.costco.com/s?dept=All&keyword={q}",
        "id_keys": ("item_number", "itemNumber", "productId", "id"),
        "url_template": None,
        "reviews": True,
        "host": "costco.com",
    },
    "wholefoods": {
        "search_url": "https://www.wholefoodsmarket.com/search?text={q}",
        "id_keys": ("slug", "asin", "id"),
        "url_template": "https://www.wholefoodsmarket.com/product/{id}",
        "reviews": False,
        "host": "wholefoodsmarket.com",
    },
    "kroger": {
        "search_url": "https://www.kroger.com/search?query={q}",
        "id_keys": ("upc", "productId", "id"),
        "url_template": "https://www.kroger.com/p/-/{id}",
        "reviews": False,
        "host": "kroger.com",
    },
}

BLOCK_MARKERS = (
    "Robot or human", "px-captcha", "Access Denied", "Pardon Our Interruption",
    "_Incapsula_", "Please verify you are a human", "Reference #18",
    "detected unusual traffic",
)


class BlockedError(RuntimeError):
    pass


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


def walk_dicts(obj):
    """Yield every dict anywhere in a nested structure (including obj)."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_dicts(v)


def to_float(value):
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    m = re.search(r"[\d.]+", str(value).replace(",", ""))
    try:
        return float(m.group()) if m else None
    except ValueError:
        return None


def to_int(value):
    f = to_float(value)
    return int(f) if f is not None else None


def parse_date(value):
    if not value:
        return None
    s = str(value).strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)  # ISO / ISO datetime
    if m:
        return m.group(1)
    for fmt in ("%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return s


def polite_sleep(base):
    time.sleep(base + random.uniform(0, base))


def now_stamp():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_csv(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("  wrote %s (%d rows)" % (path, len(rows)))


def merge_rows(path, columns, new_rows, key_fn):
    """Union rows on disk at `path` with new_rows, deduped by key_fn (fresh
    rows win). Returns (columns, merged_rows); keyless rows always survive."""
    if not os.path.exists(path):
        return columns, list(new_rows)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_rows = list(reader)
        old_cols = reader.fieldnames or columns
    merged, seen = [], {}
    synth = 0
    for row in old_rows + list(new_rows):
        key = key_fn(row)
        if key is None:
            synth += 1
            key = ("__synthetic__", synth)
        if key in seen:
            merged[seen[key]] = row  # later (fresh) row wins in place
        else:
            seen[key] = len(merged)
            merged.append(row)
    print("  merge %s: %d on disk + %d scraped -> %d total"
          % (os.path.basename(path), len(old_rows), len(new_rows), len(merged)))
    return old_cols, merged


def product_key(row):
    iid = str(row.get("item_id") or "").strip()
    return (str(row.get("retailer") or ""), iid) if iid else None


def review_key(row):
    rid = str(row.get("review_id") or "").strip()
    if rid:
        return (str(row.get("retailer") or ""), rid)
    text = str(row.get("review_text") or "").strip()
    if text:
        return (str(row.get("retailer") or ""), str(row.get("item_id") or ""),
                text, str(row.get("review_date") or ""))
    return None


# --------------------------------------------------------------------------
# Generic harvesting — product/review objects out of captured JSON
# --------------------------------------------------------------------------

TITLE_KEYS = ("title", "name", "displayName", "item_title", "product_title",
              "productName", "description")
PRICE_KEYS = ("current_retail", "retail_price", "formatted_current_price",
              "current_price", "salePrice", "sale_price", "promo", "regular",
              "price", "listPrice", "amount", "current")
LIST_PRICE_KEYS = ("reg_retail", "regularPrice", "was_price", "wasPrice",
                   "list_price", "strikethroughPrice")
RATING_KEYS = ("averageRating", "average_rating", "average", "averageOverallRating",
               "ratingValue", "rating")
COUNT_KEYS = ("numberOfReviews", "review_count", "reviewCount", "total_review_count",
              "totalReviewCount", "ratingCount", "reviewsCount", "TotalReviewCount")
URL_KEYS = ("canonicalUrl", "canonical_url", "product_page_url", "buy_url",
            "productUrl", "url")
SIZE_KEYS = ("package_size", "size", "item_size", "unitOfSize")
TEXT_KEYS = ("ReviewText", "reviewText", "review_text", "reviewBody", "text")
REVIEW_RATING_KEYS = ("Rating", "rating", "rating_value", "ratingValue")


def _pick(d, keys, coerce=None, limiter=None):
    """First usable value for any of `keys`, searched shallowly then deep."""
    for k in keys:
        if k in d:
            v = coerce(d[k]) if coerce else d[k]
            if v is not None and (limiter is None or limiter(v)):
                return v
    for k in keys:
        for raw in find_key(d, k):
            v = coerce(raw) if coerce else raw
            if v is not None and (limiter is None or limiter(v)):
                return v
    return None


def _title_of(d):
    for k in TITLE_KEYS:
        v = d.get(k)
        if isinstance(v, str) and 3 <= len(v) <= 300:
            return v.strip()
    for k in TITLE_KEYS:
        for v in find_key(d, k):
            if isinstance(v, str) and 3 <= len(v) <= 300:
                return v.strip()
    return None


def _id_of(d, id_keys):
    for k in id_keys:
        v = d.get(k)
        if v is None:
            for v in find_key(d, k):
                break
        if v is not None and not isinstance(v, (dict, list)):
            s = str(v).strip()
            if 0 < len(s) < 64:
                return s
    return None


def _link_of(d, host):
    for k in URL_KEYS:
        for v in find_key(d, k):
            if isinstance(v, str):
                if v.startswith("http") and host in v:
                    return v
                if v.startswith("/"):
                    return "https://www.%s%s" % (host, v)
    return None


def ld_json_products(blob):
    """schema.org Product objects (from <script type=application/ld+json>)."""
    out = []
    for d in walk_dicts(blob):
        if d.get("@type") not in ("Product", ["Product"]):
            continue
        offers = d.get("offers") or {}
        agg = d.get("aggregateRating") or {}
        brand = d.get("brand")
        if isinstance(brand, dict):
            brand = brand.get("name")
        out.append({
            "id": str(d.get("sku") or d.get("productID") or d.get("@id") or ""),
            "title": d.get("name"),
            "brand": brand,
            "price": _pick(offers, ("price", "lowPrice"), to_float,
                           lambda v: 0 < v < 10000) if offers else None,
            "rating": to_float(agg.get("ratingValue")),
            "reviews_total": to_int(agg.get("reviewCount") or agg.get("ratingCount")),
            "link": d.get("url"),
        })
    return out


def harvest_products(blobs, cfg, term, retailer):
    """Product rows out of every JSON blob a page produced."""
    rows, seen = [], set()

    def emit(item_id, title, brand=None, price=None, list_price=None,
             rating=None, count=None, size=None, link=None, availability=None):
        if not item_id or not title or item_id in seen:
            return
        seen.add(item_id)
        if not link and cfg.get("url_template"):
            link = cfg["url_template"].format(id=item_id)
        rows.append({
            "retailer": retailer, "item_id": item_id, "search_term": term,
            "title": title, "brand": norm_brand(brand) or brand_from_title(title),
            "price_usd": price, "list_price_usd": list_price, "rating": rating,
            "reviews_total": count, "size": size, "availability": availability,
            "link": link, "scraped_at": now_stamp(),
        })

    for blob in blobs:
        # 1) schema.org Product markup — standardized, retailer-agnostic
        for p in ld_json_products(blob):
            emit(p["id"], p["title"], p["brand"], p["price"], None,
                 p["rating"], p["reviews_total"], None, p["link"])
        # 2) retailer JSON: any dict carrying one of the retailer's id keys
        #    plus a resolvable title is treated as a product object
        for d in walk_dicts(blob):
            item_id = _id_of(d, cfg["id_keys"])
            if not item_id or item_id in seen:
                continue
            title = _title_of(d)
            if not title:
                continue
            price = _pick(d, PRICE_KEYS, to_float, lambda v: 0 < v < 10000)
            rating = _pick(d, RATING_KEYS, to_float, lambda v: 0 < v <= 5)
            # require at least one commercial signal so nav/menu junk is skipped
            if price is None and rating is None and not _link_of(d, cfg["host"]):
                continue
            emit(
                item_id, title,
                brand=_pick(d, ("brand", "brand_name", "brandName"),
                            lambda v: v if isinstance(v, str) else None),
                price=price,
                list_price=_pick(d, LIST_PRICE_KEYS, to_float,
                                 lambda v: 0 < v < 10000),
                rating=rating,
                count=_pick(d, COUNT_KEYS, to_int, lambda v: 0 <= v < 10**7),
                size=_pick(d, SIZE_KEYS,
                           lambda v: v if isinstance(v, str) else None),
                link=_link_of(d, cfg["host"]),
                availability=_pick(d, ("availability", "availabilityStatus",
                                       "purchasable", "availability_status"),
                                   lambda v: str(v) if isinstance(
                                       v, (str, bool)) else None),
            )
    return rows


def harvest_reviews(blobs, product, term):
    """Review rows out of captured JSON (Bazaarvoice, Target r2d2, etc.)."""
    rows, seen = [], set()
    for blob in blobs:
        for d in walk_dicts(blob):
            text = None
            for k in TEXT_KEYS:
                v = d.get(k)
                if isinstance(v, str) and len(v.strip()) >= 3:
                    text = v.strip()
                    break
            if text is None:
                continue
            rating = None
            for k in REVIEW_RATING_KEYS:
                rating = to_float(d.get(k))
                if rating is not None:
                    break
            if rating is None or not (0 < rating <= 5):
                continue
            rid = d.get("Id") or d.get("id") or d.get("review_id") or d.get("reviewId")
            rid = str(rid).strip() if rid is not None else ""
            key = rid or (text, str(d.get("SubmissionTime") or ""))
            if key in seen:
                continue
            seen.add(key)
            verified = bool(
                d.get("IsVerifiedPurchaser") or d.get("verifiedPurchaser")
                or d.get("verified_purchase") or d.get("VerifiedPurchaser")
            )
            rows.append({
                "retailer": product["retailer"], "item_id": product["item_id"],
                "brand": product["brand"], "product_title": product["title"],
                "search_term": term, "review_id": rid,
                "review_title": d.get("Title") or d.get("title")
                or d.get("reviewTitle") or d.get("summary"),
                "review_text": text, "rating": rating,
                "review_date": parse_date(
                    d.get("SubmissionTime") or d.get("submissionTime")
                    or d.get("submission_date") or d.get("reviewSubmissionTime")
                    or d.get("date")),
                "verified_purchase": verified,
                "helpful_votes": to_int(
                    d.get("TotalPositiveFeedbackCount")
                    or d.get("positiveFeedback") or d.get("helpfulVotes")
                    or d.get("helpful_votes")),
            })
    return rows


# --------------------------------------------------------------------------
# Browser backend
# --------------------------------------------------------------------------

_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = window.chrome || {runtime: {}};
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
"""


class BrowserFetcher:
    """One persistent Chromium window shared across every retailer; collects
    all JSON the page fetches plus JSON embedded in the HTML."""

    def __init__(self, headless=False, profile_dir=None):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise SystemExit(
                "The browser backend needs Playwright:\n"
                "  pip3 install playwright\n"
                "  python3 -m playwright install chromium"
            )
        profile_dir = profile_dir or os.path.expanduser(
            "~/.cache/energydrink-retailers-profile")
        os.makedirs(profile_dir, exist_ok=True)
        self._pw = sync_playwright().start()
        self._context = self._pw.chromium.launch_persistent_context(
            profile_dir, headless=headless,
            viewport={"width": 1366, "height": 900}, locale="en-US",
            user_agent=UA,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context.add_init_script(_STEALTH_JS)
        self._page = (self._context.pages[0] if self._context.pages
                      else self._context.new_page())
        self._responses = []
        self._page.on("response", self._responses.append)
        self._headless = headless

    def blobs(self, url, scrolls=3, settle_ms=2500):
        """Navigate; return every JSON object the page produced."""
        self._responses.clear()
        self._page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        try:
            self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        for _ in range(scrolls):  # trigger lazy loads / review sections
            try:
                self._page.mouse.wheel(0, 2200)
                self._page.wait_for_timeout(settle_ms // max(scrolls, 1) + 400)
            except Exception:
                break
        html = self._page.content()
        if not self._responses and any(m in html for m in BLOCK_MARKERS):
            self._maybe_challenge(html)
        out = []
        # a) captured network responses that parse as JSON
        for resp in list(self._responses):
            try:
                ct = (resp.headers or {}).get("content-type", "")
            except Exception:
                ct = ""
            if "json" not in ct and "javascript" not in ct:
                continue
            try:
                body = resp.text()
            except Exception:
                continue
            if not body or len(body) > 8_000_000:
                continue
            body = body.lstrip()
            if not body.startswith(("{", "[")):
                continue
            try:
                out.append(json.loads(body))
            except ValueError:
                continue
        # b) JSON embedded in the HTML (Next.js payloads, ld+json, preloads)
        for m in re.finditer(
                r'<script[^>]*type="application/(?:ld\+)?json"[^>]*>(.*?)</script>',
                html, re.DOTALL):
            try:
                out.append(json.loads(m.group(1)))
            except ValueError:
                continue
        if not out and any(mk in html for mk in BLOCK_MARKERS):
            self._maybe_challenge(html)
        return out

    def _maybe_challenge(self, html):
        if self._headless:
            raise BlockedError(
                "This retailer served a bot challenge in headless mode — "
                "rerun without --headless and solve it once in the window "
                "(the profile is saved for next time).")
        print("  >> bot challenge detected — solve it in the browser window; "
              "waiting up to 3 min...")
        deadline = time.time() + 180
        while time.time() < deadline:
            self._page.wait_for_timeout(3000)
            cur = self._page.content()
            if not any(mk in cur for mk in BLOCK_MARKERS):
                return
        raise BlockedError("challenge was not solved within 3 minutes")

    def close(self):
        try:
            self._context.close()
            self._pw.stop()
        except Exception:
            pass


# --------------------------------------------------------------------------
# Kroger official API backend (free key from developer.kroger.com)
# --------------------------------------------------------------------------

def kroger_token(client_id, client_secret):
    req = urllib.request.Request(
        "https://api.kroger.com/v1/connect/oauth2/token",
        data=urllib.parse.urlencode({
            "grant_type": "client_credentials", "scope": "product.compact",
        }).encode(),
        headers={
            "Authorization": "Basic " + base64.b64encode(
                ("%s:%s" % (client_id, client_secret)).encode()).decode(),
            "Content-Type": "application/x-www-form-urlencoded",
        })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["access_token"]


def kroger_get(path, params, token):
    url = "https://api.kroger.com/v1/%s?%s" % (path, urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def kroger_location_for_zip(zip_code, token):
    data = kroger_get("locations", {"filter.zipCode.near": zip_code,
                                    "filter.limit": 1}, token)
    locs = data.get("data") or []
    return locs[0]["locationId"] if locs else None


def kroger_product_row(d, term):
    items = d.get("items") or [{}]
    price = (items[0].get("price") or {}) if items else {}
    title = d.get("description") or ""
    item_id = str(d.get("productId") or d.get("upc") or "")
    return {
        "retailer": "kroger", "item_id": item_id, "search_term": term,
        "title": title,
        "brand": norm_brand(d.get("brand")) or brand_from_title(title),
        "price_usd": to_float(price.get("promo") or price.get("regular")),
        "list_price_usd": to_float(price.get("regular"))
        if price.get("promo") else None,
        "rating": None, "reviews_total": None,  # not exposed by the API
        "size": items[0].get("size") if items else None,
        "availability": (items[0].get("fulfillment") or {}).get("inStore")
        if items else None,
        "link": "https://www.kroger.com/p/-/%s" % (d.get("upc") or item_id),
        "scraped_at": now_stamp(),
    }


def scrape_kroger_api(terms, max_products, location_id, sleep):
    cid = os.environ.get("KROGER_CLIENT_ID", "").strip()
    secret = os.environ.get("KROGER_CLIENT_SECRET", "").strip()
    token = kroger_token(cid, secret)
    rows = []
    for term in terms:
        params = {"filter.term": term, "filter.limit": min(max_products, 50)}
        if location_id:
            params["filter.locationId"] = location_id
        try:
            data = kroger_get("products", params, token)
        except urllib.error.HTTPError as e:
            print("  ! kroger API %s for %r" % (e.code, term))
            continue
        got = [kroger_product_row(d, term) for d in (data.get("data") or [])]
        rows.extend(got)
        print("  [kroger:%s] %d products%s" % (
            term, len(got), "" if location_id else " (no store -> no prices)"))
        polite_sleep(sleep)
    return rows


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retailers", nargs="+", choices=sorted(RETAILERS),
                    default=sorted(RETAILERS))
    ap.add_argument("--terms", nargs="+", default=DEFAULT_TERMS)
    ap.add_argument("--max-products", type=int, default=25,
                    help="max products kept per retailer per term (default 25)")
    ap.add_argument("--no-reviews", action="store_true",
                    help="skip visiting product pages for reviews")
    ap.add_argument("--review-products", type=int, default=8,
                    help="product pages visited for reviews per retailer "
                         "(default 8)")
    ap.add_argument("--scrolls", type=int, default=3,
                    help="page scrolls to trigger lazy loading (default 3)")
    ap.add_argument("--sleep", type=float, default=2.5)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--profile-dir", default=None)
    ap.add_argument("--kroger-location", default=None,
                    help="Kroger store locationId (enables prices)")
    ap.add_argument("--kroger-zip", default=None,
                    help="zip code -> nearest Kroger store for prices")
    ap.add_argument("--fresh", action="store_true",
                    help="overwrite CSVs instead of merging")
    ap.add_argument("--out", default="data/retailers")
    args = ap.parse_args()

    kroger_api = bool(os.environ.get("KROGER_CLIENT_ID")
                      and os.environ.get("KROGER_CLIENT_SECRET"))
    need_browser = [r for r in args.retailers
                    if not (r == "kroger" and kroger_api)]

    products, reviews = [], []
    fetcher = None
    try:
        if need_browser:
            fetcher = BrowserFetcher(headless=args.headless,
                                     profile_dir=args.profile_dir)
        for retailer in args.retailers:
            cfg = RETAILERS[retailer]
            print("== %s ==" % retailer)
            if retailer == "kroger" and kroger_api:
                loc = args.kroger_location
                if not loc and args.kroger_zip:
                    token = kroger_token(os.environ["KROGER_CLIENT_ID"],
                                         os.environ["KROGER_CLIENT_SECRET"])
                    loc = kroger_location_for_zip(args.kroger_zip, token)
                    print("  using Kroger locationId %s" % loc)
                products.extend(scrape_kroger_api(
                    args.terms, args.max_products, loc, args.sleep))
                continue
            retailer_products = []
            for term in args.terms:
                url = cfg["search_url"].format(q=urllib.parse.quote_plus(term))
                try:
                    blobs = fetcher.blobs(url, scrolls=args.scrolls)
                except BlockedError as e:
                    print("  BLOCKED on %s: %s — skipping retailer" % (retailer, e))
                    retailer_products = []
                    break
                got = harvest_products(blobs, cfg, term, retailer)
                kept = got[:args.max_products]
                retailer_products.extend(kept)
                print("  [%s:%s] %d harvested, kept %d"
                      % (retailer, term, len(got), len(kept)))
                polite_sleep(args.sleep)
            # de-dup within the retailer across terms
            uniq, seen = [], set()
            for p in retailer_products:
                if p["item_id"] in seen:
                    continue
                seen.add(p["item_id"])
                uniq.append(p)
            products.extend(uniq)
            if cfg["reviews"] and not args.no_reviews:
                with_links = [p for p in uniq if p.get("link")]
                for p in with_links[:args.review_products]:
                    try:
                        blobs = fetcher.blobs(p["link"], scrolls=5)
                    except BlockedError as e:
                        print("  BLOCKED on review pass: %s" % e)
                        break
                    got = harvest_reviews(blobs, p, p["search_term"])
                    reviews.extend(got)
                    print("  [%s] %s: %d reviews"
                          % (retailer, p["item_id"], len(got)))
                    polite_sleep(args.sleep)
    finally:
        if fetcher:
            fetcher.close()

    ppath = os.path.join(args.out, "products.csv")
    rpath = os.path.join(args.out, "reviews.csv")
    if args.fresh:
        write_csv(ppath, PRODUCT_COLUMNS, products)
        write_csv(rpath, REVIEW_COLUMNS, reviews)
    else:
        cols, merged = merge_rows(ppath, PRODUCT_COLUMNS, products, product_key)
        write_csv(ppath, cols, merged)
        cols, merged = merge_rows(rpath, REVIEW_COLUMNS, reviews, review_key)
        write_csv(rpath, cols, merged)
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit("BLOCKED: %s" % e)
