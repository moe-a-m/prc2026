# Check: p6_lirf_unmatched_regimes_by_band

Run at 2026-10-03T05:56:33+00:00 (UTC), duckdb 1.5.6.

LIRF NM-unmatched 2025 departures: three label regimes (echo |y-d_sched|<=120 s; day-minus y in [20h,28h] not echo; normal) by lateness band.

```sql
WITH b AS (SELECT mvt_id, month, y, epoch(t_mvt)-epoch(t_sched) d_sched FROM clean_dep WHERE ds='train' AND airport='LIRF' AND f_no_nm_match), r AS (SELECT *, CASE WHEN abs(y - d_sched) <= 120 THEN 'echo' WHEN y BETWEEN 72000 AND 100800 THEN 'dayminus' ELSE 'normal' END reg, CASE WHEN d_sched < 10800 THEN '0 <3h' WHEN d_sched < 21600 THEN '1 3-6h' WHEN d_sched < 50400 THEN '2 6-14h' ELSE '3 >=14h' END band FROM b)
SELECT band, count(*) n, round(100*avg((reg='echo')::INT),1) pct_echo, round(100*avg((reg='dayminus')::INT),1) pct_dayminus,
  round(100*avg((reg='normal')::INT),1) pct_normal, round(avg(y) FILTER (reg='normal')) mean_y_normal,
  round(avg(y-86400) FILTER (reg='dayminus')) mean_y_minus_86400_dayminus
FROM r GROUP BY 1 ORDER BY 1
```

4 rows

| band    |    n |   pct_echo |   pct_dayminus |   pct_normal |   mean_y_normal |   mean_y_minus_86400_dayminus |
|:--------|-----:|-----------:|---------------:|-------------:|----------------:|------------------------------:|
| 0 <3h   | 1244 |       44.9 |            0   |         55.1 |            1561 |                           nan |
| 1 3-6h  |  180 |       62.8 |            0.6 |         36.7 |            1430 |                           768 |
| 2 6-14h |   43 |       97.7 |            0   |          2.3 |            1078 |                           nan |
| 3 >=14h |   20 |       45   |           55   |          0   |             nan |                          1136 |
