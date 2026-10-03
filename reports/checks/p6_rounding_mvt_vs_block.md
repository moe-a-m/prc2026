# Check: p6_rounding_mvt_vs_block

Run at 2026-10-03T05:39:36+00:00 (UTC), duckdb 1.5.6.

Minute-rounding of take-off (MVT) vs block time, training departures.

```sql
-- Is a minute-rounded take-off time (visible in 2026) a marker for a minute-rounded block time (label-derived)?
SELECT airport, round(100*avg((second(t_mvt)=0)::INT),1) pct_mvt_sec0,
  round(100*avg((second(t_block)=0)::INT) FILTER (WHERE second(t_mvt)=0),1) p_blk0_given_mvt0,
  round(100*avg((second(t_block)=0)::INT) FILTER (WHERE second(t_mvt)<>0),1) p_blk0_given_mvt_not0,
  round(sqrt(avg(y::DOUBLE*y) FILTER (WHERE second(t_mvt)=0)) - sqrt(avg(y::DOUBLE*y) FILTER (WHERE second(t_mvt)<>0))) rms_y_diff,
  round(100*avg((flight_id IS NULL)::INT) FILTER (WHERE second(t_mvt)=0),2) pct_unm_mvt0, round(100*avg((flight_id IS NULL)::INT) FILTER (WHERE second(t_mvt)<>0),2) pct_unm_mvt_not0
FROM clean_dep WHERE ds='train' GROUP BY 1 ORDER BY 1
```

10 rows

| airport   |   pct_mvt_sec0 |   p_blk0_given_mvt0 |   p_blk0_given_mvt_not0 |   rms_y_diff |   pct_unm_mvt0 |   pct_unm_mvt_not0 |
|:----------|---------------:|--------------------:|------------------------:|-------------:|---------------:|-------------------:|
| EDDF      |            1.8 |                 1.8 |                     1.7 |           -4 |           0.66 |               0.85 |
| EDDM      |            8.3 |                50.3 |                     4.5 |           -2 |           0.47 |               0.62 |
| EGLL      |            8.3 |                49.7 |                     4.7 |            5 |           0.63 |               0.59 |
| EHAM      |            1.7 |                 3.3 |                     1.7 |          -19 |           4    |               1.61 |
| LEBL      |            1.7 |                 9.1 |                     8.3 |          -14 |           0.97 |               1.03 |
| LEMD      |            1.6 |                 8.6 |                     8.4 |            8 |           0.55 |               0.44 |
| LFPG      |            8.3 |                50   |                     4.5 |          134 |           1.53 |               1.58 |
| LIRF      |            8.4 |                50.3 |                     4.5 |          159 |           0.88 |               0.93 |
| LSZH      |            1.7 |                 2.4 |                     2   |          -42 |           2.16 |               1.69 |
| LTFM      |            8.3 |                49.9 |                     4.5 |           -2 |           1.35 |               1.33 |
