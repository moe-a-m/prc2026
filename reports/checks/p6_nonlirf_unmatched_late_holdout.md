# Check: p6_nonlirf_unmatched_late_holdout

Run at 2026-10-03T06:03:34+00:00 (UTC), duckdb 1.5.6.

Non-LIRF NM-unmatched departures by lateness vs schedule: 2025 label stats (no schedule echo outside LIRF), EXP-031 hold-out error, and 2026 ranking counts (EHAM separately).

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (SELECT c.mvt_id, c.airport, c.ds, c.y, epoch(c.t_mvt)-epoch(c.t_sched) d_sched,
   CASE WHEN epoch(c.t_mvt)-epoch(c.t_sched) < 3600 THEN 'a <1h' WHEN epoch(c.t_mvt)-epoch(c.t_sched) < 10800 THEN 'b 1-3h' ELSE 'c >=3h' END band
  FROM clean_dep c WHERE c.f_no_nm_match AND c.airport <> 'LIRF')
SELECT band, count(*) FILTER (ds='train') n_train2025, round(median(y) FILTER (ds='train')) med_y_2025, round(avg(y) FILTER (ds='train' AND y < 72000)) mean_y_2025_excl_dayshift,
  round(100*avg((abs(y-d_sched)<=120)::INT) FILTER (ds='train'),2) pct_echo_2025,
  count(o.mvt_id) n_hold, round(avg(o.pred)) mean_pred_hold, round(avg(o.y_oof)) mean_y_hold, round(sqrt(avg(o.se))) rmse_hold,
  round(100*sum(o.se)/any_value(tot_se),2) pct_total_sq_err,
  count(*) FILTER (ds='rank') n_rank2026, count(*) FILTER (ds='rank' AND airport='EHAM') n_rank2026_eham
FROM b LEFT JOIN oof o USING (mvt_id), tot GROUP BY 1 ORDER BY 1
```

3 rows

| band   |   n_train2025 |   med_y_2025 |   mean_y_2025_excl_dayshift |   pct_echo_2025 |   n_hold |   mean_pred_hold |   mean_y_hold |   rmse_hold |   pct_total_sq_err |   n_rank2026 |   n_rank2026_eham |
|:-------|--------------:|-------------:|----------------------------:|----------------:|---------:|-----------------:|--------------:|------------:|-------------------:|-------------:|------------------:|
| a <1h  |          6608 |          730 |                         726 |           18.04 |     1113 |              730 |           850 |        3064 |              24    |         1184 |               292 |
| b 1-3h |         13224 |          983 |                        1125 |            0.19 |     3556 |             1091 |          1130 |         634 |               3.28 |         3123 |               617 |
| c >=3h |          1105 |         1069 |                        1363 |            0    |      300 |             1236 |          1216 |         701 |               0.34 |          593 |               297 |
