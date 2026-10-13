# Data card: ourairports

## Identity
- id: `ourairports`; OurAirports open data (David Megginson); https://ourairports.com/data/
- files: https://raw.githubusercontent.com/davidmegginson/ourairports-data/ac08c301fd36bc1b9ea2bf4acfd4fef691360b5c/airports.csv, .../runways.csv (pinned commit; retrieved 2026-10-02 from https://davidmegginson.github.io/ourairports-data/, same bytes)

## Licence
- Public domain: "All data is released to the Public Domain, and comes with no guarantee of accuracy or fitness for use."
  Snapshot: `docs/references/licences/ourairports_data_page_2026-10-02.html` (read 2026-10-02). Credit appreciated, not required.

## Challenge eligibility
- open (public domain); open-data rule (organizer, 01/10/2026: "anything you think that helps, use it!").

## Coverage
- 40 runway rows for the 10 airports; challenge runway designators present (review §3).

## Retrieval
- `make fetch` (runs `scripts/fetch/ourairports.py`); retrieved 2026-10-02 13:42 UTC. Updated nightly upstream →
  pinned by SHA256. Tool versions: see `uv.lock` / `reports/env.txt`.

## Files
- `data/external/ourairports/raw/{airports,runways}.csv` in `data/external/MANIFEST.csv`

## Schema
- runways.csv: airport_ident, le_/he_ident, le_/he_latitude_deg, le_/he_longitude_deg, le_/he_heading_degT, closed, …

## Lineage / Value
- `runways.csv`: the extent of the open runways' thresholds (`le_`/`he_` latitude/longitude) plus a 2 km margin gives
  the box around each airport inside which adsb.lol points are kept (`scripts/fetch/adsblol.py: boxes()`).
- `airports.csv`: field elevation → `ref_airport_geo` (`sql/00_ingest/06_raw_ourairports.sql`,
  `sql/10_stage/04_ref_airport_geo.sql`), used to detect ADS-B take-offs (altitude above the field,
  `sql/40_adsb/02_adsb_takeoffs.sql`, M-018).
- Used by the final model only indirectly, through the ADS-B step M-028. Stand→runway distance features from runway
  thresholds were planned but never built.

## Re-fetch policy
- an existing listed file is never overwritten; checksum mismatch stops the script.
- the download is pinned to upstream git commit `ac08c30` of `github.com/davidmegginson/ourairports-data`
  (2026-10-02 01:53 UTC), whose `airports.csv` and `runways.csv` have exactly the SHA256 in the manifest (checked
  2026-10-13 by a fresh fetch into an empty folder), so a fresh clone gets the identical files although upstream
  updates them nightly. A re-downloaded file with other bytes would stop the script (`prc.fetchutil.changed_upstream`).
