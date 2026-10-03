# Submissions

Each upload is logged here with its local validation score. The next version number is read from this table.
Team `motivated-engine`, bucket `prc-2026-motivated-engine`, file name `motivated-engine_vN.parquet`
(organizer acceptance e-mail). The leaderboard is a sanity check, never an objective (CLAUDE.md §9).

| version | file | date (UTC) | experiment | local Jan-25 RMSE | local Jul-25 RMSE | board score | used_pairs | notes |
|---|---|---|---|---|---|---|---|---|
| 1 | motivated-engine_v1.parquet | 2026-10-02 12:19 (uploaded by the user) | EXP-011 (final fit on all 2025, seed 42) | 372.78 | 397.32 | 347.2252 | 344841 | sha256 9b173bc1…f338 identical to local file; 62 preds clipped at 0 |
| 2 | motivated-engine_v2.parquet | 2026-10-02 18:11 (uploaded by the user) | EXP-025 (per-airport LightGBM + METAR weather, final fit on all 2025, seed 42) | 347.41 | 378.08 | 319.9019 | 344841 | sha256 e48a20d1…a117 identical to local file; 86 preds clipped at 0; rms change vs v1 213 s (mostly LIRF hedges) |
| 3 | motivated-engine_v3.parquet | 2026-10-03 (uploaded by the user) | EXP-031 (0.490 × 3-seed per-airport LightGBM + weather [EXP-025+EXP-029] + 0.508 × per-airport CatBoost + weather [EXP-028]; final fits on all 2025) | 347.72 | 361.72 | 299.0976 | 344841 | sha256 b244cd6b…8fa9 identical to local file; 40 preds clipped at 0; rms change vs v2 91 s |
