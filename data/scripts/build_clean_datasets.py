# Rebuilds data/{amazon,instagram,youtube,combined}/*.csv from the raw scraper
# exports. The raw zips/xlsx are not committed to the repo (PII + size), so
# point RAW at wherever you've unzipped "Amazon data/", "Instagram data/" and
# "Youtube data/" before running this.
import ast
import os
import re
import pandas as pd

RAW = os.environ.get("RAW_DATA_DIR", "/tmp/extract")
OUT = os.path.join(os.path.dirname(__file__), "..")

os.makedirs(f"{OUT}/amazon", exist_ok=True)
os.makedirs(f"{OUT}/instagram", exist_ok=True)
os.makedirs(f"{OUT}/youtube", exist_ok=True)
os.makedirs(f"{OUT}/combined", exist_ok=True)

# ---------------------------------------------------------------------------
# Brand normalization
# ---------------------------------------------------------------------------
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


def norm_brand(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    key = str(value).strip().lower()
    return BRAND_ALIASES.get(key, str(value).strip())


def split_brands(value):
    """Split a comma-separated 'brands_mentioned' cell into a normalized list."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [norm_brand(b) for b in str(value).split(",") if b.strip()]


# ---------------------------------------------------------------------------
# Amazon
# ---------------------------------------------------------------------------
def clean_amazon():
    products = pd.read_csv(f"{RAW}/amazon/Amazon data/amazon_75_products.csv")
    reviews = pd.read_csv(f"{RAW}/amazon/Amazon data/amazon_75_products_reviews.csv")

    products = products.drop_duplicates(subset="asin").copy()

    # Capture the FIRST price-like number ("$19.98 ($1.67/Fl Oz)" -> 19.98)
    # rather than stripping every non-digit and concatenating them, which would
    # fuse a price and a per-unit figure into one bogus number.
    price_re = re.compile(r"\$?\s*(\d[\d,]*(?:\.\d+)?)")

    def parse_price(cell):
        if pd.isna(cell):
            return None
        m = price_re.search(str(cell))
        return float(m.group(1).replace(",", "")) if m else None

    products["price_usd"] = products["price"].apply(parse_price)

    def extract_categories(cell):
        if pd.isna(cell):
            return ""
        try:
            # ast.literal_eval safely parses the list-of-dicts literal; eval()
            # on scraped page text is an unnecessary code-execution risk.
            items = ast.literal_eval(cell)
        except (ValueError, SyntaxError):
            return ""
        if not isinstance(items, (list, tuple)):
            return ""
        return "; ".join(d.get("name", "") for d in items if isinstance(d, dict))

    products["categories"] = products["categories"].apply(extract_categories)
    products["brand"] = products["brand"].apply(norm_brand)
    products["scraped_at"] = pd.to_datetime(products["scraped_at"], errors="coerce")

    products = products[
        [
            "asin", "search_term", "title", "brand", "price_usd", "rating",
            "ratings_total", "reviews_total", "categories", "description",
            "feature_bullets", "link", "scraped_at",
        ]
    ].sort_values("asin")

    reviews = reviews.drop_duplicates(subset="review_id").copy()

    date_re = re.compile(r"Reviewed in (.+?) on (.+)$")

    def split_date(cell):
        if pd.isna(cell):
            return pd.Series([None, None])
        m = date_re.match(str(cell).strip())
        if not m:
            return pd.Series([None, None])
        return pd.Series([m.group(1).strip(), m.group(2).strip()])

    reviews[["review_country", "review_date_raw"]] = reviews["date"].apply(split_date)
    reviews["review_date"] = pd.to_datetime(
        reviews["review_date_raw"], errors="coerce"
    ).dt.date
    reviews["brand"] = reviews["asin"].map(
        products.set_index("asin")["brand"].to_dict()
    )

    # Brand-less rows are silently dropped from the cross-platform views in
    # build_combined() (guarded by `if r["brand"]`), so surface the count here
    # rather than losing ~10% of the corpus without a trace.
    missing_p = int(products["brand"].isna().sum())
    missing_r = int(reviews["brand"].isna().sum())
    if missing_p or missing_r:
        print(
            f"  amazon: {missing_p}/{len(products)} products and "
            f"{missing_r}/{len(reviews)} reviews have no brand — these are "
            "excluded from the combined brand views"
        )

    reviews = reviews[
        [
            "asin", "brand", "product_title", "search_term", "review_id",
            "review_title", "review_text", "rating", "review_date",
            "review_country", "verified_purchase", "helpful_votes",
        ]
    ].sort_values(["asin", "review_date"])

    products.to_csv(f"{OUT}/amazon/products.csv", index=False)
    reviews.to_csv(f"{OUT}/amazon/reviews.csv", index=False)
    return products, reviews


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------
def clean_instagram():
    df = pd.read_csv(f"{RAW}/instagram/Instagram data/instagram_energy_drink_posts.csv")
    df = df.drop_duplicates(subset="post_url").copy()

    meta_re = re.compile(
        r"^([\d.,]+[KM]?)\s+likes,\s*([\d.,]+[KM]?)\s+comments\s*-\s*(.+?)\s+on\s+(.+?):\s*\"(.*)\"\.\s*$",
        re.DOTALL,
    )

    def parse_count(text):
        if text is None:
            return None
        text = text.strip().upper().replace(",", "")
        mult = 1
        if text.endswith("K"):
            mult, text = 1_000, text[:-1]
        elif text.endswith("M"):
            mult, text = 1_000_000, text[:-1]
        try:
            return int(float(text) * mult)
        except ValueError:
            return None

    def parse_meta(cell):
        if pd.isna(cell):
            return pd.Series([None, None, None, None])
        m = meta_re.match(str(cell).strip())
        if not m:
            return pd.Series([None, None, None, None])
        likes, comments, _username, date_str, caption = m.groups()
        return pd.Series([parse_count(likes), parse_count(comments), date_str, caption.strip()])

    df[["likes_count", "comments_count", "post_date_raw", "caption"]] = df["caption_meta"].apply(
        parse_meta
    )
    df["post_date"] = pd.to_datetime(df["post_date_raw"], errors="coerce").dt.date
    df["brand"] = df["brand_username"].apply(norm_brand)

    df = df[
        [
            "brand", "brand_username", "post_url", "post_date", "likes_count",
            "comments_count", "caption", "hashtags",
        ]
    ].sort_values(["brand", "post_date"])

    df.to_csv(f"{OUT}/instagram/posts.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------
def clean_youtube():
    overnight = pd.read_csv(
        f"{RAW}/youtube/Youtube data/yt_webscrapping_protoype_3(overnight)/energy_drink_12hr_dataset.csv"
    )
    brand_mentions = pd.read_csv(
        f"{RAW}/youtube/Youtube data/yt_webscrapping_protoype_3(overnight)/energy_drink_brand_mentions.csv"
    )[["video_id", "brands_mentioned"]]

    v1 = pd.read_csv(
        f"{RAW}/youtube/Youtube data/yt_webscrapping_prototype_1/energy_drink_youtube_videos_no_api.csv"
    )
    c1 = pd.read_csv(
        f"{RAW}/youtube/Youtube data/yt_webscrapping_prototype_1/energy_drink_youtube_comments_no_api.csv"
    )

    v2 = pd.read_csv(
        f"{RAW}/youtube/Youtube data/yt_webscrapping_prototype_2/energy_drink_videos_prototype.csv"
    )
    c2 = pd.read_csv(
        f"{RAW}/youtube/Youtube data/yt_webscrapping_prototype_2/energy_drink_comments_prototype.csv"
    )

    # --- videos: unify schema across the three scraper generations ---
    v0 = (
        overnight.drop_duplicates(subset="video_id")[
            [
                "search_query", "video_id", "video_title", "channel",
                "upload_date", "duration_seconds", "view_count", "like_count",
                "video_comment_count", "description", "tags", "categories",
                "url", "transcript",
            ]
        ]
        .rename(columns={"video_title": "title", "video_comment_count": "comment_count"})
    )
    v0["source"] = "overnight_12hr"

    v1 = v1.rename(columns={"views": "view_count", "likes": "like_count"}).copy()
    v1["source"] = "prototype_1"
    v1["search_query"] = None

    v2 = v2.rename(columns={"comment_count": "comment_count"}).copy()
    v2["source"] = "prototype_2"

    video_cols = [
        "source", "search_query", "video_id", "title", "channel", "upload_date",
        "duration_seconds", "view_count", "like_count", "comment_count",
        "description", "tags", "categories", "url", "transcript",
    ]
    videos = pd.concat(
        [v0.reindex(columns=video_cols), v1.reindex(columns=video_cols), v2.reindex(columns=video_cols)],
        ignore_index=True,
    )
    # one row per video: prefer the richest source if a video was scraped twice
    videos = videos.sort_values("source").drop_duplicates(subset="video_id", keep="first")

    videos = videos.merge(brand_mentions, on="video_id", how="left")
    videos["brands_mentioned"] = videos["brands_mentioned"].apply(
        lambda v: "; ".join(split_brands(v)) if pd.notna(v) else None
    )
    videos["upload_date"] = pd.to_datetime(
        videos["upload_date"], format="%Y%m%d", errors="coerce"
    ).dt.date

    videos = videos.sort_values("video_id")
    videos.to_csv(f"{OUT}/youtube/videos.csv", index=False)

    # --- comments: unify schema ---
    cm0 = overnight.dropna(subset=["comment_id"])[
        ["video_id", "comment_id", "comment_author", "comment_text", "comment_likes", "comment_timestamp"]
    ].rename(columns={"comment_author": "author", "comment_text": "comment"})
    cm0["source"] = "overnight_12hr"

    cm1 = c1.rename(columns={"likes": "comment_likes", "timestamp": "comment_timestamp"})[
        ["video_id", "comment_id", "author", "comment", "comment_likes", "comment_timestamp"]
    ]
    cm1["source"] = "prototype_1"

    cm2 = c2.rename(columns={"comment_likes": "comment_likes", "comment_timestamp": "comment_timestamp"})[
        ["video_id", "comment_id", "author", "comment", "comment_likes", "comment_timestamp"]
    ]
    cm2["source"] = "prototype_2"

    comments = pd.concat([cm0, cm1, cm2], ignore_index=True)
    comments = comments.drop_duplicates(subset="comment_id")
    comments["comment_timestamp"] = pd.to_numeric(comments["comment_timestamp"], errors="coerce")
    comments["comment_date"] = pd.to_datetime(
        comments["comment_timestamp"], unit="s", errors="coerce"
    ).dt.date

    comments = comments[
        ["source", "video_id", "comment_id", "author", "comment", "comment_likes", "comment_date"]
    ].sort_values("video_id")
    comments.to_csv(f"{OUT}/youtube/comments.csv", index=False)

    return videos, comments


# ---------------------------------------------------------------------------
# Combined cross-platform views
# ---------------------------------------------------------------------------
def build_combined(products, reviews, ig_posts, videos, comments):
    rows = []

    for _, r in products.iterrows():
        if r["brand"]:
            rows.append(
                dict(
                    platform="amazon", brand=r["brand"], record_type="product",
                    record_id=r["asin"], date=None, engagement_metric="ratings_total",
                    engagement_value=r["ratings_total"], text_sample=r["title"],
                )
            )

    for _, r in reviews.iterrows():
        if r["brand"]:
            rows.append(
                dict(
                    platform="amazon", brand=r["brand"], record_type="review",
                    record_id=r["review_id"], date=r["review_date"],
                    engagement_metric="helpful_votes", engagement_value=r["helpful_votes"],
                    text_sample=r["review_text"],
                )
            )

    for _, r in ig_posts.iterrows():
        if r["brand"]:
            rows.append(
                dict(
                    platform="instagram", brand=r["brand"], record_type="post",
                    record_id=r["post_url"], date=r["post_date"],
                    engagement_metric="likes_count", engagement_value=r["likes_count"],
                    text_sample=r["caption"],
                )
            )

    for _, r in videos.iterrows():
        for brand in (r["brands_mentioned"].split("; ") if pd.notna(r["brands_mentioned"]) else []):
            rows.append(
                dict(
                    platform="youtube", brand=brand, record_type="video",
                    record_id=r["video_id"], date=r["upload_date"],
                    engagement_metric="view_count", engagement_value=r["view_count"],
                    text_sample=r["title"],
                )
            )

    mentions = pd.DataFrame(rows)
    mentions.to_csv(f"{OUT}/combined/brand_mentions_by_platform.csv", index=False)

    # brand-level summary
    amz_p = products[products["brand"].notna()].groupby("brand").agg(
        amazon_products=("asin", "nunique"),
        amazon_avg_rating=("rating", "mean"),
        amazon_avg_price_usd=("price_usd", "mean"),
    )
    amz_r = reviews[reviews["brand"].notna()].groupby("brand").agg(
        amazon_reviews=("review_id", "nunique"),
        amazon_avg_review_rating=("rating", "mean"),
    )
    ig = ig_posts[ig_posts["brand"].notna()].groupby("brand").agg(
        instagram_posts=("post_url", "nunique"),
        instagram_total_likes=("likes_count", "sum"),
        instagram_total_comments=("comments_count", "sum"),
    )

    yt_exploded = videos.assign(
        brand=videos["brands_mentioned"].fillna("").str.split("; ")
    ).explode("brand")
    yt_exploded = yt_exploded[yt_exploded["brand"] != ""]
    yt = yt_exploded.groupby("brand").agg(
        youtube_videos=("video_id", "nunique"),
        youtube_total_views=("view_count", "sum"),
        youtube_avg_views=("view_count", "mean"),
    )

    summary = amz_p.join(amz_r, how="outer").join(ig, how="outer").join(yt, how="outer")
    summary = summary.reset_index().rename(columns={"index": "brand"})
    summary.to_csv(f"{OUT}/combined/brand_summary.csv", index=False)

    return mentions, summary


if __name__ == "__main__":
    products, reviews = clean_amazon()
    ig_posts = clean_instagram()
    videos, comments = clean_youtube()
    mentions, summary = build_combined(products, reviews, ig_posts, videos, comments)

    print("products", products.shape)
    print("reviews", reviews.shape)
    print("instagram posts", ig_posts.shape)
    print("youtube videos", videos.shape)
    print("youtube comments", comments.shape)
    print("brand mentions", mentions.shape)
    print("brand summary", summary.shape)
