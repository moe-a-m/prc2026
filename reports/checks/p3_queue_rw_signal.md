# Check: p3_queue_rw_signal

Run at 2026-10-02T13:23:57+00:00 (UTC), duckdb 1.5.6.

Pearson correlation with taxi-out (2025, y ≤ 3 h): same-runway vs whole-airport take-offs since AOBT_3.

```sql
SELECT f.airport, round(corr(q.n_rw_takeoffs_since_aobt3, f.y),3) corr_rw_aobt3, round(corr(f.n_takeoffs_since_aobt3, f.y),3) corr_ap_aobt3,
       round(corr(q.n_rw_takeoffs_since_sched, f.y),3) corr_rw_sched, round(avg(q.n_rw_takeoffs_since_aobt3),1) mean_rw_q
FROM feat_dep f JOIN feat_dep_queue_rw q USING (mvt_id) WHERE f.ds='train' AND f.y <= 3*3600 GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

11 rows

| airport   |   corr_rw_aobt3 |   corr_ap_aobt3 |   corr_rw_sched |   mean_rw_q |
|:----------|----------------:|----------------:|----------------:|------------:|
| EDDF      |           0.467 |           0.449 |           0.232 |         5.7 |
| EDDM      |           0.102 |           0.049 |           0.252 |         3.3 |
| EGLL      |           0.441 |           0.463 |           0.325 |        14.8 |
| EHAM      |           0.489 |           0.438 |           0.192 |         6.7 |
| LEBL      |           0.432 |           0.477 |           0.253 |         6.5 |
| LEMD      |           0.272 |           0.247 |           0.204 |         4.9 |
| LFPG      |           0.326 |           0.384 |           0.224 |         5.6 |
| LIRF      |           0.131 |           0.263 |           0.257 |         5.6 |
| LSZH      |           0.134 |           0.356 |           0.163 |         3.5 |
| LTFM      |           0.124 |           0.193 |           0.24  |         7.6 |
| nan       |           0.434 |           0.371 |           0.281 |         6.7 |
