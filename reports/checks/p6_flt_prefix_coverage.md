# Check: p6_flt_prefix_coverage

Run at 2026-10-03T06:04:57+00:00 (UTC), duckdb 1.5.6.

Coverage of the carrier key flt_prefix (regexp '^[A-Z]{{3}}' on FLIGHT_mvt) and NM operator by flight-number class and NM match; EXP-031 hold-out error share.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (SELECT c.mvt_id, c.airport, c.ds, c.f_no_nm_match um, CASE WHEN flight_mvt IS NULL THEN 'null'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{3}[0-9][0-9A-Z]{0,4}$') THEN 'icao3+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,1)=substr(flight_mvt,3,1) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,2)=substr(flight_mvt,2,2) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') THEN 'letters4+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z0-9]{2}[0-9]+[A-Z]?$') THEN 'iata2+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]+$') THEN 'letters_only(reg?)'
  ELSE 'other' END fn_class, f.flt_prefix, c.operator
   FROM clean_dep c JOIN feat_dep f USING (mvt_id))
SELECT um AS unmatched, fn_class, count(*) FILTER (ds='train') n_train, count(*) FILTER (ds='rank') n_rank,
  round(100*avg((coalesce(flt_prefix,'')='')::INT),1) pct_prefix_empty, round(100*avg((operator IS NULL)::INT),1) pct_operator_null,
  mode(airport) top_airport, count(o.mvt_id) n_hold, round(sqrt(avg(o.se))) rmse_hold, round(100*sum(o.se)/any_value(tot_se),2) pct_total_sq_err
FROM b LEFT JOIN oof o USING (mvt_id), tot GROUP BY ALL ORDER BY unmatched DESC, n_train DESC
```

14 rows

| unmatched   | fn_class           |   n_train |   n_rank |   pct_prefix_empty |   pct_operator_null | top_airport   |   n_hold |   rmse_hold |   pct_total_sq_err |
|:------------|:-------------------|----------:|---------:|-------------------:|--------------------:|:--------------|---------:|------------:|-------------------:|
| True        | icao3+num          |     16654 |     3660 |                0   |                 100 | LFPG          |     3955 |        2113 |              40.55 |
| True        | iata2+num          |      3869 |     1284 |              100   |                 100 | EHAM          |     1045 |         448 |               0.48 |
| True        | letters_only(reg?) |      1333 |      197 |                0   |                 100 | LSZH          |      253 |         937 |               0.51 |
| True        | letters4+num       |       228 |       47 |                0   |                 100 | EHAM          |       34 |         267 |               0.01 |
| True        | mangled_repeat     |       167 |       48 |                0   |                 100 | LIRF          |       40 |       10433 |              10    |
| True        | other              |       108 |       24 |               97.7 |                 100 | LSZH          |       34 |        1032 |               0.08 |
| True        | null               |        65 |       23 |              100   |                 100 | LIRF          |        5 |        1362 |               0.02 |
| False       | icao3+num          |   1609559 |   268979 |                0   |                   0 | LTFM          |   265093 |         260 |              41.18 |
| False       | iata2+num          |    436945 |    67927 |              100   |                   0 | EHAM          |    71114 |         178 |               5.19 |
| False       | letters_only(reg?) |      9213 |     1456 |                0   |                   0 | EHAM          |     1547 |         236 |               0.2  |
| False       | other              |      3489 |      644 |               98.5 |                   0 | LSZH          |      696 |         243 |               0.09 |
| False       | mangled_repeat     |      2756 |      434 |                0   |                   0 | LIRF          |      488 |        1202 |               1.62 |
| False       | letters4+num       |       538 |       83 |                0   |                   0 | EHAM          |       95 |         237 |               0.01 |
| False       | null               |       123 |       35 |              100   |                   0 | LIRF          |       20 |        1099 |               0.06 |
