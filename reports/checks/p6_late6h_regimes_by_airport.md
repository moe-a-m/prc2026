# Check: p6_late6h_regimes_by_airport

Run at 2026-10-03T05:56:49+00:00 (UTC), duckdb 1.5.6.

2025 departures taking off >= 6 h after schedule: echo / day-minus / NM-proxy-correct shares by airport x NM-match, and EXP-031 hold-out squared-error share.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (SELECT mvt_id, airport, f_no_nm_match unmatched, y, epoch(t_mvt)-epoch(t_sched) d_sched,
    epoch(t_mvt)-epoch(t_aobt3) d_aobt3 FROM clean_dep WHERE ds='train' AND epoch(t_mvt)-epoch(t_sched) >= 21600)
SELECT airport, unmatched, count(*) n, round(100*avg((abs(y-d_sched)<=120)::INT),1) pct_echo,
  round(100*avg((y BETWEEN 72000 AND 100800 AND abs(y-d_sched)>120)::INT),1) pct_dayminus,
  round(100*avg((abs(y-d_aobt3)<=300)::INT),1) pct_proxy_within5min,
  count(o.mvt_id) n_hold, round(100*sum(o.se)/any_value(tot_se),2) pct_total_sq_err
FROM b LEFT JOIN oof o USING (mvt_id), tot GROUP BY ALL ORDER BY pct_total_sq_err DESC NULLS LAST
```

20 rows

| airport   | unmatched   |   n |   pct_echo |   pct_dayminus |   pct_proxy_within5min |   n_hold |   pct_total_sq_err |
|:----------|:------------|----:|-----------:|---------------:|-----------------------:|---------:|-------------------:|
| LIRF      | True        |  63 |       81   |           17.5 |                  nan   |       21 |              13.41 |
| LIRF      | False       |  86 |        1.2 |            0   |                   64   |       21 |               5.26 |
| LTFM      | False       | 534 |        0   |            0   |                   39   |       88 |               0.03 |
| EHAM      | True        |  33 |        0   |            0   |                  nan   |        8 |               0.02 |
| EHAM      | False       | 330 |        0   |            0   |                   70   |       43 |               0.01 |
| EDDF      | False       | 610 |        0   |            0   |                   80.8 |      117 |               0.01 |
| LFPG      | False       | 234 |        0   |            0   |                   68.4 |       33 |               0.01 |
| EGLL      | False       |  98 |        0   |            0   |                   72.4 |       18 |               0    |
| LFPG      | True        |  36 |        0   |            0   |                  nan   |        7 |               0    |
| LEBL      | True        |  13 |        0   |            0   |                  nan   |        2 |               0    |
| LEMD      | False       | 159 |        0   |            0   |                   76.7 |       21 |               0    |
| EDDM      | True        |   7 |        0   |            0   |                  nan   |        1 |               0    |
| LSZH      | False       |  37 |        0   |            0   |                   78.4 |        9 |               0    |
| LEBL      | False       | 101 |        0   |            0   |                   76   |       23 |               0    |
| LEMD      | True        |   1 |        0   |            0   |                  nan   |        1 |               0    |
| EDDF      | True        |  29 |        0   |            0   |                  nan   |       10 |               0    |
| EDDM      | False       |  66 |        0   |            0   |                   63.6 |       11 |               0    |
| EGLL      | True        |  12 |        0   |            0   |                  nan   |        2 |               0    |
| LTFM      | True        |  11 |        0   |            0   |                  nan   |        0 |             nan    |
| LSZH      | True        |   2 |        0   |            0   |                  nan   |        0 |             nan    |
