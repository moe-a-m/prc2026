"""M-034 evidence: do ADS-B movement observations carry information the NM proxy lacks, and do they transfer to 2026?

1. On 2025 matched departures (y ≤ 3 h) with an ADS-B ground segment, by NM-vs-airport disagreement band
   (|d_aobt3 − y|): median |estimate − y| of the NM proxy (d_aobt3), the ADS-B first-movement estimate when the
   aircraft was seen parked (adsb_first_move_s) and the stand estimate (adsb_stand_move_s), and the share of rows
   where ADS-B is closer than NM.
2. Drift: per airport, quantiles of the movement features on 2025 vs 2026 departures that have a ground segment.

  python scripts/checks/m034_adsb_inputs.py
"""
from prc import db

con = db.connect(read_only=True)

AGREE = """
WITH d AS (
    SELECT f.airport, f.y, f.d_aobt3, a.adsb_first_move_s AS fm, a.adsb_seen_parked AS parked, s.adsb_stand_move_s AS sm,
           CASE WHEN abs(f.d_aobt3 - f.y) <= 60 THEN 'a ≤1 min' WHEN abs(f.d_aobt3 - f.y) <= 300 THEN 'b 1–5 min'
                WHEN abs(f.d_aobt3 - f.y) <= 900 THEN 'c 5–15 min' ELSE 'd >15 min' END AS nm_gap
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE f.ds = 'train' AND NOT coalesce(f.nm_unmatched, false) AND f.y <= 10800 AND f.d_aobt3 IS NOT NULL
      AND a.adsb_has_ground
)
SELECT nm_gap, count(*) AS n,
  round(median(abs(d_aobt3 - y)), 0) AS medae_nm,
  count(*) FILTER (WHERE parked AND fm IS NOT NULL) AS n_parked,
  round(median(abs(fm - y)) FILTER (WHERE parked AND fm IS NOT NULL), 0) AS medae_adsb_first_move_parked,
  round(avg((abs(fm - y) < abs(d_aobt3 - y))::INT) FILTER (WHERE parked AND fm IS NOT NULL), 3) AS share_adsb_closer_parked,
  count(*) FILTER (WHERE sm IS NOT NULL) AS n_stand,
  round(median(abs(sm - y)) FILTER (WHERE sm IS NOT NULL), 0) AS medae_adsb_stand,
  round(avg((abs(sm - y) < abs(d_aobt3 - y))::INT) FILTER (WHERE sm IS NOT NULL), 3) AS share_adsb_closer_stand
FROM d GROUP BY ROLLUP (nm_gap) ORDER BY nm_gap NULLS LAST
"""
db.save_check(con, "m034_adsb_vs_nm", AGREE,
              "2025 matched departures with an ADS-B ground segment (all extracted Jan/Jul days): accuracy of the NM proxy "
              "vs ADS-B movement estimates, by how far NM's AOBT_3 is from the airport off-block.")

DRIFT = """
WITH d AS (
    SELECT f.airport, CASE WHEN f.ds = 'train' THEN 2025 ELSE 2026 END AS yr, a.*
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) WHERE a.adsb_has_ground
)
SELECT airport, yr, count(*) AS n_ground,
  round(avg(adsb_seen_parked::INT), 3) AS share_parked,
  round(median(adsb_first_move_s) FILTER (WHERE adsb_seen_parked), 0) AS med_first_move_parked_s,
  round(median(adsb_taxi_dist_m), 0) AS med_taxi_dist_m,
  round(median(adsb_hold_s), 0) AS med_hold_s,
  round(median(adsb_first_ground_s), 0) AS med_first_ground_s,
  round(median(adsb_n_pts), 0) AS med_n_pts,
  round(median(adsb_max_gap_s), 0) AS med_max_gap_s
FROM d GROUP BY ALL ORDER BY airport, yr
"""
db.save_check(con, "m034_adsb_feature_drift", DRIFT,
              "Movement features (seen parked, first movement, taxi distance, holds) vs reception features (first ground "
              "observation, points, largest gap) on departures with an ADS-B ground segment, 2025 vs 2026 ranking. "
              "Reception features are expected to drift with the receiver network (forum, a participant 27/09).")
