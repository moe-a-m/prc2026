# Check: p4_adsblol_moving_at_stand_EXP-045

Run at 2026-10-05T11:19:06+00:00 (UTC), duckdb 1.5.6.

Rows seen within 60 m of the own OSM stand but never stationary there (M-021 fallback: first at-stand observation = lower bound on taxi-out) vs EXP-045 hold-out predictions, all extracted 2025 days.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-045_jan.parquet', 'models/oof/EXP-045_jul.parquet'])),
e AS (SELECT f.airport, f.y, o.pred, s.adsb_stand_first_s AS est
      FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb_stand s USING (mvt_id)
      WHERE s.adsb_seen_at_stand AND NOT s.adsb_still_at_stand AND s.adsb_stand_first_s IS NOT NULL)
SELECT airport, CASE WHEN abs(est - pred) <= 60 THEN 'a ≤60' WHEN abs(est - pred) <= 180 THEN 'b 60–180'
                     WHEN abs(est - pred) <= 600 THEN 'c 180–600' ELSE 'd >600' END AS gap,
  count(*) n, round(median(est - y), 0) med_est_minus_y, round(sqrt(avg((pred - y)^2)), 1) rmse_model,
  round(sqrt(avg((est - y)^2)), 1) rmse_est, round(median(abs(pred - y)), 1) medae_model,
  round(median(abs(est - y)), 1) medae_est
FROM e GROUP BY ROLLUP (airport, gap) ORDER BY airport NULLS LAST, gap NULLS LAST
```

45 rows

| airport   | gap       |     n |   med_est_minus_y |   rmse_model |   rmse_est |   medae_model |   medae_est |
|:----------|:----------|------:|------------------:|-------------:|-----------:|--------------:|------------:|
| EDDF      | a ≤60     |   916 |               -20 |         73.3 |       70.5 |          33.9 |        21   |
| EDDF      | b 60–180  |  1264 |               -27 |        116.2 |       73.1 |          89.1 |        29   |
| EDDF      | c 180–600 |   741 |               -46 |        237.1 |      154.9 |         203.3 |        46.5 |
| EDDF      | d >600    |    31 |               -95 |        627.5 |      999.8 |         523.2 |       137.3 |
| EDDF      | nan       |  2952 |               -30 |        160.3 |      142.7 |          84.4 |        30.4 |
| EDDM      | a ≤60     |  1644 |               -38 |         58.1 |       52.1 |          37.2 |        38   |
| EDDM      | b 60–180  |  2095 |               -39 |        109.4 |       52.5 |          89.8 |        39.3 |
| EDDM      | c 180–600 |   752 |               -42 |        272.5 |       94.3 |         233.7 |        43.1 |
| EDDM      | d >600    |    43 |               -30 |        754.7 |     1426.8 |         685.2 |        53   |
| EDDM      | nan       |  4534 |               -39 |        156.4 |      151.8 |          77.2 |        39.4 |
| EGLL      | a ≤60     |   114 |              -141 |        158.5 |      159.8 |         140.4 |       141.1 |
| EGLL      | b 60–180  |   280 |              -147 |        118.3 |      169.5 |          49.6 |       147.3 |
| EGLL      | c 180–600 |   560 |              -159 |        200.9 |      214.7 |         145.4 |       159.5 |
| EGLL      | d >600    |    32 |              -342 |        716.1 |      464.3 |         472.2 |       342.3 |
| EGLL      | nan       |   986 |              -154 |        215.5 |      210.4 |         122.3 |       154.1 |
| EHAM      | a ≤60     |  2863 |                 8 |         71.6 |       65.2 |          32.2 |        14   |
| EHAM      | b 60–180  |  3415 |                 7 |        121.3 |       92.9 |          97.4 |        15.8 |
| EHAM      | c 180–600 |  2219 |              -152 |        207.6 |      199.5 |         157.2 |       160.7 |
| EHAM      | d >600    |    90 |                10 |        855.3 |     1019.2 |         677.5 |        24.7 |
| EHAM      | nan       |  8587 |                 5 |        162.4 |      161.3 |          76.2 |        17.7 |
| LEBL      | a ≤60     |  1240 |               -25 |        145.6 |      144.3 |          34.9 |        28   |
| LEBL      | b 60–180  |  1684 |               -27 |        163.2 |      134.7 |          98.9 |        30.2 |
| LEBL      | c 180–600 |   777 |               -34 |        315.9 |      240.9 |         220.8 |        36.1 |
| LEBL      | d >600    |    25 |               -58 |        748.6 |     1354.9 |         714.9 |       115.7 |
| LEBL      | nan       |  3726 |               -28 |        209   |      198.8 |          91.1 |        30.7 |
| LEMD      | a ≤60     |     6 |              -118 |        120.6 |      123.7 |         102.5 |       117.6 |
| LEMD      | b 60–180  |    18 |              -118 |        113.3 |      169.1 |          58.1 |       118   |
| LEMD      | c 180–600 |    47 |              -137 |        185.3 |      186.5 |         159   |       137.5 |
| LEMD      | d >600    |     7 |              -503 |        291.7 |      503.6 |         109.5 |       502.8 |
| LEMD      | nan       |    78 |              -140 |        180   |      226.9 |         112.6 |       140.1 |
| LFPG      | a ≤60     |     2 |               -37 |         65.9 |       37.5 |          47.5 |        36.6 |
| LFPG      | b 60–180  |     5 |               -49 |        113.9 |       57.6 |          96.9 |        49.4 |
| LFPG      | c 180–600 |     1 |               -50 |        198.2 |       50.3 |         198.2 |        50.3 |
| LFPG      | nan       |     8 |               -47 |        118.8 |       52.4 |          95.1 |        47   |
| LIRF      | a ≤60     |    87 |               -62 |        150.3 |      150.3 |          57.5 |        66.5 |
| LIRF      | b 60–180  |   149 |               -72 |        150.1 |      189.9 |          87.5 |        74   |
| LIRF      | c 180–600 |   300 |              -135 |        321.2 |      355.1 |         212.7 |       138.9 |
| LIRF      | d >600    |    62 |              -125 |       2133.3 |     2015.6 |         716.9 |       125.3 |
| LIRF      | nan       |   598 |               -99 |        729.7 |      704.8 |         161.2 |       105.2 |
| LSZH      | a ≤60     |   565 |               -29 |         72.2 |       69   |          30.7 |        30.2 |
| LSZH      | b 60–180  |   823 |               -34 |        122.4 |       82.5 |          89.1 |        34.3 |
| LSZH      | c 180–600 |   463 |               -40 |        264.7 |      182   |         204.9 |        42.2 |
| LSZH      | d >600    |    37 |               -40 |       1275   |      517.9 |         680.9 |        50.2 |
| LSZH      | nan       |  1888 |               -34 |        239   |      133.3 |          85.2 |        35.3 |
| nan       | nan       | 23357 |               -25 |        212.1 |      197.8 |          83.1 |        30.9 |
