# Check: p6_lfpg_unmatched_structure

Run at 2026-10-03T05:39:36+00:00 (UTC), duckdb 1.5.6.

LFPG NM-unmatched training departures by label band.

```sql
WITH d AS (SELECT f.*, abs(epoch(c.t_block)-epoch(c.t_sched)) blk_sched_abs
           FROM feat_dep f JOIN clean_dep c USING (mvt_id) WHERE f.ds='train' AND f.airport='LFPG' AND f.nm_unmatched)
SELECT CASE WHEN y > 72000 THEN '1 y>20h' WHEN y > 10800 THEN '2 3-20h' WHEN y > 3600 THEN '3 1-3h' ELSE '4 ≤1h' END AS y_band,
  count(*) n, round(median(d_sched)) med_dsched, round(100*avg((blk_sched_abs<=60)::INT),1) pct_block_eq_sched,
  round(100*avg((d_sched > 3*3600)::INT),1) pct_late3h, round(100*avg(actype_mvt_missing::INT),1) pct_actype_missing,
  mode(flt_prefix) top_prefix, round(median(y)) med_y
FROM d GROUP BY 1 ORDER BY 1
```

4 rows

| y_band   |    n |   med_dsched |   pct_block_eq_sched |   pct_late3h |   pct_actype_missing | top_prefix   |   med_y |
|:---------|-----:|-------------:|---------------------:|-------------:|---------------------:|:-------------|--------:|
| 1 y>20h  |    1 |         1740 |                  0   |          0   |                  0   | EJU          |   84240 |
| 2 3-20h  |    1 |         2043 |                  0   |          0   |                  0   | EJU          |   58206 |
| 3 1-3h   |   44 |         8733 |                  9.1 |         15.9 |                  0   | AFR          |    4742 |
| 4 ≤1h    | 3719 |         5821 |                  0.6 |          6.7 |                  0.1 | AFR          |    1020 |
