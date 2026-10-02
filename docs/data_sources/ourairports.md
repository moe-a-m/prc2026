# Data card: ourairports

## Identity
- id: `ourairports`; OurAirports open data (David Megginson); https://ourairports.com/data/
- files: https://davidmegginson.github.io/ourairports-data/airports.csv, .../runways.csv

## Licence
- Public domain: "All data is released to the Public Domain, and comes with no guarantee of accuracy or fitness for use."
  Snapshot: `docs/references/licences/ourairports_data_page_2026-10-02.html` (read 2026-10-02). Credit appreciated, not required.

## Challenge eligibility
- open (public domain); open-data rule (organizer, 01/10/2026: "anything you think that helps, use it!").

## Coverage
- 40 runway rows for the 10 airports; challenge runway designators present (review §3).

## Retrieval
- `uv run python scripts/fetch/ourairports.py`; retrieved 2026-10-02 13:42 UTC. Updated nightly upstream → pinned by SHA256.

## Files
- `data/external/ourairports/raw/{airports,runways}.csv` in `data/external/MANIFEST.csv`

## Schema
- runways.csv: airport_ident, le_/he_ident, le_/he_latitude_deg, le_/he_longitude_deg, le_/he_heading_degT, closed, …

## Lineage / Value
- airport boxes for the adsb.lol extraction (`scripts/fetch/adsblol.py: boxes()`); runway thresholds for stand→runway
  distance features (planned).

## Re-fetch policy
- an existing listed file is never overwritten; checksum mismatch stops the script.
