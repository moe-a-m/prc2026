-- requires-glob: data/external/ourairports/raw/runways.csv
-- Verbatim OurAirports tables (public domain; docs/data_sources/ourairports.md).
CREATE OR REPLACE TABLE raw_oa_airports AS SELECT * FROM read_csv('data/external/ourairports/raw/airports.csv');
CREATE OR REPLACE TABLE raw_oa_runways AS SELECT * FROM read_csv('data/external/ourairports/raw/runways.csv');
