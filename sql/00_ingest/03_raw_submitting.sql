-- Verbatim load of the final-phase submission template (never filled in place).
CREATE OR REPLACE TABLE raw_submitting AS
SELECT * FROM read_parquet('data/raw/submitting/final_submitting.parquet');
