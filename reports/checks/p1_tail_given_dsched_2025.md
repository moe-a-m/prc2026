# Check: p1_tail_given_dsched_2025

Run at 2026-10-02T10:43:05+00:00 (UTC), duckdb 1.5.6.

```sql
-- In 2025, when take-off is >3 h after schedule, how often is the label an echo (y ≈ d_sched)?
SELECT airport, nm_unmatched, count(*) n,
  round(100.0*avg((abs(y - d_sched) <= 60)::INT),1) pct_y_eq_dsched,
  round(100.0*avg((y > 3600)::INT),1) pct_y_gt1h, round(median(y)) med_y
FROM feat_dep WHERE ds='train' AND d_sched > 3*3600 GROUP BY ALL ORDER BY airport, nm_unmatched
```

20 rows

| airport   | nm_unmatched   |    n |   pct_y_eq_dsched |   pct_y_gt1h |   med_y |
|:----------|:---------------|-----:|------------------:|-------------:|--------:|
| EDDF      | False          | 1462 |               0   |          0.2 |    1038 |
| EDDF      | True           |  140 |               0   |          0.7 |    1074 |
| EDDM      | False          |  382 |               0   |          0.8 |     849 |
| EDDM      | True           |   31 |               0   |          0   |     851 |
| EGLL      | False          | 1104 |               0.1 |          1   |    1433 |
| EGLL      | True           |  118 |               0   |          2.5 |    1390 |
| EHAM      | False          | 1664 |               0   |          0.1 |     855 |
| EHAM      | True           |  218 |               0   |          0.9 |     797 |
| LEBL      | False          | 1072 |               0   |          0   |     990 |
| LEBL      | True           |  161 |               0   |          0   |    1080 |
| LEMD      | False          | 1261 |               0   |          0   |    1082 |
| LEMD      | True           |   52 |               0   |          0   |    1146 |
| LFPG      | False          | 1774 |               0   |          1.5 |    1017 |
| LFPG      | True           |  256 |               0   |          2.7 |    1080 |
| LIRF      | False          |  925 |               0.6 |          2.1 |    1131 |
| LIRF      | True           |  243 |              67.5 |         73.3 |   13556 |
| LSZH      | False          |  322 |               0   |          0.6 |     787 |
| LSZH      | True           |   43 |               0   |          0   |     776 |
| LTFM      | False          | 2858 |               0   |          1.6 |     953 |
| LTFM      | True           |   85 |               0   |         40   |    1554 |
