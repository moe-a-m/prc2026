# Check: p4_wx_taxi_by_condition

Run at 2026-10-02T12:31:04+00:00 (UTC), duckdb 1.5.6.

Taxi-out (rows ≤ 3 h) with snow/freezing precipitation in the 3 h before take-off vs without.

```sql
-- Does taxi-out differ on snow/freezing days? (CLAUDE.md §6: check before modelling) — 2025 training DEP
SELECT f.airport,
  round(avg(y) FILTER (WHERE NOT coalesce(w.wx3h_snow OR w.wx3h_freezing, false)), 0) mean_y_clear,
  round(avg(y) FILTER (WHERE w.wx3h_snow OR w.wx3h_freezing), 0) mean_y_snow_or_fz,
  count(*) FILTER (WHERE w.wx3h_snow OR w.wx3h_freezing) n_snow_or_fz,
  round(median(y) FILTER (WHERE NOT coalesce(w.wx3h_snow OR w.wx3h_freezing, false)), 0) med_y_clear,
  round(median(y) FILTER (WHERE w.wx3h_snow OR w.wx3h_freezing), 0) med_y_snow_or_fz,
  round(median(y) FILTER (WHERE w.wx_vis_m < 1500), 0) med_y_vis_lt1500, count(*) FILTER (WHERE w.wx_vis_m < 1500) n_vis_lt1500,
  round(100.0*avg(w.wx_stale::INT), 2) pct_stale
FROM feat_dep f JOIN feat_dep_wx w USING (mvt_id) WHERE f.ds = 'train' AND f.y <= 3*3600 GROUP BY 1 ORDER BY 1
```

10 rows

| airport   |   mean_y_clear |   mean_y_snow_or_fz |   n_snow_or_fz |   med_y_clear |   med_y_snow_or_fz |   med_y_vis_lt1500 |   n_vis_lt1500 |   pct_stale |
|:----------|---------------:|--------------------:|---------------:|--------------:|-------------------:|-------------------:|---------------:|------------:|
| EDDF      |            861 |                1132 |           2367 |           836 |                940 |                925 |           1648 |        0    |
| EDDM      |            796 |                1272 |           5711 |           772 |               1136 |                957 |           3997 |        0    |
| EGLL      |           1363 |                1589 |            630 |          1319 |               1437 |               1745 |            453 |        0    |
| EHAM      |            780 |                1083 |           4041 |           741 |                840 |                791 |           2958 |        0    |
| LEBL      |            957 |                 nan |              0 |           906 |                nan |                966 |            634 |        0.01 |
| LEMD      |           1015 |                1026 |            145 |           985 |                967 |               1049 |            385 |        0    |
| LFPG      |           1011 |                1880 |           2150 |           954 |               1619 |               1437 |           3219 |        0    |
| LIRF      |           1165 |                 nan |              0 |          1024 |                nan |               1312 |            138 |        0.02 |
| LSZH      |            734 |                1074 |           2466 |           710 |                861 |                773 |           3089 |        0    |
| LTFM      |           1038 |                1720 |           5997 |           962 |               1151 |               1074 |           2613 |        0    |
