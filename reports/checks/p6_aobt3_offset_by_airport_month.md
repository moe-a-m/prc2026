# Check: p6_aobt3_offset_by_airport_month

Run at 2026-10-03T06:01:21+00:00 (UTC), duckdb 1.5.6.

Monthly median of the NM-proxy error (MVT-AOBT_3)-y (s) per airport, 2025 NM-matched regular rows (|error|<600 s).

```sql
WITH b AS (SELECT airport, strftime(month,'%m') mon, epoch(t_mvt)-epoch(t_aobt3) - y AS e FROM clean_dep
  WHERE ds='train' AND NOT f_no_nm_match AND t_aobt3 IS NOT NULL AND abs(epoch(t_mvt)-epoch(t_aobt3) - y) < 600)
PIVOT b ON mon USING round(median(e)) GROUP BY airport ORDER BY airport
```

10 rows

| airport   |   01 |   02 |   03 |   04 |   05 |   06 |   07 |   08 |   09 |   10 |   11 |   12 |
|:----------|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|
| EDDF      |  107 |  110 |  112 |  100 |   87 |   83 |   87 |   93 |   75 |   77 |   81 |   90 |
| EDDM      |   57 |   58 |   56 |    5 |    2 |    2 |   -4 |   -2 |   -5 |   -2 |    2 |   -2 |
| EGLL      |   57 |    5 |   55 |    4 |    5 |    4 |   54 |    5 |    5 |    5 |   54 |   55 |
| EHAM      |   93 |   94 |  105 |  104 |  105 |   96 |   96 |   98 |   94 |   97 |   89 |   87 |
| LEBL      |    1 |   -1 |   -4 |   -5 |  -56 |  -57 |  -57 |   -6 |   -6 |   -6 |   -2 |   -2 |
| LEMD      |   57 |   56 |   -1 |    6 |   54 |    1 |   -1 |   -3 |   -2 |    1 |    5 |    6 |
| LFPG      |   -3 |   -1 |   -1 |   -2 |   -3 |   -3 |  -56 |   -6 |   -6 |   -3 |   -3 |   -5 |
| LIRF      |   -6 |   -4 |  -58 |  -64 |  -65 | -115 |  -66 |  -64 |  -62 |  -62 |   -1 |   -5 |
| LSZH      |  -22 |  -23 |  -22 |  -31 |  -26 |  -27 |  -29 |  -26 |  -26 |  -22 |  -28 |  -37 |
| LTFM      |  297 |  296 |  299 |  243 |  240 |  239 |  183 |  236 |  238 |  240 |  270 |  244 |
