-- requires-glob: data/external/adsblol/extract/*.parquet
-- ADS-B off-block observations as model inputs (M-034). Movement-based estimates only (take-off − observed off-block,
-- seconds); reception-dependent quantities (first ground observation, points, gaps, taxi distance) are left out because
-- they drift with the receiver network (reports/checks/m034_adsb_feature_drift.md). Missing = no usable observation.
--   ax_stand_still : first movement at the own OSM stand after being stationary there (M-021, source 'still')
--   ax_stand_moving: first sighting within 60 m of the stand, never stationary there (M-028 source 'moving')
--   ax_near        : same within 150 m (M-028 source 'near', sql/40_adsb/05)
--   ax_parked      : first movement when the ground segment starts parked (M-018), no stand geometry needed
--   ax_best        : first available of the four, in that order; ax_best_minus_nm = ax_best − d_aobt3
CREATE OR REPLACE TABLE feat_dep_adsb_inputs AS
WITH e AS (
    SELECT f.mvt_id, f.d_aobt3,
        CASE WHEN s.adsb_still_at_stand THEN s.adsb_stand_move_s END                                     AS ax_stand_still,
        CASE WHEN s.adsb_seen_at_stand AND NOT s.adsb_still_at_stand THEN s.adsb_stand_first_s END       AS ax_stand_moving,
        CASE WHEN n.adsb_seen_near_stand THEN n.adsb_near_s END                                          AS ax_near,
        CASE WHEN a.adsb_seen_parked THEN a.adsb_first_move_s END                                        AS ax_parked
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id)
    LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    LEFT JOIN feat_dep_adsb_near n USING (mvt_id)
)
SELECT mvt_id, ax_stand_still, ax_stand_moving, ax_near, ax_parked,
    coalesce(ax_stand_still, ax_stand_moving, ax_near, ax_parked)             AS ax_best,
    coalesce(ax_stand_still, ax_stand_moving, ax_near, ax_parked) - d_aobt3   AS ax_best_minus_nm
FROM e;
