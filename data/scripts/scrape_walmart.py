#!/usr/bin/env python3
"""Scrape Walmart.com energy-drink products + customer reviews into clean CSVs.

Three backends:

  browser  — RECOMMENDED. Drives a real Chromium via Playwright, which passes
             Walmart's bot protection from a residential connection. If the
             "Robot or human?" press-and-hold challenge appears, solve it once
             in the opened browser window and the scrape continues. Setup:
               pip3 install playwright
               python3 -m playwright install chromium
  direct   — stdlib-only urllib fetch of the same pages. Kept as a zero-install
             fallback, but Walmart's bot protection (PerimeterX) fingerprints
             the TLS client, so plain Python requests are usually challenged
             even from residential IPs. Expect BLOCKED.
  serpapi  — SerpAPI's Walmart engines (search + product reviews). Works from
             anywhere but needs an API key in $SERPAPI_KEY (https://serpapi.com;
             free tier is 100 searches/month — budget with --max-products /
             --review-pages: each search page and each review page is 1 search).
             PAID beyond the free tier, so `auto` NEVER selects it — you must
             pass --backend serpapi explicitly to spend credits.

Usage (VS Code terminal on macOS):
  python3 data/scripts/scrape_walmart.py                       # auto backend
  python3 data/scripts/scrape_walmart.py --backend browser
  python3 data/scripts/scrape_walmart.py --backend serpapi \
      --search-pages 1 --max-products 6 --review-pages 2       # ~65 API calls
  python3 data/scripts/scrape_walmart.py --terms "Red Bull energy drink" \
      --max-products 20 --review-pages 3
  python3 data/scripts/scrape_walmart.py --fresh               # overwrite CSVs
  python3 data/scripts/scrape_walmart.py --detail              # +upc/gtin

Outputs (schema mirrors data/amazon/):
  data/walmart/products.csv   one row per product (price, rating, review count,
                              badges — incl. "N+ bought since yesterday", the
                              closest public proxy Walmart gives for purchases).
                              The `upc` column is the cross-retailer join key:
                              filled free when the search payload includes it,
                              otherwise only with --detail (one extra /ip/ page
                              load per product).
  data/walmart/reviews.csv    one row per customer review

Runs are INCREMENTAL: if an output CSV already exists, its rows are merged
with the fresh scrape — union of old + new, deduped on item_id (products) /
review_id (reviews), with the freshly scraped row winning on collision and
the file's existing column order preserved. Reviews already on disk also seed
the in-run dedupe so a re-run doesn't re-collect them. Pass --fresh to skip
the merge and overwrite from scratch.

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
    "item_id", "upc", "search_term", "title", "brand", "price_usd",
    "list_price_usd", "rating", "reviews_total", "seller", "sponsored",
    "badges", "bought_since_yesterday", "availability", "link", "scraped_at",
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


def iter_dicts(obj):
    """Yield every dict anywhere in a nested structure."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from iter_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_dicts(v)


# Walmart exposes the barcode under a few keys depending on the surface.
_UPC_KEYS = ("upc", "wupc", "gtin", "gtin13", "gtin14")


def extract_upc(obj):
    """First plausible UPC/GTIN (8-14 digits) found under any *_UPC_KEYS in a
    product blob, else None. Non-numeric or wrong-length values are skipped."""
    for key in _UPC_KEYS:
        for val in find_key(obj, key):
            digits = re.sub(r"\D", "", str(val))
            if 8 <= len(digits) <= 14:
                return digits
    return None


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


def read_csv_rows(path):
    """Return (rows, columns) already on disk at `path`, or ([], None)."""
    if not os.path.exists(path):
        return [], None
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = list(reader.fieldnames) if reader.fieldnames else None
    return rows, columns


def merge_rows(path, columns, rows, key):
    """Union freshly scraped `rows` with whatever CSV already sits at `path`.

    Makes runs incremental instead of destructive: dedupes on the `key`
    column (compared as strings, since disk rows come back as str), with the
    freshly scraped row winning on collision. Rows whose key is missing/empty
    get a unique synthetic key so they are never silently dropped. The
    existing file's column order is preserved when it has one. Returns
    (columns, merged_rows) and prints the kept-from-disk vs fresh split.
    """
    old_rows, old_columns = read_csv_rows(path)
    if old_columns:
        columns = old_columns
    merged, index = [], {}
    for n, row in enumerate(old_rows):
        val = row.get(key)
        k = str(val) if val not in (None, "") else ("__nokey_old__", n)
        index[k] = len(merged)
        merged.append(row)
    old_slots = set(range(len(merged)))  # merged indices still holding disk rows
    for n, row in enumerate(rows):
        val = row.get(key)
        k = str(val) if val not in (None, "") else ("__nokey_new__", n)
        if k in index:
            merged[index[k]] = row  # freshly scraped row wins
            old_slots.discard(index[k])
        else:
            index[k] = len(merged)
            merged.append(row)
    print(f"  merge {os.path.basename(path)}: kept {len(old_slots)} rows from "
          f"disk + {len(rows)} freshly scraped -> {len(merged)} total")
    return columns, merged


def review_key(row):
    """In-run review dedupe key: review_id when present, else a content tuple.

    Mirrors the historical str-or-tuple mix in main()'s `review_ids` set, but
    normalizes everything to strings so rows read back from reviews.csv (all
    str) match freshly scraped ones.
    """
    rid = row.get("review_id")
    if rid not in (None, ""):
        return str(rid)
    return (
        str(row.get("item_id") or ""),
        str(row.get("review_text") or ""),
        str(row.get("review_date") or ""),
    )


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


def stdlib_json_blobs(url):
    """Fetch a walmart.com page with urllib; only the SSR payload is visible."""
    return [extract_next_data(http_get(url))]


def direct_search(term, page, sleep, fetch_blobs=stdlib_json_blobs):
    url = "https://www.walmart.com/search?" + urllib.parse.urlencode(
        {"q": term, "page": page}
    )
    blobs = fetch_blobs(url)
    polite_sleep(sleep)

    # Products live under itemStacks[*].items[*]; rather than hard-coding the
    # full path (Walmart moves it), grab every dict that looks like a product.
    seen, items = set(), []
    for data in blobs:
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
        # Search results occasionally carry the UPC already — grab it free.
        # The optional --detail pass fills in the rest from the product page.
        "upc": extract_upc(it),
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


def direct_reviews(item_id, page, sleep, fetch_blobs=stdlib_json_blobs):
    url = (
        f"https://www.walmart.com/reviews/product/{item_id}?"
        + urllib.parse.urlencode({"page": page, "sort": "submission-desc"})
    )
    blobs = fetch_blobs(url)
    polite_sleep(sleep)

    # Reviews may be server-rendered in __NEXT_DATA__ or fetched client-side
    # via GraphQL (the browser backend captures those responses as extra
    # blobs) — scan every blob and dedupe.
    reviews, seen = [], set()
    for data in blobs:
        for block in find_key(data, "customerReviews"):
            if not isinstance(block, list):
                continue
            for r in block:
                if not isinstance(r, dict):
                    continue
                key = r.get("reviewId") or r.get("id") or id(r)
                if key in seen:
                    continue
                seen.add(key)
                reviews.append(r)
    return reviews


def product_detail_url(item_id):
    return f"https://www.walmart.com/ip/{item_id}"


def fetch_upc(item_id, sleep, fetch_blobs=stdlib_json_blobs):
    """Load a product's /ip/ detail page and return its UPC/GTIN, or None.

    Prefers the node whose id matches this product so a UPC from a "similar
    items" carousel on the same page isn't mistaken for the product's own.
    """
    blobs = fetch_blobs(product_detail_url(item_id))
    polite_sleep(sleep)
    for data in blobs:
        for node in iter_dicts(data):
            nid = node.get("usItemId") or node.get("id")
            if nid is not None and str(nid) == str(item_id):
                upc = extract_upc(node)
                if upc:
                    return upc
    # Fallback: any UPC on the page (last resort — may be a related item).
    for data in blobs:
        upc = extract_upc(data)
        if upc:
            return upc
    return None


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
# Browser backend — real Chromium via Playwright (best against bot protection)
# --------------------------------------------------------------------------

# Chromium's automation fingerprint is the easiest tell; hide the obvious ones.
_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = window.chrome || {runtime: {}};
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
"""


class BrowserFetcher:
    """Fetches pages in a real Chromium; reuses one window for the whole run.

    Uses a persistent profile dir so the human-verification cookie set by
    solving the press-and-hold challenge is reused on later runs — solve it
    once and you'll usually never see it again.
    """

    def __init__(self, headless=False, profile_dir=None, auto_hold=True):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise SystemExit(
                "The browser backend needs Playwright:\n"
                "  pip3 install playwright\n"
                "  python3 -m playwright install chromium"
            )
        self._headless = headless
        self._auto_hold = auto_hold
        profile_dir = profile_dir or os.path.expanduser(
            "~/.cache/energydrink-walmart-profile"
        )
        os.makedirs(profile_dir, exist_ok=True)
        self._pw = sync_playwright().start()
        # A persistent context keeps cookies/localStorage between runs.
        self._context = self._pw.chromium.launch_persistent_context(
            profile_dir,
            headless=headless,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            user_agent=UA,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        self._context.add_init_script(_STEALTH_JS)
        self._page = (
            self._context.pages[0] if self._context.pages
            else self._context.new_page()
        )
        # Keep every response of the current navigation; reviews are often
        # fetched client-side via GraphQL rather than server-rendered.
        self._responses = []
        self._page.on("response", lambda resp: self._responses.append(resp))
        self._warmed = False

    def _warmup(self):
        # Land on the homepage first (like a real visitor) so PerimeterX seeds
        # its baseline cookies before we hit a search URL — reduces how often
        # the press-and-hold challenge fires.
        if self._warmed:
            return
        self._warmed = True
        try:
            self._page.goto("https://www.walmart.com/",
                            wait_until="domcontentloaded", timeout=60_000)
            self._page.wait_for_timeout(2000 + int(random.uniform(0, 1500)))
        except Exception:
            pass

    def _looks_challenged(self):
        try:
            html = self._page.content()
        except Exception:
            return False
        return "Robot or human" in html or "px-captcha" in html

    def _try_auto_hold(self):
        """Best-effort: press and hold the challenge button.

        PerimeterX scores the *motion* of the hold, so a synthetic hold often
        still fails — this is a convenience attempt, not a guaranteed bypass.
        Returns True only if the challenge cleared afterwards.
        """
        for frame in self._page.frames:
            for sel in ("#px-captcha", "[id*=px-captcha]", "button",
                        "div[role=button]"):
                try:
                    btn = frame.query_selector(sel)
                except Exception:
                    btn = None
                if not btn:
                    continue
                try:
                    box = btn.bounding_box()
                    if not box:
                        continue
                    x = box["x"] + box["width"] / 2
                    y = box["y"] + box["height"] / 2
                    self._page.mouse.move(x, y)
                    self._page.mouse.down()
                    # Hold ~10s with tiny jitter to look less robotic.
                    for _ in range(20):
                        self._page.mouse.move(
                            x + random.uniform(-1.5, 1.5),
                            y + random.uniform(-1.5, 1.5),
                        )
                        time.sleep(0.5)
                    self._page.mouse.up()
                    self._page.wait_for_timeout(3000)
                    if not self._looks_challenged():
                        return True
                except Exception:
                    continue
        return False

    def get(self, url):
        self._warmup()
        self._responses.clear()
        self._page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        try:
            self._page.wait_for_selector(
                "script#__NEXT_DATA__", state="attached", timeout=10_000
            )
        except Exception:
            if self._looks_challenged():
                cleared = False
                if self._auto_hold:
                    print("  >> Walmart challenge — attempting auto press-and-"
                          "hold...")
                    cleared = self._try_auto_hold()
                if not cleared:
                    if self._headless:
                        raise BlockedError(
                            "Walmart challenge appeared and auto-hold failed in "
                            "headless mode — rerun without --headless and solve "
                            "it once in the window (the profile is saved, so "
                            "later runs should skip it)."
                        )
                    print("  >> Solve the press-and-hold in the browser window; "
                          "waiting up to 3 min... (only needed once — the "
                          "profile is saved for next time)")
            # Wait for either a solved challenge or a slow page.
            self._page.wait_for_selector(
                "script#__NEXT_DATA__", state="attached", timeout=180_000
            )
        # Give client-side data fetches (reviews GraphQL) a moment to land.
        try:
            self._page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        return self._page.content()

    def json_blobs(self, url):
        """SSR payload + any walmart.com JSON/GraphQL responses of this page."""
        blobs = [extract_next_data(self.get(url))]
        for resp in list(self._responses):
            u = resp.url
            if "walmart.com" not in u:
                continue
            if "graphql" not in u and "review" not in u.lower():
                continue
            try:
                blobs.append(json.loads(resp.text()))
            except Exception:
                continue
        return blobs

    def close(self):
        try:
            self._context.close()
            self._pw.stop()
        except Exception:
            pass


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
        "upc": extract_upc(it),
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
    ap.add_argument("--backend",
                    choices=["auto", "browser", "direct", "serpapi"],
                    default="auto")
    ap.add_argument("--headless", action="store_true",
                    help="browser backend: hide the window (challenges can't "
                         "be solved manually then)")
    ap.add_argument("--profile-dir", default=None,
                    help="browser backend: Chromium profile dir to persist the "
                         "human-verification cookie across runs (default "
                         "~/.cache/energydrink-walmart-profile)")
    ap.add_argument("--no-auto-hold", action="store_true",
                    help="browser backend: don't attempt the automated press-"
                         "and-hold; wait for you to solve it manually")
    ap.add_argument("--terms", nargs="+", default=DEFAULT_TERMS)
    ap.add_argument("--search-pages", type=int, default=2,
                    help="search result pages per term (default 2, ~40 items)")
    ap.add_argument("--max-products", type=int, default=25,
                    help="max products per term to keep (default 25)")
    ap.add_argument("--review-pages", type=int, default=3,
                    help="review pages per product, ~20 reviews each (default 3)")
    ap.add_argument("--detail", action="store_true",
                    help="fetch each product's /ip/ detail page to capture "
                         "upc/gtin (the cross-retailer join key). Adds ~1 page "
                         "load per product = more bot-wall exposure; off by "
                         "default. Ignored by the serpapi backend.")
    ap.add_argument("--sleep", type=float, default=2.5,
                    help="base delay between requests in seconds (default 2.5)")
    ap.add_argument("--out", default="data/walmart", help="output directory")
    ap.add_argument("--fresh", action="store_true",
                    help="overwrite the output CSVs from scratch instead of "
                         "merging with rows already on disk")
    args = ap.parse_args()

    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    backend = args.backend
    if backend == "auto":
        # Always prefer the FREE path. SerpAPI (paid, credits-per-call) is used
        # only when you ask for it explicitly with --backend serpapi — a merely
        # present SERPAPI_KEY must never silently spend credits.
        try:
            import playwright  # noqa: F401
            backend = "browser"
        except ImportError:
            backend = "direct"
    if backend == "serpapi" and not api_key:
        sys.exit("SERPAPI_KEY is not set — export it, or use --backend browser.")
    print(f"Backend: {backend}")

    fetcher = (
        BrowserFetcher(headless=args.headless, profile_dir=args.profile_dir,
                       auto_hold=not args.no_auto_hold)
        if backend == "browser" else None
    )
    fetch_blobs = fetcher.json_blobs if fetcher else stdlib_json_blobs
    walmart = backend in ("browser", "direct")

    products, product_ids = [], set()
    for term in args.terms:
        kept = 0
        for page in range(1, args.search_pages + 1):
            if walmart:
                raw_items = direct_search(term, page, args.sleep, fetch_blobs)
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
    if args.detail and walmart:
        need = [p for p in products if not p.get("upc")]
        print(f"  detail pass: fetching UPC for {len(need)}/{len(products)} "
              f"products missing it (+{len(need)} page loads)")
        for p in need:
            try:
                p["upc"] = fetch_upc(p["item_id"], args.sleep, fetch_blobs)
            except BlockedError:
                raise
            except Exception as e:  # one bad detail page shouldn't kill the run
                print(f"  ! detail failed for {p['item_id']}: {e}")
    elif args.detail and not walmart:
        print("  (--detail ignored: the serpapi backend has no detail fetch)")

    products_path = os.path.join(args.out, "products.csv")
    if args.fresh:
        write_csv(products_path, PRODUCT_COLUMNS, products)
    else:
        columns, merged = merge_rows(products_path, PRODUCT_COLUMNS, products,
                                     "item_id")
        write_csv(products_path, columns, merged)

    reviews_path = os.path.join(args.out, "reviews.csv")
    reviews, review_ids = [], set()
    if not args.fresh:
        # Seed the in-run dedupe with what's already on disk so a re-run
        # doesn't re-collect (and merge_rows then duplicate, for rows without
        # a review_id) reviews we already have.
        for old_row in read_csv_rows(reviews_path)[0]:
            review_ids.add(review_key(old_row))
    for i, product in enumerate(products, 1):
        term = product["search_term"]
        got = 0
        for page in range(1, args.review_pages + 1):
            try:
                if walmart:
                    raw = direct_reviews(product["item_id"], page, args.sleep,
                                         fetch_blobs)
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
                key = review_key(row)
                if key in review_ids:
                    continue
                review_ids.add(key)
                reviews.append(row)
                got += 1
        note = ""
        if got == 0 and (product.get("reviews_total") or 0) > 0:
            note = f" (listing reports {product['reviews_total']})"
        print(f"  [{i}/{len(products)}] {product['item_id']}: {got} reviews{note}")
    if args.fresh:
        write_csv(reviews_path, REVIEW_COLUMNS, reviews)
    else:
        columns, merged = merge_rows(reviews_path, REVIEW_COLUMNS, reviews,
                                     "review_id")
        write_csv(reviews_path, columns, merged)

    if fetcher:
        fetcher.close()
    print("Done. Next: rerun `python data/scripts/build_dashboard_json.py` if "
          "you wire Walmart into the dashboard aggregate.")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit(f"BLOCKED: {e}")
