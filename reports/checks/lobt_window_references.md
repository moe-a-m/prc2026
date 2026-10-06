# Check: lobt_window_references

Run at 2026-10-06T18:03:47+00:00 (UTC), duckdb 1.5.6.

Hard-edge test per NM/airport reference time (2025 departures having that reference). If the off-block (not the take-off) is bounded by exactly one reference, the bound is a property of how airport records were associated with NM flights (APDF spec Ed. 1.0 §4: AOBT is a matching key), not of operations.

```sql
WITH t AS (SELECT * FROM feat_dep WHERE ds = 'train'),
u AS (
    SELECT 'LOBT (last known off-block)' AS reference, d_lobt - y AS block_minus_ref, d_lobt AS mvt_minus_ref FROM t WHERE d_lobt IS NOT NULL
    UNION ALL SELECT 'IOBT (initial off-block)', d_iobt - y, d_iobt FROM t WHERE d_iobt IS NOT NULL
    UNION ALL SELECT 'EOBT_1 (FPL-based trajectory)', d_eobt1 - y, d_eobt1 FROM t WHERE d_eobt1 IS NOT NULL
    UNION ALL SELECT 'schedule (airport)', d_sched - y, d_sched FROM t WHERE d_sched IS NOT NULL
)
SELECT reference, count(*) AS n,
  min(block_minus_ref) AS min_block_minus_ref_s, max(block_minus_ref) AS max_block_minus_ref_s,
  count(*) FILTER (WHERE abs(block_minus_ref) > 3606) AS n_block_outside_3606,
  count(*) FILTER (WHERE abs(block_minus_ref) BETWEEN 3540 AND 3606) AS n_block_in_last_minute,
  count(*) FILTER (WHERE abs(mvt_minus_ref) > 3606) AS n_takeoff_outside_3606,
  max(abs(mvt_minus_ref)) AS max_abs_takeoff_minus_ref_s
FROM u GROUP BY reference ORDER BY reference
```

4 rows

| reference                     |       n |   min_block_minus_ref_s |   max_block_minus_ref_s |   n_block_outside_3606 |   n_block_in_last_minute |   n_takeoff_outside_3606 |   max_abs_takeoff_minus_ref_s |
|:------------------------------|--------:|------------------------:|------------------------:|-----------------------:|-------------------------:|-------------------------:|------------------------------:|
| EOBT_1 (FPL-based trajectory) | 2062577 |                  -10383 |                    8705 |                    614 |                      667 |                    20355 |                         87001 |
| IOBT (initial off-block)      | 2062577 |                   -3840 |                   10737 |                     58 |                     1157 |                    29236 |                         87001 |
| LOBT (last known off-block)   | 2062577 |                   -3606 |                    3606 |                      0 |                     1159 |                    29162 |                         87001 |
| schedule (airport)            | 2085047 |                 -114415 |                  269095 |                 107499 |                     4668 |                   193936 |                        270508 |
