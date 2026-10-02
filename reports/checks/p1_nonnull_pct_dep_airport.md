# Check: p1_nonnull_pct_dep_airport

Run at 2026-10-02T10:12:14+00:00 (UTC), duckdb 1.5.6.

```sql
SELECT ds, ADEP_mvt, count(*) n,
  round(100.0*count(FLIGHT_ID_mvt)/count(*),2) flight_id, round(100.0*count(AOBT_3_flt)/count(*),2) aobt3,
  round(100.0*count(RUNWAY_mvt)/count(*),2) runway, round(100.0*count(STAND_mvt)/count(*),2) stand,
  round(100.0*count(SCHED_TIME_UTC_mvt)/count(*),2) sched, round(100.0*count(EOBT_1_flt)/count(*),2) eobt1,
  round(100.0*count(AIRCRAFT_TYPE_mvt)/count(*),2) actype
FROM (SELECT 'train' ds, ADEP_mvt, FLIGHT_ID_mvt, AOBT_3_flt, RUNWAY_mvt, STAND_mvt, SCHED_TIME_UTC_mvt, EOBT_1_flt, AIRCRAFT_TYPE_mvt FROM raw_training WHERE PHASE_mvt='DEP'
      UNION ALL SELECT 'rank', ADEP_mvt, FLIGHT_ID_mvt, AOBT_3_flt, RUNWAY_mvt, STAND_mvt, SCHED_TIME_UTC_mvt, EOBT_1_flt, AIRCRAFT_TYPE_mvt FROM raw_ranking WHERE PHASE_mvt='DEP')
GROUP BY ALL ORDER BY 2, 1 DESC
```

20 rows

| ds    | ADEP_mvt   |      n |   flight_id |   aobt3 |   runway |   stand |   sched |   eobt1 |   actype |
|:------|:-----------|-------:|------------:|--------:|---------:|--------:|--------:|--------:|---------:|
| train | EDDF       | 230141 |       99.15 |   99.15 |      100 |  100    |     100 |   99.15 |   100    |
| rank  | EDDF       |  36317 |       98.84 |   98.84 |      100 |  100    |     100 |   98.84 |   100    |
| train | EDDM       | 167334 |       99.4  |   99.4  |      100 |  100    |     100 |   99.4  |   100    |
| rank  | EDDM       |  25966 |       99.08 |   99.08 |      100 |  100    |     100 |   99.08 |   100    |
| train | EGLL       | 239546 |       99.41 |   99.41 |      100 |  100    |     100 |   99.41 |   100    |
| rank  | EGLL       |  39840 |       99.38 |   99.38 |      100 |   99.99 |     100 |   99.38 |   100    |
| train | EHAM       | 247951 |       98.35 |   98.35 |      100 |  100    |     100 |   98.35 |   100    |
| rank  | EHAM       |  38182 |       96.84 |   96.84 |      100 |  100    |     100 |   96.84 |   100    |
| train | LEBL       | 179705 |       98.97 |   98.96 |      100 |  100    |     100 |   98.96 |   100    |
| rank  | LEBL       |  30080 |       98.53 |   98.53 |      100 |  100    |     100 |   98.53 |   100    |
| train | LEMD       | 212242 |       99.56 |   99.55 |      100 |  100    |     100 |   99.55 |   100    |
| rank  | LEMD       |  36954 |       99.36 |   99.36 |      100 |  100    |     100 |   99.36 |   100    |
| train | LFPG       | 239552 |       98.43 |   98.42 |      100 |   99.99 |     100 |   98.42 |   100    |
| rank  | LFPG       |  39872 |       98.16 |   98.16 |      100 |   99.99 |     100 |   98.16 |   100    |
| train | LIRF       | 160704 |       99.07 |   99.07 |      100 |   99.99 |     100 |   99.07 |    99.07 |
| rank  | LIRF       |  26899 |       98.58 |   98.58 |      100 |  100    |     100 |   98.58 |    98.58 |
| train | LSZH       | 134907 |       98.3  |   98.3  |      100 |  100    |     100 |   98.3  |    99.99 |
| rank  | LSZH       |  23150 |       97.15 |   97.15 |      100 |  100    |     100 |   97.15 |   100    |
| train | LTFM       | 272965 |       98.67 |   98.66 |      100 |  100    |     100 |   98.66 |   100    |
| rank  | LTFM       |  47581 |       98.49 |   98.48 |      100 |  100    |     100 |   98.48 |    99.99 |
