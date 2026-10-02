# Check: p4_stand_geo_match

Run at 2026-10-02T18:37:27+00:00 (UTC), duckdb 1.5.6.

Share of departures (train + ranking) whose stand code has OSM parking_position coordinates.

```sql
SELECT f.airport, count(*) n_dep, round(100*avg((g.lat IS NOT NULL)::INT),1) pct_stand_geo,
       round(100*avg((g.match_kind='base')::INT),1) pct_base_match
FROM feat_dep f LEFT JOIN stg_stand_geo g USING (airport, stand) GROUP BY ROLLUP(1) ORDER BY 1 NULLS LAST
```

11 rows

| airport   |   n_dep |   pct_stand_geo |   pct_base_match |
|:----------|--------:|----------------:|-----------------:|
| EDDF      |  266458 |            96.7 |              0.4 |
| EDDM      |  193300 |            87   |             34   |
| EGLL      |  279386 |            98.3 |              0   |
| EHAM      |  286133 |            94.8 |              0   |
| LEBL      |  209785 |            89.6 |              0   |
| LEMD      |  249196 |            98.8 |              0   |
| LFPG      |  279424 |            97.1 |              0   |
| LIRF      |  187603 |            98.9 |              0   |
| LSZH      |  158057 |            96.4 |              0   |
| LTFM      |  320546 |            99.2 |              0   |
| nan       | 2429888 |            96   |              2.5 |
