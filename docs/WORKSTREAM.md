# Energy-Drink Market Intelligence — Project Workstream

A working plan for the data + analytics side of the Bogus Banana project: a
free, self-run pipeline that collects competitive energy-drink market data,
turns it into analysis, and surfaces it in a dashboard to support product and
positioning decisions.

## Goal

Build a repeatable, zero-cost intelligence tool that answers, for the US energy
-drink category: **who is winning, where, why, and what consumers actually want**
— across retail (price, ratings, reviews), social (engagement, share of voice),
and paid media (ad messaging) — and feed it into a decision-ready dashboard.

## Workstream stages

### 1. Collect (self-run scrapers — free)
- **Retail:** Amazon, Walmart, Target, Trader Joe's, Publix, H-E-B, Costco,
  Whole Foods, Kroger → products, prices, list/discount, ratings, review counts,
  full review text, pack size, availability, badges, "bought since yesterday".
- **Social:** YouTube (videos + comments), TikTok (videos + engagement +
  comments), Instagram (brand posts + engagement), Reddit (r/EnergyDrinks,
  aggregates only, no PII).
- **Paid media:** Meta Ad Library (brand ad copy, CTA, platforms, campaign dates).
- One command: `run_all.py` (`--deep` for max volume, `--headless` after first
  challenge solve). Incremental merge/dedupe so re-runs extend the corpus.

### 2. Clean & normalize
- `build_clean_datasets.py` / `build_external_datasets.py` → canonical brand
  names, parsed dates/prices, tidy CSVs. External market reports
  (Statista/Catalyst market size, Mintel concept interest + motivations) folded in.

### 3. Analyze
- **Sentiment** (`analyze_sentiment.py`): pos/neg/neu by brand and by theme
  (taste, sweetness, energy, crash, price, health, packaging), 3 selectable
  models (lexicon / VADER / transformer).
- **Share of voice & momentum**: fractional attribution, music/entertainment
  noise filter, trailing-12-month mention-share trend.
- **Price × quality, flavor demand, review ratings, engagement.**

### 4. Surface
- `build_dashboard_json.py` → one ~20 KB aggregate powering the Market Intel
  dashboard (14 panels + sortable cross-platform brand table), login-gated.

### 5. Decide
- Use the above to identify white space (unmet needs, under-served price/flavor
  segments) and inform Bogus Banana's positioning, flavor lineup, price, and
  channel strategy.

## What exists today
- 10 free scrapers with offline fixture tests + a one-command runner.
- Cleaned corpora: Amazon (75 products / 552 reviews), Instagram (120 posts),
  YouTube (3,214 videos / 125,054 comments), Reddit brand pulse, market facts.
- Working dashboard reading `public/data/dashboard.json`.
- Sentiment analysis tool (3 models), example-output reference.

## Open questions / roadmap
- Fold new sources (Walmart, retailers, TikTok, Facebook ads) into the
  cross-platform `brand_summary` and dashboard panels.
- Time-series: schedule periodic scrapes to track price/sentiment/SoV over time.
- Nutrition/ingredient capture for a "clean label" analysis axis.
- Turn insights into a concrete product recommendation memo.

## Constraints & principles
- **Free only** — no paid APIs/proxies; official free APIs where they exist
  (YouTube, Kroger).
- **Run locally** — retail/social bot-walls block cloud IPs.
- **Privacy** — Reddit stored as aggregates only, no usernames.
- **Incremental & tested** — merge/dedupe, offline fixture tests per scraper.
