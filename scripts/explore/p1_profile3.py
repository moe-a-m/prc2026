"""P1 profiling: second=0 by month, AOBT_3 − BLOCK offset distribution."""
from prc import db

con = db.connect(read_only=True)
C = lambda name, sql, note="": print(name, "\n", db.save_check(con, name, sql, note).to_string(max_rows=150), "\n")

C("p1_block_sec0_by_month", """
PIVOT (SELECT ADEP_mvt ap, strftime(src_month,'%m') m, round(100.0*avg((second(BLOCK_TIME_UTC_mvt)=0)::INT),1) v
       FROM raw_training WHERE PHASE_mvt='DEP' GROUP BY ALL)
ON m USING first(v) GROUP BY ap ORDER BY ap""", "% DEP rows with BLOCK second = 0, airport × month.")

C("p1_aobt3_minus_block_hist", """
-- offset d = AOBT_3 − BLOCK in seconds, binned
WITH d AS (SELECT ADEP_mvt ap, epoch(AOBT_3_flt)-epoch(BLOCK_TIME_UTC_mvt) d FROM raw_training
           WHERE PHASE_mvt='DEP' AND AOBT_3_flt IS NOT NULL)
SELECT ap,
 round(100.0*avg((d < -600)::INT),1) "<-600",
 round(100.0*avg((d >= -600 AND d < -180)::INT),1) "[-600,-180)",
 round(100.0*avg((d >= -180 AND d < -60)::INT),1) "[-180,-60)",
 round(100.0*avg((d >= -60 AND d <= 0)::INT),1) "[-60,0]",
 round(100.0*avg((d > 0 AND d <= 60)::INT),1) "(0,60]",
 round(100.0*avg((d > 60 AND d <= 180)::INT),1) "(60,180]",
 round(100.0*avg((d > 180 AND d <= 600)::INT),1) "(180,600]",
 round(100.0*avg((d > 600)::INT),1) ">600",
 median(d) med
FROM d GROUP BY ROLLUP(ap) ORDER BY ap NULLS LAST""")

C("p1_aobt3_minus_block_by_month", """
PIVOT (SELECT ADEP_mvt ap, strftime(src_month,'%m') m, median(epoch(AOBT_3_flt)-epoch(BLOCK_TIME_UTC_mvt)) v
       FROM raw_training WHERE PHASE_mvt='DEP' GROUP BY ALL)
ON m USING first(v) GROUP BY ap ORDER BY ap""", "Median AOBT_3 − BLOCK (s), airport × month.")
