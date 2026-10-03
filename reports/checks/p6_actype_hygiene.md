# Check: p6_actype_hygiene

Run at 2026-10-03T06:04:35+00:00 (UTC), duckdb 1.5.6.

Aircraft type code (ACTYPE_mvt) pattern classes for departures; mismatch count vs NM type.

```sql
WITH b AS (SELECT airport, ds, actype_mvt a, actype_flt f FROM clean_dep)
SELECT CASE WHEN a IS NULL THEN 'null' WHEN regexp_matches(a, '^[A-Z][A-Z0-9]{1,3}$') THEN 'icao-like' WHEN a <> upper(a) THEN 'lowercase' ELSE 'other' END cls,
  count(*) FILTER (ds='train') n_train, count(*) FILTER (ds='rank') n_rank,
  count(*) FILTER (a IS NOT NULL AND f IS NOT NULL AND a <> f) n_neq_flt,
  string_agg(DISTINCT a, ',') FILTER (NOT regexp_matches(coalesce(a,'A1'), '^[A-Z][A-Z0-9]{1,3}$')) examples
FROM b GROUP BY 1 ORDER BY 2 DESC
```

2 rows

| cls       |   n_train |   n_rank |   n_neq_flt | examples   |
|:----------|----------:|---------:|------------:|:-----------|
| icao-like |   2083540 |   344453 |        7625 |            |
| null      |      1507 |      388 |           0 |            |
