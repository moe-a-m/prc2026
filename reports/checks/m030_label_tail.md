# Check: m030_label_tail

Run at 2026-10-06T10:58:20+00:00 (UTC), duckdb 1.5.6.

2025 training departures: labels > 3 h and their share of squared deviation from the per-airport median (M-030 motivation).

```sql
SELECT count(*) n, count(*) FILTER (WHERE y>10800) n_gt3h,
 round(100.0*count(*) FILTER (WHERE y>10800)/count(*),3) pct_gt3h,
 round(100*sum(CASE WHEN y>10800 THEN (y-med)^2 END)/sum((y-med)^2),1) pct_sq_dev_gt3h,
 count(*) FILTER (WHERE y>10800 AND airport='LIRF') n_gt3h_lirf
FROM (SELECT airport, y, median(y) OVER (PARTITION BY airport) med FROM feat_dep WHERE ds='train')
```

1 rows

|           n |   n_gt3h |   pct_gt3h |   pct_sq_dev_gt3h |   n_gt3h_lirf |
|------------:|---------:|-----------:|------------------:|--------------:|
| 2.08505e+06 |      202 |       0.01 |              42.1 |           188 |
