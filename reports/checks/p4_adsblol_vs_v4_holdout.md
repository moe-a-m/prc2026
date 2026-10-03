# Check: p4_adsblol_vs_v4_holdout

Run at 2026-10-03T20:23:40+00:00 (UTC), duckdb 1.5.6.

Exploratory (not a tuned rule): EXP-039 (v4 recipe) Jan/Jul-2025 hold-out predictions vs the raw ADS-B off-block estimate (stand = first movement at own OSM stand, M-021; parked = first movement when seen parked, M-018), on the 10 extracted 2025 days, binned by |est − pred|. rmse_mean = simple average of the two.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-039_jan.parquet', 'models/oof/EXP-039_jul.parquet'])),
e AS (
    SELECT f.airport, strftime(f.month, '%Y-%m') AS ym, f.y, o.pred,
           CASE WHEN s.adsb_still_at_stand THEN s.adsb_stand_move_s WHEN a.adsb_seen_parked THEN a.adsb_first_move_s END AS est,
           CASE WHEN s.adsb_still_at_stand THEN 'stand' WHEN a.adsb_seen_parked THEN 'parked' END AS src
    FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
)

SELECT src, CASE WHEN abs(est - pred) <= 60 THEN 'a ≤60' WHEN abs(est - pred) <= 180 THEN 'b 60–180'
                 WHEN abs(est - pred) <= 600 THEN 'c 180–600' ELSE 'd >600' END AS gap,
  count(*) n, round(sqrt(avg((pred - y)^2)), 1) rmse_model, round(sqrt(avg((est - y)^2)), 1) rmse_est,
  round(sqrt(avg(((pred + est)/2 - y)^2)), 1) rmse_mean,
  round(median(abs(pred - y)), 1) medae_model, round(median(abs(est - y)), 1) medae_est
FROM e WHERE est IS NOT NULL GROUP BY ROLLUP (src, gap) ORDER BY src NULLS LAST, gap NULLS LAST
```

11 rows

| src    | gap       |    n |   rmse_model |   rmse_est |   rmse_mean |   medae_model |   medae_est |
|:-------|:----------|-----:|-------------:|-----------:|------------:|--------------:|------------:|
| parked | a ≤60     |   72 |        123.4 |      129.6 |       125.3 |          43.4 |        37.5 |
| parked | b 60–180  |  145 |        142.5 |      150.8 |       133   |         104.5 |        51.2 |
| parked | c 180–600 |  274 |        209.2 |      329.2 |       200.3 |         119   |       289.1 |
| parked | d >600    |   87 |        337.2 |     1056.9 |       570.9 |         171.9 |       856.5 |
| parked | nan       |  578 |        211.8 |      476.8 |       272.9 |         106   |       209.1 |
| stand  | a ≤60     | 1799 |         78.7 |       74   |        74.4 |          30.9 |        18.2 |
| stand  | b 60–180  | 2274 |        118.2 |       68.1 |        77.2 |          98.7 |        19.7 |
| stand  | c 180–600 | 1089 |        272.6 |      172.6 |       172.8 |         218.9 |        29.7 |
| stand  | d >600    |  284 |        541.5 |     4320.8 |      2186   |         129.5 |      3414.6 |
| stand  | nan       | 5446 |        195   |      991.6 |       509.4 |          83.9 |        21.3 |
| nan    | nan       | 6024 |        196.7 |      954.3 |       491.7 |          85.6 |        23.3 |
