-- requires-glob: data/external/adsblol/extract/*.parquet
-- Take-off events per aircraft and airport (M-018). Segments: consecutive points of one icao24 at one airport with
-- the same ground/airborne state and no gap > 20 min. A take-off = an airborne segment that starts ≤ 1500 ft above
-- the field (barometric altitude − OurAirports elevation) and climbs ≥ 300 ft; its preceding ground segment (if
-- adjacent, ≤ 180 s earlier) is the taxi segment.
CREATE OR REPLACE TABLE adsb_seg AS
WITH p AS (
    SELECT *, lag(t) OVER w AS t_prev, lag(on_ground) OVER w AS g_prev
    FROM stg_adsb WINDOW w AS (PARTITION BY icao24, airport ORDER BY t)
), b AS (
    SELECT *, (t_prev IS NULL OR epoch(t) - epoch(t_prev) > 1200 OR on_ground IS DISTINCT FROM g_prev)::INT AS brk FROM p
)
SELECT *, sum(brk) OVER (PARTITION BY icao24, airport ORDER BY t ROWS UNBOUNDED PRECEDING) AS seg FROM b;

CREATE OR REPLACE TABLE adsb_takeoff AS
WITH s AS (
    SELECT icao24, airport, seg, bool_and(on_ground) AS g, min(t) AS t0, max(t) AS t1, count(*) AS n,
           arg_min(alt_ft, t) AS alt_first, max(alt_ft) AS alt_max, max(callsign) AS cs,
           max(epoch(t) - epoch(t_prev)) FILTER (WHERE brk = 0) AS max_gap_s
    FROM adsb_seg GROUP BY ALL
)
SELECT a.icao24, a.airport, a.seg AS air_seg, a.t0 AS t_air0, a.alt_first, a.cs AS cs_air,
       CASE WHEN g.g AND epoch(a.t0) - epoch(g.t1) <= 180 THEN g.seg END AS ground_seg,
       CASE WHEN g.g AND epoch(a.t0) - epoch(g.t1) <= 180 THEN g.cs END AS cs_ground
FROM s a LEFT JOIN s g ON g.icao24 = a.icao24 AND g.airport = a.airport AND g.seg = a.seg - 1
JOIN ref_airport_geo r ON r.airport = a.airport
WHERE NOT a.g AND a.alt_first - r.elev_ft <= 1500 AND a.alt_max - a.alt_first >= 300;
