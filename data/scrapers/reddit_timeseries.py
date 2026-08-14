#!/usr/bin/env python3
"""Collect r/EnergyDrinks brand mentions and sentiment as a MONTHLY time series.

Why this exists
---------------
The committed `data/reddit/brand_pulse.csv` is a single 19-day snapshot
(21 May – 9 Jun 2026), and the dashboard is careful to label it as such: it can
rank brands by chatter but it cannot show a trend. Every other social source we
have is time-deep — YouTube runs 2007–2026 — so Reddit is the one place where a
longer pull buys something genuinely new rather than more of the same.

Why the official API rather than cookie scraping
------------------------------------------------
Reddit blocks anonymous access, and the usual workaround is to drive a
logged-in browser session or replay cookies. That is a terms-of-service problem
and a fragile one. Reddit's own API has a free tier (100 queries/minute for a
registered "script" app), it is documented, and it is allowed. For work that may
be submitted academically, allowed beats convenient.

Get credentials (2 minutes, free):
  1. https://www.reddit.com/prefs/apps  ->  "create another app..."
  2. Choose type **script**. Redirect URI can be http://localhost:8080
  3. Export the two values it shows you:
       export REDDIT_CLIENT_ID=...        # under the app name
       export REDDIT_CLIENT_SECRET=...    # the "secret" field
       export REDDIT_USER_AGENT="script:bogus-banana-research:v1 (by /u/yourname)"

Run (needs outbound network — this repo's dev container blocks Reddit, so run it
on your own machine):
    python data/scrapers/reddit_timeseries.py                 # default: 5 years back
    REDDIT_YEARS=8 python data/scrapers/reddit_timeseries.py
    python data/scrapers/reddit_timeseries.py --dry-run       # show the plan, call nothing

Output — aggregates only, matching the repo's existing privacy rule that no
usernames or raw comment text are ever committed:
    data/reddit/brand_pulse_monthly.csv
        month, brand, mentions, pos, neu, neg, score_sum, comment_sum
    data/reddit/meta_timeseries.csv
        key, value  (window, posts seen, method, generated_at)

A KNOWN LIMITATION, stated up front
-----------------------------------
Reddit's search endpoint does not paginate arbitrarily far back — listings cap
out around 1,000 items per query. This script works around that by issuing one
query per (brand x time-slice) rather than one big crawl, which gets far deeper
than a single sweep but is still **not a census**. Treat the output as a
consistent sample per month, good for direction and relative movement, not for
absolute mention counts. The same caveat already applies to the snapshot.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BRAND_ALIASES, match_known_brand, write_csv  # noqa: E402

UA = os.environ.get("REDDIT_USER_AGENT", "script:bogus-banana-research:v1")
SUB = os.environ.get("REDDIT_SUB", "EnergyDrinks")
YEARS = int(os.environ.get("REDDIT_YEARS", "5"))
SLEEP = float(os.environ.get("REDDIT_SLEEP", "1.1"))   # 100 QPM budget, stay well under

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"


# ---------------------------------------------------------------- sentiment
def make_scorer():
    """VADER if available, else the same lexicon fallback the other builders use."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        an = SentimentIntensityAnalyzer()
        return "VADER", lambda t: an.polarity_scores(t)["compound"]
    except ImportError:
        pos = {"love", "great", "best", "amazing", "awesome", "perfect", "good",
               "favorite", "delicious", "smooth", "clean", "worth"}
        neg = {"hate", "worst", "awful", "terrible", "gross", "nasty", "crash",
               "jitters", "sick", "headache", "expensive", "overpriced", "disgusting"}

        def score(t):
            w = set(t.lower().split())
            p, n = len(w & pos), len(w & neg)
            return 0.0 if p + n == 0 else (p - n) / (p + n)
        return "lexicon-fallback", score


# ------------------------------------------------------------------- oauth
def get_token():
    cid = os.environ.get("REDDIT_CLIENT_ID")
    sec = os.environ.get("REDDIT_CLIENT_SECRET")
    if not cid or not sec:
        sys.exit("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET — see the docstring.")
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, headers={"User-Agent": UA})
    import base64
    tok = base64.b64encode(f"{cid}:{sec}".encode()).decode()
    req.add_header("Authorization", f"Basic {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def api_get(path, token, **params):
    url = f"{API}{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Authorization": f"bearer {token}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:                      # rate limited — back off and retry
                time.sleep(2 ** attempt * 5)
                continue
            if e.code in (401, 403):
                raise
            time.sleep(2 ** attempt)
    return {}


# -------------------------------------------------------------------- pull
def month_slices(years):
    """Whole months, oldest first, ending with the last complete month."""
    today = dt.date.today().replace(day=1)
    out = []
    cur = today
    for _ in range(years * 12):
        prev = (cur - dt.timedelta(days=1)).replace(day=1)
        out.append((prev, cur - dt.timedelta(days=1)))
        cur = prev
    return sorted(out)


def collect(token, scorer, years, dry_run=False):
    """One search per (brand, month). Deeper than a single sweep; still a sample."""
    name, score = scorer
    brands = sorted(set(BRAND_ALIASES.values()))
    slices = month_slices(years)
    print(f"plan: {len(brands)} brands x {len(slices)} months = "
          f"{len(brands) * len(slices):,} queries, ~{len(brands)*len(slices)*SLEEP/60:.0f} min")
    if dry_run:
        print("dry run — no calls made. Brands:", ", ".join(brands))
        return {}, 0

    agg, seen = {}, 0
    for start, end in slices:
        mkey = start.strftime("%Y-%m")
        for brand in brands:
            q = f'{brand} timestamp:{int(time.mktime(start.timetuple()))}..{int(time.mktime(end.timetuple()))}'
            d = api_get(f"/r/{SUB}/search", token, q=q, restrict_sr=1, sort="new",
                        limit=100, syntax="cloudsearch", t="all")
            time.sleep(SLEEP)
            for child in d.get("data", {}).get("children", []):
                p = child.get("data", {})
                text = f"{p.get('title','')} {p.get('selftext','')}"
                if not text.strip():
                    continue
                cb = match_known_brand(text) or brand

                s = score(text)
                k = (mkey, cb)
                row = agg.setdefault(k, {"mentions": 0, "pos": 0, "neu": 0, "neg": 0,
                                         "score_sum": 0.0, "comment_sum": 0})
                row["mentions"] += 1
                row["pos" if s > 0.05 else "neg" if s < -0.05 else "neu"] += 1
                row["score_sum"] += s
                row["comment_sum"] += int(p.get("num_comments") or 0)
                seen += 1
        print(f"  {mkey}  running total {seen:,} posts")
    return agg, seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--years", type=int, default=YEARS)
    args = ap.parse_args()

    scorer = make_scorer()
    print(f"sentiment: {scorer[0]}")
    token = None if args.dry_run else get_token()
    agg, seen = collect(token, scorer, args.years, args.dry_run)
    if args.dry_run:
        return

    rows = [[m, b, v["mentions"], v["pos"], v["neu"], v["neg"],
             round(v["score_sum"], 3), v["comment_sum"]]
            for (m, b), v in sorted(agg.items())]
    write_csv("reddit/brand_pulse_monthly.csv",
              ["month", "brand", "mentions", "pos", "neu", "neg", "score_sum", "comment_sum"],
              rows)
    months = sorted({m for m, _ in agg})
    write_csv("reddit/meta_timeseries.csv", ["key", "value"], [
        ("subreddit", f"r/{SUB}"),
        ("month_start", months[0] if months else ""),
        ("month_end", months[-1] if months else ""),
        ("posts_seen", seen),
        ("brands", len({b for _, b in agg})),
        ("sentiment_method", scorer[0]),
        ("sampling", "one search per brand-month; listings cap near 1,000 items so counts "
                     "are a consistent sample, not a census"),
        ("generated_at", dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"),
    ])
    print(f"\nwrote {len(rows)} brand-months from {seen:,} posts -> data/reddit/")
    print("Next: rerun data/scripts/build_dashboard_json.py to fold it into the site.")


if __name__ == "__main__":
    main()
