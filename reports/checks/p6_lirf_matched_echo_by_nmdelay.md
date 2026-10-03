# Check: p6_lirf_matched_echo_by_nmdelay

Run at 2026-10-03T06:05:48+00:00 (UTC), duckdb 1.5.6.

LIRF NM-matched 2025 departures: share with BLOCK within 60 s of SCHED ('echo') by NM delay (AOBT_3 - SCHED); EXP-031 hold-out RMSE for echo and non-echo rows.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (SELECT c.mvt_id, c.y, abs(epoch(c.t_block)-epoch(c.t_sched)) <= 60 echo,
    (epoch(c.t_aobt3)-epoch(c.t_sched))/60 nm_delay_min
  FROM clean_dep c WHERE c.ds='train' AND c.airport='LIRF' AND NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL)
SELECT CASE WHEN nm_delay_min < -2 THEN 'a AOBT3 before SCHED' WHEN nm_delay_min <= 2 THEN 'b on time ±2' WHEN nm_delay_min <= 10 THEN 'c 2-10 min late'
  WHEN nm_delay_min <= 30 THEN 'd 10-30' WHEN nm_delay_min <= 60 THEN 'e 30-60' WHEN nm_delay_min <= 180 THEN 'f 1-3h' ELSE 'g >3h' END nm_delay,
  count(*) n, round(100*avg(echo::INT),1) pct_echo, count(o.mvt_id) n_hold, round(sqrt(avg(o.se))) rmse_hold,
  round(sqrt(avg(o.se) FILTER (echo))) rmse_hold_echo, round(sqrt(avg(o.se) FILTER (NOT echo))) rmse_hold_nonecho,
  round(100*sum(o.se)/any_value(tot_se),2) pct_total_sq_err
FROM b LEFT JOIN oof o USING (mvt_id), tot GROUP BY 1 ORDER BY 1
```

7 rows

| nm_delay             |     n |   pct_echo |   n_hold |   rmse_hold |   rmse_hold_echo |   rmse_hold_nonecho |   pct_total_sq_err |
|:---------------------|------:|-----------:|---------:|------------:|-----------------:|--------------------:|-------------------:|
| a AOBT3 before SCHED | 26705 |       15.7 |     4042 |         689 |             1684 |                 156 |               4.4  |
| b on time ±2         | 24623 |       42.9 |     3667 |         168 |              104 |                 203 |               0.24 |
| c 2-10 min late      | 36024 |       31.2 |     5347 |         224 |              174 |                 243 |               0.62 |
| d 10-30              | 43642 |       11.2 |     7152 |         352 |              606 |                 308 |               2.03 |
| e 30-60              | 19422 |        7   |     3687 |         617 |             1640 |                 455 |               3.22 |
| f 1-3h               |  8084 |        4.5 |     2029 |         849 |             2546 |                 672 |               3.36 |
| g >3h                |   716 |        0   |      207 |        2609 |              nan |                2609 |               3.24 |
