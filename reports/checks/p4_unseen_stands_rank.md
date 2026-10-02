# Check: p4_unseen_stands_rank

Run at 2026-10-02T14:44:05+00:00 (UTC), duckdb 1.5.6.

Share of ranking departures whose (stand, runway) pair or stand never/rarely appears in 2025 training.

```sql
WITH tr AS (SELECT airport, stand, runway, count(*) n FROM feat_dep WHERE ds='train' GROUP BY ALL),
     ts AS (SELECT airport, stand, count(*) n FROM feat_dep WHERE ds='train' GROUP BY ALL)
SELECT r.airport, count(*) n_rank,
  round(100*avg((tr.n IS NULL)::INT),2) pct_pair_unseen, round(100*avg((coalesce(tr.n,0) < 20)::INT),2) pct_pair_lt20,
  round(100*avg((ts.n IS NULL)::INT),2) pct_stand_unseen
FROM feat_dep r LEFT JOIN tr USING (airport, stand, runway) LEFT JOIN ts USING (airport, stand)
WHERE r.ds='rank' GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

11 rows

| airport   |   n_rank |   pct_pair_unseen |   pct_pair_lt20 |   pct_stand_unseen |
|:----------|---------:|------------------:|----------------:|-------------------:|
| EDDF      |    36317 |              2.37 |            7.33 |               0.83 |
| EDDM      |    25966 |              4.57 |            4.86 |               4.55 |
| EGLL      |    39840 |              0.18 |            0.53 |               0.01 |
| EHAM      |    38182 |              0.06 |            2.8  |               0.03 |
| LEBL      |    30080 |              0.2  |            1.23 |               0    |
| LEMD      |    36954 |              0.17 |            2.55 |               0.04 |
| LFPG      |    39872 |              0.13 |            2.76 |               0.03 |
| LIRF      |    26899 |              0.09 |            1.09 |               0.03 |
| LSZH      |    23150 |              0.4  |            2.16 |               0.25 |
| LTFM      |    47581 |              0.13 |            2.77 |               0.01 |
| nan       |   344841 |              0.72 |            2.82 |               0.46 |
