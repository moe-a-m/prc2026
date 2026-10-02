# Check: p4_adsb_offblock_variants_2025-01-01

Run at 2026-10-02T14:40:39+00:00 (UTC), duckdb 1.5.6.

Off-block estimate variants on matched ground segments, 2025-01-01, y ≤ 3 h. A = first movement (gs ≥ 1 kt) when the segment starts stationary for ≥ 60 s (aircraft seen parked); B = first movement, all; C = first ground observation.

```sql
WITH m AS (  -- matched departures with ground segment, same matching as feat_dep_adsb
  SELECT f.mvt_id, f.airport, f.y, f.d_aobt3, timezone('UTC', to_timestamp(f.t_mvt_epoch)) t_mvt, e.icao24, e.ground_seg
  FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id)
  JOIN (SELECT * FROM adsb_takeoff) e ON e.airport = f.airport AND abs(epoch(e.t_air0) - f.t_mvt_epoch - a.adsb_dt_takeoff_s) < 0.001
  WHERE f.ds='train' AND a.adsb_has_ground AND f.y <= 10800 AND f.month = DATE '2025-01-01'),
p AS (SELECT m.mvt_id, s.t, coalesce(s.gs_kt,0) gs FROM m JOIN adsb_seg s ON s.icao24=m.icao24 AND s.airport=m.airport AND s.seg=m.ground_seg),
first_move AS (SELECT mvt_id, min(t) FILTER (WHERE gs >= 1) t_move, min(t) t0, arg_min(gs, t) gs0 FROM p GROUP BY 1),
v AS (SELECT m.*, epoch(m.t_mvt) - epoch(fm.t_move) est_b, epoch(m.t_mvt) - epoch(fm.t0) est_c, fm.gs0 < 1 AS starts_still,
             epoch(fm.t_move) - epoch(fm.t0) still_dur FROM m JOIN first_move fm USING (mvt_id))
SELECT airport, count(*) n,
  round(100*avg((starts_still AND still_dur >= 60)::INT),1) pct_seen_parked,
  round(sqrt(avg((est_b - y)^2) FILTER (WHERE starts_still AND still_dur >= 60)),0) rmse_A_parked_first_move,
  round(median(est_b - y) FILTER (WHERE starts_still AND still_dur >= 60),0) med_err_A,
  round(100*avg((abs(est_b - y) <= 60)::INT) FILTER (WHERE starts_still AND still_dur >= 60),1) pct_A_within60,
  round(sqrt(avg((d_aobt3 - y)^2) FILTER (WHERE starts_still AND still_dur >= 60)),0) rmse_aobt3_same_rows,
  round(sqrt(avg((est_b - y)^2)),0) rmse_B_first_move_all, round(sqrt(avg((est_c - y)^2)),0) rmse_C_first_seen_all
FROM v GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

7 rows

| airport   |    n |   pct_seen_parked |   rmse_A_parked_first_move |   med_err_A |   pct_A_within60 |   rmse_aobt3_same_rows |   rmse_B_first_move_all |   rmse_C_first_seen_all |
|:----------|-----:|------------------:|---------------------------:|------------:|-----------------:|-----------------------:|------------------------:|------------------------:|
| EDDF      |  306 |              10.5 |                        308 |        -146 |             34.4 |                    254 |                     467 |                     467 |
| EDDM      |  309 |              32.4 |                         61 |         -37 |             84   |                    442 |                     625 |                     703 |
| EGLL      |  159 |               8.2 |                        903 |        -416 |              0   |                    255 |                     951 |                    2314 |
| EHAM      |  586 |              14   |                        156 |          14 |             69.5 |                    284 |                     458 |                     501 |
| LEBL      |  419 |               7.4 |                        212 |         -17 |             77.4 |                    209 |                     373 |                     397 |
| LSZH      |  244 |              15.2 |                        951 |         -27 |             94.6 |                    190 |                    1026 |                    1336 |
| nan       | 2023 |              14.6 |                        415 |         -29 |             71.5 |                    328 |                     616 |                     922 |
