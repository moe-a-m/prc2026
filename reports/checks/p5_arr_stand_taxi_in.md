# Check: p5_arr_stand_taxi_in

Run at 2026-10-03T05:31:47+00:00 (UTC), duckdb 1.5.6.

Median ARR taxi-in per (airport, stand) over 2025 + 2026 arrivals (label-free for departures): coverage of ranking departures, correlation with taxi-out (2025, y ≤ 2 h), and ranking departures at stands unseen in 2025 departures that it covers.

```sql
WITH a AS (SELECT airport, stand, median(y) med_in, count(*) n_in FROM stg_mvt WHERE phase='ARR' AND y BETWEEN 0 AND 3600 AND stand IS NOT NULL GROUP BY ALL),
d AS (SELECT f.airport, f.stand, f.ds, f.y, a.med_in, a.n_in FROM feat_dep f LEFT JOIN a USING (airport, stand))
SELECT airport, round(100*avg((med_in IS NOT NULL)::INT) FILTER (WHERE ds='rank'),1) pct_rank_cov,
  round(corr(med_in, y) FILTER (WHERE ds='train' AND y <= 7200),3) corr_taxiin_vs_taxiout,
  (SELECT count(*) FROM d d2 WHERE d2.airport=d.airport AND d2.ds='rank' AND d2.med_in IS NOT NULL
     AND d2.stand NOT IN (SELECT stand FROM feat_dep WHERE ds='train' AND airport=d.airport AND stand IS NOT NULL)) n_rank_new_stand_covered
FROM d GROUP BY 1 ORDER BY 1
```

10 rows

| airport   |   pct_rank_cov |   corr_taxiin_vs_taxiout |   n_rank_new_stand_covered |
|:----------|---------------:|-------------------------:|---------------------------:|
| EDDF      |            100 |                    0.272 |                        299 |
| EDDM      |            100 |                    0.119 |                       1178 |
| EGLL      |            100 |                    0.034 |                          0 |
| EHAM      |            100 |                    0.334 |                         11 |
| LEBL      |            100 |                   -0.178 |                          1 |
| LEMD      |            100 |                    0.46  |                         13 |
| LFPG      |            100 |                    0.175 |                          7 |
| LIRF      |            100 |                    0.044 |                          9 |
| LSZH      |            100 |                    0.15  |                         57 |
| LTFM      |            100 |                    0.01  |                          5 |
