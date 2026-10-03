# Check: p4_adsblol_stand_last_vs_v4

Run at 2026-10-03T20:24:35+00:00 (UTC), duckdb 1.5.6.

Exploratory: M-021 variant. est_last = first moving point (gs ≥ 1 kt) after the last stationary point within 60 m of the own OSM stand; est_first = current M-021 (first moving point at the stand). Rows seen stationary at the stand, 2025 extracted days, vs EXP-039 hold-out predictions, binned by |est_last − pred|.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-039_jan.parquet', 'models/oof/EXP-039_jul.parquet'])),
e AS (SELECT f.airport, f.y, o.pred, s.adsb_stand_move_s AS est_first, x.est_last, x.lag_s
      FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb_stand s USING (mvt_id) JOIN est x USING (mvt_id)
      WHERE s.adsb_still_at_stand)
SELECT CASE WHEN abs(est_last - pred) <= 60 THEN 'a ≤60' WHEN abs(est_last - pred) <= 180 THEN 'b 60–180'
            WHEN abs(est_last - pred) <= 600 THEN 'c 180–600' ELSE 'd >600' END AS gap_last,
  count(*) n, round(sqrt(avg((pred - y)^2)), 1) rmse_model, round(sqrt(avg((est_first - y)^2)), 1) rmse_first,
  round(sqrt(avg((est_last - y)^2)), 1) rmse_last, round(median(abs(est_last - y)), 1) medae_last,
  round(median(abs(pred - y)), 1) medae_model, round(100*avg((abs(est_last - y) <= 60)::INT), 1) pct60_last,
  round(median(lag_s), 0) med_lag_s
FROM e GROUP BY ROLLUP (1) ORDER BY 1 NULLS LAST
```

5 rows

| gap_last   |    n |   rmse_model |   rmse_first |   rmse_last |   medae_last |   medae_model |   pct60_last |   med_lag_s |
|:-----------|-----:|-------------:|-------------:|------------:|-------------:|--------------:|-------------:|------------:|
| a ≤60      | 1173 |         98.7 |        949.3 |        97.3 |         27.1 |          37   |         80   |          16 |
| b 60–180   | 1947 |        125.7 |       1090.5 |       126.4 |         34.9 |          93.5 |         67.2 |          16 |
| c 180–600  | 2499 |        192.2 |        939.4 |       257.6 |        212.3 |         104   |         21.9 |          19 |
| d >600     |  140 |        774.7 |        673.4 |       591.2 |        375   |         387.6 |         22.9 |          39 |
| nan        | 5759 |        194.8 |        991.6 |       211.2 |         65.5 |          84.1 |         49.1 |          18 |
