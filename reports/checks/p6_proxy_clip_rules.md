# Check: p6_proxy_clip_rules

Run at 2026-10-03T05:58:39+00:00 (UTC), duckdb 1.5.6.

Exploratory post-hoc rules on EXP-031 hold-out predictions: clip the prediction to within ±60/±30 min of the raw NM proxy MVT-AOBT_3 when the proxy is not suspect (AOBT_3 present, |AOBT_3-EOBT_1|<=1 h, AOBT_3 before take-off); variants restricted to flights > 3 h late and to LIRF; and a floor at 60 s. RMSE in seconds; NULL fold = Jan+Jul combined.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (
  SELECT o.mvt_id, o.fold, o.y_oof y, o.pred, o.se, c.airport, epoch(c.t_mvt)-epoch(c.t_aobt3) px,
    epoch(c.t_mvt)-epoch(c.t_sched) d_sched,
    (c.t_aobt3 IS NOT NULL AND NOT c.f_no_nm_match AND abs(epoch(c.t_aobt3) - epoch(c.t_eobt1)) <= 3600 AND epoch(c.t_mvt) >= epoch(c.t_aobt3)) AS px_ok
  FROM oof o JOIN clean_dep c USING (mvt_id)),
r AS (SELECT *,
  CASE WHEN px_ok THEN least(greatest(pred, px-3600), px+3600) ELSE pred END r_clip60_all,
  CASE WHEN px_ok THEN least(greatest(pred, px-1800), px+1800) ELSE pred END r_clip30_all,
  CASE WHEN px_ok AND d_sched > 10800 THEN least(greatest(pred, px-1800), px+1800) ELSE pred END r_clip30_late3h,
  CASE WHEN px_ok AND d_sched > 10800 AND airport='LIRF' THEN least(greatest(pred, px-1800), px+1800) ELSE pred END r_clip30_late3h_lirf,
  greatest(pred, 60) r_floor60
 FROM b)
SELECT fold, count(*) n,
  count(*) FILTER (pred < 0) n_pred_negative, count(*) FILTER (pred < 60) n_pred_lt60,
  round(sqrt(avg(se)),2) rmse_now,
  round(sqrt(avg((r_clip60_all-y)^2)),2) rmse_clip60_all, count(*) FILTER (r_clip60_all<>pred) n_chg60,
  round(sqrt(avg((r_clip30_all-y)^2)),2) rmse_clip30_all, count(*) FILTER (r_clip30_all<>pred) n_chg30,
  round(sqrt(avg((r_clip30_late3h-y)^2)),2) rmse_clip30_late3h, count(*) FILTER (r_clip30_late3h<>pred) n_chg30l,
  round(sqrt(avg((r_clip30_late3h_lirf-y)^2)),2) rmse_clip30_late3h_lirf, count(*) FILTER (r_clip30_late3h_lirf<>pred) n_chg30ll,
  round(sqrt(avg((r_floor60-y)^2)),2) rmse_floor60
FROM r GROUP BY ROLLUP(fold) ORDER BY fold
```

3 rows

| fold   |      n |   n_pred_negative |   n_pred_lt60 |   rmse_now |   rmse_clip60_all |   n_chg60 |   rmse_clip30_all |   n_chg30 |   rmse_clip30_late3h |   n_chg30l |   rmse_clip30_late3h_lirf |   n_chg30ll |   rmse_floor60 |
|:-------|-------:|------------------:|--------------:|-----------:|------------------:|----------:|------------------:|----------:|---------------------:|-----------:|--------------------------:|------------:|---------------:|
| jan    | 153706 |                38 |            49 |     347.72 |            347.73 |        10 |            348.74 |       216 |               347.66 |          2 |                    347.66 |           1 |         347.71 |
| jul    | 190713 |                74 |            89 |     361.72 |            341.29 |       107 |            345.91 |       830 |               339.76 |         46 |                    340.14 |          40 |         360.68 |
| nan    | 344419 |               112 |           138 |     355.54 |            344.18 |       117 |            347.18 |      1046 |               343.31 |         48 |                    343.51 |          41 |         354.95 |
