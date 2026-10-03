# Check: p6_dayshift_rows_all

Run at 2026-10-03T05:55:08+00:00 (UTC), duckdb 1.5.6.

All 2025 departures with label y > 20 h (day-shifted labels): airport, match status, lateness vs schedule, NM proxy, EXP-031 hold-out prediction.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof)
SELECT c.airport, c.f_no_nm_match unmatched, c.month, c.flight_mvt,
  round((epoch(c.t_mvt)-epoch(c.t_sched))/3600,2) d_sched_h, round(c.y/3600,2) y_h,
  round((epoch(c.t_mvt)-epoch(c.t_aobt3))/60,1) d_aobt3_min,
  c.y - 86400 AS y_minus_1day_s,
  date_diff('day', c.t_sched::DATE, c.t_mvt::DATE) day_shift, strftime(c.t_sched,'%H:%M') sched_hhmm, strftime(c.t_mvt,'%H:%M') mvt_hhmm,
  round(o.pred) pred, o.fold
FROM clean_dep c LEFT JOIN oof o USING (mvt_id)
WHERE c.ds='train' AND c.y > 72000 ORDER BY c.airport, d_sched_h
```

16 rows

| airport   | unmatched   | month               | flight_mvt   |   d_sched_h |   y_h |   d_aobt3_min |   y_minus_1day_s |   day_shift | sched_hhmm   | mvt_hhmm   |   pred | fold   |
|:----------|:------------|:--------------------|:-------------|------------:|------:|--------------:|-----------------:|------------:|:-------------|:-----------|-------:|:-------|
| LFPG      | True        | 2025-01-01 00:00:00 | EJU983W      |        0.48 | 23.4  |           nan |            -2160 |           0 | 18:25        | 18:54      |    900 | jan    |
| LIRF      | True        | 2025-06-01 00:00:00 | ITY332       |        3.25 | 24.21 |           nan |              768 |           1 | 21:59        | 01:13      |    nan | nan    |
| LIRF      | True        | 2025-09-01 00:00:00 | ITYTY630     |       14.05 | 24.32 |           nan |             1143 |           0 | 08:35        | 22:38      |    nan | nan    |
| LIRF      | True        | 2025-11-01 00:00:00 | ITYTY680     |       15.7  | 24.3  |           nan |             1080 |           1 | 21:40        | 13:22      |    nan | nan    |
| LIRF      | True        | 2025-07-01 00:00:00 | ITYTY680     |       16.27 | 24.22 |           nan |              786 |           1 | 20:30        | 12:46      |  63465 | jul    |
| LIRF      | True        | 2025-01-01 00:00:00 | EXSXS1GT     |       16.7  | 24.22 |           nan |              777 |           1 | 10:55        | 03:36      |  53248 | jan    |
| LIRF      | True        | 2025-11-01 00:00:00 | BAWW561D     |       16.83 | 24.33 |           nan |             1198 |           1 | 19:25        | 12:14      |    nan | nan    |
| LIRF      | True        | 2025-03-01 00:00:00 | SWUU1919     |       18.18 | 24.24 |           nan |              847 |           1 | 16:30        | 10:41      |    nan | nan    |
| LIRF      | True        | 2025-06-01 00:00:00 | AMX071       |       18.8  | 24.55 |           nan |             1992 |           1 | 21:15        | 16:03      |    nan | nan    |
| LIRF      | True        | 2025-07-01 00:00:00 | VOE6BB       |       20.35 | 24.27 |           nan |              961 |           1 | 20:40        | 17:01      |  62385 | jul    |
| LIRF      | True        | 2025-07-01 00:00:00 | CHHHH438     |       23.4  | 24.48 |           nan |             1732 |           1 | 09:05        | 08:28      |  63295 | jul    |
| LIRF      | True        | 2025-12-01 00:00:00 | NOSOS610     |       23.92 | 24.33 |           nan |             1205 |           1 | 18:40        | 18:35      |    nan | nan    |
| LIRF      | False       | 2025-07-01 00:00:00 | AEZ146R      |       24.17 | 24.17 |          1453 |              602 |           1 | 20:00        | 20:10      |  44494 | jul    |
| LIRF      | True        | 2025-07-01 00:00:00 | RYRR90BN     |       25.98 | 24.21 |           nan |              770 |           1 | 13:00        | 14:58      |  59862 | jul    |
| LIRF      | True        | 2025-02-01 00:00:00 | NOSOS739     |       36.43 | 36.44 |           nan |            44767 |           1 | 05:25        | 17:51      |    nan | nan    |
| LSZH      | True        | 2025-05-01 00:00:00 | NJE389D      |        0.26 | 24.26 |           nan |              941 |           0 | 14:40        | 14:55      |    nan | nan    |
