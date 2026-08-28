-- Step 0 (discovery): print the schema of the PDI panel.
-- INFORMATION_SCHEMA reads are metadata-only -> 0 bytes billed, $0.
-- Replace <PROJECT> with the GCP project that owns the `energy_drinks` dataset.
--
-- Run all four, paste the output back into the Claude session, and the real
-- Step 1 aggregation can be written against actual column names instead of
-- guesses. Nothing here touches the 1.69B data rows.

-- 1. Columns of pdi_daily_agg: names, types, and which column is the partition key.
SELECT
  ordinal_position,
  column_name,
  data_type,
  is_nullable,
  is_partitioning_column,
  clustering_ordinal_position
FROM `<PROJECT>.energy_drinks.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'pdi_daily_agg'
ORDER BY ordinal_position;

-- 2. Table options: confirms whether a partition filter is REQUIRED.
--    If require_partition_filter = true, any query without a filter on the
--    partition column errors out instead of silently full-scanning.
SELECT option_name, value
FROM `<PROJECT>.energy_drinks.INFORMATION_SCHEMA.TABLE_OPTIONS`
WHERE table_name = 'pdi_daily_agg';

-- 3. Physical size + row count, to sanity-check the 1.69B figure and
--    estimate what a full scan would actually cost.
SELECT
  table_name,
  row_count,
  ROUND(size_bytes / POW(1024, 3), 1) AS size_gib,
  ROUND(size_bytes / POW(1024, 4) * 6.25, 2) AS full_scan_usd_est
FROM `<PROJECT>.energy_drinks.__TABLES__`
WHERE table_id = 'pdi_daily_agg';

-- 4. Partition coverage: confirms the real date range and shows how thin
--    2018 and how partial 2026 actually are (the task assumes we exclude both).
SELECT
  SUBSTR(partition_id, 1, 4) AS year,
  COUNT(*)                   AS partitions,
  SUM(total_rows)            AS rows
FROM `<PROJECT>.energy_drinks.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'pdi_daily_agg'
  AND partition_id NOT IN ('__NULL__', '__UNPARTITIONED__')
GROUP BY year
ORDER BY year;

-- Every other table in the dataset, in case the panel is split or there is a
-- product-dimension table that makes the pdi_unique_products.csv join unnecessary.
SELECT table_name, table_type
FROM `<PROJECT>.energy_drinks.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name;
