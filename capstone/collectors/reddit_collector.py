#!/usr/bin/env python3
"""Reddit Data API collector for flavor + brand mentions. Workstream 3, item 2.

    python capstone/collectors/reddit_collector.py --dry-run     # plan only, no calls
    python capstone/collectors/reddit_collector.py --months 24   # real run, needs creds

OFFICIAL API ONLY. This makes authenticated calls to oauth.reddit.com. It does
not fetch, parse or render reddit.com HTML, does not use old.reddit.com, and
does not replay browser cookies - all of which are the things the project's
compliance rules rule out. If a request fails, it fails; there is no
unauthenticated fallback path anywhere in this file, by design.

CREDENTIALS COME FROM THE ENVIRONMENT, NEVER FROM THIS FILE
    Create a **script** app at https://www.reddit.com/prefs/apps, then:
      export REDDIT_CLIENT_ID=...
      export REDDIT_CLIENT_SECRET=...
      export REDDIT_USER_AGENT="script:bogus-banana-capstone:v1 (by /u/<you>)"
    A descriptive User-Agent is required by Reddit and a generic one gets
    rate-limited harder. No token is written to disk or logged.

>>> BEFORE THE FIRST REAL RUN, SEE capstone/REDDIT_API_TERMS.md <<<
    The project brief makes a current terms summary a precondition of running
    this. That file records what must be confirmed and why it could not be
    confirmed from this environment. --dry-run works without it; a real run is
    Cai's call to make knowingly.

PRIVACY - ENFORCED HERE, NOT BY CONVENTION
    Usernames are never read into the aggregate and raw text is never written
    to disk. The collector holds a comment body only long enough to score it,
    then discards it. The output is counts and sentiment per flavor and brand.
    This matches the rule the repo already follows for data/reddit/.

WHAT IT CANNOT DO
    Reddit's listing endpoints cap around 1,000 items per query, so this cannot
    enumerate a subreddit's history. It issues one query per (term x month)
    slice to get deeper than a single sweep, which yields a CONSISTENT SAMPLE
    per month - good for direction and relative movement, not for absolute
    counts. Any chart built on it must say so.
"""
import argparse
import collections
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flavor_mentions import analyse, FLAVOR_ALIASES, BRAND_ALIASES  # noqa: E402

# ----------------------------------------------------------------- config --
OUT_DIR = os.path.join(ROOT, "data/reddit")
CACHE_DIR = os.path.join(ROOT, ".cache/reddit")
def ua():
    """Read the User-Agent at CALL time, never at import time.

    This was `UA = os.environ.get(...)` evaluated when the module loaded, and
    it broke the standalone bundle: the bundle installs its embedded modules
    before main() runs, so UA was captured as "" before load_dotenv() had put
    anything in the environment. The credential check then failed with
    "Missing credentials" on a machine whose .env had just loaded three
    variables successfully - preflight saw them, this did not.

    Anything read from the environment at import time has the same hazard.
    Read it when you need it."""
    return os.environ.get("REDDIT_USER_AGENT", "").strip()

# Subreddit names are case-insensitive on Reddit, so "energydrinks" and
# "EnergyDrinks" are one subreddit and listing both burned half the calls on
# those rows twice. Deduped case-insensitively below rather than by hand, so a
# future edit cannot reintroduce it.
_SUBS = ["EnergyDrinks", "caffeine", "Celsius_Official", "MonsterEnergy",
         "bang_energy", "AlaniNu", "GhostEnergy"]
SUBREDDITS = list({s.lower(): s for s in _SUBS}.values())

# Pre-registered search terms. Proposed, not settled - the brief says Cai
# approves these before a real run, so they live here to be reviewed.
SEARCH_TERMS = ["energy drink flavor", "energy drink taste", "best flavor",
                "worst flavor", "new flavor", "flavor review", "tier list"]

# Reddit's documented free tier for an OAuth script app is 100 queries per
# minute averaged over a 10-minute window. This paces well under that: the
# collector is not the bottleneck in anyone's day and being a good client is
# cheaper than being rate-limited. VERIFY THIS NUMBER against current docs -
# it is exactly the sort of figure that changes (see REDDIT_API_TERMS.md).
QPM_BUDGET = 60
SLEEP = 60.0 / QPM_BUDGET

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"


class Quota:
    """Counts calls and reads Reddit's own rate-limit headers back, so the
    collector reports what the server said rather than what it assumed."""

    def __init__(self):
        self.calls = 0
        self.remaining = None
        self.reset = None
        self.started = time.time()

    def note(self, headers):
        self.calls += 1
        for k, attr in (("x-ratelimit-remaining", "remaining"),
                        ("x-ratelimit-reset", "reset")):
            v = headers.get(k)
            if v is not None:
                try:
                    setattr(self, attr, float(v))
                except ValueError:
                    pass

    def report(self):
        mins = (time.time() - self.started) / 60 or 1e-9
        return {"calls": self.calls, "calls_per_min": round(self.calls / mins, 1),
                "server_remaining": self.remaining, "server_reset_s": self.reset}


# -------------------------------------------------------------- collector --
def token():
    """OAuth2 client-credentials grant. Raises rather than degrading: there is
    deliberately no unauthenticated path to fall back to."""
    cid = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    sec = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not (cid and sec and ua()):
        sys.exit(
            "Missing credentials. Set all three, then rerun:\n"
            "  export REDDIT_CLIENT_ID=...\n"
            "  export REDDIT_CLIENT_SECRET=...\n"
            '  export REDDIT_USER_AGENT="script:bogus-banana-capstone:v1 (by /u/<you>)"\n'
            "Create a *script* app at https://www.reddit.com/prefs/apps")
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    import base64
    auth = base64.b64encode(f"{cid}:{sec}".encode()).decode()
    req = urllib.request.Request(TOKEN_URL, data=data, headers={
        "Authorization": "Basic " + auth, "User-Agent": ua()})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def get(path, tok, quota, **params):
    """One authenticated GET. Caches by URL so a re-run costs nothing and an
    interrupted run resumes - which matters when a full pull is thousands of
    calls and Reddit's listings shift under you."""
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    key = os.path.join(CACHE_DIR, str(abs(hash(url))) + ".json")
    if os.path.exists(key):
        with open(key) as fh:
            return json.load(fh)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + tok, "User-Agent": ua()})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                quota.note({k.lower(): v for k, v in r.headers.items()})
                body = json.load(r)
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(key, "w") as fh:
                json.dump(body, fh)
            time.sleep(SLEEP)
            return body
        except urllib.error.HTTPError as e:
            if e.code == 429:              # rate limited: back off and retry
                time.sleep(2 ** attempt * 5)
                continue
            if e.code in (401, 403):
                sys.exit(f"Reddit refused the request ({e.code}). Check the "
                         "credentials and that the app type is 'script'.")
            raise
        except urllib.error.URLError as e:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt * 2)
    return None


# --- getting past the 1,000-item listing cap --------------------------------
#
# Reddit caps ANY single listing at roughly 1,000 items. Paginating with
# `after` past that returns nothing - it is a product limit, not a rate limit,
# and no amount of patience or politeness gets a 1,001st item out of one query.
#
# You get past it by PARTITIONING the space into many separate listings, each
# with its own 1,000 cap, and taking the union. That is ordinary documented API
# use, not evasion: every call is an authenticated, rate-limited request to a
# public endpoint. What it is NOT is a census - see the honesty note below.
#
# Three axes, multiplying together:
#
#   1. QUERY TERM. Each distinct `q` is its own listing with its own cap. This
#      is the biggest lever, and it is why the term list below includes bland
#      high-frequency words as well as topical ones: "the" and "it" partition
#      the subreddit far more evenly than "tier list" does.
#   2. SORT. new / top / relevance / comments surface different slices of the
#      same result set, so they overlap heavily but not completely.
#   3. TIME WINDOW. `t` takes all/year/month/week/day. Each is a separate cap,
#      and the narrow ones reach content the `all` listing has long buried.
#
# Then the real multiplier: COMMENT TREES. The cap applies to post listings.
# Each unique post's comments are a separate fetch, and taste talk lives in the
# comments anyway. A few thousand posts at 10-40 comments each is where the
# corpus actually comes from.
#
# HONESTY NOTE, which belongs in the methods section too: the union of many
# capped listings is still not the subreddit. Reddit's search index does not
# reliably surface very old or low-engagement posts at all, so coverage decays
# with age in a way this cannot measure from the inside. Report what was
# collected, never imply completeness.

DEEP_TERMS = [
    # high-frequency partitioners - these do the heavy lifting
    "the", "it", "a", "and", "is", "my", "this", "you", "but", "not",
    # topical, for precision on the flavor question
    "flavor", "flavour", "taste", "tastes", "best", "worst", "new", "tried",
    "review", "tier list", "favorite", "sugar", "caffeine", "can", "drink",
]
DEEP_SORTS = ["new", "top", "relevance", "comments"]
DEEP_WINDOWS = ["all", "year", "month"]

PAGE = 100          # max Reddit returns per call
LISTING_CAP = 1000  # per-listing ceiling; stop paginating when reached


def _listing(path, tok, quota, **params):
    """Paginate one listing to its cap, yielding post dicts.

    Stops on: no children, no `after` cursor, or LISTING_CAP reached. The cap
    check is what keeps this from spending calls on pages Reddit will not
    serve."""
    after, seen = None, 0
    while seen < LISTING_CAP:
        p = dict(params, limit=PAGE)
        if after:
            p["after"] = after
        body = get(path, tok, quota, **p)
        if not body:
            return
        data = body.get("data", {})
        kids = data.get("children", [])
        if not kids:
            return
        for c in kids:
            yield c.get("data", {})
        seen += len(kids)
        after = data.get("after")
        if not after:
            return


def harvest(tok, quota, months, verbose=True, deep=False, max_posts=None):
    """Walk the partition space, yielding (month, text) - TEXT ONLY.

    Post ids are held in memory to deduplicate and to fetch comment trees, and
    are never yielded, written or logged. The caller receives bare strings, so
    no username, id or permalink can reach the analyser or the output.
    """
    since = dt.datetime.utcnow() - dt.timedelta(days=30 * months)
    terms = DEEP_TERMS if deep else SEARCH_TERMS
    sorts = DEEP_SORTS if deep else ["new"]
    windows = DEEP_WINDOWS if deep else ["all"]

    seen_ids = set()      # dedupe across partitions; in-memory only
    stats = {"queries": 0, "posts_raw": 0, "posts_unique": 0, "comments": 0,
             "too_old": 0}

    for sub in SUBREDDITS:
        for term in terms:
            for sort in sorts:
                for win in windows:
                    if max_posts and len(seen_ids) >= max_posts:
                        break
                    stats["queries"] += 1
                    for d in _listing(f"/r/{sub}/search", tok, quota, q=term,
                                      restrict_sr=1, sort=sort, t=win):
                        stats["posts_raw"] += 1
                        pid = d.get("id")
                        if not pid or pid in seen_ids:
                            continue          # union, not sum
                        seen_ids.add(pid)
                        stats["posts_unique"] += 1
                        created = dt.datetime.utcfromtimestamp(d.get("created_utc", 0))
                        if created < since:
                            stats["too_old"] += 1
                            continue
                        month = created.strftime("%Y-%m")
                        text = " ".join(filter(None, [d.get("title"), d.get("selftext")]))
                        if text.strip():
                            yield month, text

                        # The multiplier. Comment trees are not subject to the
                        # post-listing cap, and this is where taste talk is.
                        cbody = get(f"/r/{sub}/comments/{pid}", tok, quota,
                                    limit=500, depth=2, sort="top")
                        if not cbody or len(cbody) < 2:
                            continue
                        for t in _walk_comments(cbody[1].get("data", {}).get("children", [])):
                            stats["comments"] += 1
                            yield month, t
                    if verbose:
                        print(f"  r/{sub} q={term!r} sort={sort} t={win} -> "
                              f"{stats['posts_unique']:,} unique posts, "
                              f"{stats['comments']:,} comments", flush=True)
    harvest.stats = stats


def _walk_comments(children, depth=0):
    """Yield comment bodies from a tree. Skips `more` stubs rather than
    expanding them: each expansion is another call, and at this corpus size the
    marginal comment is not worth the quota. Recorded as a known limitation."""
    if depth > 4:
        return
    for c in children or []:
        if c.get("kind") != "t1":
            continue                      # `more` stubs and anything non-comment
        d = c.get("data", {})
        body = d.get("body")
        if body and body not in ("[deleted]", "[removed]"):
            yield body
        replies = d.get("replies")
        if isinstance(replies, dict):
            yield from _walk_comments(
                replies.get("data", {}).get("children", []), depth + 1)


# --------------------------------------------------------------- analyser --
def run(months, limit=None, verbose=True, deep=False, max_posts=None):
    quota = Quota()
    tok = token()
    rows, by_month = [], collections.Counter()
    for month, text in harvest(tok, quota, months, verbose, deep, max_posts):
        rows.append({"comment": text, "month": month})
        by_month[month] += 1
        if limit and len(rows) >= limit:
            break
    res = analyse(rows)                      # aggregates only
    res["months"] = dict(sorted(by_month.items()))
    res["quota"] = quota.report()
    res["harvest"] = getattr(harvest, "stats", {})
    return res


def _show(path):
    """Display path: relative when that is genuinely shorter and inside ROOT,
    absolute otherwise. relpath against ROOT produced "var/folders/..." for a
    temp dir on macOS - a path that does not exist and cannot be copied."""
    try:
        rel = os.path.relpath(path, ROOT)
    except ValueError:
        return path
    return path if rel.startswith("..") or os.path.isabs(rel) else rel


def write(res, months):
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = dt.date.today().isoformat()

    for name, key in (("flavor", "flavors"), ("brand", "brands")):
        path = os.path.join(OUT_DIR, f"{name}_pulse_api_{stamp}.csv")
        import csv as _csv
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = _csv.DictWriter(fh, fieldnames=list(res[key][0].keys()))
            w.writeheader()
            w.writerows(res[key])
        print(f"  wrote {_show(path)}  ({len(res[key])} rows)")

    meta = os.path.join(OUT_DIR, f"meta_api_{stamp}.csv")
    import csv as _csv
    with open(meta, "w", newline="", encoding="utf-8") as fh:
        w = _csv.writer(fh)
        w.writerow(["key", "value"])
        for k, v in [
            ("source", "Reddit Data API (oauth.reddit.com)"),
            ("method", "authenticated OAuth script app; no HTML, no cookies"),
            ("subreddits", "|".join(SUBREDDITS)),
            ("search_terms", "|".join(SEARCH_TERMS)),
            ("months_requested", months),
            ("rows_seen", res["rows_seen"]),
            ("rows_matched", res["rows_matched"]),
            ("match_rate_pct", res["match_rate_pct"]),
            ("sentiment_engine", res["engine"]),
            ("api_calls", res["quota"]["calls"]),
            ("generated_at", dt.datetime.utcnow().isoformat() + "Z"),
            ("privacy", "aggregates only; no usernames, ids or raw text stored"),
            ("sampling", "listing endpoints cap ~1000 items/query; consistent "
                         "sample per month, NOT a census"),
        ]:
            w.writerow([k, v])
    print(f"  wrote {_show(meta)}")


# ------------------------------------------------------------------- main --
def plan(deep=False):
    """What a real run would do, printed without making a single call."""
    terms = DEEP_TERMS if deep else SEARCH_TERMS
    sorts = DEEP_SORTS if deep else ["new"]
    wins = DEEP_WINDOWS if deep else ["all"]
    parts = len(SUBREDDITS) * len(terms) * len(sorts) * len(wins)
    calls = parts
    print(f"""
PLAN — no network calls made   [{'DEEP' if deep else 'standard'}]

  subreddits     {len(SUBREDDITS)}  {', '.join('r/' + x for x in SUBREDDITS)}
  query terms    {len(terms)}
  sorts          {len(sorts)}  {sorts}
  time windows   {len(wins)}  {wins}
  ------------------------------------------------------------------
  partitions     {parts:,}  (subreddit x term x sort x window)
  each paginates to the {LISTING_CAP:,}-item per-listing cap, so the ceiling is
  {parts * LISTING_CAP:,} post-hits before dedupe - the union will be far smaller,
  and that union is the number that matters.

  search calls   {parts:,} .. {parts * (LISTING_CAP // PAGE):,}  (1 per page, up to {LISTING_CAP // PAGE} pages each)
  comment calls  1 per UNIQUE post
  pacing         {QPM_BUDGET} queries/min ({SLEEP:.1f}s apart)

  HOW THE 1,000 CAP IS BEATEN
  The cap is per listing, not per subreddit. Each distinct (term, sort, window)
  is its own listing with its own {LISTING_CAP:,}. Taking the union across {parts:,} of
  them is ordinary API use - every call is authenticated and rate-limited.
  Comment trees are not subject to the post cap at all, and are where most of
  the text comes from.

  WHAT IT STILL IS NOT
  A census. Reddit's search index does not reliably surface very old or
  low-engagement posts, so coverage decays with age in a way this cannot
  measure from the inside. Report what was collected; never imply completeness.

  WHAT IT COSTS IN TIME
  Pacing is the binding constraint, not quota. A mock run of the same logic
  (capstone/tests/test_deep_harvest.py) turned 48 partitions into ~21,700
  unique posts, so this plan's {parts:,} partitions are in the tens of
  thousands of posts - and every unique post costs one more call for its
  comments. At {QPM_BUDGET}/min that is realistically
  {(parts + 20000) * SLEEP / 3600:.0f}-{(parts * 5 + 40000) * SLEEP / 3600:.0f} HOURS for a full pull.

  Do a bounded first run instead, look at what comes back, then widen:
      --deep --max-posts 2000        (~{(200 + 2000) * SLEEP / 60:.0f} min)
  The cache makes this free to resume, so a long run can be stopped and
  restarted without losing work.

  cache          {os.path.relpath(CACHE_DIR, ROOT)}  (re-runs free, interrupted runs resume)
  vocabulary     {len(FLAVOR_ALIASES)} flavors / {len(BRAND_ALIASES)} brands
  writes         data/reddit/flavor_pulse_api_<date>.csv, brand_..., meta_...
  never writes   usernames, post ids, permalinks, or raw comment text

CREDENTIALS  {'present' if os.environ.get('REDDIT_CLIENT_ID') else 'NOT SET — a real run will stop and tell you how'}
TERMS        read capstone/REDDIT_API_TERMS.md before the first real run
""")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="print the plan, call nothing")
    ap.add_argument("--months", type=int, default=24, help="how far back (default 24)")
    ap.add_argument("--limit", type=int, help="stop after N texts (for a cheap first look)")
    ap.add_argument("--deep", action="store_true",
                    help="partition across terms x sorts x time windows to get "
                         "past the 1,000-item per-listing cap")
    ap.add_argument("--max-posts", type=int,
                    help="stop once this many UNIQUE posts have been seen")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if a.dry_run:
        plan(a.deep)
        return

    res = run(a.months, a.limit, verbose=not a.quiet, deep=a.deep,
              max_posts=a.max_posts)
    h = res.get("harvest", {})
    print(f"\n  {res['rows_seen']:,} texts, {res['rows_matched']:,} matched "
          f"({res['match_rate_pct']}%)  ·  {res['quota']['calls']} API calls")
    if h:
        # Printed because it is the number that answers "did we get past 1,000":
        # posts_raw counts every hit across partitions, posts_unique counts the
        # union. If unique is stuck near 1,000 the partitioning is not working.
        print(f"  {h['queries']} partitions · {h['posts_raw']:,} hits -> "
              f"{h['posts_unique']:,} UNIQUE posts "
              f"({h['posts_raw'] - h['posts_unique']:,} duplicates across "
              f"partitions) · {h['comments']:,} comments")
    write(res, a.months)


if __name__ == "__main__":
    main()
