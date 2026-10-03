# Check: p6_pred_proxy_gt1h_nonsuspect

Run at 2026-10-03T05:58:11+00:00 (UTC), duckdb 1.5.6.

EXP-031 hold-out NM-matched rows where the model departs > 1 h from a non-suspect NM proxy: breakdown.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (
  SELECT o.mvt_id, o.fold, o.y_oof y, o.pred, o.se, c.airport, epoch(c.t_mvt)-epoch(c.t_aobt3) d_aobt3,
    epoch(c.t_mvt)-epoch(c.t_sched) d_sched
  FROM oof o JOIN clean_dep c USING (mvt_id) WHERE NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL
   AND NOT (abs(epoch(c.t_aobt3) - epoch(c.t_eobt1)) > 3600 OR epoch(c.t_mvt) < epoch(c.t_aobt3))
   AND abs(o.pred - (epoch(c.t_mvt)-epoch(c.t_aobt3))) > 3600)
SELECT airport, CASE WHEN pred > d_aobt3 THEN 'model above proxy' ELSE 'model below proxy' END dir,
  d_sched > 10800 AS late3h, count(*) n, round(median(d_aobt3)) med_proxy, round(median(pred)) med_pred, round(median(y)) med_y,
  round(100*avg((abs(y-d_aobt3)<=300)::INT),1) pct_proxy_ok,
  round(100*sum(se)/any_value(tot_se),2) pct_sq_now, round(100*sum((d_aobt3-y)^2)/any_value(tot_se),2) pct_sq_proxy,
  round(100*sum(((d_aobt3+pred)/2-y)^2)/any_value(tot_se),2) pct_sq_avg
FROM b, tot GROUP BY ALL ORDER BY pct_sq_now DESC
```

8 rows

| airport   | dir               | late3h   |   n |   med_proxy |   med_pred |   med_y |   pct_proxy_ok |   pct_sq_now |   pct_sq_proxy |   pct_sq_avg |
|:----------|:------------------|:---------|----:|------------:|-----------:|--------:|---------------:|-------------:|---------------:|-------------:|
| LIRF      | model below proxy | True     |   4 |        1380 |      -3291 |    1771 |           50   |         4.32 |           0    |         1.08 |
| LIRF      | model above proxy | True     |  25 |         905 |       7295 |    1267 |           52   |         2.68 |           0.44 |         0.78 |
| LIRF      | model above proxy | False    |  41 |        1080 |       5421 |    5520 |            4.9 |         0.41 |           2.11 |         0.78 |
| EHAM      | model below proxy | True     |   1 |        7796 |       1810 |   10972 |            0   |         0.19 |           0.02 |         0.09 |
| LTFM      | model below proxy | True     |   1 |        6302 |       1640 |    1080 |            0   |         0    |           0.06 |         0.02 |
| LFPG      | model above proxy | False    |   2 |        1116 |       4879 |    5076 |            0   |         0    |           0.07 |         0.02 |
| LTFM      | model below proxy | False    |  42 |        4720 |        910 |     925 |            0   |         0    |           1.4  |         0.35 |
| LFPG      | model below proxy | False    |   1 |        5344 |       1449 |    1088 |            0   |         0    |           0.04 |         0.01 |
