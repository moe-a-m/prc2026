-- Verbatim load of the ranking set (Jan + Jul 2026; DEP block/taxi blanked by the organizers).
CREATE OR REPLACE TABLE raw_ranking AS
SELECT *, regexp_extract(filename, '[^/]+$') AS src_file
FROM read_parquet('data/raw/ranking/ranking.parquet', filename = true);
