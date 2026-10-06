-- Recent departures' NM taxi-out proxy (M-033). For each departure, departures at the same airport (and runway) that
-- took off strictly earlier: mean of their take-off − NM actual off-block (d_aobt3, kept when 0–3 h) over the previous
-- 30 min and over the last 5 departures, plus how many contributed. Label-free: d_aobt3 exists for 2025 and the 2026
-- ranking rows alike; departure labels (y) are never read. Literature: average taxi time of the previous half hour
-- (Balakrishna et al. 2008) / quarter hour (Srivastava 2011), average speed of the last 5/10 departures (Wang et al.
-- 2021, Transp. Res. C 124:102892). Means rounded to 0.1 s so rebuilds are bit-identical.
CREATE OR REPLACE TABLE feat_dep_recent AS
WITH d AS (
    SELECT mvt_id, airport, runway, t_mvt_epoch,
           CASE WHEN d_aobt3 BETWEEN 0 AND 10800 THEN d_aobt3 END AS px
    FROM feat_dep
)
SELECT mvt_id,
    round(avg(px) OVER ap30, 1)                 AS rec_px_ap_30p,
    count(px) OVER ap30                         AS rec_n_ap_30p,
    round(avg(px) OVER ap5, 1)                  AS rec_px_ap_last5,
    round(avg(px) OVER rw30, 1)                 AS rec_px_rw_30p,
    count(px) OVER rw30                         AS rec_n_rw_30p
FROM d
WINDOW ap30 AS (PARTITION BY airport ORDER BY t_mvt_epoch RANGE BETWEEN 1800 PRECEDING AND 1 PRECEDING),
       ap5  AS (PARTITION BY airport ORDER BY t_mvt_epoch, mvt_id ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING),
       rw30 AS (PARTITION BY airport, runway ORDER BY t_mvt_epoch RANGE BETWEEN 1800 PRECEDING AND 1 PRECEDING);
