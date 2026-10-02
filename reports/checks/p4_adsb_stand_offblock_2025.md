# Check: p4_adsb_stand_offblock_2025

Run at 2026-10-02T18:38:40+00:00 (UTC), duckdb 1.5.6.

2025 labelled days extracted so far, matched departures, y ≤ 3 h. still = seen stationary within 60 m of its OSM stand, estimate = first movement there; moving-only = seen at the stand only while moving, estimate = first at-stand point.

```sql
WITH d AS (SELECT f.airport, f.y, f.d_aobt3, a.adsb_seen_parked, a.adsb_first_move_s, s.*
           FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
           WHERE f.ds='train' AND a.adsb_matched AND f.y <= 10800)
SELECT airport, count(*) n_matched,
  round(100*avg(adsb_seen_parked::INT),1) pct_seen_parked,
  round(100*avg(coalesce(adsb_still_at_stand,false)::INT),1) pct_still_at_stand,
  round(100*avg(coalesce(adsb_seen_at_stand,false)::INT),1) pct_seen_at_stand,
  round(100*avg((abs(adsb_stand_move_s - y) <= 60)::INT) FILTER (WHERE adsb_still_at_stand),1) pct_within60_still,
  round(sqrt(avg((adsb_stand_move_s - y)^2) FILTER (WHERE adsb_still_at_stand)),0) rmse_still,
  round(100*avg((abs(adsb_stand_first_s - y) <= 60)::INT) FILTER (WHERE adsb_seen_at_stand AND NOT adsb_still_at_stand),1) pct_within60_moving_only,
  round(median(adsb_stand_first_s - y) FILTER (WHERE adsb_seen_at_stand AND NOT adsb_still_at_stand),0) med_err_moving_only
FROM d GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

11 rows

| airport   |   n_matched |   pct_seen_parked |   pct_still_at_stand |   pct_seen_at_stand |   pct_within60_still |   rmse_still |   pct_within60_moving_only |   med_err_moving_only |
|:----------|------------:|------------------:|---------------------:|--------------------:|---------------------:|-------------:|---------------------------:|----------------------:|
| EDDF      |        2632 |               7.5 |                  5.9 |                12.3 |                 73.6 |          411 |                       72   |                   -22 |
| EDDM      |        1920 |              28.5 |                 23.1 |                39   |                 88.9 |          856 |                       78.4 |                   -37 |
| EGLL      |        2814 |               8.5 |                  3.9 |                 7   |                  0   |          603 |                        0   |                  -162 |
| EHAM      |        3235 |              16.8 |                 42.2 |                61.1 |                 88.5 |          953 |                       74.9 |                     4 |
| LEBL      |        2433 |              13.3 |                 16.7 |                32.8 |                 77.5 |          902 |                       75.6 |                   -28 |
| LEMD      |        2599 |              10.5 |                  1.4 |                 3.4 |                 20   |          204 |                        7.7 |                  -119 |
| LFPG      |        2315 |               3.2 |                  0.1 |                 0.1 |                100   |           39 |                        0   |                  -100 |
| LIRF      |        1333 |               3.7 |                  2.8 |                 6.9 |                 34.4 |          793 |                       27.3 |                  -115 |
| LSZH      |        1719 |              18.5 |                 23.6 |                31.8 |                 80.9 |         1470 |                       75.7 |                   -34 |
| LTFM      |           3 |             nan   |                  0   |                 0   |                nan   |          nan |                      nan   |                   nan |
| nan       |       21003 |              14   |                 14.1 |                22.7 |                 80.7 |          986 |                       68.5 |                   -26 |
