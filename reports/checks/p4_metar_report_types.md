# Check: p4_metar_report_types

Run at 2026-10-02T12:31:04+00:00 (UTC), duckdb 1.5.6.

Raw vs staged rows (difference = duplicates removed).

```sql
SELECT station, count(*) n, sum(is_auto::INT) n_auto, sum(is_cor::INT) n_cor,
  sum((metar LIKE 'SPECI%' OR metar LIKE '% SPECI %')::INT) n_speci, count(rvr_min_m) n_rvr,
  (SELECT count(*) FROM raw_metar r WHERE r.station = s.station) n_raw
FROM stg_metar s GROUP BY 1 ORDER BY 1
```

10 rows

| station   |     n |   n_auto |   n_cor |   n_speci |   n_rvr |   n_raw |
|:----------|------:|---------:|--------:|----------:|--------:|--------:|
| EDDF      | 27884 |    27884 |       0 |         0 |     533 |   28076 |
| EDDM      | 27886 |    27885 |       3 |         0 |    1786 |   28078 |
| EGLL      | 27878 |    26887 |     112 |         0 |     125 |   28070 |
| EHAM      | 27805 |        0 |       2 |         0 |     639 |   27996 |
| LEBL      | 28206 |        1 |       2 |         0 |     227 |   28398 |
| LEMD      | 28302 |        0 |       0 |         0 |     135 |   28494 |
| LFPG      | 27897 |     2299 |       1 |         0 |     743 |   28089 |
| LIRF      | 27797 |      790 |       1 |         0 |     334 |   27989 |
| LSZH      | 27879 |     6950 |       0 |         0 |    1421 |   28071 |
| LTFM      | 27872 |        0 |       3 |         0 |     821 |   28064 |
