-- Model input table for departures (train + ranking). One row per DEP mvt_id.
CREATE OR REPLACE TABLE feat_dep_base AS
WITH d AS (
    SELECT c.*, r.tz FROM clean_dep c JOIN ref_airport r USING (airport)
),
win AS (  -- same-airport and same-runway movement counts around the take-off
    SELECT mvt_id, phase, airport, runway, t_mvt, wake,
        count(*) FILTER (WHERE phase='DEP') OVER w_ap_10p AS n_dep_ap_10p,
        count(*) FILTER (WHERE phase='DEP') OVER w_ap_30p AS n_dep_ap_30p,
        count(*) FILTER (WHERE phase='DEP') OVER w_ap_10f AS n_dep_ap_10f,
        count(*) FILTER (WHERE phase='ARR') OVER w_ap_10p AS n_arr_ap_10p,
        count(*) FILTER (WHERE phase='ARR') OVER w_ap_10f AS n_arr_ap_10f,
        count(*) FILTER (WHERE phase='DEP') OVER w_ap_60c AS n_dep_ap_60c,
        count(*) FILTER (WHERE phase='ARR') OVER w_ap_60c AS n_arr_ap_60c,
        avg(arr_taxi_in) FILTER (WHERE phase='ARR') OVER w_ap_30p AS arr_taxi_in_30p,
        count(*) FILTER (WHERE phase='DEP') OVER w_rw_10p AS n_dep_rw_10p,
        count(*) FILTER (WHERE phase='DEP') OVER w_rw_30p AS n_dep_rw_30p,
        count(*) FILTER (WHERE phase='ARR') OVER w_rw_10p AS n_arr_rw_10p,
        count(*) FILTER (WHERE phase='ARR') OVER w_rw_10f AS n_arr_rw_10f
    FROM ev_mvt
    WINDOW
        w_ap_10p AS (PARTITION BY airport ORDER BY t_mvt RANGE BETWEEN INTERVAL 10 MINUTES PRECEDING AND INTERVAL 1 MICROSECOND PRECEDING),
        w_ap_30p AS (PARTITION BY airport ORDER BY t_mvt RANGE BETWEEN INTERVAL 30 MINUTES PRECEDING AND INTERVAL 1 MICROSECOND PRECEDING),
        w_ap_10f AS (PARTITION BY airport ORDER BY t_mvt RANGE BETWEEN INTERVAL 1 MICROSECOND FOLLOWING AND INTERVAL 10 MINUTES FOLLOWING),
        w_ap_60c AS (PARTITION BY airport ORDER BY t_mvt RANGE BETWEEN INTERVAL 30 MINUTES PRECEDING AND INTERVAL 30 MINUTES FOLLOWING),
        w_rw_10p AS (PARTITION BY airport, runway ORDER BY t_mvt RANGE BETWEEN INTERVAL 10 MINUTES PRECEDING AND INTERVAL 1 MICROSECOND PRECEDING),
        w_rw_30p AS (PARTITION BY airport, runway ORDER BY t_mvt RANGE BETWEEN INTERVAL 30 MINUTES PRECEDING AND INTERVAL 1 MICROSECOND PRECEDING),
        w_rw_10f AS (PARTITION BY airport, runway ORDER BY t_mvt RANGE BETWEEN INTERVAL 1 MICROSECOND FOLLOWING AND INTERVAL 10 MINUTES FOLLOWING)
),
seq AS (  -- same-runway departure sequence
    SELECT mvt_id,
        epoch(t_mvt) - epoch(lag(t_mvt) OVER w) AS gap_prev_dep_rw,
        epoch(lead(t_mvt) OVER w) - epoch(t_mvt) AS gap_next_dep_rw,
        lag(wake) OVER w AS prev_wake_rw
    FROM stg_mvt WHERE phase = 'DEP'
    WINDOW w AS (PARTITION BY airport, runway ORDER BY t_mvt, mvt_id)  -- mvt_id: deterministic order of tied take-offs
)
SELECT
    d.ds, d.month, d.mvt_id, d.airport, d.y,
    -- evaluation flags (not model inputs)
    d.f_no_nm_match, d.f_block_eq_sched, d.f_block_eq_planned, d.f_round_minute_block,
    d.f_negative_taxi, d.f_taxi_gt_3h,
    -- categoricals
    d.runway, d.stand, coalesce(d.actype_flt, d.actype_mvt) AS actype, d.wake, d.market, d.flight_type,
    d.flight_rule_mvt, d.operator, d.ades_mvt AS ades, left(d.ades_mvt, 2) AS ades_region,
    regexp_extract(d.flight_mvt, '^[A-Z]{3}') AS flt_prefix,
    d.actype_mvt IS NULL AS actype_mvt_missing,
    d.f_no_nm_match AS nm_unmatched,
    d.f_aobt3_round_minute AS aobt3_round_minute,
    d.f_type_mismatch_mvt_flt AS type_mismatch,
    -- time deltas relative to the take-off (seconds)
    epoch(d.t_mvt) - epoch(d.t_sched)  AS d_sched,
    epoch(d.t_mvt) - epoch(d.t_lobt)   AS d_lobt,
    epoch(d.t_mvt) - epoch(d.t_iobt)   AS d_iobt,
    epoch(d.t_mvt) - epoch(d.t_eobt1)  AS d_eobt1,
    epoch(d.t_mvt) - epoch(d.t_aobt3)  AS d_aobt3,
    epoch(d.t_arvt1) - epoch(d.t_eobt1) AS dur_plan,
    epoch(d.t_arvt3) - epoch(d.t_aobt3) AS dur_act,
    epoch(d.t_arvt3) - epoch(d.t_mvt)   AS d_arvt3,
    epoch(d.t_aobt3) - epoch(d.t_eobt1) AS aobt3_minus_eobt1,
    epoch(d.t_sched) - epoch(d.t_lobt)  AS sched_minus_lobt,
    second(d.t_sched) AS sched_second,
    date_diff('day', d.t_sched::DATE, d.t_mvt::DATE) AS day_shift,
    -- calendar (local time of the airport)
    hour(timezone(d.tz, timezone('UTC', d.t_mvt))) + minute(timezone(d.tz, timezone('UTC', d.t_mvt))) / 60.0 AS hour_local,
    hour(timezone(d.tz, timezone('UTC', d.t_sched))) + minute(timezone(d.tz, timezone('UTC', d.t_sched))) / 60.0 AS sched_hour_local,
    isodow(timezone(d.tz, timezone('UTC', d.t_mvt))) AS dow_local,
    month(d.t_mvt) AS month_of_year,
    -- congestion
    w.n_dep_ap_10p, w.n_dep_ap_30p, w.n_dep_ap_10f, w.n_arr_ap_10p, w.n_arr_ap_10f, w.n_dep_ap_60c, w.n_arr_ap_60c,
    w.arr_taxi_in_30p, w.n_dep_rw_10p, w.n_dep_rw_30p, w.n_arr_rw_10p, w.n_arr_rw_10f,
    s.gap_prev_dep_rw, s.gap_next_dep_rw, s.prev_wake_rw,
    -- keys for the ASOF features below
    d.t_mvt, d.t_aobt3, d.t_sched
FROM d
JOIN win w ON w.mvt_id = d.mvt_id
JOIN seq s ON s.mvt_id = d.mvt_id;
