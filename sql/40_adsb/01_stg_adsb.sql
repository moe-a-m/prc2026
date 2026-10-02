-- requires-glob: data/external/adsblol/extract/*.parquet
-- adsb.lol airport-surface points (docs/data_sources/adsblol.md), one row per (icao24, ts); UTC timestamps.
CREATE OR REPLACE TABLE stg_adsb AS
SELECT airport, icao24, any_value(reg) AS reg, any_value(actype) AS actype, any_value(callsign) AS callsign,
       to_timestamp(ts)::TIMESTAMPTZ AT TIME ZONE 'UTC' AS t, any_value(lat) AS lat, any_value(lon) AS lon,
       any_value(alt_ft) AS alt_ft, bool_or(on_ground) AS on_ground, any_value(gs_kt) AS gs_kt
FROM read_parquet('data/external/adsblol/extract/*.parquet')
GROUP BY airport, icao24, ts;
