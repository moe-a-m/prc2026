# Data sources

One row per source; each external source has a data card with licence snapshot, retrieval, schema, lineage and
quality checks. Every raw file is listed with its SHA256 in `data/raw/MANIFEST.csv` (challenge files) or
`data/external/MANIFEST.csv` (external files); a fetch stops on a checksum mismatch instead of overwriting.

| id | name | card | used by final model | fetch command | status |
|---|---|---|---|---|---|
| challenge | PRC Data Challenge 2026 training / ranking / submitting parquet files | (this page, below) | yes — all training and prediction inputs | `make download` (needs the bucket keys in `.env`; see README) | in use |
| iem_metar | METAR, IEM ASOS archive (public domain) | [iem_metar.md](data_sources/iem_metar.md) | yes — weather inputs `wx_*` / `wx3h_*` of both base learners | `make fetch` | fetched 2026-10-02; introduced in EXP-018 (one global LightGBM); per-airport models + weather in EXP-025, the base configuration of every later model incl. the final one (EXP-103–112) |
| adsblol | adsb.lol globe_history, ODbL-1.0 | [adsblol.md](data_sources/adsblol.md) | yes — ADS-B stand off-block estimates in the post-processing step M-028 (EXP-117); not model inputs | `make fetch-adsblol ADSB_DAYS=final` (default; Jan, Feb, Jun, Jul 2026, needed by `make predict`), `ADSB_DAYS=janjul` (`make validate`), `ADSB_DAYS=all` (`make validate-fullyear`) | complete 2026-10-05 (124 days, 388.5 GB streamed, 1.2 GB extracts); extended 2026-10-08 on Modal to all of 2025 + Feb/Jun 2026 (485 days, +1,136 GB streamed, 5.1 GB extracts); kept via M-028 (EXP-050, final form EXP-117) |
| ourairports | OurAirports runways/airports (public domain) | [ourairports.md](data_sources/ourairports.md) | yes, indirectly — runway thresholds define the adsb.lol extraction boxes; field elevation for ADS-B take-off detection | `make fetch` | fetched 2026-10-02 |
| osm_aeroway | OpenStreetMap aeroway features (ODbL), date-pinned Overpass | [osm_aeroway.md](data_sources/osm_aeroway.md) | yes — stand coordinates that the ADS-B step M-028 needs (M-021) | `make fetch` | fetched 2026-10-02 |
| eurocontrol_apt | EUROCONTROL AIU airport datasets (custom terms: attribution, non-commercial, no modification; organizer-approved) | [eurocontrol_apt.md](data_sources/eurocontrol_apt.md) | no — used only by rejected experiments (EXP-024 inputs, EXP-052 level calibration); its SQL is skipped when the files are absent | `make fetch-optional` | fetched 2026-10-02; rejected (EXP-024, EXP-052) |

No other external source enters the pipeline. Candidate sources that were considered (e.g. ERA5, X-Plane apt.dat)
or ruled out (NOAA ISD: redistribution restricted; OpenSky state vectors) are listed with their basis in the
external-data ledger of `CLAUDE.md`, which holds the development working rules of this repo.

"Modal" (here and in the cards) is the cloud container service used for long runs (`scripts/modal/`); run IDs such
as adsb-more-1 are labels of those runs, logs not in the repo.

## Challenge files
- Location: `data/raw/{training,ranking,submitting}/`, manifest `data/raw/MANIFEST.csv` (bytes + SHA256).
- Downloaded 2026-09-21 (file mtimes), i.e. **after** the 2026-09-04 ranking reissue.
  Neither ranking nor submitting hash matches the stale pre-reissue hashes
  (check: `tests/test_contracts.py::test_no_stale_raw_files`). Ranking DEP count = submitting rows = 344,841
  with identical ID sets (`reports/checks/p1_submitting_vs_ranking.md`).
- Licence: not stated by the organizers ("ask the owner"); raw files and row-level extracts are never committed.
- Cloud copy (2026-10-05, team decision): the raw files are also stored on the team's **private** Modal volume
  `prc2026-data` for optional cloud runs (`scripts/modal/`); checksums re-verified there (`verify-raw: 14 files, 0 problems`).
  Not public, not redistributed.
- Bucket paths: recorded per file in `data/raw/MANIFEST.csv` (`dc26:prc-2026-datasets/…`).

## Change log
- 2026-10-13: `make fetch` fetches only the sources the final model uses (IEM METAR, OurAirports, OSM aeroway).
  EUROCONTROL AIU files moved to `make fetch-optional`: they serve only rejected experiments, and upstream rewrites
  the 2026 files monthly, so a fresh fetch no longer returns the archived bytes. New `make fetch-adsblol
  ADSB_DAYS=final|janjul|all` fetches the adsb.lol day sets locally (see the adsb.lol card).
- 2026-10-13: a fetch in a fresh clone now stops when a re-downloaded file differs from the committed manifest row
  (before, it replaced the row); override `PRC_ACCEPT_UPSTREAM_CHANGES=1`. OurAirports is pinned to upstream commit
  `ac08c30`, which holds the archived bytes.
- 2026-10-08: final phase — `final_ranking.parquet` / `final_submitting.parquet` added (bucket upload 11:04 UTC;
  manifest 16 files; `reports/checks/final_phase_files.md`); the pipeline reads them; the public-phase files stay
  listed. adsb.lol extended by 361 days (Modal, `scripts/modal/app.py::fetch_adsblol`).
- 2026-10-05: adsb.lol archive complete; challenge + external files copied to the private Modal volume.
- 2026-10-02: training files moved from `data/raw/` to `data/raw/training/` (no content change; hashes in manifest).

## Combined attribution block
- Challenge data: EUROCONTROL PRC Data Challenge 2026 (movements: airport APDF; flight data: EUROCONTROL NM).
- Weather observations: Iowa Environmental Mesonet (IEM), Iowa State University, ASOS/METAR archive,
  https://mesonet.agron.iastate.edu/ (public domain).
- Contains information from adsb.lol globe_history, which is made available here under the Open Database License
  (ODbL), https://github.com/adsblol/globe_history_2025, https://opendatacommons.org/licenses/odbl/1.0/.
- Airport/runway data: OurAirports (public domain), https://ourairports.com/data/.
- © OpenStreetMap contributors (ODbL) — stand coordinates (M-021).
- Airport performance data: Source: EUROCONTROL Aviation Intelligence Portal, https://ansperformance.eu/.
