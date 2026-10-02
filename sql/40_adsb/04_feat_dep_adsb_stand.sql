-- requires-glob: data/external/adsblol/extract/*.parquet
-- Off-block from the aircraft leaving its own stand (M-021): the departure's APDF stand code → OSM parking_position
-- coordinates (stg_stand_geo); points of the matched ADS-B ground segment within STAND_R_M of that position are
-- "at stand". Off-block estimate = first moving point (gs ≥ 1 kt) while at stand; if the aircraft is never seen
-- stationary at the stand, the first at-stand observation (a lower bound on taxi-out).
-- Idea credited to the push-back detection of the `traffic` library (X. Olive, MIT), which combines a documented
-- parking position with the start of movement; this is an independent SQL implementation.
CREATE OR REPLACE TABLE feat_dep_adsb_stand AS
WITH m AS (  -- matched take-offs with a ground segment (same one-to-one match as feat_dep_adsb)
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
    min(d_stand_m)                                                       AS adsb_min_d_stand_m,
    arg_min(d_stand_m, t)                                                AS adsb_first_d_stand_m,
    bool_or(d_stand_m <= 60)                                             AS adsb_seen_at_stand,
    epoch(any_value(t_mvt)) - epoch(min(t) FILTER (WHERE d_stand_m <= 60 AND gs >= 1)) AS adsb_stand_move_s,
    epoch(any_value(t_mvt)) - epoch(min(t) FILTER (WHERE d_stand_m <= 60))              AS adsb_stand_first_s,
    bool_or(d_stand_m <= 60 AND gs < 1)                                  AS adsb_still_at_stand
FROM p GROUP BY mvt_id;
