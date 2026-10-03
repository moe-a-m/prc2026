# Check: p6_stand_normalisation

Run at 2026-10-03T06:04:12+00:00 (UTC), duckdb 1.5.6.

Stand code hygiene per airport (departures, train+rank): distinct codes before/after upper/trim/strip-leading-zeros, null and placeholder counts, non-numeric codes.

```sql
WITH s AS (SELECT airport, stand, ds, count(*) n FROM clean_dep GROUP BY ALL),
k AS (SELECT *, upper(trim(stand)) s_up,
        CASE WHEN regexp_matches(upper(trim(stand)), '^0+[0-9]') THEN regexp_replace(upper(trim(stand)), '^0+', '') ELSE upper(trim(stand)) END s_nz FROM s)
SELECT airport, count(DISTINCT stand) n_stand_codes, count(DISTINCT s_nz) n_after_norm,
  count(DISTINCT stand) - count(DISTINCT s_nz) n_codes_merged,
  sum(n) FILTER (stand IS NULL) n_rows_null, sum(n) FILTER (s_up IN ('NA','N/A','UNK','?','0','-','')) n_rows_placeholder,
  sum(n) FILTER (stand <> s_nz) n_rows_changed_by_norm,
  string_agg(DISTINCT stand, ',') FILTER (stand <> s_nz) examples_changed,
  sum(n) FILTER (NOT regexp_matches(coalesce(stand,''), '^[0-9]+$')) n_rows_non_numeric
FROM k GROUP BY airport ORDER BY airport
```

10 rows

| airport   |   n_stand_codes |   n_after_norm |   n_codes_merged |   n_rows_null |   n_rows_placeholder |   n_rows_changed_by_norm | examples_changed   |   n_rows_non_numeric |
|:----------|----------------:|---------------:|-----------------:|--------------:|---------------------:|-------------------------:|:-------------------|---------------------:|
| EDDF      |             252 |            252 |                0 |           nan |                  nan |                      nan | nan                |               266458 |
| EDDM      |             213 |            213 |                0 |           nan |                  nan |                      nan | nan                |                 1305 |
| EGLL      |             231 |            231 |                0 |             6 |                  nan |                      nan | nan                |                33031 |
| EHAM      |             263 |            263 |                0 |           nan |                  nan |                      nan | nan                |               286133 |
| LEBL      |             233 |            233 |                0 |           nan |                  nan |                      325 | 03,01,02,04        |                 6138 |
| LEMD      |             381 |            381 |                0 |           nan |                  nan |                      nan | nan                |                76609 |
| LFPG      |             414 |            414 |                0 |            16 |                  nan |                      nan | nan                |               279424 |
| LIRF      |             143 |            143 |                0 |            10 |                  nan |                      nan | nan                |                   24 |
| LSZH      |             219 |            219 |                0 |           nan |                  nan |                      nan | nan                |               148611 |
| LTFM      |             419 |            419 |                0 |           nan |                  nan |                      nan | nan                |               285743 |
