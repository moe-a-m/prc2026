# Check: p6_dayshift_precursors

Run at 2026-10-03T06:00:07+00:00 (UTC), duckdb 1.5.6.

Day-shifted labels (y > 20 h) vs label-free precursors: LIRF, NM match, lateness band, calendar-day shift between SCHED and MVT, SCHED within 22-02 UTC. Counts for 2025 and for the 2026 ranking set.

```sql
WITH b AS (SELECT airport='LIRF' AS lirf, f_no_nm_match unmatched,
   CASE WHEN epoch(t_mvt)-epoch(t_sched) < 3*3600 THEN 'a <3h' WHEN epoch(t_mvt)-epoch(t_sched) < 50400 THEN 'b 3-14h' ELSE 'c >=14h' END late_band,
   date_diff('day', t_sched::DATE, t_mvt::DATE) <> 0 AS day_shift_ne0,
   hour(t_sched) >= 22 OR hour(t_sched) < 2 AS sched_near_midnight,
   y > 72000 AS dayshift_label, ds FROM clean_dep)
SELECT lirf, unmatched, late_band, day_shift_ne0, count(*) FILTER (ds='train') n_train, count(*) FILTER (ds='train' AND dayshift_label) n_y_gt20h,
  round(100.0*count(*) FILTER (ds='train' AND dayshift_label)/count(*) FILTER (ds='train'),3) pct_y_gt20h,
  count(*) FILTER (ds='train' AND dayshift_label AND sched_near_midnight) n_y_gt20h_sched_near_midnight,
  count(*) FILTER (ds='rank') n_rank2026
FROM b GROUP BY ALL HAVING count(*) FILTER (ds='train') > 0 ORDER BY lirf DESC, unmatched DESC, late_band, day_shift_ne0
```

23 rows

| lirf   | unmatched   | late_band   | day_shift_ne0   |   n_train |   n_y_gt20h |   pct_y_gt20h |   n_y_gt20h_sched_near_midnight |   n_rank2026 |
|:-------|:------------|:------------|:----------------|----------:|------------:|--------------:|--------------------------------:|-------------:|
| True   | True        | a <3h       | False           |      1231 |           0 |         0     |                               0 |          304 |
| True   | True        | a <3h       | True            |        13 |           0 |         0     |                               0 |            5 |
| True   | True        | b 3-14h     | False           |       186 |           0 |         0     |                               0 |           53 |
| True   | True        | b 3-14h     | True            |        37 |           1 |         2.703 |                               0 |           15 |
| True   | True        | c >=14h     | False           |         3 |           1 |        33.333 |                               0 |            1 |
| True   | True        | c >=14h     | True            |        17 |          11 |        64.706 |                               0 |            5 |
| True   | False       | a <3h       | False           |    158239 |           0 |         0     |                               0 |        26274 |
| True   | False       | a <3h       | True            |        52 |           0 |         0     |                               0 |           12 |
| True   | False       | b 3-14h     | False           |       869 |           0 |         0     |                               0 |          217 |
| True   | False       | b 3-14h     | True            |        56 |           0 |         0     |                               0 |           12 |
| True   | False       | c >=14h     | True            |         1 |           1 |       100     |                               0 |            1 |
| False  | True        | a <3h       | False           |     19771 |           2 |         0.01  |                               0 |         4292 |
| False  | True        | a <3h       | True            |        61 |           0 |         0     |                               0 |           15 |
| False  | True        | b 3-14h     | False           |      1011 |           0 |         0     |                               0 |          566 |
| False  | True        | b 3-14h     | True            |        59 |           0 |         0     |                               0 |           15 |
| False  | True        | c >=14h     | False           |         2 |           0 |         0     |                               0 |            2 |
| False  | True        | c >=14h     | True            |        33 |           0 |         0     |                               0 |           10 |
| False  | False       | a <3h       | False           |   1888956 |           0 |         0     |                               0 |       309483 |
| False  | False       | a <3h       | True            |      2539 |           0 |         0     |                               0 |          560 |
| False  | False       | b 3-14h     | False           |     10135 |           0 |         0     |                               0 |         2652 |
| False  | False       | b 3-14h     | True            |      1352 |           0 |         0     |                               0 |          258 |
| False  | False       | c >=14h     | False           |        29 |           0 |         0     |                               0 |           12 |
| False  | False       | c >=14h     | True            |       395 |           0 |         0     |                               0 |           77 |
