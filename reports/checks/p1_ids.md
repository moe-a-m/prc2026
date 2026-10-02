# Check: p1_ids

Run at 2026-10-02T10:11:48+00:00 (UTC), duckdb 1.5.6.

```sql
SELECT 'train' ds, count(*) n, count(MVT_ID_mvt) n_id, count(DISTINCT MVT_ID_mvt) n_distinct,
       sum((MVT_ID_mvt <> floor(MVT_ID_mvt))::INT) n_nonintegral, min(MVT_ID_mvt) mn, max(MVT_ID_mvt) mx,
       count(FLIGHT_ID_mvt) n_flight_id, count(DISTINCT FLIGHT_ID_mvt) n_flight_distinct
FROM raw_training
UNION ALL
SELECT 'rank', count(*), count(MVT_ID_mvt), count(DISTINCT MVT_ID_mvt),
       sum((MVT_ID_mvt <> floor(MVT_ID_mvt))::INT), min(MVT_ID_mvt), max(MVT_ID_mvt),
       count(FLIGHT_ID_mvt), count(DISTINCT FLIGHT_ID_mvt)
FROM raw_ranking
UNION ALL
SELECT 'train∩rank ids', count(*), NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM (SELECT DISTINCT MVT_ID_mvt FROM raw_training) t JOIN (SELECT DISTINCT MVT_ID_mvt FROM raw_ranking) r USING (MVT_ID_mvt)
```

3 rows

| ds             |       n | n_id    | n_distinct   |   n_nonintegral |           mn |            mx | n_flight_id   | n_flight_distinct   |
|:---------------|--------:|:--------|:-------------|----------------:|-------------:|--------------:|:--------------|:--------------------|
| train          | 4167797 | 4167797 | 4167797      |               0 |   1.8198e+08 |   2.02065e+08 | 4136867       | 3821595             |
| rank           |  689534 | 689534  | 689534       |               0 |   2.0218e+08 |   2.13827e+08 | 682842        | 631919              |
| train∩rank ids |       0 | <NA>    | <NA>         |             nan | nan          | nan           | <NA>          | <NA>                |
