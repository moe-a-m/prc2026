# Check: p6_holdout_bias_vs_minute_step

Run at 2026-10-03T06:08:08+00:00 (UTC), duckdb 1.5.6.

EXP-031 hold-out: median residual (pred - y) on regular NM-matched rows (|proxy error|<600 s) per airport and fold, next to that month's median proxy error. If the residual tracks the month's minute step, the leave-one-month-out model could not learn the month's offset.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (SELECT o.fold, c.airport, o.pred - o.y_oof AS r, epoch(c.t_mvt)-epoch(c.t_aobt3) - c.y AS pe
  FROM oof o JOIN clean_dep c USING (mvt_id) WHERE NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL AND abs(epoch(c.t_mvt)-epoch(c.t_aobt3) - c.y) < 600)
PIVOT b ON fold USING round(median(r)) AS med_resid, round(median(pe)) AS med_proxy_err GROUP BY airport ORDER BY airport
```

10 rows

| airport   |   jan_med_resid |   jan_med_proxy_err |   jul_med_resid |   jul_med_proxy_err |
|:----------|----------------:|--------------------:|----------------:|--------------------:|
| EDDF      |               6 |                 107 |              37 |                  87 |
| EDDM      |               6 |                  57 |              -1 |                  -4 |
| EGLL      |               7 |                  57 |              22 |                  54 |
| EHAM      |             -21 |                  93 |              13 |                  96 |
| LEBL      |              13 |                   1 |              37 |                 -57 |
| LEMD      |              18 |                  57 |              29 |                  -1 |
| LFPG      |              31 |                  -3 |              36 |                 -56 |
| LIRF      |              11 |                  -6 |              69 |                 -66 |
| LSZH      |              12 |                 -22 |              24 |                 -29 |
| LTFM      |              -5 |                 297 |              12 |                 183 |
