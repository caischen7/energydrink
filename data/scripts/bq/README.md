# PDI sales panel → predictive model

> **This work has moved to `ayounker/msbai-capstone-energydrinks` (private).**
> Nothing further should be attempted from this repo. See "Why it moved" below.

Working notes kept here for the one artifact that stayed:
`00_discover_schema.sql`.

## Why this exists

The predictive-modeling track stalls on granularity: the committed PDI panel is
GTIN × YEAR, which leaves ~7 annual points per flavor — far too few to fit or
validate a forecast. Aggregating `pdi_daily_agg` to **flavor_family × MONTH**
over 2019-01 → 2025-12 turns ~91 annual rows into ~1,000 monthly panel rows
(~84 months × 13 families), which can support a regression and a rolling-origin
backtest. 2018 is excluded (coverage too thin — ~$38M vs $395M in 2019) and
2026 is excluded (partial scrape).

## Why it moved

Everything the model needs lives in the capstone repo, not here:

| Needed | Location |
| --- | --- |
| `classify_target_consumers.py` (`FLAVOR_FAMILIES` taxonomy) | capstone repo |
| `pdi_unique_products.csv` (~2,309 labeled GTINs) | capstone repo |
| `trends_model.py`, `data/trends/` | capstone repo |
| GCP credentials for BigQuery `energy_drinks` | capstone repo (encrypted, via cloud-bootstrap) |

None of these have ever existed in `caischen7/energydrink` — verified across all
branches with `git log --all --diff-filter=A --name-only`. The capstone repo
also cannot be attached to a session already sourcing this one (`add_repo`
rejects cross-owner adds), so the work needs a session sourced from it directly.

There is also a licensing reason: **this repo is public.** Licensed PDI data and
its aggregates must not land here. The capstone repo is private and is the
correct home. Scaffolding may travel out of this repo; no PDI comes back in.

## What's still here

`00_discover_schema.sql` — metadata-only ($0, bills 0 bytes). Returns
`pdi_daily_agg`'s column names and types, whether `require_partition_filter` is
set, table size with a full-scan cost estimate, per-year partition coverage (to
verify the 2018/2026 exclusions), and the dataset's other tables. Kept as a
reference copy; the working copy now lives in the capstone repo.

## Rules that travel with the work

- Never `SELECT *` against `pdi_daily_agg` (1.69B rows).
- Always filter on the partition column; always dry-run and check bytes billed
  before a real run. A full scan is ~$0.35–0.55.
- Time-based validation only — never random k-fold on a time series.
- A model that doesn't beat persistence and seasonal-naive baselines is a
  finding, not a failure to hide.
- Licensed raw PDI data stays out of git. Aggregates only.
