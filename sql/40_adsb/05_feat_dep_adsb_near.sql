-- requires-glob: data/external/adsblol/extract/*.parquet
-- Near-stand variant of M-021 (EXP-080): same matched ground segment and OSM stand position as feat_dep_adsb_stand,
-- radius 150 m instead of 60 m. reports/checks/p4_adsblol_stand_gap.md: 10% of departures with a ground segment come
-- within 60–150 m of their OSM stand but never within 60 m. Off-block estimate = first moving point (gs ≥ 1 kt)
-- within 150 m when the aircraft was stationary there, else the first observation within 150 m.
CREATE OR REPLACE TABLE feat_dep_adsb_near AS
WITH m AS (
    SELECT a.mvt_id, f.airport, f.stand, timezone('UTC', to_timestamp(f.t_mvt_epoch)) AS t_mvt, e.icao24, e.ground_seg
    FROM feat_dep_adsb a JOIN feat_dep f USING (mvt_id)
    JOIN adsb_takeoff e ON e.airport = f.airport AND a.adsb_has_ground
     AND abs(epoch(e.t_air0) - f.t_mvt_epoch - a.adsb_dt_takeoff_s) < 0.001
),
p AS (
    SELECT m.mvt_id, m.t_mvt, s.t, coalesce(s.gs_kt, 0) AS gs,
           ST_Distance_Sphere(ST_Point(s.lat, s.lon), ST_Point(g.lat, g.lon)) AS d_stand_m
    FROM m JOIN adsb_seg s ON s.icao24 = m.icao24 AND s.airport = m.airport AND s.seg = m.ground_seg
    JOIN stg_stand_geo g ON g.airport = m.airport AND g.stand = m.stand
)
SELECT mvt_id,
    bool_or(d_stand_m <= 150)                                                            AS adsb_seen_near_stand,
    bool_or(d_stand_m <= 150 AND gs < 1)                                                 AS adsb_still_near_stand,
    epoch(any_value(t_mvt)) - CASE WHEN bool_or(d_stand_m <= 150 AND gs < 1)
        THEN epoch(min(t) FILTER (WHERE d_stand_m <= 150 AND gs >= 1))
        ELSE epoch(min(t) FILTER (WHERE d_stand_m <= 150)) END                           AS adsb_near_s
FROM p GROUP BY mvt_id;
