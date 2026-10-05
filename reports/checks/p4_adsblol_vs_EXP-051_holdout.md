# Check: p4_adsblol_vs_EXP-051_holdout

Run at 2026-10-05T11:54:25+00:00 (UTC), duckdb 1.5.6.

EXP-051 Jan/Jul-2025 hold-out predictions vs the raw ADS-B off-block estimate (stand = M-021, parked = M-018), all extracted 2025 days, binned by |est − pred|.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-051_jan.parquet', 'models/oof/EXP-051_jul.parquet'])),
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
| parked | a ≤60     |   719 |        105.3 |      106.9 |          32.8 |        31.1 |
| parked | b 60–180  |   848 |        136.8 |      155   |          96.2 |        55.2 |
| parked | c 180–600 |  1522 |        212.5 |      351.2 |         107   |       304.4 |
| parked | d >600    |   543 |        465.2 |     1397.7 |         178.3 |       989.1 |
| parked | nan       |  3632 |        240.5 |      593   |          89.4 |       205.2 |
| stand  | a ≤60     | 30234 |         82   |       86.6 |          15   |        19.3 |
| stand  | b 60–180  |  2577 |        212.3 |      236.7 |          58.8 |        43.6 |
| stand  | c 180–600 |   171 |        182.7 |      274.4 |          87.7 |       174   |
| stand  | d >600    |  1726 |        505.8 |     4948.8 |          98.1 |      3544.8 |
| stand  | nan       | 34708 |        148.6 |     1108.6 |          17.7 |        21.2 |
| nan    | nan       | 38340 |        159.6 |     1070.4 |          19.8 |        23   |
