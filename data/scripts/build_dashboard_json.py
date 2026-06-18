#!/usr/bin/env python3
"""
Aggregate the cleaned market-research CSVs in data/ into one compact JSON
that the website dashboard consumes (src/data/dashboard.json).

Stdlib only — no pandas — so it runs in the base environment. Reduces the
~25 MB YouTube comment corpus down to keyword/theme counts so nothing large
is ever shipped to the browser.

Usage:  python data/scripts/build_dashboard_json.py
"""
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

csv.field_size_limit(10**9)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "src", "data", "dashboard.json")


def rd(path):
    """Read a CSV into a list of dict rows; [] if missing."""
    p = os.path.join(DATA, path)
    if not os.path.exists(p):
        print(f"  ! missing {path}", file=sys.stderr)
        return []
    with open(p, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def num(v):
    """Parse a float from messy cells; None if blank/non-numeric."""
    if v is None:
        return None
    s = str(v).strip().replace("$", "").replace(",", "")
    if s == "" or s.lower() in ("nan", "none", "null"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def year_of(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:19], fmt).year
        except ValueError:
            pass
    m = re.search(r"(19|20)\d{2}", s)
    return int(m.group(0)) if m else None


def rnd(x, n=2):
    return None if x is None else round(x, n)


# ---------------------------------------------------------------- load
print("Reading cleaned CSVs ...")
products = rd("amazon/products.csv")
reviews = rd("amazon/reviews.csv")
posts = rd("instagram/posts.csv")
videos = rd("youtube/videos.csv")
summary = rd("combined/brand_summary.csv")

# ---------------------------------------------------------------- brands (cross-platform table)
brands = []
for r in summary:
    brands.append({
        "brand": r["brand"],
        "amazon_products": int(num(r["amazon_products"]) or 0),
        "amazon_rating": rnd(num(r["amazon_avg_rating"])),
        "amazon_price": rnd(num(r["amazon_avg_price_usd"])),
        "amazon_reviews": int(num(r["amazon_reviews"]) or 0),
        "review_rating": rnd(num(r["amazon_avg_review_rating"])),
        "ig_posts": int(num(r["instagram_posts"]) or 0),
        "ig_likes": int(num(r["instagram_total_likes"]) or 0),
        "ig_comments": int(num(r["instagram_total_comments"]) or 0),
        "yt_videos": int(num(r["youtube_videos"]) or 0),
        "yt_views": int(num(r["youtube_total_views"]) or 0),
        "yt_avg_views": int(num(r["youtube_avg_views"]) or 0),
    })

# ---------------------------------------------------------------- share of voice (YT views)
sov = sorted(
    [{"brand": b["brand"], "views": b["yt_views"]} for b in brands if b["yt_views"] > 0],
    key=lambda x: -x["views"],
)

# ---------------------------------------------------------------- price vs rating (per brand, from products)
pr = defaultdict(lambda: {"price": [], "rating": [], "ratings_total": 0})
for r in products:
    b = (r.get("brand") or "").strip()
    if not b:
        continue
    p, rt = num(r.get("price_usd")), num(r.get("rating"))
    if p is not None:
        pr[b]["price"].append(p)
    if rt is not None:
        pr[b]["rating"].append(rt)
    pr[b]["ratings_total"] += int(num(r.get("ratings_total")) or 0)

price_vs_rating = []
for b, v in pr.items():
    if v["price"] and v["rating"]:
        price_vs_rating.append({
            "brand": b,
            "price": rnd(sum(v["price"]) / len(v["price"])),
            "rating": rnd(sum(v["rating"]) / len(v["rating"])),
            "ratings_total": v["ratings_total"],
        })
price_vs_rating.sort(key=lambda x: -x["ratings_total"])

# ---------------------------------------------------------------- review ratings distribution + trend + verified
dist = Counter()
verified = 0
rev_years = Counter()
for r in reviews:
    rt = num(r.get("rating"))
    if rt is not None and 1 <= rt <= 5:
        dist[int(round(rt))] += 1
    if str(r.get("verified_purchase")).strip().lower() in ("true", "1", "yes"):
        verified += 1
    y = year_of(r.get("review_date"))
    if y and 2015 <= y <= 2026:
        rev_years[y] += 1

rated = sum(dist.values())
review_ratings = {
    "dist": {str(k): dist.get(k, 0) for k in range(1, 6)},
    "total": len(reviews),
    "rated": rated,
    "avg": rnd(sum(k * v for k, v in dist.items()) / rated, 2) if rated else None,
    "verified_pct": rnd(100 * verified / len(reviews), 1) if reviews else None,
}
review_trend = [{"year": y, "count": rev_years[y]} for y in sorted(rev_years)]

# ---------------------------------------------------------------- instagram engagement
ig = defaultdict(lambda: {"likes": 0, "comments": 0, "posts": 0})
hashtags = Counter()
ig_years = Counter()
for r in posts:
    b = (r.get("brand") or r.get("brand_username") or "").strip()
    ig[b]["likes"] += int(num(r.get("likes_count")) or 0)
    ig[b]["comments"] += int(num(r.get("comments_count")) or 0)
    ig[b]["posts"] += 1
    for tag in re.findall(r"#\w+", r.get("hashtags") or ""):
        hashtags[tag.lower()] += 1
    y = year_of(r.get("post_date"))
    if y:
        ig_years[y] += 1

instagram_engagement = sorted(
    [{"brand": b, **v} for b, v in ig.items() if b and v["likes"] > 0],
    key=lambda x: -x["likes"],
)
top_hashtags = [{"tag": t, "count": c} for t, c in hashtags.most_common(14)]

# ---------------------------------------------------------------- youtube trend + channels + top videos
yt_years = defaultdict(lambda: {"videos": 0, "views": 0})
channels = defaultdict(lambda: {"views": 0, "videos": 0})
top_videos = []
total_yt_views = 0
for r in videos:
    v = int(num(r.get("view_count")) or 0)
    total_yt_views += v
    y = year_of(r.get("upload_date"))
    if y and 2008 <= y <= 2026:
        yt_years[y]["videos"] += 1
        yt_years[y]["views"] += v
    ch = (r.get("channel") or "").strip()
    if ch:
        channels[ch]["views"] += v
        channels[ch]["videos"] += 1
    title = (r.get("title") or "").strip()
    if title:
        top_videos.append({"title": title[:80], "channel": ch, "views": v})

youtube_trend = [
    {"year": y, "videos": yt_years[y]["videos"], "views": yt_years[y]["views"]}
    for y in sorted(yt_years)
]
top_channels = sorted(
    [{"channel": c, **v} for c, v in channels.items()],
    key=lambda x: -x["views"],
)[:10]
top_videos = sorted(top_videos, key=lambda x: -x["views"])[:10]

# ---------------------------------------------------------------- voice of customer (reviews + comments)
THEMES = [
    ("Taste & Flavor", r"\b(taste|tastes|tasty|flavou?r|flavou?rs|delicious|yummy)\b"),
    ("Energy & Focus", r"\b(energy|focus|focused|alert|awake|productiv\w*|boost)\b"),
    ("Sugar-Free / Zero", r"(sugar[\s-]?free|zero[\s-]?sugar|no sugar|sugarless)"),
    ("Crash & Jitters", r"\b(crash|crashes|jitter\w*|anxiety|anxious|shaky|shakes)\b"),
    ("Natural / Clean", r"\b(natural|clean|organic|healthy|health)\b"),
    ("Caffeine", r"\b(caffeine|caffeinated)\b"),
    ("Price / Value", r"\b(price|pricey|expensive|cheap|worth|value|overpriced)\b"),
    ("Hydration", r"\b(hydrat\w*|electrolyte\w*)\b"),
]
theme_re = [(name, re.compile(rx, re.I)) for name, rx in THEMES]
voc = Counter()

def scan(text):
    if not text:
        return
    for name, rx in theme_re:
        if rx.search(text):
            voc[name] += 1

for r in reviews:
    scan((r.get("review_title") or "") + " " + (r.get("review_text") or ""))

# stream the big comments file so we never hold it all in memory
cpath = os.path.join(DATA, "youtube/comments.csv")
n_comments = 0
if os.path.exists(cpath):
    with open(cpath, encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            n_comments += 1
            scan(row.get("comment"))
voice_of_customer = [{"theme": n, "mentions": voc[n]} for n, _ in THEMES]
voice_of_customer.sort(key=lambda x: -x["mentions"])

# ---------------------------------------------------------------- KPIs
kpis = {
    "brands": len(brands),
    "amazon_products": len(products),
    "amazon_reviews": len(reviews),
    "instagram_posts": len(posts),
    "youtube_videos": len(videos),
    "youtube_comments": n_comments,
    "youtube_views": total_yt_views,
    "data_points": len(products) + len(reviews) + len(posts) + len(videos) + n_comments,
}

# ---------------------------------------------------------------- write
out = {
    "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "kpis": kpis,
    "brands": brands,
    "share_of_voice": sov,
    "price_vs_rating": price_vs_rating,
    "review_ratings": review_ratings,
    "review_trend": review_trend,
    "instagram_engagement": instagram_engagement,
    "instagram_trend": [{"year": y, "posts": ig_years[y]} for y in sorted(ig_years)],
    "top_hashtags": top_hashtags,
    "youtube_trend": youtube_trend,
    "top_channels": top_channels,
    "top_videos": top_videos,
    "voice_of_customer": voice_of_customer,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, separators=(",", ":"), ensure_ascii=False)

size_kb = os.path.getsize(OUT) / 1024
print(f"Wrote {OUT} ({size_kb:.1f} KB)")
print(f"  brands={kpis['brands']} products={kpis['amazon_products']} "
      f"reviews={kpis['amazon_reviews']} ig_posts={kpis['instagram_posts']} "
      f"yt_videos={kpis['youtube_videos']} yt_comments={kpis['youtube_comments']}")
print(f"  yt_views={kpis['youtube_views']:,} data_points={kpis['data_points']:,}")
