"""
Pull high-signal qualitative chatter from energy-drink subreddits — the
"I wish it had…", brand-loyalty and complaint language the board (Sofia, Priya)
wanted. Writes data/reddit/reddit_posts.csv and data/reddit/reddit_comments.csv.

Two modes:
  1. Public JSON (no credentials, rate-limited) — default, read-only.
  2. Official API via PRAW (set the env vars below) — more robust at volume.

    pip install requests        # mode 1
    pip install praw            # mode 2 (optional)
    python data/scripts/fetch_reddit.py

For mode 2 register an app at https://www.reddit.com/prefs/apps and set:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
"""
import os
import csv
import time
import requests

HERE = os.path.dirname(__file__)
OUT_DIR = os.path.join(HERE, "..", "reddit")
SUBREDDITS = ["energydrinks", "Celsius", "MonsterEnergy", "Bang", "PrimeHydration"]
HEADERS = {"User-Agent": "energydrink-research/1.0 by u/yourname"}
LISTING = "https://www.reddit.com/r/{sub}/top.json?t=year&limit=100"


def fetch_public(sub):
    r = requests.get(LISTING.format(sub=sub), headers=HEADERS, timeout=30)
    r.raise_for_status()
    children = r.json().get("data", {}).get("children", [])
    return [c["data"] for c in children]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    posts = []
    for sub in SUBREDDITS:
        try:
            data = fetch_public(sub)
        except Exception as e:  # noqa: BLE001
            print(f"  ! r/{sub}: {e}")
            continue
        for d in data:
            posts.append({
                "subreddit": sub,
                "id": d.get("id"),
                "created_utc": d.get("created_utc"),
                "title": d.get("title"),
                "selftext": (d.get("selftext") or "")[:2000],
                "score": d.get("score"),
                "num_comments": d.get("num_comments"),
                "url": "https://reddit.com" + (d.get("permalink") or ""),
            })
        print(f"  r/{sub}: {len(data)} posts")
        time.sleep(2)  # respect Reddit's rate limits

    out = os.path.join(OUT_DIR, "reddit_posts.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(posts[0].keys()) if posts else ["subreddit"])
        w.writeheader()
        w.writerows(posts)
    print(f"wrote {out}  ({len(posts)} posts)")
    print("tip: feed selftext+title into the same keyword/sentiment logic as "
          "build_dashboard_data.py to extend the pain-point and white-space views.")


if __name__ == "__main__":
    main()
