# Check: p1_x_error_by_ymag

Run at 2026-10-02T10:13:13+00:00 (UTC), duckdb 1.5.6.

```sql
-- where do big naive errors come from: label (y) extreme or x extreme?
WITH d AS (SELECT TAXITIME_SEC_mvt y, epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt) x FROM raw_training WHERE PHASE_mvt='DEP' AND AOBT_3_flt IS NOT NULL)
SELECT CASE WHEN abs(x-y)<=60 THEN 'a <=60' WHEN abs(x-y)<=300 THEN 'b 60-300' WHEN abs(x-y)<=900 THEN 'c 300-900' ELSE 'd >900' END err_bin,
 count(*) n, round(100.0*count(*)/sum(count(*)) over(),2) pct_rows, round(100.0*sum((x-y)^2)/sum(sum((x-y)^2)) over(),2) pct_sq_err,
 round(median(y)) med_y, round(median(x)) med_x
FROM d GROUP BY 1 ORDER BY 1
```

4 rows

| err_bin   |       n |   pct_rows |   pct_sq_err |   med_y |   med_x |
|:----------|--------:|-----------:|-------------:|--------:|--------:|
| a <=60    |  433576 |      21.02 |         0.21 |     864 |     868 |
| b 60-300  | 1106066 |      53.63 |        11.09 |     905 |     912 |
| c 300-900 |  473592 |      22.96 |        37.99 |    1011 |    1151 |
| d >900    |   49343 |       2.39 |        50.7  |    1854 |    1020 |
