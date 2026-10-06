# Check: p4_adsblol_stand_gap_codes

Run at 2026-10-06T10:46:51+00:00 (UTC), duckdb 1.5.6.

Top-15 APDF stand codes per airport (by departures with an ADS-B ground segment) that have no OSM parking_position in stg_stand_geo — shows whether the miss is a code-normalisation problem or a genuinely unmapped stand.

```sql
WITH d AS (
    SELECT f.airport, f.stand, count(*) AS n_dep
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id)
    LEFT JOIN stg_stand_geo g ON g.airport = f.airport AND g.stand = f.stand
    WHERE month(f.month) IN (1, 7) AND a.adsb_has_ground AND f.stand IS NOT NULL AND g.stand IS NULL
    GROUP BY ALL
)
SELECT * FROM (SELECT *, row_number() OVER (PARTITION BY airport ORDER BY n_dep DESC, stand) AS rk FROM d)
WHERE rk <= 15 ORDER BY airport, rk
```

107 rows

| airport   | stand   |   n_dep |   rk |
|:----------|:--------|--------:|-----:|
| EDDF      | V151    |     450 |    1 |
| EDDF      | V153    |     412 |    2 |
| EDDF      | D4A     |     215 |    3 |
| EDDF      | A54B    |     210 |    4 |
| EDDF      | A66A    |     161 |    5 |
| EDDF      | F237    |     102 |    6 |
| EDDF      | J1      |     101 |    7 |
| EDDF      | F238    |      66 |    8 |
| EDDF      | V333    |      23 |    9 |
| EDDF      | V335    |      20 |   10 |
| EDDF      | V337    |      13 |   11 |
| EDDF      | V152    |       4 |   12 |
| EDDF      | J2A     |       1 |   13 |
| EDDF      | J2B     |       1 |   14 |
| EDDF      | X115M   |       1 |   15 |
| EDDM      | 356     |     317 |    1 |
| EDDM      | 355     |     298 |    2 |
| EDDM      | 371     |     287 |    3 |
| EDDM      | 514     |     245 |    4 |
| EDDM      | 515     |     225 |    5 |
| EDDM      | 513     |     221 |    6 |
| EDDM      | 517     |     220 |    7 |
| EDDM      | 516     |     215 |    8 |
| EDDM      | 518     |     191 |    9 |
| EDDM      | 512     |     189 |   10 |
| EDDM      | 354     |     188 |   11 |
| EDDM      | 519     |     186 |   12 |
| EDDM      | 520     |     165 |   13 |
| EDDM      | 522     |     164 |   14 |
| EDDM      | 106     |     161 |   15 |
| EGLL      | 235     |     210 |    1 |
| EGLL      | 237L    |     152 |    2 |
| EGLL      | 237R    |     145 |    3 |
| EGLL      | 237     |     115 |    4 |
| EGLL      | 422     |      63 |    5 |
| EHAM      | B20     |     764 |    1 |
| EHAM      | H04     |     672 |    2 |
| EHAM      | G03     |     545 |    3 |
| EHAM      | H05     |     537 |    4 |
| EHAM      | A44     |     487 |    5 |
| EHAM      | R77     |      57 |    6 |
| EHAM      | HG03    |      47 |    7 |
| EHAM      | HG01    |      44 |    8 |
| EHAM      | R74     |      39 |    9 |
| EHAM      | R72     |      34 |   10 |
| EHAM      | R80     |      21 |   11 |
| EHAM      | R81     |      20 |   12 |
| EHAM      | HG32    |      18 |   13 |
| EHAM      | R82     |      16 |   14 |
| EHAM      | HG11    |       6 |   15 |
| LEBL      | UNKNOWN |     430 |    1 |
| LEBL      | 285     |     361 |    2 |
| LEBL      | 281     |     317 |    3 |
| LEBL      | 287     |     287 |    4 |
| LEBL      | 291     |     249 |    5 |
| LEBL      | 280     |     204 |    6 |
| LEBL      | 295     |     198 |    7 |
| LEBL      | 282     |     188 |    8 |
| LEBL      | 276     |     177 |    9 |
| LEBL      | 296     |     173 |   10 |
| LEBL      | 278     |     169 |   11 |
| LEBL      | 410     |     164 |   12 |
| LEBL      | 290     |     163 |   13 |
| LEBL      | 292     |     154 |   14 |
| LEBL      | 151A    |     153 |   15 |
| LEMD      | 402     |     146 |    1 |
| LEMD      | 25      |      45 |    2 |
| LEMD      | 26      |      41 |    3 |
| LEMD      | 24      |      37 |    4 |
| LEMD      | 23      |      32 |    5 |
| LEMD      | UNKNOWN |       3 |    6 |
| LFPG      | I50     |      36 |    1 |
| LFPG      | I54     |      24 |    2 |
| LFPG      | I52     |      21 |    3 |
| LFPG      | I79     |      19 |    4 |
| LFPG      | E44     |      16 |    5 |
| LFPG      | I36     |      16 |    6 |
| LFPG      | I73     |      16 |    7 |
| LFPG      | I77     |      13 |    8 |
| LFPG      | I71     |      10 |    9 |
| LFPG      | I75     |       9 |   10 |
| LFPG      | I35     |       8 |   11 |
| LFPG      | I39     |       8 |   12 |
| LFPG      | I38     |       7 |   13 |
| LFPG      | I37     |       6 |   14 |
| LFPG      | S6B     |       2 |   15 |
| LIRF      | 801     |     172 |    1 |
| LIRF      | 108     |      51 |    2 |
| LIRF      | 106     |       5 |    3 |
| LIRF      | 851     |       5 |    4 |
| LIRF      | 852     |       4 |    5 |
| LIRF      | 849     |       3 |    6 |
| LSZH      | GA6     |     650 |    1 |
| LSZH      | REG     |     264 |    2 |
| LSZH      | MFG     |     141 |    3 |
| LSZH      | HAN     |     133 |    4 |
| LSZH      | T50     |      34 |    5 |
| LSZH      | HPW     |      15 |    6 |
| LSZH      | GA8     |      11 |    7 |
| LSZH      | X17     |       8 |    8 |
| LSZH      | W51     |       7 |    9 |
| LSZH      | GA3     |       3 |   10 |
| LSZH      | X11     |       3 |   11 |
| LSZH      | C1      |       1 |   12 |
| LSZH      | F1      |       1 |   13 |
| LSZH      | JET     |       1 |   14 |
| LSZH      | TWR     |       1 |   15 |
