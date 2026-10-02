# Experiments

Protocol (CLAUDE.md §9): train on 2025 minus the held-out month, predict Jan-2025 and Jul-2025 separately.
`data` = content hash of `data/raw/MANIFEST.csv` + all `sql/**/*.sql` (12 hex); full per-run detail
(per-airport RMSE, matched/unmatched, flagged/clean, top-20 rows) in `reports/experiments/EXP-###.md`.

| ID | date | hypothesis | data | git | features / params | seed | Jan-25 | Jul-25 | combined | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
