-- Verbatim load of the 12 monthly training files. Adds provenance columns only.
CREATE OR REPLACE TABLE raw_training AS
SELECT
    *,
    regexp_extract(filename, '[^/]+$') AS src_file,
    CAST(regexp_extract(filename, 'training_(\d{4}-\d{2})-01_', 1) || '-01' AS DATE) AS src_month
FROM read_parquet('data/raw/training/training_*.parquet', filename = true);
