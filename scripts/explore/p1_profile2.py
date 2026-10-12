"""P1 profiling: null rates, AOBT_3 relationship, label-defect shares. Outputs -> reports/checks/."""
from prc import db

con = db.connect(read_only=True)
C = lambda name, sql, note="": print(name, "\n", db.save_check(con, name, sql, note).to_string(max_rows=120), "\n")

cols = [r[0] for r in con.sql("DESCRIBE raw_ranking").fetchall() if r[0] != "src_file"]
nn = ", ".join(f"round(100.0*count({c})/count(*),2) AS \"{c}\"" for c in cols)
C("p1_nonnull_pct_dep", f"""
SELECT ds, {nn}, count(*) n FROM (
  SELECT 'train' ds, * EXCLUDE (src_file, src_month) FROM raw_training WHERE PHASE_mvt='DEP'
  UNION ALL BY NAME
  SELECT 'rank' ds, * EXCLUDE (src_file) FROM raw_ranking WHERE PHASE_mvt='DEP') GROUP BY ds""",
  "Percent non-null per column, DEP rows only.")

C("p1_nonnull_pct_dep_airport", f"""
SELECT ds, ADEP_mvt, count(*) n,
  round(100.0*count(FLIGHT_ID_mvt)/count(*),2) flight_id, round(100.0*count(AOBT_3_flt)/count(*),2) aobt3,
  round(100.0*count(RUNWAY_mvt)/count(*),2) runway, round(100.0*count(STAND_mvt)/count(*),2) stand,
  round(100.0*count(SCHED_TIME_UTC_mvt)/count(*),2) sched, round(100.0*count(EOBT_1_flt)/count(*),2) eobt1,
  round(100.0*count(AIRCRAFT_TYPE_mvt)/count(*),2) actype
FROM (SELECT 'train' ds, ADEP_mvt, FLIGHT_ID_mvt, AOBT_3_flt, RUNWAY_mvt, STAND_mvt, SCHED_TIME_UTC_mvt, EOBT_1_flt, AIRCRAFT_TYPE_mvt FROM raw_training WHERE PHASE_mvt='DEP'
      UNION ALL SELECT 'rank', ADEP_mvt, FLIGHT_ID_mvt, AOBT_3_flt, RUNWAY_mvt, STAND_mvt, SCHED_TIME_UTC_mvt, EOBT_1_flt, AIRCRAFT_TYPE_mvt FROM raw_ranking WHERE PHASE_mvt='DEP')
GROUP BY ALL ORDER BY 2, 1 DESC""")

C("p1_aobt3_error", """
-- error of the naive estimate MVT - AOBT_3 vs target, DEP train
WITH d AS (SELECT ADEP_mvt ap, TAXITIME_SEC_mvt y, epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt) x,
                  second(AOBT_3_flt) s3 FROM raw_training WHERE PHASE_mvt='DEP')
SELECT ap, count(*) n, count(x) n_aobt3,
  round(100.0*avg((s3=0)::INT),2) pct_aobt3_round_min,
  round(sqrt(avg((x-y)^2)),1) rmse, round(median(x-y),1) med_err,
  round(100.0*avg((abs(x-y)<=60)::INT),2) pct_within_60s, round(100.0*avg((abs(x-y)<=180)::INT),2) pct_within_180s,
  round(quantile_cont(abs(x-y),0.9),1) p90_abs, round(quantile_cont(abs(x-y),0.99),1) p99_abs
FROM d GROUP BY ROLLUP(ap) ORDER BY ap NULLS LAST""", "Naive estimate taxi = MVT − AOBT_3_flt on rows where AOBT_3 exists.")

C("p1_block_echo", """
-- How often does BLOCK equal a planned time? (label-defect hypothesis raised on the forum)
SELECT ADEP_mvt ap, count(*) n,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = SCHED_TIME_UTC_mvt)::INT),2) pct_eq_sched,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = LOBT_flt)::INT),2) pct_eq_lobt,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = IOBT_flt)::INT),2) pct_eq_iobt,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = EOBT_1_flt)::INT),2) pct_eq_eobt1,
 round(100.0*avg((second(BLOCK_TIME_UTC_mvt)=0)::INT),2) pct_block_sec0,
 round(100.0*avg((second(MVT_TIME_UTC_mvt)=0)::INT),2) pct_mvt_sec0,
 round(100.0*avg((minute(BLOCK_TIME_UTC_mvt)%5=0 AND second(BLOCK_TIME_UTC_mvt)=0)::INT),2) pct_block_5min
FROM raw_training WHERE PHASE_mvt='DEP' GROUP BY ROLLUP(ap) ORDER BY ap NULLS LAST""",
 "Uniform-random seconds would give pct_block_sec0 ≈ 1.67%; 5-minute marks ≈ 0.33%.")
