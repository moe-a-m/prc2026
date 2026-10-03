# Check: p6_lirf_matched_mangled

Run at 2026-10-03T06:05:11+00:00 (UTC), duckdb 1.5.6.

LIRF NM-matched departures: mangled flight numbers vs regular ones — echo share, NM-proxy failure, lateness, EXP-031 hold-out error vs raw proxy.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (SELECT c.mvt_id, c.ds, (CASE WHEN flight_mvt IS NULL THEN 'null'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{3}[0-9][0-9A-Z]{0,4}$') THEN 'icao3+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,1)=substr(flight_mvt,3,1) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,2)=substr(flight_mvt,2,2) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') THEN 'letters4+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z0-9]{2}[0-9]+[A-Z]?$') THEN 'iata2+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]+$') THEN 'letters_only(reg?)'
  ELSE 'other' END)='mangled_repeat' mangled, c.y, epoch(c.t_mvt)-epoch(c.t_sched) d_sched,
    epoch(c.t_mvt)-epoch(c.t_aobt3) px FROM clean_dep c WHERE c.airport='LIRF' AND NOT c.f_no_nm_match)
SELECT mangled, count(*) FILTER (ds='train') n_train, round(100*avg((abs(y-d_sched)<=120 AND d_sched>3600)::INT) FILTER (ds='train'),2) pct_echo_late1h,
  round(100*avg((abs(y-px)>3600)::INT) FILTER (ds='train'),2) pct_proxy_off1h, round(100*avg((d_sched>10800)::INT) FILTER (ds='train'),2) pct_late3h_2025,
  round(100*avg((d_sched>10800)::INT) FILTER (ds='rank'),2) pct_late3h_2026,
  count(o.mvt_id) n_hold, round(sqrt(avg(o.se))) rmse_hold, round(100*sum(o.se)/any_value(tot_se),2) pct_total_sq_err,
  round(sqrt(avg((px-o.y_oof)^2) FILTER (o.mvt_id IS NOT NULL AND px IS NOT NULL))) rmse_raw_proxy_hold
FROM b LEFT JOIN oof o USING (mvt_id), tot GROUP BY 1
```

2 rows

| mangled   |   n_train |   pct_echo_late1h |   pct_proxy_off1h |   pct_late3h_2025 |   pct_late3h_2026 |   n_hold |   rmse_hold |   pct_total_sq_err |   rmse_raw_proxy_hold |
|:----------|----------:|------------------:|------------------:|------------------:|------------------:|---------:|------------:|-------------------:|----------------------:|
| True      |      2742 |              1.06 |              0.4  |              4.96 |              6.57 |      485 |        1205 |               1.62 |                   589 |
| False     |    156475 |              0.6  |              0.29 |              0.5  |              0.77 |    25646 |         513 |              15.49 |                   649 |
