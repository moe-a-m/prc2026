-- NM default-taxi detection (M-004 refinement, reports/checks/p1_x_minute_concentration.md):
-- for many flights AOBT_3 = NM take-off − a default taxi time, so MVT − AOBT_3 piles up on one whole-minute
-- value per airport × runway × month. Distance from that mode says whether AOBT_3 carries real off-block
-- information. Label-free (uses only MVT and AOBT_3), identical for training and ranking rows.
CREATE OR REPLACE TABLE feat_dep_nm AS
WITH x AS (
    SELECT mvt_id, airport, runway, month, d_aobt3, round(d_aobt3 / 60) AS xm FROM feat_dep WHERE d_aobt3 IS NOT NULL
),
g AS (
    SELECT airport, runway, month, mode(xm) AS nm_default_min, count(*) AS n_grp FROM x GROUP BY ALL
),
s AS (
    SELECT x.airport, x.runway, x.month, avg((x.xm = g.nm_default_min)::INT) AS nm_default_share
    FROM x JOIN g USING (airport, runway, month) GROUP BY ALL
)
SELECT x.mvt_id, g.nm_default_min, s.nm_default_share,
       x.d_aobt3 - 60 * g.nm_default_min AS d_aobt3_minus_default,
       abs(x.xm - g.nm_default_min) = 0 AS aobt3_at_default
FROM x JOIN g USING (airport, runway, month) JOIN s USING (airport, runway, month);
