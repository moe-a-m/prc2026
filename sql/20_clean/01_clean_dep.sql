-- Departures with data-quality flags. Flag, don't drop (CLAUDE.md §8).
CREATE OR REPLACE TABLE clean_dep AS
SELECT
    m.*,
    flight_id IS NULL                                        AS f_no_nm_match,
    y < 0                                                    AS f_negative_taxi,
    y > 3 * 3600                                             AS f_taxi_gt_3h,
    count(*) OVER (PARTITION BY mvt_id) > 1                  AS f_dup_mvt_id,
    t_block = t_sched                                        AS f_block_eq_sched,
    t_block IN (t_lobt, t_iobt, t_eobt1)                     AS f_block_eq_planned,
    second(t_block) = 0                                      AS f_round_minute_block,
    actype_flt IS NOT NULL AND actype_mvt IS DISTINCT FROM actype_flt AS f_type_mismatch_mvt_flt,
    adep_flt IS NOT NULL AND adep_mvt IS DISTINCT FROM adep_flt       AS f_adep_mismatch,
    second(t_aobt3) = 0                                      AS f_aobt3_round_minute
FROM stg_mvt m
WHERE phase = 'DEP';
