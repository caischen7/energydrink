-- 01_brand_momentum.sql — real brand momentum from POS sell-through.
--
-- Regenerates data/bq/derived/brand_momentum_real.csv. Verified to match it
-- exactly.
--
-- Uses pdi_energy_drinks_monthly (13.6k rows), NOT pdi_daily_agg (1.09B rows
-- / 400GB), so this is effectively free to run. The monthly rollup already
-- has canonical_brand, so no crosswalk join is needed.
--
-- Two things this query is fussy about, both of which produced wrong numbers
-- in an earlier draft:
--
--   1. The final month in the panel is PARTIAL. The window is anchored on the
--      last *complete* month (MAX(month) - 1) — same COMPLETE_THROUGH logic as
--      build_dashboard_json.py. Anchoring on MAX(month) and using a strict >
--      yields an 11-month window compared against a 12-month one, which
--      understates every brand (Red Bull read -8.3% instead of +2.6%).
--      Bounds are inclusive on both ends: >= anchor-11mo AND <= anchor.
--
--   2. Share is computed against the WHOLE category, not just the brands that
--      survive the min-n filter. Filtering first inflates every share.

WITH bounds AS (
  SELECT DATE_SUB(MAX(month), INTERVAL 1 MONTH) AS anchor    -- last complete month
  FROM `msbai-capstone-energydrinks.energy_drinks.pdi_energy_drinks_monthly`
),
windowed AS (
  SELECT
    m.canonical_brand AS brand,
    SUM(IF(m.month >= DATE_SUB(b.anchor, INTERVAL 11 MONTH)
       AND m.month <= b.anchor, m.revenue, 0))                          AS t12m,
    SUM(IF(m.month >= DATE_SUB(b.anchor, INTERVAL 23 MONTH)
       AND m.month <= DATE_SUB(b.anchor, INTERVAL 12 MONTH), m.revenue, 0)) AS prior_12m
  FROM `msbai-capstone-energydrinks.energy_drinks.pdi_energy_drinks_monthly` m, bounds b
  GROUP BY brand
),
totals AS (                    -- denominator spans ALL brands, pre-filter
  SELECT SUM(t12m) AS tot_now, SUM(prior_12m) AS tot_prev FROM windowed
)
SELECT
  w.brand,
  ROUND(w.t12m, 2)                                        AS t12m_revenue,
  ROUND(w.prior_12m, 2)                                   AS prior_12m_revenue,
  ROUND(100 * SAFE_DIVIDE(w.t12m, w.prior_12m) - 100, 1)  AS yoy_pct,
  ROUND(100 * w.t12m / t.tot_now, 2)                      AS share_pct,
  ROUND(100 * w.t12m / t.tot_now
      - 100 * w.prior_12m / t.tot_prev, 2)                AS share_delta_pp
FROM windowed w, totals t
WHERE w.t12m > 2000000        -- min-n gate: ignore brands too small to read
ORDER BY share_pct DESC;
