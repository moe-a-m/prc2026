# Check: p1_block_echo

Run at 2026-10-02T10:12:16+00:00 (UTC), duckdb 1.5.6.

Uniform-random seconds would give pct_block_sec0 ≈ 1.67%; 5-minute marks ≈ 0.33%.

```sql
-- How often does BLOCK equal a planned time? (label-defect hypothesis raised on the forum)
SELECT ADEP_mvt ap, count(*) n,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = SCHED_TIME_UTC_mvt)::INT),2) pct_eq_sched,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = LOBT_flt)::INT),2) pct_eq_lobt,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = IOBT_flt)::INT),2) pct_eq_iobt,
 round(100.0*avg((BLOCK_TIME_UTC_mvt = EOBT_1_flt)::INT),2) pct_eq_eobt1,
 round(100.0*avg((second(BLOCK_TIME_UTC_mvt)=0)::INT),2) pct_block_sec0,
 round(100.0*avg((second(MVT_TIME_UTC_mvt)=0)::INT),2) pct_mvt_sec0,
 round(100.0*avg((minute(BLOCK_TIME_UTC_mvt)%5=0 AND second(BLOCK_TIME_UTC_mvt)=0)::INT),2) pct_block_5min
FROM raw_training WHERE PHASE_mvt='DEP' GROUP BY ROLLUP(ap) ORDER BY ap NULLS LAST
```

11 rows

| ap   |       n |   pct_eq_sched |   pct_eq_lobt |   pct_eq_iobt |   pct_eq_eobt1 |   pct_block_sec0 |   pct_mvt_sec0 |   pct_block_5min |
|:-----|--------:|---------------:|--------------:|--------------:|---------------:|-----------------:|---------------:|-----------------:|
| EDDF |  230141 |           0.06 |          0.07 |          0.07 |           0.07 |             1.69 |           1.77 |             0.34 |
| EDDM |  167334 |           0.41 |          0.48 |          0.48 |           0.54 |             8.34 |           8.31 |             1.62 |
| EGLL |  239546 |           0.43 |          0.48 |          0.48 |           0.58 |             8.38 |           8.28 |             1.77 |
| EHAM |  247951 |           0.06 |          0.08 |          0.08 |           0.08 |             1.69 |           1.73 |             0.36 |
| LEBL |  179705 |           0.47 |          0.58 |          0.59 |           0.66 |             8.3  |           1.66 |             1.86 |
| LEMD |  212242 |           0.36 |          0.46 |          0.46 |           0.54 |             8.37 |           1.64 |             1.75 |
| LFPG |  239552 |           0.37 |          0.48 |          0.48 |           0.52 |             8.28 |           8.32 |             1.66 |
| LIRF |  160704 |           1.51 |          1.49 |          1.49 |           1.47 |             8.35 |           8.38 |             3.31 |
| LSZH |  134907 |           0.05 |          0.06 |          0.06 |           0.07 |             1.98 |           1.68 |             0.33 |
| LTFM |  272965 |           0.41 |          0.44 |          0.45 |           0.44 |             8.3  |           8.33 |             1.66 |
| nan  | 2085047 |           0.39 |          0.44 |          0.44 |           0.48 |             6.4  |           5.13 |             1.44 |
