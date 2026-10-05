# Check: p4_adsblol_stand_by_airport_EXP-045

Run at 2026-10-05T11:19:06+00:00 (UTC), duckdb 1.5.6.

Rows seen stationary at the own stand with |est − pred| ≤ 600 s (pred = EXP-045 hold-out), all extracted 2025 days: per-airport bias and RMSE of the raw estimate vs the model.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-045_jan.parquet', 'models/oof/EXP-045_jul.parquet'])),
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
| EDDF      |    1 |   704 |               -18 |        150.9 |       84.2 |        79.3 |
| EDDF      |    7 |  1329 |               -17 |        156.8 |       70.9 |        81.8 |
| EDDF      |  nan |  2033 |               -17 |        154.8 |       75.8 |        80.9 |
| EDDM      |    1 |  4103 |               -30 |        136.1 |       49.3 |        89.9 |
| EDDM      |    7 |  1784 |               -29 |        148.7 |       57.7 |        89.9 |
| EDDM      |  nan |  5887 |               -29 |        140   |       52   |        89.9 |
| EGLL      |    1 |   732 |              -145 |        166.4 |      199   |         2.5 |
| EGLL      |    7 |    72 |              -149 |        172.1 |      207   |         0   |
| EGLL      |  nan |   804 |              -145 |        166.9 |      199.7 |         2.2 |
| EHAM      |    1 |  5982 |                13 |        134.2 |       77.5 |        91.3 |
| EHAM      |    7 | 10549 |                12 |        149.5 |      104   |        89.7 |
| EHAM      |  nan | 16531 |                13 |        144.2 |       95.2 |        90.3 |
| LEBL      |    1 |  1092 |               -15 |        120.9 |       55.1 |        85.9 |
| LEBL      |    7 |  2266 |               -17 |        237   |      214   |        77.4 |
| LEBL      |  nan |  3358 |               -17 |        206.6 |      178.6 |        80.1 |
| LEMD      |    7 |    65 |              -103 |        175.5 |      164.6 |        18.5 |
| LEMD      |  nan |    65 |              -103 |        175.5 |      164.6 |        18.5 |
| LFPG      |    7 |     4 |                14 |        207.9 |      123.8 |        75   |
| LFPG      |  nan |     4 |                14 |        207.9 |      123.8 |        75   |
| LIRF      |    7 |   260 |              -104 |        362.7 |      400.1 |        31.5 |
| LIRF      |  nan |   260 |              -104 |        362.7 |      400.1 |        31.5 |
| LSZH      |    1 |  1975 |               -24 |        133.2 |       72.3 |        90.7 |
| LSZH      |    7 |  2041 |               -25 |        130.2 |       72.5 |        91.6 |
| LSZH      |  nan |  4016 |               -25 |        131.7 |       72.4 |        91.1 |
| nan       |  nan | 32958 |                -5 |        153.8 |      107.5 |        85.9 |
