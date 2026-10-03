# Check: p6_lirf_unmatched_echo_by_dsched

Run at 2026-10-03T05:54:24+00:00 (UTC), duckdb 1.5.6.

LIRF NM-unmatched 2025 departures: echo share (|BLOCK-SCHED|<=60 s) and EXP-031 hold-out squared-error share by MVT-SCHED band.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof),
d AS (SELECT c.mvt_id, c.y, epoch(c.t_mvt)-epoch(c.t_sched) d_sched,
        abs(epoch(c.t_block)-epoch(c.t_sched)) <= 60 AS echo
      FROM clean_dep c WHERE c.ds='train' AND c.airport='LIRF' AND c.f_no_nm_match)
SELECT CASE WHEN d_sched < 0 THEN 'a <0' WHEN d_sched < 3600 THEN 'b 0-1h' WHEN d_sched < 5400 THEN 'c 1-1.5h'
  WHEN d_sched < 7200 THEN 'd 1.5-2h' WHEN d_sched < 10800 THEN 'e 2-3h' WHEN d_sched < 21600 THEN 'f 3-6h' ELSE 'g >6h' END AS dsched_band, count(*) n_train2025, round(100*avg(echo::INT),1) pct_echo,
  round(median(y) FILTER (NOT echo)) med_y_nonecho,
  count(o.mvt_id) n_holdout, round(100*sum(o.se)/any_value(tot_se),2) pct_total_sq_err,
  round(sqrt(avg(o.se))) rmse_holdout
FROM d LEFT JOIN oof o USING (mvt_id), tot GROUP BY 1 ORDER BY 1
```

7 rows

| dsched_band   |   n_train2025 |   pct_echo |   med_y_nonecho |   n_holdout |   pct_total_sq_err |   rmse_holdout |
|:--------------|--------------:|-----------:|----------------:|------------:|-------------------:|---------------:|
| a <0          |            16 |        0   |             606 |           5 |               0.02 |           1200 |
| b 0-1h        |            96 |       47.9 |            6604 |          17 |               0.35 |           3006 |
| c 1-1.5h      |           290 |       28.6 |             955 |          75 |               0.46 |           1642 |
| d 1.5-2h      |           458 |       42.8 |            1083 |         119 |               1.11 |           2017 |
| e 2-3h        |           384 |       60.4 |            1027 |          98 |               2.36 |           3240 |
| f 3-6h        |           180 |       62.8 |            1139 |          62 |               6.31 |           6658 |
| g >6h         |            63 |       81   |           87421 |          21 |              13.41 |          16677 |
