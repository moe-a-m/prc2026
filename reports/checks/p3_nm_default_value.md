# Check: p3_nm_default_value

Run at 2026-10-02T12:58:13+00:00 (UTC), duckdb 1.5.6.

Is MVT − AOBT_3 more accurate when it is NOT at the NM default minute? (2025 DEP, y ≤ 3 h)

```sql
SELECT f.airport, round(100.0*avg(n.aobt3_at_default::INT),1) pct_at_default,
  round(sqrt(avg((f.d_aobt3 - f.y)^2) FILTER (WHERE n.aobt3_at_default)),1) rmse_x_at_default,
  round(sqrt(avg((f.d_aobt3 - f.y)^2) FILTER (WHERE NOT n.aobt3_at_default)),1) rmse_x_off_default,
  round(100.0*avg((abs(f.d_aobt3 - f.y) <= 60)::INT) FILTER (WHERE NOT n.aobt3_at_default),1) pct_within60_off_default
FROM feat_dep f JOIN feat_dep_nm n USING (mvt_id) WHERE f.ds='train' AND f.y <= 3*3600 GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

11 rows

| airport   |   pct_at_default |   rmse_x_at_default |   rmse_x_off_default |   pct_within60_off_default |
|:----------|-----------------:|--------------------:|---------------------:|---------------------------:|
| EDDF      |             12.2 |               215.8 |                260.1 |                       21   |
| EDDM      |             31   |               190.4 |                400.3 |                       24.1 |
| EGLL      |              7.3 |               251.3 |                427.1 |                       19.2 |
| EHAM      |             17.1 |               171.1 |                353.6 |                       22.7 |
| LEBL      |             19.2 |               262.9 |                321.8 |                       26.2 |
| LEMD      |             16.4 |               207.9 |                288   |                       26   |
| LFPG      |             14.5 |               300.2 |                385.8 |                       21.1 |
| LIRF      |             17.5 |               466.1 |                571.9 |                       18.2 |
| LSZH      |             21.9 |               247.3 |                274.1 |                       24   |
| LTFM      |             54.1 |               417.1 |                639   |                        9.2 |
| nan       |             21.5 |               320.4 |                399.5 |                       21.3 |
