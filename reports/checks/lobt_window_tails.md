# Check: lobt_window_tails

Run at 2026-10-06T18:03:47+00:00 (UTC), duckdb 1.5.6.

Counts of 2025 departures by off-block − LOBT in 5-min bins, |off-block − LOBT| ≥ 40 min only: the distribution runs up to the ±1 h edge and stops (no thinning tail beyond).

```sql
SELECT (floor((d_lobt - y) / 300) * 300)::INT AS block_minus_lobt_bin_s, count(*) AS n
FROM feat_dep WHERE ds = 'train' AND d_lobt IS NOT NULL AND abs(d_lobt - y) >= 2400
GROUP BY ALL ORDER BY 1
```

11 rows

|   block_minus_lobt_bin_s |     n |
|-------------------------:|------:|
|                    -3900 |    45 |
|                    -3600 |   334 |
|                    -3300 |   365 |
|                    -3000 |   459 |
|                    -2700 |   620 |
|                    -2400 |    19 |
|                     2400 | 11284 |
|                     2700 |  7893 |
|                     3000 |  5594 |
|                     3300 |  4114 |
|                     3600 |   249 |
