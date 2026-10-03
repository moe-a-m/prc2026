# Check: p5_cross_airport_link_unmatched

Run at 2026-10-03T05:30:54+00:00 (UTC), duckdb 1.5.6.

Unmatched-NM departures that fly to another challenge airport and whose arrival row there carries an NM match / AOBT_3.

```sql
WITH dep AS (SELECT * FROM stg_mvt WHERE phase='DEP'),
arr AS (SELECT * FROM stg_mvt WHERE phase='ARR'),
link AS (  -- same flight number, DEP origin/destination = ARR origin/destination, landing after take-off within 18 h
  SELECT d.mvt_id, d.ds, d.airport, d.flight_id IS NULL AS dep_unmatched, a.flight_id IS NOT NULL AS arr_has_nm,
         a.t_aobt3 IS NOT NULL AS arr_has_aobt3,
         row_number() OVER (PARTITION BY d.mvt_id ORDER BY epoch(a.t_mvt) - epoch(d.t_mvt)) rn
  FROM dep d JOIN arr a ON a.flight_mvt = d.flight_mvt AND a.adep_mvt = d.adep_mvt AND a.ades_mvt = d.ades_mvt
   AND a.t_mvt > d.t_mvt AND a.t_mvt < d.t_mvt + INTERVAL 18 HOUR)
SELECT d.ds, d.airport, count(*) n_dep_unmatched,
  sum((d.ades_mvt IN (SELECT airport FROM ref_airport))::INT) n_to_challenge_airport,
  sum((l.mvt_id IS NOT NULL)::INT) n_arr_row_found,
  sum(coalesce(l.arr_has_nm,false)::INT) n_arr_has_nm,
  sum(coalesce(l.arr_has_aobt3,false)::INT) n_arr_has_aobt3
FROM dep d LEFT JOIN (SELECT * FROM link WHERE rn=1) l USING (mvt_id)
WHERE d.flight_id IS NULL GROUP BY ROLLUP(d.ds, d.airport) ORDER BY 1, 2
```

23 rows

| ds    | airport   |   n_dep_unmatched |   n_to_challenge_airport |   n_arr_row_found |   n_arr_has_nm |   n_arr_has_aobt3 |
|:------|:----------|------------------:|-------------------------:|------------------:|---------------:|------------------:|
| rank  | EDDF      |               421 |                       57 |                11 |             10 |                10 |
| rank  | EDDM      |               238 |                       43 |                29 |             27 |                27 |
| rank  | EGLL      |               248 |                       31 |                18 |             18 |                18 |
| rank  | EHAM      |              1206 |                      309 |               205 |             13 |                13 |
| rank  | LEBL      |               441 |                       57 |                35 |             34 |                34 |
| rank  | LEMD      |               236 |                       57 |                28 |             27 |                27 |
| rank  | LFPG      |               732 |                       62 |                37 |             37 |                37 |
| rank  | LIRF      |               383 |                       71 |                42 |             42 |                42 |
| rank  | LSZH      |               659 |                       79 |                18 |              5 |                 5 |
| rank  | LTFM      |               719 |                       25 |                14 |             14 |                14 |
| rank  | nan       |              5283 |                      791 |               437 |            227 |               227 |
| train | EDDF      |              1956 |                      270 |                66 |             56 |                56 |
| train | EDDM      |              1009 |                      199 |               117 |            113 |               113 |
| train | EGLL      |              1414 |                      150 |                82 |             81 |                81 |
| train | EHAM      |              4084 |                     1615 |              1334 |             36 |                36 |
| train | LEBL      |              1856 |                      323 |               218 |            123 |               123 |
| train | LEMD      |               939 |                      192 |                94 |             94 |                94 |
| train | LFPG      |              3765 |                      330 |               184 |            184 |               183 |
| train | LIRF      |              1487 |                      216 |               118 |            116 |               115 |
| train | LSZH      |              2291 |                      372 |               152 |             22 |                22 |
| train | LTFM      |              3623 |                      185 |                82 |             81 |                81 |
| train | nan       |             22424 |                     3852 |              2447 |            906 |               904 |
| nan   | nan       |             27707 |                     4643 |              2884 |           1133 |              1131 |
