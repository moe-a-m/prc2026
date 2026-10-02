"""P1 profiling checks on raw tables (CLAUDE.md §8 'First checks'). Outputs -> reports/checks/."""
from prc import db

con = db.connect(read_only=True)
C = lambda name, sql, note="": print(name, "\n", db.save_check(con, name, sql, note).to_string(max_rows=80), "\n")

C("p1_rows_per_file_phase", """
SELECT src_month, PHASE_mvt, count(*) n FROM raw_training GROUP BY ALL ORDER BY ALL""")

C("p1_airport_columns", """
-- Which column holds the airport? For DEP it should be ADEP_mvt, for ARR ADES_mvt.
SELECT 'train' ds, PHASE_mvt, ADEP_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH') adep_in10,
       ADES_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH') ades_in10, count(*) n
FROM raw_training GROUP BY ALL
UNION ALL
SELECT 'rank', PHASE_mvt, ADEP_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH'),
       ADES_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH'), count(*)
FROM raw_ranking GROUP BY ALL ORDER BY ALL""")

C("p1_ids", """
SELECT 'train' ds, count(*) n, count(MVT_ID_mvt) n_id, count(DISTINCT MVT_ID_mvt) n_distinct,
       sum((MVT_ID_mvt <> floor(MVT_ID_mvt))::INT) n_nonintegral, min(MVT_ID_mvt) mn, max(MVT_ID_mvt) mx,
       count(FLIGHT_ID_mvt) n_flight_id, count(DISTINCT FLIGHT_ID_mvt) n_flight_distinct
FROM raw_training
UNION ALL
SELECT 'rank', count(*), count(MVT_ID_mvt), count(DISTINCT MVT_ID_mvt),
       sum((MVT_ID_mvt <> floor(MVT_ID_mvt))::INT), min(MVT_ID_mvt), max(MVT_ID_mvt),
       count(FLIGHT_ID_mvt), count(DISTINCT FLIGHT_ID_mvt)
FROM raw_ranking
UNION ALL
SELECT 'train∩rank ids', count(*), NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM (SELECT DISTINCT MVT_ID_mvt FROM raw_training) t JOIN (SELECT DISTINCT MVT_ID_mvt FROM raw_ranking) r USING (MVT_ID_mvt)""")

C("p1_submitting_vs_ranking", """
SELECT
  (SELECT count(*) FROM raw_submitting) n_sub,
  (SELECT count(*) FROM raw_ranking WHERE PHASE_mvt='DEP') n_rank_dep,
  (SELECT count(*) FROM raw_submitting s ANTI JOIN (SELECT * FROM raw_ranking WHERE PHASE_mvt='DEP') r USING (MVT_ID_mvt)) sub_not_in_rank_dep,
  (SELECT count(*) FROM (SELECT * FROM raw_ranking WHERE PHASE_mvt='DEP') r ANTI JOIN raw_submitting s USING (MVT_ID_mvt)) rank_dep_not_in_sub""")

C("p1_target_identity", """
SELECT PHASE_mvt, count(*) n, count(TAXITIME_SEC_mvt) n_target,
  sum((TAXITIME_SEC_mvt = epoch(MVT_TIME_UTC_mvt) - epoch(BLOCK_TIME_UTC_mvt))::INT) n_exact,
  sum((abs(TAXITIME_SEC_mvt - (epoch(MVT_TIME_UTC_mvt) - epoch(BLOCK_TIME_UTC_mvt))) <= 1)::INT) n_within_1s,
  sum((TAXITIME_SEC_mvt = epoch(BLOCK_TIME_UTC_mvt) - epoch(MVT_TIME_UTC_mvt))::INT) n_exact_reversed,
  max(abs(TAXITIME_SEC_mvt - (epoch(MVT_TIME_UTC_mvt) - epoch(BLOCK_TIME_UTC_mvt)))) max_abs_diff
FROM raw_training GROUP BY ALL""", "Identity: DEP target = MVT − BLOCK; ARR presumably BLOCK − MVT (taxi-in).")

C("p1_target_quantiles_dep", """
SELECT ADEP_mvt airport, count(*) n, count(TAXITIME_SEC_mvt) n_t,
  min(TAXITIME_SEC_mvt) mn, quantile_cont(TAXITIME_SEC_mvt, 0.01) p01, quantile_cont(TAXITIME_SEC_mvt, 0.5) p50,
  round(avg(TAXITIME_SEC_mvt),1) mean, round(stddev(TAXITIME_SEC_mvt),1) sd,
  quantile_cont(TAXITIME_SEC_mvt, 0.99) p99, max(TAXITIME_SEC_mvt) mx,
  sum((TAXITIME_SEC_mvt < 0)::INT) n_neg, sum((TAXITIME_SEC_mvt > 3*3600)::INT) n_gt3h
FROM raw_training WHERE PHASE_mvt='DEP' GROUP BY ALL ORDER BY 1""")
