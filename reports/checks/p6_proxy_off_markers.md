# Check: p6_proxy_off_markers

Run at 2026-10-03T05:57:32+00:00 (UTC), duckdb 1.5.6.

NM-matched 2025 departures with AOBT_3: label-free markers vs 'NM proxy off by > 1 h' (|MVT-AOBT_3-y|>3600). Lift and EXP-031 hold-out squared-error share.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (
  SELECT c.mvt_id, c.y, epoch(c.t_mvt)-epoch(c.t_aobt3) d_aobt3,
    abs(epoch(c.t_mvt)-epoch(c.t_aobt3) - c.y) > 3600 AS proxy_off,
    coalesce(c.ades_mvt <> c.ades_flt, false) m_ades_mismatch,
    coalesce(c.f_type_mismatch_mvt_flt, false) m_type_mismatch,
    NOT (c.callsign = c.flight_mvt OR (left(c.callsign,3)=left(c.flight_mvt,3)
         AND regexp_extract(c.callsign,'[0-9].*') = regexp_extract(c.flight_mvt,'[0-9].*'))) AS m_callsign_neq_flight,
    epoch(c.t_mvt)-epoch(c.t_aobt3) > 7200 AS m_proxy_gt2h,
    epoch(c.t_mvt)-epoch(c.t_aobt3) < 0 AS m_proxy_negative,
    epoch(c.t_aobt3) < epoch(c.t_sched) - 3600 AS m_aobt3_1h_before_sched,
    abs(epoch(c.t_aobt3) - epoch(c.t_eobt1)) > 3600 AS m_aobt3_eobt1_gt1h,
    abs(epoch(c.t_sched) - epoch(c.t_lobt)) > 3*3600 AS m_sched_lobt_gt3h,
    epoch(c.t_mvt)-epoch(c.t_sched) > 6*3600 AS m_late6h,
    c.airport='LIRF' AS m_lirf
  FROM clean_dep c WHERE c.ds='train' AND NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL),
u AS (UNPIVOT b ON m_ades_mismatch, m_type_mismatch, m_callsign_neq_flight, m_proxy_gt2h, m_proxy_negative,
      m_aobt3_1h_before_sched, m_aobt3_eobt1_gt1h, m_sched_lobt_gt3h, m_late6h, m_lirf INTO NAME marker VALUE val)
SELECT marker, count(*) FILTER (val) n_marked, round(100*avg(val::INT),3) pct_rows,
  round(100*avg(proxy_off::INT) FILTER (val),2) pct_proxy_off_if_marked,
  round(100*avg(proxy_off::INT) FILTER (NOT val),3) pct_proxy_off_if_not,
  count(*) FILTER (val AND proxy_off) n_marked_and_off,
  round(100*sum(o.se) FILTER (val)/any_value(tot_se),2) pct_total_sq_err_marked,
  round(100*sum(o.se) FILTER (val AND proxy_off)/any_value(tot_se),2) pct_total_sq_err_marked_and_off
FROM u LEFT JOIN oof o USING (mvt_id), tot GROUP BY 1 ORDER BY pct_proxy_off_if_marked DESC
```

10 rows

| marker                  |   n_marked |   pct_rows |   pct_proxy_off_if_marked |   pct_proxy_off_if_not |   n_marked_and_off |   pct_total_sq_err_marked |   pct_total_sq_err_marked_and_off |
|:------------------------|-----------:|-----------:|--------------------------:|-----------------------:|-------------------:|--------------------------:|----------------------------------:|
| m_proxy_gt2h            |         19 |      0.001 |                     57.89 |                  0.087 |                 11 |                      4.35 |                              0.01 |
| m_proxy_negative        |       1012 |      0.049 |                     30.73 |                  0.073 |                311 |                      0.31 |                              0.2  |
| m_aobt3_eobt1_gt1h      |       3197 |      0.155 |                     29.28 |                  0.042 |                936 |                      2.32 |                              1.33 |
| m_aobt3_1h_before_sched |       1200 |      0.058 |                     27.75 |                  0.072 |                333 |                      0.01 |                              0    |
| m_type_mismatch         |       7013 |      0.34  |                      2.45 |                  0.08  |                172 |                      0.27 |                              0.12 |
| m_sched_lobt_gt3h       |       8807 |      0.427 |                      0.51 |                  0.086 |                 45 |                      3.3  |                              0.01 |
| m_late6h                |       2252 |      0.109 |                      0.31 |                  0.087 |                  7 |                      5.32 |                              0    |
| m_lirf                  |     159216 |      7.719 |                      0.29 |                  0.071 |                457 |                     17.11 |                              1.69 |
| m_ades_mismatch         |      29160 |      1.414 |                      0.15 |                  0.087 |                 45 |                      0.88 |                              0.1  |
| m_callsign_neq_flight   |     557756 |     27.043 |                      0.06 |                  0.099 |                315 |                      6.77 |                              0.61 |
