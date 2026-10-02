# Check: p4_adsb_match_2026-01-01

Run at 2026-10-02T14:18:43+00:00 (UTC), duckdb 1.5.6.

First extracted day (ranking day, no labels): share of departures matched to an ADS-B take-off, with a ground segment, with a stand stop.

```sql
SELECT f.airport, count(*) n_dep, round(100*avg(a.adsb_matched::INT),1) pct_matched, round(100*avg(a.adsb_has_ground::INT),1) pct_ground,
  round(100*avg((a.adsb_stand_end_s IS NOT NULL)::INT),1) pct_stand_stop, round(100*avg(a.adsb_cs_match::INT),1) pct_callsign_agree,
  round(median(a.adsb_dt_takeoff_s),1) med_dt_takeoff_s, round(median(a.adsb_n_pts)) med_ground_pts
FROM feat_dep_adsb a JOIN feat_dep f USING (mvt_id)
WHERE (timezone('UTC', to_timestamp(f.t_mvt_epoch)))::DATE = DATE '2026-01-01' GROUP BY 1 ORDER BY 1
```

10 rows

| airport   |   n_dep |   pct_matched |   pct_ground |   pct_stand_stop |   pct_callsign_agree |   med_dt_takeoff_s |   med_ground_pts |
|:----------|--------:|--------------:|-------------:|-----------------:|---------------------:|-------------------:|-----------------:|
| EDDF      |     429 |          92.8 |         75.1 |             11.2 |                 96.2 |               -3.9 |               28 |
| EDDM      |     320 |          95.9 |         95.9 |             50.3 |                 99.7 |               14.7 |              101 |
| EGLL      |     645 |          88.7 |         18.1 |              5.3 |                 98.3 |               26.8 |               23 |
| EHAM      |     618 |          98.2 |         97.9 |             38.8 |                 99   |              -25.9 |               85 |
| LEBL      |     452 |          99.6 |         97.8 |             14.8 |                 98.9 |               -7.3 |               80 |
| LEMD      |     523 |          98.5 |         98.5 |             23.1 |                 99.6 |              -15.6 |              100 |
| LFPG      |     595 |          77.3 |         16   |              0.2 |                 93.7 |               27.2 |                4 |
| LIRF      |     397 |          92.9 |         71.5 |              5.3 |                 96.6 |               10   |               18 |
| LSZH      |     320 |          95.9 |         90   |             42.8 |                 99   |              -10.2 |               92 |
| LTFM      |     671 |           0   |          0   |              0   |                nan   |              nan   |              nan |
