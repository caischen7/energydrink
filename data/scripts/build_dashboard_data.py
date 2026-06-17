"""
Build the Market Intelligence dataset that powers the founder dashboard.

Reads the cleaned CSVs in data/ and emits a single compact JSON at
public/market_intel.json. Everything the dashboard shows is pre-aggregated
here (the browser never loads the 24MB comment corpus), and every number is
traceable back to the source tables.

Run:  python data/scripts/build_dashboard_data.py
"""
import os
import re
import json
import html
from datetime import datetime, timezone

import pandas as pd

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..")
OUT = os.path.join(HERE, "..", "..", "public", "market_intel.json")


# ---------------------------------------------------------------------------
# Vocabulary: the signals we hunt for in consumer text and product copy.
# ---------------------------------------------------------------------------
FLAVORS = [
    "mango", "strawberry", "watermelon", "peach", "grape", "cherry", "lemon",
    "lime", "orange", "pineapple", "coconut", "vanilla", "blueberry",
    "raspberry", "green apple", "citrus", "tropical", "cola", "ginger",
    "mint", "kiwi", "passion fruit", "dragon fruit", "guava", "lychee",
]

# Functional / positioning attributes consumers ask for, with the supply-side
# synonyms we count in product copy.
ATTRIBUTES = {
    "Zero / low sugar": (["zero sugar", "no sugar", "sugar free", "sugarfree"],
                         ["zero sugar", "no sugar", "sugar free", "sugarfree"]),
    "All-natural": (["natural", "no artificial", "naturally"],
                    ["natural", "no artificial"]),
    "Organic": (["organic"], ["organic"]),
    "Electrolytes / hydration": (["electrolyte", "electrolytes", "hydration", "hydrating"],
                                 ["electrolyte", "electrolytes", "hydration"]),
    "Protein": (["protein"], ["protein"]),
    "No crash / clean energy": (["no crash", "clean energy", "without the crash", "smooth energy"],
                                ["no crash", "clean energy", "smooth energy"]),
    "Focus / nootropic": (["focus", "nootropic", "l-theanine", "alpha gpc"],
                          ["focus", "nootropic", "l-theanine"]),
    "Gut health / pre+probiotic": (["gut health", "probiotic", "prebiotic", "gut"],
                                   ["gut health", "probiotic", "prebiotic"]),
    "Adaptogens": (["adaptogen", "ashwagandha", "lions mane", "lion's mane"],
                   ["adaptogen", "ashwagandha", "lions mane"]),
    "Keto / low calorie": (["keto", "low calorie", "low cal"],
                           ["keto", "low calorie"]),
    "Antioxidant": (["antioxidant"], ["antioxidant"]),
    "Vegan": (["vegan"], ["vegan"]),
    "Collagen / beauty": (["collagen", "biotin", "beauty"],
                          ["collagen", "biotin"]),
    "Natural caffeine source": (["green tea", "guarana", "yerba mate", "yerba"],
                                ["green tea", "guarana", "yerba mate", "yerba"]),
}

# Consumer pain points — complaints are differentiation opportunities.
PAINPOINTS = {
    "Tastes artificial / chemical": ["artificial", "chemical", "fake taste"],
    "Too sweet": ["too sweet", "too sugary", "way too sweet"],
    "Bad aftertaste": ["aftertaste", "weird aftertaste", "chemical aftertaste"],
    "Energy crash": ["crash", "crashed", "crashing"],
    "Jitters / anxiety": ["jitters", "jittery", "anxiety", "anxious"],
    "Heart / health worry": ["heart", "heart rate", "palpitation", "blood pressure"],
    "Stomach issues": ["stomach", "nausea", "nauseous", "gut ache"],
    "Too expensive": ["expensive", "overpriced", "too pricey", "not worth the price"],
    "Too much caffeine": ["too much caffeine", "too strong", "caffeine overload"],
    "Feels addictive": ["addicted", "addiction", "addictive"],
}


def ival(v):
    """NaN/None-safe int (NaN is truthy, so `x or 0` is not enough)."""
    return 0 if v is None or pd.isna(v) else int(v)


def fval(v):
    return 0.0 if v is None or pd.isna(v) else float(v)


def count_terms(series, terms):
    """How many rows contain ANY of the given whole-word terms."""
    pat = r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")\b"
    return int(series.str.contains(pat, regex=True, na=False).sum())


def clean_quote(text, max_len=180):
    text = re.sub(r"\s+", " ", str(text)).strip()
    text = re.sub(r"@\w+", "", text)            # strip @mentions
    text = re.sub(r"http\S+", "", text)         # strip urls
    text = html.unescape(text)
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "…"
    return text.strip()


def sample_quotes(series, terms, n=3, min_len=40, max_len=180):
    pat = r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")\b"
    hits = series[series.str.contains(pat, regex=True, na=False)]
    out, seen = [], set()
    for raw in hits:
        q = clean_quote(raw, max_len)
        key = q.lower()[:60]
        if min_len <= len(q) and key not in seen:
            out.append(q)
            seen.add(key)
        if len(out) >= n:
            break
    return out


def main():
    products = pd.read_csv(f"{DATA}/amazon/products.csv")
    reviews = pd.read_csv(f"{DATA}/amazon/reviews.csv")
    ig = pd.read_csv(f"{DATA}/instagram/posts.csv")
    videos = pd.read_csv(f"{DATA}/youtube/videos.csv")
    comments = pd.read_csv(f"{DATA}/youtube/comments.csv")
    summary = pd.read_csv(f"{DATA}/combined/brand_summary.csv")

    # --- text corpora -----------------------------------------------------
    rtext = reviews["review_text"].dropna().astype(str).str.lower()
    ctext = comments["comment"].dropna().astype(str).str.lower()
    consumer = pd.concat([rtext, ctext], ignore_index=True)
    n_consumer = len(consumer)
    ptext = (
        products["title"].fillna("") + " "
        + products["description"].fillna("") + " "
        + products["feature_bullets"].fillna("")
    ).str.lower()
    n_products = len(products)

    # --- brand leaderboard ------------------------------------------------
    total_yt_views = summary["youtube_total_views"].fillna(0).sum()
    total_ig_likes = summary["instagram_total_likes"].fillna(0).sum()
    brands = []
    for _, r in summary.iterrows():
        yt_views = fval(r.get("youtube_total_views"))
        ig_likes = fval(r.get("instagram_total_likes"))
        brands.append({
            "brand": r["brand"],
            "amazon_products": ival(r.get("amazon_products")),
            "avg_rating": round(float(r["amazon_avg_rating"]), 2) if pd.notna(r.get("amazon_avg_rating")) else None,
            "avg_price": round(float(r["amazon_avg_price_usd"]), 2) if pd.notna(r.get("amazon_avg_price_usd")) else None,
            "reviews": ival(r.get("amazon_reviews")),
            "ig_posts": ival(r.get("instagram_posts")),
            "ig_likes": int(ig_likes),
            "yt_videos": ival(r.get("youtube_videos")),
            "yt_views": int(yt_views),
            # share of voice = blended social reach (YouTube views + IG likes)
            "sov_pct": round(100 * (yt_views + ig_likes) / (total_yt_views + total_ig_likes), 2),
        })
    brands.sort(key=lambda b: b["sov_pct"], reverse=True)

    # --- pricing ----------------------------------------------------------
    band_edges = [0, 15, 25, 35, 50, 100]
    band_labels = ["<$15", "$15–25", "$25–35", "$35–50", "$50+"]
    bands = pd.cut(products["price_usd"], band_edges, labels=band_labels)
    pricing_bands = [{"label": l, "count": int((bands == l).sum())} for l in band_labels]
    scatter = []
    for _, r in products.iterrows():
        if pd.notna(r["price_usd"]) and pd.notna(r["rating"]):
            scatter.append({
                "brand": r["brand"] if pd.notna(r["brand"]) else "Unbranded",
                "title": str(r["title"])[:80],
                "price": round(float(r["price_usd"]), 2),
                "rating": float(r["rating"]),
                "reviews": int(r["ratings_total"]) if pd.notna(r["ratings_total"]) else 0,
            })

    # --- flavor demand vs supply -----------------------------------------
    flavors = []
    for f in FLAVORS:
        demand = count_terms(consumer, [f])
        supply = count_terms(ptext, [f])
        flavors.append({
            "name": f,
            "demand": demand,
            "demand_pct": round(100 * demand / n_consumer, 3),
            "supply": supply,
            "supply_pct": round(100 * supply / n_products, 1),
        })
    flavors.sort(key=lambda x: x["demand"], reverse=True)

    # --- attribute demand vs supply (the white-space engine) -------------
    attributes = []
    max_demand = 1
    rows = []
    for label, (dterms, sterms) in ATTRIBUTES.items():
        demand = count_terms(consumer, dterms)
        supply = count_terms(ptext, sterms)
        rows.append((label, demand, supply, dterms))
        max_demand = max(max_demand, demand)
    for label, demand, supply, dterms in rows:
        supply_pct = 100 * supply / n_products
        demand_norm = demand / max_demand                  # 0..1
        # white-space score: lots of consumer pull, little shelf supply
        gap = round(100 * demand_norm * (1 - supply_pct / 100), 1)
        attributes.append({
            "name": label,
            "demand": demand,
            "demand_pct": round(100 * demand / n_consumer, 3),
            "supply": supply,
            "supply_pct": round(supply_pct, 1),
            "gap_score": gap,
        })
    attributes.sort(key=lambda x: x["gap_score"], reverse=True)

    # --- pain points ------------------------------------------------------
    painpoints = []
    for label, terms in PAINPOINTS.items():
        mentions = count_terms(consumer, terms)
        painpoints.append({
            "name": label,
            "mentions": mentions,
            "share_pct": round(100 * mentions / n_consumer, 2),
            "quotes": sample_quotes(pd.concat([rtext, ctext], ignore_index=True), terms, n=3),
        })
    painpoints.sort(key=lambda x: x["mentions"], reverse=True)

    # --- opportunity cards: top white spaces, narrated -------------------
    attr_quotes = pd.concat([rtext, ctext], ignore_index=True)
    opportunities = []
    for a in attributes[:6]:
        terms = ATTRIBUTES[a["name"]][0]
        opportunities.append({
            "title": a["name"],
            "gap_score": a["gap_score"],
            "demand": a["demand"],
            "supply": a["supply"],
            "supply_pct": a["supply_pct"],
            "thesis": (
                f"{a['demand']:,} consumer mentions across reviews & comments, but only "
                f"{a['supply']} of {n_products} catalog products ({a['supply_pct']:.0f}%) "
                f"position on it — strong pull, thin shelf."
            ),
            "quotes": sample_quotes(attr_quotes, terms, n=2),
        })

    out = {
        "meta": {
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "n_products": int(n_products),
            "n_reviews": int(len(reviews)),
            "n_ig_posts": int(len(ig)),
            "n_videos": int(videos["video_id"].nunique()),
            "n_comments": int(len(comments)),
            "n_brands": int(len(brands)),
            "sources": ["Amazon", "Instagram", "YouTube"],
        },
        "brands": brands,
        "pricing": {"bands": pricing_bands, "scatter": scatter},
        "flavors": flavors,
        "attributes": attributes,
        "painpoints": painpoints,
        "opportunities": opportunities,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        # allow_nan=False: NaN/Infinity are invalid JSON and break fetch().json()
        # in the browser — fail loudly here instead of shipping a broken file.
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    size_kb = os.path.getsize(OUT) / 1024
    print(f"wrote {OUT}  ({size_kb:.0f} KB)")
    print(f"  brands={len(brands)} flavors={len(flavors)} attrs={len(attributes)} "
          f"pains={len(painpoints)} opps={len(opportunities)} products_plotted={len(scatter)}")
    print("  top white spaces:", ", ".join(f"{a['name']}({a['gap_score']})" for a in attributes[:4]))


if __name__ == "__main__":
    main()
