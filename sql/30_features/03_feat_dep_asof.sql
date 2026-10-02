-- Queue / stand features via ASOF lookups on cumulative event counts and ARR stand occupancy.
-- n_takeoffs_since_aobt3: departures that took off at the airport between this flight's NM AOBT_3 and its take-off
--   (≈ queue ahead of it while taxiing). n_taxiing_at_mvt: departures with AOBT_3 ≤ t and take-off > t.
-- Stand: latest ARR in-block at the same stand before this take-off (and the one before it). An arrival that
--   blocks in at the stand after this flight's off-block bounds its off-block from above (post-ops use).
CREATE OR REPLACE TABLE feat_dep AS
WITH dm AS (SELECT * FROM ev_cum WHERE kind = 'dep_mvt'),
     am AS (SELECT * FROM ev_cum WHERE kind = 'arr_mvt'),
     da AS (SELECT * FROM ev_cum WHERE kind = 'dep_aobt3'),
     dw AS (SELECT * FROM ev_cum WHERE kind = 'dep_mvt_w_aobt3'),
     arr_stand AS (
        SELECT airport, stand, t_arr_block,
               lag(t_arr_block) OVER (PARTITION BY airport, stand ORDER BY t_arr_block) AS t_arr_block_prev
        FROM ev_mvt WHERE phase = 'ARR' AND stand IS NOT NULL AND t_arr_block IS NOT NULL
     ),
     dep_stand AS (
        SELECT airport, stand, t_mvt AS t_dep_prev FROM ev_mvt WHERE phase = 'DEP' AND stand IS NOT NULL
     ),
     q AS (
        SELECT b.mvt_id,
            c_t.cnt  AS c_dep_t,     -- departures with take-off ≤ t (includes self)
            c_a.cnt  AS c_dep_a,     -- departures with take-off ≤ AOBT_3
            c_s.cnt  AS c_dep_s,     -- departures with take-off ≤ SCHED
            a_t.cnt  AS c_arr_t,
            a_a.cnt  AS c_arr_a,
            p_t.cnt  AS c_aobt3_t,   -- departures with AOBT_3 ≤ t
            w_t.cnt  AS c_dep_w_t    -- departures having an AOBT_3 with take-off ≤ t
        FROM feat_dep_base b
        ASOF LEFT JOIN dm c_t ON c_t.airport = b.airport AND c_t.ts <= b.t_mvt
        ASOF LEFT JOIN dm c_a ON c_a.airport = b.airport AND c_a.ts <= b.t_aobt3
        ASOF LEFT JOIN dm c_s ON c_s.airport = b.airport AND c_s.ts <= b.t_sched
        ASOF LEFT JOIN am a_t ON a_t.airport = b.airport AND a_t.ts <= b.t_mvt
        ASOF LEFT JOIN am a_a ON a_a.airport = b.airport AND a_a.ts <= b.t_aobt3
        ASOF LEFT JOIN da p_t ON p_t.airport = b.airport AND p_t.ts <= b.t_mvt
        ASOF LEFT JOIN dw w_t ON w_t.airport = b.airport AND w_t.ts <= b.t_mvt
     ),
     st AS (
        SELECT b.mvt_id,
            epoch(b.t_mvt) - epoch(s.t_arr_block)      AS gap_arr_stand_1,
            epoch(b.t_mvt) - epoch(s.t_arr_block_prev) AS gap_arr_stand_2
        FROM feat_dep_base b
        ASOF LEFT JOIN arr_stand s ON s.airport = b.airport AND s.stand = b.stand AND s.t_arr_block <= b.t_mvt
     ),
     sd AS (
        SELECT b.mvt_id, epoch(b.t_mvt) - epoch(p.t_dep_prev) AS gap_prev_dep_stand
        FROM feat_dep_base b
        ASOF LEFT JOIN dep_stand p ON p.airport = b.airport AND p.stand = b.stand AND p.t_dep_prev < b.t_mvt
     )
SELECT b.* EXCLUDE (t_mvt, t_aobt3, t_sched, sched_second),
    CASE WHEN b.t_aobt3 IS NOT NULL THEN coalesce(q.c_dep_t, 0) - 1 - coalesce(q.c_dep_a, 0) END AS n_takeoffs_since_aobt3,
    CASE WHEN b.t_aobt3 IS NOT NULL THEN coalesce(q.c_arr_t, 0) - coalesce(q.c_arr_a, 0) END     AS n_landings_since_aobt3,
    coalesce(q.c_dep_t, 0) - 1 - coalesce(q.c_dep_s, 0)  AS n_takeoffs_since_sched,
    coalesce(q.c_aobt3_t, 0) - coalesce(q.c_dep_w_t, 0)  AS n_taxiing_at_mvt,
    st.gap_arr_stand_1, st.gap_arr_stand_2, sd.gap_prev_dep_stand,
    epoch(b_t.t_mvt) AS t_mvt_epoch
FROM feat_dep_base b
JOIN (SELECT mvt_id, t_mvt FROM feat_dep_base) b_t USING (mvt_id)
LEFT JOIN q USING (mvt_id)
LEFT JOIN st USING (mvt_id)
LEFT JOIN sd USING (mvt_id);
