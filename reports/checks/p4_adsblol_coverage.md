# Check: p4_adsblol_coverage

Run at 2026-10-03T20:23:23+00:00 (UTC), duckdb 1.5.6.

Departures on the 24 UTC days with adsb.lol extracts so far (2026-10-03). Share of departures with a matched take-off, a ground (taxi) segment, seen parked (≥ 60 s stationary at segment start), seen within 60 m of the OSM stand, seen stationary there. Points/gaps are on the ground segment. Drift check 2025 vs 2026 per CLAUDE.md §3 (a participant 27/09: receiver network changed).

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
| EDDF      | 2025-01 |        5 |    2424 |          95.3 |         71   |               5.8 |                10.1 |                  5.3 |               22 |             108 |
| EDDF      | 2025-07 |        5 |    3413 |          93.6 |         82.1 |               6.9 |                14.8 |                  7.1 |               30 |              97 |
| EDDF      | 2026-01 |        7 |    3533 |          90.9 |         55.4 |               4   |                 8.5 |                  3.9 |               15 |             103 |
| EDDF      | 2026-07 |        7 |    4656 |          87.1 |         66   |               3   |                 6.1 |                  2   |               10 |             117 |
| EDDF      | nan     |       24 |   14026 |          91   |         68.1 |               4.7 |                 9.6 |                  4.3 |               17 |             107 |
| EDDM      | 2025-01 |        5 |    1793 |          99.6 |         99.1 |              27.5 |                68.8 |                 39.7 |               89 |             138 |
| EDDM      | 2025-07 |        5 |    2544 |          82.5 |          0.1 |               0   |                 0   |                  0   |                7 |              45 |
| EDDM      | 2026-01 |        7 |    2539 |          97.9 |         97.7 |              28.4 |                69.5 |                 40.4 |              111 |             125 |
| EDDM      | 2026-07 |        7 |    3333 |          97.3 |         97.1 |              27.6 |                53.6 |                 31.5 |               99 |              88 |
| EDDM      | nan     |       24 |   10209 |          94.2 |         73.4 |              20.9 |                46.9 |                 27.3 |               99 |             107 |
| EGLL      | 2025-01 |        5 |    3156 |          89   |         26.5 |               2.7 |                 7.6 |                  4.3 |               15 |             182 |
| EGLL      | 2025-07 |        5 |    3327 |          83.3 |          8.4 |               0.4 |                 1.1 |                  0.4 |                5 |             159 |
| EGLL      | 2026-01 |        7 |    4399 |          90.8 |         41.4 |               4.4 |                19.5 |                  9.1 |               39 |             252 |
| EGLL      | 2026-07 |        7 |    4628 |          97.4 |         97.2 |              21.5 |                74.6 |                 42.7 |               86 |             193 |
| EGLL      | nan     |       24 |   15510 |          90.8 |         47.9 |               8.3 |                29.6 |                 16.3 |               65 |             203 |
| EHAM      | 2025-01 |        5 |    3080 |          98.5 |         95.9 |              13.3 |                53.3 |                 34.4 |               75 |              87 |
| EHAM      | 2025-07 |        5 |    3534 |          97.4 |         97.3 |              21.1 |                72.5 |                 51   |              111 |              79 |
| EHAM      | 2026-01 |        7 |    2509 |          96.7 |         96.2 |              21.3 |                67.2 |                 45.1 |              149 |              85 |
| EHAM      | 2026-07 |        7 |    4955 |          97.2 |         97   |              20.7 |                73.1 |                 51.5 |              136 |              79 |
| EHAM      | nan     |       24 |   14078 |          97.4 |         96.7 |              19.3 |                67.6 |                 46.5 |              109 |              80 |
| LEBL      | 2025-01 |        5 |    2274 |          99.6 |         98.7 |               7.7 |                24   |                 10.6 |               83 |             129 |
| LEBL      | 2025-07 |        5 |    2625 |          96.3 |         91.1 |              15.4 |                35.8 |                 19.4 |               96 |             112 |
| LEBL      | 2026-01 |        7 |    3114 |          98   |         91.6 |              10.6 |                32.2 |                 17.3 |               75 |             131 |
| LEBL      | 2026-07 |        7 |    4063 |          97.2 |         90.4 |              19.5 |                39.2 |                 22.5 |              117 |              97 |
| LEBL      | nan     |       24 |   12076 |          97.7 |         92.4 |              14.1 |                33.8 |                 18.2 |               92 |             118 |
| LEMD      | 2025-01 |        5 |    2752 |          81.1 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LEMD      | 2025-07 |        5 |    3019 |          88.5 |         11.9 |               1.3 |                 3.2 |                  1.4 |               85 |             105 |
| LEMD      | 2026-01 |        7 |    3864 |          97.4 |         97.2 |              10.4 |                33.2 |                 15.6 |               96 |              90 |
| LEMD      | 2026-07 |        7 |    4551 |          90.1 |         58.6 |               6.7 |                18.1 |                  9.2 |               35 |             192 |
| LEMD      | nan     |       24 |   14186 |          90   |         47.8 |               5.2 |                15.5 |                  7.5 |               75 |             114 |
| LFPG      | 2025-01 |        5 |    3196 |          64.1 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LFPG      | 2025-07 |        5 |    3254 |          73.4 |          4.2 |               0.2 |                 0.1 |                  0.1 |                4 |             120 |
| LFPG      | 2026-01 |        7 |    4226 |          77.2 |         15.2 |               0.4 |                 0.1 |                  0   |                5 |             182 |
| LFPG      | 2026-07 |        7 |    4842 |          76.1 |         17.2 |               0.3 |                 0.1 |                  0.1 |                5 |             149 |
| LFPG      | nan     |       24 |   15518 |          73.4 |         10.4 |               0.2 |                 0.1 |                  0   |                5 |             155 |
| LIRF      | 2025-01 |        5 |    2062 |          30.8 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LIRF      | 2025-07 |        5 |    2391 |          96   |         81.4 |               3   |                 8.6 |                  3.4 |               31 |             105 |
| LIRF      | 2026-01 |        7 |    2772 |          90.5 |         61.4 |               3.3 |                10.4 |                  4.4 |               13 |             114 |
| LIRF      | 2026-07 |        7 |    3570 |          29.3 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LIRF      | nan     |       24 |   10795 |          60.1 |         33.8 |               1.5 |                 4.6 |                  1.9 |               21 |             108 |
| LSZH      | 2025-01 |        5 |    1657 |          96.9 |         78.7 |              14.4 |                33.9 |                 23.3 |               67 |              80 |
| LSZH      | 2025-07 |        5 |    2011 |          95.3 |         79.2 |              13.5 |                26.9 |                 20.3 |               80 |              78 |
| LSZH      | 2026-01 |        7 |    2349 |          96.5 |         89   |              14   |                46.2 |                 29.8 |               95 |              80 |
| LSZH      | 2026-07 |        7 |    2936 |          96.2 |         90.3 |               4.8 |                28.2 |                  9   |               47 |              80 |
| LSZH      | nan     |       24 |    8953 |          96.2 |         85.3 |              11   |                33.7 |                 19.6 |               66 |              80 |
| LTFM      | 2025-01 |        5 |    3529 |           0   |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LTFM      | 2025-07 |        5 |    3983 |           0.3 |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LTFM      | 2026-01 |        7 |    5102 |           0   |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LTFM      | 2026-07 |        7 |    5645 |           3   |          0   |               0   |                 0   |                  0   |              nan |             nan |
| LTFM      | nan     |       24 |   18259 |           1   |          0   |               0   |                 0   |                  0   |              nan |             nan |
| nan       | nan     |       24 |  133610 |          75.9 |         51.6 |               7.8 |                22.5 |                 13.2 |               70 |             108 |
