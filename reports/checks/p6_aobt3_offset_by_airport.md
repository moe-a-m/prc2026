# Check: p6_aobt3_offset_by_airport

Run at 2026-10-03T06:01:06+00:00 (UTC), duckdb 1.5.6.

NM-matched 2025 departures with |MVT-AOBT_3-y| < 600 s ('regular'): second==0 shares of AOBT_3 / MVT / BLOCK and the NM-proxy error (MVT-AOBT_3)-y per airport, overall and split by AOBT_3 on a whole minute; spread of monthly medians.

```sql
WITH b AS (SELECT airport, month, second(t_aobt3)=0 a_s0, second(t_mvt)=0 m_s0, second(t_block)=0 b_s0,
    epoch(t_mvt)-epoch(t_aobt3) - y AS e FROM clean_dep
  WHERE ds='train' AND NOT f_no_nm_match AND t_aobt3 IS NOT NULL AND abs(epoch(t_mvt)-epoch(t_aobt3) - y) < 600),
m AS (SELECT airport, month, median(e) med_e FROM b GROUP BY ALL)
SELECT b.airport, count(*) n, round(100*avg(a_s0::INT),1) pct_aobt3_sec0, round(100*avg(m_s0::INT),1) pct_mvt_sec0,
  round(100*avg(b_s0::INT),1) pct_block_sec0,
  round(median(e)) med_proxy_minus_y, round(median(e) FILTER (a_s0)) med_if_aobt3_sec0, round(median(e) FILTER (NOT a_s0)) med_if_aobt3_not_sec0,
  round(quantile_cont(e,0.25)) q25, round(quantile_cont(e,0.75)) q75,
  (SELECT round(min(med_e)) FROM m WHERE m.airport=b.airport) min_month_med, (SELECT round(max(med_e)) FROM m WHERE m.airport=b.airport) max_month_med
FROM b GROUP BY b.airport ORDER BY 1
```

10 rows

| airport   |      n |   pct_aobt3_sec0 |   pct_mvt_sec0 |   pct_block_sec0 |   med_proxy_minus_y |   med_if_aobt3_sec0 |   med_if_aobt3_not_sec0 |   q25 |   q75 |   min_month_med |   max_month_med |
|:----------|-------:|-----------------:|---------------:|-----------------:|--------------------:|--------------------:|------------------------:|------:|------:|----------------:|----------------:|
| EDDF      | 224395 |             99   |            1.8 |              1.7 |                  91 |                  90 |                     111 |   -37 |   199 |              75 |             112 |
| EDDM      | 154186 |            100   |            8.3 |              8.3 |                   1 |                   1 |                     -37 |  -121 |   119 |              -5 |              58 |
| EGLL      | 222774 |            100   |            8.2 |              8.3 |                   6 |                   6 |                      53 |  -122 |   182 |               4 |              57 |
| EHAM      | 231269 |             83.9 |            1.7 |              1.6 |                  97 |                  93 |                     115 |   -10 |   214 |              87 |             105 |
| LEBL      | 170214 |             99.6 |            1.7 |              8.3 |                  -5 |                  -5 |                     -23 |  -175 |   114 |             -57 |               1 |
| LEMD      | 205016 |             99.7 |            1.6 |              8.3 |                   3 |                   3 |                      -4 |  -119 |   121 |              -3 |              57 |
| LFPG      | 218936 |             99.7 |            8.3 |              8.2 |                  -4 |                  -4 |                     -59 |  -177 |   121 |             -56 |              -1 |
| LIRF      | 137540 |             99.6 |            8.3 |              8.3 |                 -60 |                 -60 |                    -124 |  -241 |    66 |            -115 |              -1 |
| LSZH      | 128966 |            100   |            1.7 |              2   |                 -27 |                 -27 |                     -72 |  -170 |    99 |             -37 |             -22 |
| LTFM      | 226020 |             99.4 |            8.3 |              8   |                 241 |                 241 |                     266 |    56 |   417 |             183 |             299 |
