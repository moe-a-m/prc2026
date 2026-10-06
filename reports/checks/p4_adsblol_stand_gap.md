# Check: p4_adsblol_stand_gap

Run at 2026-10-06T10:46:51+00:00 (UTC), duckdb 1.5.6.

Departures (Jan/Jul 2025 and 2026) with a matched ADS-B ground segment, split by why the M-021 stand estimate is or is not available: no APDF stand code, stand code without an OSM parking_position (stg_stand_geo), seen within 60 m, or closest ground point 60–150 / 150–500 / > 500 m from the OSM position. Last column: median distance of the first ground point for rows not seen within 60 m.

```sql
WITH d AS (
    SELECT f.airport, strftime(f.month, '%Y-%m') AS ym, f.stand, a.adsb_has_ground,
           g.stand IS NOT NULL AS has_geo, s.adsb_seen_at_stand, s.adsb_min_d_stand_m AS min_d, s.adsb_first_d_stand_m AS first_d
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id)
    LEFT JOIN stg_stand_geo g ON g.airport = f.airport AND g.stand = f.stand
    LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE month(f.month) IN (1, 7) AND a.adsb_has_ground
)
SELECT airport, ym, count(*) AS n_ground,
  round(100*avg((stand IS NULL)::INT), 1) AS pct_no_stand_code,
  round(100*avg((stand IS NOT NULL AND NOT has_geo)::INT), 1) AS pct_no_osm_position,
  round(100*avg(coalesce(adsb_seen_at_stand, false)::INT), 1) AS pct_seen_le60m,
  round(100*avg((min_d > 60 AND min_d <= 150)::INT), 1) AS pct_min_60_150m,
  round(100*avg((min_d > 150 AND min_d <= 500)::INT), 1) AS pct_min_150_500m,
  round(100*avg((min_d > 500)::INT), 1) AS pct_min_gt500m,
  round(median(first_d) FILTER (WHERE NOT adsb_seen_at_stand), 0) AS med_first_d_not_seen_m
FROM d GROUP BY ROLLUP (airport, ym) ORDER BY airport NULLS LAST, ym NULLS LAST
```

45 rows

| airport   | ym      |   n_ground |   pct_no_stand_code |   pct_no_osm_position |   pct_seen_le60m |   pct_min_60_150m |   pct_min_150_500m |   pct_min_gt500m |   med_first_d_not_seen_m |
|:----------|:--------|-----------:|--------------------:|----------------------:|-----------------:|------------------:|-------------------:|-----------------:|-------------------------:|
| EDDF      | 2025-01 |      12173 |                   0 |                   3.4 |             16.4 |              10.5 |               28.2 |             44.4 |                      538 |
| EDDF      | 2025-07 |      17462 |                   0 |                   3.2 |             20.5 |              11.3 |               27   |             40.6 |                      519 |
| EDDF      | 2026-01 |       9382 |                   0 |                   3.1 |             12.1 |               5.7 |               19.3 |             62.5 |                      823 |
| EDDF      | 2026-07 |      12874 |                   0 |                   4.1 |              9.2 |               7.1 |                9.7 |             73.6 |                     1362 |
| EDDF      | nan     |      51891 |                   0 |                   3.4 |             15.2 |               9   |               21.6 |             53.6 |                      677 |
| EDDM      | 2025-01 |      10899 |                   0 |                   9.7 |             69.6 |              10.9 |                7.8 |              4.2 |                      165 |
| EDDM      | 2025-07 |       5761 |                   0 |                  13.9 |             57.6 |              13.4 |               14.2 |              5.5 |                      202 |
| EDDM      | 2026-01 |      10430 |                   0 |                  10.3 |             70.2 |              11.5 |                7.4 |              2.9 |                      136 |
| EDDM      | 2026-07 |      14491 |                   0 |                  14.8 |             55.2 |              17.7 |               15.1 |              2.5 |                      166 |
| EDDM      | nan     |      41581 |                   0 |                  12.2 |             63.1 |              13.7 |               11   |              3.5 |                      166 |
| EGLL      | 2025-01 |       5668 |                   0 |                   1.2 |             30.3 |               4.9 |               12.9 |             51.6 |                     1287 |
| EGLL      | 2025-07 |       2066 |                   0 |                   1.7 |             10   |               2.8 |                6.3 |             80.8 |                     2430 |
| EGLL      | 2026-01 |      12355 |                   0 |                   1.6 |             43.2 |               9   |               20.9 |             26.2 |                      447 |
| EGLL      | 2026-07 |      20018 |                   0 |                   1.9 |             78.2 |               9.6 |                7.2 |              3.5 |                      170 |
| EGLL      | nan     |      40107 |                   0 |                   1.7 |             57.1 |               8.4 |               12.2 |             21.3 |                      522 |
| EHAM      | 2025-01 |      17982 |                   0 |                   5.3 |             56.9 |              16.5 |               20.5 |              2.9 |                      173 |
| EHAM      | 2025-07 |      21780 |                   0 |                   4.2 |             73.2 |              11.3 |                9.1 |              3.3 |                      155 |
| EHAM      | 2026-01 |      15457 |                   0 |                   4.1 |             70.3 |              11.1 |               12.3 |              3.3 |                      169 |
| EHAM      | 2026-07 |      21263 |                   0 |                   3.9 |             75.5 |               9.4 |                8.1 |              4   |                      170 |
| EHAM      | nan     |      76482 |                   0 |                   4.3 |             69.4 |              11.9 |               12.1 |              3.4 |                      166 |
| LEBL      | 2025-01 |      11854 |                   0 |                  10.8 |             23.9 |              13   |               16.1 |             44   |                      678 |
| LEBL      | 2025-07 |      13716 |                   0 |                  10.3 |             33.1 |              11.5 |               17.9 |             33.8 |                      604 |
| LEBL      | 2026-01 |      10692 |                   0 |                  11.2 |             32.3 |              11.9 |               21.7 |             30   |                      552 |
| LEBL      | 2026-07 |      16437 |                   0 |                  10.4 |             37.3 |              13.4 |               19.6 |             25.4 |                      564 |
| LEBL      | nan     |      52699 |                   0 |                  10.6 |             32.2 |              12.5 |               18.8 |             32.7 |                      594 |
| LEMD      | 2025-07 |        745 |                   0 |                   1.2 |             20   |               6.3 |               14.8 |             58.7 |                     1323 |
| LEMD      | 2026-01 |      15874 |                   0 |                   1.2 |             29.9 |              10.8 |               26.2 |             32.7 |                      494 |
| LEMD      | 2026-07 |       9025 |                   0 |                   1.2 |             32.9 |               6.4 |               11.4 |             48.9 |                     1600 |
| LEMD      | nan     |      25644 |                   0 |                   1.2 |             30.7 |               9.1 |               20.7 |             39.1 |                      660 |
| LFPG      | 2025-07 |       1368 |                   0 |                   6   |              0.9 |               0.3 |                3.9 |             94.9 |                     2208 |
| LFPG      | 2026-01 |       1503 |                   0 |                   2.8 |              0.6 |               0.4 |                8.5 |             90.5 |                     1756 |
| LFPG      | 2026-07 |       1803 |                   0 |                   4.8 |              1.3 |               1.1 |                8.2 |             89.3 |                     1655 |
| LFPG      | nan     |       4674 |                   0 |                   4.5 |              1   |               0.6 |                7   |             91.3 |                     1793 |
| LIRF      | 2025-07 |      12357 |                   0 |                   1   |              8.2 |               3.1 |               11.6 |             77   |                     1009 |
| LIRF      | 2026-01 |       6994 |                   0 |                   1.7 |             20.5 |               4.4 |               11.7 |             63   |                     1358 |
| LIRF      | 2026-07 |         16 |                   0 |                   0   |              0   |               0   |               31.3 |             68.8 |                      618 |
| LIRF      | nan     |      19367 |                   0 |                   1.2 |             12.6 |               3.6 |               11.6 |             72   |                     1059 |
| LSZH      | 2025-01 |       7810 |                   0 |                   3.7 |             45.6 |               7.8 |               32.4 |             12.5 |                      326 |
| LSZH      | 2025-07 |       9762 |                   0 |                   3.8 |             35.3 |               5.2 |               34.8 |             23.3 |                      404 |
| LSZH      | 2026-01 |       8578 |                   0 |                   3.1 |             52.5 |               5.1 |               25.6 |             15.1 |                      369 |
| LSZH      | 2026-07 |      11656 |                   0 |                   3.1 |             32   |              10.6 |               34   |             22.4 |                      430 |
| LSZH      | nan     |      37806 |                   0 |                   3.4 |             40.3 |               7.4 |               32   |             19   |                      387 |
| LTFM      | 2026-07 |          4 |                   0 |                   0   |              0   |               0   |                0   |            100   |                     3153 |
| LTFM      | nan     |          4 |                   0 |                   0   |              0   |               0   |                0   |            100   |                     3153 |
| nan       | nan     |     350255 |                   0 |                   5.3 |             43.6 |              10   |               17.1 |             26.9 |                      527 |
