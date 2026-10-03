# Check: p6_flightnum_pattern_by_match

Run at 2026-10-03T05:54:10+00:00 (UTC), duckdb 1.5.6.

Departure flight-number (FLIGHT_mvt) pattern classes by NM-match status, LIRF vs other airports. 'mangled_repeat' = ICAO prefix followed by a repeat of its last 1-2 letters (e.g. NOSOS739, ITYTY672, WZZZ8068).

```sql
SELECT CASE WHEN flight_mvt IS NULL THEN 'null'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{3}[0-9][0-9A-Z]{0,4}$') THEN 'icao3+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,1)=substr(flight_mvt,3,1) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') AND substr(flight_mvt,4,2)=substr(flight_mvt,2,2) THEN 'mangled_repeat'
  WHEN regexp_matches(flight_mvt, '^[A-Z]{4,5}[0-9][0-9A-Z]*$') THEN 'letters4+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z0-9]{2}[0-9]+[A-Z]?$') THEN 'iata2+num'
  WHEN regexp_matches(flight_mvt, '^[A-Z]+$') THEN 'letters_only(reg?)'
  ELSE 'other' END AS fn_class, f_no_nm_match AS unmatched, airport='LIRF' AS is_lirf,
  count(*) FILTER (ds='train') n_train, count(*) FILTER (ds='rank') n_rank,
  any_value(flight_mvt) example
FROM clean_dep GROUP BY ALL ORDER BY unmatched, is_lirf, n_train DESC
```

25 rows

| fn_class           | unmatched   | is_lirf   |   n_train |   n_rank | example   |
|:-------------------|:------------|:----------|----------:|---------:|:----------|
| icao3+num          | False       | False     |   1453303 |   242933 | EJU1960   |
| iata2+num          | False       | False     |    436935 |    67927 | LX1069    |
| letters_only(reg?) | False       | False     |      9180 |     1453 | DCDSO     |
| other              | False       | False     |      3435 |      638 | N8BD      |
| letters4+num       | False       | False     |       537 |       83 | AOJF1     |
| mangled_repeat     | False       | False     |        14 |        8 | OYBBF1    |
| null               | False       | False     |         2 |        0 | nan       |
| icao3+num          | False       | True      |    156256 |    26046 | ACA893    |
| mangled_repeat     | False       | True      |      2742 |      426 | AEZZ9863  |
| null               | False       | True      |       121 |       35 | nan       |
| other              | False       | True      |        54 |        6 | WMTWMT6N  |
| letters_only(reg?) | False       | True      |        33 |        3 | MABTE     |
| iata2+num          | False       | True      |        10 |        0 | I2251     |
| letters4+num       | False       | True      |         1 |        0 | EXSWR1    |
| icao3+num          | True        | False     |     15410 |     3340 | TUI2142   |
| iata2+num          | True        | False     |      3869 |     1284 | DE4419    |
| letters_only(reg?) | True        | False     |      1325 |      197 | MALLB     |
| letters4+num       | True        | False     |       228 |       47 | PHTDS1    |
| other              | True        | False     |       102 |       24 | T7VKS     |
| mangled_repeat     | True        | False     |         3 |        8 | POLLY01A  |
| icao3+num          | True        | True      |      1244 |      320 | UAL506    |
| mangled_repeat     | True        | True      |       164 |       40 | WMTT3653  |
| null               | True        | True      |        65 |       23 | nan       |
| letters_only(reg?) | True        | True      |         8 |        0 | MABMABTE  |
| other              | True        | True      |         6 |        0 | T78T7850  |
