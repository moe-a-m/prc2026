# Check: p6_lirf_dsched_by_month

Run at 2026-10-03T05:53:49+00:00 (UTC), duckdb 1.5.6.

LIRF departures: distribution of MVT-SCHED (s) by month and NM-match status. Tests whether the LIRF schedule column is in local time or delayed for unmatched rows.

```sql
SELECT ds, month, f_no_nm_match AS unmatched, count(*) n,
  round(quantile_cont(epoch(t_mvt)-epoch(t_sched),0.10)) q10_dsched,
  round(median(epoch(t_mvt)-epoch(t_sched))) med_dsched,
  round(quantile_cont(epoch(t_mvt)-epoch(t_sched),0.90)) q90_dsched,
  round(median(y)) med_y,
  round(100*avg((abs(epoch(t_block)-epoch(t_sched))<=60)::INT),1) pct_block_eq_sched60,
  round(100*avg((actype_mvt IS NULL)::INT),1) pct_actype_missing
FROM clean_dep WHERE airport='LIRF' GROUP BY ALL ORDER BY unmatched, ds, month
```

28 rows

| ds    | month               | unmatched   |     n |   q10_dsched |   med_dsched |   q90_dsched |   med_y |   pct_block_eq_sched60 |   pct_actype_missing |
|:------|:--------------------|:------------|------:|-------------:|-------------:|-------------:|--------:|-----------------------:|---------------------:|
| rank  | 2026-01-01 00:00:00 | False       | 10954 |          419 |         1145 |         3299 |     nan |                  nan   |                    0 |
| rank  | 2026-07-01 00:00:00 | False       | 15562 |          774 |         1864 |         4801 |     nan |                  nan   |                    0 |
| train | 2025-01-01 00:00:00 | False       | 11257 |          478 |         1144 |         2816 |    1009 |                   22.3 |                    0 |
| train | 2025-02-01 00:00:00 | False       | 10645 |          481 |         1145 |         2705 |     959 |                   23.3 |                    0 |
| train | 2025-03-01 00:00:00 | False       | 12485 |          483 |         1203 |         2815 |    1012 |                   23.8 |                    0 |
| train | 2025-04-01 00:00:00 | False       | 13959 |          545 |         1379 |         3185 |    1030 |                   20.1 |                    0 |
| train | 2025-05-01 00:00:00 | False       | 14442 |          599 |         1435 |         3300 |    1031 |                   20.4 |                    0 |
| train | 2025-06-01 00:00:00 | False       | 14511 |          779 |         1742 |         4196 |    1082 |                   18.8 |                    0 |
| train | 2025-07-01 00:00:00 | False       | 14874 |          836 |         2038 |         5096 |    1130 |                   16.4 |                    0 |
| train | 2025-08-01 00:00:00 | False       | 15262 |          719 |         1683 |         4078 |    1071 |                   19.2 |                    0 |
| train | 2025-09-01 00:00:00 | False       | 14499 |          664 |         1624 |         3842 |    1031 |                   18.2 |                    0 |
| train | 2025-10-01 00:00:00 | False       | 14027 |          654 |         1501 |         3660 |    1031 |                   20.2 |                    0 |
| train | 2025-11-01 00:00:00 | False       | 11276 |          423 |         1194 |         2815 |     963 |                   22.6 |                    0 |
| train | 2025-12-01 00:00:00 | False       | 11980 |          480 |         1257 |         3117 |     971 |                   23   |                    0 |
| rank  | 2026-01-01 00:00:00 | True        |   107 |         1191 |         7141 |        19592 |     nan |                  nan   |                  100 |
| rank  | 2026-07-01 00:00:00 | True        |   276 |         4495 |         6897 |        14461 |     nan |                  nan   |                  100 |
| train | 2025-01-01 00:00:00 | True        |    60 |         3628 |         6688 |        14332 |    1316 |                   41.7 |                  100 |
| train | 2025-02-01 00:00:00 | True        |    58 |         3746 |         6635 |        15033 |    6175 |                   75.9 |                  100 |
| train | 2025-03-01 00:00:00 | True        |    59 |         3748 |         6715 |        11018 |    7130 |                   74.6 |                  100 |
| train | 2025-04-01 00:00:00 | True        |    69 |          997 |         6715 |        13107 |    5216 |                   66.7 |                  100 |
| train | 2025-05-01 00:00:00 | True        |    99 |         4620 |         6001 |        12310 |    4974 |                   46.5 |                  100 |
| train | 2025-06-01 00:00:00 | True        |   185 |         4489 |         6666 |        11353 |    1922 |                   48.6 |                  100 |
| train | 2025-07-01 00:00:00 | True        |   337 |         4799 |         6783 |        15035 |    1447 |                   32.3 |                  100 |
| train | 2025-08-01 00:00:00 | True        |   197 |         4716 |         6662 |        13412 |    3127 |                   45.2 |                  100 |
| train | 2025-09-01 00:00:00 | True        |   168 |         4857 |         6810 |        13525 |    1445 |                   43.5 |                  100 |
| train | 2025-10-01 00:00:00 | True        |   115 |         4488 |         6006 |        10750 |    2397 |                   48.7 |                  100 |
| train | 2025-11-01 00:00:00 | True        |    52 |         4794 |         6180 |        11390 |    5733 |                   61.5 |                  100 |
| train | 2025-12-01 00:00:00 | True        |    88 |         1431 |         6898 |        11732 |    6035 |                   76.1 |                  100 |
