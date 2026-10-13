# Data card: iem_metar

## Identity
- id: `iem_metar`
- name / provider: METAR reports, ASOS/AWOS archive of the Iowa Environmental Mesonet (IEM), Iowa State University
- landing page: https://mesonet.agron.iastate.edu/request/download.phtml
- exact endpoint: `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py` with
  `station=<ICAO>&data=all&tz=Etc/UTC&format=onlycomma&latlon=yes&elev=yes&missing=M&trace=T&sts=<ISO>&ets=<ISO>`
  (API documentation snapshot: `docs/references/iem_asos_api_help_2026-10-02.html`)

## Licence
- Public domain: "The materials found on this website are in the public domain and may be used freely by anyone for
  any lawful purpose. Attributing the Iowa Environmental Mesonet of Iowa State University would be appreciated."
- verbatim snapshot: `docs/references/licences/iem_disclaimer_2026-10-02.txt` (+ `.html`), read 2026-10-02
- attribution string: "Weather observations: Iowa Environmental Mesonet (IEM), Iowa State University,
  ASOS/METAR archive, https://mesonet.agron.iastate.edu/"

## Challenge eligibility
- organizer, forum 17/09/2026 and 26/09/2026: open-licensed data may be used if declared.
  Public domain satisfies the prize rule "openly accessible, open-licensed and documented".

## Coverage
- requested: stations EDDF EDDM EGLL EHAM LEBL LEMD LFPG LIRF LSZH LTFM; periods 2024-12-30 → 2026-01-03 and
  2025-12-30 → 2026-08-03 (UTC, ≥ 1 day margin around 2025 and Jan/Jul 2026)
- measured per airport-month: `reports/checks/p4_metar_coverage.md`

## Retrieval
- script: `scripts/fetch/iem_metar.py`; run by `make fetch` (with OurAirports and OSM aeroway)
- one request per station × period, 5 s between requests (service throttles to 1 request/s per IP)
- retrieved: 2026-10-02 (timestamps per file in the manifest); requests 2.34.2, Python 3.14.7 (log `logs/fetch/iem_metar.log`)

## Files
- 20 CSV files under `data/external/iem_metar/raw/`, listed in `data/external/MANIFEST.csv` (path, bytes, SHA256, retrieved_at)

## Schema
- header (verified on EDDF file): station, valid, lon, lat, elevation, tmpf, dwpf, relh, drct, sknt, p01i, alti, mslp,
  vsby, gust, skyc1-4, skyl1-4, wxcodes, ice_accretion_1hr/3hr/6hr, peak_wind_gust, peak_wind_drct, peak_wind_time,
  feel, metar, snowdepth
- units (IEM download page, snapshot `docs/references/iem_asos_download_page_2026-10-02.html`): temperature °F,
  wind/gust knots, visibility statute miles, cloud height ft, altimeter inches Hg; `valid` in the requested tz (UTC)
- missing marker `M`; visibility ≥ 10 km is reported as 6.21 mi (9999 in the METAR)
- no SPECI/COR reports found in the archive for EDDF (`reports/checks/p4_metar_report_types.md`)

## Lineage
- `raw_metar` (`sql/00_ingest/04_raw_metar.sql`, all text) → `stg_metar` (`sql/10_stage/03_stg_metar.sql`, SI units,
  one row per station/time, weather flags) → `feat_dep_wx` (`sql/30_features/04_feat_dep_wx.sql`)

## Quality
- uniqueness check `sql/90_checks/07_metar_unique.sql`; coverage/cadence `reports/checks/p4_metar_coverage.md`;
  weather-flag parser vs raw METAR text on a random sample `reports/checks/p4_metar_parser_sample.md`;
  2025 vs 2026 drift `reports/checks/p4_metar_drift.md`

## Value
- features: `wx_*` and `wx3h_*` in `feat_dep_wx`. Introduced in EXP-018 (one global LightGBM: non-LIRF y≤3h −2.0 Jan /
  −2.2 Jul); inside per-airport models in EXP-025 (−5.1 / −4.0 vs EXP-022), whose inputs are the base of every later
  model, including the final base learners EXP-103–112 (`configs/ablations/EXP-025_per_airport_weather.yaml` →
  `configs/m030_lgb.yaml` / `configs/cat_pa_wx.yaml` → `configs/ablations/EXP-103_recent_lgb.yaml` / `EXP-104_recent_cat.yaml`).
  **Used by the final model.**

## Re-fetch policy
- the script skips files whose SHA256 matches the manifest and stops on a mismatch; it never overwrites silently.
- in a fresh clone (file absent) the script downloads the file again and compares it with the committed manifest
  row (`prc.fetchutil.changed_upstream`): if the bytes differ, it stops without recording them. To continue with the
  new upstream bytes, set `PRC_ACCEPT_UPSTREAM_CHANGES=1` (results may then differ from ours).
- checked 2026-10-13: a fresh fetch of all 20 files into an empty folder gave bytes identical to the manifest.
- Redistribution: public domain, so the raw files may be archived publicly (e.g. Zenodo); not done so far.
