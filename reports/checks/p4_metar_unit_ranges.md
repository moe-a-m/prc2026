# Check: p4_metar_unit_ranges

Run at 2026-10-02T12:31:04+00:00 (UTC), duckdb 1.5.6.

Sanity ranges in SI units.

```sql
SELECT station, round(min(temp_c),1) tmin, round(max(temp_c),1) tmax, round(max(wind_ms),1) wmax, round(max(gust_ms),1) gmax,
  round(min(vis_m)) vmin, round(max(vis_m)) vmax, round(min(ceiling_m)) cmin, min(rvr_min_m) rvrmin, max(rvr_min_m) rvrmax,
  round(100.0*avg((temp_c IS NULL)::INT),2) pct_temp_null, round(100.0*avg((vis_m IS NULL)::INT),2) pct_vis_null
FROM stg_metar GROUP BY 1 ORDER BY 1
```

10 rows

| station   |   tmin |   tmax |   wmax |   gmax |   vmin |   vmax |   cmin |   rvrmin |   rvrmax |   pct_temp_null |   pct_vis_null |
|:----------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|---------:|---------:|----------------:|---------------:|
| EDDF      |     -9 |     41 |   14.9 |   19   |    257 |   9994 |     30 |      250 |     2000 |            0    |           0    |
| EDDM      |    -15 |     37 |   15.4 |   26.2 |    193 |   9994 |     30 |       50 |     2000 |            0.02 |           0    |
| EGLL      |     -5 |     35 |   14.9 |   21.6 |     97 |   9994 |      0 |      225 |     1500 |            0    |           0    |
| EHAM      |     -7 |     36 |   18.5 |   25.2 |    145 |   9994 |      0 |      150 |     2000 |            0    |           0    |
| LEBL      |      0 |     37 |   22.6 |   31.4 |     48 |   9994 |     30 |      250 |     2000 |            0    |           0    |
| LEMD      |     -7 |     41 |   19.5 |   22.6 |     97 |   9994 |     30 |      350 |     2000 |            0    |           0    |
| LFPG      |     -6 |     40 |   19   |   26.8 |    145 |   9994 |      0 |      100 |     2000 |            0    |           0    |
| LIRF      |     -1 |     36 |   12.9 |   19   |     48 |   9994 |     30 |      200 |     2000 |            0.01 |           0.02 |
| LSZH      |    -13 |     38 |   12.3 |   21.6 |     97 |   9994 |     30 |      250 |     2000 |            0.01 |           0.01 |
| LTFM      |     -5 |     39 |   19   |   24.7 |    193 |   9994 |     30 |      175 |     1500 |            0    |           0    |
