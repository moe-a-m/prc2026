# Check: p1_aobt3_error

Run at 2026-10-02T10:12:15+00:00 (UTC), duckdb 1.5.6.

Naive estimate taxi = MVT − AOBT_3_flt on rows where AOBT_3 exists.

```sql
-- error of the naive estimate MVT - AOBT_3 vs target, DEP train
WITH d AS (SELECT ADEP_mvt ap, TAXITIME_SEC_mvt y, epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt) x,
                  second(AOBT_3_flt) s3 FROM raw_training WHERE PHASE_mvt='DEP')
SELECT ap, count(*) n, count(x) n_aobt3,
  round(100.0*avg((s3=0)::INT),2) pct_aobt3_round_min,
  round(sqrt(avg((x-y)^2)),1) rmse, round(median(x-y),1) med_err,
  round(100.0*avg((abs(x-y)<=60)::INT),2) pct_within_60s, round(100.0*avg((abs(x-y)<=180)::INT),2) pct_within_180s,
  round(quantile_cont(abs(x-y),0.9),1) p90_abs, round(quantile_cont(abs(x-y),0.99),1) p99_abs
FROM d GROUP BY ROLLUP(ap) ORDER BY ap NULLS LAST
```

11 rows

| ap   |       n |   n_aobt3 |   pct_aobt3_round_min |   rmse |   med_err |   pct_within_60s |   pct_within_180s |   p90_abs |   p99_abs |
|:-----|--------:|----------:|----------------------:|-------:|----------:|-----------------:|------------------:|----------:|----------:|
| EDDF |  230141 |    228185 |                 99.04 |  255.1 |        87 |            20.97 |             59.82 |       339 |       745 |
| EDDM |  167334 |    166324 |                 99.94 |  348.9 |        -2 |            25.72 |             64.74 |       476 |      1375 |
| EGLL |  239546 |    238132 |                 99.99 |  418.5 |        54 |            19.35 |             51.29 |       484 |      1564 |
| EHAM |  247951 |    243867 |                 83.8  |  329.6 |       107 |            23.67 |             61.73 |       433 |      1258 |
| LEBL |  179705 |    177843 |                 99.57 |  311.4 |       -54 |            26.35 |             63.38 |       419 |      1204 |
| LEMD |  212242 |    211295 |                 99.72 |  276.4 |         2 |            26.25 |             66.65 |       357 |      1079 |
| LFPG |  239552 |    235779 |                 99.72 |  379.5 |        -4 |            21.94 |             54.71 |       536 |      1085 |
| LIRF |  160704 |    159216 |                 99.57 |  557.4 |      -118 |            18.55 |             46.72 |       718 |      2282 |
| LSZH |  134907 |    132616 |                 99.99 |  268.4 |       -33 |            24.23 |             60.57 |       373 |       804 |
| LTFM |  272965 |    269320 |                 98.91 |  530.6 |       296 |             8.69 |             25.85 |       664 |      1624 |
| nan  | 2085047 |   2062577 |                 97.7  |  384.9 |        51 |            21.02 |             54.48 |       513 |      1321 |
