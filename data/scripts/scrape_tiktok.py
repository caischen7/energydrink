#!/usr/bin/env python3
"""Scrape TikTok energy-drink content: brand-account videos + hashtag pages,
with engagement stats (plays / likes / comments / shares / saves).

How it works (free, no API key): TikTok's web app embeds the full video data
as JSON in each page (__UNIVERSAL_DATA_FOR_REHYDRATION__ / SIGI_STATE script
tags) and fetches more via JSON XHRs while scrolling. A real Chromium via
Playwright loads profile and hashtag pages, scrolls, and this script harvests
every video-shaped object from both sources. Same setup as the other browser
scrapers:
  pip3 install playwright && python3 -m playwright install chromium   # once

Notes:
- Run from a residential IP. TikTok may show a puzzle/slider captcha —
  solve it once in the window; the persistent profile remembers.
- The official TikTok Research API is an alternative if you can get academic
  access (free for approved researchers — worth applying with an .edu email).
- Comments (--comments N) visit the top N videos per source and capture the
  comment-list XHRs; slower, off by default.

Usage (VS Code terminal on macOS):
  python3 data/scripts/scrape_tiktok.py
  python3 data/scripts/scrape_tiktok.py --profiles monsterenergy redbull
  python3 data/scripts/scrape_tiktok.py --hashtags energydrink celsius --comments 5

Outputs:
  data/tiktok/videos.csv     one row per video, deduped on video_id
  data/tiktok/comments.csv   (only when --comments > 0)

Runs are INCREMENTAL: existing rows are merged, deduped on video_id /
comment_id, fresh rows win. --fresh overwrites.

Creative angles this data supports:
- brand engagement benchmarking (views/likes per post across brand accounts)
- hashtag momentum (#energydrink vs #celsius vs #alaninu post volume)
- organic vs brand voice: hashtag pages surface creator content about brands,
  not just the brands' own marketing.
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

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# Brand accounts (TikTok handles) and hashtags worth tracking.
DEFAULT_PROFILES = ["monsterenergy", "redbull", "celsiusofficial",
                    "alaninutrition", "ghostlifestyle", "drinkprime",
                    "rockstarenergy", "zoaenergy"]
DEFAULT_HASHTAGS = ["energydrink", "energydrinks", "celsiuslive",
                    "alaninuenergy"]

BRAND_ALIASES = {
    "celsius": "Celsius", "celsiusofficial": "Celsius",
    "red bull": "Red Bull", "redbull": "Red Bull",
    "monster": "Monster", "monsterenergy": "Monster",
    "liquid i.v.": "Liquid I.V.", "liquid iv": "Liquid I.V.",
    "ghost": "Ghost", "ghostlifestyle": "Ghost", "ghostenergy": "Ghost",
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

# word-boundary patterns; multi-word aliases match loosely on whitespace
_BRAND_PATTERNS = [
    (canon, re.compile(r"\b" + re.escape(alias).replace(r"\ ", r"\s*") + r"\b",
                       re.I))
    for alias, canon in BRAND_ALIASES.items()
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

VIDEO_COLUMNS = [
    "video_id", "source", "author", "desc", "hashtags", "create_date",
    "plays", "likes", "comments_count", "shares", "saves", "url",
    "brands_mentioned", "scraped_at",
]
COMMENT_COLUMNS = [
    "video_id", "comment_id", "author", "comment", "comment_likes",
    "comment_date", "scraped_at",
]

BLOCK_MARKERS = ("Verify to continue", "captcha-verify", "Access Denied",
                 "tiktok-verify-page", "security check")


class BlockedError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def to_int(value):
    """Parse ints incl. TikTok's abbreviated counts ('1.2M', '4700', 4700)."""
    if value is None or isinstance(value, (dict, list)):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip().upper().replace(",", "")
    m = re.match(r"^([\d.]+)([KMB]?)$", s)
    if not m:
        return None
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[m.group(2)]
    try:
        return int(float(m.group(1)) * mult)
    except ValueError:
        return None


def unix_date(ts):
    try:
        return dt.datetime.utcfromtimestamp(int(ts)).date().isoformat()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def hashtags_of(desc, extra=None):
    tags = re.findall(r"#(\w+)", desc or "")
    for t in extra or []:
        if t and t not in tags:
            tags.append(t)
    return " ".join("#" + t for t in tags)


def brands_mentioned(*texts):
    joined = " ".join(t for t in texts if t)
    hits = []
    for canon, pat in _BRAND_PATTERNS:
        if canon not in hits and pat.search(joined):
            hits.append(canon)
    return ", ".join(sorted(hits))


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


# --------------------------------------------------------------------------
# Harvesting — video / comment objects out of TikTok JSON
# --------------------------------------------------------------------------

def _stats_of(d):
    """Counts from `stats` (ints) or `statsV2` (strings) or flat keys."""
    stats = d.get("statsV2") or d.get("stats") or {}
    def g(*keys):
        for k in keys:
            v = to_int(stats.get(k))
            if v is None:
                v = to_int(d.get(k))
            if v is not None:
                return v
        return None
    return {
        "plays": g("playCount", "play_count"),
        "likes": g("diggCount", "digg_count", "likeCount"),
        "comments_count": g("commentCount", "comment_count"),
        "shares": g("shareCount", "share_count"),
        "saves": g("collectCount", "collect_count"),
    }


def harvest_videos(blobs, source):
    """Video rows from every blob a page produced. A dict is a video if it
    has a numeric-string id, a desc, and a stats block."""
    rows, seen = [], set()
    for blob in blobs:
        for d in walk_dicts(blob):
            vid = d.get("id")
            if not isinstance(vid, str) or not vid.isdigit() or vid in seen:
                continue
            if "desc" not in d or not (d.get("stats") or d.get("statsV2")):
                continue
            author = d.get("author")
            if isinstance(author, dict):
                author = author.get("uniqueId") or author.get("unique_id")
            if not isinstance(author, str):
                author = None
            desc = d.get("desc") or ""
            extra_tags = []
            for te in d.get("textExtra") or []:
                if isinstance(te, dict) and te.get("hashtagName"):
                    extra_tags.append(te["hashtagName"])
            stats = _stats_of(d)
            seen.add(vid)
            rows.append({
                "video_id": vid, "source": source, "author": author,
                "desc": desc, "hashtags": hashtags_of(desc, extra_tags),
                "create_date": unix_date(d.get("createTime")),
                "plays": stats["plays"], "likes": stats["likes"],
                "comments_count": stats["comments_count"],
                "shares": stats["shares"], "saves": stats["saves"],
                "url": "https://www.tiktok.com/@%s/video/%s"
                       % (author or "_", vid),
                "brands_mentioned": brands_mentioned(desc, author),
                "scraped_at": now_stamp(),
            })
    return rows


def harvest_comments(blobs, video_id):
    """Comment rows: dicts with cid + text (TikTok comment-list responses)."""
    rows, seen = [], set()
    for blob in blobs:
        for d in walk_dicts(blob):
            cid = d.get("cid")
            text = d.get("text")
            if not cid or not isinstance(text, str) or not text.strip():
                continue
            cid = str(cid)
            if cid in seen:
                continue
            seen.add(cid)
            user = d.get("user")
            author = None
            if isinstance(user, dict):
                author = user.get("unique_id") or user.get("uniqueId")
            rows.append({
                "video_id": video_id, "comment_id": cid, "author": author,
                "comment": text.strip(),
                "comment_likes": to_int(d.get("digg_count")
                                        or d.get("diggCount")),
                "comment_date": unix_date(d.get("create_time")
                                          or d.get("createTime")),
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
            "~/.cache/energydrink-tiktok-profile")
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

    def blobs(self, url, scrolls=6):
        self._responses.clear()
        self._page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        try:
            self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        html = self._page.content()
        if any(m in html for m in BLOCK_MARKERS):
            self._wait_for_captcha()
        for _ in range(scrolls):
            try:
                self._page.mouse.wheel(0, 2400)
                self._page.wait_for_timeout(900)
            except Exception:
                break
        html = self._page.content()
        out = []
        for resp in list(self._responses):
            try:
                ct = (resp.headers or {}).get("content-type", "")
                if "json" not in ct:
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
                r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
                html, re.DOTALL):
            try:
                out.append(json.loads(m.group(1)))
            except ValueError:
                continue
        return out

    def _wait_for_captcha(self):
        if self._headless:
            raise BlockedError(
                "TikTok showed a verification puzzle in headless mode — "
                "rerun without --headless and solve it once in the window.")
        print("  >> TikTok verification puzzle — solve it in the browser "
              "window; waiting up to 3 min...")
        deadline = time.time() + 180
        while time.time() < deadline:
            self._page.wait_for_timeout(3000)
            if not any(m in self._page.content() for m in BLOCK_MARKERS):
                return
        raise BlockedError("verification was not solved within 3 minutes")

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
    ap.add_argument("--profiles", nargs="+", default=DEFAULT_PROFILES,
                    help="brand account handles (without @)")
    ap.add_argument("--hashtags", nargs="+", default=DEFAULT_HASHTAGS)
    ap.add_argument("--comments", type=int, default=0,
                    help="visit the top N videos per source for comments "
                         "(default 0 = skip)")
    ap.add_argument("--scrolls", type=int, default=6,
                    help="scrolls per page; more scrolls = more videos")
    ap.add_argument("--sleep", type=float, default=3.0)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--profile-dir", default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out", default="data/tiktok")
    args = ap.parse_args()

    videos, comments = [], []
    fetcher = BrowserFetcher(headless=args.headless,
                             profile_dir=args.profile_dir)
    try:
        sources = ([("@" + p, "https://www.tiktok.com/@%s" % p)
                    for p in args.profiles] +
                   [("#" + h, "https://www.tiktok.com/tag/%s" % h)
                    for h in args.hashtags])
        for label, url in sources:
            try:
                blobs = fetcher.blobs(url, scrolls=args.scrolls)
            except BlockedError as e:
                print("  BLOCKED on %s: %s" % (label, e))
                continue
            got = harvest_videos(blobs, label)
            videos.extend(got)
            print("  [%s] %d videos" % (label, len(got)))
            if args.comments > 0:
                ranked = sorted(got, key=lambda v: -(v["plays"] or 0))
                for v in ranked[:args.comments]:
                    try:
                        vblobs = fetcher.blobs(v["url"], scrolls=4)
                    except BlockedError as e:
                        print("  BLOCKED on comments: %s" % e)
                        break
                    cg = harvest_comments(vblobs, v["video_id"])
                    comments.extend(cg)
                    print("    %s: %d comments" % (v["video_id"], len(cg)))
                    polite_sleep(args.sleep)
            polite_sleep(args.sleep)
    finally:
        fetcher.close()

    # cross-source dedupe (a brand video can appear under its hashtag too)
    uniq, seen = [], set()
    for v in videos:
        if v["video_id"] in seen:
            continue
        seen.add(v["video_id"])
        uniq.append(v)

    vpath = os.path.join(args.out, "videos.csv")
    cpath = os.path.join(args.out, "comments.csv")
    if args.fresh:
        write_csv(vpath, VIDEO_COLUMNS, uniq)
        if comments:
            write_csv(cpath, COMMENT_COLUMNS, comments)
    else:
        cols, merged = merge_rows(vpath, VIDEO_COLUMNS, uniq, "video_id")
        write_csv(vpath, cols, merged)
        if comments or os.path.exists(cpath):
            cols, merged = merge_rows(cpath, COMMENT_COLUMNS, comments,
                                      "comment_id")
            write_csv(cpath, cols, merged)
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit("BLOCKED: %s" % e)
