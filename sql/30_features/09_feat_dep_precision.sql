-- Record-precision markers (M-025), label-free. A minute-rounded take-off time marks departures whose block time is
-- also likely minute-rounded (manual recording): P(block sec=0 | MVT sec=0) ≈ 50% vs 4.5% at EDDM/EGLL/LFPG/LIRF/LTFM
-- (reports/checks/p6_rounding_mvt_vs_block.md). Arrival rows at the same airport give the local share of rounded records
-- (window over ±60 min of movement time, computed once over all movements).
CREATE OR REPLACE TABLE feat_dep_precision AS
WITH m AS (
    SELECT mvt_id, phase, airport, t_mvt,
           CASE WHEN phase = 'ARR' THEN (second(t_mvt) = 0)::INT END AS arr_sec0
    FROM stg_mvt
),
w AS (
    SELECT mvt_id, phase, t_mvt,
           avg(arr_sec0) OVER (PARTITION BY airport ORDER BY t_mvt
                               RANGE BETWEEN INTERVAL 60 MINUTE PRECEDING AND INTERVAL 60 MINUTE FOLLOWING) AS arr_mvt_sec0_share_60m
    FROM m
)
SELECT mvt_id, (second(t_mvt) = 0) AS mvt_sec0, second(t_mvt) AS mvt_second, arr_mvt_sec0_share_60m
FROM w WHERE phase = 'DEP';
