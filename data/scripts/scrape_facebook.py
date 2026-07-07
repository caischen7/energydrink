#!/usr/bin/env python3
"""Scrape Facebook/Meta energy-drink brand ADVERTISING from the Meta Ad
Library — the public ads-transparency database at facebook.com/ads/library.

Why ads instead of posts: Facebook requires login for almost all content and
its Graph API needs app review for public posts, but the Ad Library is public
BY DESIGN (no login) and covers every active ad a brand runs across Facebook,
Instagram, Messenger and Audience Network. That makes it the one free,
reliable Facebook window — and a signal no other source in this repo has:
**marketing intensity and messaging** per brand (what claims they push, which
platforms they buy, when campaigns start).

How it works: Playwright loads Ad Library search results for each brand query
and harvests ad objects from the JSON/GraphQL responses the page fetches
(same capture pattern as the retailer/TikTok scrapers). Setup:
  pip3 install playwright && python3 -m playwright install chromium   # once

Usage (VS Code terminal on macOS):
  python3 data/scripts/scrape_facebook.py
  python3 data/scripts/scrape_facebook.py --queries "Celsius" "Alani Nu"
  python3 data/scripts/scrape_facebook.py --country US --scrolls 8

Output:
  data/facebook/ads.csv   one row per ad, deduped on ad_id (ad_archive_id)

Runs are INCREMENTAL: existing rows merged, deduped on ad_id, fresh rows win.
--fresh overwrites.

Creative angles this data supports:
- marketing-intensity ranking: active-ad counts per brand over time
- messaging themes: mine ad_text for the claims brands lead with
  (zero sugar / focus / hydration / taste) and compare against what consumers
  actually praise or complain about in the review corpora
- platform mix: who buys Instagram vs Facebook vs Audience Network
- campaign cadence: start_date clustering shows launch pushes.

If you later want organic posts too, the practical free-ish routes are the
official Meta Content Library (research access application, .edu helps) —
regular Graph API access to public page content requires app review.
"""

import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import sys
import time
import urllib.parse

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

DEFAULT_QUERIES = [
    "Monster Energy", "Red Bull", "Celsius", "Alani Nu", "Ghost Energy",
    "Rockstar Energy", "Reign Body Fuel", "Prime Energy", "Zoa Energy",
    "Bang Energy",
]

BRAND_ALIASES = {
    "celsius": "Celsius", "celsiusofficial": "Celsius",
    "red bull": "Red Bull", "redbull": "Red Bull",
    "monster": "Monster", "monsterenergy": "Monster",
    "monster energy": "Monster",
    "liquid i.v.": "Liquid I.V.", "liquid iv": "Liquid I.V.",
    "ghost": "Ghost", "ghost energy": "Ghost",
    "bang": "Bang", "bangenergy": "Bang", "bang energy": "Bang",
    "alani nu": "Alani Nu", "alaninutrition": "Alani Nu", "alani": "Alani Nu",
    "rockstar": "Rockstar", "rockstarenergy": "Rockstar",
    "rockstar energy": "Rockstar",
    "5-hour energy": "5-hour Energy", "5 hour energy": "5-hour Energy",
    "nos": "NOS",
    "reign": "Reign", "reignbodyfuel": "Reign", "reign body fuel": "Reign",
    "zoa": "Zoa", "zoaenergy": "Zoa", "zoa energy": "Zoa",
    "prime": "Prime", "drinkprime": "Prime", "prime energy": "Prime",
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

AD_COLUMNS = [
    "ad_id", "query", "brand", "page_name", "ad_text", "cta", "start_date",
    "end_date", "active", "platforms", "snapshot_url", "scraped_at",
]

BLOCK_MARKERS = ("You must log in to continue", "checkpoint required",
                 "Temporarily Blocked", "security check to continue")

SEARCH_URL = (
    "https://www.facebook.com/ads/library/?active_status=all&ad_type=all"
    "&country={country}&q={q}&search_type=keyword_unordered&media_type=all"
)


class BlockedError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def norm_brand(value):
    if not value:
        return None
    return BRAND_ALIASES.get(str(value).strip().lower())


def brand_of(page_name, query):
    low_page = (page_name or "").lower()
    for alias, canon in _TITLE_BRANDS:
        if alias in low_page:
            return canon
    return norm_brand(query) or query


def unix_date(ts):
    try:
        return dt.datetime.utcfromtimestamp(int(ts)).date().isoformat()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


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


def merge_rows(path, columns, new_rows, key_col):
    if not os.path.exists(path):
        return columns, list(new_rows)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        old_rows = list(reader)
        old_cols = reader.fieldnames or columns
    merged, seen, synth = [], {}, 0
    for row in old_rows + list(new_rows):
        key = str(row.get(key_col) or "").strip()
        if not key:
            synth += 1
            key = "__synthetic__%d" % synth
        if key in seen:
            merged[seen[key]] = row
        else:
            seen[key] = len(merged)
            merged.append(row)
    print("  merge %s: %d on disk + %d scraped -> %d total"
          % (os.path.basename(path), len(old_rows), len(new_rows), len(merged)))
    return old_cols, merged


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


# --------------------------------------------------------------------------
# Harvesting — ad objects out of Ad Library JSON/GraphQL
# --------------------------------------------------------------------------

AD_ID_KEYS = ("adArchiveID", "ad_archive_id", "adArchiveId", "adid")


def _ad_text_of(d):
    """Ad copy: creative bodies list, or every `text`/`body` string in the
    snapshot, deduped, joined with ' | ' and capped."""
    texts = []
    for v in find_key(d, "ad_creative_bodies"):
        if isinstance(v, list):
            texts.extend(t for t in v if isinstance(t, str))
    for key in ("body", "text", "title", "link_description"):
        for v in find_key(d, key):
            if isinstance(v, dict):
                v = v.get("text")
            if isinstance(v, str) and v.strip():
                texts.append(v.strip())
    seen, uniq = set(), []
    for t in texts:
        t = re.sub(r"\s+", " ", t).strip()
        if t and t.lower() not in seen and len(t) > 2:
            seen.add(t.lower())
            uniq.append(t)
    joined = " | ".join(uniq)
    return joined[:1000] if joined else None


def harvest_ads(blobs, query):
    """Ad rows: any dict carrying an ad-archive id."""
    rows, seen = [], set()
    for blob in blobs:
        for d in walk_dicts(blob):
            ad_id = None
            for k in AD_ID_KEYS:
                if d.get(k) is not None:
                    ad_id = str(d[k]).strip()
                    break
            if not ad_id or ad_id in ("0", "") or ad_id in seen:
                continue
            snapshot = d.get("snapshot") if isinstance(d.get("snapshot"), dict) else d
            page_name = None
            for v in find_key(d, "page_name"):
                if isinstance(v, str) and v.strip():
                    page_name = v.strip()
                    break
            start = (d.get("startDate") or d.get("start_date")
                     or snapshot.get("startDate"))
            end = (d.get("endDate") or d.get("end_date")
                   or snapshot.get("endDate"))
            active = d.get("isActive")
            if active is None:
                active = d.get("is_active")
            platforms = None
            for k in ("publisherPlatform", "publisher_platform",
                      "publisher_platforms"):
                for v in find_key(d, k):
                    if isinstance(v, list) and v:
                        platforms = "; ".join(str(p) for p in v)
                        break
                if platforms:
                    break
            cta = None
            for k in ("ctaText", "cta_text"):
                for v in find_key(d, k):
                    if isinstance(v, str) and v.strip():
                        cta = v.strip()
                        break
                if cta:
                    break
            seen.add(ad_id)
            rows.append({
                "ad_id": ad_id, "query": query,
                "brand": brand_of(page_name, query),
                "page_name": page_name,
                "ad_text": _ad_text_of(snapshot),
                "cta": cta,
                "start_date": unix_date(start) if str(start or "").isdigit()
                else (start or None),
                "end_date": unix_date(end) if str(end or "").isdigit()
                else (end or None),
                "active": bool(active) if active is not None else None,
                "platforms": platforms,
                "snapshot_url":
                    "https://www.facebook.com/ads/library/?id=%s" % ad_id,
                "scraped_at": now_stamp(),
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
                "This scraper needs Playwright:\n"
                "  pip3 install playwright\n"
                "  python3 -m playwright install chromium")
        profile_dir = profile_dir or os.path.expanduser(
            "~/.cache/energydrink-facebook-profile")
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

    def blobs(self, url, scrolls=6):
        self._responses.clear()
        self._page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        try:
            self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        html = self._page.content()
        if any(m in html for m in BLOCK_MARKERS):
            raise BlockedError(
                "the Ad Library asked for a login/checkpoint — wait a while, "
                "or try a different network. (The Ad Library normally needs "
                "no login at all.)")
        for _ in range(scrolls):  # each scroll loads another page of ads
            try:
                self._page.mouse.wheel(0, 2600)
                self._page.wait_for_timeout(1200)
            except Exception:
                break
        out = []
        for resp in list(self._responses):
            try:
                body = resp.text()
            except Exception:
                continue
            body = (body or "").lstrip()
            # graphql responses are json; some are prefixed anti-hijack lines
            if body.startswith("for (;;);"):
                body = body[len("for (;;);"):]
            if not body.startswith(("{", "[")) or len(body) > 8_000_000:
                continue
            try:
                out.append(json.loads(body))
            except ValueError:
                # graphql batches: one json object per line
                for line in body.splitlines():
                    line = line.strip()
                    if line.startswith("{"):
                        try:
                            out.append(json.loads(line))
                        except ValueError:
                            pass
                continue
        html = self._page.content()
        for m in re.finditer(
                r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
                html, re.DOTALL):
            try:
                out.append(json.loads(m.group(1)))
            except ValueError:
                continue
        return out

    def close(self):
        try:
            self._context.close()
            self._pw.stop()
        except Exception:
            pass


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--queries", nargs="+", default=DEFAULT_QUERIES,
                    help="brand names to search the Ad Library for")
    ap.add_argument("--country", default="US")
    ap.add_argument("--scrolls", type=int, default=6,
                    help="scrolls per query; each loads more ads (default 6)")
    ap.add_argument("--sleep", type=float, default=3.0)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--profile-dir", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out", default="data/facebook")
    args = ap.parse_args()

    ads = []
    fetcher = BrowserFetcher(headless=args.headless,
                             profile_dir=args.profile_dir)
    try:
        for q in args.queries:
            url = SEARCH_URL.format(country=args.country,
                                    q=urllib.parse.quote_plus(q))
            try:
                blobs = fetcher.blobs(url, scrolls=args.scrolls)
            except BlockedError as e:
                print("  BLOCKED on %r: %s" % (q, e))
                continue
            got = harvest_ads(blobs, q)
            ads.extend(got)
            print("  [%s] %d ads" % (q, len(got)))
            polite_sleep(args.sleep)
    finally:
        fetcher.close()

    # cross-query dedupe (one ad can match several brand queries)
    uniq, seen = [], set()
    for a in ads:
        if a["ad_id"] in seen:
            continue
        seen.add(a["ad_id"])
        uniq.append(a)

    path = os.path.join(args.out, "ads.csv")
    if args.fresh:
        write_csv(path, AD_COLUMNS, uniq)
    else:
        cols, merged = merge_rows(path, AD_COLUMNS, uniq, "ad_id")
        write_csv(path, cols, merged)
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit("BLOCKED: %s" % e)
