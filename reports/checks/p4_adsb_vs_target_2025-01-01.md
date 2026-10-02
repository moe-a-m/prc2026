# Check: p4_adsb_vs_target_2025-01-01

Run at 2026-10-02T14:40:15+00:00 (UTC), duckdb 1.5.6.

2025-01-01 (labelled): ADS-B off-block estimate (end of the longest stationary run ≥ 120 s) vs target, rows y ≤ 3 h; NM AOBT_3 on the same rows for comparison.

```sql
WITH d AS (SELECT f.airport, f.y, a.*, f.d_aobt3 FROM feat_dep_adsb a JOIN feat_dep f USING (mvt_id)
           WHERE f.ds='train' AND (timezone('UTC', to_timestamp(f.t_mvt_epoch)))::DATE = DATE '2025-01-01' AND f.y <= 10800)
SELECT airport, count(*) n, round(100*avg(adsb_matched::INT),1) pct_matched,
  count(adsb_stand_end_s) n_stand, round(sqrt(avg((adsb_stand_end_s - y)^2)),0) rmse_stand_end,
  round(median(adsb_stand_end_s - y),0) med_err_stand_end,
  round(100*avg((abs(adsb_stand_end_s - y) <= 60)::INT) FILTER (WHERE adsb_stand_end_s IS NOT NULL),1) pct_stand_within60,
  round(sqrt(avg((d_aobt3 - y)^2) FILTER (WHERE adsb_stand_end_s IS NOT NULL)),0) rmse_aobt3_same_rows,
  round(100*avg((adsb_first_ground_s >= y - 60)::INT) FILTER (WHERE adsb_has_ground),1) pct_first_seen_before_offblock
FROM d GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

11 rows

| airport   |    n |   pct_matched |   n_stand |   rmse_stand_end |   med_err_stand_end |   pct_stand_within60 |   rmse_aobt3_same_rows |   pct_first_seen_before_offblock |
|:----------|-----:|--------------:|----------:|-----------------:|--------------------:|---------------------:|-----------------------:|---------------------------------:|
| EDDF      |  434 |          95.9 |        28 |              534 |                 -41 |                 46.4 |                    245 |                             14.1 |
| EDDM      |  310 |          99.7 |       169 |              648 |                -295 |                 24.9 |                    424 |                             76.1 |
| EGLL      |  600 |          83.3 |        20 |              759 |                -440 |                  0   |                    239 |                              2.5 |
| EHAM      |  594 |          99   |       191 |              367 |                -252 |                 13.1 |                    266 |                             52.6 |
| LEBL      |  420 |          99.8 |        51 |              630 |                -262 |                 35.3 |                    374 |                             29.6 |
| LEMD      |  508 |          93.1 |         0 |              nan |                 nan |                nan   |                    nan |                            nan   |
| LFPG      |  577 |          73.1 |         0 |              nan |                 nan |                nan   |                    nan |                            nan   |
| LIRF      |  387 |          21.7 |         0 |              nan |                 nan |                nan   |                    nan |                            nan   |
| LSZH      |  296 |          97.3 |        84 |              501 |                -224 |                 41.7 |                    244 |                             46.7 |
| LTFM      |  662 |           0   |         0 |              nan |                 nan |                nan   |                    nan |                            nan   |
| nan       | 4788 |          73.1 |       543 |              539 |                -266 |                 24.5 |                    329 |                             40.9 |
