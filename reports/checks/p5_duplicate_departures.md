# Check: p5_duplicate_departures

Run at 2026-10-03T05:32:55+00:00 (UTC), duckdb 1.5.6.

Departures sharing (airport, flight number, UTC date). Groups within 1 h of each other are candidate duplicate records.

```sql
WITH d AS (SELECT ds, airport, flight_mvt, t_mvt::DATE AS dday, count(*) c, max(epoch(t_mvt))-min(epoch(t_mvt)) span_s
           FROM stg_mvt WHERE phase='DEP' AND flight_mvt IS NOT NULL GROUP BY ALL HAVING count(*) > 1)
SELECT ds, count(*) n_groups, sum(c) n_rows, sum((span_s < 3600)::INT) n_groups_within_1h, round(median(span_s)) med_span_s
FROM d GROUP BY 1 ORDER BY 1
```

2 rows

| ds    |   n_groups |   n_rows |   n_groups_within_1h |   med_span_s |
|:------|-----------:|---------:|---------------------:|-------------:|
| rank  |        490 |      985 |                   23 |        74845 |
| train |       2697 |     5401 |                  124 |        70111 |
