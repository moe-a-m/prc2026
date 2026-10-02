"""P1 profiling: is MVT − AOBT_3 concentrated on NM default taxi values? Share of top-3 whole-minute values."""
from prc import db

con = db.connect(read_only=True)
C = lambda name, sql, note="": print(name, "\n", db.save_check(con, name, sql, note).to_string(max_rows=150), "\n")

C("p1_x_minute_concentration", """
WITH d AS (SELECT ADEP_mvt ap, RUNWAY_mvt rwy, round((epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt))/60) xm,
                  TAXITIME_SEC_mvt y, epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt) x
           FROM raw_training WHERE PHASE_mvt='DEP' AND AOBT_3_flt IS NOT NULL),
c AS (SELECT ap, xm, count(*) n, sqrt(avg((x-y)^2)) rmse_x, avg((abs(x-y)<=60)::INT) w60 FROM d GROUP BY ALL),
r AS (SELECT *, row_number() OVER (PARTITION BY ap ORDER BY n DESC) rk, n/sum(n) OVER (PARTITION BY ap) AS shr FROM c)
SELECT ap, rk, xm AS x_minutes, n, round(100*shr,1) pct, round(rmse_x,0) rmse_x, round(100*w60,1) pct_within60
FROM r WHERE rk<=4 ORDER BY ap, rk""", "Top-4 rounded-minute values of MVT−AOBT_3 per airport, with error of x vs target in each bin.")

C("p1_x_error_by_ymag", """
-- where do big naive errors come from: label (y) extreme or x extreme?
WITH d AS (SELECT TAXITIME_SEC_mvt y, epoch(MVT_TIME_UTC_mvt)-epoch(AOBT_3_flt) x FROM raw_training WHERE PHASE_mvt='DEP' AND AOBT_3_flt IS NOT NULL)
SELECT CASE WHEN abs(x-y)<=60 THEN 'a <=60' WHEN abs(x-y)<=300 THEN 'b 60-300' WHEN abs(x-y)<=900 THEN 'c 300-900' ELSE 'd >900' END err_bin,
 count(*) n, round(100.0*count(*)/sum(count(*)) over(),2) pct_rows, round(100.0*sum((x-y)^2)/sum(sum((x-y)^2)) over(),2) pct_sq_err,
 round(median(y)) med_y, round(median(x)) med_x
FROM d GROUP BY 1 ORDER BY 1""")
