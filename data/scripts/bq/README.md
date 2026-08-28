# PDI sales panel → predictive model

Working notes for the SALES-as-dependent-variable modeling track. This
directory holds the BigQuery side; the modeling scripts land next to it once
the panel exists.

## Why this exists

The descriptive work stalls on granularity: the committed PDI panel is
GTIN × YEAR, which leaves ~7 annual points per flavor — far too few to fit or
validate a forecast. Fixing the sales side comes first. Aggregating
`pdi_daily_agg` to **flavor_family × MONTH** over 2019-01 → 2025-12 turns ~91
annual rows into ~1,000 monthly panel rows (~84 months × 13 families), which is
enough to support the regression and a rolling-origin backtest.

2018 is excluded (PDI coverage is too thin — ~$38M vs $395M in 2019) and 2026
is excluded (partial scrape).

## Status: BLOCKED on schema

Nothing here has been run. This session has no BigQuery credentials, and by
decision the credential stays out of the repo entirely — **you run the
queries, commit the aggregate.** (`caischen7/energydrink` is a public repo, so
committing even an encrypted service-account key was ruled out.)

Two prerequisites are also unreachable from this session:

| Needed | Where it lives | Status |
| --- | --- | --- |
| `pdi_daily_agg` schema | BigQuery `energy_drinks` | not yet inspected — run `00_discover_schema.sql` |
| `classify_target_consumers.py` (`FLAVOR_FAMILIES` taxonomy) | `ayounker/msbai-capstone-energydrinks` | unreachable — see below |
| `pdi_unique_products.csv` (~2,309 labeled GTINs) | same | unreachable |
| `trends_model.py`, `data/trends/README.md` | same | unreachable |

The capstone repo cannot be attached to a session that already sources
`caischen7/energydrink` — `add_repo` rejects cross-owner adds, and the GitHub
API is scoped to the session's initial repo. Fix: start a session with
`ayounker/msbai-capstone-energydrinks` as the initial source, or copy the four
files across.

## Sequence

1. **`00_discover_schema.sql`** — run first. Metadata-only, $0. Returns column
   names/types, whether a partition filter is required, table size, per-year
   partition coverage, and the dataset's other tables. Paste the output back.
2. **`01_monthly_panel.sql`** — not yet written; needs step 1's column names.
   Will aggregate to flavor_family × month and flavor_family × audience × month,
   with a partition filter on the date column. **Dry-run first**
   (`bq query --dry_run`) and confirm bytes billed drops well below a full scan
   before running for real — a full scan of this table is ~$0.35–0.55.
3. Save the reduced panel locally as CSV. The aggregate is safe to commit;
   licensed row-level PDI data is not.
4. Modeling (log-linear OLS → gradient-boosting benchmark), scored with
   rolling-origin validation against persistence and seasonal-naive baselines.

## Rules carried over

- Never `SELECT *` against `pdi_daily_agg`.
- Always filter on the partition column; always dry-run first.
- Time-based validation only — never random k-fold on a time series.
- A model that doesn't beat both baselines is a finding, not a failure to hide.
- Licensed raw PDI data stays out of the repo.
