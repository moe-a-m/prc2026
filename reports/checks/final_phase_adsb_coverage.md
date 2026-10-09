# Check: final_phase_adsb_coverage

Run at 2026-10-09T13:10:12+00:00 (UTC), duckdb 1.5.6.

adsb.lol coverage on the 485 extracted UTC days (all of 2025; Jan, Feb, Jun, Jul 2026): share of departures with a ground (taxi) segment, seen within 60 m of their OSM stand, seen stationary there (the M-028 'still' source). Receiver-network drift 2025→2026 per CLAUDE.md §3.

```sql
WITH days AS (SELECT DISTINCT t::DATE AS day FROM stg_adsb),
d AS (
    SELECT f.airport, strftime(f.month, '%Y-%m') AS ym, f.ds,
           coalesce(a.adsb_has_ground, false) AS has_ground,
           coalesce(s.adsb_seen_at_stand, false) AS seen_at_stand,
           coalesce(s.adsb_still_at_stand, false) AS still_at_stand
    FROM feat_dep f LEFT JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE timezone('UTC', to_timestamp(f.t_mvt_epoch))::DATE IN (SELECT day FROM days)
)
SELECT airport, ym, ds, count(*) AS n_dep,
  round(100 * avg(has_ground::INT), 1) AS pct_ground,
  round(100 * avg(seen_at_stand::INT), 1) AS pct_seen_at_stand,
  round(100 * avg(still_at_stand::INT), 1) AS pct_still_at_stand
FROM d GROUP BY ALL ORDER BY airport, ym
```

160 rows

| airport   | ym      | ds    |   n_dep |   pct_ground |   pct_seen_at_stand |   pct_still_at_stand |
|:----------|:--------|:------|--------:|-------------:|--------------------:|---------------------:|
| EDDF      | 2025-01 | train |   15496 |         78.6 |                12.9 |                  5.9 |
| EDDF      | 2025-02 | train |   15099 |         90.1 |                18.4 |                  8.5 |
| EDDF      | 2025-03 | train |   17636 |         91.7 |                19.9 |                  9.2 |
| EDDF      | 2025-04 | train |   19583 |         91.3 |                17.9 |                  8.5 |
| EDDF      | 2025-05 | train |   21130 |         89.7 |                16.2 |                  7.7 |
| EDDF      | 2025-06 | train |   20706 |         84.8 |                15.4 |                  7.3 |
| EDDF      | 2025-07 | train |   21334 |         81.9 |                16.7 |                  8   |
| EDDF      | 2025-08 | train |   21468 |         83.8 |                19.2 |                  9.2 |
| EDDF      | 2025-09 | train |   21004 |         87.5 |                37.8 |                 19.8 |
| EDDF      | 2025-10 | train |   21239 |         83.5 |                25   |                 12.2 |
| EDDF      | 2025-11 | train |   18122 |         88.6 |                45.4 |                 22.3 |
| EDDF      | 2025-12 | train |   17324 |         89.2 |                42.5 |                 20.8 |
| EDDF      | 2026-01 | rank  |   15667 |         59.9 |                 7.3 |                  3   |
| EDDF      | 2026-02 | rank  |   14654 |         11.6 |                 1.2 |                  0.4 |
| EDDF      | 2026-06 | rank  |   19700 |         62.6 |                 7.3 |                  2.5 |
| EDDF      | 2026-07 | rank  |   20650 |         62.3 |                 5.7 |                  1.9 |
| EDDM      | 2025-01 | train |   11266 |         96.7 |                67.3 |                 39.1 |
| EDDM      | 2025-02 | train |   10381 |         89.6 |                62.2 |                 35.5 |
| EDDM      | 2025-03 | train |   12513 |         89.7 |                61.6 |                 34.9 |
| EDDM      | 2025-04 | train |   14326 |         82.6 |                48.8 |                 27.3 |
| EDDM      | 2025-05 | train |   15798 |         92.2 |                47.9 |                 26.2 |
| EDDM      | 2025-06 | train |   15661 |         66.6 |                36.1 |                 20.5 |
| EDDM      | 2025-07 | train |   15825 |         36.4 |                21   |                 12.4 |
| EDDM      | 2025-08 | train |   15562 |         77.1 |                40.5 |                 24.1 |
| EDDM      | 2025-09 | train |   15936 |         85.7 |                44.4 |                 25.8 |
| EDDM      | 2025-10 | train |   15469 |         93.8 |                53.4 |                 31.8 |
| EDDM      | 2025-11 | train |   12562 |         97   |                64   |                 36.8 |
| EDDM      | 2025-12 | train |   12035 |         96.8 |                65.4 |                 37.5 |
| EDDM      | 2026-01 | rank  |   10953 |         95.2 |                66.9 |                 39.1 |
| EDDM      | 2026-02 | rank  |   10534 |         97.2 |                68.1 |                 39.5 |
| EDDM      | 2026-06 | rank  |   14372 |         88.2 |                45.6 |                 26.5 |
| EDDM      | 2026-07 | rank  |   15013 |         96.5 |                53.3 |                 31.2 |
| EGLL      | 2025-01 | train |   19420 |         29.2 |                 8.8 |                  4.3 |
| EGLL      | 2025-02 | train |   17956 |         22.4 |                 8.5 |                  4.2 |
| EGLL      | 2025-03 | train |   19251 |         14.5 |                 4.5 |                  2.2 |
| EGLL      | 2025-04 | train |   20229 |          5.5 |                 1.1 |                  0.5 |
| EGLL      | 2025-05 | train |   20791 |          4.7 |                 0.5 |                  0.2 |
| EGLL      | 2025-06 | train |   20063 |          8.8 |                 0.6 |                  0.3 |
| EGLL      | 2025-07 | train |   20790 |          9.9 |                 1   |                  0.5 |
| EGLL      | 2025-08 | train |   20828 |         14.4 |                 1.3 |                  0.5 |
| EGLL      | 2025-09 | train |   20138 |         16   |                 1.2 |                  0.5 |
| EGLL      | 2025-10 | train |   20657 |         25.1 |                 4.7 |                  2.6 |
| EGLL      | 2025-11 | train |   19423 |         33.1 |                14.6 |                  6.5 |
| EGLL      | 2025-12 | train |   20000 |         41.3 |                15.3 |                  6.4 |
| EGLL      | 2026-01 | rank  |   19283 |         64.1 |                27.7 |                 12   |
| EGLL      | 2026-02 | rank  |   17719 |         57.7 |                23.4 |                  9.8 |
| EGLL      | 2026-06 | rank  |   19662 |         89.1 |                69   |                 39.9 |
| EGLL      | 2026-07 | rank  |   20557 |         97.4 |                76.1 |                 43.3 |
| EHAM      | 2025-01 | train |   18460 |         97.4 |                55.4 |                 34.6 |
| EHAM      | 2025-02 | train |   17852 |         96.7 |                55   |                 34.1 |
| EHAM      | 2025-03 | train |   20224 |         96.4 |                55.1 |                 34.7 |
| EHAM      | 2025-04 | train |   20935 |         84.1 |                30.9 |                 18.4 |
| EHAM      | 2025-05 | train |   22173 |         91.8 |                51.1 |                 34.3 |
| EHAM      | 2025-06 | train |   21257 |         97.7 |                64.2 |                 44.9 |
| EHAM      | 2025-07 | train |   22489 |         96.8 |                70.8 |                 49.7 |
| EHAM      | 2025-08 | train |   22621 |         96.8 |                69.4 |                 47.7 |
| EHAM      | 2025-09 | train |   21466 |         96.9 |                69.5 |                 49.1 |
| EHAM      | 2025-10 | train |   21784 |         96.6 |                71.5 |                 50.9 |
| EHAM      | 2025-11 | train |   19232 |         97   |                68.1 |                 45.8 |
| EHAM      | 2025-12 | train |   19458 |         97   |                66.1 |                 43.8 |
| EHAM      | 2026-01 | rank  |   16232 |         95.3 |                66.9 |                 44.8 |
| EHAM      | 2026-02 | rank  |   16802 |         96.9 |                64.5 |                 42.7 |
| EHAM      | 2026-06 | rank  |   20881 |         88.7 |                64.2 |                 44.3 |
| EHAM      | 2026-07 | rank  |   21950 |         96.9 |                73.1 |                 50.8 |
| LEBL      | 2025-01 | train |   12234 |         96.9 |                23.2 |                  9.7 |
| LEBL      | 2025-02 | train |   12169 |         97.9 |                24.6 |                 10   |
| LEBL      | 2025-03 | train |   14147 |         97.8 |                22.4 |                  9.9 |
| LEBL      | 2025-04 | train |   15374 |         98.2 |                29.7 |                 15.4 |
| LEBL      | 2025-05 | train |   16507 |         97.8 |                31.8 |                 17.7 |
| LEBL      | 2025-06 | train |   16315 |         95.6 |                40.1 |                 22.6 |
| LEBL      | 2025-07 | train |   16752 |         81.9 |                27.1 |                 14.7 |
| LEBL      | 2025-08 | train |   16596 |         91.1 |                38.7 |                 21.3 |
| LEBL      | 2025-09 | train |   16144 |         82   |                26.2 |                 14.2 |
| LEBL      | 2025-10 | train |   16300 |         85.4 |                29.4 |                 15.4 |
| LEBL      | 2025-11 | train |   13332 |         90.6 |                33.3 |                 19.4 |
| LEBL      | 2025-12 | train |   13835 |         94.6 |                33.7 |                 17.8 |
| LEBL      | 2026-01 | rank  |   12201 |         87.6 |                28.3 |                 15.1 |
| LEBL      | 2026-02 | rank  |   12167 |         91.4 |                27   |                 14.1 |
| LEBL      | 2026-06 | rank  |   17067 |         83.1 |                33.2 |                 18.3 |
| LEBL      | 2026-07 | rank  |   17879 |         91.9 |                34.3 |                 18.4 |
| LEMD      | 2025-01 | train |   16510 |          0   |                 0   |                  0   |
| LEMD      | 2025-02 | train |   15390 |          0   |                 0   |                  0   |
| LEMD      | 2025-03 | train |   17546 |         73.8 |                17.9 |                  8.5 |
| LEMD      | 2025-04 | train |   17348 |         95.8 |                23.6 |                 11.6 |
| LEMD      | 2025-05 | train |   18180 |         98   |                20.9 |                 10.2 |
| LEMD      | 2025-06 | train |   17992 |         96.7 |                22.6 |                 11.3 |
| LEMD      | 2025-07 | train |   18818 |          4   |                 0.8 |                  0.4 |
| LEMD      | 2025-08 | train |   18490 |          5.9 |                 0.8 |                  0.4 |
| LEMD      | 2025-09 | train |   17672 |         85.9 |                24.7 |                 12.8 |
| LEMD      | 2025-10 | train |   18892 |         94   |                31.7 |                 15.4 |
| LEMD      | 2025-11 | train |   17419 |         94.9 |                22   |                 10.8 |
| LEMD      | 2025-12 | train |   17985 |         96.7 |                33.3 |                 16.9 |
| LEMD      | 2026-01 | rank  |   16802 |         94.5 |                28.2 |                 13.4 |
| LEMD      | 2026-02 | rank  |   16191 |         96.5 |                25.2 |                 11.9 |
| LEMD      | 2026-06 | rank  |   19335 |         64.1 |                20.5 |                 10.8 |
| LEMD      | 2026-07 | rank  |   20152 |         44.8 |                14.7 |                  7.4 |
| LFPG      | 2025-01 | train |   17900 |          0   |                 0   |                  0   |
| LFPG      | 2025-02 | train |   16806 |          0   |                 0   |                  0   |
| LFPG      | 2025-03 | train |   19341 |          0   |                 0   |                  0   |
| LFPG      | 2025-04 | train |   20002 |          0   |                 0   |                  0   |
| LFPG      | 2025-05 | train |   20908 |          0   |                 0   |                  0   |
| LFPG      | 2025-06 | train |   20887 |          1.9 |                 0   |                  0   |
| LFPG      | 2025-07 | train |   21712 |          6.3 |                 0.1 |                  0   |
| LFPG      | 2025-08 | train |   22081 |          5.9 |                 0   |                  0   |
| LFPG      | 2025-09 | train |   20682 |          6.6 |                 0.1 |                  0   |
| LFPG      | 2025-10 | train |   20809 |         10.4 |                 0.1 |                  0   |
| LFPG      | 2025-11 | train |   18646 |         22.5 |                 0.2 |                  0   |
| LFPG      | 2025-12 | train |   19778 |          9.5 |                 0.1 |                  0   |
| LFPG      | 2026-01 | rank  |   18129 |          8.2 |                 0   |                  0   |
| LFPG      | 2026-02 | rank  |   16934 |          4.1 |                 0   |                  0   |
| LFPG      | 2026-06 | rank  |   20714 |         12.5 |                 0.2 |                  0.1 |
| LFPG      | 2026-07 | rank  |   21743 |          8.2 |                 0.1 |                  0   |
| LIRF      | 2025-01 | train |   11317 |          0   |                 0   |                  0   |
| LIRF      | 2025-02 | train |   10703 |          0   |                 0   |                  0   |
| LIRF      | 2025-03 | train |   12544 |          0   |                 0   |                  0   |
| LIRF      | 2025-04 | train |   14028 |          0   |                 0   |                  0   |
| LIRF      | 2025-05 | train |   14541 |         19.8 |                 1.2 |                  0.4 |
| LIRF      | 2025-06 | train |   14696 |         63.6 |                 8   |                  3.5 |
| LIRF      | 2025-07 | train |   15211 |         81.2 |                 6.6 |                  2.7 |
| LIRF      | 2025-08 | train |   15459 |         76.9 |                 7.1 |                  2.9 |
| LIRF      | 2025-09 | train |   14667 |         19.7 |                 2.1 |                  0.9 |
| LIRF      | 2025-10 | train |   14142 |         38.6 |                 5.9 |                  2.2 |
| LIRF      | 2025-11 | train |   11328 |         32.4 |                 5.6 |                  2.2 |
| LIRF      | 2025-12 | train |   12068 |         59.7 |                12.9 |                  5.3 |
| LIRF      | 2026-01 | rank  |   11061 |         63.2 |                13   |                  5.3 |
| LIRF      | 2026-02 | rank  |   10264 |         56.8 |                11.2 |                  4.2 |
| LIRF      | 2026-06 | rank  |   14983 |          0   |                 0   |                  0   |
| LIRF      | 2026-07 | rank  |   15838 |          0.1 |                 0   |                  0   |
| LSZH      | 2025-01 | train |    9735 |         80.2 |                36.6 |                 25.6 |
| LSZH      | 2025-02 | train |    9048 |         83.3 |                36.5 |                 25.4 |
| LSZH      | 2025-03 | train |   10449 |         80.8 |                34.1 |                 24.1 |
| LSZH      | 2025-04 | train |   11162 |         80.2 |                32.1 |                 23   |
| LSZH      | 2025-05 | train |   12040 |         80.7 |                29.7 |                 21.6 |
| LSZH      | 2025-06 | train |   12083 |         79.8 |                27.9 |                 20.9 |
| LSZH      | 2025-07 | train |   12611 |         77.4 |                27.3 |                 20.8 |
| LSZH      | 2025-08 | train |   12636 |         79.2 |                28   |                 20.7 |
| LSZH      | 2025-09 | train |   12178 |         79.7 |                28   |                 20.9 |
| LSZH      | 2025-10 | train |   12302 |         83.4 |                30.5 |                 21.2 |
| LSZH      | 2025-11 | train |   10078 |         85.8 |                32   |                 18.5 |
| LSZH      | 2025-12 | train |   10585 |         87.7 |                45.6 |                 30.3 |
| LSZH      | 2026-01 | rank  |    9995 |         85.8 |                45.1 |                 29.5 |
| LSZH      | 2026-02 | rank  |    9374 |         89.1 |                48.2 |                 30.9 |
| LSZH      | 2026-06 | rank  |   12384 |         80.2 |                25.5 |                  8.2 |
| LSZH      | 2026-07 | rank  |   13155 |         88.6 |                28.3 |                  9   |
| LTFM      | 2025-01 | train |   21368 |          0   |                 0   |                  0   |
| LTFM      | 2025-02 | train |   18327 |          0   |                 0   |                  0   |
| LTFM      | 2025-03 | train |   20799 |          0   |                 0   |                  0   |
| LTFM      | 2025-04 | train |   22301 |          0   |                 0   |                  0   |
| LTFM      | 2025-05 | train |   23134 |          0   |                 0   |                  0   |
| LTFM      | 2025-06 | train |   23482 |          0   |                 0   |                  0   |
| LTFM      | 2025-07 | train |   25171 |          0   |                 0   |                  0   |
| LTFM      | 2025-08 | train |   25440 |          0   |                 0   |                  0   |
| LTFM      | 2025-09 | train |   24064 |          0   |                 0   |                  0   |
| LTFM      | 2025-10 | train |   24080 |          0   |                 0   |                  0   |
| LTFM      | 2025-11 | train |   22190 |          0   |                 0   |                  0   |
| LTFM      | 2025-12 | train |   22609 |          0   |                 0   |                  0   |
| LTFM      | 2026-01 | rank  |   22396 |          0   |                 0   |                  0   |
| LTFM      | 2026-02 | rank  |   19519 |          0   |                 0   |                  0   |
| LTFM      | 2026-06 | rank  |   22693 |          0   |                 0   |                  0   |
| LTFM      | 2026-07 | rank  |   25185 |          0   |                 0   |                  0   |
