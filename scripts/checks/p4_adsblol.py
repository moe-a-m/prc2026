"""adsb.lol checks (M-018/M-021/M-028): coverage per airport-month, raw stand estimate vs hold-out predictions.

  python scripts/checks/p4_adsblol.py [BASE_EXP]      (default EXP-045; reads models/oof/<BASE>_{jan,jul}.parquet)
"""
import sys

from prc import db

BASE = sys.argv[1] if len(sys.argv) > 1 else "EXP-045"
OOF = f"read_parquet(['models/oof/{BASE}_jan.parquet', 'models/oof/{BASE}_jul.parquet'])"
con = db.connect(read_only=True)
days = con.sql("SELECT count(DISTINCT t::DATE) FILTER (WHERE month(t) IN (1, 7)) FROM stg_adsb").fetchone()[0]

COV = """
WITH days AS (SELECT DISTINCT t::DATE AS day FROM stg_adsb),
d AS (
    SELECT f.airport, strftime(f.month, '%Y-%m') AS ym, timezone('UTC', to_timestamp(f.t_mvt_epoch))::DATE AS day, a.*,
           coalesce(s.adsb_still_at_stand, false) AS still_at_stand, coalesce(s.adsb_seen_at_stand, false) AS seen_at_stand
    FROM feat_dep f JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
    WHERE timezone('UTC', to_timestamp(f.t_mvt_epoch))::DATE IN (SELECT day FROM days)
      AND month(f.month) IN (1, 7)  -- extracts spill a few hours into adjacent days (e.g. 30 Jun)
)
SELECT airport, ym, count(DISTINCT day) AS n_days, count(*) AS n_dep,
  round(100*avg(adsb_matched::INT), 1) AS pct_matched,
  round(100*avg(coalesce(adsb_has_ground, false)::INT), 1) AS pct_ground,
  round(100*avg(coalesce(adsb_seen_parked, false)::INT), 1) AS pct_seen_parked,
  round(100*avg(seen_at_stand::INT), 1) AS pct_seen_at_stand,
  round(100*avg(still_at_stand::INT), 1) AS pct_still_at_stand,
  round(median(adsb_n_pts) FILTER (WHERE adsb_has_ground), 0) AS med_pts_ground,
  round(median(adsb_max_gap_s) FILTER (WHERE adsb_has_ground), 0) AS med_max_gap_s
FROM d GROUP BY ROLLUP (airport, ym) ORDER BY airport NULLS LAST, ym NULLS LAST
"""
db.save_check(con, "p4_adsblol_coverage", COV,
              f"Departures on the {days} UTC days with adsb.lol extracts (full Jan + Jul 2025/2026 archive). Share of "
              "departures with a matched take-off, a ground (taxi) segment, seen parked (≥ 60 s stationary at segment "
              "start), seen within 60 m of the OSM stand, seen stationary there. Points/gaps are on the ground "
              "segment. Drift check 2025 vs 2026 per CLAUDE.md §3 (a participant 27/09: receiver network changed).")

Q_GAP = f"""
WITH o AS (SELECT mvt_id, pred FROM {OOF}),
e AS (
    SELECT f.airport, f.y, o.pred,
           CASE WHEN s.adsb_still_at_stand THEN s.adsb_stand_move_s WHEN a.adsb_seen_parked THEN a.adsb_first_move_s END AS est,
           CASE WHEN s.adsb_still_at_stand THEN 'stand' WHEN a.adsb_seen_parked THEN 'parked' END AS src
    FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb a USING (mvt_id) LEFT JOIN feat_dep_adsb_stand s USING (mvt_id)
)
SELECT src, CASE WHEN abs(est - pred) <= 60 THEN 'a ≤60' WHEN abs(est - pred) <= 180 THEN 'b 60–180'
                 WHEN abs(est - pred) <= 600 THEN 'c 180–600' ELSE 'd >600' END AS gap,
  count(*) n, round(sqrt(avg((pred - y)^2)), 1) rmse_model, round(sqrt(avg((est - y)^2)), 1) rmse_est,
  round(median(abs(pred - y)), 1) medae_model, round(median(abs(est - y)), 1) medae_est
FROM e WHERE est IS NOT NULL GROUP BY ROLLUP (src, gap) ORDER BY src NULLS LAST, gap NULLS LAST
"""
db.save_check(con, f"p4_adsblol_vs_{BASE}_holdout", Q_GAP,
              f"{BASE} Jan/Jul-2025 hold-out predictions vs the raw ADS-B off-block estimate (stand = M-021, parked = "
              "M-018), all extracted 2025 days, binned by |est − pred|.")

Q_AP = f"""
WITH o AS (SELECT mvt_id, pred FROM {OOF}),
e AS (SELECT f.airport, strftime(f.month, '%m') AS mo, f.y, o.pred, s.adsb_stand_move_s AS est
      FROM o JOIN feat_dep f USING (mvt_id) JOIN feat_dep_adsb_stand s USING (mvt_id)
      WHERE s.adsb_still_at_stand AND abs(s.adsb_stand_move_s - o.pred) <= 600)
SELECT airport, mo, count(*) n, round(median(est - y), 0) med_est_minus_y,
  round(sqrt(avg((pred - y)^2)), 1) rmse_model, round(sqrt(avg((est - y)^2)), 1) rmse_est,
  round(100*avg((abs(est - y) <= 60)::INT), 1) pct60_est
FROM e GROUP BY ROLLUP (airport, mo) ORDER BY airport NULLS LAST, mo NULLS LAST
"""
db.save_check(con, f"p4_adsblol_stand_by_airport_{BASE}", Q_AP,
              f"Rows seen stationary at the own stand with |est − pred| ≤ 600 s (pred = {BASE} hold-out), all extracted "
              "2025 days: per-airport bias and RMSE of the raw estimate vs the model.")
print(f"saved ADS-B checks ({days} days, base {BASE})")
