#!/usr/bin/env python3
"""Scrape Amazon.com energy-drink products + customer reviews into clean CSVs.

FREE replacement for the paid scraper exports that originally produced
data/amazon/products.csv and data/amazon/reviews.csv. Same schemas, and reruns
MERGE into the existing CSVs (deduped on asin / review_id, fresh rows win), so
scraping is incremental rather than destructive.

One backend:

  browser  — Drives a real Chromium via Playwright, which passes Amazon's bot
             checks from a residential connection. Amazon's challenge is a
             text CAPTCHA ("Type the characters you see" at
             /errors/validateCaptcha) rather than Walmart's press-and-hold:
             if it appears, type the characters once in the opened window and
             the scrape continues — the persistent profile remembers the pass
             so later runs usually skip it.

Setup (macOS, VS Code terminal):
  pip3 install playwright
  python3 -m playwright install chromium

Usage (macOS, VS Code terminal — run from the repo root):
  python3 data/scripts/scrape_amazon.py                              # default full run
  python3 data/scripts/scrape_amazon.py --no-details                 # search pages only
  python3 data/scripts/scrape_amazon.py --terms "Red Bull energy drink" \
      --search-pages 1 --max-products 10
  python3 data/scripts/scrape_amazon.py --login --review-pages 5     # deep reviews (see warning)

Reviews — an important limitation: since 2024 Amazon gates the paginated
/product-reviews/<ASIN> pages behind sign-in; only the ~8 "top reviews" shown
on each product page are public. By default this script collects those on-page
reviews (free, no account needed). --login opens amazon.com in the window so
you can sign in once (the persistent profile keeps the session), after which
--review-pages N paginates the full review history per product.
WARNING: scraping while signed in is against Amazon's Terms of Service and
risks the account you use — that is your informed choice to make; the default
stays signed out and collects only the public on-page reviews.

Outputs (schema matches the committed files exactly):
  data/amazon/products.csv   one row per product, deduped on asin
  data/amazon/reviews.csv    one row per customer review, deduped on review_id
"""

import argparse
import csv
import datetime as dt
import os
import random
import re
import sys
import time
import urllib.parse
from html.parser import HTMLParser

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# Same brand terms as the original Amazon corpus (see data/amazon/products.csv),
# plus the generic category query so bestsellers of every brand show up.
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

# Must match the committed data/amazon/*.csv headers EXACTLY.
PRODUCT_COLUMNS = [
    "asin", "search_term", "title", "brand", "price_usd", "rating",
    "ratings_total", "reviews_total", "categories", "description",
    "feature_bullets", "link", "scraped_at",
]
REVIEW_COLUMNS = [
    "asin", "brand", "product_title", "search_term", "review_id",
    "review_title", "review_text", "rating", "review_date",
    "review_country", "verified_purchase", "helpful_votes",
]

RETRIES = 4  # navigation attempts per URL (exponential backoff on 429/5xx)


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
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return s  # keep raw rather than lose it


def parse_review_date_line(text):
    """'Reviewed in the United States on January 5, 2026' -> (country, ISO date).

    The country is kept exactly as Amazon prints it ('the United States',
    'Germany', ...) to match the committed reviews.csv values.
    """
    m = re.search(r"Reviewed in (.+?) on (.+)$", (text or "").strip())
    if not m:
        return None, None
    return m.group(1).strip(), parse_review_date(m.group(2))


def parse_star_rating(text):
    """'4.7 out of 5 stars' -> 4.7 (None if the pattern is absent)."""
    m = re.search(r"([\d.]+)\s+out of\s+5", text or "")
    return float(m.group(1)) if m else None


def parse_helpful_votes(text):
    """'12 people found this helpful' -> 12; 'One person ...' -> 1."""
    if not text:
        return None
    s = str(text).strip()
    if re.match(r"(?i)one person", s):
        return 1
    return to_int(s)


def polite_sleep(base):
    time.sleep(base + random.uniform(0, base))


def write_csv(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore",
                                restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {path} ({len(rows)} rows)")


def merge_with_existing(path, new_rows, key_column, fallback_columns):
    """Union `new_rows` with any CSV already at `path`, preferring new rows.

    Rows are keyed on `key_column`; rows with a blank key fall back to the
    tuple of `fallback_columns`. Existing row order is preserved (fresh rows
    replace stale ones in place; brand-new rows are appended), so reruns are
    incremental instead of destructive.
    """
    def key(row):
        k = str(row.get(key_column) or "").strip()
        if k:
            return ("k", k)
        return ("fb",) + tuple(
            str(row.get(c) or "").strip() for c in fallback_columns
        )

    merged = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                merged[key(row)] = row
        if merged:
            print(f"  merging with {len(merged)} existing rows in {path}")
    for row in new_rows:
        merged[key(row)] = row  # fresh row wins, position preserved
    return list(merged.values())


# --------------------------------------------------------------------------
# Tiny tolerant HTML tree (stdlib html.parser) — Amazon pages are too nested
# for one-shot regexes, and this keeps the script dependency-free.
# --------------------------------------------------------------------------

_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag, attrs=()):
        self.tag = tag
        self.attrs = {k: (v if v is not None else "") for k, v in attrs}
        self.children = []  # Node and str entries, interleaved

    def classes(self):
        return self.attrs.get("class", "").split()

    def text(self):
        """All descendant text, space-joined, whitespace-collapsed."""
        parts, stack = [], [self]
        while stack:
            n = stack.pop()
            if isinstance(n, str):
                parts.append(n)
            else:
                stack.extend(reversed(n.children))
        return re.sub(r"\s+", " ", " ".join(parts)).strip()


class _TreeBuilder(HTMLParser):
    """Builds a Node tree; tolerates Amazon's unclosed/mismatched tags."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("[document]")
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self._stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self._stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        # Pop back to the matching open tag; ignore stray close tags.
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                return

    def handle_data(self, data):
        if data and data.strip():
            self._stack[-1].children.append(data)


def parse_html(html):
    builder = _TreeBuilder()
    builder.feed(html or "")
    return builder.root


def iter_nodes(root):
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(
            c for c in reversed(node.children) if isinstance(c, Node)
        )


def find_all(root, tag=None, attrs=None):
    """Descendants (document order) matching tag + attrs.

    attrs values: exact string match, or a callable predicate; the "class"
    key matches a single class token (like a CSS .class selector).
    """
    out = []
    for node in iter_nodes(root):
        if tag and node.tag != tag:
            continue
        ok = True
        for k, want in (attrs or {}).items():
            have = node.attrs.get(k)
            if have is None:
                ok = False
                break
            if k == "class":
                if want not in have.split():
                    ok = False
                    break
            elif callable(want):
                if not want(have):
                    ok = False
                    break
            elif have != want:
                ok = False
                break
        if ok:
            out.append(node)
    return out


def find_first(root, tag=None, attrs=None):
    found = find_all(root, tag, attrs)
    return found[0] if found else None


# --------------------------------------------------------------------------
# Parsers — search results, product detail, review blocks, CAPTCHA detection
# --------------------------------------------------------------------------

_CAPTCHA_MARKERS = (
    "/errors/validateCaptcha",
    "Type the characters you see",
    "Enter the characters you see",
    "api-services-support@amazon.com",
)


def looks_captcha(html, url=""):
    if "/errors/validateCaptcha" in (url or ""):
        return True
    return any(marker in (html or "") for marker in _CAPTCHA_MARKERS)


def parse_search_page(html):
    """Product cards from a rendered /s?k=... page.

    Cards are div[data-component-type="s-search-result"] with a data-asin;
    empty data-asin (ad shells) are skipped.
    """
    root = parse_html(html)
    products = []
    for card in find_all(root, "div",
                         {"data-component-type": "s-search-result"}):
        asin = (card.attrs.get("data-asin") or "").strip()
        if not asin:
            continue

        h2 = find_first(card, "h2")
        title = h2.text() if h2 else ""
        if h2 and not title:
            title = (h2.attrs.get("aria-label") or "").strip()

        # First non-struck price (span.a-price without a-text-price).
        price = None
        for pr in find_all(card, "span", {"class": "a-price"}):
            if "a-text-price" in pr.classes():
                continue  # struck-through list price
            off = find_first(pr, "span", {"class": "a-offscreen"})
            if off:
                price = to_float(off.text())
                break

        # Star rating lives in a span.a-icon-alt like "4.7 out of 5 stars".
        rating = None
        for alt in find_all(card, "span", {"class": "a-icon-alt"}):
            rating = parse_star_rating(alt.text())
            if rating is not None:
                break

        # Ratings count: the underlined number next to the stars.
        ratings_total = None
        cnt = find_first(card, "span", {"class": "s-underline-text"})
        if cnt:
            ratings_total = to_int(cnt.text())
        if ratings_total is None:  # fallback: aria-label="21,467 ratings"
            lab = find_first(card, "a", {
                "aria-label": lambda v: re.search(r"[\d,]+\s+ratings?", v),
            })
            if lab:
                ratings_total = to_int(lab.attrs.get("aria-label"))

        products.append({
            "asin": asin,
            "title": title,
            "price_usd": price,
            "rating": rating,
            "ratings_total": ratings_total,
            "link": "https://www.amazon.com/dp/" + asin,
        })
    return products


def extract_reviews(root):
    """Review blocks (data-hook="review") from a parsed page — used for both
    the on-page top reviews of /dp/<ASIN> and /product-reviews/<ASIN> pages.
    """
    reviews = []
    for block in find_all(root, None, {"data-hook": "review"}):
        title_node = find_first(block, None, {"data-hook": "review-title"})
        title = None
        if title_node:
            # The title anchor also wraps the star icon; keep the first span
            # that isn't the icon's alt text or an a-letter-space spacer.
            for span in find_all(title_node, "span"):
                cls = span.classes()
                if "a-icon-alt" in cls or "a-letter-space" in cls:
                    continue
                txt = span.text()
                if txt and "out of 5 stars" not in txt:
                    title = txt
                    break
            if title is None:
                title = re.sub(r"^\s*[\d.]+ out of 5 stars\s*", "",
                               title_node.text()).strip() or None

        rating = None
        for hook in ("review-star-rating", "cmps-review-star-rating"):
            star = find_first(block, None, {"data-hook": hook})
            if star:
                rating = parse_star_rating(star.text())
                break
        if rating is not None and rating == int(rating):
            rating = int(rating)  # star ratings are whole numbers

        body_node = find_first(block, None, {"data-hook": "review-body"})
        body = body_node.text() if body_node else None
        if body:
            body = re.sub(r"\s*Read more$", "", body)

        date_node = find_first(block, None, {"data-hook": "review-date"})
        country, date = parse_review_date_line(
            date_node.text() if date_node else None
        )

        helpful_node = find_first(
            block, None, {"data-hook": "helpful-vote-statement"}
        )

        reviews.append({
            "review_id": block.attrs.get("id"),
            "review_title": title,
            "review_text": body,
            "rating": rating,
            "review_date": date,
            "review_country": country,
            "verified_purchase": bool(
                find_first(block, None, {"data-hook": "avp-badge"})
            ),
            "helpful_votes": parse_helpful_votes(
                helpful_node.text() if helpful_node else None
            ),
        })
    return reviews


def parse_detail_page(html):
    """Title, bullets, description, breadcrumb categories and the on-page
    top reviews from a rendered /dp/<ASIN> page."""
    root = parse_html(html)

    t = find_first(root, None, {"id": "productTitle"})
    title = t.text() if t else None

    bullets = []
    fb = (find_first(root, None, {"id": "feature-bullets"})
          or find_first(root, None, {"id": "featurebullets_feature_div"}))
    if fb:
        for li in find_all(fb, "li"):
            if "aok-hidden" in li.classes():
                continue
            txt = li.text()
            if txt and not txt.startswith("Make sure this fits"):
                bullets.append(txt)

    desc_node = find_first(root, None, {"id": "productDescription"})
    description = desc_node.text() if desc_node else None

    categories = []
    crumbs = find_first(root, None, {
        "id": lambda v: v.startswith("wayfinding-breadcrumbs"),
    })
    if crumbs:
        categories = [a.text() for a in find_all(crumbs, "a") if a.text()]

    return {
        "title": title,
        "feature_bullets": bullets,
        "description": description,
        "categories": categories,
        "reviews": extract_reviews(root),
    }


def parse_reviews_page(html):
    """Review blocks from a rendered /product-reviews/<ASIN> page (same
    data-hook="review" markup as the on-page top reviews)."""
    return extract_reviews(parse_html(html))


# --------------------------------------------------------------------------
# Browser backend — real Chromium via Playwright (the only workable free path;
# Amazon blocks plain HTTP clients on TLS/header fingerprint alone)
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

    Uses a persistent profile dir so the cookie set by solving Amazon's text
    CAPTCHA (and any --login session) is reused on later runs — solve it once
    and you'll usually never see it again.
    """

    def __init__(self, headless=False, profile_dir=None):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise SystemExit(
                "The browser backend needs Playwright:\n"
                "  pip3 install playwright\n"
                "  python3 -m playwright install chromium"
            )
        self._headless = headless
        profile_dir = profile_dir or os.path.expanduser(
            "~/.cache/energydrink-amazon-profile"
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
        # Keep every response of the current navigation (parity with the
        # Walmart scraper; handy if Amazon moves data into XHR responses).
        self._responses = []
        self._page.on("response", lambda resp: self._responses.append(resp))

    def url(self):
        return self._page.url

    def _looks_captcha(self):
        try:
            return looks_captcha(self._page.content(), self._page.url)
        except Exception:
            return False

    def _wait_out_captcha(self):
        """Block until the user solves Amazon's text CAPTCHA in the window."""
        if self._headless:
            raise BlockedError(
                "Amazon served its text CAPTCHA and the window is hidden — "
                "rerun without --headless and type the characters once in "
                "the opened window (the persistent profile remembers the "
                "pass, so later runs should skip it)."
            )
        print("  >> Amazon CAPTCHA — type the characters in the browser "
              "window; waiting up to 3 min... (usually needed once — the "
              "profile is saved for next time)")
        deadline = time.time() + 180
        while time.time() < deadline:
            time.sleep(3)
            if not self._looks_captcha():
                return
        raise BlockedError(
            "The CAPTCHA wasn't solved within 3 minutes — rerun and solve "
            "it in the browser window."
        )

    def get(self, url, wait_selector=None):
        """Navigate with retries/backoff on 429/5xx, then handle the CAPTCHA
        interstitial, then return the rendered HTML."""
        for attempt in range(RETRIES):
            self._responses.clear()
            try:
                resp = self._page.goto(url, wait_until="domcontentloaded",
                                       timeout=60_000)
            except Exception as e:
                if attempt == RETRIES - 1:
                    raise BlockedError(
                        f"Navigation to {url} kept failing ({e}). Check that "
                        "this machine can reach amazon.com (sandboxed cloud "
                        "environments usually can't — run from your own "
                        "residential connection)."
                    )
                polite_sleep(2 ** attempt * 2)
                continue
            status = resp.status if resp else 200
            if status == 429 or status >= 500:
                if attempt == RETRIES - 1:
                    raise BlockedError(
                        f"HTTP {status} from amazon.com after {RETRIES} "
                        "attempts — you're being throttled. Raise --sleep "
                        "and retry later."
                    )
                wait = 2 ** attempt * 5
                print(f"  >> HTTP {status} — backing off {wait}s...")
                time.sleep(wait + random.uniform(0, 3))
                continue
            break
        if self._looks_captcha():
            self._wait_out_captcha()
            # Amazon usually bounces back to the requested page after the
            # solve; re-navigate once to be certain we're on the right URL.
            try:
                self._page.goto(url, wait_until="domcontentloaded",
                                timeout=60_000)
            except Exception:
                pass
        if wait_selector:
            try:
                self._page.wait_for_selector(wait_selector, state="attached",
                                             timeout=15_000)
            except Exception:
                pass  # zero-result pages / layout drift — parse what's there
        # Give client-side widgets (reviews, prices) a moment to land.
        try:
            self._page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        return self._page.content()

    def login(self, timeout=300):
        """Open amazon.com and wait for the user to sign in (see the ToS
        warning in the module docstring). The persistent profile keeps the
        session for later runs."""
        if self._headless:
            raise SystemExit(
                "--login needs a visible browser window — drop --headless."
            )
        self._page.goto("https://www.amazon.com/",
                        wait_until="domcontentloaded", timeout=60_000)
        if self._looks_captcha():
            self._wait_out_captcha()
        print("  >> Sign in to Amazon in the browser window (Account & Lists "
              "-> Sign in); waiting up to 5 min. The profile keeps the "
              "session, so this is one-time. Reminder: scraping while "
              "signed in is against Amazon ToS and risks the account.")
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                greeting = self._page.evaluate(
                    "() => {"
                    "  const el = document.querySelector("
                    "    '#nav-link-accountList-nav-line-1');"
                    "  return el ? el.textContent : '';"
                    "}"
                ) or ""
            except Exception:
                greeting = ""
            if greeting.strip() and "sign in" not in greeting.lower():
                print(f"  >> Signed in ({greeting.strip()}).")
                return True
            time.sleep(5)
        print("  !! Could not confirm the sign-in — continuing anyway "
              "(paginated reviews may hit the sign-in wall).")
        return False

    def close(self):
        try:
            self._context.close()
            self._pw.stop()
        except Exception:
            pass


# --------------------------------------------------------------------------
# Row builders
# --------------------------------------------------------------------------

def product_row(card, term):
    return {
        "asin": card["asin"],
        "search_term": term,
        "title": card["title"],
        "brand": brand_from_title(card["title"]),
        "price_usd": card["price_usd"],
        "rating": card["rating"],
        "ratings_total": card["ratings_total"],
        "reviews_total": None,  # Amazon stopped exposing this; stays blank
        "categories": None,     # filled from the detail page
        "description": None,    # filled from the detail page
        "feature_bullets": None,  # filled from the detail page
        "link": card["link"],
        "scraped_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def enrich_product(row, detail):
    if detail.get("title"):
        row["title"] = detail["title"]
        row["brand"] = row["brand"] or brand_from_title(detail["title"])
    if detail.get("categories"):
        row["categories"] = "; ".join(detail["categories"])
    if detail.get("description"):
        row["description"] = detail["description"]
    if detail.get("feature_bullets"):
        row["feature_bullets"] = " | ".join(detail["feature_bullets"])


def review_row(r, product):
    return {
        "asin": product["asin"],
        "brand": product["brand"],
        "product_title": product["title"],
        "search_term": product["search_term"],
        "review_id": r["review_id"],
        "review_title": r["review_title"],
        "review_text": r["review_text"],
        "rating": r["rating"],
        "review_date": r["review_date"],
        "review_country": r["review_country"],
        "verified_purchase": r["verified_purchase"],
        "helpful_votes": r["helpful_votes"],
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--backend", choices=["browser"], default="browser",
                    help="only 'browser' — Amazon fingerprints and blocks "
                         "plain HTTP clients, so there is no direct backend")
    ap.add_argument("--headless", action="store_true",
                    help="hide the browser window (the CAPTCHA can't be "
                         "solved manually then)")
    ap.add_argument("--profile-dir", default=None,
                    help="Chromium profile dir persisting the CAPTCHA pass "
                         "and any --login session across runs (default "
                         "~/.cache/energydrink-amazon-profile)")
    ap.add_argument("--login", action="store_true",
                    help="wait for you to sign in to Amazon first, enabling "
                         "--review-pages pagination. WARNING: scraping while "
                         "signed in is against Amazon ToS and risks the "
                         "account — see the docstring")
    ap.add_argument("--terms", nargs="+", default=DEFAULT_TERMS)
    ap.add_argument("--search-pages", type=int, default=2,
                    help="search result pages per term (default 2)")
    ap.add_argument("--max-products", type=int, default=25,
                    help="max products per term to keep (default 25)")
    ap.add_argument("--no-details", action="store_true",
                    help="skip /dp/<ASIN> detail pages (loses description, "
                         "bullets, categories and the on-page top reviews)")
    ap.add_argument("--review-pages", type=int, default=0,
                    help="paginated /product-reviews pages per product, ~10 "
                         "reviews each (default 0 = the free on-page top "
                         "reviews only; >0 effectively requires --login)")
    ap.add_argument("--sleep", type=float, default=2.5,
                    help="base delay between page loads in seconds; actual "
                         "delay is base + random jitter (default 2.5)")
    ap.add_argument("--out", default="data/amazon", help="output directory")
    args = ap.parse_args()

    if args.review_pages > 0 and not args.login:
        print("NOTE: --review-pages > 0 without --login — Amazon has gated "
              "paginated reviews behind sign-in since 2024, so this will "
              "likely stop at the sign-in wall unless the saved profile "
              "already has a session.")
    print(f"Backend: {args.backend}")

    fetcher = BrowserFetcher(headless=args.headless,
                             profile_dir=args.profile_dir)
    try:
        if args.login:
            fetcher.login()

        # ---- search pages -> product rows --------------------------------
        products, seen_asins = [], set()
        for term in args.terms:
            kept = 0
            for page in range(1, args.search_pages + 1):
                url = "https://www.amazon.com/s?" + urllib.parse.urlencode(
                    {"k": term, "page": page}
                )
                html = fetcher.get(
                    url,
                    wait_selector='div[data-component-type="s-search-result"]',
                )
                polite_sleep(args.sleep)
                cards = parse_search_page(html)
                for card in cards:
                    if kept >= args.max_products:
                        break
                    if card["asin"] in seen_asins:
                        continue
                    seen_asins.add(card["asin"])
                    products.append(product_row(card, term))
                    kept += 1
                print(f"  [{term}] page {page}: {len(cards)} items, "
                      f"kept {kept}")
                if kept >= args.max_products:
                    break

        # ---- detail pages + reviews ---------------------------------------
        reviews, review_keys = [], set()

        def keep_review(row):
            key = row["review_id"] or (
                row["asin"], row["review_title"], row["review_date"]
            )
            if key in review_keys:
                return False
            review_keys.add(key)
            reviews.append(row)
            return True

        review_pages = args.review_pages
        for i, product in enumerate(products, 1):
            got = 0
            if not args.no_details:
                try:
                    html = fetcher.get(product["link"],
                                       wait_selector="#productTitle")
                    polite_sleep(args.sleep)
                    detail = parse_detail_page(html)
                    enrich_product(product, detail)
                    for r in detail["reviews"]:
                        if keep_review(review_row(r, product)):
                            got += 1
                except BlockedError:
                    raise
                except Exception as e:  # one bad product shouldn't kill it
                    print(f"  ! detail failed for {product['asin']}: {e}")
            for page in range(1, review_pages + 1):
                url = (
                    f"https://www.amazon.com/product-reviews/"
                    f"{product['asin']}?" + urllib.parse.urlencode(
                        {"pageNumber": page, "sortBy": "recent"}
                    )
                )
                try:
                    html = fetcher.get(url)
                    polite_sleep(args.sleep)
                except BlockedError:
                    raise
                except Exception as e:
                    print(f"  ! reviews failed for {product['asin']}: {e}")
                    break
                if "/ap/signin" in fetcher.url():
                    print("  !! Amazon's sign-in wall is blocking paginated "
                          "reviews (required since 2024). Rerun with --login "
                          "to enable them — skipping pagination for the rest "
                          "of this run; the free on-page top reviews are "
                          "still collected.")
                    review_pages = 0
                    break
                new = sum(
                    keep_review(review_row(r, product))
                    for r in parse_reviews_page(html)
                )
                got += new
                if new == 0:
                    break  # last page reached (or no public reviews)
            print(f"  [{i}/{len(products)}] {product['asin']}: "
                  f"{got} reviews")
    finally:
        fetcher.close()

    # ---- merge with the committed CSVs and write --------------------------
    products_path = os.path.join(args.out, "products.csv")
    reviews_path = os.path.join(args.out, "reviews.csv")
    write_csv(products_path, PRODUCT_COLUMNS,
              merge_with_existing(products_path, products,
                                  key_column="asin",
                                  fallback_columns=("link", "title")))
    write_csv(reviews_path, REVIEW_COLUMNS,
              merge_with_existing(reviews_path, reviews,
                                  key_column="review_id",
                                  fallback_columns=("asin", "review_title",
                                                    "review_date")))
    print("Done. Next: rerun `python3 data/scripts/build_dashboard_json.py` "
          "to refresh the dashboard aggregate.")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit(f"BLOCKED: {e}")
