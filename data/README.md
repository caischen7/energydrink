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
  openfoodfacts/
    products.csv     energy-drink products with sugar + caffeine per 100ml + Nutri-Score
  wikipedia/
    brand_interest.csv   monthly Wikipedia pageviews per brand (curiosity proxy)
    brand_pages.csv      per-brand 12-month pageview totals
  scrapers/                          NEW live scrapers (stdlib urllib, no pandas)
    common.py                        shared brand normalization + polite HTTP helper
    openfoodfacts.py                 Open Food Facts API -> openfoodfacts/products.csv
    wikipedia.py                     Wikimedia Pageviews API -> wikipedia/*.csv
  scripts/
    build_clean_datasets.py          regenerates amazon/instagram/youtube from raw exports
    build_external_datasets.py       regenerates market/ + reddit/ from raw corpus
    generate_sample_data.py          zero-dep synthetic data in the SAME schema (no network)
    run_scrapers.py                  runs the new scrapers live, or --sample to generate
    build_dashboard_json.py          reduces everything to src/data/dashboard.json
```

## Additional scrapers (`scrapers/`)

Two new sources extend the corpus beyond the original three platforms, each
hitting a **public, ToS-friendly, key-free API** and normalizing to the same 23
canonical brands:

- **Open Food Facts** (`openfoodfacts.py`) — the nutrition axis Amazon lacks:
  sugar + caffeine per 100 ml and a Nutri-Score per product.
- **Wikipedia** (`wikipedia.py`) — monthly pageviews as a platform-neutral
  proxy for public curiosity in each brand (a build-your-own Trends signal).

```bash
python data/scrapers/openfoodfacts.py           # -> data/openfoodfacts/products.csv
python data/scrapers/wikipedia.py               # -> data/wikipedia/*.csv
python data/scripts/run_scrapers.py             # both, one command
python data/scripts/build_dashboard_json.py     # refresh the dashboard aggregate
```

These need outbound network. In an offline/locked-down environment, generate
same-schema placeholder data instead (deterministic, zero dependencies):

```bash
python data/scripts/generate_sample_data.py                 # -> data/sample/ (full set)
python data/scripts/run_scrapers.py --sample --out data     # seed the two new sources in place
```

> The committed `openfoodfacts/` and `wikipedia/` CSVs are **generated samples**
> (see each dir's README) so the dashboard renders on a fresh checkout; replace
> them with real values by running the scrapers where network is allowed.

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
