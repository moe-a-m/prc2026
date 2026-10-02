# Data sources

| id | name | card | status |
|---|---|---|---|
| challenge | PRC Data Challenge 2026 training / ranking / submitting parquet files | (this page, below) | in use |

No external source is in the pipeline yet (CLAUDE.md §4 ledger lists candidates).

## Challenge files
- Location: `data/raw/{training,ranking,submitting}/`, manifest `data/raw/MANIFEST.csv` (bytes + SHA256).
- Downloaded 2026-09-21 (file mtimes), i.e. **after** the 2026-09-04 ranking reissue.
  Neither ranking nor submitting hash matches the stale pre-reissue hashes
  (check: `tests/test_contracts.py::test_no_stale_raw_files`). Ranking DEP count = submitting rows = 344,841
  with identical ID sets (`reports/checks/p1_submitting_vs_ranking.md`).
- Licence: not stated by the organizers ("ask the owner"); raw files and row-level extracts are never committed.
- Bucket path: not recorded at download time — see `docs/OPEN_QUESTIONS.md`.

## Change log
- 2026-10-02: training files moved from `data/raw/` to `data/raw/training/` (no content change; hashes in manifest).

## Combined attribution block
(none yet — no external data)
