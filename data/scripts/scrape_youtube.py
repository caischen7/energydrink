#!/usr/bin/env python3
"""Scrape YouTube energy-drink videos + comments into clean CSVs — for FREE.

Replaces the paid exports behind data/youtube/videos.csv / comments.csv.
Two backends:

  api    — RECOMMENDED. The official YouTube Data API v3 called with plain
           urllib (no Google client library needed). Get a FREE key: open
           https://console.cloud.google.com/ → create a project → "APIs &
           Services" → Library → enable "YouTube Data API v3" → Credentials
           → Create credentials → API key. Free quota is 10,000 units/day;
           each search page costs 100 units, each videos/commentThreads
           page 1 unit. The script prints a quota estimate up front — the
           defaults (8 queries × 50 videos × 2 comment pages ≈ 1,600 units)
           fit comfortably in one day's free quota.
  ytdlp  — zero-key fallback via the yt-dlp library (public web client, no
           API key, no quota). MUCH slower: it extracts every video page in
           full, comments included (a few seconds per video before the
           polite delay), and is more fragile when YouTube changes its
           internals. Setup: pip3 install yt-dlp

Setup + usage (macOS, VS Code terminal):
  export YOUTUBE_API_KEY="AIza..."                    # api backend key
  python3 data/scripts/scrape_youtube.py              # auto: api if key set, else ytdlp
  python3 data/scripts/scrape_youtube.py --backend ytdlp          # no key needed
  python3 data/scripts/scrape_youtube.py --queries "Zoa energy drink" \
      "C4 energy review" --max-videos-per-query 25 --comment-pages 1

Outputs (schemas match the committed files exactly):
  data/youtube/videos.csv    one row per video (source is "api_v3" or
                             "yt_dlp"; tags "; "-joined; brands_mentioned is
                             a comma-joined scan of title+description against
                             the shared brand aliases; transcript is always
                             "" — the original corpus never filled it either,
                             captions would need a separate API)
  data/youtube/comments.csv  one row per comment — top-level comments AND
                             their replies

Both CSVs are MERGED with whatever is already at the output path: existing
rows are kept, deduped on video_id / comment_id, freshly scraped rows win.
Reruns are incremental, not destructive. comments.csv is ~25 MB / 150k rows,
so the merge streams it row-by-row instead of loading it whole.
"""

import argparse
import csv
import datetime as dt
import json
import math
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

# Queries behind the original corpus: generic category searches + the brands
# with the strongest share of voice. Override with --queries.
DEFAULT_QUERIES = [
    "energy drink review",
    "best energy drink",
    "energy drink taste test",
    "Monster energy drink",
    "Celsius energy drink",
    "Alani Nu energy drink",
    "Ghost energy drink",
    "Red Bull",
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


def _brand_patterns():
    """One compiled word-boundary regex per canonical brand.

    (?<!\\w) / (?!\\w) instead of \\b so aliases ending in punctuation
    ("liquid i.v.") still anchor correctly. Ambiguous names (Monster, Prime,
    Ghost, NOS, Reign, Bang) WILL match non-drink uses like "prime minister"
    — that is deliberate: it matches the alias behavior everywhere else in
    the pipeline (build_clean_datasets / build_external_datasets), and the
    dashboard's noise filter compensates downstream.
    """
    by_canon = {}
    for alias, canon in BRAND_ALIASES.items():
        by_canon.setdefault(canon, []).append(alias)
    patterns = {}
    for canon, aliases in by_canon.items():
        alts = "|".join(
            re.escape(a) for a in sorted(aliases, key=len, reverse=True)
        )
        patterns[canon] = re.compile(
            r"(?<!\w)(?:%s)(?!\w)" % alts, re.IGNORECASE
        )
    return patterns


BRAND_PATTERNS = _brand_patterns()

# Descriptive UA for the API backend (yt-dlp manages its own).
UA = (
    "energydrink-market-research/1.0 "
    "(academic project; stdlib urllib; contact: repo owner)"
)

API_BASE = "https://www.googleapis.com/youtube/v3"
DAILY_FREE_QUOTA = 10_000

VIDEO_COLUMNS = [
    "source", "search_query", "video_id", "title", "channel", "upload_date",
    "duration_seconds", "view_count", "like_count", "comment_count",
    "description", "tags", "categories", "url", "transcript",
    "brands_mentioned",
]
COMMENT_COLUMNS = [
    "source", "video_id", "comment_id", "author", "comment", "comment_likes",
    "comment_date",
]

# YouTube Data API v3 category ids → names (the common ones in this corpus);
# unknown ids pass through as the raw id rather than getting lost.
CATEGORY_NAMES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
}

# Some descriptions/comments in the existing corpus are very long; don't let
# the csv module refuse to read them back during the merge.
csv.field_size_limit(10_000_000)


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


def iso_date(value):
    """'2024-11-02T15:04:05Z' or '20241102' → '2024-11-02' (else raw / '')."""
    if not value:
        return ""
    s = str(value).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if m:
        return "%s-%s-%s" % m.groups()
    return s  # keep raw rather than lose it


_DURATION_RE = re.compile(
    r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$"
)


def duration_seconds(iso):
    """ISO-8601 duration ('PT1H2M3S', 'PT45S', 'P1DT2H', 'P0D') → seconds."""
    if not iso:
        return ""
    m = _DURATION_RE.match(str(iso).strip())
    if not m:
        return ""
    days, hours, minutes, seconds = (float(g) if g else 0 for g in m.groups())
    return int(days * 86400 + hours * 3600 + minutes * 60 + seconds)


def category_name(category_id):
    cid = "" if category_id is None else str(category_id).strip()
    return CATEGORY_NAMES.get(cid, cid)


def brands_mentioned(*texts):
    """Comma-joined canonical brands found in the given texts (sorted)."""
    blob = " ".join(t for t in texts if t)
    found = [canon for canon, pat in sorted(BRAND_PATTERNS.items())
             if pat.search(blob)]
    return ", ".join(found)


def polite_sleep(base):
    time.sleep(base + random.uniform(0, base))


def backoff_sleep(attempt, base):
    delay = base * (2 ** attempt) + random.uniform(0, base)
    print("  retrying in %.0fs..." % delay)
    time.sleep(delay)


# --------------------------------------------------------------------------
# Incremental CSV merge (pure stdlib — unit-tested with fixtures)
# --------------------------------------------------------------------------

def iter_existing(path, columns):
    """Yield rows already in the output CSV, coerced onto the expected
    columns, one at a time (comments.csv is ~150k rows — never load it whole)."""
    if not os.path.exists(path):
        return
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            yield {c: (r.get(c) if r.get(c) is not None else "") for c in columns}


def merge_rows(old_rows, new_rows, key_col):
    """Union old + new, dedupe on key_col, freshly scraped rows win.

    Old rows keep their original order (updated in place when re-scraped) so
    reruns produce small diffs; genuinely new rows are appended after. Rows
    with an empty key pass through untouched. Yields — never materializes
    the old side.
    """
    fresh = {}
    for row in new_rows:
        key = row.get(key_col)
        if key:
            fresh[key] = row
    seen = set()
    for row in old_rows:
        key = row.get(key_col) or ""
        if not key:
            yield row
            continue
        if key in seen:
            continue  # duplicate already in the old file
        seen.add(key)
        yield fresh.pop(key, row)
    for row in new_rows:
        key = row.get(key_col)
        if key and key in fresh:
            yield fresh.pop(key)


def write_csv_merged(path, columns, new_rows, key_col):
    """Stream-merge new_rows into the CSV at `path` (schema = `columns`)."""
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    counts = {"old": 0}

    def _old():
        for row in iter_existing(path, columns):
            counts["old"] += 1
            yield row

    tmp = path + ".tmp"
    total = 0
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in merge_rows(_old(), new_rows, key_col):
            writer.writerow(row)
            total += 1
    os.replace(tmp, path)
    print("  wrote %s (%d rows: %d already there, %d scraped, %d net new)"
          % (path, total, counts["old"], len(new_rows), total - counts["old"]))


# --------------------------------------------------------------------------
# API backend — YouTube Data API v3 via plain urllib
# --------------------------------------------------------------------------

class QuotaExceededError(RuntimeError):
    """The API key's daily quota is exhausted — stop and say what was spent."""


class CommentsDisabled(RuntimeError):
    """Comments are turned off for this video — skip it, not a failure."""


class ApiError(RuntimeError):
    pass


def api_error_reason(body):
    """Pull the machine-readable reason out of an API error JSON body."""
    try:
        err = json.loads(body).get("error") or {}
        for item in (err.get("errors") or []) + (err.get("details") or []):
            reason = item.get("reason")
            if reason:
                return reason
        return err.get("status") or ""
    except (ValueError, AttributeError, TypeError):
        return ""


def quota_estimate(n_queries, max_videos, comment_pages):
    """Upper-bound quota units for one run (search pages are 100 units,
    /videos and /commentThreads pages are 1 unit each)."""
    search_calls = n_queries * int(math.ceil(max_videos / 50.0))
    video_calls = int(math.ceil(n_queries * max_videos / 50.0))
    comment_calls = n_queries * max_videos * comment_pages
    return search_calls * 100 + video_calls + comment_calls


class ApiSession:
    """Thin urllib wrapper: retries with exponential backoff on 429/5xx,
    keeps a running count of quota units likely spent."""

    def __init__(self, api_key, sleep=2.0, max_attempts=4):
        self.api_key = api_key
        self.sleep = sleep
        self.max_attempts = max_attempts
        self.units = 0

    def get(self, endpoint, params, cost):
        self.units += cost  # count the attempt — quota bills it either way
        qs = urllib.parse.urlencode(dict(params, key=self.api_key))
        url = "%s/%s?%s" % (API_BASE, endpoint, qs)
        last_err = None
        for attempt in range(self.max_attempts):
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    payload = json.load(resp)
                polite_sleep(self.sleep)
                return payload
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                reason = api_error_reason(body)
                if reason == "quotaExceeded":
                    raise QuotaExceededError(
                        "daily quota exhausted after ~%d units spent this run "
                        "(free tier: %d/day, resets midnight Pacific). Rerun "
                        "tomorrow with fewer --queries / a smaller "
                        "--max-videos-per-query / --comment-pages, or switch "
                        "to --backend ytdlp (no key, no quota)."
                        % (self.units, DAILY_FREE_QUOTA))
                if reason == "commentsDisabled":
                    raise CommentsDisabled()
                if reason in ("keyInvalid", "badRequest") and "key" in body.lower():
                    raise ApiError(
                        "the API rejected YOUTUBE_API_KEY (%s) — re-check the "
                        "key in the Google Cloud console and make sure "
                        "'YouTube Data API v3' is enabled for its project."
                        % (reason or "keyInvalid"))
                if e.code in (429, 500, 503) and attempt < self.max_attempts - 1:
                    last_err = e
                    backoff_sleep(attempt, self.sleep)
                    continue
                raise ApiError("HTTP %d from the YouTube API (reason: %s): %s"
                               % (e.code, reason or "unknown", body[:300]))
            except (urllib.error.URLError, OSError) as e:
                if attempt < self.max_attempts - 1:
                    last_err = e
                    backoff_sleep(attempt, self.sleep)
                    continue
                raise ApiError(
                    "could not reach googleapis.com (%s). Check your "
                    "connection — sandboxed cloud environments with a domain "
                    "allowlist block it; run this from your own machine." % e)
        raise ApiError(str(last_err))


def api_search_ids(payload):
    """(video ids, nextPageToken) from one /search page."""
    ids = []
    for item in payload.get("items") or []:
        vid = (item.get("id") or {}).get("videoId")
        if vid:
            ids.append(vid)
    return ids, payload.get("nextPageToken")


def api_video_row(item, query):
    """One videos.csv row from a /videos item (part=snippet,statistics,
    contentDetails)."""
    snippet = item.get("snippet") or {}
    stats = item.get("statistics") or {}
    content = item.get("contentDetails") or {}
    vid = item.get("id") or ""
    title = snippet.get("title") or ""
    description = snippet.get("description") or ""
    return {
        "source": "api_v3",
        "search_query": query,
        "video_id": vid,
        "title": title,
        "channel": snippet.get("channelTitle") or "",
        "upload_date": iso_date(snippet.get("publishedAt")),
        "duration_seconds": duration_seconds(content.get("duration")),
        "view_count": to_int(stats.get("viewCount")),
        "like_count": to_int(stats.get("likeCount")),  # hidden likes → blank
        "comment_count": to_int(stats.get("commentCount")),
        "description": description,
        "tags": "; ".join(snippet.get("tags") or []),
        "categories": category_name(snippet.get("categoryId")),
        "url": "https://www.youtube.com/watch?v=%s" % vid,
        "transcript": "",  # never populated — see module docstring
        "brands_mentioned": brands_mentioned(title, description),
    }


def _api_comment_row(comment_id, snippet, video_id):
    return {
        "source": "api_v3",
        "video_id": video_id,
        "comment_id": comment_id or "",
        "author": snippet.get("authorDisplayName") or "",
        "comment": snippet.get("textDisplay") or "",
        "comment_likes": to_int(snippet.get("likeCount")),
        "comment_date": iso_date(snippet.get("publishedAt")),
    }


def api_comment_rows(payload, video_id):
    """Top-level comments AND their inline replies from one /commentThreads
    page (part=snippet,replies)."""
    rows = []
    for item in payload.get("items") or []:
        top = (item.get("snippet") or {}).get("topLevelComment") or {}
        if top:
            rows.append(_api_comment_row(
                top.get("id") or item.get("id"),
                top.get("snippet") or {}, video_id))
        for reply in (item.get("replies") or {}).get("comments") or []:
            rows.append(_api_comment_row(
                reply.get("id"), reply.get("snippet") or {}, video_id))
    return rows


def api_backend(queries, max_videos, comment_pages, sleep, api_key):
    """Returns (video_rows, comment_rows, quota_message_or_None). If the
    quota dies mid-run, everything scraped so far is still returned so the
    caller can write partial output before exiting."""
    session = ApiSession(api_key, sleep=sleep)
    videos, comments = [], []
    quota_hit = None
    try:
        # 1) /search — collect video ids (100 units per page, the pricey part)
        query_of, ordered_ids = {}, []
        for query in queries:
            found, token = 0, None
            while found < max_videos:
                params = {"part": "id", "q": query, "type": "video",
                          "maxResults": min(50, max_videos - found)}
                if token:
                    params["pageToken"] = token
                ids, token = api_search_ids(
                    session.get("search", params, cost=100))
                fresh = 0
                for vid in ids:
                    found += 1
                    if vid not in query_of:
                        query_of[vid] = query
                        ordered_ids.append(vid)
                        fresh += 1
                    if found >= max_videos:
                        break
                print("  [%s] +%d videos (%d unique total)"
                      % (query, fresh, len(ordered_ids)))
                if not token or not ids:
                    break

        # 2) /videos — hydrate details+stats in chunks of 50 ids (1 unit each)
        for i in range(0, len(ordered_ids), 50):
            chunk = ordered_ids[i:i + 50]
            payload = session.get(
                "videos",
                {"part": "snippet,statistics,contentDetails",
                 "id": ",".join(chunk)},
                cost=1)
            for item in payload.get("items") or []:
                videos.append(
                    api_video_row(item, query_of.get(item.get("id"), "")))
        print("  hydrated %d videos (~%d quota units so far)"
              % (len(videos), session.units))

        # 3) /commentThreads — top-level comments + replies (1 unit per page)
        for n, row in enumerate(videos, 1):
            vid, token, got = row["video_id"], None, 0
            try:
                for _ in range(comment_pages):
                    params = {"part": "snippet,replies", "videoId": vid,
                              "maxResults": 100, "textFormat": "plainText"}
                    if token:
                        params["pageToken"] = token
                    payload = session.get("commentThreads", params, cost=1)
                    rows = api_comment_rows(payload, vid)
                    comments.extend(rows)
                    got += len(rows)
                    token = payload.get("nextPageToken")
                    if not token:
                        break
            except CommentsDisabled:
                print("  [%d/%d] %s: comments disabled — skipped"
                      % (n, len(videos), vid))
                continue
            except ApiError as e:  # one bad video shouldn't kill the run
                print("  ! comments failed for %s: %s" % (vid, e))
                continue
            print("  [%d/%d] %s: %d comments" % (n, len(videos), vid, got))
    except QuotaExceededError as e:
        quota_hit = str(e)
        print("  !! %s" % quota_hit)
        print("  !! writing everything scraped before the quota ran out...")
    print("  quota spent: ~%d units" % session.units)
    return videos, comments, quota_hit


# --------------------------------------------------------------------------
# ytdlp backend — yt-dlp public web client (no key, no quota, slower)
# --------------------------------------------------------------------------

def _load_ytdlp():
    try:
        from yt_dlp import YoutubeDL
        return YoutubeDL
    except ImportError:
        raise SystemExit(
            "The ytdlp backend needs yt-dlp:\n"
            "  pip3 install yt-dlp\n"
            "Or set YOUTUBE_API_KEY and use --backend api (recommended)."
        )


def ytdlp_video_row(info, query):
    """One videos.csv row from a yt-dlp info dict."""
    vid = info.get("id") or ""
    title = info.get("title") or ""
    description = info.get("description") or ""
    return {
        "source": "yt_dlp",
        "search_query": query,
        "video_id": vid,
        "title": title,
        "channel": info.get("channel") or info.get("uploader") or "",
        "upload_date": iso_date(info.get("upload_date")),  # YYYYMMDD → ISO
        "duration_seconds": to_int(info.get("duration")),
        "view_count": to_int(info.get("view_count")),
        "like_count": to_int(info.get("like_count")),
        "comment_count": to_int(info.get("comment_count")),
        "description": description,
        "tags": "; ".join(info.get("tags") or []),
        "categories": "; ".join(info.get("categories") or []),
        "url": "https://www.youtube.com/watch?v=%s" % vid,
        "transcript": "",  # never populated — see module docstring
        "brands_mentioned": brands_mentioned(title, description),
    }


def ytdlp_comment_rows(info):
    """comments.csv rows from a yt-dlp info dict's comments list (top-level
    comments and replies arrive in the same flat list)."""
    rows = []
    for c in info.get("comments") or []:
        ts = c.get("timestamp")
        if isinstance(ts, (int, float)):
            date = dt.datetime.fromtimestamp(
                ts, dt.timezone.utc).date().isoformat()
        else:
            date = ""
        rows.append({
            "source": "yt_dlp",
            "video_id": info.get("id") or "",
            "comment_id": c.get("id") or "",
            "author": c.get("author") or "",
            "comment": c.get("text") or "",
            "comment_likes": to_int(c.get("like_count")),
            "comment_date": date,
        })
    return rows


def ytdlp_backend(queries, max_videos, comment_pages, sleep):
    YoutubeDL = _load_ytdlp()
    # Mirror the API's page size: --comment-pages × ~100 comments per video.
    max_comments = max(1, comment_pages) * 100
    flat_opts = {"quiet": True, "no_warnings": True, "skip_download": True,
                 "extract_flat": True}
    full_opts = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "getcomments": True,
        "extractor_args": {"youtube": {"max_comments": [str(max_comments)]}},
    }

    # 1) flat search — ids only, one request per query
    query_of, ordered_ids = {}, []
    with YoutubeDL(flat_opts) as ydl:
        for query in queries:
            try:
                info = ydl.extract_info(
                    "ytsearch%d:%s" % (max_videos, query), download=False)
            except Exception as e:  # one bad query shouldn't kill the run
                print("  ! search failed for %r: %s" % (query, e))
                continue
            fresh = 0
            for entry in (info or {}).get("entries") or []:
                vid = (entry or {}).get("id")
                if vid and vid not in query_of:
                    query_of[vid] = query
                    ordered_ids.append(vid)
                    fresh += 1
            print("  [%s] +%d videos (%d unique total)"
                  % (query, fresh, len(ordered_ids)))
            polite_sleep(sleep)

    # 2) full per-video extraction, comments included (the slow part)
    videos, comments = [], []
    with YoutubeDL(full_opts) as ydl:
        for n, vid in enumerate(ordered_ids, 1):
            try:
                info = ydl.extract_info(
                    "https://www.youtube.com/watch?v=%s" % vid,
                    download=False)
            except Exception as e:  # private/removed/rate-limited video
                print("  ! video failed for %s: %s" % (vid, e))
                polite_sleep(sleep)
                continue
            videos.append(ytdlp_video_row(info, query_of.get(vid, "")))
            rows = ytdlp_comment_rows(info)
            comments.extend(rows)
            print("  [%d/%d] %s: %d comments"
                  % (n, len(ordered_ids), vid, len(rows)))
            polite_sleep(sleep)
    return videos, comments


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--backend", choices=["auto", "api", "ytdlp"],
                    default="auto",
                    help="auto = api if YOUTUBE_API_KEY is set, else ytdlp")
    ap.add_argument("--queries", nargs="+", default=DEFAULT_QUERIES)
    ap.add_argument("--max-videos-per-query", type=int, default=50,
                    help="videos to collect per query (default 50)")
    ap.add_argument("--comment-pages", type=int, default=2,
                    help="comment pages per video, ~100 top-level comments "
                         "plus replies each (default 2)")
    ap.add_argument("--sleep", type=float, default=2.0,
                    help="base delay between requests in seconds, jittered "
                         "up to 2x (default 2.0)")
    ap.add_argument("--out", default="data/youtube",
                    help="output directory (CSVs there are merged, not "
                         "overwritten)")
    args = ap.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    backend = args.backend
    if backend == "auto":
        backend = "api" if api_key else "ytdlp"
    if backend == "api" and not api_key:
        sys.exit(
            "YOUTUBE_API_KEY is not set. Get a FREE key (10,000 units/day):\n"
            "  https://console.cloud.google.com/ → create a project → enable\n"
            "  'YouTube Data API v3' → Credentials → Create credentials → "
            "API key\n"
            "then:  export YOUTUBE_API_KEY='AIza...'\n"
            "Or use --backend ytdlp (no key needed, slower)."
        )
    print("Backend: %s" % backend)

    quota_hit = None
    if backend == "api":
        est = quota_estimate(len(args.queries), args.max_videos_per_query,
                             args.comment_pages)
        print("Quota estimate: ~%d units (free tier: %d/day; each search "
              "page = 100 units, everything else = 1)"
              % (est, DAILY_FREE_QUOTA))
        if est > DAILY_FREE_QUOTA:
            print("  !! the estimate exceeds the free daily quota — expect a "
                  "quotaExceeded stop; trim --queries or lower "
                  "--max-videos-per-query / --comment-pages")
        videos, comments, quota_hit = api_backend(
            args.queries, args.max_videos_per_query, args.comment_pages,
            args.sleep, api_key)
    else:
        print("Note: yt-dlp does a full page extraction per video — expect "
              "up to %d videos x a few seconds each plus the polite delay."
              % (len(args.queries) * args.max_videos_per_query))
        videos, comments = ytdlp_backend(
            args.queries, args.max_videos_per_query, args.comment_pages,
            args.sleep)

    write_csv_merged(os.path.join(args.out, "videos.csv"),
                     VIDEO_COLUMNS, videos, "video_id")
    write_csv_merged(os.path.join(args.out, "comments.csv"),
                     COMMENT_COLUMNS, comments, "comment_id")
    print("Done. Next: rerun `python3 data/scripts/build_dashboard_json.py` "
          "to refresh the dashboard aggregate.")
    if quota_hit:
        sys.exit("QUOTA EXCEEDED (partial results were saved): %s" % quota_hit)


if __name__ == "__main__":
    try:
        main()
    except QuotaExceededError as e:
        sys.exit("QUOTA EXCEEDED: %s" % e)
    except ApiError as e:
        sys.exit("API ERROR: %s" % e)
