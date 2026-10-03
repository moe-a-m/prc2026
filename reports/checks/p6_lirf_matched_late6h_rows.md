# Check: p6_lirf_matched_late6h_rows

Run at 2026-10-03T05:57:01+00:00 (UTC), duckdb 1.5.6.

LIRF NM-matched 2025 departures >= 6 h late: NM timestamps vs label (minutes), EXP-031 hold-out error share.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof)
SELECT c.month, c.flight_mvt, c.callsign, c.ades_mvt, c.ades_flt,
  round((epoch(c.t_mvt)-epoch(c.t_sched))/60) d_sched_min, round((epoch(c.t_mvt)-epoch(c.t_aobt3))/60) d_aobt3_min,
  round((epoch(c.t_mvt)-epoch(c.t_lobt))/60) d_lobt_min, round((epoch(c.t_mvt)-epoch(c.t_eobt1))/60) d_eobt1_min,
  round(c.y/60) y_min, round(o.pred/60) pred_min, round(100*o.se/tot_se,2) pct_sq_err
FROM clean_dep c LEFT JOIN oof o USING (mvt_id), tot
WHERE c.ds='train' AND c.airport='LIRF' AND NOT c.f_no_nm_match AND epoch(c.t_mvt)-epoch(c.t_sched) >= 21600
ORDER BY o.se DESC NULLS LAST, d_sched_min LIMIT 60
```

60 rows

| month               | flight_mvt   | callsign   | ades_mvt   | ades_flt   |   d_sched_min |   d_aobt3_min |   d_lobt_min |   d_eobt1_min |   y_min |   pred_min |   pct_sq_err |
|:--------------------|:-------------|:-----------|:-----------|:-----------|--------------:|--------------:|-------------:|--------------:|--------:|-----------:|-------------:|
| 2025-07-01 00:00:00 | AEZ146R      | AEZ146R    | LICJ       | LICJ       |          1450 |          1453 |         1450 |          1450 |    1450 |        742 |         4.15 |
| 2025-07-01 00:00:00 | NOSS95ML     | NOS95ML    | HESH       | HESH       |           459 |            18 |           -1 |            14 |      15 |        327 |         0.8  |
| 2025-07-01 00:00:00 | AAR562       | AAR562     | RKSI       | RKSI       |           397 |            18 |           27 |            27 |      19 |        140 |         0.12 |
| 2025-07-01 00:00:00 | ETH508       | ETH508     | KEWR       | KEWR       |           377 |            19 |           27 |            32 |      30 |        -57 |         0.06 |
| 2025-07-01 00:00:00 | UAL885       | UAL885     | KIAD       | KIAD       |           470 |            17 |           85 |            60 |      61 |        135 |         0.05 |
| 2025-07-01 00:00:00 | AIZIZ336     | AIZ336     | LLBG       | LLBG       |           487 |            18 |           22 |            16 |      21 |         63 |         0.01 |
| 2025-07-01 00:00:00 | TAM8121      | TAM8121    | SBGR       | SBGR       |           604 |            20 |           44 |            36 |      30 |         -8 |         0.01 |
| 2025-07-01 00:00:00 | TAM8121      | TAM8121    | SBGR       | SBGR       |           473 |            18 |           28 |            23 |      20 |        -18 |         0.01 |
| 2025-07-01 00:00:00 | NBTBT40H     | NBT40H     | KJFK       | KJFK       |           384 |            18 |           30 |            30 |      18 |        -12 |         0.01 |
| 2025-01-01 00:00:00 | ABRBR898     | ABR898     | EBLG       | EBLG       |           747 |            17 |           22 |            28 |      12 |         34 |         0    |
| 2025-07-01 00:00:00 | NBT40H       | NBT40H     | KJFK       | KJFK       |           361 |            17 |           19 |            19 |      16 |         -6 |         0    |
| 2025-07-01 00:00:00 | TAR753       | TAR753     | DTTA       | DTTA       |           551 |            19 |           16 |            16 |      11 |        -10 |         0    |
| 2025-07-01 00:00:00 | WMT7DQ       | WMT7DQ     | LATI       | LATI       |           432 |            20 |           52 |            42 |      27 |          7 |         0    |
| 2025-01-01 00:00:00 | WZZ3BV       | WZZ3BV     | EGKK       | EGKK       |           560 |            16 |           30 |            41 |      25 |         45 |         0    |
| 2025-01-01 00:00:00 | RYRR8009     | RYR8009    | LIPX       | LIPX       |           500 |            16 |           40 |            31 |      20 |         39 |         0    |
| 2025-07-01 00:00:00 | FIN4NC       | FIN4NC     | EFHK       | EFHK       |           365 |            15 |           35 |            35 |      10 |         -8 |         0    |
| 2025-07-01 00:00:00 | AAL239       | AAL239     | KDFW       | KDFW       |           410 |            18 |           35 |            30 |      22 |          5 |         0    |
| 2025-07-01 00:00:00 | SWU1974      | SWU1974    | LQMO       | LQMO       |           466 |             8 |           11 |            11 |       6 |         23 |         0    |
| 2025-07-01 00:00:00 | ITY1767      | ITY1767    | LICJ       | LICJ       |           368 |            10 |           38 |            28 |      19 |          6 |         0    |
| 2025-07-01 00:00:00 | ITY792       | ITY792     | RJTT       | RJTT       |           389 |            15 |           24 |            24 |      22 |         29 |         0    |
| 2025-07-01 00:00:00 | AEZZ141W     | AEZ141W    | LICJ       | LICJ       |           375 |            22 |           15 |            15 |      10 |         14 |         0    |
| 2025-09-01 00:00:00 | VLG650D      | VLG650D    | LEBL       | LEBL       |           360 |            17 |           25 |            25 |      17 |        nan |       nan    |
| 2025-09-01 00:00:00 | AAL239       | AAL239     | KDFW       | KDFW       |           361 |            19 |           29 |            23 |      15 |        nan |       nan    |
| 2025-08-01 00:00:00 | TAR753       | TAR753     | DTTA       | DTTA       |           362 |            17 |           12 |            12 |      14 |        nan |       nan    |
| 2025-05-01 00:00:00 | UAL3934      | UAL3934    | KEWR       | KEWR       |           364 |            16 |           64 |            29 |      29 |        nan |       nan    |
| 2025-03-01 00:00:00 | DAL67        | DAL67      | KATL       | KATL       |           364 |            16 |            4 |            14 |      16 |        nan |       nan    |
| 2025-04-01 00:00:00 | RYR7451      | RYR7451    | LEBL       | LEBL       |           365 |            13 |           20 |            20 |      14 |        nan |       nan    |
| 2025-02-01 00:00:00 | CCA732       | CCA732     | ZSHC       | ZSHC       |           367 |            13 |            7 |            15 |      15 |        nan |       nan    |
| 2025-08-01 00:00:00 | WMT1605      | WMT1605    | LFMN       | LFMN       |           369 |            14 |           49 |            26 |      16 |        nan |       nan    |
| 2025-04-01 00:00:00 | WZZZZ6KG     | WZZ6KG     | EPWA       | EPWA       |           371 |            13 |           31 |            20 |      12 |        nan |       nan    |
| 2025-02-01 00:00:00 | IBE06TR      | IBE06TR    | LEMD       | LEMD       |           375 |            13 |           10 |            13 |      13 |        nan |       nan    |
| 2025-10-01 00:00:00 | CYFYF131     | CYF131     | LLBG       | LLBG       |           375 |            12 |           30 |            19 |      15 |        nan |       nan    |
| 2025-10-01 00:00:00 | DAL113       | DAL113     | KBOS       | KBOS       |           375 |            14 |            5 |            20 |      18 |        nan |       nan    |
| 2025-04-01 00:00:00 | QTR7R        | QTR7R      | OTHH       | OTHH       |           376 |            20 |           38 |            39 |      28 |        nan |       nan    |
| 2025-08-01 00:00:00 | VLG93TY      | VLG93TY    | LEBL       | LEBL       |           378 |            14 |           16 |            16 |      13 |        nan |       nan    |
| 2025-03-01 00:00:00 | EZSS93XP     | EZS93XP    | LFSB       | LFSB       |           378 |            16 |            8 |            13 |      12 |        nan |       nan    |
| 2025-06-01 00:00:00 | WMT2911      | WMT2911    | LEMD       | LEMD       |           379 |            16 |           54 |            29 |      24 |        nan |       nan    |
| 2025-03-01 00:00:00 | AFRR33GM     | AFR33GM    | LFPG       | LFPG       |           380 |            11 |           15 |            15 |      11 |        nan |       nan    |
| 2025-06-01 00:00:00 | RYRR9945     | RYR9945    | LOWW       | LOWW       |           381 |            15 |           35 |            26 |      21 |        nan |       nan    |
| 2025-09-01 00:00:00 | WMT8989      | WMT8989    | LCLK       | LCLK       |           384 |            19 |           64 |            34 |      17 |        nan |       nan    |
| 2025-10-01 00:00:00 | AAL239       | AAL239     | KDFW       | KDFW       |           386 |            18 |           21 |            27 |      19 |        nan |       nan    |
| 2025-11-01 00:00:00 | GFA026       | GFA026     | OBBI       | OBBI       |           388 |            18 |           23 |            18 |      18 |        nan |       nan    |
| 2025-06-01 00:00:00 | RYR2ZV       | RYR2ZV     | LMML       | LMML       |           392 |            26 |           22 |            22 |      22 |        nan |       nan    |
| 2025-10-01 00:00:00 | NBT41L       | NBT41L     | KLAX       | KLAX       |           393 |            17 |           33 |            33 |      27 |        nan |       nan    |
| 2025-08-01 00:00:00 | ITY650       | ITY650     | CYYZ       | CYYZ       |           396 |            21 |           51 |            49 |      20 |        nan |       nan    |
| 2025-06-01 00:00:00 | DAL207       | DAL207     | KDTW       | KDTW       |           397 |            22 |           67 |            35 |      24 |        nan |       nan    |
| 2025-08-01 00:00:00 | ARGG1141     | ARG1141    | SAEZ       | SAEZ       |           401 |            23 |           26 |            26 |      26 |        nan |       nan    |
| 2025-08-01 00:00:00 | ITYTY770     | ITY770     | VIDP       | VIDP       |           404 |            20 |           29 |            39 |      19 |        nan |       nan    |
| 2025-02-01 00:00:00 | TAP839       | TAP839     | LPPT       | LPPT       |           405 |            15 |           20 |            27 |      14 |        nan |       nan    |
| 2025-04-01 00:00:00 | WMT7TL       | WMT7TL     | LROP       | LROP       |           407 |            13 |           27 |            27 |      31 |        nan |       nan    |
| 2025-06-01 00:00:00 | RYR3571      | RYR3571    | EIDW       | EIDW       |           408 |            17 |           32 |            28 |      17 |        nan |       nan    |
| 2025-05-01 00:00:00 | TVFF35XC     | TVF35XC    | LFPO       | LFPO       |           408 |            13 |           18 |            22 |      12 |        nan |       nan    |
| 2025-10-01 00:00:00 | AFR16TY      | AFR16TY    | LFPG       | LFPG       |           411 |            13 |           12 |            12 |      10 |        nan |       nan    |
| 2025-06-01 00:00:00 | DAL215       | DAL215     | KATL       | KATL       |           413 |            22 |           38 |            28 |      30 |        nan |       nan    |
| 2025-06-01 00:00:00 | NBT40H       | NBT40H     | KJFK       | KJFK       |           414 |            18 |           26 |            27 |      23 |        nan |       nan    |
| 2025-10-01 00:00:00 | WZZ60DA      | WZZ60DA    | EPKT       | EPKT       |           421 |            12 |           16 |            16 |      13 |        nan |       nan    |
| 2025-11-01 00:00:00 | TAP8RL       | TAP8RL     | LPPT       | LPPT       |           423 |            13 |           48 |            38 |      10 |        nan |       nan    |
| 2025-08-01 00:00:00 | SWU9580      | SWU9580    | LIMP       | LIMP       |           424 |             9 |           24 |            24 |       5 |        nan |       nan    |
| 2025-02-01 00:00:00 | VOE2YJ       | VOE2YJ     | LFST       | LFST       |           441 |            12 |           12 |            12 |      12 |        nan |       nan    |
| 2025-06-01 00:00:00 | RYR52AZ      | RYR52AZ    | LGKO       | LGKO       |           452 |            21 |           37 |            32 |      21 |        nan |       nan    |
