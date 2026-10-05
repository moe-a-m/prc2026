# Check: p4_adsblol_moving_at_stand_EXP-051

Run at 2026-10-05T11:54:26+00:00 (UTC), duckdb 1.5.6.

Rows seen within 60 m of the own OSM stand but never stationary there (M-021 fallback: first at-stand observation = lower bound on taxi-out) vs EXP-051 hold-out predictions, all extracted 2025 days.

```sql
WITH o AS (SELECT mvt_id, pred FROM read_parquet(['models/oof/EXP-051_jan.parquet', 'models/oof/EXP-051_jul.parquet'])),
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

44 rows

| airport   | gap       |     n |   med_est_minus_y |   rmse_model |   rmse_est |   medae_model |   medae_est |
|:----------|:----------|------:|------------------:|-------------:|-----------:|--------------:|------------:|
| EDDF      | a ≤60     |  2385 |               -25 |         65.4 |       72   |          25.4 |        26   |
| EDDF      | b 60–180  |   515 |               -52 |        130.7 |      167.4 |          81.8 |        53.2 |
| EDDF      | c 180–600 |    24 |              -371 |        222.8 |      332.1 |         190.5 |       371   |
| EDDF      | d >600    |    28 |               -91 |        648.1 |     1046.4 |         569.3 |       129.8 |
| EDDF      | nan       |  2952 |               -30 |        104   |      142.7 |          30.6 |        30.4 |
| EDDM      | a ≤60     |  3841 |               -38 |         40.7 |       52.3 |          20.7 |        38.6 |
| EDDM      | b 60–180  |   618 |               -44 |         98.8 |       97.1 |          67.8 |        44.6 |
| EDDM      | c 180–600 |    35 |               -44 |        278.6 |      131.7 |         170.1 |        44.1 |
| EDDM      | d >600    |    40 |               -27 |        766   |     1479.3 |         700.8 |        56.7 |
| EDDM      | nan       |  4534 |               -39 |         92.2 |      151.8 |          23.8 |        39.4 |
| EGLL      | a ≤60     |    32 |              -128 |        123.6 |      136.8 |         118   |       128.5 |
| EGLL      | b 60–180  |   673 |              -146 |         71.8 |      175.1 |          42.6 |       146.1 |
| EGLL      | c 180–600 |   268 |              -179 |        131.7 |      256.9 |          86.2 |       179   |
| EGLL      | d >600    |    13 |              -357 |       1004   |      604.4 |         495.7 |       357.5 |
| EGLL      | nan       |   986 |              -154 |        148.4 |      210.4 |          53.3 |       154.1 |
| EHAM      | a ≤60     |  6484 |                 7 |         81.7 |       86.2 |          16.5 |        15.2 |
| EHAM      | b 60–180  |  1991 |              -153 |        150.7 |      201.5 |         105.6 |       162.1 |
| EHAM      | c 180–600 |    24 |                16 |        234.2 |      197.5 |         182   |        19.7 |
| EHAM      | d >600    |    88 |                10 |        860.5 |     1030.7 |         689.2 |        24.7 |
| EHAM      | nan       |  8587 |                 5 |        134.3 |      161.3 |          24.7 |        17.7 |
| LEBL      | a ≤60     |  3152 |               -26 |        138.7 |      143.5 |          26.1 |        29.3 |
| LEBL      | b 60–180  |   543 |               -36 |        247.3 |      259   |          85.6 |        39.2 |
| LEBL      | c 180–600 |     7 |               -41 |        270.7 |      177.1 |         153.1 |        40.8 |
| LEBL      | d >600    |    24 |               -54 |        762.2 |     1380.9 |         715.6 |        91.1 |
| LEBL      | nan       |  3726 |               -28 |        170.5 |      198.8 |          31   |        30.7 |
| LEMD      | a ≤60     |    28 |              -118 |        123.6 |      156.6 |          81.9 |       118   |
| LEMD      | b 60–180  |    43 |              -137 |        102.2 |      190.2 |          38.2 |       137.5 |
| LEMD      | c 180–600 |     3 |              -503 |        278.6 |      453.6 |         294.2 |       502.8 |
| LEMD      | d >600    |     4 |              -571 |        307.5 |      538   |         182.1 |       570.6 |
| LEMD      | nan       |    78 |              -140 |        138.1 |      226.9 |          62   |       140.1 |
| LFPG      | a ≤60     |     7 |               -45 |         31.8 |       52.7 |          17.9 |        44.6 |
| LFPG      | b 60–180  |     1 |               -50 |         46   |       50.3 |          46   |        50.3 |
| LFPG      | nan       |     8 |               -47 |         33.9 |       52.4 |          23.3 |        47   |
| LIRF      | a ≤60     |   268 |               -68 |        202.5 |      216.2 |          48.7 |        71.7 |
| LIRF      | b 60–180  |   246 |              -140 |        271.5 |      339.2 |          95.9 |       141.7 |
| LIRF      | c 180–600 |    28 |               -91 |        338.4 |      426.2 |         131.8 |        91.2 |
| LIRF      | d >600    |    56 |              -157 |       2239.9 |     2117.7 |         766.6 |       157   |
| LIRF      | nan       |   598 |               -99 |        723.8 |      704.8 |          91.1 |       105.2 |
| LSZH      | a ≤60     |  1512 |               -32 |         70   |       76.8 |          16.8 |        32.9 |
| LSZH      | b 60–180  |   307 |               -43 |        158.1 |      183.8 |          84.4 |        45   |
| LSZH      | c 180–600 |    36 |              -133 |        307.8 |      348.2 |         175.1 |       133.2 |
| LSZH      | d >600    |    33 |               -40 |       1334.9 |      548   |         698.3 |        50.2 |
| LSZH      | nan       |  1888 |               -34 |        202.3 |      133.3 |          21.7 |        35.3 |
| nan       | nan       | 23357 |               -25 |        178.9 |      197.8 |          27.6 |        30.9 |
