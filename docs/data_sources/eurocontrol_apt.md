# Data card: eurocontrol_apt

## Identity
- **Not used by the final model.** Used only by rejected experiments (EXP-024 model inputs, M-017; EXP-052 level
  calibration, M-029). Fetched with `make fetch-optional`, not by `make fetch` / `make reproduce`; the SQL that reads
  these files is skipped when they are absent. Upstream rewrites the 2026 files monthly, so a re-fetch today returns different
  bytes from those archived on 2026-10-02 (see Re-fetch policy) and could not reproduce EXP-024 / EXP-052 exactly.
- id: `eurocontrol_apt`; EUROCONTROL Aviation Intelligence Unit, airport datasets (ansperformance.eu)
- index: https://ansperformance.eu/csv/ ; URL pattern `https://www.eurocontrol.int/performance/data/download/csv/{name}_{YYYY}.csv`
- files used: taxi_out_additional_time (monthly), all_pre_departure_delays (daily), atfm_slot_adherence (daily);
  also archived: airport_traffic (daily), apt_dly (daily arrival ATFM delay, .bz2 — not yet parsed)

## Licence / terms
- Not an open licence in the OSI/OKF sense. Verbatim (https://ansperformance.eu/about/disclaimer/, snapshot
  `docs/references/licences/ansperformance_disclaimer_2026-10-02.html`, read 2026-10-02): "This data is published by
  EUROCONTROL for information purposes. It may be copied in whole or in part, provided that EUROCONTROL is mentioned as
  the source and it is not used for commercial purposes (i.e. for financial gain). The information in this document may
  not be modified without prior written permission from EUROCONTROL."
- Compliance: files archived byte-for-byte (SHA256 in the manifest), never modified; features are derived in our code;
  EUROCONTROL credited as source; non-commercial research use.
- attribution: "Source: EUROCONTROL Aviation Intelligence Portal, https://ansperformance.eu/"

## Challenge eligibility (organizer = EUROCONTROL PRU)
- organizer, forum 17/09/2026, on these daily airport files and their non-commercial clause:
  "can be considered open data for the challenge".
- organizer, forum 27/09/2026 18:14 (answering a participant's question of 15:49), on using the published Jan/Jul 2026 monthly taxi-out figures as model input:
  "I already answered above: yes".
- Tension: organizer, 01/10/2026: "If no open license is present it is not open". Team decision 2026-10-02: use,
  unmodified, behind a config flag (`extra_tables: [feat_dep_ec]`). Moot for the final model, which does not use it.

## Coverage
- all 10 airports; taxi-out monthly 2025-01..2026-07; daily files 2025-01-01..2026-08-31
  (`reports/checks/p4_ec_vs_target.md`: no departure without a daily match)

## Retrieval
- `make fetch-optional` (= `uv run --frozen python scripts/fetch/eurocontrol_apt.py`), retrieved 2026-10-02
  (timestamps in the manifest); tool versions: see `uv.lock` / `reports/env.txt`

## Schema (verified with DuckDB read_csv)
- taxi_out_additional_time: YEAR, MONTH_NUM, APT_ICAO, TF, VALID_FL, NO_REF, TOTAL_REF_NB_FL, TOTAL_REF_TIME_MIN,
  TOTAL_ADD_TIME_MIN (minutes); all_pre_departure_delays: FLT_DATE, APT_ICAO, FLT_DEP_1, FLT_DEP_IFR_2, DLY_ALL_PRE_2 (min);
  atfm_slot_adherence: FLT_DATE, APT_ICAO, FLT_DEP_1, FLT_DEP_REG_1, FLT_DEP_OUT_EARLY_1, FLT_DEP_IN_1, FLT_DEP_OUT_LATE_1
- method of the monthly indicator: EUROCONTROL, Additional taxi-out time indicator document, Ed. 01.00 (2023):
  reference = P10 per stand×runway group over 12 months; flights de-iced after off-block and > 120 min excluded

## Lineage
- `raw_ec_taxi`, `raw_ec_predep`, `raw_ec_slot` (`sql/00_ingest/05_raw_eurocontrol.sql`) → `feat_dep_ec`
  (`sql/30_features/07_feat_dep_ec.sql`; joins on airport × UTC month and airport × UTC date of take-off)

## Quality
- 2025 airport-month correlation of EC mean taxi-out with our target mean (y ≤ 2 h): 0.98 (`p4_ec_vs_target`).
  Winter gap EC < ours at EDDM/LFPG/LSZH consistent with the de-icing exclusion.

## Value
- EXP-024: rejected as model inputs (paired vs EXP-018, non-LIRF y≤3h +2.3 Jan / −1.7 Jul; level shifts between
  2025 and 2026 a 2025-trained model cannot use). Kept only as a documentation/consistency check (`p4_ec_vs_target`).

## Re-fetch policy
- a file already present and listed is never overwritten; a checksum mismatch stops the script.
- in a fresh clone (file absent) the script downloads the file again and compares it with the committed manifest
  row (`prc.fetchutil.changed_upstream`): if the bytes differ, it stops without recording them. To continue with the
  new upstream bytes, set `PRC_ACCEPT_UPSTREAM_CHANGES=1` (results may then differ from ours). Upstream rewrites the 2026 files monthly,
  so expect this for them; the final model does not use this source.
