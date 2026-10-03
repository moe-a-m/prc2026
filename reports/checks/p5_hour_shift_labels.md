# Check: p5_hour_shift_labels

Run at 2026-10-03T05:31:16+00:00 (UTC), duckdb 1.5.6.

Counts of training departures whose label differs from the NM proxy MVT−AOBT_3 by about ±0.5/1/1.5/2 h (±300 s) and +1 day.

```sql
-- r = y − (MVT − AOBT_3) for NM-matched training departures. A clock/time-zone error in the airport block time would
-- create excess mass near r ≈ ±3600 / ±7200 compared with neighbouring offsets (±1800 / ±5400 as controls).
WITH d AS (SELECT airport, y - d_aobt3 AS r FROM feat_dep WHERE ds='train' AND d_aobt3 IS NOT NULL)
SELECT airport, count(*) n,
  sum((abs(r + 7200) <= 300)::INT) "≈-2h", sum((abs(r + 5400) <= 300)::INT) "≈-1.5h (ctrl)", sum((abs(r + 3600) <= 300)::INT) "≈-1h",
  sum((abs(r + 1800) <= 300)::INT) "≈-0.5h (ctrl)", sum((abs(r - 1800) <= 300)::INT) "≈+0.5h (ctrl)", sum((abs(r - 3600) <= 300)::INT) "≈+1h",
  sum((abs(r - 5400) <= 300)::INT) "≈+1.5h (ctrl)", sum((abs(r - 7200) <= 300)::INT) "≈+2h", sum((abs(r - 86400) <= 1800)::INT) "≈+1d"
FROM d GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

11 rows

| airport   |       n |   ≈-2h |   ≈-1.5h (ctrl) |   ≈-1h |   ≈-0.5h (ctrl) |   ≈+0.5h (ctrl) |   ≈+1h |   ≈+1.5h (ctrl) |   ≈+2h |   ≈+1d |
|:----------|--------:|-------:|----------------:|-------:|----------------:|----------------:|-------:|----------------:|-------:|-------:|
| EDDF      |  228185 |      0 |               0 |      0 |               6 |             161 |     22 |               5 |      5 |      0 |
| EDDM      |  166324 |      0 |               3 |      1 |               1 |             880 |     28 |               3 |      0 |      0 |
| EGLL      |  238132 |      0 |               0 |     15 |             273 |             982 |    157 |              29 |      7 |      0 |
| EHAM      |  243867 |      0 |               0 |     29 |            1039 |              20 |     17 |               5 |      3 |      0 |
| LEBL      |  177843 |      0 |               0 |      0 |               0 |             721 |     11 |               3 |      3 |      0 |
| LEMD      |  211295 |      0 |               0 |      0 |               3 |             807 |      5 |               1 |      2 |      0 |
| LFPG      |  235779 |      0 |               0 |     12 |              55 |             511 |     44 |              17 |     16 |      0 |
| LIRF      |  159216 |      0 |               0 |      1 |               5 |            1861 |    327 |              38 |      4 |      0 |
| LSZH      |  132616 |      0 |               0 |      0 |               3 |              69 |     10 |               4 |      3 |      0 |
| LTFM      |  269320 |      0 |              10 |    674 |             229 |             875 |     49 |               6 |      4 |      0 |
| nan       | 2062577 |      0 |              13 |    732 |            1614 |            6887 |    670 |             111 |     47 |      0 |
