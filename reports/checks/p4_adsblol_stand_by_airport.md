# Check: p4_adsblol_stand_by_airport

Run at 2026-10-03T20:25:07+00:00 (UTC), duckdb 1.5.6.

Exploratory: rows seen stationary at the own stand with |est − pred| ≤ 600 s (est = M-021 first movement at stand, pred = EXP-039 hold-out), 2025 extracted days, per airport and month: bias and RMSE of the raw estimate vs the model.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-039_jan.parquet', 'models/oof/EXP-039_jul.parquet'])),
e AS (SELECT f.airport, strftime(f.month, '%m') AS mo, f.y, o.pred, s.adsb_stand_move_s AS est
      FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb_stand s USING (mvt_id)
      WHERE s.adsb_still_at_stand AND abs(s.adsb_stand_move_s - o.pred) <= 600)
SELECT airport, mo, count(*) n, round(median(est - y), 0) med_est_minus_y, round(median(pred - y), 0) med_pred_minus_y,
  round(sqrt(avg((pred - y)^2)), 1) rmse_model, round(sqrt(avg((est - y)^2)), 1) rmse_est,
  round(100*avg((abs(est - y) <= 60)::INT), 1) pct60_est
FROM e GROUP BY ROLLUP (airport, mo) ORDER BY airport NULLS LAST, mo NULLS LAST
```

24 rows

| airport   |   mo |    n |   med_est_minus_y |   med_pred_minus_y |   rmse_model |   rmse_est |   pct60_est |
|:----------|-----:|-----:|------------------:|-------------------:|-------------:|-----------:|------------:|
| EDDF      |    1 |  102 |               -24 |                 19 |        164.6 |       92.4 |        71.6 |
| EDDF      |    7 |  179 |               -16 |                 57 |        140.7 |       90.8 |        82.1 |
| EDDF      |  nan |  281 |               -18 |                 47 |        149.8 |       91.4 |        78.3 |
| EDDM      |    1 |  648 |               -31 |                 16 |        161.8 |       49.4 |        90   |
| EDDM      |  nan |  648 |               -31 |                 16 |        161.8 |       49.4 |        90   |
| EGLL      |    1 |  115 |              -140 |                 73 |        199.6 |      186.9 |         0   |
| EGLL      |    7 |    9 |              -128 |                 32 |        175.9 |      223   |         0   |
| EGLL      |  nan |  124 |              -140 |                 69 |        198   |      189.8 |         0   |
| EHAM      |    1 |  971 |                13 |                -18 |        144.2 |       80.2 |        91   |
| EHAM      |    7 | 1692 |                13 |                 19 |        133.4 |       77.6 |        90.5 |
| EHAM      |  nan | 2663 |                13 |                  7 |        137.4 |       78.6 |        90.7 |
| LEBL      |    1 |  228 |               -15 |                 28 |        122.3 |       41.8 |        90.4 |
| LEBL      |    7 |  469 |               -22 |                 53 |        228.5 |      209.5 |        76.5 |
| LEBL      |  nan |  697 |               -19 |                 42 |        200   |      173.5 |        81.1 |
| LEMD      |    7 |   39 |               -89 |                 87 |        182.7 |      155.9 |        17.9 |
| LEMD      |  nan |   39 |               -89 |                 87 |        182.7 |      155.9 |        17.9 |
| LFPG      |    7 |    2 |               -22 |                240 |        242.4 |       39.4 |       100   |
| LFPG      |  nan |    2 |               -22 |                240 |        242.4 |       39.4 |       100   |
| LIRF      |    7 |   58 |               -97 |                 56 |        260.6 |      253.6 |        34.5 |
| LIRF      |  nan |   58 |               -97 |                 56 |        260.6 |      253.6 |        34.5 |
| LSZH      |    1 |  324 |               -25 |                 21 |        147.7 |       60.8 |        91   |
| LSZH      |    7 |  326 |               -25 |                 31 |        125.3 |       59.6 |        92   |
| LSZH      |  nan |  650 |               -25 |                 29 |        136.9 |       60.2 |        91.5 |
| nan       |  nan | 5162 |                -3 |                 19 |        154.9 |      101.2 |        85.4 |
