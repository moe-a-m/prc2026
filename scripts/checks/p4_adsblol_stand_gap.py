"""Where the ADS-B stand estimate (M-021) is lost: departures with a matched taxi segment that are not seen within
60 m of their stand — no APDF stand code, stand code without OSM position, or aircraft only seen farther away.

  python scripts/checks/p4_adsblol_stand_gap.py
"""
from prc import db

con = db.connect(read_only=True)

GAP = """
WITH d AS (
    SELECT f.airport, strftime(f.month, '%Y-%m') AS ym, f.stand, a.adsb_has_ground,
           g.stand IS NOT NULL AS has_geo, s.adsb_seen_at_stand, s.adsb_min_d_stand_m AS min_d, s.adsb_first_d_stand_m AS first_d
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id)
    LEFT JOIN stg_stand_geo g ON g.airport = f.airport AND g.stand = f.stand
    LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE month(f.month) IN (1, 7) AND a.adsb_has_ground
)
SELECT airport, ym, count(*) AS n_ground,
  round(100*avg((stand IS NULL)::INT), 1) AS pct_no_stand_code,
  round(100*avg((stand IS NOT NULL AND NOT has_geo)::INT), 1) AS pct_no_osm_position,
  round(100*avg(coalesce(adsb_seen_at_stand, false)::INT), 1) AS pct_seen_le60m,
  round(100*avg((min_d > 60 AND min_d <= 150)::INT), 1) AS pct_min_60_150m,
  round(100*avg((min_d > 150 AND min_d <= 500)::INT), 1) AS pct_min_150_500m,
  round(100*avg((min_d > 500)::INT), 1) AS pct_min_gt500m,
  round(median(first_d) FILTER (WHERE NOT adsb_seen_at_stand), 0) AS med_first_d_not_seen_m
FROM d GROUP BY ROLLUP (airport, ym) ORDER BY airport NULLS LAST, ym NULLS LAST
"""
db.save_check(con, "p4_adsblol_stand_gap", GAP,
              "Departures (Jan/Jul 2025 and 2026) with a matched ADS-B ground segment, split by why the M-021 stand "
              "estimate is or is not available: no APDF stand code, stand code without an OSM parking_position "
              "(stg_stand_geo), seen within 60 m, or closest ground point 60–150 / 150–500 / > 500 m from the OSM "
              "position. Last column: median distance of the first ground point for rows not seen within 60 m.")

STANDS = """
WITH d AS (
    SELECT f.airport, f.stand, count(*) AS n_dep
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id)
    LEFT JOIN stg_stand_geo g ON g.airport = f.airport AND g.stand = f.stand
    WHERE month(f.month) IN (1, 7) AND a.adsb_has_ground AND f.stand IS NOT NULL AND g.stand IS NULL
    GROUP BY ALL
)
SELECT * FROM (SELECT *, row_number() OVER (PARTITION BY airport ORDER BY n_dep DESC, stand) AS rk FROM d)
WHERE rk <= 15 ORDER BY airport, rk
"""
db.save_check(con, "p4_adsblol_stand_gap_codes", STANDS,
              "Top-15 APDF stand codes per airport (by departures with an ADS-B ground segment) that have no OSM "
              "parking_position in stg_stand_geo — shows whether the miss is a code-normalisation problem or a "
              "genuinely unmapped stand.")
