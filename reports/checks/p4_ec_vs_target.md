# Check: p4_ec_vs_target

Run at 2026-10-02T13:49:57+00:00 (UTC), duckdb 1.5.6.

EUROCONTROL monthly taxi-out (reference + additional, per flight) vs our target, Jan/Jul 2025 and 2026 (ranking: target blank).

```sql
SELECT f.airport, strftime(f.month,'%Y-%m') m, count(*) n, round(avg(f.y)) mean_y_all, round(avg(f.y) FILTER (WHERE f.y <= 7200)) mean_y_le2h,
  round(any_value(e.ec_m_taxi_mean_s)) ec_mean_s, round(any_value(e.ec_m_taxi_add_s)) ec_add_s,
  round(100.0*avg((e.ec_d_predep_dly_min IS NULL)::INT),2) pct_no_daily
FROM feat_dep f JOIN feat_dep_ec e USING (mvt_id) WHERE month(f.month) IN (1,7) GROUP BY ALL ORDER BY 1, 2
```

40 rows

| airport   | m       |     n |   mean_y_all |   mean_y_le2h |   ec_mean_s |   ec_add_s |   pct_no_daily |
|:----------|:--------|------:|-------------:|--------------:|------------:|-----------:|---------------:|
| EDDF      | 2025-01 | 15496 |          885 |           885 |         832 |        189 |              0 |
| EDDF      | 2025-07 | 21334 |          868 |           868 |         866 |        225 |              0 |
| EDDF      | 2026-01 | 15667 |          nan |           nan |         854 |        199 |              0 |
| EDDF      | 2026-07 | 20650 |          nan |           nan |         854 |        192 |              0 |
| EDDM      | 2025-01 | 11266 |          870 |           870 |         706 |        147 |              0 |
| EDDM      | 2025-07 | 15825 |          805 |           805 |         805 |        245 |              0 |
| EDDM      | 2026-01 | 10953 |          nan |           nan |         755 |        173 |              0 |
| EDDM      | 2026-07 | 15013 |          nan |           nan |         776 |        204 |              0 |
| EGLL      | 2025-01 | 19420 |         1330 |          1327 |        1328 |        353 |              0 |
| EGLL      | 2025-07 | 20790 |         1431 |          1426 |        1427 |        445 |              0 |
| EGLL      | 2026-01 | 19283 |          nan |           nan |        1335 |        361 |              0 |
| EGLL      | 2026-07 | 20557 |          nan |           nan |        1344 |        382 |              0 |
| EHAM      | 2025-01 | 18460 |          811 |           811 |         803 |        258 |              0 |
| EHAM      | 2025-07 | 22489 |          787 |           787 |         786 |        182 |              0 |
| EHAM      | 2026-01 | 16232 |          nan |           nan |         982 |        422 |              0 |
| EHAM      | 2026-07 | 21950 |          nan |           nan |         841 |        187 |              0 |
| LEBL      | 2025-01 | 12234 |          887 |           887 |         885 |        169 |              0 |
| LEBL      | 2025-07 | 16752 |         1008 |          1008 |         999 |        271 |              0 |
| LEBL      | 2026-01 | 12201 |          nan |           nan |         883 |        174 |              0 |
| LEBL      | 2026-07 | 17879 |          nan |           nan |         967 |        257 |              0 |
| LEMD      | 2025-01 | 16510 |          986 |           986 |         974 |        189 |              0 |
| LEMD      | 2025-07 | 18818 |         1032 |          1032 |        1028 |        244 |              0 |
| LEMD      | 2026-01 | 16802 |          nan |           nan |         987 |        195 |              0 |
| LEMD      | 2026-07 | 20152 |          nan |           nan |        1020 |        225 |              0 |
| LFPG      | 2025-01 | 17900 |         1080 |          1071 |         935 |        239 |              0 |
| LFPG      | 2025-07 | 21712 |         1028 |          1025 |         983 |        285 |              0 |
| LFPG      | 2026-01 | 18129 |          nan |           nan |         928 |        224 |              0 |
| LFPG      | 2026-07 | 21743 |          nan |           nan |         965 |        244 |              0 |
| LIRF      | 2025-01 | 11317 |         1097 |          1068 |        1056 |        305 |              0 |
| LIRF      | 2025-07 | 15211 |         1406 |          1297 |        1284 |        543 |              0 |
| LIRF      | 2026-01 | 11061 |          nan |           nan |        1043 |        319 |              0 |
| LIRF      | 2026-07 | 15838 |          nan |           nan |        1214 |        487 |              0 |
| LSZH      | 2025-01 |  9735 |          775 |           773 |         689 |        181 |              0 |
| LSZH      | 2025-07 | 12611 |          742 |           742 |         732 |        214 |              0 |
| LSZH      | 2026-01 |  9995 |          nan |           nan |         711 |        195 |              0 |
| LSZH      | 2026-07 | 13155 |          nan |           nan |         742 |        212 |              0 |
| LTFM      | 2025-01 | 21368 |         1041 |          1041 |        1031 |        263 |              0 |
| LTFM      | 2025-07 | 25171 |         1094 |          1094 |        1071 |        371 |              0 |
| LTFM      | 2026-01 | 22396 |          nan |           nan |        1089 |        294 |              0 |
| LTFM      | 2026-07 | 25185 |          nan |           nan |        1009 |        302 |              0 |
