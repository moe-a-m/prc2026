"""P4 METAR checks: coverage/cadence per station-month, report types, parser sample, unit ranges, drift."""
from prc import db

con = db.connect(read_only=True)
C = lambda name, sql, note="": print(name, "\n", db.save_check(con, name, sql, note).to_string(max_rows=200), "\n")

C("p4_metar_coverage", """
SELECT station, strftime(date_trunc('month', t_obs), '%Y-%m') m, count(*) n_obs,
  round(count(*) / (date_diff('day', min(t_obs)::DATE, max(t_obs)::DATE) + 1.0), 1) obs_per_day,
  round(max(gap_min)) max_gap_min, sum((gap_min > 120)::INT) n_gaps_gt2h
FROM (SELECT *, (epoch(t_obs) - epoch(lag(t_obs) OVER (PARTITION BY station ORDER BY t_obs))) / 60 gap_min FROM stg_metar)
WHERE t_obs >= '2025-01-01' AND t_obs < '2026-08-01' GROUP BY ALL ORDER BY 1, 2""",
 "Observations per station-month (UTC), max gap between consecutive reports, gaps > 2 h.")

C("p4_metar_report_types", """
SELECT station, count(*) n, sum(is_auto::INT) n_auto, sum(is_cor::INT) n_cor,
  sum((metar LIKE 'SPECI%' OR metar LIKE '% SPECI %')::INT) n_speci, count(rvr_min_m) n_rvr,
  (SELECT count(*) FROM raw_metar r WHERE r.station = s.station) n_raw
FROM stg_metar s GROUP BY 1 ORDER BY 1""", "Raw vs staged rows (difference = duplicates removed).")

C("p4_metar_unit_ranges", """
SELECT station, round(min(temp_c),1) tmin, round(max(temp_c),1) tmax, round(max(wind_ms),1) wmax, round(max(gust_ms),1) gmax,
  round(min(vis_m)) vmin, round(max(vis_m)) vmax, round(min(ceiling_m)) cmin, min(rvr_min_m) rvrmin, max(rvr_min_m) rvrmax,
  round(100.0*avg((temp_c IS NULL)::INT),2) pct_temp_null, round(100.0*avg((vis_m IS NULL)::INT),2) pct_vis_null
FROM stg_metar GROUP BY 1 ORDER BY 1""", "Sanity ranges in SI units.")

C("p4_metar_parser_sample", """
-- flags derived from IEM wxcodes vs presence of the same groups in the raw METAR text, random sample of
-- reports that have any weather code (reproducible: SAMPLE with fixed seed)
WITH s AS (SELECT * FROM stg_metar WHERE wxcodes IS NOT NULL USING SAMPLE reservoir(400 ROWS) REPEATABLE (42)),
c AS (SELECT *,
  regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|DR|BL|SH|TS|FZ)*(SN|SG|PL)') raw_snow,
  regexp_matches(metar, ' [-+]?(VC)?FZ') raw_freezing,
  regexp_matches(metar, ' [-+]?(VC)?TS') raw_thunder,
  regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|FZ)*FG') raw_fog FROM s)
SELECT count(*) n,
  sum((wx_snow = raw_snow)::INT) agree_snow, sum((wx_freezing = raw_freezing)::INT) agree_freezing,
  sum((wx_thunder = raw_thunder)::INT) agree_thunder, sum((wx_fog = raw_fog)::INT) agree_fog
FROM c""", "Agreement of parsed flags with an independent regex on the raw METAR text (400-row sample).")

C("p4_metar_parser_disagreements", """
WITH s AS (SELECT * FROM stg_metar WHERE wxcodes IS NOT NULL USING SAMPLE reservoir(400 ROWS) REPEATABLE (42))
SELECT station, t_obs, wxcodes, wx_snow, wx_freezing, wx_thunder, wx_fog, metar FROM s
WHERE wx_snow <> regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|DR|BL|SH|TS|FZ)*(SN|SG|PL)')
   OR wx_freezing <> regexp_matches(metar, ' [-+]?(VC)?FZ')
   OR wx_thunder <> regexp_matches(metar, ' [-+]?(VC)?TS')
   OR wx_fog <> regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|FZ)*FG') LIMIT 30""")

C("p4_metar_drift", """
SELECT station, strftime(t_obs, '%Y-%m') m, count(*) n, round(avg(temp_c),1) temp_mean,
  round(100.0*avg(wx_snow::INT),2) pct_snow, round(100.0*avg(wx_freezing::INT),2) pct_freezing,
  round(100.0*avg(wx_thunder::INT),2) pct_thunder, round(100.0*avg((vis_m < 1500)::INT),2) pct_vis_lt1500,
  round(100.0*avg((temp_c <= 0)::INT),2) pct_subzero
FROM stg_metar WHERE month(t_obs) IN (1, 7) AND t_obs >= '2025-01-01' AND t_obs < '2026-08-01'
GROUP BY ALL ORDER BY 1, 2""", "Jan/Jul 2025 vs Jan/Jul 2026 weather distribution per station.")

C("p4_wx_taxi_by_condition", """
-- Does taxi-out differ on snow/freezing days? (CLAUDE.md §6: check before modelling) — 2025 training DEP
SELECT f.airport,
  round(avg(y) FILTER (WHERE NOT coalesce(w.wx3h_snow OR w.wx3h_freezing, false)), 0) mean_y_clear,
  round(avg(y) FILTER (WHERE w.wx3h_snow OR w.wx3h_freezing), 0) mean_y_snow_or_fz,
  count(*) FILTER (WHERE w.wx3h_snow OR w.wx3h_freezing) n_snow_or_fz,
  round(median(y) FILTER (WHERE NOT coalesce(w.wx3h_snow OR w.wx3h_freezing, false)), 0) med_y_clear,
  round(median(y) FILTER (WHERE w.wx3h_snow OR w.wx3h_freezing), 0) med_y_snow_or_fz,
  round(median(y) FILTER (WHERE w.wx_vis_m < 1500), 0) med_y_vis_lt1500, count(*) FILTER (WHERE w.wx_vis_m < 1500) n_vis_lt1500,
  round(100.0*avg(w.wx_stale::INT), 2) pct_stale
FROM feat_dep f JOIN feat_dep_wx w USING (mvt_id) WHERE f.ds = 'train' AND f.y <= 3*3600 GROUP BY 1 ORDER BY 1""",
 "Taxi-out (rows ≤ 3 h) with snow/freezing precipitation in the 3 h before take-off vs without.")
