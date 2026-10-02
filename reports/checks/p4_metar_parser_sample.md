# Check: p4_metar_parser_sample

Run at 2026-10-02T12:31:04+00:00 (UTC), duckdb 1.5.6.

Agreement of parsed flags with an independent regex on the raw METAR text (400-row sample).

```sql
-- flags derived from IEM wxcodes vs presence of the same groups in the raw METAR text, random sample of
-- reports that have any weather code (reproducible: SAMPLE with fixed seed)
WITH s AS (SELECT * FROM stg_metar WHERE wxcodes IS NOT NULL USING SAMPLE reservoir(400 ROWS) REPEATABLE (42)),
c AS (SELECT *,
  regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|DR|BL|SH|TS|FZ)*(SN|SG|PL)') raw_snow,
  regexp_matches(metar, ' [-+]?(VC)?FZ') raw_freezing,
  regexp_matches(metar, ' [-+]?(VC)?TS') raw_thunder,
  regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|FZ)*FG') raw_fog FROM s)
SELECT count(*) n,
  sum((wx_snow = raw_snow)::INT) agree_snow, sum((wx_freezing = raw_freezing)::INT) agree_freezing,
  sum((wx_thunder = raw_thunder)::INT) agree_thunder, sum((wx_fog = raw_fog)::INT) agree_fog
FROM c
```

1 rows

|   n |   agree_snow |   agree_freezing |   agree_thunder |   agree_fog |
|----:|-------------:|-----------------:|----------------:|------------:|
|  69 |           69 |               69 |              68 |          69 |
