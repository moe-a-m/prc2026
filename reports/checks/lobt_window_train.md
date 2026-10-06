# Check: lobt_window_train

Run at 2026-10-06T17:53:23+00:00 (UTC), duckdb 1.5.6.

2025 departures: |BLOCK − LOBT| = |d_lobt − y| (d_lobt = take-off − NM LOBT). Claim to verify (rival repo EnioAguiar/prc-taxiout-2026 @30e23de, docs/research/2026-09-27-janela-lobt.md): ≤ 3606 s for every row with an LOBT.

```sql
SELECT airport, count(*) AS n, count(d_lobt) AS n_lobt,
  count(*) FILTER (WHERE d_lobt IS NOT NULL AND abs(d_lobt - y) > 3606) AS n_outside_3606,
  max(abs(d_lobt - y)) AS max_abs_block_minus_lobt_s,
  count(*) FILTER (WHERE d_lobt IS NULL) AS n_no_lobt
FROM feat_dep WHERE ds = 'train' GROUP BY ROLLUP (airport) ORDER BY airport NULLS LAST
```

11 rows

| airport   |       n |   n_lobt |   n_outside_3606 |   max_abs_block_minus_lobt_s |   n_no_lobt |
|:----------|--------:|---------:|-----------------:|-----------------------------:|------------:|
| EDDF      |  230141 |   228185 |                0 |                         3605 |        1956 |
| EDDM      |  167334 |   166324 |                0 |                         3606 |        1010 |
| EGLL      |  239546 |   238132 |                0 |                         3606 |        1414 |
| EHAM      |  247951 |   243867 |                0 |                         3602 |        4084 |
| LEBL      |  179705 |   177843 |                0 |                         3606 |        1862 |
| LEMD      |  212242 |   211295 |                0 |                         3606 |         947 |
| LFPG      |  239552 |   235779 |                0 |                         3606 |        3773 |
| LIRF      |  160704 |   159216 |                0 |                         3606 |        1488 |
| LSZH      |  134907 |   132616 |                0 |                         3602 |        2291 |
| LTFM      |  272965 |   269320 |                0 |                         3606 |        3645 |
| nan       | 2085047 |  2062577 |                0 |                         3606 |       22470 |
