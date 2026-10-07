# Check: m034_adsb_vs_nm

Run at 2026-10-07T12:16:05+00:00 (UTC), duckdb 1.5.6.

2025 matched departures with an ADS-B ground segment (all extracted Jan/Jul days): accuracy of the NM proxy vs ADS-B movement estimates, by how far NM's AOBT_3 is from the airport off-block.

```sql
WITH d AS (
    SELECT f.airport, f.y, f.d_aobt3, a.adsb_first_move_s AS fm, a.adsb_seen_parked AS parked, s.adsb_stand_move_s AS sm,
           CASE WHEN abs(f.d_aobt3 - f.y) <= 60 THEN 'a ≤1 min' WHEN abs(f.d_aobt3 - f.y) <= 300 THEN 'b 1–5 min'
                WHEN abs(f.d_aobt3 - f.y) <= 900 THEN 'c 5–15 min' ELSE 'd >15 min' END AS nm_gap
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE f.ds = 'train' AND NOT coalesce(f.nm_unmatched, false) AND f.y <= 10800 AND f.d_aobt3 IS NOT NULL
      AND a.adsb_has_ground
)
SELECT nm_gap, count(*) AS n,
  round(median(abs(d_aobt3 - y)), 0) AS medae_nm,
  count(*) FILTER (WHERE parked AND fm IS NOT NULL) AS n_parked,
  round(median(abs(fm - y)) FILTER (WHERE parked AND fm IS NOT NULL), 0) AS medae_adsb_first_move_parked,
  round(avg((abs(fm - y) < abs(d_aobt3 - y))::INT) FILTER (WHERE parked AND fm IS NOT NULL), 3) AS share_adsb_closer_parked,
  count(*) FILTER (WHERE sm IS NOT NULL) AS n_stand,
  round(median(abs(sm - y)) FILTER (WHERE sm IS NOT NULL), 0) AS medae_adsb_stand,
  round(avg((abs(sm - y) < abs(d_aobt3 - y))::INT) FILTER (WHERE sm IS NOT NULL), 3) AS share_adsb_closer_stand
FROM d GROUP BY ROLLUP (nm_gap) ORDER BY nm_gap NULLS LAST
```

5 rows

| nm_gap     |      n |   medae_nm |   n_parked |   medae_adsb_first_move_parked |   share_adsb_closer_parked |   n_stand |   medae_adsb_stand |   share_adsb_closer_stand |
|:-----------|-------:|-----------:|-----------:|-------------------------------:|---------------------------:|----------:|-------------------:|--------------------------:|
| a ≤1 min   |  34199 |         30 |       4554 |                             30 |                      0.418 |     13903 |                 22 |                     0.517 |
| b 1–5 min  |  85416 |        147 |      11828 |                             32 |                      0.796 |     32939 |                 23 |                     0.885 |
| c 5–15 min |  25490 |        416 |       3797 |                             39 |                      0.901 |      8911 |                 31 |                     0.948 |
| d >15 min  |   4339 |       1259 |        697 |                             45 |                      0.9   |      1695 |                 32 |                     0.953 |
| nan        | 149444 |        139 |      20876 |                             33 |                      0.736 |     57448 |                 24 |                     0.808 |
