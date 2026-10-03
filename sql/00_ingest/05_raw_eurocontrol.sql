-- requires-glob: data/external/eurocontrol_apt/raw/*.csv
-- Verbatim loads of EUROCONTROL AIU airport files (docs/data_sources/eurocontrol_apt.md). Files are not modified.
CREATE OR REPLACE TABLE raw_ec_taxi AS
SELECT *, regexp_extract(filename, '[^/]+$') AS src_file
FROM read_csv('data/external/eurocontrol_apt/raw/taxi_out_additional_time_*.csv', filename = true, union_by_name = true);
CREATE OR REPLACE TABLE raw_ec_predep AS
SELECT *, regexp_extract(filename, '[^/]+$') AS src_file
FROM read_csv('data/external/eurocontrol_apt/raw/all_pre_departure_delays_*.csv', filename = true, union_by_name = true);
CREATE OR REPLACE TABLE raw_ec_slot AS
SELECT *, regexp_extract(filename, '[^/]+$') AS src_file
FROM read_csv('data/external/eurocontrol_apt/raw/atfm_slot_adherence_*.csv', filename = true, union_by_name = true);
