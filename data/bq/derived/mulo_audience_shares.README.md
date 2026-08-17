# MULO-derived audience shares

Every Mintel MULO figure this project uses, in one file. **This is a derived
aggregate, not the MULO dataset.** Mintel MULO is licensed; the raw extract is
not committed here and should not be. See `data/README.md`.

## Columns

| Column | Meaning |
| --- | --- |
| `pdi_share_pct` | Audience share of PDI convenience revenue (measured) |
| `mulo_share_pct` | Audience share of Mintel MULO brand sales (measured, top brands only) |
| `passport_share_pct` | Audience share from Euromonitor Passport, all channels |
| `published_2025_pct` | **What the site publishes** — Passport-anchored, tail allocated on PDI |
| `superseded_mulo_2025_pct` | The earlier MULO-blended estimate, kept for audit |
| `superseded_mulo_2025_usd_m` | The same, in $M against a $26,948M market |
| `superseded_mulo_2030_pct` | Earlier projection |
| `published_2030_pct` | Current projection |

## Why two sets of numbers

The site originally blended PDI convenience shares with MULO multi-outlet
shares on Mintel channel weights. That was replaced.

**MULO covers top brands only.** In a category where the female-skewing growth
is concentrated in exactly two brands — Celsius and Alani Nu — a top-brands
panel over-weights them badly. MULO puts women at **28.2%**; Euromonitor
Passport, which sees all channels and the full brand tail, puts them at
**12.1%**. The published figure is 13.2% after allocating the sub-threshold
tail on PDI proportions.

The practical size of the error: the superseded basis put women at 18.4% of
2025 demand against 13.2% published — **5.2 points, about $1.4B**.

MULO is still used as a *cross-check* on direction. It is no longer used to
set the level.

## Where the raw data lives

Not in this repo. It is in your licensed sources:

* BigQuery — the `mintel_*` tables in the project you queried earlier
  (small: 7–21 rows each, effectively free to re-query)
* The original Mintel export under your unzipped `02_Data` directory

`data/scripts/add_audiences.py` carries the reduced aggregate that the site
reads, so the pipeline runs without the licensed extract present.
