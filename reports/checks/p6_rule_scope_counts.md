# Check: p6_rule_scope_counts

Run at 2026-10-03T06:10:08+00:00 (UTC), duckdb 1.5.6.

Scope of proposed rules R1-R3 and the proxy-suspect flag (rows; categories assigned in order, mutually exclusive): 2025 train vs 2026 ranking months.

```sql
SELECT CASE WHEN airport='LIRF' AND f_no_nm_match AND epoch(t_mvt)-epoch(t_sched) >= 50400 THEN 'R1 LIRF-unm >=14h'
            WHEN airport='LIRF' AND f_no_nm_match AND epoch(t_mvt)-epoch(t_sched) >= 21600 THEN 'R1 LIRF-unm 6-14h'
            WHEN airport='LIRF' AND f_no_nm_match AND epoch(t_mvt)-epoch(t_sched) >= 3600 THEN 'R2 LIRF-unm 1-6h'
            WHEN t_aobt3 IS NOT NULL AND NOT f_no_nm_match AND abs(epoch(t_aobt3)-epoch(t_eobt1)) <= 3600 AND epoch(t_mvt) >= epoch(t_aobt3)
                 AND epoch(t_mvt)-epoch(t_sched) > 10800 THEN 'R3 matched non-suspect >3h'
            WHEN t_aobt3 IS NOT NULL AND NOT f_no_nm_match AND (abs(epoch(t_aobt3)-epoch(t_eobt1)) > 3600 OR epoch(t_mvt) < epoch(t_aobt3)
                 OR epoch(t_aobt3) < epoch(t_sched)-3600 OR epoch(t_mvt)-epoch(t_aobt3) > 7200) THEN 'flag proxy_suspect'
            ELSE 'other' END AS rule_scope,
  count(*) FILTER (ds='train') n_train2025, count(*) FILTER (ds='rank' AND month(month)=1) n_rank_jan2026, count(*) FILTER (ds='rank' AND month(month)=7) n_rank_jul2026
FROM clean_dep GROUP BY 1 ORDER BY 1
```

6 rows

| rule_scope                 |   n_train2025 |   n_rank_jan2026 |   n_rank_jul2026 |
|:---------------------------|--------------:|-----------------:|-----------------:|
| R1 LIRF-unm 6-14h          |            43 |                9 |               11 |
| R1 LIRF-unm >=14h          |            20 |                2 |                4 |
| R2 LIRF-unm 1-6h           |          1312 |               78 |              244 |
| R3 matched non-suspect >3h |         12654 |             1757 |             1394 |
| flag proxy_suspect         |          4832 |              509 |              550 |
| other                      |       2066186 |           150364 |           189919 |
