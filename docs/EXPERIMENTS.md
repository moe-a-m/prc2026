# Experiments

Protocol (CLAUDE.md §9): train on 2025 minus the held-out month, predict Jan-2025 and Jul-2025 separately.
`data` = content hash of `data/raw/MANIFEST.csv` + all `sql/**/*.sql` (12 hex); full per-run detail
(per-airport RMSE, matched/unmatched, flagged/clean, top-20 rows) in `reports/experiments/EXP-###.md`.

| ID | date | hypothesis | data | git | features / params | seed | Jan-25 | Jul-25 | combined | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| EXP-001 | 2026-10-02 | reference: global median | 64a9ec802eeb | 99ea67d | — | — | 610.5 | 753.8 | 693.5 | reference |
| EXP-002 | 2026-10-02 | reference: airport median | 64a9ec802eeb | 99ea67d | — | — | 586.6 | 723.8 | 666.1 | reference |
| EXP-003 | 2026-10-02 | reference: airport×runway median | 64a9ec802eeb | 99ea67d | — | — | 579.2 | 716.5 | 658.7 | reference |
| EXP-004 | 2026-10-02 | stand×runway median carries distance (M-005) | 64a9ec802eeb | 99ea67d | fallback ap×rwy, ap | — | 555.4 | 693.1 | 635.4 | reference |
| EXP-005 | 2026-10-02 | means beat medians under RMSE | 64a9ec802eeb | 99ea67d | — | — | 604.8 | 746.0 | 686.6 | confirmed (−7 vs EXP-001) |
| EXP-006 | 2026-10-02 | as EXP-002, mean | 64a9ec802eeb | 99ea67d | — | — | 584.7 | 715.3 | 660.2 | reference |
| EXP-007 | 2026-10-02 | as EXP-003, mean | 64a9ec802eeb | 99ea67d | — | — | 578.6 | 708.3 | 653.6 | reference |
| EXP-008 | 2026-10-02 | as EXP-004, mean | 64a9ec802eeb | 99ea67d | fallback ap×rwy, ap | — | 553.9 | 683.6 | 629.0 | best group baseline |
| EXP-009 | 2026-10-02 | MVT − AOBT_3 ≈ target (M-004) | 64a9ec802eeb | 99ea67d | fallback EXP-008 | — | 557.4 | 715.2 | 649.6 | rejected as estimator: worse than EXP-008; AOBT_3 often NM-derived |
| EXP-010 | 2026-10-02 | MVT − AOBT_3 + ap×rwy mean residual | 64a9ec802eeb | 99ea67d | fallback EXP-008 | — | 541.6 | 702.2 | 635.5 | reference; Jan best, Jul worse than EXP-008 |

Notes on the baselines: in every baseline the top 20 rows (of 344,419) carry ≈ 50% of the squared error, and NM-
unmatched rows (1.6%) have RMSE ≈ 4,000 s vs ≈ 400 s for matched rows (`reports/experiments/EXP-010.md`).
