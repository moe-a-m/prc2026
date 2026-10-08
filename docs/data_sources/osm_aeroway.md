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
  (`reports/checks/p4_unseen_stands_rank.md`) → low expected value; deprioritised.

## Retrieval
- `uv run python scripts/fetch/osm_aeroway.py`; 10 files retrieved 2026-10-02 (504s retried); log `logs/fetch/osm_aeroway.log`

## Files
- `data/external/osm_aeroway/raw/<ICAO>_2026-10-01.json` in `data/external/MANIFEST.csv`

## Schema
- Overpass JSON `elements[]`: type, id, lat/lon (nodes) or center (ways), tags (aeroway, ref, name, …); `osm3s.timestamp_osm_base`

## Lineage / Quality / Value
- `raw_osm_aeroway` (`sql/00_ingest/07_raw_osm_aeroway.sql`) → `stg_stand_geo` (`sql/10_stage/05_stg_stand_geo.sql`,
  96.0% of departures matched, `reports/checks/p4_stand_geo_match.md`) → `feat_dep_adsb_stand`
  (`sql/40_adsb/04_feat_dep_adsb_stand.sql`, M-021; 150 m variant `05_feat_dep_adsb_near.sql`). Value: the stand
  positions make the M-028 ADS-B step possible (EXP-050/051/080, see the adsb.lol card); 5.3% of departures with an
  ADS-B ground segment have no OSM stand position (`reports/checks/p4_adsblol_stand_gap.md`).

## Re-fetch policy
- listed files never overwritten; checksum mismatch stops the script.
