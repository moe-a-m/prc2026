-- requires-glob: data/external/adsblol/extract/*.parquet
-- Match departures to ADS-B take-offs and describe the taxi segment (M-018).
-- Match: same airport, |t_air0 − t_mvt| ≤ 180 s; preference = callsign agreement, then smallest |Δt|;
-- one-to-one (best departure per event and best event per departure).
-- Taxi description on the matched ground segment ("how it moved", a participant 27/09: transfers across years):
--   stationary runs = consecutive points with gs < 1 kt; stand stop = longest run ≥ 120 s (kept, but a poor off-block
--   estimate: reports/checks/p4_adsb_vs_target_2025-01-01.md);
--   seen parked = segment starts with ≥ 60 s stationary; first movement = first point with gs ≥ 1 kt — the off-block
--   estimate (reports/checks/p4_adsb_offblock_variants_2025-01-01.md: 72% within 60 s of the target when seen parked).
CREATE OR REPLACE TABLE feat_dep_adsb AS
WITH dep AS (
    SELECT f.mvt_id, f.airport, timezone('UTC', to_timestamp(f.t_mvt_epoch)) AS t_mvt, m.callsign
    FROM feat_dep f JOIN stg_mvt m USING (mvt_id)
    WHERE f.month IN (SELECT DISTINCT date_trunc('month', t)::DATE FROM stg_adsb)
),
cand AS (
    SELECT d.mvt_id, e.*, epoch(e.t_air0) - epoch(d.t_mvt) AS dt,
           (d.callsign IS NOT NULL AND (d.callsign = e.cs_air OR d.callsign = e.cs_ground)) AS cs_match
    FROM dep d JOIN adsb_takeoff e
      ON e.airport = d.airport AND e.t_air0 BETWEEN d.t_mvt - INTERVAL 180 SECOND AND d.t_mvt + INTERVAL 180 SECOND
),
r AS (
    SELECT *, row_number() OVER (PARTITION BY mvt_id ORDER BY cs_match DESC, abs(dt), icao24, air_seg) AS r_dep,
              row_number() OVER (PARTITION BY icao24, airport, air_seg ORDER BY cs_match DESC, abs(dt), mvt_id) AS r_ev  -- unique tie-breaks
    FROM cand
),
m AS (SELECT * FROM r WHERE r_dep = 1 AND r_ev = 1),
pts AS (  -- points of matched ground segments, with stationary-run ids
    SELECT m.mvt_id, s.t, s.lat, s.lon, s.gs_kt, (coalesce(s.gs_kt, 0) < 1) AS still,
           lag(s.lat) OVER w AS lat_p, lag(s.lon) OVER w AS lon_p, epoch(s.t) - epoch(lag(s.t) OVER w) AS dt_p
    FROM m JOIN adsb_seg s ON s.icao24 = m.icao24 AND s.airport = m.airport AND s.seg = m.ground_seg
    WINDOW w AS (PARTITION BY m.mvt_id ORDER BY s.t)
),
runs AS (
    SELECT *, sum(chg) OVER (PARTITION BY mvt_id ORDER BY t ROWS UNBOUNDED PRECEDING) AS run_id
    FROM (SELECT *, (still IS DISTINCT FROM lag(still) OVER (PARTITION BY mvt_id ORDER BY t))::INT AS chg FROM pts)
),
stops AS (
    SELECT mvt_id, run_id, min(t) AS s0, max(t) AS s1, epoch(max(t)) - epoch(min(t)) AS dur
    FROM runs WHERE still GROUP BY ALL
),
stand AS (
    SELECT mvt_id, max(s1) FILTER (WHERE dur = longest) AS t_stand_end, max(dur) AS stand_stop_s  -- latest of tied longest stops
    FROM (SELECT *, max(dur) OVER (PARTITION BY mvt_id) AS longest FROM stops WHERE dur >= 120) GROUP BY mvt_id
),
agg AS (
    SELECT p.mvt_id, min(p.t) AS t_seg0, count(*) AS n_pts, max(p.dt_p) AS max_gap_s,
           min(p.t) FILTER (WHERE NOT p.still) AS t_first_move, arg_min(p.still, p.t) AS first_still
    FROM pts p GROUP BY p.mvt_id
),
after AS (  -- movement after the stand stop: distance, holds
    SELECT p.mvt_id,
           sum(CASE WHEN p.lat_p IS NOT NULL THEN ST_Distance_Sphere(ST_Point(p.lat_p, p.lon_p), ST_Point(p.lat, p.lon)) END) AS taxi_dist_m,
           sum(CASE WHEN p.still THEN p.dt_p ELSE 0 END) AS hold_s
    FROM pts p LEFT JOIN stand st USING (mvt_id)
    WHERE st.t_stand_end IS NULL OR p.t > st.t_stand_end
    GROUP BY p.mvt_id
)
SELECT d.mvt_id,
    m.mvt_id IS NOT NULL                                   AS adsb_matched,
    m.cs_match                                             AS adsb_cs_match,
    m.dt                                                   AS adsb_dt_takeoff_s,
    m.ground_seg IS NOT NULL                               AS adsb_has_ground,
    epoch(d.t_mvt) - epoch(a.t_seg0)                       AS adsb_first_ground_s,
    a.first_still AND epoch(a.t_first_move) - epoch(a.t_seg0) >= 60 AS adsb_seen_parked,
    epoch(d.t_mvt) - epoch(a.t_first_move)                 AS adsb_first_move_s,
    CASE WHEN a.first_still THEN epoch(a.t_first_move) - epoch(a.t_seg0) END AS adsb_parked_s,
    epoch(d.t_mvt) - epoch(st.t_stand_end)                 AS adsb_stand_end_s,
    st.stand_stop_s                                        AS adsb_stand_stop_s,
    a.n_pts                                                AS adsb_n_pts,
    a.max_gap_s                                            AS adsb_max_gap_s,
    af.taxi_dist_m                                         AS adsb_taxi_dist_m,
    af.hold_s                                              AS adsb_hold_s
FROM dep d
LEFT JOIN m USING (mvt_id)
LEFT JOIN agg a USING (mvt_id)
LEFT JOIN stand st USING (mvt_id)
LEFT JOIN after af USING (mvt_id);
