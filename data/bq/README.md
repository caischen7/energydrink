# BigQuery source — `msbai-capstone-energydrinks.energy_drinks`

The capstone BigQuery project holds **34 tables** of licensed and public
market data. This is a far stronger foundation than the scraped Amazon /
Instagram / YouTube corpus the dashboard was originally built on, because it
contains **measured sell-through** rather than social proxies.

Findings and caveats: **`docs/bigquery-findings.md`** — read that first.

## What's committed here

Only small **derived aggregates** under `derived/`:

| File | What it is |
| --- | --- |
| `derived/brand_momentum_real.csv` | Trailing-12-month POS revenue, YoY, and share change by brand |
| `derived/gnpd_claim_trends.csv` | Positioning-claim prevalence in new launches, 2018–20 vs 2024–26 |

**Raw table pulls are deliberately NOT committed.** Two reasons: this repo's
standing convention is that raw data stays out (only cleaned/derived CSVs are
tracked), and much of this is licensed third-party content (Euromonitor
Passport, Mintel GNPD/MULO) that shouldn't be redistributed in a git repo.
Everything is reproducible from `data/sql/`.

## The tables that matter

**Sell-through (PDI convenience-store POS)**
- `pdi_daily_agg` — 1.09B rows / 400GB, brand × SKU × store × day. **Always
  filter the `DATE` partition.** Dry-run before querying.
- `pdi_energy_drinks_monthly` — 13.6k rows, pre-aggregated by brand × month.
  **Use this instead** for anything brand/time-shaped; it costs ~nothing.
- `pdi_master_gtin` — SKU metadata (FLAVOR, PACK_SIZE, PRODUCT_TYPE), joins to
  the daily table on `GTIN`.
- `pdi_stores`, `pdi_stores_status` — store panel composition.

**Market share / size**
- `passport_brand_shares` — Euromonitor, USA, 2016–2025, brand share by
  `retail_value_rsp_pct` **and** `total_volume_pct`. Filter on `measure` and
  drop the `Total` / `Others` rows or shares will double-count.
- `passport_company_shares`, `passport_market_size`
- `mintel_mulo_brand_sales` — MULO retail $ and share change

**Innovation / white space**
- `gnpd_products` — Mintel GNPD, 766 real product launches 2018→2026 with
  flavours, positioning claims, launch type, pack, price. 100% coverage on
  claims and dates. This is the closest thing to a **leading indicator** in
  the dataset.

**Nutrition** (see the caveat in the findings doc)
- `usda_branded_foods` — 1,316 energy-drink SKUs. Good for sugar/calories/
  sodium/ingredients; **`caffeine_mg` is only 0.7% populated — unusable.**
- `usda_food_nutrients`

**Consumer / context**
- `mintel_*` survey tables, `simmons_brand_profiles`, `similarweb_visits_all`,
  `umich_consumer_sentiment`, `us_population_by_age`, `reference_generations`
- `brand_crosswalk` — canonical brand mapping; mirrors the `BRAND_ALIASES`
  logic in `data/scripts/build_clean_datasets.py`. Prefer this going forward.

## Re-running

Access requires membership in the capstone GCP project. A student account can
query BigQuery but generally **cannot** create service accounts, so the
practical options are running the SQL in Cloud Shell, or minting a short-lived
token with `gcloud auth application-default print-access-token`.

```bash
bq query --use_legacy_sql=false --format=csv \
  --project_id=msbai-capstone-energydrinks \
  < data/sql/01_brand_share.sql > /tmp/brand_share.csv
```

Cost note: on-demand BigQuery bills per byte scanned. `pdi_energy_drinks_monthly`
queries are effectively free; the flavor join against `pdi_daily_agg` scans
~65GB (~$0.40). Always `--dry_run` an unfamiliar query against the daily table.
