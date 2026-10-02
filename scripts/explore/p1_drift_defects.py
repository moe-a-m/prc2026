"""Drift of defect-prone populations, Jan/Jul 2025 vs Jan/Jul 2026 (CLAUDE.md §3 drift)."""
from prc import db

con = db.connect(read_only=True)
C = lambda name, sql, note="": print(name, "\n", db.save_check(con, name, sql, note).to_string(max_rows=150), "\n")

C("p1_drift_defect_population", """
SELECT airport, strftime(month, '%Y-%m') m, count(*) n,
  round(100.0*avg(nm_unmatched::INT),2) pct_unmatched,
  round(100.0*avg((d_sched > 3*3600)::INT),3) pct_dsched_gt3h,
  round(100.0*avg((nm_unmatched AND d_sched > 3*3600)::INT),3) pct_unm_dsched_gt3h,
  round(100.0*avg((day_shift <> 0)::INT),3) pct_day_shift,
  round(100.0*avg(actype_mvt_missing::INT),3) pct_actype_missing
FROM feat_dep WHERE month(month) IN (1, 7) GROUP BY ALL ORDER BY airport, m""",
 "Jan/Jul 2025 (train) vs Jan/Jul 2026 (ranking). d_sched = take-off − scheduled.")

C("p1_tail_given_dsched_2025", """
-- In 2025, when take-off is >3 h after schedule, how often is the label an echo (y ≈ d_sched)?
SELECT airport, nm_unmatched, count(*) n,
  round(100.0*avg((abs(y - d_sched) <= 60)::INT),1) pct_y_eq_dsched,
  round(100.0*avg((y > 3600)::INT),1) pct_y_gt1h, round(median(y)) med_y
FROM feat_dep WHERE ds='train' AND d_sched > 3*3600 GROUP BY ALL ORDER BY airport, nm_unmatched""")
