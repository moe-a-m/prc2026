# Check: p4_adsblol_offblock_2025

Run at 2026-10-03T20:23:24+00:00 (UTC), duckdb 1.5.6.

2025 labelled departures (y ≤ 3 h) on the extracted days. est = first movement at the own stand when seen stationary there (M-021), else first movement when seen parked (M-018). Raw estimate vs target, no model.

```sql
WITH days AS (SELECT DISTINCT t::DATE AS day FROM stg_adsb),
d AS (
    SELECT f.airport, f.y, a.*, s.*
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE f.ds = 'train' AND f.y <= 10800
      AND timezone('UTC', to_timestamp(f.t_mvt_epoch))::DATE IN (SELECT day FROM days)
),
e AS (  -- best available off-block estimate: stationary at own stand > seen parked > first ground observation
    SELECT *, CASE WHEN adsb_still_at_stand THEN adsb_stand_move_s WHEN adsb_seen_parked THEN adsb_first_move_s END AS est,
              CASE WHEN adsb_still_at_stand THEN 'stand' WHEN adsb_seen_parked THEN 'parked' END AS src
    FROM d
)
SELECT airport, count(*) AS n_dep, count(est) AS n_est, round(100*count(est)/count(*), 1) AS pct_est,
  round(100*avg((abs(est - y) <= 60)::INT) FILTER (WHERE est IS NOT NULL), 1) AS pct_within60,
  round(sqrt(avg((est - y)^2) FILTER (WHERE est IS NOT NULL)), 0) AS rmse_est,
  round(median(abs(est - y)) FILTER (WHERE est IS NOT NULL), 0) AS medae_est
FROM e GROUP BY ROLLUP (airport) ORDER BY airport NULLS LAST
```

11 rows

| airport   |   n_dep |   n_est |   pct_est |   pct_within60 |   rmse_est |   medae_est |
|:----------|--------:|--------:|----------:|---------------:|-----------:|------------:|
| EDDF      |    7235 |     403 |       5.6 |           62.8 |        461 |          37 |
| EDDM      |    5367 |     801 |      14.9 |           79.4 |        787 |          37 |
| EGLL      |    7822 |     163 |       2.1 |            0   |        729 |         162 |
| EHAM      |    8060 |    2877 |      35.7 |           86.3 |        975 |          17 |
| LEBL      |    6004 |     857 |      14.3 |           72.5 |        686 |          32 |
| LEMD      |    7002 |      51 |       0.7 |           15.7 |        308 |         118 |
| LFPG      |    7843 |       7 |       0.1 |           28.6 |       1029 |        1100 |
| LIRF      |    5457 |      91 |       1.7 |           23.1 |        859 |         219 |
| LSZH      |    4505 |     774 |      17.2 |           79.5 |       1439 |          29 |
| LTFM      |    9018 |       0 |       0   |          nan   |        nan |         nan |
| nan       |   68313 |    6024 |       8.8 |           77   |        954 |          23 |
