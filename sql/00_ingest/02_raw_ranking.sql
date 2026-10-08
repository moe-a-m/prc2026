-- Verbatim load of the final-phase ranking set (Jan, Feb, Jun, Jul 2026; DEP block/taxi blanked by the organizers).
-- It contains every row of the public-phase ranking.parquet (Jan + Jul), with re-perturbed take-off times
-- (reports/checks/final_phase_files.md).
CREATE OR REPLACE TABLE raw_ranking AS
SELECT *, regexp_extract(filename, '[^/]+$') AS src_file
FROM read_parquet('data/raw/ranking/final_ranking.parquet', filename = true);
