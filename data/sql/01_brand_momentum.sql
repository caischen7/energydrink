-- 01_brand_momentum.sql — real brand momentum from POS sell-through.
--
-- Regenerates data/bq/derived/brand_momentum_real.csv.
--
-- Uses pdi_energy_drinks_monthly (13.6k rows), NOT pdi_daily_agg (1.09B rows
-- / 400GB), so this is effectively free to run. The monthly rollup already
-- has canonical_brand, so no crosswalk join is needed.
--
-- The final month in the panel is partial, so it is excluded — otherwise the
-- most recent brand would always look like it fell off a cliff. Same
-- COMPLETE_THROUGH logic as build_dashboard_json.py.

WITH bounds AS (
  SELECT MAX(month) AS last_month
  FROM `msbai-capstone-energydrinks.energy_drinks.pdi_energy_drinks_monthly`
),
scoped AS (
  SELECT m.canonical_brand AS brand, m.month, m.revenue
  FROM `msbai-capstone-energydrinks.energy_drinks.pdi_energy_drinks_monthly` m, bounds b
  WHERE m.month < b.last_month           -- drop the partial final month
),
windowed AS (
  SELECT
    brand,
    SUM(IF(month >  DATE_SUB((SELECT last_month FROM bounds), INTERVAL 12 MONTH), revenue, 0)) AS t12m,
    SUM(IF(month <= DATE_SUB((SELECT last_month FROM bounds), INTERVAL 12 MONTH)
       AND month >  DATE_SUB((SELECT last_month FROM bounds), INTERVAL 24 MONTH), revenue, 0)) AS prior_12m
  FROM scoped
  GROUP BY brand
)
SELECT
  brand,
  ROUND(t12m, 2)                                                       AS t12m_revenue,
  ROUND(prior_12m, 2)                                                  AS prior_12m_revenue,
  ROUND(100 * SAFE_DIVIDE(t12m, prior_12m) - 100, 1)                   AS yoy_pct,
  ROUND(100 * t12m      / SUM(t12m)      OVER (), 2)                   AS share_pct,
  ROUND(100 * t12m      / SUM(t12m)      OVER ()
      - 100 * prior_12m / SUM(prior_12m) OVER (), 2)                    AS share_delta_pp
FROM windowed
WHERE t12m > 2000000        -- min-n gate: ignore brands too small to read
ORDER BY share_pct DESC;
