# Check: p1_submitting_vs_ranking

Run at 2026-10-02T10:11:48+00:00 (UTC), duckdb 1.5.6.

```sql
SELECT
  (SELECT count(*) FROM raw_submitting) n_sub,
  (SELECT count(*) FROM raw_ranking WHERE PHASE_mvt='DEP') n_rank_dep,
  (SELECT count(*) FROM raw_submitting s ANTI JOIN (SELECT * FROM raw_ranking WHERE PHASE_mvt='DEP') r USING (MVT_ID_mvt)) sub_not_in_rank_dep,
  (SELECT count(*) FROM (SELECT * FROM raw_ranking WHERE PHASE_mvt='DEP') r ANTI JOIN raw_submitting s USING (MVT_ID_mvt)) rank_dep_not_in_sub
```

1 rows

|   n_sub |   n_rank_dep |   sub_not_in_rank_dep |   rank_dep_not_in_sub |
|--------:|-------------:|----------------------:|----------------------:|
|  344841 |       344841 |                     0 |                     0 |
