"""Final-phase drift and coverage checks (CLAUDE.md §3 drift rule; final phase adds Feb + Jun 2026, organizer e-mail
2026-10-08). Two saved checks:

  final_phase_input_drift   per airport and month (2025-01…12 training, 2026-01/02/06/07 final ranking set): departures,
                            NM-unmatched share, coverage and median of take-off − AOBT_3 / − LOBT / − schedule — the
                            inputs the recipe leans on (M-004, M-022, M-031, M-014/M-026)
  final_phase_adsb_coverage per airport and month: share of departures with an adsb.lol ground segment, seen at / still
                            at the own OSM stand (M-028 sources) — all 485 extracted days

  python scripts/checks/final_phase_drift.py
"""
from prc import db

con = db.connect(read_only=True)

DRIFT = """
SELECT airport, strftime(month, '%Y-%m') AS ym, ds, count(*) AS n_dep,
  round(100 * avg(nm_unmatched::INT), 1) AS pct_nm_unmatched,
  round(100 * avg((d_aobt3 IS NOT NULL)::INT), 1) AS pct_aobt3,
  round(median(d_aobt3), 0) AS med_d_aobt3_s,
  round(100 * avg((d_lobt IS NOT NULL)::INT), 1) AS pct_lobt,
  round(median(d_lobt), 0) AS med_d_lobt_s,
  round(median(d_sched), 0) AS med_d_sched_s
FROM feat_dep
GROUP BY ALL ORDER BY airport, ym
"""
db.save_check(con, "final_phase_input_drift", DRIFT,
              "Inputs the final recipe leans on, per airport and month: training months 2025-01…12 (ds = train) and the "
              "four final-phase months 2026-01/02/06/07 (ds = rank, final_ranking.parquet). d_* = take-off minus the "
              "NM/airport time in seconds. Compare Feb/Jun 2026 with Feb/Jun 2025 (and Jan/Jul) for drift.",
              max_rows=200)

COV = """
WITH days AS (SELECT DISTINCT t::DATE AS day FROM stg_adsb),
d AS (
    SELECT f.airport, strftime(f.month, '%Y-%m') AS ym, f.ds,
           coalesce(a.adsb_has_ground, false) AS has_ground,
           coalesce(s.adsb_seen_at_stand, false) AS seen_at_stand,
           coalesce(s.adsb_still_at_stand, false) AS still_at_stand
    FROM feat_dep f LEFT JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE timezone('UTC', to_timestamp(f.t_mvt_epoch))::DATE IN (SELECT day FROM days)
)
SELECT airport, ym, ds, count(*) AS n_dep,
  round(100 * avg(has_ground::INT), 1) AS pct_ground,
  round(100 * avg(seen_at_stand::INT), 1) AS pct_seen_at_stand,
  round(100 * avg(still_at_stand::INT), 1) AS pct_still_at_stand
FROM d GROUP BY ALL ORDER BY airport, ym
"""
n_days = con.sql("SELECT count(DISTINCT t::DATE) FROM stg_adsb").fetchone()[0]
db.save_check(con, "final_phase_adsb_coverage", COV,
              f"adsb.lol coverage on the {n_days} extracted UTC days (all of 2025; Jan, Feb, Jun, Jul 2026): share of "
              "departures with a ground (taxi) segment, seen within 60 m of their OSM stand, seen stationary there "
              "(the M-028 'still' source). Receiver-network drift 2025→2026 per CLAUDE.md §3.",
              max_rows=200)
