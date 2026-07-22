#!/usr/bin/env python3
"""Scrape Kroger energy-drink products (+ reviews) — directly from kroger.com
or via Kroger's official free API.

Two backends:

  browser  — scrapes kroger.com DIRECTLY. A real Chromium (Playwright) loads
             the search page and product pages and this script harvests the
             product + review JSON the site fetches for itself, plus schema.org
             ld+json markup. This is what you asked for — a direct-website
             scraper — and it also captures ratings/reviews (the API does not).
             CAVEAT: kroger.com is behind Akamai bot management, the toughest
             wall of any retailer here. Run from a residential IP; if a
             challenge appears, solve it once in the window (the persistent
             profile remembers). Expect this to be flakier than the API.
  api      — Kroger's official Products API (developer.kroger.com — free app,
             OAuth2). Rock-solid, but returns NO ratings/reviews and needs a
             store for prices. Auto-selected when KROGER_CLIENT_ID /
             KROGER_CLIENT_SECRET are set (unless you pass --backend browser).

Setup (VS Code terminal on macOS):
  pip3 install playwright && python3 -m playwright install chromium   # browser
  # for the API: create an app at developer.kroger.com, then export:
  #   KROGER_CLIENT_ID=... KROGER_CLIENT_SECRET=...

Usage:
  python3 data/scripts/scrape_kroger.py                       # auto backend
  python3 data/scripts/scrape_kroger.py --backend browser     # force website
  python3 data/scripts/scrape_kroger.py --backend api --kroger-zip 10012
  python3 data/scripts/scrape_kroger.py --no-reviews          # skip review pass

Output (schema matches data/retailers/, retailer column = "kroger"):
  data/kroger/products.csv
  data/kroger/reviews.csv     (browser backend only — API exposes no reviews)

Runs are INCREMENTAL: existing rows merged, deduped on item_id / review_id,
fresh rows win. --fresh overwrites. Kroger publishes no unit sales; ratings +
review counts are the demand proxies.
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

# Schema mirrors data/retailers/ so Kroger rows fold into the same analysis.
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

ID_KEYS = ("upc", "productId", "product_id", "id")
BLOCK_MARKERS = ("Access Denied", "Pardon Our Interruption", "_Incapsula_",
                 "Reference #18", "Robot or human", "px-captcha",
                 "unusual traffic", "Request unsuccessful")
# A HARD deny, not a solvable interstitial: waiting/clicking in the window does
# nothing (the IP/fingerprint is flagged), so don't stall for 3 minutes —
# redirect straight to the free official API.
HARD_BLOCK_MARKERS = ("Access Denied", "Reference #18")

API_HINT = (
    "Use the free official API instead: create an app at developer.kroger.com, "
    "export KROGER_CLIENT_ID / KROGER_CLIENT_SECRET, and rerun (it auto-selects "
    "--backend api). Note: the API returns products + prices but no reviews."
)


class BlockedError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Helpers (self-contained; mirrors scrape_retailers.py conventions)
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


def walk_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_dicts(v)


def find_key(obj, key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from find_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_key(v, key)


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
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
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
    if not os.path.exists(path):
        return columns, list(new_rows)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_rows = list(reader)
        old_cols = reader.fieldnames or columns
    merged, seen, synth = [], {}, 0
    for row in old_rows + list(new_rows):
        key = key_fn(row)
        if key is None:
            synth += 1
            key = ("__synthetic__", synth)
        if key in seen:
            merged[seen[key]] = row
        else:
            seen[key] = len(merged)
            merged.append(row)
    print("  merge %s: %d on disk + %d scraped -> %d total"
          % (os.path.basename(path), len(old_rows), len(new_rows), len(merged)))
    return old_cols, merged


def product_key(row):
    iid = str(row.get("item_id") or "").strip()
    return ("kroger", iid) if iid else None


def review_key(row):
    rid = str(row.get("review_id") or "").strip()
    if rid:
        return ("kroger", rid)
    text = str(row.get("review_text") or "").strip()
    if text:
        return ("kroger", str(row.get("item_id") or ""), text,
                str(row.get("review_date") or ""))
    return None


# --------------------------------------------------------------------------
# Harvesting — products + reviews out of captured JSON (browser backend)
# --------------------------------------------------------------------------

TITLE_KEYS = ("description", "title", "name", "productName")
PRICE_KEYS = ("promo", "regular", "current", "price", "salePrice", "amount")
RATING_KEYS = ("averageRating", "average_rating", "ratingValue", "rating")
COUNT_KEYS = ("numberOfReviews", "review_count", "reviewCount",
              "totalReviewCount", "TotalReviewCount")
TEXT_KEYS = ("ReviewText", "reviewText", "review_text", "reviewBody", "text")
REVIEW_RATING_KEYS = ("Rating", "rating", "ratingValue")


def _id_of(d):
    for k in ID_KEYS:
        v = d.get(k)
        if v is not None and not isinstance(v, (dict, list)):
            s = str(v).strip()
            if 0 < len(s) < 64:
                return s
    return None


def _title_of(d):
    for k in TITLE_KEYS:
        v = d.get(k)
        if isinstance(v, str) and 3 <= len(v) <= 300:
            return v.strip()
    return None


def _price_of(d):
    # Kroger nests price under items[].price.{regular,promo}
    for pr in find_key(d, "price"):
        if isinstance(pr, dict):
            v = to_float(pr.get("promo")) or to_float(pr.get("regular"))
            if v and 0 < v < 10000:
                return v
    for k in PRICE_KEYS:
        v = to_float(d.get(k))
        if v and 0 < v < 10000:
            return v
    return None


def harvest_products(blobs, term):
    rows, seen = [], set()
    for blob in blobs:
        # schema.org Product markup first
        for d in walk_dicts(blob):
            if d.get("@type") in ("Product", ["Product"]):
                offers = d.get("offers") or {}
                agg = d.get("aggregateRating") or {}
                brand = d.get("brand")
                if isinstance(brand, dict):
                    brand = brand.get("name")
                iid = str(d.get("sku") or d.get("gtin13") or d.get("productID")
                          or "").strip()
                title = d.get("name")
                if iid and title and iid not in seen:
                    seen.add(iid)
                    rows.append(_row(iid, title, term, brand,
                                     to_float((offers or {}).get("price")),
                                     None, to_float(agg.get("ratingValue")),
                                     to_int(agg.get("reviewCount")),
                                     None, None, d.get("url")))
        # Kroger product JSON
        for d in walk_dicts(blob):
            iid = _id_of(d)
            if not iid or iid in seen:
                continue
            title = _title_of(d)
            if not title:
                continue
            price = _price_of(d)
            rating = None
            for k in RATING_KEYS:
                rating = to_float(d.get(k))
                if rating is not None and 0 < rating <= 5:
                    break
                rating = None
            if price is None and rating is None:
                continue  # skip nav/menu junk with no commercial signal
            items = d.get("items") or [{}]
            size = items[0].get("size") if items and isinstance(items[0], dict) else None
            list_price = None
            for pr in find_key(d, "price"):
                if isinstance(pr, dict) and pr.get("promo") and pr.get("regular"):
                    list_price = to_float(pr.get("regular"))
                    break
            seen.add(iid)
            rows.append(_row(iid, title, term, d.get("brand"), price,
                             list_price, rating,
                             _first_int(d, COUNT_KEYS), size, None,
                             "https://www.kroger.com/p/-/%s" % iid))
    return rows


def _first_int(d, keys):
    for k in keys:
        for v in find_key(d, k):
            iv = to_int(v)
            if iv is not None and 0 <= iv < 10**7:
                return iv
    return None


def _row(iid, title, term, brand, price, list_price, rating, count, size,
         avail, link):
    return {
        "retailer": "kroger", "item_id": iid, "search_term": term,
        "title": title,
        "brand": norm_brand(brand) or brand_from_title(title),
        "price_usd": price, "list_price_usd": list_price, "rating": rating,
        "reviews_total": count, "size": size, "availability": avail,
        "link": link, "scraped_at": now_stamp(),
    }


def harvest_reviews(blobs, product, term):
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
            rid = d.get("Id") or d.get("id") or d.get("reviewId")
            rid = str(rid).strip() if rid is not None else ""
            key = rid or (text, str(d.get("SubmissionTime") or ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "retailer": "kroger", "item_id": product["item_id"],
                "brand": product["brand"], "product_title": product["title"],
                "search_term": term, "review_id": rid,
                "review_title": d.get("Title") or d.get("title"),
                "review_text": text, "rating": rating,
                "review_date": parse_date(
                    d.get("SubmissionTime") or d.get("submissionTime")
                    or d.get("date")),
                "verified_purchase": bool(
                    d.get("IsVerifiedPurchaser") or d.get("verifiedPurchaser")),
                "helpful_votes": to_int(
                    d.get("TotalPositiveFeedbackCount")
                    or d.get("helpfulVotes")),
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
    def __init__(self, headless=False, profile_dir=None):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise SystemExit(
                "The browser backend needs Playwright:\n"
                "  pip3 install playwright\n"
                "  python3 -m playwright install chromium")
        profile_dir = profile_dir or os.path.expanduser(
            "~/.cache/energydrink-kroger-profile")
        os.makedirs(profile_dir, exist_ok=True)
        self._pw = sync_playwright().start()
        self._context = self._pw.chromium.launch_persistent_context(
            profile_dir, headless=headless,
            viewport={"width": 1366, "height": 900}, locale="en-US",
            user_agent=UA,
            args=["--disable-blink-features=AutomationControlled"])
        self._context.add_init_script(_STEALTH_JS)
        self._page = (self._context.pages[0] if self._context.pages
                      else self._context.new_page())
        self._responses = []
        self._page.on("response", lambda resp: self._responses.append(resp))
        self._headless = headless
        self._warmed = False

    def _warmup(self):
        # Land on the homepage first (like a real visitor) so Akamai sets its
        # cookies before we hit search — reduces how often it challenges.
        if self._warmed:
            return
        try:
            self._page.goto("https://www.kroger.com/", wait_until="domcontentloaded",
                            timeout=60_000)
            self._page.wait_for_timeout(2500)
        except Exception:
            pass
        self._warmed = True

    def blobs(self, url, scrolls=3):
        self._warmup()
        self._responses.clear()
        self._page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        try:
            self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        html = self._page.content()
        if any(m in html for m in BLOCK_MARKERS):
            self._wait_for_challenge()
        for _ in range(scrolls):
            try:
                self._page.mouse.wheel(0, 2400)
                self._page.wait_for_timeout(1000)
            except Exception:
                break
        html = self._page.content()
        out = []
        for resp in list(self._responses):
            try:
                ct = (resp.headers or {}).get("content-type", "")
                if "json" not in ct and "javascript" not in ct:
                    continue
                body = resp.text()
            except Exception:
                continue
            body = (body or "").lstrip()
            if not body.startswith(("{", "[")) or len(body) > 8_000_000:
                continue
            try:
                out.append(json.loads(body))
            except ValueError:
                continue
        for m in re.finditer(
                r'<script[^>]*type="application/(?:ld\+)?json"[^>]*>(.*?)</script>',
                html, re.DOTALL):
            try:
                out.append(json.loads(m.group(1)))
            except ValueError:
                continue
        return out

    def _wait_for_challenge(self):
        if any(m in self._page.content() for m in HARD_BLOCK_MARKERS):
            raise BlockedError(
                "kroger.com hard-blocked this request (Akamai 'Access "
                "Denied'). This is not a solvable challenge — waiting or "
                "clicking in the window won't clear it. " + API_HINT)
        if self._headless:
            raise BlockedError(
                "kroger.com served an Akamai challenge in headless mode — "
                "rerun without --headless and solve it once (profile saved), "
                "or use --backend api.")
        print("  >> Kroger bot challenge — solve it in the window; waiting "
              "up to 3 min...")
        deadline = time.time() + 180
        while time.time() < deadline:
            self._page.wait_for_timeout(3000)
            if not any(m in self._page.content() for m in BLOCK_MARKERS):
                return
        raise BlockedError("challenge not solved within 3 minutes. " + API_HINT)

    def close(self):
        try:
            self._context.close()
            self._pw.stop()
        except Exception:
            pass


def scrape_browser(terms, max_products, review_products, do_reviews, scrolls,
                   sleep, headless, profile_dir):
    fetcher = BrowserFetcher(headless=headless, profile_dir=profile_dir)
    products, reviews = [], []
    try:
        seen = set()
        for term in terms:
            url = ("https://www.kroger.com/search?query=%s&searchType=default_search"
                   % urllib.parse.quote_plus(term))
            got = harvest_products(fetcher.blobs(url, scrolls=scrolls), term)
            kept = 0
            for p in got:
                if p["item_id"] in seen or kept >= max_products:
                    continue
                seen.add(p["item_id"])
                products.append(p)
                kept += 1
            print("  [%s] %d harvested, kept %d" % (term, len(got), kept))
            polite_sleep(sleep)
        if do_reviews:
            with_links = [p for p in products if p.get("link")]
            for p in with_links[:review_products]:
                got = harvest_reviews(fetcher.blobs(p["link"], scrolls=5),
                                      p, p["search_term"])
                reviews.extend(got)
                print("  reviews %s: %d" % (p["item_id"], len(got)))
                polite_sleep(sleep)
    finally:
        fetcher.close()
    return products, reviews


# --------------------------------------------------------------------------
# Official API backend
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


def api_product_row(d, term):
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
        "rating": None, "reviews_total": None,
        "size": items[0].get("size") if items else None,
        "availability": (items[0].get("fulfillment") or {}).get("inStore")
        if items else None,
        "link": "https://www.kroger.com/p/-/%s" % (d.get("upc") or item_id),
        "scraped_at": now_stamp(),
    }


def scrape_api(terms, max_products, location_id, sleep):
    cid = os.environ["KROGER_CLIENT_ID"]
    secret = os.environ["KROGER_CLIENT_SECRET"]
    token = kroger_token(cid, secret)
    rows = []
    for term in terms:
        params = {"filter.term": term, "filter.limit": min(max_products, 50)}
        if location_id:
            params["filter.locationId"] = location_id
        try:
            data = kroger_get("products", params, token)
        except urllib.error.HTTPError as e:
            print("  ! API %s for %r" % (e.code, term))
            continue
        got = [api_product_row(d, term) for d in (data.get("data") or [])]
        rows.extend(got)
        print("  [%s] %d products%s" % (
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
    ap.add_argument("--backend", choices=["auto", "browser", "api"],
                    default="auto",
                    help="auto = api if KROGER_CLIENT_ID/SECRET set, else browser")
    ap.add_argument("--terms", nargs="+", default=DEFAULT_TERMS)
    ap.add_argument("--max-products", type=int, default=25,
                    help="max products kept per term (default 25)")
    ap.add_argument("--no-reviews", action="store_true",
                    help="browser: skip the product-page review pass")
    ap.add_argument("--review-products", type=int, default=8,
                    help="browser: product pages visited for reviews (default 8)")
    ap.add_argument("--scrolls", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=2.5)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--profile-dir", default=None)
    ap.add_argument("--kroger-location", default=None,
                    help="api: store locationId (enables prices)")
    ap.add_argument("--kroger-zip", default=None,
                    help="api: zip -> nearest store for prices")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out", default="data/kroger")
    args = ap.parse_args()

    has_creds = bool(os.environ.get("KROGER_CLIENT_ID")
                     and os.environ.get("KROGER_CLIENT_SECRET"))
    backend = args.backend
    if backend == "auto":
        backend = "api" if has_creds else "browser"
    if backend == "api" and not has_creds:
        sys.exit("--backend api needs KROGER_CLIENT_ID and "
                 "KROGER_CLIENT_SECRET (create a free app at "
                 "developer.kroger.com), or use --backend browser.")
    print("Backend: %s" % backend)

    reviews = []
    if backend == "api":
        loc = args.kroger_location
        if not loc and args.kroger_zip:
            token = kroger_token(os.environ["KROGER_CLIENT_ID"],
                                 os.environ["KROGER_CLIENT_SECRET"])
            loc = kroger_location_for_zip(args.kroger_zip, token)
            print("  using locationId %s" % loc)
        products = scrape_api(args.terms, args.max_products, loc, args.sleep)
    else:
        products, reviews = scrape_browser(
            args.terms, args.max_products, args.review_products,
            not args.no_reviews, args.scrolls, args.sleep, args.headless,
            args.profile_dir)

    ppath = os.path.join(args.out, "products.csv")
    rpath = os.path.join(args.out, "reviews.csv")
    if args.fresh:
        write_csv(ppath, PRODUCT_COLUMNS, products)
        if reviews:
            write_csv(rpath, REVIEW_COLUMNS, reviews)
    else:
        cols, merged = merge_rows(ppath, PRODUCT_COLUMNS, products, product_key)
        write_csv(ppath, cols, merged)
        if reviews or os.path.exists(rpath):
            cols, merged = merge_rows(rpath, REVIEW_COLUMNS, reviews, review_key)
            write_csv(rpath, cols, merged)
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit("BLOCKED: %s" % e)
