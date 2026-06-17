# Energy drink market data

Cleaned, de-duplicated exports from three scraping efforts (Amazon, Instagram,
YouTube) covering the energy drink category. Raw scraper output (zips/xlsx)
is not committed — it's large, messy (HTML noise, exploded join rows,
inconsistent schemas across scraper versions) and partly redundant. The CSVs
here are the cleaned result; `scripts/build_clean_datasets.py` regenerates
them from the raw exports.

## Layout

```
data/
  amazon/
    products.csv   75 energy drink products: brand, price, rating, category, description
    reviews.csv    552 reviews keyed by asin, with parsed date/country and verified flag
  instagram/
    posts.csv      120 posts from 8 brand accounts, with likes/comments parsed out of caption_meta
  youtube/
    videos.csv     3,214 unique videos merged from 3 scraper generations, with brand mentions
    comments.csv   125,054 unique comments across those videos
  combined/
    brand_mentions_by_platform.csv   long-format table: one row per (platform, brand, item)
    brand_summary.csv                one row per brand, aggregated across all 3 platforms
  scripts/
    build_clean_datasets.py          regenerates everything above from raw exports
    build_dashboard_data.py          aggregates the cleaned CSVs into public/market_intel.json
    fetch_openfoodfacts.py           loader: per-SKU nutrition from Open Food Facts (open API)
    fetch_google_trends.py           loader: search-interest momentum from Google Trends (pytrends)
    fetch_reddit.py                  loader: qualitative chatter from energy-drink subreddits
  nutrition/
    brand_nutrition.csv              curated flagship nutrition (caffeine, sugar, calories) per brand
  market/
    market_context.json              real US market size + dollar-share, with sources
```

### Added data sources

- **Nutrition** (`nutrition/brand_nutrition.csv`) — curated, public label values
  for each tracked brand's flagship SKU (caffeine mg, sugar g, calories, serving).
  Powers the dashboard's **Formulation map**. Extend per-SKU with
  `fetch_openfoodfacts.py` where outbound network is available.
- **Market context** (`market/market_context.json`) — real US category size
  (~$21B), CAGR, and dollar-share (Red Bull 37 / Monster 28 / Celsius 12 /
  others 23), pulled via web search with sources cited inline. Powers the
  **Market sizing / TAM** feature.
- **Momentum** — no new file; computed in `build_dashboard_data.py` from our own
  timestamps (YouTube `upload_date` + Amazon `review_date` + Instagram
  `post_date`) into monthly per-brand series. Powers the **Momentum explorer**.
  `fetch_google_trends.py` upgrades this to true search interest.
- **Loaders** (`fetch_*.py`) are runnable where outbound HTTPS is allowed (they
  hit live APIs). Each documents its prereqs; Reddit/Trends note any credentials.

The **Market Intelligence terminal** (`/dashboard.html`, source in
`src/dashboard/`) is a founder-facing tool built on this data — a white-space
finder, pricing-arbitrage view, pain→positioning board, share-of-voice
leaderboard and an interactive concept builder. It reads a single pre-aggregated
file, `public/market_intel.json`, produced by `build_dashboard_data.py` (the
browser never loads the 24MB comment corpus). The advisory board that scoped the
tool and voted the data roadmap is documented in
[`../docs/advisory-board.md`](../docs/advisory-board.md) and
[`../docs/board-discussion.md`](../docs/board-discussion.md).

```
# regenerate the dashboard feed after the cleaned CSVs change
pip install pandas
python data/scripts/build_dashboard_data.py    # -> public/market_intel.json
```

## Cleaning notes

- **Brands normalized** to a single canonical name across all platforms (e.g.
  `monsterenergy` / `Monster` / `MONSTER` -> `Monster`). See `BRAND_ALIASES`
  in the build script.
- **Amazon**: `price` stripped to a numeric `price_usd`; `categories` (a
  stringified list of dicts) flattened to a `;`-joined string; reviews'
  `date` column split into `review_country` + parsed `review_date`.
- **Instagram**: `caption_meta` (a single freeform string like `"41K likes,
  151 comments - monsterenergy on April 28, 2026: \"...\""`) parsed into
  `likes_count`, `comments_count`, `post_date`, `caption`. K/M suffixes
  expanded to integers.
- **YouTube**: three scraper generations (`prototype_1`, `prototype_2`,
  `overnight_12hr`) used different column names and one of them exploded to
  one row per comment, inflating the raw file to 3.3M lines for only ~3,200
  distinct videos. Reshaped into one `videos` table (deduped on `video_id`)
  and one `comments` table (deduped on `comment_id`), with a `source` column
  so provenance isn't lost. The `overnight_12hr` brand-mention extraction
  (regex/keyword matching of brand names in title/description) was merged
  onto `videos.brands_mentioned`.

## How the datasets combine

The three platforms aren't directly joinable row-by-row (different units:
products, reviews, posts, videos, comments) but they share **brand** as a
common key, which is what `combined/` is built around:

- **`brand_mentions_by_platform.csv`** — a long/tidy table with one row per
  mention of a brand on any platform (`platform`, `brand`, `record_type`,
  `record_id`, `date`, `engagement_metric`, `engagement_value`,
  `text_sample`). This is the table to filter/groupby/pivot for
  cross-platform brand analysis, sentiment-over-time charts, etc.
- **`brand_summary.csv`** — one row per brand with aggregated stats from all
  three platforms side by side: Amazon product count/avg rating/avg price,
  Amazon review count/avg rating, Instagram post count/total likes/total
  comments, YouTube video count/total views/avg views. Good for a single
  "which brand wins where" table or chart.

Other ways to extend the join:
- **Time-aligned trend analysis**: `amazon/reviews.review_date`,
  `instagram/posts.post_date`, and `youtube/videos.upload_date` /
  `youtube/comments.comment_date` are all real dates — bucket by week/month
  per brand to compare review sentiment against social posting cadence.
- **Text corpus per brand**: concatenate `amazon/reviews.review_text` +
  `instagram/posts.caption` + `youtube/comments.comment` filtered by brand
  for topic modeling / sentiment analysis on a single brand across every
  channel consumers talk about it.
- **Engagement-to-rating correlation**: join `brand_summary` columns to see
  whether brands with higher Instagram/YouTube engagement also have higher
  Amazon ratings, or whether they diverge (e.g. high social buzz but
  mediocre product reviews).

## Regenerating

```
pip install pandas openpyxl
RAW_DATA_DIR=/path/to/unzipped/raw/data python data/scripts/build_clean_datasets.py
```

`RAW_DATA_DIR` should contain `Amazon data/`, `Instagram data/`, and
`Youtube data/` subfolders matching the original scraper export layout.
