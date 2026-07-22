#!/usr/bin/env python3
"""Scrape r/EnergyDrinks posts + comments into dated RAW CSVs (free, no keys).

Two backends (both free):

  public  — DEFAULT, zero-key, stdlib-only. Reads Reddit's public JSON
            listings (new / hot / top?t=year / top?t=all) with a descriptive
            User-Agent, paginates via the `after` cursor, dedupes post ids
            across listings, then pulls each post's comment tree from
            /comments/<id>.json and flattens it recursively. Polite: >=2s +
            jitter between requests, 60s back-off on HTTP 429. If Reddit
            403s your IP/User-Agent, switch to praw.
  praw    — optional, still free: the official API via a free Reddit
            "script" app. Create one at https://www.reddit.com/prefs/apps
            (button "create app", type "script", any redirect URI), then:
              pip3 install praw
              export REDDIT_CLIENT_ID=...        # under the app name
              export REDDIT_CLIENT_SECRET=...    # the "secret" field
              export REDDIT_USER_AGENT="energydrink-market-research/1.0"
  auto    — praw if REDDIT_CLIENT_ID/SECRET are set, else public.

Setup + usage (VS Code terminal on macOS, from the repo root):
  python3 data/scripts/scrape_reddit.py                        # auto backend
  python3 data/scripts/scrape_reddit.py --backend public --max-posts 400
  pip3 install praw                                            # backend B once
  python3 data/scripts/scrape_reddit.py --backend praw

Full flow (scrape -> committed aggregates -> dashboard):
  python3 data/scripts/scrape_reddit.py
  RAW_DATA_DIR=raw_data python3 data/scripts/build_external_datasets.py
      # only the Reddit step needs raw_data/ to exist; build_market and
      # build_mintel just print warnings when their sources are absent
  python3 data/scripts/build_dashboard_json.py

Outputs (RAW, deliberately NOT committed — the dir is in .gitignore, which
this script re-adds if the line is ever removed):
  raw_data/Reddit data/r-Energy Drinks/energydrinks_posts_<YYYYMMDD>.csv
      id,title,selftext,created_utc,score,num_comments,permalink
  raw_data/Reddit data/r-Energy Drinks/energydrinks_comments_<YYYYMMDD>.csv
      id,link_id,body,created_utc,score

Privacy (hard repo rule): only aggregates get committed; raw text stays in
the untracked raw_data/ dir and usernames are NEVER collected — no author
field is read, stored, or written by this script.
build_external_datasets.py::build_reddit reduces these files to the small
committed data/reddit/brand_pulse.csv + data/reddit/meta.csv.

Reruns on the same day are incremental: rows already in today's files are
merged with the fresh scrape (union deduped on id, fresh rows win).
"""

import argparse
import csv
import datetime as dt
import gzip
import io
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Post selftexts / comment bodies can be very long; keep DictReader happy
# when merging with an existing output file.
csv.field_size_limit(10**9)

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# Repo root (this file lives at data/scripts/), so the default --out lands in
# <repo>/raw_data/ no matter which directory the script is launched from.
REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Matches what build_external_datasets.py::build_reddit expects under
# RAW_DATA_DIR ("Reddit data/r-Energy Drinks").
DEFAULT_OUT = os.path.join("raw_data", "Reddit data", "r-Energy Drinks")

# Descriptive UA per Reddit's API etiquette — generic browser UAs are far
# more likely to get the public JSON endpoints blocked.
UA = "energydrink-market-research/1.0 (personal research script)"

# Listings crawled for posts, in order; ids are deduped across all of them.
LISTINGS = [
    ("new", {}),
    ("hot", {}),
    ("top", {"t": "year"}),
    ("top", {"t": "all"}),
]

# Schemas consumed by build_external_datasets.py::build_reddit — it reads
# title/selftext/body, created_utc (int(float(ts))), and counts rows.
POST_COLUMNS = [
    "id", "title", "selftext", "created_utc", "score", "num_comments",
    "permalink",
]
COMMENT_COLUMNS = ["id", "link_id", "body", "created_utc", "score"]


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def to_int(value):
    f = to_float(value)
    return int(f) if f is not None else None


def fmt_ts(value):
    """Keep created_utc as the raw unix stamp string (float or int) —
    build_external_datasets.py parses it with int(float(ts))."""
    return "" if value is None else str(value)


def polite_sleep(base):
    time.sleep(base + random.uniform(0, base))


def read_csv_rows(path, columns):
    """Rows of an existing output CSV, coerced onto `columns` (for merging)."""
    rows = []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({c: (r.get(c) or "") for c in columns})
    return rows


def merge_rows(old_rows, new_rows, key):
    """Union old + new rows deduped on `key`; freshly scraped rows win."""
    merged = {}
    for row in old_rows + new_rows:
        k = row.get(key)
        if k:
            merged[k] = row  # dict update: fresh value wins, first-seen order
    return list(merged.values())


def write_csv_merged(path, columns, rows, key):
    """Write rows, first merging with any existing file at the same path so
    reruns are incremental instead of destructive."""
    old = read_csv_rows(path, columns) if os.path.exists(path) else []
    merged = merge_rows(old, rows, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)
    print(f"  wrote {path} ({len(merged)} rows; merged {len(old)} existing)")
    return merged


def ensure_gitignored():
    """Privacy guard: raw Reddit text/ids must never be committed — make sure
    .gitignore has a raw_data/ line (append it if it was removed)."""
    gi = os.path.join(REPO_ROOT, ".gitignore")
    existing = ""
    if os.path.exists(gi):
        with open(gi, encoding="utf-8") as f:
            existing = f.read()
    if any(line.strip().rstrip("/") == "raw_data"
           for line in existing.splitlines()):
        return
    with open(gi, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("raw_data/\n")
    print("  added raw_data/ to .gitignore (raw scrape output stays untracked)")


# --------------------------------------------------------------------------
# Public backend — reddit.com/*.json listings (zero-key, stdlib only)
# --------------------------------------------------------------------------

class BlockedError(RuntimeError):
    pass


def http_get_json(url, max_retries=4):
    """GET a Reddit JSON endpoint with polite retries.

    429 -> sleep 60s and retry (public endpoints are tightly rate-limited);
    5xx / transient network errors -> exponential backoff; 403 -> raise a
    BlockedError that points at the praw backend.
    """
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }
    attempt = 0
    while True:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    body = gzip.GzipFile(fileobj=io.BytesIO(body)).read()
                return json.loads(body.decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            attempt += 1
            if e.code == 429:
                if attempt > max_retries:
                    raise BlockedError(
                        f"still HTTP 429 after {max_retries} retries — Reddit "
                        "is rate-limiting hard. Raise --sleep, or use "
                        "--backend praw (the authenticated API has a much "
                        "higher quota)."
                    ) from e
                print(f"  >> HTTP 429 (rate limited) — sleeping 60s, retry "
                      f"{attempt}/{max_retries} ...")
                time.sleep(60)
                continue
            if e.code == 403:
                raise BlockedError(
                    "HTTP 403 from reddit.com — Reddit is blocking this "
                    "IP/User-Agent (datacenter IPs and VPNs are common "
                    "triggers). Try later from a residential connection, or "
                    "use --backend praw with a free script app (see the "
                    "module docstring)."
                ) from e
            if 500 <= e.code < 600 and attempt <= max_retries:
                wait = 5 * (2 ** (attempt - 1))
                print(f"  >> HTTP {e.code} — backing off {wait}s, retry "
                      f"{attempt}/{max_retries} ...")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, OSError) as e:
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                # Not a Reddit block — the local Python has no CA bundle. Common
                # on macOS with a python.org install. Retrying won't help.
                raise BlockedError(
                    "SSL certificate verification failed — this is a local "
                    "Python setup issue, not a Reddit block. On macOS with a "
                    "python.org Python, run the bundled installer once:\n"
                    "  open \"/Applications/Python 3.x/Install Certificates.command\"\n"
                    "(replace 3.x with your version), or: "
                    "pip3 install --upgrade certifi. Then rerun."
                ) from e
            attempt += 1
            if attempt <= max_retries:
                wait = 5 * (2 ** (attempt - 1))
                print(f"  >> network error ({e}) — backing off {wait}s, retry "
                      f"{attempt}/{max_retries} ...")
                time.sleep(wait)
                continue
            raise BlockedError(
                f"could not reach reddit.com ({e}). This network may not "
                "reach reddit.com at all (e.g. a sandboxed cloud environment "
                "with a domain allowlist). Run this script from your own "
                "machine, or use --backend praw if only the public endpoints "
                "are blocked."
            ) from e


def listing_url(subreddit, listing, extra, after=None, limit=100):
    params = {"limit": limit, "raw_json": 1}
    params.update(extra)
    if after:
        params["after"] = after
    return ("https://www.reddit.com/r/%s/%s.json?" % (subreddit, listing)
            + urllib.parse.urlencode(params))


def comments_url(post_id, limit=500):
    return ("https://www.reddit.com/comments/%s.json?" % post_id
            + urllib.parse.urlencode({"limit": limit, "raw_json": 1}))


def post_row(d):
    """t3 listing-child data -> output row. No author — never collected."""
    return {
        "id": d.get("id"),
        "title": d.get("title") or "",
        "selftext": d.get("selftext") or "",
        "created_utc": fmt_ts(d.get("created_utc")),
        "score": d.get("score") if d.get("score") is not None else "",
        "num_comments": (d.get("num_comments")
                         if d.get("num_comments") is not None else ""),
        "permalink": d.get("permalink") or "",
    }


def comment_row(d):
    """t1 comment data -> output row. No author — never collected."""
    return {
        "id": d.get("id"),
        "link_id": d.get("link_id") or "",
        "body": d.get("body") or "",
        "created_utc": fmt_ts(d.get("created_utc")),
        "score": d.get("score") if d.get("score") is not None else "",
    }


def parse_listing(payload):
    """Listing JSON -> ([post rows], after cursor or None)."""
    data = (payload or {}).get("data") or {}
    rows = []
    for child in data.get("children") or []:
        if not isinstance(child, dict) or child.get("kind") != "t3":
            continue
        d = child.get("data") or {}
        if d.get("id"):
            rows.append(post_row(d))
    return rows, data.get("after")


def flatten_comments(children, cap, out=None):
    """Depth-first flatten of a comment tree into rows, capped at `cap`.

    Keeps kind "t1" and recurses into data.replies; "more" stubs (the
    'load more comments' placeholders) are skipped — fetching them would
    cost one extra request each. Note replies is "" (empty string) when a
    comment has none, hence the isinstance(dict) check.
    """
    if out is None:
        out = []
    for child in children or []:
        if len(out) >= cap:
            break
        if not isinstance(child, dict) or child.get("kind") != "t1":
            continue  # skips kind "more" and anything unexpected
        d = child.get("data") or {}
        if d.get("id"):
            out.append(comment_row(d))
        replies = d.get("replies")
        if isinstance(replies, dict):
            flatten_comments(
                ((replies.get("data") or {}).get("children")), cap, out
            )
    return out


def public_listing_posts(subreddit, max_posts, sleep, fetch_json=None):
    """Crawl every listing in LISTINGS, paginating via `after`, until
    max_posts unique post ids are collected or the listings are exhausted."""
    fetch = fetch_json or http_get_json
    posts, seen = [], set()
    for listing, extra in LISTINGS:
        label = listing + ("?t=" + extra["t"] if extra else "")
        after = None
        while len(posts) < max_posts:
            payload = fetch(listing_url(subreddit, listing, extra, after))
            polite_sleep(sleep)
            rows, after = parse_listing(payload)
            added = 0
            for row in rows:
                if len(posts) >= max_posts:
                    break
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                posts.append(row)
                added += 1
            print(f"  [{label}] +{added} posts (total {len(posts)})")
            if not rows or not after:
                break  # listing exhausted
        if len(posts) >= max_posts:
            break
    return posts


def public_post_comments(post_id, max_comments, sleep, fetch_json=None):
    """Fetch one post's comment page and flatten its tree."""
    fetch = fetch_json or http_get_json
    payload = fetch(comments_url(post_id))
    polite_sleep(sleep)
    # /comments/<id>.json returns [post listing, comment listing].
    if not isinstance(payload, list) or len(payload) < 2:
        return []
    children = (((payload[1] or {}).get("data") or {}).get("children")) or []
    return flatten_comments(children, max_comments)


# --------------------------------------------------------------------------
# praw backend — official API via a free "script" app (optional)
# --------------------------------------------------------------------------

def praw_client():
    try:
        import praw
    except ImportError:
        raise SystemExit(
            "The praw backend needs praw:\n"
            "  pip3 install praw\n"
            "plus a free Reddit 'script' app — see the module docstring."
        )
    client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not (client_id and client_secret):
        raise SystemExit(
            "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are not set. Create a "
            "free app at https://www.reddit.com/prefs/apps (type 'script'), "
            "export both env vars, or use --backend public."
        )
    user_agent = os.environ.get("REDDIT_USER_AGENT", "").strip() or UA
    return praw.Reddit(client_id=client_id, client_secret=client_secret,
                       user_agent=user_agent, check_for_async=False)


def praw_post_row(submission):
    """praw Submission -> output row (same shape as post_row; no author)."""
    return {
        "id": submission.id,
        "title": submission.title or "",
        "selftext": getattr(submission, "selftext", "") or "",
        "created_utc": fmt_ts(submission.created_utc),
        "score": submission.score,
        "num_comments": submission.num_comments,
        "permalink": submission.permalink or "",
    }


def praw_listing_posts(reddit, subreddit, max_posts):
    sub = reddit.subreddit(subreddit)
    listings = [
        ("new", sub.new(limit=max_posts)),
        ("hot", sub.hot(limit=max_posts)),
        ("top?t=year", sub.top(time_filter="year", limit=max_posts)),
        ("top?t=all", sub.top(time_filter="all", limit=max_posts)),
    ]
    posts, seen = [], set()
    for label, gen in listings:
        added = 0
        for s in gen:
            if len(posts) >= max_posts:
                break
            if s.id in seen:
                continue
            seen.add(s.id)
            posts.append(praw_post_row(s))
            added += 1
        print(f"  [{label}] +{added} posts (total {len(posts)})")
        if len(posts) >= max_posts:
            break
    return posts


def praw_post_comments(reddit, post_id, max_comments):
    submission = reddit.submission(id=post_id)
    submission.comments.replace_more(limit=0)  # drop 'load more' stubs
    rows = []
    for c in submission.comments.list():
        if len(rows) >= max_comments:
            break
        rows.append({
            "id": c.id,
            "link_id": c.link_id or "",
            "body": c.body or "",
            "created_utc": fmt_ts(c.created_utc),
            "score": c.score,
        })
    return rows


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--backend", choices=["auto", "public", "praw"],
                    default="auto")
    ap.add_argument("--subreddit", default="EnergyDrinks",
                    help="subreddit to scrape (default EnergyDrinks)")
    ap.add_argument("--max-posts", type=int, default=800,
                    help="total unique posts across all listings (default 800)")
    ap.add_argument("--max-comments-per-post", type=int, default=300,
                    help="cap on flattened comments per post (default 300)")
    ap.add_argument("--sleep", type=float, default=2.0,
                    help="base delay between requests in seconds; the actual "
                         "delay adds up to the same again as jitter "
                         "(default 2.0)")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="output dir for the RAW csvs; a relative path is "
                         "resolved against the repo root "
                         "(default: raw_data/Reddit data/r-Energy Drinks)")
    args = ap.parse_args()

    backend = args.backend
    if backend == "auto":
        has_creds = (os.environ.get("REDDIT_CLIENT_ID", "").strip()
                     and os.environ.get("REDDIT_CLIENT_SECRET", "").strip())
        backend = "praw" if has_creds else "public"
    print(f"Backend: {backend}")

    out_dir = args.out
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(REPO_ROOT, out_dir)
    ensure_gitignored()

    stamp = dt.date.today().strftime("%Y%m%d")
    posts_path = os.path.join(out_dir, "energydrinks_posts_%s.csv" % stamp)
    comments_path = os.path.join(
        out_dir, "energydrinks_comments_%s.csv" % stamp
    )

    reddit = praw_client() if backend == "praw" else None
    if reddit:
        posts = praw_listing_posts(reddit, args.subreddit, args.max_posts)
    else:
        posts = public_listing_posts(args.subreddit, args.max_posts,
                                     args.sleep)
    write_csv_merged(posts_path, POST_COLUMNS, posts, "id")

    comments, seen = [], set()
    for i, post in enumerate(posts, 1):
        if to_int(post.get("num_comments")) == 0:
            print(f"  [{i}/{len(posts)}] {post['id']}: 0 comments (skipped)")
            continue
        try:
            if reddit:
                rows = praw_post_comments(reddit, post["id"],
                                          args.max_comments_per_post)
                polite_sleep(args.sleep)  # praw self-throttles; stay polite
            else:
                rows = public_post_comments(post["id"],
                                            args.max_comments_per_post,
                                            args.sleep)
        except BlockedError:
            raise
        except Exception as e:  # one bad post shouldn't kill the run
            print(f"  ! comments failed for {post['id']}: {e}")
            continue
        got = 0
        for row in rows:
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            comments.append(row)
            got += 1
        print(f"  [{i}/{len(posts)}] {post['id']}: {got} comments")
    write_csv_merged(comments_path, COMMENT_COLUMNS, comments, "id")

    print("Done. Next (raw stays untracked; only aggregates are committed):\n"
          "  RAW_DATA_DIR=raw_data python3 "
          "data/scripts/build_external_datasets.py\n"
          "  python3 data/scripts/build_dashboard_json.py")


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit(f"BLOCKED: {e}")
