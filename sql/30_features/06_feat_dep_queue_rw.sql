-- Same-runway queue counts (M-015). Label-free: take-off times of all departures, landing times of all
-- arrivals, NM AOBT_3 and the schedule. Identical for training and ranking rows.
CREATE OR REPLACE TABLE feat_dep_queue_rw AS
WITH dc AS (SELECT airport, runway, t_mvt AS ts,  -- counts include ties (see 01_feat_events.sql)
                   count(*) OVER (PARTITION BY airport, runway ORDER BY t_mvt) AS cnt
            FROM ev_mvt WHERE phase = 'DEP' AND runway IS NOT NULL),
     ac AS (SELECT airport, runway, t_mvt AS ts,
                   count(*) OVER (PARTITION BY airport, runway ORDER BY t_mvt) AS cnt
            FROM ev_mvt WHERE phase = 'ARR' AND runway IS NOT NULL),
     d AS (SELECT mvt_id, airport, runway, t_mvt, t_aobt3, t_sched FROM stg_mvt WHERE phase = 'DEP'),
     q AS (
        SELECT d.mvt_id, d.t_aobt3,
               c_t.cnt AS c_t, c_a.cnt AS c_a, c_s.cnt AS c_s, a_t.cnt AS a_t, a_a.cnt AS a_a
        FROM d
        ASOF LEFT JOIN dc c_t ON c_t.airport = d.airport AND c_t.runway = d.runway AND c_t.ts <= d.t_mvt
        ASOF LEFT JOIN dc c_a ON c_a.airport = d.airport AND c_a.runway = d.runway AND c_a.ts <= d.t_aobt3
        ASOF LEFT JOIN dc c_s ON c_s.airport = d.airport AND c_s.runway = d.runway AND c_s.ts <= d.t_sched
        ASOF LEFT JOIN ac a_t ON a_t.airport = d.airport AND a_t.runway = d.runway AND a_t.ts <= d.t_mvt
        ASOF LEFT JOIN ac a_a ON a_a.airport = d.airport AND a_a.runway = d.runway AND a_a.ts <= d.t_aobt3
     )
SELECT mvt_id,
    CASE WHEN t_aobt3 IS NOT NULL THEN coalesce(c_t, 0) - 1 - coalesce(c_a, 0) END AS n_rw_takeoffs_since_aobt3,
    CASE WHEN t_aobt3 IS NOT NULL THEN coalesce(a_t, 0) - coalesce(a_a, 0) END     AS n_rw_landings_since_aobt3,
    coalesce(c_t, 0) - 1 - coalesce(c_s, 0)                                        AS n_rw_takeoffs_since_sched
FROM q;
