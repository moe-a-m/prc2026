# Check: p6_matched_block_eq_sched_by_airport

Run at 2026-10-03T06:05:30+00:00 (UTC), duckdb 1.5.6.

NM-matched 2025 departures: share with BLOCK within 60 s of SCHED (possible echo) vs AOBT_3 within 60 s of SCHED (real on-time departures), NM-proxy agreement, EXP-031 hold-out RMSE.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (SELECT c.mvt_id, c.airport, c.y, abs(epoch(c.t_block)-epoch(c.t_sched)) <= 60 beq,
    epoch(c.t_mvt)-epoch(c.t_aobt3) px, epoch(c.t_aobt3)-epoch(c.t_sched) aobt3_minus_sched
  FROM clean_dep c WHERE c.ds='train' AND NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL)
SELECT airport, round(100*avg(beq::INT),1) pct_block_eq_sched,
  round(100*avg((abs(aobt3_minus_sched)<=60)::INT),1) pct_aobt3_eq_sched,
  round(100*avg((abs(px-y)>300)::INT) FILTER (beq),1) pct_proxy_off5min_if_beq,
  round(100*avg((abs(px-y)>300)::INT) FILTER (NOT beq),1) pct_proxy_off5min_if_not,
  round(median(px-y) FILTER (beq)) med_proxy_err_if_beq,
  round(sqrt(avg(o.se) FILTER (beq))) rmse_hold_beq, round(sqrt(avg(o.se) FILTER (NOT beq))) rmse_hold_not,
  round(100*sum(o.se) FILTER (beq)/any_value(tot_se),2) pct_total_sq_err_beq
FROM b LEFT JOIN oof o USING (mvt_id), tot GROUP BY 1 ORDER BY 1
```

10 rows

| airport   |   pct_block_eq_sched |   pct_aobt3_eq_sched |   pct_proxy_off5min_if_beq |   pct_proxy_off5min_if_not |   med_proxy_err_if_beq |   rmse_hold_beq |   rmse_hold_not |   pct_total_sq_err_beq |
|:----------|---------------------:|---------------------:|---------------------------:|---------------------------:|-----------------------:|----------------:|----------------:|-----------------------:|
| EDDF      |                  7   |                 10.5 |                       12.4 |                       14.7 |                     90 |             138 |             183 |                   0.1  |
| EDDM      |                 10.4 |                 12.1 |                       14.3 |                       17.8 |                      2 |             124 |             170 |                   0.09 |
| EGLL      |                  9.9 |                 14.3 |                       19   |                       27.8 |                      4 |             195 |             238 |                   0.3  |
| EHAM      |                  7   |                 10.8 |                        9.1 |                       19.8 |                     84 |             124 |             178 |                   0.08 |
| LEBL      |                 10   |                 10   |                       23.1 |                       17.8 |                    -58 |             332 |             202 |                   0.75 |
| LEMD      |                  8.6 |                 10.4 |                       13.1 |                       13.5 |                      4 |             152 |             174 |                   0.15 |
| LFPG      |                  8.3 |                  9.1 |                       26.1 |                       26.2 |                      5 |             180 |             252 |                   0.21 |
| LIRF      |                 20.5 |                  9.4 |                       44.3 |                       31.6 |                   -183 |             837 |             434 |                   7.96 |
| LSZH      |                  5.8 |                  7.7 |                       14.7 |                       17.6 |                    -25 |             168 |             187 |                   0.08 |
| LTFM      |                 10.6 |                  8.9 |                       55.5 |                       55.6 |                    298 |             191 |             249 |                   0.4  |
