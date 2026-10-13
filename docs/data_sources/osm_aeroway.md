# Data card: osm_aeroway

## Identity
- id: `osm_aeroway`; OpenStreetMap aeroway features via the Overpass API (https://overpass-api.de/api/interpreter)
- query (per airport ICAO, pinned snapshot): `[out:json][timeout:170][date:"2026-10-01T00:00:00Z"];
  area["aeroway"="aerodrome"]["icao"="<ICAO>"]->.a; nwr(area.a)["aeroway"~"^(parking_position|holding_position|deicing_pad|gate)$"]; out tags center;`

## Licence
- ODbL 1.0: "OpenStreetMap is open data, licensed under the Open Data Commons Open Database License (ODbL) by the
  OpenStreetMap Foundation (OSMF)." Snapshot `docs/references/licences/osm_copyright_2026-10-02.html` (read 2026-10-02).
- attribution: "© OpenStreetMap contributors" (https://www.openstreetmap.org/copyright); share-alike for derived databases.

## Challenge eligibility
- open-licensed; open-data rule (organizer, 01/10/2026).

## Coverage
- review (`docs/references/open_data_review_2026-10-02.md` §4): `parking_position` refs match 89.6–99.2% of DEP rows at 9
  airports, 57% at EDDM (A/B sub-stands); de-icing pads tagged only at EDDM/LTFM.
- need: ranking departures with a (stand, runway) pair unseen in 2025 = 0.72% overall, EDDM 4.57% (new stands 103–108)
  (`reports/checks/p4_unseen_stands_rank.md`) → low expected value as a *stand→runway geometry feature*; that use was
  deprioritised and never built.
- actual use: the stand positions are what the ADS-B off-block step needs (M-021 stand matching → M-028), so the
  final model depends on this source (see Lineage / Value).

## Retrieval
- `make fetch` (runs `scripts/fetch/osm_aeroway.py`); 10 files retrieved 2026-10-02 (504s retried); log
  `logs/fetch/osm_aeroway.log`; tool versions: see `uv.lock` / `reports/env.txt`

## Files
- `data/external/osm_aeroway/raw/<ICAO>_2026-10-01.json` in `data/external/MANIFEST.csv`

## Schema
- Overpass JSON `elements[]`: type, id, lat/lon (nodes) or center (ways), tags (aeroway, ref, name, …); `osm3s.timestamp_osm_base`

## Lineage / Quality / Value
- `raw_osm_aeroway` (`sql/00_ingest/07_raw_osm_aeroway.sql`) → `stg_stand_geo` (`sql/10_stage/05_stg_stand_geo.sql`,
  96.0% of departures matched, `reports/checks/p4_stand_geo_match.md`) → `feat_dep_adsb_stand`
  (`sql/40_adsb/04_feat_dep_adsb_stand.sql`, M-021; 150 m variant `05_feat_dep_adsb_near.sql`). Value: the stand
  positions make the M-028 ADS-B step possible (EXP-050/051/080; final form EXP-117 in the final model; see the
  adsb.lol card); 5.3% of departures with an
  ADS-B ground segment have no OSM stand position (`reports/checks/p4_adsblol_stand_gap.md`).

## Re-fetch policy
- listed files never overwritten; checksum mismatch stops the script.
- in a fresh clone (file absent) the script downloads the file again and compares it with the committed manifest
  row (`prc.fetchutil.changed_upstream`): if the bytes differ, it stops without recording them. To continue with the
  new upstream bytes, set `PRC_ACCEPT_UPSTREAM_CHANGES=1` (results may then differ from ours).
- Overpass writes the server's current database time into every response (`osm3s.timestamp_osm_base`), so
  re-downloaded raw bytes never equal the archived ones. The script therefore checks the `elements` (all that
  `sql/00_ingest/07_raw_osm_aeroway.sql` reads) against `ELEMENTS_SHA256`, the hashes of our 2026-10-02 responses.
  Checked 2026-10-13: a fresh fetch into an empty folder matched for all 10 airports.
