# Check: p6_pred_vs_proxy_disagreement

Run at 2026-10-03T05:57:53+00:00 (UTC), duckdb 1.5.6.

EXP-031 hold-out, NM-matched rows with AOBT_3: disagreement between model prediction and the raw NM proxy MVT-AOBT_3, split by a label-free 'proxy suspect' marker (|AOBT_3-EOBT_1|>1 h or AOBT_3 after take-off). Compares squared error now vs if the raw proxy were used.

```sql
WITH oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof), b AS (
  SELECT o.mvt_id, o.fold, o.y_oof y, o.pred, o.se, c.airport, epoch(c.t_mvt)-epoch(c.t_aobt3) d_aobt3,
    abs(epoch(c.t_aobt3) - epoch(c.t_eobt1)) > 3600 OR epoch(c.t_mvt) < epoch(c.t_aobt3) AS suspect
  FROM oof o JOIN clean_dep c USING (mvt_id) WHERE NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL)
SELECT CASE WHEN abs(pred-d_aobt3) <= 600 THEN 'a <=10min' WHEN abs(pred-d_aobt3) <= 1800 THEN 'b 10-30min'
            WHEN abs(pred-d_aobt3) <= 3600 THEN 'c 30-60min' ELSE 'd >60min' END AS pred_vs_proxy,
  suspect AS proxy_suspect, count(*) n, round(100*avg((abs(y-d_aobt3)<=300)::INT),1) pct_proxy_within5min,
  round(100*avg((abs(y-pred)<abs(y-d_aobt3))::INT),1) pct_model_closer,
  round(100*sum(se)/any_value(tot_se),2) pct_total_sq_err_now,
  round(100*sum((d_aobt3-y)*(d_aobt3-y))/any_value(tot_se),2) pct_total_sq_err_if_proxy
FROM b, tot GROUP BY ALL ORDER BY 1, 2
```

8 rows

| pred_vs_proxy   | proxy_suspect   |      n |   pct_proxy_within5min |   pct_model_closer |   pct_total_sq_err_now |   pct_total_sq_err_if_proxy |
|:----------------|:----------------|-------:|-----------------------:|-------------------:|-----------------------:|----------------------------:|
| a <=10min       | False           | 321854 |                   77   |               66.6 |                  29.91 |                       62.01 |
| a <=10min       | True            |    204 |                   51.5 |               66.7 |                   0.34 |                        0.43 |
| b 10-30min      | False           |  15115 |                    8.7 |               87.8 |                   7.01 |                       35.22 |
| b 10-30min      | True            |    271 |                   15.9 |               70.8 |                   0.59 |                        1.44 |
| c 30-60min      | False           |    929 |                    3   |               91.2 |                   1.32 |                       13.29 |
| c 30-60min      | True            |    291 |                    0.7 |               93.5 |                   0.82 |                        6.37 |
| d >60min        | False           |    117 |                   14.5 |               70.9 |                   7.61 |                        4.15 |
| d >60min        | True            |    265 |                    0   |               97   |                   0.74 |                       19.86 |
