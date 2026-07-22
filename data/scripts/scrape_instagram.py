#!/usr/bin/env python3
"""Scrape recent Instagram posts from energy-drink brand accounts into a CSV.

One backend (FREE — replaces the paid export that produced the original CSV):

  instaloader — uses the Instaloader library's Instagram web client.
                Anonymous mode works for PUBLIC profiles at LOW volume:
                Instaloader's built-in rate controller paces individual
                requests, and this script additionally sleeps 30-60 s
                (jittered; tune with --sleep) between profiles. Keep
                --max-posts modest (default 60) and don't loop it — Instagram
                rate-limits anonymous clients aggressively (HTTP 401/429).
                Optional --login USERNAME authenticates for higher
                reliability: it reuses a saved session file from
                ~/.config/instaloader when one exists
                (Instaloader.load_session_from_file), otherwise prompts for
                the password interactively and saves the session for next
                time. WARNING: automated access violates Instagram's Terms of
                Service and logging in ties the activity to that account —
                Instagram may challenge, temporarily lock, or ban it. Use a
                throwaway account, never your personal one.

Setup (macOS, VS Code terminal):
  pip3 install instaloader

Usage:
  python3 data/scripts/scrape_instagram.py                     # 8 default brand accounts
  python3 data/scripts/scrape_instagram.py --accounts monsterenergy ghostenergy \
      --max-posts 30
  python3 data/scripts/scrape_instagram.py --login MY_THROWAWAY_ACCOUNT
  python3 data/scripts/scrape_instagram.py --sleep 60          # extra-polite pacing

Output:
  data/instagram/posts.csv  one row per post (schema matches the committed
                            file: brand, brand_username, post_url, post_date,
                            likes_count, comments_count, caption, hashtags).
                            Existing rows are MERGED in, deduped on the post
                            shortcode in post_url, freshly scraped rows win —
                            reruns are incremental, not destructive.

Note: instagram.com is unreachable from sandboxed cloud environments with a
domain allowlist (like Claude Code containers) — run this from your own
machine on a residential connection.
"""

import argparse
import csv
import datetime as dt
import os
import random
import re
import sys
import time

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# The 8 brand accounts behind the original data/instagram/posts.csv export.
# Override with --accounts (usernames); brands are derived via BRAND_ALIASES.
DEFAULT_ACCOUNTS = [
    "monsterenergy",     # Monster
    "celsiusofficial",   # Celsius
    "alaninutrition",    # Alani Nu
    "bangenergy",        # Bang
    "drinkprime",        # Prime
    "reignbodyfuel",     # Reign
    "rockstarenergy",    # Rockstar
    "zoaenergy",         # Zoa
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

# Instagram serves bot-identifying User-Agents an instant login wall, so a
# real browser UA (same one the Walmart scraper uses) is passed to Instaloader
# instead of a descriptive one.
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Must match the committed data/instagram/posts.csv header exactly.
POST_COLUMNS = [
    "brand", "brand_username", "post_url", "post_date",
    "likes_count", "comments_count", "caption", "hashtags",
]

# Same tag charset Instagram allows: word characters (unicode-aware in py3).
HASHTAG_RE = re.compile(r"#(\w+)")

# Post shortcode inside any Instagram permalink style — the committed CSV has
# both https://www.instagram.com/<user>/p/<code>/ and .../<user>/reel/<code>/,
# while this script writes the canonical https://www.instagram.com/p/<code>/.
SHORTCODE_RE = re.compile(r"/(?:p|reel|tv)/([A-Za-z0-9_-]+)")


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


def brand_for_username(username):
    """Map an IG username to a canonical brand; fall back to the username."""
    low = (username or "").strip().lower()
    if low in BRAND_ALIASES:
        return BRAND_ALIASES[low]
    return brand_from_title(low) or username


def to_int(value):
    if value is None:
        return None
    m = re.search(r"[\d.]+", str(value).replace(",", ""))
    return int(float(m.group())) if m else None


def extract_hashtags(caption):
    """'#Tag soup #here' -> '#Tag #here' (space-joined, order kept, deduped).

    Instaloader also exposes post.caption_hashtags, but deriving the tags from
    the caption with one regex keeps the row builder testable with plain stubs.
    """
    seen, tags = set(), []
    for tag in HASHTAG_RE.findall(caption or ""):
        if tag.lower() in seen:
            continue
        seen.add(tag.lower())
        tags.append("#" + tag)
    return " ".join(tags)


def post_date_iso(value):
    """post.date_utc (datetime) -> ISO date string; tolerate date/None."""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    return ""


def shortcode_key(post_url):
    """Merge/dedupe key: the shortcode, so old and new URL styles collide."""
    m = SHORTCODE_RE.search(post_url or "")
    return m.group(1) if m else (post_url or "")


def polite_sleep(base):
    time.sleep(base + random.uniform(0, base))


def backoff_sleep(attempt, base):
    delay = base * (2 ** attempt) + random.uniform(0, base)
    print("  retrying in %.0fs..." % delay)
    time.sleep(delay)


def write_csv(path, columns, rows):
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("  wrote %s (%d rows)" % (path, len(rows)))


# --------------------------------------------------------------------------
# Row building + incremental merge (pure stdlib — unit-tested with stubs)
# --------------------------------------------------------------------------

def post_row(post, brand, username):
    """Build one CSV row from an instaloader Post (or a test stub with the
    same attributes: shortcode, date_utc, likes, comments, caption)."""
    caption = post.caption or ""
    likes = getattr(post, "likes", None)
    comments = getattr(post, "comments", None)
    return {
        "brand": brand,
        "brand_username": username,
        "post_url": "https://www.instagram.com/p/%s/" % post.shortcode,
        "post_date": post_date_iso(getattr(post, "date_utc", None)),
        # Instagram hides like counts on some posts; instaloader reports -1.
        "likes_count": likes if isinstance(likes, int) and likes >= 0 else "",
        "comments_count": comments
        if isinstance(comments, int) and comments >= 0 else "",
        "caption": caption,
        "hashtags": extract_hashtags(caption),
    }


def read_existing(path, columns):
    """Rows already in the output CSV, coerced onto the expected columns."""
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {c: (r.get(c) if r.get(c) is not None else "") for c in columns}
            for r in reader
        ]


def merge_rows(old_rows, new_rows):
    """Union old + new, dedupe on the post shortcode, fresh rows win.

    Old rows keep their original order (updated in place when re-scraped) so
    reruns produce small diffs; genuinely new posts are appended after.
    """
    fresh = {}
    for row in new_rows:
        fresh[shortcode_key(row["post_url"])] = row
    merged, seen = [], set()
    for row in old_rows:
        key = shortcode_key(row["post_url"])
        if key in seen:
            continue  # duplicate already in the old file
        seen.add(key)
        merged.append(fresh.pop(key, row))
    for row in new_rows:
        key = shortcode_key(row["post_url"])
        if key in fresh and key not in seen:
            seen.add(key)
            merged.append(fresh.pop(key))
    return merged


# --------------------------------------------------------------------------
# Instaloader backend
# --------------------------------------------------------------------------

class BlockedError(RuntimeError):
    """Instagram is rate-limiting or demanding a login — abort politely."""


class SkipProfile(RuntimeError):
    """This one profile can't be scraped (private/renamed) — skip, keep going."""


class InstaloaderBackend:
    """Thin wrapper: lazy import, optional login, per-profile post iteration.

    Instaloader's built-in RateController already paces and retries individual
    HTTP requests; the between-profile sleeps live in main().
    """

    def __init__(self, login=None):
        try:
            import instaloader
        except ImportError:
            raise SystemExit(
                "The instaloader backend needs Instaloader:\n"
                "  pip3 install instaloader"
            )
        self._il = instaloader
        self.exceptions = instaloader.exceptions
        self.logged_in = bool(login)
        self.loader = instaloader.Instaloader(
            quiet=True,               # suppress per-post download chatter
            user_agent=UA,
            download_pictures=False,  # metadata only — never download media
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
        )
        if login:
            self._login(login)

    def _login(self, username):
        """Reuse the saved session (~/.config/instaloader) or log in and save.

        See the module docstring for the ToS / account-risk warning.
        """
        try:
            self.loader.load_session_from_file(username)
            print("Loaded saved Instagram session for @%s" % username)
            return
        except FileNotFoundError:
            pass
        try:
            self.loader.interactive_login(username)  # prompts for password/2FA
        except self.exceptions.InstaloaderException as e:
            raise SystemExit(
                "Instagram login for @%s failed: %s\n"
                "Check the credentials, complete any checkpoint challenge in "
                "a real browser, then retry." % (username, e)
            )
        self.loader.save_session_to_file()
        print("Logged in as @%s (session saved for reuse)" % username)

    def fetch_posts(self, username, max_posts):
        """Most recent `max_posts` posts of one profile, or raise
        SkipProfile / BlockedError with an actionable message."""
        ex = self.exceptions
        try:
            profile = self._il.Profile.from_username(
                self.loader.context, username
            )
            if profile.is_private and not profile.followed_by_viewer:
                raise SkipProfile(
                    "@%s is private — follow it from the --login account to "
                    "include it" % username
                )
            posts = []
            for post in profile.get_posts():
                posts.append(post)
                if len(posts) >= max_posts:
                    break
            return posts
        except ex.ProfileNotExistsException:
            if not self.logged_in:
                # Instagram now returns 403 on the anonymous graphql endpoint,
                # which instaloader surfaces as a bogus "profile not found".
                # For a well-known brand handle this is almost never a real
                # deletion — it's the block. Abort with the actionable cause
                # instead of skipping every profile with a misleading message.
                raise BlockedError(
                    "Could not load @%s. Instagram returns 403 on the "
                    "anonymous GraphQL endpoint (see the 403 logged above), "
                    "which shows up here as a false 'profile not found' — the "
                    "account almost certainly still exists. Anonymous scraping "
                    "is effectively blocked; rerun with --login USERNAME (use a "
                    "throwaway account — see the docstring warning)." % username
                )
            raise SkipProfile(
                "@%s does not exist (renamed or deleted?) — skipping"
                % username
            )
        except ex.TooManyRequestsException as e:
            raise BlockedError(
                "Instagram is rate-limiting this client (429: %s). Wait a few "
                "hours before rerunning, raise --sleep, or authenticate with "
                "--login USERNAME (see the docstring warning first)." % e
            )
        except ex.LoginRequiredException as e:
            raise BlockedError(
                "Instagram wants a login before serving @%s (%s). Anonymous "
                "access is throttled hard — wait and retry, or use --login "
                "USERNAME (see the docstring warning first)." % (username, e)
            )
        except ex.ConnectionException as e:
            msg = str(e)
            if "401" in msg or "429" in msg or "rate" in msg.lower():
                raise BlockedError(
                    "Instagram rejected the request (%s) — this IP/client is "
                    "throttled. Wait an hour or more before rerunning, or use "
                    "--login USERNAME (see the docstring warning first)." % msg
                )
            raise  # transient network error — main() retries with backoff


def fetch_with_retries(backend, username, max_posts, retries, sleep):
    """Retry transient failures with exponential backoff; never retry
    BlockedError (hammering a rate limit makes it worse) or SkipProfile."""
    for attempt in range(retries + 1):
        try:
            return backend.fetch_posts(username, max_posts)
        except (BlockedError, SkipProfile):
            raise
        except Exception as e:
            if attempt >= retries:
                print("  ! @%s failed after %d attempts: %s — skipping"
                      % (username, retries + 1, e))
                return []
            print("  ! @%s: %s" % (username, e))
            backoff_sleep(attempt, sleep)
    return []


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--accounts", nargs="+", default=DEFAULT_ACCOUNTS,
                    metavar="USERNAME",
                    help="Instagram usernames to scrape (default: the 8 brand "
                         "accounts in the committed CSV)")
    ap.add_argument("--max-posts", type=int, default=60,
                    help="most recent posts to pull per profile (default 60)")
    ap.add_argument("--sleep", type=float, default=30.0,
                    help="base delay between profiles in seconds; actual "
                         "delay is base + jitter, i.e. 30-60s by default")
    ap.add_argument("--retries", type=int, default=2,
                    help="retries per profile on transient errors (default 2)")
    ap.add_argument("--login", default=None, metavar="USERNAME",
                    help="authenticate as this Instagram account (reuses the "
                         "saved session in ~/.config/instaloader; ToS risk — "
                         "see docstring)")
    ap.add_argument("--out", default="data/instagram/posts.csv",
                    help="output CSV (merged with existing rows)")
    args = ap.parse_args()

    backend = InstaloaderBackend(login=args.login)
    print("Backend: instaloader%s"
          % (" (logged in as @%s)" % args.login if args.login else
             " (anonymous — public profiles only)"))

    new_rows, blocked = [], None
    for i, username in enumerate(args.accounts, 1):
        if i > 1:
            polite_sleep(args.sleep)
        brand = brand_for_username(username)
        try:
            posts = fetch_with_retries(backend, username, args.max_posts,
                                       args.retries, args.sleep)
        except SkipProfile as e:
            print("  ! %s" % e)
            continue
        except BlockedError as e:
            blocked = e
            break
        rows = [post_row(p, brand, username) for p in posts]
        new_rows.extend(rows)
        print("  [%d/%d] @%s (%s): %d posts"
              % (i, len(args.accounts), username, brand, len(rows)))

    if new_rows:
        old_rows = read_existing(args.out, POST_COLUMNS)
        merged = merge_rows(old_rows, new_rows)
        print("Merging: %d existing + %d scraped -> %d total"
              % (len(old_rows), len(new_rows), len(merged)))
        write_csv(args.out, POST_COLUMNS, merged)
        print("Done. Next: rerun `python3 data/scripts/build_dashboard_json.py` "
              "to refresh the dashboard aggregate.")
    else:
        print("No new posts scraped — leaving %s untouched." % args.out)

    if blocked:
        sys.exit("BLOCKED: %s%s" % (
            blocked,
            " (partial results were merged into %s)" % args.out
            if new_rows else "",
        ))


if __name__ == "__main__":
    try:
        main()
    except BlockedError as e:
        sys.exit("BLOCKED: %s" % e)
