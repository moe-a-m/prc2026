# Check: p6_lirf_unmatched_block_minus_sched

Run at 2026-10-03T05:55:44+00:00 (UTC), duckdb 1.5.6.

LIRF NM-unmatched 2025 departures: off-block minus schedule (BLOCK-SCHED, s) classes. Shows the regimes echo / -1 day / early block.

```sql
WITH d AS (SELECT epoch(t_block)-epoch(t_sched) bs, epoch(t_mvt)-epoch(t_sched) d_sched, y FROM clean_dep
  WHERE ds='train' AND airport='LIRF' AND f_no_nm_match)
SELECT CASE WHEN abs(bs)<=120 THEN 'a |B-S|<=2min (echo)'
            WHEN bs BETWEEN -86400-10800 AND -86400+10800 THEN 'b B-S ~ -1 day'
            WHEN bs < -10800 THEN 'c B-S < -3h'
            WHEN bs < -120 THEN 'd B-S in [-3h,-2min)'
            WHEN bs <= 3600 THEN 'e B-S in (2min,1h]'
            ELSE 'f B-S > 1h' END AS block_vs_sched,
  count(*) n, round(median(d_sched)) med_dsched, round(median(y)) med_y, round(median(bs)) med_bs,
  round(quantile_cont(bs,0.1)) q10_bs, round(quantile_cont(bs,0.9)) q90_bs
FROM d GROUP BY 1 ORDER BY 1
```

5 rows

| block_vs_sched       |   n |   med_dsched |   med_y |   med_bs |   q10_bs |   q90_bs |
|:---------------------|----:|-------------:|--------:|---------:|---------:|---------:|
| a |B-S|<=2min (echo) | 722 |         7532 |    7534 |        0 |       -5 |        5 |
| c B-S < -3h          |  15 |        50581 |   87177 |   -27059 |   -34921 |   -16743 |
| d B-S in [-3h,-2min) |  64 |         1048 |    4978 |    -3750 |    -7160 |     -480 |
| e B-S in (2min,1h]   |  16 |         3901 |    1232 |     2074 |     1080 |     2610 |
| f B-S > 1h           | 670 |         6122 |    1022 |     5099 |     3838 |     9478 |
