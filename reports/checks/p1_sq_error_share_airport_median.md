# Check: p1_sq_error_share_airport_median

Run at 2026-10-02T10:18:21+00:00 (UTC), duckdb 1.5.6.

```sql
-- Share of squared error from top-1% rows under the per-airport-median baseline (in-sample, all 2025 DEP)
WITH m AS (SELECT airport, median(y) med FROM clean_dep WHERE ds='train' GROUP BY 1),
e AS (SELECT d.airport, d.f_no_nm_match, (y-med)^2 se, y FROM clean_dep d JOIN m USING (airport) WHERE ds='train'),
r AS (SELECT *, percent_rank() OVER (ORDER BY se DESC) pr FROM e)
SELECT round(sqrt(avg(se)),1) rmse_all,
       round(100*sum(se) FILTER (WHERE pr < 0.01)/sum(se),1) pct_sq_top1pct,
       round(100*sum(se) FILTER (WHERE y > 3*3600)/sum(se),1) pct_sq_y_gt3h,
       round(100*sum(se) FILTER (WHERE f_no_nm_match)/sum(se),1) pct_sq_nomatch,
       round(100.0*avg(f_no_nm_match::INT),2) pct_rows_nomatch,
       round(sqrt(avg(se) FILTER (WHERE y <= 3*3600)),1) rmse_excl_gt3h
FROM r
```

1 rows

|   rmse_all |   pct_sq_top1pct |   pct_sq_y_gt3h |   pct_sq_nomatch |   pct_rows_nomatch |   rmse_excl_gt3h |
|-----------:|-----------------:|----------------:|-----------------:|-------------------:|-----------------:|
|      519.5 |             63.9 |            42.1 |             46.5 |               1.08 |            395.4 |
