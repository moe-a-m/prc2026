# Check: m034_adsb_feature_drift

Run at 2026-10-07T12:16:05+00:00 (UTC), duckdb 1.5.6.

Movement features (seen parked, first movement, taxi distance, holds) vs reception features (first ground observation, points, largest gap) on departures with an ADS-B ground segment, 2025 vs 2026 ranking. Reception features are expected to drift with the receiver network (forum, a participant 27/09).

```sql
WITH d AS (
    SELECT f.airport, CASE WHEN f.ds = 'train' THEN 2025 ELSE 2026 END AS yr, a.*
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) WHERE a.adsb_has_ground
)
SELECT airport, yr, count(*) AS n_ground,
  round(avg(adsb_seen_parked::INT), 3) AS share_parked,
  round(median(adsb_first_move_s) FILTER (WHERE adsb_seen_parked), 0) AS med_first_move_parked_s,
  round(median(adsb_taxi_dist_m), 0) AS med_taxi_dist_m,
  round(median(adsb_hold_s), 0) AS med_hold_s,
  round(median(adsb_first_ground_s), 0) AS med_first_ground_s,
  round(median(adsb_n_pts), 0) AS med_n_pts,
  round(median(adsb_max_gap_s), 0) AS med_max_gap_s
FROM d GROUP BY ALL ORDER BY airport, yr
```

19 rows

| airport   |   yr |   n_ground |   share_parked |   med_first_move_parked_s |   med_taxi_dist_m |   med_hold_s |   med_first_ground_s |   med_n_pts |   med_max_gap_s |
|:----------|-----:|-----------:|---------------:|--------------------------:|------------------:|-------------:|---------------------:|------------:|----------------:|
| EDDF      | 2025 |      29635 |          0.087 |                       615 |              2657 |            0 |                  485 |          30 |             101 |
| EDDF      | 2026 |      22256 |          0.046 |                       608 |              2085 |            0 |                  362 |          11 |             111 |
| EDDM      | 2025 |      16660 |          0.272 |                       715 |              3156 |           25 |                  760 |         102 |             120 |
| EDDM      | 2026 |      24921 |          0.286 |                       744 |              3005 |           36 |                  780 |         112 |             100 |
| EGLL      | 2025 |       7734 |          0.084 |                       667 |               954 |            0 |                  453 |          12 |             176 |
| EGLL      | 2026 |      32373 |          0.18  |                      1120 |              2329 |           53 |                 1037 |          69 |             211 |
| EHAM      | 2025 |      39762 |          0.18  |                       779 |              2737 |           39 |                  706 |         106 |              80 |
| EHAM      | 2026 |      36720 |          0.204 |                       835 |              3288 |           46 |                  795 |         151 |              79 |
| LEBL      | 2025 |      25570 |          0.102 |                       773 |              3081 |            0 |                  684 |          76 |             131 |
| LEBL      | 2026 |      27129 |          0.143 |                       829 |              3125 |            4 |                  734 |          81 |             126 |
| LEMD      | 2025 |        745 |          0.074 |                       808 |              2759 |            0 |                  386 |          21 |              94 |
| LEMD      | 2026 |      24899 |          0.107 |                       908 |              3118 |            6 |                  595 |          76 |             113 |
| LFPG      | 2025 |       1368 |          0.046 |                        75 |               298 |            0 |                  115 |           3 |              75 |
| LFPG      | 2026 |       3306 |          0.021 |                       102 |               589 |            0 |                  200 |           4 |             158 |
| LIRF      | 2025 |      12357 |          0.03  |                       639 |              1417 |            0 |                  389 |          36 |              94 |
| LIRF      | 2026 |       7010 |          0.057 |                       664 |               727 |            0 |                  255 |          14 |             113 |
| LSZH      | 2025 |      17572 |          0.179 |                       468 |              1635 |           35 |                  511 |          78 |              78 |
| LSZH      | 2026 |      20234 |          0.099 |                       555 |              1553 |           38 |                  528 |          59 |              80 |
| LTFM      | 2026 |          4 |          0     |                       nan |               130 |            0 |                   15 |           2 |              35 |
