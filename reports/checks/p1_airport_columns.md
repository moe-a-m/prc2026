# Check: p1_airport_columns

Run at 2026-10-02T10:11:47+00:00 (UTC), duckdb 1.5.6.

```sql
-- Which column holds the airport? For DEP it should be ADEP_mvt, for ARR ADES_mvt.
SELECT 'train' ds, PHASE_mvt, ADEP_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH') adep_in10,
       ADES_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH') ades_in10, count(*) n
FROM raw_training GROUP BY ALL
UNION ALL
SELECT 'rank', PHASE_mvt, ADEP_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH'),
       ADES_mvt IN ('EDDF','EDDM','EGLL','EHAM','LEBL','LEMD','LFPG','LIRF','LTFM','LSZH'), count(*)
FROM raw_ranking GROUP BY ALL ORDER BY ALL
```

12 rows

| ds    | PHASE_mvt   | adep_in10   | ades_in10   |       n |
|:------|:------------|:------------|:------------|--------:|
| rank  | ARR         | False       | True        |  292935 |
| rank  | ARR         | True        | True        |   51745 |
| rank  | ARR         | <NA>        | True        |      13 |
| rank  | DEP         | True        | False       |  293202 |
| rank  | DEP         | True        | True        |   51626 |
| rank  | DEP         | True        | <NA>        |      13 |
| train | ARR         | False       | True        | 1763487 |
| train | ARR         | True        | True        |  319179 |
| train | ARR         | <NA>        | True        |      84 |
| train | DEP         | True        | False       | 1766265 |
| train | DEP         | True        | True        |  318660 |
| train | DEP         | True        | <NA>        |     122 |
