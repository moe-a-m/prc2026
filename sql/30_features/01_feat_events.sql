-- Event series used by congestion features. Built from train + ranking together (times are disjoint:
-- 2025 vs 2026), using only columns available for every row in both sets:
--   * take-off / landing times (MVT) of all movements,
--   * NM AOBT_3 of departures,
--   * ARR block (in-block) times and ARR taxi-in (ranking ARR rows are intact).
-- Departure BLOCK_TIME / TAXITIME are never read here (train/serve parity, tests/test_leakage.py).
CREATE OR REPLACE TABLE ev_mvt AS
SELECT mvt_id, airport, phase, runway, stand, wake, t_mvt,
       CASE WHEN phase = 'ARR' THEN t_block END AS t_arr_block,
       CASE WHEN phase = 'ARR' THEN y END       AS arr_taxi_in,
       CASE WHEN phase = 'DEP' THEN t_aobt3 END AS t_aobt3
FROM stg_mvt;

-- cumulative counts at each event time, per airport and kind; looked up with ASOF joins
CREATE OR REPLACE TABLE ev_cum AS
-- cnt = number of events of that kind at or before ts, ties included (count with the default RANGE frame covers peers);
-- row_number() here made counts depend on the arbitrary order of tied timestamps (AOBT_3 is minute-rounded).
SELECT airport, kind, ts, count(*) OVER (PARTITION BY airport, kind ORDER BY ts) AS cnt
FROM (
    SELECT airport, 'dep_mvt' AS kind, t_mvt AS ts FROM ev_mvt WHERE phase = 'DEP'
    UNION ALL SELECT airport, 'arr_mvt', t_mvt FROM ev_mvt WHERE phase = 'ARR'
    UNION ALL SELECT airport, 'dep_aobt3', t_aobt3 FROM ev_mvt WHERE phase = 'DEP' AND t_aobt3 IS NOT NULL
    -- take-offs of departures that have an AOBT_3 (so 'pushed back but not airborne' counts are consistent)
    UNION ALL SELECT airport, 'dep_mvt_w_aobt3', t_mvt FROM ev_mvt WHERE phase = 'DEP' AND t_aobt3 IS NOT NULL
);
