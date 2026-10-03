# Check: p6_lirf_matched_late_echo_by_mvtsec0

Run at 2026-10-03T06:06:19+00:00 (UTC), duckdb 1.5.6.

LIRF NM-matched 2025 departures with NM delay (AOBT_3-SCHED) > 10 min: echo share (|BLOCK-SCHED|<=60 s) by MVT on a whole minute and mangled flight number.

```sql
WITH b AS (SELECT c.mvt_id, c.month, c.y, abs(epoch(c.t_block)-epoch(c.t_sched)) <= 60 echo, (epoch(c.t_aobt3)-epoch(c.t_sched)) nm_delay,
   epoch(c.t_mvt)-epoch(c.t_sched) d_sched, epoch(c.t_mvt)-epoch(c.t_aobt3) px, second(c.t_mvt)=0 mvt_s0, (CASE WHEN flight_mvt IS NULL THEN 'null'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{3}[0-9][0-9A-Z]{0,4}$') THEN 'icao3+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,1)=substr(flight_mvt,3,1) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,2)=substr(flight_mvt,2,2) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') THEN 'letters4+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z0-9]{2}[0-9]+[A-Z]?$') THEN 'iata2+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]+$') THEN 'letters_only(reg?)'
  ELSE 'other' END)='mangled_repeat' mangled,
   coalesce(c.operator,'?') op, c.stand, hour(c.t_mvt) hr, c.runway
   FROM clean_dep c WHERE c.ds='train' AND c.airport='LIRF' AND NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL AND epoch(c.t_aobt3)-epoch(c.t_sched) > 600) SELECT mvt_s0, mangled, count(*) n, round(100*avg(echo::INT),1) pct_echo FROM b GROUP BY ALL ORDER BY ALL
```

4 rows

| mvt_s0   | mangled   |     n |   pct_echo |
|:---------|:----------|------:|-----------:|
| False    | False     | 64624 |        9.2 |
| False    | True      |  1242 |        8.6 |
| True     | False     |  5892 |        9.3 |
| True     | True      |   106 |       10.4 |
