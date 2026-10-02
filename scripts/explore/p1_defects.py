"""Label-defect taxonomy (CLAUDE.md §3): near-echo of SCHED and day-shifted block dates."""
from prc import db

con = db.connect(read_only=True)
C = lambda name, sql, note="": print(name, "\n", db.save_check(con, name, sql, note).to_string(max_rows=150), "\n")

C("p1_defect_near_echo", """
WITH d AS (SELECT *, abs(epoch(t_block)-epoch(t_sched)) e_s, epoch(t_mvt)-epoch(t_sched) dsch FROM clean_dep WHERE ds='train'),
t AS (SELECT sum(y::DOUBLE^2) tot FROM d)  -- squared error of predicting 0 is meaningless; use the per-airport-median baseline below
SELECT airport, count(*) n,
  sum((e_s <= 10)::INT) n_echo10, round(100.0*avg((e_s<=10)::INT),2) pct_echo10,
  sum((e_s <= 10 AND f_no_nm_match)::INT) n_echo10_nomatch,
  sum((e_s <= 10 AND dsch > 3600)::INT) n_echo10_late1h,
  sum((y > 3600)::INT) n_y_gt1h, sum((y > 3600 AND e_s <= 10)::INT) n_y_gt1h_echo,
  sum((y > 3600 AND f_no_nm_match)::INT) n_y_gt1h_nomatch,
  round(100.0*avg(f_no_nm_match::INT),2) pct_nomatch
FROM d GROUP BY ROLLUP(airport) ORDER BY airport NULLS LAST""",
 "Near-echo = |BLOCK − SCHED| ≤ 10 s.")

C("p1_sq_error_share_airport_median", """
-- Share of squared error from top-1% rows under the per-airport-median baseline (in-sample, all 2025 DEP)
WITH m AS (SELECT airport, median(y) med FROM clean_dep WHERE ds='train' GROUP BY 1),
e AS (SELECT d.airport, d.f_no_nm_match, (y-med)^2 se, y FROM clean_dep d JOIN m USING (airport) WHERE ds='train'),
r AS (SELECT *, percent_rank() OVER (ORDER BY se DESC) pr FROM e)
SELECT round(sqrt(avg(se)),1) rmse_all,
       round(100*sum(se) FILTER (WHERE pr < 0.01)/sum(se),1) pct_sq_top1pct,
       round(100*sum(se) FILTER (WHERE y > 3*3600)/sum(se),1) pct_sq_y_gt3h,
       round(100*sum(se) FILTER (WHERE f_no_nm_match)/sum(se),1) pct_sq_nomatch,
       round(100.0*avg(f_no_nm_match::INT),2) pct_rows_nomatch,
       round(sqrt(avg(se) FILTER (WHERE y <= 3*3600)),1) rmse_excl_gt3h
FROM r""")

C("p1_unmatched_by_airport_month", """
PIVOT (SELECT airport, strftime(month,'%Y-%m') m, round(100.0*avg(f_no_nm_match::INT),2) v FROM clean_dep GROUP BY ALL)
ON m USING first(v) GROUP BY airport ORDER BY airport""", "% DEP rows without NM match, train 2025 and rank 2026 months.")
