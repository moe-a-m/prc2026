-- M-031 data contract: every 2025 departure with an NM LOBT has its airport off-block within ±3606 s of LOBT
-- (take-off − LOBT − taxi-out = off-block − LOBT). reports/checks/lobt_window_train.md.
SELECT mvt_id, airport, d_lobt - y AS block_minus_lobt_s FROM feat_dep
WHERE ds = 'train' AND d_lobt IS NOT NULL AND abs(d_lobt - y) > 3606;
