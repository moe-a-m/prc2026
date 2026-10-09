# Data card: adsblol

## Identity
- id: `adsblol`; name: adsb.lol `globe_history` (readsb trace archive); provider: adsb.lol community
- landing pages: https://github.com/adsblol/globe_history_2025, https://github.com/adsblol/globe_history_2026
- release asset pattern: `https://github.com/adsblol/globe_history_{YYYY}/releases/download/{tag}/{tag}.tar.{aa,ab,ac}`
  with `tag = v{YYYY.MM.DD}-planes-readsb-{prod|staging|...}-0`; release chosen per day by upstream
  `PREFERRED_RELEASES.txt` (snapshotted in `data/external/adsblol/meta/`, checksummed in the manifest)

## Licence
- Open Database License 1.0 (repo README: "This database is made available under the Open Database License:
  http://opendatacommons.org/licenses/odbl/1.0/"; GitHub reports ODbL-1.0). Feeder contributions CC0 (release README).
- verbatim snapshot and obligations: `docs/references/open_data_review_2026-10-02.md` §1 (licence text quotes, read 2026-10-02)
- attribution (ODbL 4.3, for predictions/paper): "Contains information from adsb.lol globe_history, which is made
  available here under the Open Database License (ODbL)." with links to the repos and the licence.
- share-alike (ODbL 4.4): if the extracted point tables or per-flight ADS-B features are ever published, they must be
  published under ODbL (not GPL). The GPL code that builds them satisfies 4.6(b). Internal use is not public use.

## Challenge eligibility
- organizer, 17/09/2026 (forum export item 3): "if their license applies as open data, ok"; 19/09/2026 (item 18):
  "if you can find open trajectory data with good ground coverage and extract off-block times, we are ok".

## Coverage
- requested: all days of Jan + Jul 2025 and Jan + Jul 2026 (124 days), no margin days (a departure pushing back before
  00:00 UTC on the 1st is only partially covered — documented limitation)
- measured per airport-month (all 124 days, 31 per month): `reports/checks/p4_adsblol_coverage.md`, run 2026-10-05.
  Share of departures with a ground (taxi) segment, Jan-25 / Jul-25 / Jan-26 / Jul-26:

  | airport | ground % | seen stationary at own OSM stand % (used by M-028) |
  |---|---|---|
  | EDDF | 79 / 82 / 60 / 62 | 6 / 8 / 3 / 2 |
  | EDDM | 97 / 36 / 95 / 97 | 39 / 12 / 39 / 31 |
  | EGLL | 29 / 10 / 64 / 97 | 4 / 0.5 / 12 / 43 |
  | EHAM | 97 / 97 / 95 / 97 | 35 / 50 / 45 / 51 |
  | LEBL | 97 / 82 / 88 / 92 | 10 / 15 / 15 / 18 |
  | LEMD | 0 / 4 / 95 / 45 | 0 / 0.4 / 13 / 7 |
  | LFPG | 0 / 6 / 8 / 8 | 0 / 0 / 0 / 0 |
  | LIRF | 0 / 81 / 63 / 0.1 | 0 / 3 / 5 / 0 |
  | LSZH | 80 / 77 / 86 / 89 | 26 / 21 / 30 / 9 |
  | LTFM | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

- **added 2026-10-08 (final phase):** Feb + Jun 2026 (scored in the final phase, organizer e-mail 2026-10-08) and every
  remaining 2025 day (Feb–Jun, Aug–Dec; full-year hold-out check) — 361 days, `adsblol.days_more()`; 485 days in all.
  2025-12-31 is listed in the globe_history_2026 PREFERRED_RELEASES file, not the 2025 one. Measured coverage per
  airport-month for all 485 days: `reports/checks/final_phase_adsb_coverage.md` (Modal run final-drift-1, 2026-10-09).
  Share of departures seen stationary at their own OSM stand (M-028 "still" source), Feb-25 / Feb-26 / Jun-25 / Jun-26:
  EDDF 8.5 / 0.4 / 7.3 / 2.5, EDDM 35.5 / 39.5 / 20.5 / 26.5, EGLL 4.2 / 9.8 / 0.3 / 39.9, EHAM 34.1 / 42.7 / 44.9 / 44.3,
  LEBL 10.0 / 14.1 / 22.6 / 18.3, LEMD 0.0 / 11.9 / 11.3 / 10.8, LFPG 0 / 0 / 0 / 0.1, LIRF 0.0 / 4.2 / 3.5 / 0.0,
  LSZH 25.4 / 30.9 / 20.9 / 8.2, LTFM 0 throughout. The receiver-network drift seen for Jan/Jul repeats (EGLL and
  LEMD much better covered in 2026, LIRF none in Jun-26, EDDF ground segments for only 12 % of Feb-26 departures);
  M-028 acts only where the aircraft is seen, so the drift changes how many rows it touches, not how it acts.

  Strong 2025→2026 drift at EDDM, EGLL, LEMD, LIRF → the tracks are used only through the agreement-gated M-028 step
  (it acts only where the aircraft is seen; elsewhere predictions are unchanged), never as raw model inputs.

## Retrieval
- script: `scripts/fetch/adsblol.py download` and `... extract` (two background processes); helper `src/prc/fetchutil.py`
- 4 parallel HTTP range requests of 64 MB; measured 0.07–5.7 MB/s (typically 2–5 MB/s) → 15–40 min per day
- retrieved 2026-10-02 … 2026-10-05: 384 parts, 388.5 GB, all SHA256 equal to the GitHub digests. Interruptions: a local
  DNS outage (2026-10-04 05:35–11:54, resumed automatically), a reboot (2026-10-04 15:42, relaunched, partial file
  resumed) and a GitHub API timeout that stopped the process (fixed in 98b3b94: the API lookup now retries)
- **2026-10-08, 361 added days on Modal** (`modal run --detach scripts/modal/app.py::fetch_adsblol --run-id adsb-more-1`):
  one container per day (1 CPU, 4 GiB, ≤ 20 at a time) runs the same `adsblol.py` functions — download to the
  container disk with 8 range requests, SHA256 vs GitHub digest, extraction, raw parts deleted. ~5 min per day;
  retrieved 2026-10-08 12:22–16:07 UTC: 724 parts, 1,136.4 GB, all digests equal; 361 extracts, 3.8 GB. Each container
  writes its manifest rows to `external/adsblol/manifest_parts/<day>.csv` on the volume; locally
  `modal volume get … extract|manifest_parts` then `adsblol.py merge` (checks every extract's SHA256 against its row,
  refuses to change an existing row). The 124 earlier days on the volume were byte-identical to the local copies.
  Asset lists for the added days: `GITHUB_TOKEN=$(gh auth token) adsblol.py assets` (authenticated: 5,000 req/h).
- GitHub API (unauthenticated, ~1 call/day) for asset sizes and SHA256 digests, cached in `data/external/adsblol/meta/`
- logs: `logs/fetch/adsblol_download.log`, `logs/fetch/adsblol_extract.log`

## Files
- raw parts: listed in `data/external/MANIFEST.csv` (path, bytes, SHA256 = GitHub digest, retrieved_at) and
  **deleted after extraction** (388 GB would not fit); the manifest is the record needed to re-fetch identical bytes
- extracts: `data/external/adsblol/extract/<YYYY-MM-DD>.parquet` (zstd), each listed in the manifest (`adsblol_extract`)

## Schema (extract)
- airport, icao24, reg, actype, callsign (latest `flight` in the trace details at/before the point), ts (UTC epoch s),
  lat, lon, alt_ft (NaN when on ground), on_ground (`alt == "ground"`), gs_kt, track_deg, new_leg (flags bit 2), src
- source format: readsb trace JSON, https://github.com/wiedehopf/readsb/blob/dev/README-json.md#trace-jsons
- filter: inside the airport box (OurAirports runway-threshold extent + 2 km) and (on ground or alt ≤ 3000 ft)

## Lineage
- extract parquet → `stg_adsb` (`sql/40_adsb/01_stg_adsb.sql`) → `adsb_seg`, `adsb_takeoff` (`02_adsb_takeoffs.sql`)
  → `feat_dep_adsb` (`03_feat_dep_adsb.sql`, M-018) and, with OSM stand positions `stg_stand_geo`,
  `feat_dep_adsb_stand` (`04_feat_dep_adsb_stand.sql`, M-021) → `prc.models.adsb_stack` (M-028); 150 m variant
  `feat_dep_adsb_near` (`05_feat_dep_adsb_near.sql`, M-028 source `near`); `feat_dep_adsb_inputs`
  (`06_feat_dep_adsb_inputs.sql`, M-034, tested as model inputs, not in the final recipe)
- copies: the extracts are also stored on the team's private Modal volume for cloud runs (internal use, not a
  publication under ODbL 4.4)

## Quality
- SHA256 of every part vs GitHub digest (mismatch → file removed, run stops); unreadable trace members counted per day
  in the extract log; coverage per airport-month and 2025-vs-2026 drift checks (a participant 27/09: receiver network changed
  between years — features about *where* an aircraft was heard may not transfer)

## Value
- EXP-042 (10 days) and EXP-050 (all days): kept — gated shrinkage toward the stand off-block estimate, −2.0 on both
  2025 hold-out months; v5 board 283.18 (v4 287.50). Rejected: "last stationary point" variant
  (`p4_adsblol_stand_last_vs_v4.md`), "seen parked" second source (`p4_adsblol_vs_EXP-045_holdout.md`).
- EXP-051 (second source, seen at the stand only while moving): −1.4 / −1.3, v6 board 279.83. EXP-080 (third source,
  within 150 m): −0.44 / −0.44, v8 board 278.54. Final v11 (EXP-118) uses the three sources; the step changes 106,843
  ranking rows. Robustness: `m028_sensitivity.md` (radius / gate scan, 2025 → 2026 gap transfer).
- EXP-119–134 (M-034, estimates as model inputs): every base model better, but the same information as the
  post-step; final −0.40 / +0.56 → not adopted. Evidence that ADS-B resolves NM/airport disagreements:
  `m034_adsb_vs_nm.md` (median error 32–45 s vs NM 1,259 s where NM is > 15 min off).

## Re-fetch policy
- a part already listed with a matching digest is not downloaded again; a mismatch stops the run.
