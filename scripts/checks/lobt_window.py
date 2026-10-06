"""Is the airport off-block bounded by an NM reference time? 2025 departures with that reference (feat_dep d_* = take-off
minus the reference time; y = take-off − off-block, so off-block − reference = d − y).

  python scripts/checks/lobt_window.py
"""
from prc import db

con = db.connect(read_only=True)

REF = """
WITH t AS (SELECT * FROM feat_dep WHERE ds = 'train'),
u AS (
    SELECT 'LOBT (last known off-block)' AS reference, d_lobt - y AS block_minus_ref, d_lobt AS mvt_minus_ref FROM t WHERE d_lobt IS NOT NULL
    UNION ALL SELECT 'IOBT (initial off-block)', d_iobt - y, d_iobt FROM t WHERE d_iobt IS NOT NULL
    UNION ALL SELECT 'EOBT_1 (FPL-based trajectory)', d_eobt1 - y, d_eobt1 FROM t WHERE d_eobt1 IS NOT NULL
    UNION ALL SELECT 'schedule (airport)', d_sched - y, d_sched FROM t WHERE d_sched IS NOT NULL
)
SELECT reference, count(*) AS n,
  min(block_minus_ref) AS min_block_minus_ref_s, max(block_minus_ref) AS max_block_minus_ref_s,
  count(*) FILTER (WHERE abs(block_minus_ref) > 3606) AS n_block_outside_3606,
  count(*) FILTER (WHERE abs(block_minus_ref) BETWEEN 3540 AND 3606) AS n_block_in_last_minute,
  count(*) FILTER (WHERE abs(mvt_minus_ref) > 3606) AS n_takeoff_outside_3606,
  max(abs(mvt_minus_ref)) AS max_abs_takeoff_minus_ref_s
FROM u GROUP BY reference ORDER BY reference
"""
db.save_check(con, "lobt_window_references", REF,
              "Hard-edge test per NM/airport reference time (2025 departures having that reference). If the off-block "
              "(not the take-off) is bounded by exactly one reference, the bound is a property of how airport records "
              "were associated with NM flights (APDF spec Ed. 1.0 §4: AOBT is a matching key), not of operations.")

HIST = """
SELECT (floor((d_lobt - y) / 300) * 300)::INT AS block_minus_lobt_bin_s, count(*) AS n
FROM feat_dep WHERE ds = 'train' AND d_lobt IS NOT NULL AND abs(d_lobt - y) >= 2400
GROUP BY ALL ORDER BY 1
"""
db.save_check(con, "lobt_window_tails", HIST,
              "Counts of 2025 departures by off-block − LOBT in 5-min bins, |off-block − LOBT| ≥ 40 min only: the "
              "distribution runs up to the ±1 h edge and stops (no thinning tail beyond).")

RANK = """
SELECT airport, count(*) AS n_dep, count(d_lobt) AS n_with_lobt,
  count(*) FILTER (WHERE d_lobt IS NOT NULL AND d_lobt - 3606 > 0) AS n_window_excludes_zero_taxi,
  min(d_lobt) AS min_takeoff_minus_lobt_s, max(d_lobt) AS max_takeoff_minus_lobt_s
FROM feat_dep WHERE ds = 'rank' GROUP BY ROLLUP (airport) ORDER BY airport NULLS LAST
"""
db.save_check(con, "lobt_window_rank", RANK,
              "2026 ranking departures: LOBT availability (the window applies only where LOBT exists) and take-off − LOBT "
              "range, the input that defines each row's feasible taxi-out interval [d_lobt − 3606, d_lobt + 3606].")
