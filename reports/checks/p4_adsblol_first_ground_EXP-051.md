# Check: p4_adsblol_first_ground_EXP-051

Run at 2026-10-05T11:54:26+00:00 (UTC), duckdb 1.5.6.

Rows with an ADS-B taxi segment but never seen at their OSM stand nor parked: est = take-off − first ground observation (M-018, a lower bound) vs EXP-051 hold-out predictions, all extracted 2025 days.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-051_jan.parquet', 'models/oof/EXP-051_jul.parquet'])),
e AS (SELECT f.airport, f.y, o.pred, a.adsb_first_ground_s AS est
      FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb a USING (mvt_id)
      LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
      WHERE a.adsb_has_ground AND NOT coalesce(s.adsb_seen_at_stand, false) AND NOT coalesce(a.adsb_seen_parked, false)
        AND a.adsb_first_ground_s IS NOT NULL)
SELECT CASE WHEN abs(est - pred) <= 60 THEN 'a ≤60' WHEN abs(est - pred) <= 180 THEN 'b 60–180'
            WHEN abs(est - pred) <= 600 THEN 'c 180–600' ELSE 'd >600' END AS gap,
  count(*) n, round(median(est - y), 0) med_est_minus_y, round(sqrt(avg((pred - y)^2)), 1) rmse_model,
  round(sqrt(avg((est - y)^2)), 1) rmse_est, round(median(abs(pred - y)), 1) medae_model,
  round(median(abs(est - y)), 1) medae_est
FROM e GROUP BY ROLLUP (gap) ORDER BY gap NULLS LAST
```

5 rows

| gap       |     n |   med_est_minus_y |   rmse_model |   rmse_est |   medae_model |   medae_est |
|:----------|------:|------------------:|-------------:|-----------:|--------------:|------------:|
| a ≤60     |  4240 |               -78 |        251.3 |      254.1 |          78.1 |        81.8 |
| b 60–180  | 10000 |              -124 |        193.4 |      234.1 |          80.9 |       127.3 |
| c 180–600 | 50218 |              -375 |        171.9 |      417.2 |          79.1 |       375.5 |
| d >600    | 23672 |              -711 |        570.9 |     1576.3 |         155.1 |       714.5 |
| nan       | 88130 |              -401 |        334.2 |      880.9 |          93.5 |       402.2 |
