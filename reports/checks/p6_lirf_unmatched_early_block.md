# Check: p6_lirf_unmatched_early_block

Run at 2026-10-03T05:55:57+00:00 (UTC), duckdb 1.5.6.

LIRF NM-unmatched 2025 departures whose off-block is 2 min-3 h BEFORE schedule: histogram of BLOCK-SCHED (10-min bins), label and hold-out error share.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), d AS (SELECT mvt_id, epoch(t_block)-epoch(t_sched) bs, epoch(t_mvt)-epoch(t_sched) d_sched, y, month FROM clean_dep
  WHERE ds='train' AND airport='LIRF' AND f_no_nm_match AND epoch(t_block)-epoch(t_sched) BETWEEN -10800 AND -121)
SELECT round(bs/600)*10 AS bs_10min, count(*) n, round(median(d_sched)) med_dsched, round(median(y)) med_y,
  round(median(y - (bs + 0)) ) med_y_minus_bs, count(o.mvt_id) n_hold, round(100*sum(o.se)/any_value(tot_se),2) pct_sq_err
FROM d LEFT JOIN oof o USING (mvt_id), tot GROUP BY 1 ORDER BY 1
```

14 rows

|   bs_10min |   n |   med_dsched |   med_y |   med_y_minus_bs |   n_hold |   pct_sq_err |
|-----------:|----:|-------------:|--------:|-----------------:|---------:|-------------:|
|       -170 |   1 |         1441 |   11822 |            22203 |        0 |       nan    |
|       -120 |   8 |          898 |    8063 |            15244 |        3 |         0.06 |
|       -110 |   3 |         1740 |    8041 |            14342 |        1 |         0.02 |
|       -100 |   6 |         2097 |    7945 |            13792 |        1 |         0.07 |
|        -90 |   2 |         2672 |    7984 |            13296 |        0 |       nan    |
|        -80 |   3 |         3363 |    8107 |            12851 |        2 |         0.05 |
|        -70 |   6 |          537 |    4624 |             8699 |        1 |         0    |
|        -60 |   5 |         1022 |    4685 |             8348 |        2 |         1.44 |
|        -50 |   1 |         3543 |    6786 |            10029 |        0 |       nan    |
|        -40 |   1 |        -1625 |     591 |             2807 |        0 |       nan    |
|        -30 |   4 |         2458 |    4257 |             6056 |        1 |         0    |
|        -20 |   8 |         -506 |     612 |             1968 |        1 |         0    |
|        -10 |  11 |          358 |     716 |             1491 |        3 |         0.12 |
|          0 |   5 |         4561 |    4683 |             4805 |        2 |         0.03 |
