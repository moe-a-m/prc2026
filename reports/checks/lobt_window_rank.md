# Check: lobt_window_rank

Run at 2026-10-06T18:03:47+00:00 (UTC), duckdb 1.5.6.

2026 ranking departures: LOBT availability (the window applies only where LOBT exists) and take-off − LOBT range, the input that defines each row's feasible taxi-out interval [d_lobt − 3606, d_lobt + 3606].

```sql
SELECT airport, count(*) AS n_dep, count(d_lobt) AS n_with_lobt,
  count(*) FILTER (WHERE d_lobt IS NOT NULL AND d_lobt - 3606 > 0) AS n_window_excludes_zero_taxi,
  min(d_lobt) AS min_takeoff_minus_lobt_s, max(d_lobt) AS max_takeoff_minus_lobt_s
FROM feat_dep WHERE ds = 'rank' GROUP BY ROLLUP (airport) ORDER BY airport NULLS LAST
```

11 rows

| airport   |   n_dep |   n_with_lobt |   n_window_excludes_zero_taxi |   min_takeoff_minus_lobt_s |   max_takeoff_minus_lobt_s |
|:----------|--------:|--------------:|------------------------------:|---------------------------:|---------------------------:|
| EDDF      |   36317 |         35896 |                           896 |                      -2162 |                       8402 |
| EDDM      |   25966 |         25728 |                           411 |                      -1740 |                       7681 |
| EGLL      |   39840 |         39592 |                           939 |                      -2160 |                      10502 |
| EHAM      |   38182 |         36976 |                          1103 |                      -3173 |                      13414 |
| LEBL      |   30080 |         29638 |                           668 |                      -2399 |                       5926 |
| LEMD      |   36954 |         36716 |                           511 |                      -1765 |                       6904 |
| LFPG      |   39872 |         39138 |                          1153 |                      -2883 |                      13620 |
| LIRF      |   26899 |         26516 |                           510 |                      -2343 |                      86820 |
| LSZH      |   23150 |         22491 |                           493 |                      -2131 |                       7458 |
| LTFM      |   47581 |         46860 |                           482 |                      -2465 |                       7859 |
| nan       |  344841 |        339551 |                          7166 |                      -3173 |                      86820 |
