# Check: p6_top_rows_holdout_EXP-031

Run at 2026-10-03T06:08:39+00:00 (UTC), duckdb 1.5.6.

Top-25 EXP-031 hold-out rows by squared error (Jan+Jul 2025) with cumulative share.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof)
SELECT o.fold, c.airport, c.f_no_nm_match unmatched, c.flight_mvt, round((epoch(c.t_mvt)-epoch(c.t_sched))/3600,2) d_sched_h,
  round((epoch(c.t_mvt)-epoch(c.t_aobt3))/60,1) d_aobt3_min, o.y_oof y, round(o.pred) pred, round(100*o.se/tot_se,2) pct_total_sq_err,
  round(100*sum(o.se) OVER (ORDER BY o.se DESC)/tot_se,1) cum_pct
FROM oof o JOIN clean_dep c USING (mvt_id), tot ORDER BY o.se DESC LIMIT 25
```

25 rows

| fold   | airport   | unmatched   | flight_mvt   |   d_sched_h |   d_aobt3_min |     y |   pred |   pct_total_sq_err |   cum_pct |
|:-------|:----------|:------------|:-------------|------------:|--------------:|------:|-------:|-------------------:|----------:|
| jan    | LFPG      | True        | EJU983W      |        0.48 |         nan   | 84240 |    900 |              15.95 |      16   |
| jan    | LFPG      | True        | EJU42AY      |        0.57 |         nan   | 58206 |    960 |               7.53 |      23.5 |
| jul    | LIRF      | False       | AEZ146R      |       24.17 |        1453   | 87002 |  44494 |               4.15 |      27.6 |
| jan    | LIRF      | True        | EXSXS1GT     |       16.7  |         nan   | 87177 |  53248 |               2.64 |      30.3 |
| jul    | LIRF      | True        | RYRR90BN     |       25.98 |         nan   | 87170 |  59862 |               1.71 |      32   |
| jul    | LIRF      | True        | PGT2WE       |        5.8  |         nan   |  1377 |  28663 |               1.71 |      33.7 |
| jul    | LIRF      | True        | VOE6BB       |       20.35 |         nan   | 87361 |  62385 |               1.43 |      35.1 |
| jul    | LIRF      | True        | CHHHH438     |       23.4  |         nan   | 88132 |  63295 |               1.42 |      36.5 |
| jul    | LIRF      | True        | ITYTY680     |       16.27 |         nan   | 87186 |  63465 |               1.29 |      37.8 |
| jul    | LIRF      | True        | ITYTY674     |       12.18 |         nan   | 43863 |  63268 |               0.86 |      38.7 |
| jul    | LIRF      | False       | NOSS95ML     |        7.65 |          18   |   899 |  19603 |               0.8  |      39.5 |
| jul    | LIRF      | True        | VLG91ZA      |        6.92 |         nan   | 24900 |  43420 |               0.79 |      40.3 |
| jul    | LIRF      | True        | ITYTY672     |       12.88 |         nan   | 46369 |  63945 |               0.71 |      41   |
| jul    | LIRF      | True        | TAR753       |       11.18 |         nan   | 40262 |  57546 |               0.69 |      41.7 |
| jul    | LIRF      | True        | ARGG1141     |       12.6  |         nan   | 45368 |  62012 |               0.64 |      42.3 |
| jul    | LIRF      | True        | RYR359       |       12.72 |         nan   | 45791 |  60012 |               0.46 |      42.8 |
| jul    | LIRF      | True        | RYR5181      |        3.88 |         nan   |   896 |  13165 |               0.35 |      43.1 |
| jul    | LIRF      | True        | RYR68SF      |        4.25 |         nan   |   723 |  11919 |               0.29 |      43.4 |
| jan    | EHAM      | True        | NCG01A       |       -0.1  |         nan   | 11032 |    154 |               0.27 |      43.7 |
| jul    | LIRF      | True        | ITY1795      |        3.53 |         nan   |  1926 |  12601 |               0.26 |      44   |
| jul    | LIRF      | True        | ITY1733      |        3.68 |         nan   |  1552 |  11946 |               0.25 |      44.2 |
| jul    | LIRF      | True        | RYR47KR      |        3.68 |         nan   |  1444 |  10901 |               0.21 |      44.4 |
| jul    | LIRF      | True        | AEZ131R      |        7.05 |         nan   | 25383 |  34822 |               0.2  |      44.6 |
| jan    | LIRF      | True        | MABGV        |       11.07 |         nan   | 39837 |  30587 |               0.2  |      44.8 |
| jul    | EHAM      | False       | OR1507       |        3.55 |         129.9 | 10972 |   1810 |               0.19 |      45   |
