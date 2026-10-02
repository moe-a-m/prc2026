# Check: p1_target_quantiles_dep

Run at 2026-10-02T10:11:48+00:00 (UTC), duckdb 1.5.6.

```sql
SELECT ADEP_mvt airport, count(*) n, count(TAXITIME_SEC_mvt) n_t,
  min(TAXITIME_SEC_mvt) mn, quantile_cont(TAXITIME_SEC_mvt, 0.01) p01, quantile_cont(TAXITIME_SEC_mvt, 0.5) p50,
  round(avg(TAXITIME_SEC_mvt),1) mean, round(stddev(TAXITIME_SEC_mvt),1) sd,
  quantile_cont(TAXITIME_SEC_mvt, 0.99) p99, max(TAXITIME_SEC_mvt) mx,
  sum((TAXITIME_SEC_mvt < 0)::INT) n_neg, sum((TAXITIME_SEC_mvt > 3*3600)::INT) n_gt3h
FROM raw_training WHERE PHASE_mvt='DEP' GROUP BY ALL ORDER BY 1
```

10 rows

| airport   |      n |    n_t |   mn |   p01 |   p50 |   mean |     sd |     p99 |     mx |   n_neg |   n_gt3h |
|:----------|-------:|-------:|-----:|------:|------:|-------:|-------:|--------:|-------:|--------:|---------:|
| EDDF      | 230141 | 230141 |    2 |   246 |   837 |  863.5 |  329.8 | 1819    |   6907 |       0 |        0 |
| EDDM      | 167334 | 167334 |    2 |   348 |   774 |  811.9 |  301.8 | 1921    |   6899 |       0 |        0 |
| EGLL      | 239546 | 239546 |    9 |   667 |  1319 | 1364.2 |  421.8 | 2701    |  11452 |       0 |        4 |
| EHAM      | 247951 | 247951 |   -4 |   173 |   742 |  784.6 |  318.5 | 1774.5  |  11032 |       3 |        2 |
| LEBL      | 179705 | 179705 |   -8 |   391 |   906 |  956.5 |  330.9 | 1961.96 |   3604 |       5 |        0 |
| LEMD      | 212242 | 212242 |   39 |   397 |   985 | 1014.7 |  312.5 | 1932    |   3598 |       0 |        0 |
| LFPG      | 239552 | 239552 |  -12 |   429 |   954 | 1019.5 |  453   | 2409    |  84240 |      61 |        6 |
| LIRF      | 160704 | 160704 |   49 |   417 |  1025 | 1194.6 | 1332   | 4018.97 | 131167 |       0 |      188 |
| LSZH      | 134907 | 134907 |  -12 |   190 |   711 |  740.5 |  385.4 | 1707    |  87341 |     298 |        2 |
| LTFM      | 272965 | 272965 |  -12 |   481 |   963 | 1053   |  427.6 | 2587    |  10309 |       2 |        0 |
