#!/usr/bin/env python3
"""Generate synthetic-but-realistic sample data in the *same schema* as the
committed datasets — so the pipeline and dashboard can be exercised end-to-end
without the (uncommitted) raw scraper exports or any network access.

Zero dependencies (stdlib `csv`/`random`/`datetime` only) and deterministic
(`--seed`), so two runs produce identical files. Every table matches the header
of its real counterpart in `data/`, and every brand is drawn from the same 23
canonical names the rest of the pipeline uses.

This is NOT a substitute for the real scrapers — the numbers are generated, not
measured. It exists so a new contributor (or CI) can run
`build_dashboard_json.py` and see a populated dashboard on a fresh checkout, and
so the two new sources (Open Food Facts, Wikipedia) have example data to render
until the live scrapers in `data/scrapers/` are run against the network.

Usage:
    python data/scripts/generate_sample_data.py                 # -> data/sample/
    python data/scripts/generate_sample_data.py --out data/sample
    python data/scripts/generate_sample_data.py --only openfoodfacts,wikipedia --out data
    python data/scripts/generate_sample_data.py --seed 7 --scale full
"""
import argparse
import csv
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scrapers"))
from common import CANONICAL_BRANDS, WIKI_ARTICLES  # noqa: E402

# --------------------------------------------------------------------------
# Per-brand "gravity" — rough relative popularity so the biggest brands get the
# most rows/views/mentions, the way the real corpus skews. Not measurements.
# --------------------------------------------------------------------------
WEIGHT = {
    "Red Bull": 100, "Monster": 95, "Celsius": 70, "Prime": 65, "Bang": 45,
    "Alani Nu": 42, "Ghost": 38, "Rockstar": 30, "Reign": 28, "G Fuel": 26,
    "C4": 22, "Zoa": 16, "5-hour Energy": 20, "NOS": 14, "Liquid Death": 24,
    "Bloom Nutrition": 18, "Liquid I.V.": 15, "GURU": 8, "AdvoCare": 7,
    "Pureboost": 5, "Zipfizz": 6, "Spylt": 4, "Xwerks": 4,
}
# brands that market themselves as zero/low sugar
SUGAR_FREE = {"Celsius", "Ghost", "Bang", "Reign", "C4", "Zoa", "Alani Nu",
              "G Fuel", "Liquid Death", "Xwerks", "Pureboost", "Bloom Nutrition"}
FLAVORS = ["Original", "Tropical Blast", "Watermelon", "Blue Razz", "Peach Mango",
           "Sour Apple", "Cherry Limeade", "Strawberry Kiwi", "Citrus", "Grape",
           "Cotton Candy", "Frozen Berry", "Mango", "Vanilla", "Cola"]
COUNTRIES = ["United States", "United Kingdom", "Canada", "Germany", "Australia"]


def wchoice(rng, brands=None):
    brands = brands or CANONICAL_BRANDS
    return rng.choices(brands, weights=[WEIGHT.get(b, 5) for b in brands], k=1)[0]


def scaled(rng, base, spread=0.35):
    return max(0, int(base * rng.uniform(1 - spread, 1 + spread)))


def rdate(rng, start, end):
    span = (end - start).days
    return start + timedelta(days=rng.randint(0, span))


def _w(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path)} ({len(rows)} rows)")


# ==========================================================================
# Generators — one per committed table, matching its exact header.
# ==========================================================================
def gen_amazon(rng, out, n_products):
    prods, reviews = [], []
    start, end = date(2018, 1, 1), date(2026, 5, 1)
    for i in range(n_products):
        brand = wchoice(rng)
        flavor = rng.choice(FLAVORS)
        asin = "B0" + "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))
        price = round(rng.uniform(1.5, 3.2) * rng.choice([1, 4, 12, 12, 24]), 2)
        rating = round(min(5, max(3.2, rng.gauss(4.4, 0.3))), 1)
        rtot = scaled(rng, WEIGHT.get(brand, 5) * 120)
        prods.append({
            "asin": asin, "search_term": f"{brand} energy drink",
            "title": f"{brand} Energy Drink, {flavor}, 12 Fl Oz (Pack of {rng.choice([4,12,24])})",
            "brand": brand, "price_usd": price, "rating": rating,
            "ratings_total": rtot, "reviews_total": scaled(rng, rtot * 0.12),
            "categories": "Grocery & Gourmet Food; Energy Drinks",
            "description": f"{brand} {flavor}. Clean energy, {'zero' if brand in SUGAR_FREE else 'real'} sugar.",
            "feature_bullets": f"{'Zero sugar' if brand in SUGAR_FREE else 'Great taste'} | {flavor} flavor | Boost focus",
            "link": f"https://www.amazon.com/dp/{asin}",
            "scraped_at": "2026-05-20T12:00:00",
        })
        for _ in range(rng.randint(3, 12)):
            rr = min(5, max(1, int(rng.gauss(rating, 1.1))))
            good = rr >= 4
            reviews.append({
                "asin": asin, "brand": brand, "product_title": prods[-1]["title"],
                "search_term": prods[-1]["search_term"],
                "review_id": "R" + "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12)),
                "review_title": rng.choice(
                    ["Love it", "Great taste", "No crash", "Too sweet", "Meh",
                     "My daily driver", "Not worth it", "Best flavor"] ),
                "review_text": rng.choice(
                    ["Tastes amazing and gives me clean energy with no crash or jitters.",
                     "Way too sweet for me, and it's overpriced for what you get.",
                     "Perfect focus boost in the afternoon, zero sugar is a huge plus.",
                     "Gave me the jitters and a rough crash a couple hours later.",
                     "Refreshing, natural flavor, my favorite hydration pick.",
                     "Decent energy but the taste is artificial and chemical."] )
                    if good or rng.random() < 0.5 else
                    "Not great — flat flavor and it just isn't worth the price.",
                "rating": rr,
                "review_date": rdate(rng, start, end).isoformat(),
                "review_country": rng.choice(COUNTRIES),
                "verified_purchase": rng.random() < 0.85,
                "helpful_votes": scaled(rng, 8),
            })
    _w(os.path.join(out, "amazon/products.csv"),
       ["asin", "search_term", "title", "brand", "price_usd", "rating",
        "ratings_total", "reviews_total", "categories", "description",
        "feature_bullets", "link", "scraped_at"], prods)
    _w(os.path.join(out, "amazon/reviews.csv"),
       ["asin", "brand", "product_title", "search_term", "review_id",
        "review_title", "review_text", "rating", "review_date",
        "review_country", "verified_purchase", "helpful_votes"], reviews)


def gen_instagram(rng, out, n_posts):
    start, end = date(2024, 1, 1), date(2026, 5, 1)
    tagset = ["#energy", "#nocrash", "#zerosugar", "#fitness", "#gym", "#focus",
              "#hydration", "#preworkout", "#vibes", "#fuel"]
    rows = []
    for _ in range(n_posts):
        brand = wchoice(rng)
        uname = brand.lower().replace(" ", "").replace(".", "").replace("-", "")
        likes = scaled(rng, WEIGHT.get(brand, 5) * 400)
        rows.append({
            "brand": brand, "brand_username": uname,
            "post_url": f"https://www.instagram.com/p/{''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=11))}/",
            "post_date": rdate(rng, start, end).isoformat(),
            "likes_count": likes, "comments_count": scaled(rng, likes * 0.03),
            "caption": rng.choice(
                ["New drop is here. Which flavor are you grabbing?",
                 "Clean energy, zero crash. Fuel your grind.",
                 "Tag your gym partner. Who needs a boost?",
                 "Summer flavor just landed. Ice cold only."]),
            "hashtags": " ".join(rng.sample(tagset, k=rng.randint(2, 5))),
        })
    _w(os.path.join(out, "instagram/posts.csv"),
       ["brand", "brand_username", "post_url", "post_date", "likes_count",
        "comments_count", "caption", "hashtags"], rows)


def gen_youtube(rng, out, n_videos, comments_per):
    start, end = date(2016, 1, 1), date(2026, 5, 1)
    videos, comments = [], []
    words = ["review", "taste test", "vs", "which is best", "ranking every",
             "trying", "honest review", "tier list", "new flavor"]
    for _ in range(n_videos):
        primary = wchoice(rng)
        mentioned = {primary}
        if rng.random() < 0.4:
            mentioned.add(wchoice(rng))
        vid = "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-", k=11))
        views = scaled(rng, WEIGHT.get(primary, 5) * 9000)
        up = rdate(rng, start, end)
        videos.append({
            "source": "sample", "search_query": f"{primary} energy drink review",
            "video_id": vid, "title": f"{primary} {rng.choice(words)} energy drink",
            "channel": rng.choice(["EnergyReviews", "DrinkTok", "GymRatFuel",
                                   "TasteTestTV", "CaffeineDaily"]),
            "upload_date": up.isoformat(), "duration_seconds": rng.randint(60, 1200),
            "view_count": views, "like_count": scaled(rng, views * 0.04),
            "comment_count": scaled(rng, views * 0.006),
            "description": f"Reviewing {primary}. Sugar, caffeine, taste, crash test.",
            "tags": "energy drink; review; " + primary.lower(),
            "categories": "Entertainment", "url": f"https://youtu.be/{vid}",
            "transcript": "", "brands_mentioned": "; ".join(sorted(mentioned)),
        })
        for _ in range(rng.randint(0, comments_per)):
            comments.append({
                "source": "sample", "video_id": vid,
                "comment_id": "Ug" + "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", k=18)),
                "author": "@" + "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=8)),
                "comment": rng.choice(
                    ["This flavor is unreal, no crash at all.",
                     "Way too much sugar for me.",
                     "Best zero sugar option hands down.",
                     "Gives me jitters every time.",
                     "The taste is so refreshing and clean.",
                     "Overpriced but the focus boost is worth it."]),
                "comment_likes": scaled(rng, 12),
                "comment_date": rdate(rng, up, end).isoformat(),
            })
    _w(os.path.join(out, "youtube/videos.csv"),
       ["source", "search_query", "video_id", "title", "channel", "upload_date",
        "duration_seconds", "view_count", "like_count", "comment_count",
        "description", "tags", "categories", "url", "transcript",
        "brands_mentioned"], videos)
    _w(os.path.join(out, "youtube/comments.csv"),
       ["source", "video_id", "comment_id", "author", "comment", "comment_likes",
        "comment_date"], comments)


def gen_reddit(rng, out):
    rows = []
    for b in CANONICAL_BRANDS:
        m = scaled(rng, WEIGHT.get(b, 5) * 3)
        if m == 0:
            continue
        pos = int(m * rng.uniform(0.35, 0.6))
        neg = int(m * rng.uniform(0.1, 0.3))
        rows.append({"brand": b, "mentions": m, "pos": pos, "neg": neg,
                     "neu": max(0, m - pos - neg)})
    rows.sort(key=lambda r: -r["mentions"])
    _w(os.path.join(out, "reddit/brand_pulse.csv"),
       ["brand", "mentions", "pos", "neg", "neu"], rows)
    _w(os.path.join(out, "reddit/meta.csv"), ["key", "value"], [
        {"key": "posts", "value": 1000}, {"key": "comments", "value": 1000},
        {"key": "date_start", "value": "2026-05-21"},
        {"key": "date_end", "value": "2026-06-09"},
        {"key": "sentiment_method", "value": "sample"},
        {"key": "subreddit", "value": "r/EnergyDrinks"}])


def gen_market(rng, out):
    sizes = []
    rev = 62.0
    for yr in range(2018, 2031):
        prev = rev
        rev = round(rev * rng.uniform(1.03, 1.09), 2)
        sizes.append({"year": yr, "revenue_busd": rev,
                      "yoy_change_pct": round(100 * (rev - prev) / prev, 1)})
    _w(os.path.join(out, "market/market_size.csv"),
       ["year", "revenue_busd", "yoy_change_pct"], sizes)
    _w(os.path.join(out, "market/concept_interest.csv"),
       ["concept", "interest_pct"],
       [{"concept": c, "interest_pct": round(rng.uniform(28, 74), 1)} for c in
        ["Zero sugar", "Natural / clean ingredients", "Added hydration",
         "Nootropic focus blend", "Lower caffeine", "Adaptogens / functional",
         "Prebiotic / gut health", "Recovery blend", "Sustained-release caffeine"]])
    _w(os.path.join(out, "market/motivations.csv"),
       ["factor", "top2box_pct"],
       [{"factor": f, "top2box_pct": round(rng.uniform(30, 78), 1)} for f in
        ["Boosts energy", "Improves focus", "Tastes good", "No sugar crash",
         "Helps hydration", "Trusted brand", "Good value", "Natural ingredients",
         "Supports workouts", "Mental clarity", "Low calorie", "Recommended by friend"]])
    _w(os.path.join(out, "market/market_facts.csv"), ["key", "value"], [
        {"key": "total_2024_busd", "value": sizes[6]["revenue_busd"]},
        {"key": "forecast_year", "value": 2030},
        {"key": "forecast_busd", "value": sizes[-1]["revenue_busd"]},
        {"key": "cagr_hist_pct", "value": 7.2},
        {"key": "cagr_fwd_pct", "value": 4.1},
        {"key": "source", "value": "GENERATED SAMPLE — not a real market report"}])


def gen_openfoodfacts(rng, out):
    rows = []
    for b in CANONICAL_BRANDS:
        for _ in range(rng.randint(1, max(1, WEIGHT.get(b, 5) // 12 + 1))):
            flavor = rng.choice(FLAVORS)
            sugar = 0.0 if b in SUGAR_FREE else round(rng.uniform(9, 13), 1)
            caff = round(rng.uniform(9.5, 32), 1)   # mg / 100 ml
            rows.append({
                "code": "".join(rng.choices("0123456789", k=13)),
                "product_name": f"{b} Energy Drink {flavor}",
                "brand": b, "brand_raw": b,
                "quantity": rng.choice(["250 ml", "355 ml", "473 ml", "500 ml"]),
                "serving_size": rng.choice(["250 ml", "355 ml", "1 can"]),
                "sugars_100g": sugar, "caffeine_mg_100g": caff,
                "energy_kcal_100g": 0 if sugar == 0 else round(sugar * 4 + rng.uniform(2, 8), 1),
                "nutriscore_grade": "e" if sugar > 8 else rng.choice(["c", "d"]),
                "ingredients_text": ("carbonated water, "
                    + ("" if sugar == 0 else "sugar, ")
                    + "citric acid, taurine, caffeine, b-vitamins, natural flavor"),
                "countries": "United States",
                "url": "https://world.openfoodfacts.org/product/" + "".join(rng.choices("0123456789", k=13)),
                "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
    rng.shuffle(rows)
    _w(os.path.join(out, "openfoodfacts/products.csv"),
       ["code", "product_name", "brand", "brand_raw", "quantity", "serving_size",
        "sugars_100g", "caffeine_mg_100g", "energy_kcal_100g", "nutriscore_grade",
        "ingredients_text", "countries", "url", "scraped_at"], rows)


def gen_wikipedia(rng, out, months=12):
    today = date.today().replace(day=1)
    ms = []
    y, m = today.year, today.month
    for _ in range(months):
        m -= 1
        if m == 0:
            m, y = 12, y - 1
        ms.append(f"{y:04d}-{m:02d}")
    ms.reverse()
    interest, pages = [], []
    for brand, article in sorted(WIKI_ARTICLES.items()):
        base = WEIGHT.get(brand, 5) * 900
        total = 0
        for month in ms:
            v = scaled(rng, base, spread=0.5)
            interest.append({"brand": brand, "article": article, "month": month, "views": v})
            total += v
        pages.append({"brand": brand, "article": article,
                      "total_views_12mo": total, "avg_monthly_views": round(total / len(ms))})
    pages.sort(key=lambda r: -r["total_views_12mo"])
    _w(os.path.join(out, "wikipedia/brand_interest.csv"),
       ["brand", "article", "month", "views"], interest)
    _w(os.path.join(out, "wikipedia/brand_pages.csv"),
       ["brand", "article", "total_views_12mo", "avg_monthly_views"], pages)


SOURCES = {
    "amazon": lambda rng, out, s: gen_amazon(rng, out, s["products"]),
    "instagram": lambda rng, out, s: gen_instagram(rng, out, s["posts"]),
    "youtube": lambda rng, out, s: gen_youtube(rng, out, s["videos"], s["comments_per"]),
    "reddit": lambda rng, out, s: gen_reddit(rng, out),
    "market": lambda rng, out, s: gen_market(rng, out),
    "openfoodfacts": lambda rng, out, s: gen_openfoodfacts(rng, out),
    "wikipedia": lambda rng, out, s: gen_wikipedia(rng, out),
}

SCALES = {
    "small": {"products": 75, "posts": 200, "videos": 300, "comments_per": 6},
    "full": {"products": 200, "posts": 600, "videos": 1500, "comments_per": 10},
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join("data", "sample"),
                    help="output directory (default: data/sample)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--scale", choices=list(SCALES), default="small")
    ap.add_argument("--only", default="",
                    help="comma-separated subset of: " + ", ".join(SOURCES))
    args = ap.parse_args()

    rng = random.Random(args.seed)
    scale = SCALES[args.scale]
    which = [s.strip() for s in args.only.split(",") if s.strip()] or list(SOURCES)
    unknown = [s for s in which if s not in SOURCES]
    if unknown:
        ap.error(f"unknown source(s): {unknown}. choose from {list(SOURCES)}")

    print(f"Generating sample data (seed={args.seed}, scale={args.scale}) -> {args.out}")
    for name in which:
        print(f"[{name}]")
        SOURCES[name](rng, args.out, scale)
    print("Done. NOTE: values are synthetic — regenerate real data with the "
          "scrapers in data/scrapers/ or build_clean_datasets.py.")


if __name__ == "__main__":
    main()
