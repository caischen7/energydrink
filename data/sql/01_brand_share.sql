-- 01_brand_share.sql — real brand dollar share, price, and promo dependency.
--
-- This REPLACES data/market/brand_dollar_share.csv, which is currently a
-- cited-but-estimated midpoint across public trackers. These numbers are
-- measured sell-through instead of published estimates.
--
-- pct_units_on_promo is the column with no equivalent anywhere else in this
-- repo: it shows how much of a brand's volume only moves at a discount. A
-- brand with high share but high promo dependency is buying its shelf, which
-- is a very different competitive picture than one selling at full price.

SELECT
  BRAND,
  ROUND(SUM(TOTAL_REVENUE_AMOUNT), 2)                                       AS revenue,
  SUM(QUANTITY)                                                             AS units,
  SUM(TRANSACTION_COUNT)                                                    AS transactions,
  ROUND(100 * SUM(TOTAL_REVENUE_AMOUNT)
        / SUM(SUM(TOTAL_REVENUE_AMOUNT)) OVER (), 2)                        AS dollar_share_pct,
  ROUND(SAFE_DIVIDE(SUM(TOTAL_REVENUE_AMOUNT), SUM(QUANTITY)), 2)           AS avg_unit_price,
  ROUND(100 * SAFE_DIVIDE(SUM(QUANTITY_WITH_DISCOUNT), SUM(QUANTITY)), 1)   AS pct_units_on_promo,
  COUNT(DISTINCT GTIN)                                                      AS skus,
  COUNT(DISTINCT STORE_ID)                                                  AS stores
FROM `msbai-capstone-energydrinks.energy_drinks.pdi_daily_agg`
GROUP BY BRAND
ORDER BY revenue DESC;
