# Check: p1_defect_near_echo

Run at 2026-10-02T10:18:20+00:00 (UTC), duckdb 1.5.6.

Near-echo = |BLOCK − SCHED| ≤ 10 s.

```sql
WITH d AS (SELECT *, abs(epoch(t_block)-epoch(t_sched)) e_s, epoch(t_mvt)-epoch(t_sched) dsch FROM clean_dep WHERE ds='train'),
t AS (SELECT sum(y::DOUBLE^2) tot FROM d)  -- squared error of predicting 0 is meaningless; use the per-airport-median baseline below
SELECT airport, count(*) n,
  sum((e_s <= 10)::INT) n_echo10, round(100.0*avg((e_s<=10)::INT),2) pct_echo10,
  sum((e_s <= 10 AND f_no_nm_match)::INT) n_echo10_nomatch,
  sum((e_s <= 10 AND dsch > 3600)::INT) n_echo10_late1h,
  sum((y > 3600)::INT) n_y_gt1h, sum((y > 3600 AND e_s <= 10)::INT) n_y_gt1h_echo,
  sum((y > 3600 AND f_no_nm_match)::INT) n_y_gt1h_nomatch,
  round(100.0*avg(f_no_nm_match::INT),2) pct_nomatch
FROM d GROUP BY ROLLUP(airport) ORDER BY airport NULLS LAST
```

11 rows

| airport   |       n |   n_echo10 |   pct_echo10 |   n_echo10_nomatch |   n_echo10_late1h |   n_y_gt1h |   n_y_gt1h_echo |   n_y_gt1h_nomatch |   pct_nomatch |
|:----------|--------:|-----------:|-------------:|-------------------:|------------------:|-----------:|----------------:|-------------------:|--------------:|
| EDDF      |  230141 |       2829 |         1.23 |                  3 |                 0 |         73 |               0 |                  3 |          0.85 |
| EDDM      |  167334 |       8341 |         4.98 |                  0 |                 1 |         59 |               1 |                 11 |          0.6  |
| EGLL      |  239546 |      11668 |         4.87 |                  4 |                28 |        728 |              28 |                 45 |          0.59 |
| EHAM      |  247951 |       3105 |         1.25 |                112 |                 1 |         82 |               1 |                 11 |          1.65 |
| LEBL      |  179705 |      10086 |         5.61 |                 34 |                 0 |          1 |               0 |                  0 |          1.03 |
| LEMD      |  212242 |       9470 |         4.46 |                  2 |                 0 |          0 |               0 |                  0 |          0.44 |
| LFPG      |  239552 |       9883 |         4.13 |                 13 |                10 |        396 |              10 |                 46 |          1.57 |
| LIRF      |  160704 |      29090 |        18.1  |                720 |              1618 |       1967 |            1618 |                745 |          0.93 |
| LSZH      |  134907 |       1531 |         1.13 |                 52 |                 1 |         26 |               1 |                  5 |          1.7  |
| LTFM      |  272965 |      14046 |         5.15 |                181 |                17 |        794 |              17 |                221 |          1.33 |
| nan       | 2085047 |     100049 |         4.8  |               1121 |              1676 |       4126 |            1676 |               1087 |          1.08 |
