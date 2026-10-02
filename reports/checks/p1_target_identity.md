# Check: p1_target_identity

Run at 2026-10-02T10:11:48+00:00 (UTC), duckdb 1.5.6.

Identity: DEP target = MVT − BLOCK; ARR presumably BLOCK − MVT (taxi-in).

```sql
SELECT PHASE_mvt, count(*) n, count(TAXITIME_SEC_mvt) n_target,
  sum((TAXITIME_SEC_mvt = epoch(MVT_TIME_UTC_mvt) - epoch(BLOCK_TIME_UTC_mvt))::INT) n_exact,
  sum((abs(TAXITIME_SEC_mvt - (epoch(MVT_TIME_UTC_mvt) - epoch(BLOCK_TIME_UTC_mvt))) <= 1)::INT) n_within_1s,
  sum((TAXITIME_SEC_mvt = epoch(BLOCK_TIME_UTC_mvt) - epoch(MVT_TIME_UTC_mvt))::INT) n_exact_reversed,
  max(abs(TAXITIME_SEC_mvt - (epoch(MVT_TIME_UTC_mvt) - epoch(BLOCK_TIME_UTC_mvt)))) max_abs_diff
FROM raw_training GROUP BY ALL
```

2 rows

| PHASE_mvt   |       n |   n_target |      n_exact |   n_within_1s |   n_exact_reversed |   max_abs_diff |
|:------------|--------:|-----------:|-------------:|--------------:|-------------------:|---------------:|
| DEP         | 2085047 |    2085047 |  2.08505e+06 |   2.08505e+06 |       19           |    0           |
| ARR         | 2082750 |    2082749 | 16           |  16           |        2.08275e+06 |    1.20959e+06 |
