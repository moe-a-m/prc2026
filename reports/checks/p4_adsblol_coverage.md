# Check: p4_adsblol_coverage

Run at 2026-10-05T10:49:19+00:00 (UTC), duckdb 1.5.6.

Departures on the 124 UTC days with adsb.lol extracts (full Jan + Jul 2025/2026 archive). Share of departures with a matched take-off, a ground (taxi) segment, seen parked (≥ 60 s stationary at segment start), seen within 60 m of the OSM stand, seen stationary there. Points/gaps are on the ground segment. Drift check 2025 vs 2026 per CLAUDE.md §3 (a participant 27/09: receiver network changed).

```sql
WITH days AS (SELECT DISTINCT t::DATE AS day FROM stg_adsb),
d AS (
    SELECT f.airport, strftime(f.month, '%Y-%m') AS ym, timezone('UTC', to_timestamp(f.t_mvt_epoch))::DATE AS day, a.*,
           coalesce(s.adsb_still_at_stand, false) AS still_at_stand, coalesce(s.adsb_seen_at_stand, false) AS seen_at_stand
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE timezone('UTC', to_timestamp(f.t_mvt_epoch))::DATE IN (SELECT day FROM days)
      AND month(f.month) IN (1, 7)  -- extracts spill a few hours into adjacent days (e.g. 30 Jun)
)
SELECT airport, ym, count(DISTINCT day) AS n_days, count(*) AS n_dep,
  round(100*avg(adsb_matched::INT), 1) AS pct_matched,
  round(100*avg(coalesce(adsb_has_ground, false)::INT), 1) AS pct_ground,
  round(100*avg(coalesce(adsb_seen_parked, false)::INT), 1) AS pct_seen_parked,
  round(100*avg(seen_at_stand::INT), 1) AS pct_seen_at_stand,
  round(100*avg(still_at_stand::INT), 1) AS pct_still_at_stand,
  round(median(adsb_n_pts) FILTER (WHERE adsb_has_ground), 0) AS med_pts_ground,
  round(median(adsb_max_gap_s) FILTER (WHERE adsb_has_ground), 0) AS med_max_gap_s
FROM d GROUP BY ROLLUP (airport, ym) ORDER BY airport NULLS LAST, ym NULLS LAST
```

51 rows

| airport   | ym      |   n_days |   n_dep |   pct_matched |   pct_ground |   pct_seen_parked |   pct_seen_at_stand |   pct_still_at_stand |   med_pts_ground |   med_max_gap_s |
|:----------|:--------|---------:|--------:|--------------:|-------------:|------------------:|--------------------:|---------------------:|-----------------:|----------------:|
| EDDF      | 2025-01 |       31 |   15496 |          95.9 |         78.6 |               5.7 |                12.9 |                  5.9 |               26 |              98 |
| EDDF      | 2025-07 |       31 |   21334 |          94.1 |         81.8 |               8   |                16.7 |                  8   |               33 |             102 |
| EDDF      | 2026-01 |       31 |   15667 |          89.4 |         59.9 |               3   |                 7.3 |                  3   |               16 |             106 |
| EDDF      | 2026-07 |       31 |   20650 |          86.2 |         62.4 |               2.7 |                 5.7 |                  1.9 |                9 |             114 |
| EDDF      | nan     |      124 |   73147 |          91.2 |         70.9 |               4.9 |                10.8 |                  4.7 |               20 |             105 |
| EDDM      | 2025-01 |       31 |   11266 |          99.3 |         96.7 |              26.6 |                67.3 |                 39.1 |              104 |             120 |
| EDDM      | 2025-07 |       31 |   15825 |          88.5 |         36.4 |               9.7 |                21   |                 12.4 |               98 |             119 |
| EDDM      | 2026-01 |       31 |   10953 |          95.4 |         95.2 |              27.3 |                66.9 |                 39.1 |              123 |             120 |
| EDDM      | 2026-07 |       31 |   15013 |          96.7 |         96.5 |              27.5 |                53.2 |                 31.2 |              104 |              90 |
| EDDM      | nan     |      124 |   53057 |          94.5 |         78.4 |              22   |                49.4 |                 28.9 |              108 |             107 |
| EGLL      | 2025-01 |       31 |   19420 |          90.7 |         29.2 |               2.6 |                 8.8 |                  4.3 |               17 |             177 |
| EGLL      | 2025-07 |       31 |   20790 |          83.3 |          9.9 |               0.7 |                 1   |                  0.5 |                6 |             174 |
| EGLL      | 2026-01 |       31 |   19283 |          91   |         64.1 |               5.8 |                27.7 |                 12   |               37 |             252 |
| EGLL      | 2026-07 |       31 |   20557 |          97.6 |         97.4 |              22.8 |                76.1 |                 43.3 |               92 |             194 |
| EGLL      | nan     |      124 |   80050 |          90.6 |         50.1 |               8.1 |                28.6 |                 15.2 |               58 |             207 |
| EHAM      | 2025-01 |       31 |   18460 |          98.9 |         97.4 |              13.4 |                55.4 |                 34.6 |               90 |              80 |
| EHAM      | 2025-07 |       31 |   22489 |          97.1 |         96.8 |              20.8 |                70.8 |                 49.7 |              131 |              79 |
| EHAM      | 2026-01 |       31 |   16232 |          95.5 |         95.2 |              18.4 |                66.9 |                 44.8 |              146 |              80 |
| EHAM      | 2026-07 |       31 |   21950 |          97.1 |         96.9 |              20.6 |                73.1 |                 50.8 |              160 |              79 |
| EHAM      | nan     |      124 |   79131 |          97.2 |         96.7 |              18.5 |                67.1 |                 45.5 |              126 |              80 |
| LEBL      | 2025-01 |       31 |   12234 |          99.1 |         96.9 |               7.1 |                23.2 |                  9.7 |               77 |             130 |
| LEBL      | 2025-07 |       31 |   16752 |          96.7 |         81.9 |              10.4 |                27.1 |                 14.7 |               76 |             131 |
| LEBL      | 2026-01 |       31 |   12201 |          94.9 |         87.6 |               9.7 |                28.3 |                 15.1 |               72 |             125 |
| LEBL      | 2026-07 |       31 |   17879 |          97   |         91.9 |              15.1 |                34.3 |                 18.4 |               87 |             127 |
| LEBL      | nan     |      124 |   59066 |          96.9 |         89.2 |              11   |                28.7 |                 14.9 |               78 |             128 |
| LEMD      | 2025-01 |       31 |   16510 |          48.6 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LEMD      | 2025-07 |       31 |   18818 |          88.3 |          4   |               0.3 |                 0.8 |                  0.4 |               21 |              94 |
| LEMD      | 2026-01 |       31 |   16802 |          94.7 |         94.5 |               9.6 |                28.2 |                 13.4 |               91 |              93 |
| LEMD      | 2026-07 |       31 |   20152 |          89.6 |         44.8 |               5.2 |                14.7 |                  7.4 |               37 |             197 |
| LEMD      | nan     |      124 |   72282 |          81.1 |         35.5 |               3.8 |                10.9 |                  5.3 |               75 |             112 |
| LFPG      | 2025-01 |       31 |   17900 |          60.5 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LFPG      | 2025-07 |       31 |   21712 |          73.7 |          6.3 |               0.3 |                 0.1 |                  0   |                3 |              75 |
| LFPG      | 2026-01 |       31 |   18129 |          72.3 |          8.3 |               0.2 |                 0   |                  0   |                4 |             144 |
| LFPG      | 2026-07 |       31 |   21743 |          75.3 |          8.3 |               0.2 |                 0.1 |                  0   |                4 |             168 |
| LFPG      | nan     |      124 |   79484 |          70.8 |          5.9 |               0.2 |                 0.1 |                  0   |                4 |             134 |
| LIRF      | 2025-01 |       31 |   11317 |          37.7 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LIRF      | 2025-07 |       31 |   15211 |          96.1 |         81.2 |               2.4 |                 6.6 |                  2.7 |               36 |              94 |
| LIRF      | 2026-01 |       31 |   11061 |          90.2 |         63.2 |               3.6 |                13   |                  5.3 |               14 |             113 |
| LIRF      | 2026-07 |       31 |   15838 |          65.3 |          0.1 |               0   |                 0   |                  0   |                7 |             146 |
| LIRF      | nan     |      124 |   53427 |          73.4 |         36.2 |               1.4 |                 4.6 |                  1.9 |               27 |              99 |
| LSZH      | 2025-01 |       31 |    9735 |          97.1 |         80.2 |              14.9 |                36.6 |                 25.6 |               76 |              79 |
| LSZH      | 2025-07 |       31 |   12611 |          94.2 |         77.4 |              13.5 |                27.3 |                 20.8 |               81 |              77 |
| LSZH      | 2026-01 |       31 |    9995 |          94.6 |         85.8 |              13.6 |                45.1 |                 29.5 |               95 |              80 |
| LSZH      | 2026-07 |       31 |   13155 |          95.8 |         88.6 |               4.8 |                28.3 |                  9   |               46 |              84 |
| LSZH      | nan     |      124 |   45496 |          95.4 |         83.1 |              11.3 |                33.5 |                 20.3 |               69 |              80 |
| LTFM      | 2025-01 |       31 |   21368 |           0   |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LTFM      | 2025-07 |       31 |   25171 |           0   |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LTFM      | 2026-01 |       31 |   22396 |           0.6 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LTFM      | 2026-07 |       31 |   25185 |           3.4 |          0   |               0   |                 0   |                  0   |                2 |              35 |
| LTFM      | nan     |      124 |   94120 |           1.1 |          0   |               0   |                 0   |                  0   |                2 |              35 |
| nan       | nan     |      124 |  689260 |          75.7 |         50.8 |               7.5 |                22.1 |                 13   |               72 |             105 |
