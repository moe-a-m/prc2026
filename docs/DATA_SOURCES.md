# Data sources

| id | name | card | status |
|---|---|---|---|
| challenge | PRC Data Challenge 2026 training / ranking / submitting parquet files | (this page, below) | in use |
| iem_metar | METAR, IEM ASOS archive (public domain) | [iem_metar.md](data_sources/iem_metar.md) | fetched 2026-10-02; kept (EXP-018) |
| adsblol | adsb.lol globe_history, ODbL-1.0 | [adsblol.md](data_sources/adsblol.md) | downloading since 2026-10-02 (124 days, stream-extract) |
| ourairports | OurAirports runways/airports (public domain) | [ourairports.md](data_sources/ourairports.md) | fetched 2026-10-02 |
| eurocontrol_apt | EUROCONTROL AIU airport datasets (custom terms: attribution, non-commercial, no modification; organizer-approved) | [eurocontrol_apt.md](data_sources/eurocontrol_apt.md) | fetched 2026-10-02; EXP-024 |

Candidates not yet used: see the CLAUDE.md §4 ledger.

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
- Challenge data: EUROCONTROL PRC Data Challenge 2026 (movements: airport APDF; flight data: EUROCONTROL NM).
- Weather observations: Iowa Environmental Mesonet (IEM), Iowa State University, ASOS/METAR archive,
  https://mesonet.agron.iastate.edu/ (public domain).
- Contains information from adsb.lol globe_history, which is made available here under the Open Database License
  (ODbL), https://github.com/adsblol/globe_history_2025, https://opendatacommons.org/licenses/odbl/1.0/.
- Airport/runway data: OurAirports (public domain), https://ourairports.com/data/.
- Airport performance data: Source: EUROCONTROL Aviation Intelligence Portal, https://ansperformance.eu/.
