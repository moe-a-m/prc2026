# Check: p4_adsblol_vs_EXP-045_holdout

Run at 2026-10-05T10:49:20+00:00 (UTC), duckdb 1.5.6.

EXP-045 Jan/Jul-2025 hold-out predictions vs the raw ADS-B off-block estimate (stand = M-021, parked = M-018), all extracted 2025 days, binned by |est − pred|.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-045_jan.parquet', 'models/oof/EXP-045_jul.parquet'])),
e AS (
    SELECT f.airport, f.y, o.pred,
           CASE WHEN s.adsb_still_at_stand THEN s.adsb_stand_move_s WHEN a.adsb_seen_parked THEN a.adsb_first_move_s END AS est,
           CASE WHEN s.adsb_still_at_stand THEN 'stand' WHEN a.adsb_seen_parked THEN 'parked' END AS src
    FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
)
SELECT src, CASE WHEN abs(est - pred) <= 60 THEN 'a ≤60' WHEN abs(est - pred) <= 180 THEN 'b 60–180'
                 WHEN abs(est - pred) <= 600 THEN 'c 180–600' ELSE 'd >600' END AS gap,
  count(*) n, round(sqrt(avg((pred - y)^2)), 1) rmse_model, round(sqrt(avg((est - y)^2)), 1) rmse_est,
  round(median(abs(pred - y)), 1) medae_model, round(median(abs(est - y)), 1) medae_est
FROM e WHERE est IS NOT NULL GROUP BY ROLLUP (src, gap) ORDER BY src NULLS LAST, gap NULLS LAST
```

11 rows

| src    | gap       |     n |   rmse_model |   rmse_est |   medae_model |   medae_est |
|:-------|:----------|------:|-------------:|-----------:|--------------:|------------:|
| parked | a ≤60     |   541 |        115.3 |      115.5 |          39.9 |        37.4 |
| parked | b 60–180  |   911 |        133.4 |      137.1 |          97.2 |        47.8 |
| parked | c 180–600 |  1636 |        214.4 |      342.2 |         111.2 |       296.4 |
| parked | d >600    |   544 |        465.2 |     1396.7 |         178.5 |       986.4 |
| parked | nan       |  3632 |        244   |      593   |          97   |       205.2 |
| stand  | a ≤60     | 12252 |         74.4 |       68.4 |          30.6 |        18.1 |
| stand  | b 60–180  | 14450 |        122.5 |       77.1 |          98.5 |        19.9 |
| stand  | c 180–600 |  6256 |        281.2 |      195   |         216.2 |        28.7 |
| stand  | d >600    |  1750 |        505.4 |     4914.9 |          99.6 |      3510.5 |
| stand  | nan       | 34708 |        188   |     1108.6 |          79.1 |        21.2 |
| nan    | nan       | 38340 |        194   |     1070.4 |          80.6 |        23   |
