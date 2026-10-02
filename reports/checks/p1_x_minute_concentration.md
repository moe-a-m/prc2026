# Check: p1_x_minute_concentration

Run at 2026-10-02T10:13:13+00:00 (UTC), duckdb 1.5.6.

Top-4 rounded-minute values of MVT−AOBT_3 per airport, with error of x vs target in each bin.

```sql
WITH d AS (SELECT ADEP_mvt ap, RUNWAY_mvt rwy, round((epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt))/60) xm,
                  TAXITIME_SEC_mvt y, epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt) x
           FROM raw_training WHERE PHASE_mvt='DEP' AND AOBT_3_flt IS NOT NULL),
c AS (SELECT ap, xm, count(*) n, sqrt(avg((x-y)^2)) rmse_x, avg((abs(x-y)<=60)::INT) w60 FROM d GROUP BY ALL),
r AS (SELECT *, row_number() OVER (PARTITION BY ap ORDER BY n DESC) rk, n/sum(n) OVER (PARTITION BY ap) AS shr FROM c)
SELECT ap, rk, xm AS x_minutes, n, round(100*shr,1) pct, round(rmse_x,0) rmse_x, round(100*w60,1) pct_within60
FROM r WHERE rk<=4 ORDER BY ap, rk
```

40 rows

| ap   |   rk |   x_minutes |      n |   pct |   rmse_x |   pct_within60 |
|:-----|-----:|------------:|-------:|------:|---------:|---------------:|
| EDDF |    1 |          14 |  26724 |  11.7 |      205 |           22.9 |
| EDDF |    2 |          15 |  25231 |  11.1 |      217 |           20.7 |
| EDDF |    3 |          13 |  21370 |   9.4 |      215 |           22.4 |
| EDDF |    4 |          19 |  18692 |   8.2 |      240 |           20.8 |
| EDDM |    1 |          12 |  40039 |  24.1 |      197 |           27.6 |
| EDDM |    2 |          11 |  35040 |  21.1 |      183 |           31.6 |
| EDDM |    3 |          14 |  19240 |  11.6 |      188 |           29.1 |
| EDDM |    4 |          13 |  18012 |  10.8 |      201 |           29.8 |
| EGLL |    1 |          22 |  16073 |   6.7 |      319 |           22.2 |
| EGLL |    2 |          23 |  15981 |   6.7 |      267 |           20.8 |
| EGLL |    3 |          20 |  15870 |   6.7 |      254 |           22.8 |
| EGLL |    4 |          21 |  15348 |   6.4 |      265 |           22.2 |
| EHAM |    1 |          10 |  29464 |  12.1 |      160 |           31.3 |
| EHAM |    2 |          12 |  22836 |   9.4 |      179 |           28.8 |
| EHAM |    3 |          11 |  22383 |   9.2 |      163 |           31.8 |
| EHAM |    4 |          15 |  18877 |   7.7 |      218 |           23   |
| LEBL |    1 |          21 |  32251 |  18.1 |      259 |           23.5 |
| LEBL |    2 |          11 |  31068 |  17.5 |      253 |           30.5 |
| LEBL |    3 |          20 |  24057 |  13.5 |      272 |           24.1 |
| LEBL |    4 |          12 |  22191 |  12.5 |      256 |           29.2 |
| LEMD |    1 |          16 |  32704 |  15.5 |      210 |           27.8 |
| LEMD |    2 |          17 |  25961 |  12.3 |      208 |           26.4 |
| LEMD |    3 |          19 |  20397 |   9.7 |      215 |           26   |
| LEMD |    4 |          18 |  20040 |   9.5 |      225 |           25.4 |
| LFPG |    1 |          13 |  27158 |  11.5 |      308 |           26.2 |
| LFPG |    2 |          14 |  25172 |  10.7 |      305 |           24.7 |
| LFPG |    3 |          15 |  23983 |  10.2 |      298 |           25.1 |
| LFPG |    4 |          11 |  19722 |   8.4 |      359 |           28.3 |
| LIRF |    1 |          14 |  23910 |  15   |      444 |           22.4 |
| LIRF |    2 |          15 |  20115 |  12.6 |      510 |           19.9 |
| LIRF |    3 |          13 |  18744 |  11.8 |      484 |           21.1 |
| LIRF |    4 |          17 |  15184 |   9.5 |      564 |           17.6 |
| LSZH |    1 |          12 |  25458 |  19.2 |      244 |           26.4 |
| LSZH |    2 |          11 |  21380 |  16.1 |      265 |           26.7 |
| LSZH |    3 |          10 |  21186 |  16   |      240 |           27   |
| LSZH |    4 |           9 |  20929 |  15.8 |      239 |           23   |
| LTFM |    1 |          20 | 113198 |  42   |      390 |            8.9 |
| LTFM |    2 |          25 |  55234 |  20.5 |      534 |            5.3 |
| LTFM |    3 |          19 |  50234 |  18.7 |      374 |           10.5 |
| LTFM |    4 |          24 |  25278 |   9.4 |      510 |            6.1 |
