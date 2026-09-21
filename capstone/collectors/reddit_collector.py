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
UA = os.environ.get("REDDIT_USER_AGENT", "")

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
    if not (cid and sec and UA):
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
        "Authorization": "Basic " + auth, "User-Agent": UA})
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
        "Authorization": "Bearer " + tok, "User-Agent": UA})
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


def harvest(tok, quota, months, verbose=True):
    """Walk subreddits and search terms, yielding TEXT ONLY.

    Yields plain strings, never the API objects, so no username, id or
    permalink can reach the analyser or the output by accident. That is a
    structural guarantee rather than a promise to be careful."""
    since = dt.datetime.utcnow() - dt.timedelta(days=30 * months)
    for sub in SUBREDDITS:
        for term in SEARCH_TERMS:
            body = get(f"/r/{sub}/search", tok, quota, q=term, restrict_sr=1,
                       sort="new", limit=100, t="all")
            if not body:
                continue
            kids = body.get("data", {}).get("children", [])
            if verbose:
                print(f"  r/{sub} :: {term!r} -> {len(kids)} posts", flush=True)
            for c in kids:
                d = c.get("data", {})
                created = dt.datetime.utcfromtimestamp(d.get("created_utc", 0))
                if created < since:
                    continue
                month = created.strftime("%Y-%m")
                text = " ".join(filter(None, [d.get("title"), d.get("selftext")]))
                yield month, text
                # Top-level comments on the post, which is where taste talk is.
                cid = d.get("id")
                if not cid:
                    continue
                cbody = get(f"/r/{sub}/comments/{cid}", tok, quota, limit=100, depth=1)
                if not cbody or len(cbody) < 2:
                    continue
                for cc in cbody[1].get("data", {}).get("children", []):
                    t = cc.get("data", {}).get("body")
                    if t and t not in ("[deleted]", "[removed]"):
                        yield month, t


# --------------------------------------------------------------- analyser --
def run(months, limit=None, verbose=True):
    quota = Quota()
    tok = token()
    rows, by_month = [], collections.Counter()
    for month, text in harvest(tok, quota, months, verbose):
        rows.append({"comment": text, "month": month})
        by_month[month] += 1
        if limit and len(rows) >= limit:
            break
    res = analyse(rows)                      # aggregates only
    res["months"] = dict(sorted(by_month.items()))
    res["quota"] = quota.report()
    return res


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
        print(f"  wrote {os.path.relpath(path, ROOT)}  ({len(res[key])} rows)")

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
    print(f"  wrote {os.path.relpath(meta, ROOT)}")


# ------------------------------------------------------------------- main --
def plan():
    """What a real run would do, printed without making a single call."""
    calls = len(SUBREDDITS) * len(SEARCH_TERMS)
    print(f"""
PLAN — no network calls made

  subreddits     {len(SUBREDDITS)}  {', '.join('r/' + s for s in SUBREDDITS)}
  search terms   {len(SEARCH_TERMS)}  {SEARCH_TERMS}
  search calls   {calls}  (one per subreddit x term)
  + one comments call per post returned, so the real total is
    roughly {calls} + (posts found), commonly {calls * 20}-{calls * 60}
  pacing         {QPM_BUDGET} queries/min ({SLEEP:.1f}s apart)
  est. wall time {calls * 30 * SLEEP / 60:.0f}-{calls * 60 * SLEEP / 60:.0f} min for a full pull
  cache          {os.path.relpath(CACHE_DIR, ROOT)}  (re-runs are free, interrupted runs resume)

  vocabulary     {len(FLAVOR_ALIASES)} flavors / {len(BRAND_ALIASES)} brands,
                 from capstone/collectors/flavor_mentions.py

  writes         data/reddit/flavor_pulse_api_<date>.csv
                 data/reddit/brand_pulse_api_<date>.csv
                 data/reddit/meta_api_<date>.csv
  never writes   usernames, post ids, permalinks, or raw comment text

CREDENTIALS  {'present' if os.environ.get('REDDIT_CLIENT_ID') else 'NOT SET — a real run will stop and tell you how'}
TERMS        read capstone/REDDIT_API_TERMS.md before the first real run
""")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="print the plan, call nothing")
    ap.add_argument("--months", type=int, default=24, help="how far back (default 24)")
    ap.add_argument("--limit", type=int, help="stop after N texts (for a cheap first look)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if a.dry_run:
        plan()
        return

    res = run(a.months, a.limit, verbose=not a.quiet)
    print(f"\n  {res['rows_seen']:,} texts, {res['rows_matched']:,} matched "
          f"({res['match_rate_pct']}%)  ·  {res['quota']['calls']} API calls")
    write(res, a.months)


if __name__ == "__main__":
    main()
