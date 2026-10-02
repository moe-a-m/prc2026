# Check: p4_metar_parser_disagreements

Run at 2026-10-02T12:31:04+00:00 (UTC), duckdb 1.5.6.

```sql
WITH s AS (SELECT * FROM stg_metar WHERE wxcodes IS NOT NULL USING SAMPLE reservoir(400 ROWS) REPEATABLE (42))
SELECT station, t_obs, wxcodes, wx_snow, wx_freezing, wx_thunder, wx_fog, metar FROM s
WHERE wx_snow <> regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|DR|BL|SH|TS|FZ)*(SN|SG|PL)')
   OR wx_freezing <> regexp_matches(metar, ' [-+]?(VC)?FZ')
   OR wx_thunder <> regexp_matches(metar, ' [-+]?(VC)?TS')
   OR wx_fog <> regexp_matches(metar, ' [-+]?(VC|MI|BC|PR|FZ)*FG') LIMIT 30
```

1 rows

| station   | t_obs               | wxcodes   | wx_snow   | wx_freezing   | wx_thunder   | wx_fog   | metar                                                                                      |
|:----------|:--------------------|:----------|:----------|:--------------|:-------------|:---------|:-------------------------------------------------------------------------------------------|
| EDDF      | 2025-08-28 01:50:00 | SHRA      | False     | False         | False        | False    | EDDF 280150Z AUTO 30004KT 9999 SHRA SCT021 FEW///CB 18/18 Q1007 TEMPO TSRA BKN010 BKN020CB |
