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
- measured per airport-month: `reports/checks/p4_adsblol_coverage.md` (to be produced after extraction)
- known weak coverage (review): LTFM ~none, LFPG thin

## Retrieval
- script: `scripts/fetch/adsblol.py download` and `... extract` (two background processes); helper `src/prc/fetchutil.py`
- 4 parallel HTTP range requests of 64 MB; measured link ~1.8–2.4 MB/s → ~28 min per day
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
- extract parquet → `raw_adsb` → `stg_adsb` → per-departure features `feat_dep_adsb` (to be written)

## Quality
- SHA256 of every part vs GitHub digest (mismatch → file removed, run stops); unreadable trace members counted per day
  in the extract log; coverage per airport-month and 2025-vs-2026 drift checks (a participant 27/09: receiver network changed
  between years — features about *where* an aircraft was heard may not transfer)

## Value
- to be measured (EXP-0xx) on Jan/Jul 2025 hold-outs

## Re-fetch policy
- a part already listed with a matching digest is not downloaded again; a mismatch stops the run.
