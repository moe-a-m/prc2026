-- requires-glob: data/external/iem_metar/raw/*.csv
-- Verbatim load of IEM ASOS/METAR downloads (all columns as text; docs/data_sources/iem_metar.md).
CREATE OR REPLACE TABLE raw_metar AS
SELECT *, regexp_extract(filename, '[^/]+$') AS src_file
FROM read_csv('data/external/iem_metar/raw/*.csv', all_varchar = true, header = true, filename = true);
