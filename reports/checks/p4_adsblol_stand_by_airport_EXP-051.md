# Check: p4_adsblol_stand_by_airport_EXP-051

Run at 2026-10-05T11:54:26+00:00 (UTC), duckdb 1.5.6.

Rows seen stationary at the own stand with |est − pred| ≤ 600 s (pred = EXP-051 hold-out), all extracted 2025 days: per-airport bias and RMSE of the raw estimate vs the model.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-051_jan.parquet', 'models/oof/EXP-051_jul.parquet'])),
e AS (SELECT f.airport, strftime(f.month, '%m') AS mo, f.y, o.pred, s.adsb_stand_move_s AS est
      FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb_stand s USING (mvt_id)
      WHERE s.adsb_still_at_stand AND abs(s.adsb_stand_move_s - o.pred) <= 600)
SELECT airport, mo, count(*) n, round(median(est - y), 0) med_est_minus_y,
  round(sqrt(avg((pred - y)^2)), 1) rmse_model, round(sqrt(avg((est - y)^2)), 1) rmse_est,
  round(100*avg((abs(est - y) <= 60)::INT), 1) pct60_est
FROM e GROUP BY ROLLUP (airport, mo) ORDER BY airport NULLS LAST, mo NULLS LAST
```

25 rows

| airport   |   mo |     n |   med_est_minus_y |   rmse_model |   rmse_est |   pct60_est |
|:----------|-----:|------:|------------------:|-------------:|-----------:|------------:|
| EDDF      |    1 |   704 |               -18 |         78.7 |       84.2 |        79.3 |
| EDDF      |    7 |  1329 |               -17 |         63.1 |       70.9 |        81.8 |
| EDDF      |  nan |  2033 |               -17 |         68.9 |       75.8 |        80.9 |
| EDDM      |    1 |  4106 |               -30 |         47.2 |       49.3 |        89.9 |
| EDDM      |    7 |  1784 |               -29 |         52.1 |       57.7 |        89.9 |
| EDDM      |  nan |  5890 |               -29 |         48.8 |       52   |        89.9 |
| EGLL      |    1 |   740 |              -145 |        100.9 |      199.6 |         2.4 |
| EGLL      |    7 |    76 |              -152 |        133.1 |      236.2 |         0   |
| EGLL      |  nan |   816 |              -145 |        104.4 |      203.3 |         2.2 |
| EHAM      |    1 |  5984 |                13 |         72.2 |       77.5 |        91.3 |
| EHAM      |    7 | 10551 |                12 |         99.9 |      104   |        89.7 |
| EHAM      |  nan | 16535 |                13 |         90.8 |       95.2 |        90.3 |
| LEBL      |    1 |  1092 |               -15 |         53.5 |       55.1 |        85.9 |
| LEBL      |    7 |  2268 |               -17 |        207.1 |      213.9 |        77.3 |
| LEBL      |  nan |  3360 |               -17 |        172.8 |      178.5 |        80.1 |
| LEMD      |    7 |    65 |              -103 |        132.9 |      164.6 |        18.5 |
| LEMD      |  nan |    65 |              -103 |        132.9 |      164.6 |        18.5 |
| LFPG      |    7 |     4 |                14 |        127.4 |      123.8 |        75   |
| LFPG      |  nan |     4 |                14 |        127.4 |      123.8 |        75   |
| LIRF      |    7 |   263 |              -105 |        379.2 |      402   |        31.2 |
| LIRF      |  nan |   263 |              -105 |        379.2 |      402   |        31.2 |
| LSZH      |    1 |  1975 |               -24 |         65.6 |       72.3 |        90.7 |
| LSZH      |    7 |  2041 |               -25 |         62.9 |       72.5 |        91.6 |
| LSZH      |  nan |  4016 |               -25 |         64.2 |       72.4 |        91.1 |
| nan       |  nan | 32982 |                -5 |         99.3 |      107.9 |        85.9 |
