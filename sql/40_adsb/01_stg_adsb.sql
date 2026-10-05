-- requires-glob: data/external/adsblol/extract/*.parquet
-- adsb.lol airport-surface points (docs/data_sources/adsblol.md), one row per (icao24, ts); UTC timestamps.
CREATE OR REPLACE TABLE stg_adsb AS
-- duplicate (icao24, ts) points (overlapping receivers/legs): deterministic aggregates (min/max), never any_value
SELECT airport, icao24, max(reg) AS reg, max(actype) AS actype, max(callsign) AS callsign,
       to_timestamp(ts)::TIMESTAMPTZ AT TIME ZONE 'UTC' AS t, min(lat) AS lat, min(lon) AS lon,
       min(alt_ft) AS alt_ft, bool_or(on_ground) AS on_ground, min(gs_kt) AS gs_kt
FROM read_parquet('data/external/adsblol/extract/*.parquet')
GROUP BY airport, icao24, ts;
