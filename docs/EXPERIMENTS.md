# Experiments

Protocol (CLAUDE.md §9): train on 2025 minus the held-out month, predict Jan-2025 and Jul-2025 separately.
`data` = hash of raw-file identities (path + SHA256) + all `sql/**/*.sql` (12 hex; `prc.validate.data_version`).
Until commit after d97420b the hash covered the whole manifest file; `64a9ec802eeb` (old definition) and
`53dfd848e02d` (new definition) denote the same inputs; full per-run detail
(per-airport RMSE, matched/unmatched, flagged/clean, top-20 rows) in `reports/experiments/EXP-###.md`.

| ID | date | hypothesis | data | git | features / params | seed | Jan-25 | Jul-25 | combined | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| EXP-001 | 2026-10-02 | reference: global median | 64a9ec802eeb | 054df8c | — | — | 610.5 | 753.8 | 693.5 | reference |
| EXP-002 | 2026-10-02 | reference: airport median | 64a9ec802eeb | 054df8c | — | — | 586.6 | 723.8 | 666.1 | reference |
| EXP-003 | 2026-10-02 | reference: airport×runway median | 64a9ec802eeb | 054df8c | — | — | 579.2 | 716.5 | 658.7 | reference |
| EXP-004 | 2026-10-02 | stand×runway median carries distance (M-005) | 64a9ec802eeb | 054df8c | fallback ap×rwy, ap | — | 555.4 | 693.1 | 635.4 | reference |
| EXP-005 | 2026-10-02 | means beat medians under RMSE | 64a9ec802eeb | 054df8c | — | — | 604.8 | 746.0 | 686.6 | confirmed (−7 vs EXP-001) |
| EXP-006 | 2026-10-02 | as EXP-002, mean | 64a9ec802eeb | 054df8c | — | — | 584.7 | 715.3 | 660.2 | reference |
| EXP-007 | 2026-10-02 | as EXP-003, mean | 64a9ec802eeb | 054df8c | — | — | 578.6 | 708.3 | 653.6 | reference |
| EXP-008 | 2026-10-02 | as EXP-004, mean | 64a9ec802eeb | 054df8c | fallback ap×rwy, ap | — | 553.9 | 683.6 | 629.0 | best group baseline |
| EXP-009 | 2026-10-02 | MVT − AOBT_3 ≈ target (M-004) | 64a9ec802eeb | 054df8c | fallback EXP-008 | — | 557.4 | 715.2 | 649.6 | rejected as estimator: worse than EXP-008; AOBT_3 often NM-derived |
| EXP-010 | 2026-10-02 | MVT − AOBT_3 + ap×rwy mean residual | 64a9ec802eeb | 054df8c | fallback EXP-008 | — | 541.6 | 702.2 | 635.5 | reference; Jan best, Jul worse than EXP-008 |
| EXP-011 | 2026-10-02 | GBM on challenge data with all P3 families (M-004…M-011) beats baselines | 64a9ec802eeb | d97420b | configs/gbm.yaml 9d3708f71e72; LGBM L2, lr .05, 1500 rounds, 255 leaves; 41 numeric + 13 cat + 6 OOF TE | 42 | 372.78 | 397.32 | 386.56 | kept (−249 vs EXP-010). y≤3h rows: 224.2 / 320.7. Top-2 rows = 48% of Jan sq. err. Seed spread not yet measured |

Notes on the baselines: in every baseline the top 20 rows (of 344,419) carry ≈ 50% of the squared error, and NM-
unmatched rows (1.6%) have RMSE ≈ 4,000 s vs ≈ 400 s for matched rows (`reports/experiments/EXP-010.md`).

Notes on EXP-011: the model learned the LIRF schedule-echo pattern and hedges on it (predicts 10k–67k s on
NM-unmatched LIRF flights that left >3 h late). Remaining top errors: two LFPG Jan rows whose block date lies
~23 h before schedule (84,240 s, 58,206 s) with no detectable signal; LIRF unmatched rows where the echo did
not happen (hedge cost). `reports/experiments/EXP-011.md`.
