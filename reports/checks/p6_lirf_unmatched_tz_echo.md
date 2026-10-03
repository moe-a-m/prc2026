# Check: p6_lirf_unmatched_tz_echo

Run at 2026-10-03T05:56:11+00:00 (UTC), duckdb 1.5.6.

LIRF NM-unmatched early-block rows: is BLOCK = SCHED minus the Rome UTC offset (1 h winter / 2 h summer; DST approximated by month Apr-Oct)?

```sql
WITH d AS (SELECT epoch(t_block)-epoch(t_sched) bs, epoch(t_block)-epoch(t_sched) - CASE WHEN month(month) BETWEEN 4 AND 10 THEN -7200 ELSE -3600 END AS bs_minus_utcoffset,
   month(month) BETWEEN 4 AND 10 AS summer FROM clean_dep
  WHERE ds='train' AND airport='LIRF' AND f_no_nm_match AND epoch(t_block)-epoch(t_sched) BETWEEN -10800 AND -121)
SELECT summer, count(*) n, count(*) FILTER (abs(bs+3600)<=120) n_bs_m1h, count(*) FILTER (abs(bs+7200)<=120) n_bs_m2h,
  count(*) FILTER (abs(bs_minus_utcoffset)<=120) n_eq_local_offset
FROM d GROUP BY 1
```

2 rows

| summer   |   n |   n_bs_m1h |   n_bs_m2h |   n_eq_local_offset |
|:---------|----:|-----------:|-----------:|--------------------:|
| False    |  19 |          2 |          1 |                   2 |
| True     |  45 |          0 |          4 |                   4 |
