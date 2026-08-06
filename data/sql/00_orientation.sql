-- 00_orientation.sql — RUN THIS FIRST.
--
-- Establishes the shape of the PDI point-of-sale table before we build
-- anything on top of it: how far back the data goes, what grain it is, how
-- many brands/SKUs/stores it covers, and the total money involved.
--
-- Everything else in this directory is scoped from these answers, so paste
-- the output back before running the rest.
--
-- Cost note: this scans a handful of columns across all partitions. It is the
-- one query here without a DATE filter, because establishing the date range is
-- the entire point. If the table turns out to be very large, add a
-- `WHERE DATE >= '2024-01-01'` and rerun.

SELECT
  COUNT(*)                                   AS row_count,
  MIN(DATE)                                  AS first_date,
  MAX(DATE)                                  AS last_date,
  COUNT(DISTINCT BRAND)                      AS brands,
  COUNT(DISTINCT MANUFACTURER)               AS manufacturers,
  COUNT(DISTINCT GTIN)                       AS skus,
  COUNT(DISTINCT STORE_ID)                   AS stores,
  COUNT(DISTINCT CATEGORY)                   AS categories,
  COUNT(DISTINCT SUBCATEGORY)                AS subcategories,
  ROUND(SUM(TOTAL_REVENUE_AMOUNT), 2)        AS total_revenue,
  SUM(QUANTITY)                              AS total_units,
  SUM(TRANSACTION_COUNT)                     AS total_transactions
FROM `msbai-capstone-energydrinks.energy_drinks.pdi_daily_agg`;
