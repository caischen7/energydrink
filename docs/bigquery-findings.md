# BigQuery findings — what the licensed data says

First pass over `msbai-capstone-energydrinks.energy_drinks` (34 tables). This
is the first time this project has touched **measured sell-through** rather
than scraped social proxies, and the two disagree in ways that matter.

## The headline: our momentum signal is directionally wrong

The dashboard's "Brand Momentum" and "Who's Moving" panels rank brands by
**share of YouTube mentions**. Rebuilt from PDI point-of-sale revenue
(trailing 12 months, 2025-07 → 2026-06, vs the prior 12):

| Brand | T12M revenue | YoY | Share | Share Δ |
| --- | ---: | ---: | ---: | ---: |
| Red Bull | $520.9M | +2.6% | 37.9% | **−1.47pp** |
| Monster | $394.8M | +9.7% | 28.7% | +0.80pp |
| Celsius | $101.2M | +8.3% | 7.4% | +0.11pp |
| **Alani Nu** | $78.9M | **+95.8%** | 5.7% | **+2.62pp** |
| Reign | $24.3M | −16.7% | 1.8% | −0.50pp |
| **Bang** | $21.9M | **−15.6%** | 1.6% | −0.42pp |

Category in this panel grew **+6.6%**.

**Bang is listed as a top riser on the current dashboard (+4.0pp mention
share). Its actual sales fell 15.6% and it lost share.** Mention volume was
tracking a brand being *talked about* — including its bankruptcy/acquisition
news cycle — not one being *bought*. This is the strongest argument for
migrating the momentum panels onto POS data.

**Alani Nu is the real breakout** (+95.8% POS, +84.2% in Mintel MULO) and is
nearly invisible in our scraped corpus. We would have missed the single most
important brand story in the category.

**Red Bull is #1 and shrinking in relative terms** — growing +2.6% in a
category growing +6.6% means it loses ~1.5pp of share per year.

## Where the white space actually is

From Mintel GNPD (766 real product launches, 2018→2026), comparing claim
prevalence in 2018–20 (n=198) vs 2024–26 (n=303):

| Positioning claim | 2018–20 | 2024–26 | Δ |
| --- | ---: | ---: | ---: |
| Functional — Brain & Nervous System | 25.8% | **53.8%** | +28.0pp |
| Sugar Free | 48.5% | **72.3%** | +23.8pp |
| Vegan / No Animal Ingredients | 15.7% | 30.7% | +15.0pp |
| Nails & Hair | 0.0% | 10.6% | +10.6pp |
| Functional — Skin | 0.0% | 10.6% | +10.6pp |
| Functional — Immune System | 0.5% | 9.2% | +8.7pp |

Two conclusions that change the product recommendation:

1. **"Sugar-free + high caffeine" is no longer white space — it's the norm.**
   72% of new launches claim sugar-free. The overnight Formulation Map called
   this an open corner; at launch-pipeline level it is now table stakes.
2. **Cognitive/nootropic is the defining trend** (+28pp, now in the majority
   of launches), and **beauty-functional (hair/nails/skin) went 0% → 10.6%**
   — that is a genuinely new segment forming. Notably it is exactly Alani Nu's
   positioning, and Alani Nu is the fastest-growing brand in the POS data.
   Two independent sources corroborating the same story is the strongest
   signal in this dataset.

## Brand share, properly sourced

`data/market/brand_dollar_share.csv` was hand-assembled from public reporting
as a cited midpoint. Euromonitor Passport (`passport_brand_shares`, 2016–2025,
retail value **and** volume) now supersedes it. The estimates held up
reasonably — Monster 35% guessed vs 38.2% actual retail-value 2025, Red Bull
32% vs 34.5%, Celsius 10% vs 10.6% — but the real table has ten years of
history and two measures, so the guessed file should be retired.

## Data-quality caveats (important — do not skip)

- **USDA caffeine is unusable**: `caffeine_mg` is populated on **0.7%** of the
  1,316 energy-drink SKUs (9 rows). USDA is excellent for sugar (90%),
  calories (96%), sodium and ingredients, but the hand-curated
  `data/nutrition/brand_nutrition.csv` remains the better caffeine source.
  GNPD only fills caffeine on 13.8% of launches. **No source here supports a
  caffeine-vs-sugar map at scale** — the current Formulation Map's 15 curated
  brands are still the honest basis for it.
- **`pdi_daily_agg` is 1.09B rows / 400GB.** Always filter the `DATE`
  partition. The pre-aggregated `pdi_energy_drinks_monthly` (13.6k rows)
  answers most brand/time questions for ~0 cost. The flavor join used here
  scanned 65GB (~$0.40); dry-run before repeating it.
- The PDI panel is convenience-store weighted, so it under-represents club and
  e-commerce. Its Red Bull/Monster split (37.9/28.7) differs from Passport's
  national retail-value split (34.5/38.2) for that reason — **these are
  different universes and should not be presented as the same metric.**
- `passport_brand_shares` contains both `retail_value_rsp_pct` and
  `total_volume_pct`, plus `Total`/`Others` rows. Filter on `measure` and
  exclude aggregate rows or shares will appear to double-count.

## Recommended next steps

1. Repoint **Brand Momentum**, **Who's Moving**, and **Competitive $ Share**
   at POS/Passport data. Keep the social panels, but reframe them explicitly
   as *attention*, not demand — the Bang case is a good on-dashboard example
   of why the two differ.
2. Add a **Launch Pipeline** panel from GNPD claim trends — this is the
   closest thing in the dataset to a true leading indicator.
3. Revisit the product recommendation: the overnight "high-caffeine,
   zero-sugar" thesis is now contradicted by the launch data. Cognitive +
   beauty-functional is where the category is actually moving.

Queries are in `data/sql/`. Raw pulls are **not** committed (licensed
Euromonitor/Mintel content, and per repo convention raw data stays out);
`data/bq/derived/` holds the small aggregates behind the tables above.
