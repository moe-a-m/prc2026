# Check: p6_lirf_unmatched_echo_by_marker

Run at 2026-10-03T05:59:38+00:00 (UTC), duckdb 1.5.6.

LIRF NM-unmatched departures 1-6 h late: echo share (|y-d_sched|<=120 s) by label-free marker (2025), and the count of matching 2026 ranking rows.

```sql
WITH b AS (SELECT c.*, epoch(c.t_mvt)-epoch(c.t_sched) d_sched, abs(c.y-(epoch(c.t_mvt)-epoch(c.t_sched)))<=120 echo,
   CASE WHEN flight_mvt IS NULL THEN 'null'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{3}[0-9][0-9A-Z]{0,4}$') THEN 'icao3+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,1)=substr(flight_mvt,3,1) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,2)=substr(flight_mvt,2,2) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') THEN 'letters4+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z0-9]{2}[0-9]+[A-Z]?$') THEN 'iata2+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]+$') THEN 'letters_only(reg?)'
  ELSE 'other' END fn_class, coalesce(regexp_extract(c.flight_mvt,'^[A-Z]{3}'),'?') pfx, second(c.t_mvt)=0 mvt_sec0
   FROM clean_dep c WHERE c.airport='LIRF' AND c.f_no_nm_match AND epoch(c.t_mvt)-epoch(c.t_sched) BETWEEN 3600 AND 21600), u AS (
  SELECT 'carrier' m, CASE WHEN pfx IN (SELECT pfx FROM b WHERE ds='train' GROUP BY pfx HAVING count(*)>=25) THEN pfx ELSE 'other' END v, echo, ds FROM b
  UNION ALL SELECT 'fn_class', fn_class, echo, ds FROM b
  UNION ALL SELECT 'mvt_sec0', mvt_sec0::VARCHAR, echo, ds FROM b
  UNION ALL SELECT 'dsched_band', CASE WHEN d_sched<5400 THEN '1-1.5h' WHEN d_sched<7200 THEN '1.5-2h' WHEN d_sched<10800 THEN '2-3h' ELSE '3-6h' END, echo, ds FROM b
  UNION ALL SELECT 'season', CASE WHEN month(month) IN (1,2,3,11,12) THEN 'winter' ELSE 'summer' END, echo, ds FROM b
  UNION ALL SELECT 'stand_class', CASE WHEN stand IS NULL THEN 'null' WHEN regexp_matches(stand,'^[0-9]+$') THEN 'numeric' ELSE 'alpha' END, echo, ds FROM b)
SELECT m AS marker, v AS value, count(*) FILTER (ds='train') n_train, round(100*avg(echo::INT) FILTER (ds='train'),1) pct_echo_2025,
  count(*) FILTER (ds='rank') n_rank2026
FROM u GROUP BY ALL ORDER BY marker, n_train DESC
```

26 rows

| marker      | value              |   n_train |   pct_echo_2025 |   n_rank2026 |
|:------------|:-------------------|----------:|----------------:|-------------:|
| carrier     | other              |       584 |            48.8 |          139 |
| carrier     | RYR                |       233 |            32.6 |           60 |
| carrier     | WMT                |       173 |            48   |           50 |
| carrier     | ITY                |        76 |             3.9 |           29 |
| carrier     | ISR                |        56 |           100   |            4 |
| carrier     | WZZ                |        55 |            72.7 |           13 |
| carrier     | AEZ                |        44 |            84.1 |            8 |
| carrier     | EJU                |        40 |            10   |            9 |
| carrier     | NOS                |        26 |            76.9 |            3 |
| carrier     | ?                  |        25 |            84   |            7 |
| dsched_band | 1.5-2h             |       458 |            42.8 |          104 |
| dsched_band | 2-3h               |       384 |            60.7 |          107 |
| dsched_band | 1-1.5h             |       290 |            28.6 |           63 |
| dsched_band | 3-6h               |       180 |            62.8 |           48 |
| fn_class    | icao3+num          |      1161 |            43.6 |          293 |
| fn_class    | mangled_repeat     |       118 |            77.1 |           22 |
| fn_class    | null               |        25 |            84   |            7 |
| fn_class    | letters_only(reg?) |         7 |            85.7 |            0 |
| fn_class    | other              |         1 |           100   |            0 |
| mvt_sec0    | false              |      1212 |            47.9 |          295 |
| mvt_sec0    | true               |       100 |            44   |           27 |
| season      | summer             |      1047 |            42   |          244 |
| season      | winter             |       265 |            69.8 |           78 |
| stand_class | numeric            |      1307 |            47.5 |          322 |
| stand_class | alpha              |         4 |           100   |            0 |
| stand_class | null               |         1 |             0   |            0 |
