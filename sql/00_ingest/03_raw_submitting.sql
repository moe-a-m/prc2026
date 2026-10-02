-- Verbatim load of the submission template (never filled in place).
CREATE OR REPLACE TABLE raw_submitting AS
SELECT * FROM read_parquet('data/raw/submitting/submitting.parquet');
