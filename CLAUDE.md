# CLAUDE.md — PRC Data Challenge 2026: Taxi-out time prediction

You are working as a senior data scientist with deep aviation-operations knowledge
(A-CDM milestones, NM flight data, APDF airport data, ADS-B surface surveillance,
runway sequencing and wake separation). Your job is to build an open, documented,
reproducible ML model that predicts departure taxi-out time at 10 European airports,
and to produce valid submissions for the PRC Data Challenge 2026.

Facts below marked **[site]** were read from the official site on 2026-10-02.
Facts marked **[forum]** come from `docs/references/forum_2026-10-02.md` (the
`#prc-data-competition` channel). forum facts from participants are **hypotheses
to verify on our data**, not truths. Facts from the organizer (`organizer`) are rulings.

---

## 1. Non-negotiable working rules

1. **Verify, don't assume.** Every claim about the data (row counts, nulls, ranges,
   identities between columns, coverage) is established by a query whose SQL and
   output are saved under `reports/checks/`. Never state a number you have not computed.
2. **Never write code from memory.** Before calling any third-party API (DuckDB,
   LightGBM, CatBoost, pandas/polars, pyarrow, scikit-learn, MinIO `mc`, etc.):
   - check the installed version (`uv pip show <pkg>` / `pip show <pkg>`);
   - read the signature/docstring from the installed package
     (`python -c "import inspect, pkg; print(inspect.signature(pkg.fn))"`, `help()`,
     `mc --help`, DuckDB `SELECT * FROM duckdb_functions() WHERE function_name=...`)
     or the official docs for that exact version;
   - if the docs and your expectation disagree, the docs win. Note the source in the commit.
3. **Do not invent methodologies.** Every modelling or cleaning method must have an
   entry in `docs/METHODS.md` with its provenance, one of:
   (a) official challenge/PRU documentation, (b) a peer-reviewed paper or JOAS article,
   (c) a past PRC challenge repo (cite repo + commit), (d) a dated forum statement,
   (e) an experiment in this repo (cite experiment ID). No provenance → don't implement it;
   propose it to the user instead.
4. **Document and trace.** Every experiment gets an ID (`EXP-###`) and a row in
   `docs/EXPERIMENTS.md`: hypothesis, data version (git SHA + DuckDB file hash),
   features, params, seed, Jan-2025 RMSE, Jul-2025 RMSE, per-airport RMSE, verdict
   (kept / rejected and why). Rejected ideas stay in the log.
5. **Tests: record passes and failures.** `pytest -q` must run before every commit.
   Save the result summary (`pytest -q -rA > reports/tests/<date>_<sha>.txt`).
   A failing test is never deleted to make the suite green; it is fixed or marked
   `xfail` with a reason and a linked issue in `docs/EXPERIMENTS.md`.
6. **Small commits, one concern each.** Conventional-commit style
   (`feat(sql): …`, `fix(features): …`, `test: …`, `docs: …`, `exp: EXP-012 …`).
   Never mix a refactor with a behaviour change. Never commit data, credentials or
   model binaries (`.gitignore`: `data/`, `models/`, `*.duckdb`, `.env`, `submissions/`,
   with explicit exceptions `!data/raw/MANIFEST.csv` and `!data/external/MANIFEST.csv`).
7. **Open data and open libraries only** (see §4 and §11). No external source enters the
   pipeline until it has a complete data card (§5) and a scripted, checksummed download.
   No dependency is added until it is recorded in `docs/DEPENDENCIES.md` with licence.
8. **Reproducibility is a primary deliverable, not a final polish.** A stranger with a
   clean clone, the challenge files and the documented credentials must be able to run
   `make reproduce` and get the same submission (bit-identical where the library allows,
   otherwise within a documented tolerance). Every commit keeps this true.
9. **When unsure, stop and ask the user.** Especially for anything that touches
   competition rules, submissions, or leaderboard use.

---

## 2. The competition (verified facts)

- **Task [site]:** predict taxi-out time of departures (`PHASE_mvt = 'DEP'`) at
  EDDF, EDDM, EGLL, EHAM, LEBL, LEMD, LFPG, LIRF, LTFM, LSZH.
- **Target [site]:** `TAXITIME_SEC_mvt = MVT_TIME_UTC_mvt − BLOCK_TIME_UTC_mvt`
  (take-off minus off-block, seconds). Verify this identity on training data first.
- **Training [site]:** 12 monthly parquet files `training_2025-MM-01_….parquet`,
  movements (ARR and DEP) left-joined with NM flight data. `_mvt` columns = airport (APDF),
  `_flt` columns = NM. 4,167,797 movements total. Military/HoS/sensitive removed.
  The data is real and messy; movement/flight inconsistencies were not reconciled.
- **Ranking set [site]:** `ranking.parquet`, Jan + Jul 2026, same columns, with
  `BLOCK_TIME_UTC_mvt` and `TAXITIME_SEC_mvt` **blanked for DEP rows**. ARR rows are intact.
  It was reissued on 2026-09-04; the scored set has **344,841** departures [forum,
  organizer result JSON]. An older copy with 215,876 DEP rows is stale — check yours.
- **Submission [site]:** fill `TAXITIME_SEC_mvt` in `submitting.parquet` (columns
  `MVT_ID_mvt`, `TAXITIME_SEC_mvt`). File name `<team-name>_v<int>.parquet`, uploaded to the
  team bucket with the MinIO CLI. Error if any ID mismatches, rows are missing, or extra
  rows exist. Max **5 submissions/day**, 1 GB per bucket. Score = RMSE; best submission counts.
  Each upload produces `<file>_result.json` with `score` and `used_pairs`.
- **Fair play [site]:** organizers monitor attempts to learn from / exploit the ranking
  process. **We do not tune against the leaderboard.** The organizer has also floated a
  single final submission or a hidden final stage [forum, 2026-09-26, undecided] —
  so the pipeline must re-run end-to-end on a new period with no manual steps.
- **Deadline [site]:** 2026-10-11 23:59:59 CET.
- **Prize eligibility [site]:** source code public on GitHub under **GNU GPLv3**; all
  external datasets openly accessible, open-licensed and documented; enough documentation
  to reproduce; solution must be **original** (re-using someone else's implementation needs
  their permission *and* significant modification). Teams are encouraged to publish in JOAS.

---

## 3. Problem framing (domain notes — verify each)

- At ranking time we know the take-off time (`MVT_TIME_UTC_mvt`) but not the airport-reported
  off-block. So the task is effectively **estimating the airport-recorded AOBT** given the
  take-off, the schedule and the NM timestamps. The organizer confirmed the model is for
  **post-ops** analysis, not tactical use, and that there is no feature-cutoff restriction
  [forum, organizer, 2026-09-19].
- `AOBT_3_flt` (NM actual off-block from the flown trajectory) is populated for ~98.5% of
  ranking departures and `MVT − AOBT_3` is often within seconds of the target
  [forum, a participant]. Verify coverage and error distribution per airport and per month.
- **Label defects:** some airport block times appear to echo a scheduled/planned or default
  value; error concentrates in a small share of rows (one team: 1% of rows ≈ ⅔ of squared
  error) [forum, a participant, a participant]. Quantify on our data: share of rows with
  `BLOCK = SCHED`, `BLOCK` on round minutes, `BLOCK` equal to `LOBT/IOBT/EOBT_1`, and their
  contribution to squared error. RMSE rewards the conditional mean: on ambiguous rows,
  **hedge**, do not commit to an extreme value [forum, a participant].
- **Unmatched NM rows** (`FLIGHT_ID_mvt` null) behave differently and are hard; the echo
  behaviour there looked carrier-specific and stable month-to-month [forum, a participant].
- **Stand→runway geometry:** median taxi time per (airport, stand, runway) encodes the
  distance in target units [forum, a participant]. Must be computed out-of-fold.
- **Runway queue / wake sequence:** consecutive same-runway take-off gaps follow the
  wake-separation ladder; useful but small once congestion features exist [forum, a participant].
- **Congestion:** number of departures/arrivals in rolling windows around the take-off per
  airport and per runway, built from *both* ARR and DEP rows (ARR rows exist in ranking).
- **Causal use of ARR rows** (e.g. last arrival at the same stand before the departure) is
  legitimate [forum, a participant]. Never use the departure's own `BLOCK_TIME`.
- **Train/serve parity:** any feature using DEP `BLOCK_TIME_UTC_mvt` or `TAXITIME_SEC_mvt`
  of *other* flights is fine only if computed from training data (aggregates); for the
  ranking set those columns are blank for all DEP rows. A test must enforce this.
- **Drift 2025→2026:** check every feature's distribution Jan/Jul-2025 vs Jan/Jul-2026.
  For ADS-B, the receiver network changed between years; features about *where an aircraft
  was heard* did not transfer, features about *how it moved* did [forum, a participant].

---

## 4. External data ledger

Every row below that we actually use must have a data card (§5). Archive raw downloads:
upstream files change (the 2024 winner hit this with METAR station metadata)
[past repo: richardalligier/prc README].

| Source                                                                          | Status                                      | Basis                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Challenge parquet files                                                         | allowed                                     | [site]                                                                                                                                                                                                                                        |
| EUROCONTROL AIU/ansperformance airport data (ATFM, traffic, taxi-out)           | allowed                                     | organizer, 2026-09-17; monthly 2026 taxi-out aggregates: organizer appeared to confirm 2026-09-27 — re-confirm before use                                                                                                                    |
| adsb.lol`globe_history` (ODbL 1.0)                                            | allowed if declared                         | organizer, 2026-09-17/26. Missing days are under other release tags; see`PREFERRED_RELEASES.txt`; corrupt archives may need the other replica [forum, a participant]                                                                         |
| X-Plane Scenery Gateway`apt.dat` (stands = row 1300, taxi network)            | likely allowed                              | X-Plane airport data is published under GNU GPL (developer.x-plane.com); used by a top team [forum, a participant]. Verify per-pack licence                                                                                                           |
| **METAR/SPECI via Iowa Environmental Mesonet (IEM) ASOS archive**         | **allowed — primary weather source** | IEM disclaimer states its materials are public domain, free for any lawful use, attribution appreciated (mesonet.agron.iastate.edu/disclaimer.php, read 2026-10-02). Used by the 2024 winner. Snapshot the disclaimer text into the data card |
| **ERA5 hourly single levels (Copernicus C3S, DOI 10.24381/cds.adbb2d47)** | **allowed — secondary / gap-fill**   | Copernicus data stores switched to CC-BY 4.0 on 2025-07-02 (ECMWF forum notice). Requires a CDS account; cite dataset + attribution string per the CDS "References" section                                                                   |
| NOAA NCEI ISD / Global Hourly                                                   | **do not use**                        | NCEI states non-U.S. ISD data are under WMO Resolution 40 restrictions and cannot be redistributed — conflicts with the open-data prize rule                                                                                                 |
| OpenSky state vectors / Trino                                                   | **do not use**                        | stated by participants (not the organizer); treat as disallowed unless the organizer says otherwise                                                                                                                                           |
| Anything non-open, scraped, or paid                                             | **forbidden**                         | [site]                                                                                                                                                                                                                                        |

Expected coverage of adsb.lol surface tracks [forum, a participant/a participant — verify]:
LEMD good, LFPG thin, LTFM ~none, LIRF none in Jul-2026. Build features so missing coverage
is a first-class state, not a silent zero.

---

## 5. Data source documentation & reproducibility

Goal: anyone can see exactly which data went in, under which licence, and rebuild it.

**One data card per source** at `docs/data_sources/<source_id>.md`, copied from
`docs/data_sources/_TEMPLATE.md`. A card is complete only when every field is filled
from evidence (a query, a file, a saved web page), never from memory:

| Field                 | Content                                                                                                                                                                              |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Identity              | id, name, provider, landing page URL, exact endpoint / URL pattern used                                                                                                              |
| Licence               | licence name + URL,**verbatim snapshot** of licence/disclaimer text with the date it was read (save the page under `docs/references/licences/`), required attribution string |
| Challenge eligibility | basis for use: organizer ruling (date + quote location) or prize-rule text                                                                                                           |
| Coverage              | requested (stations / grid points / period, incl. margins) vs**measured** coverage per airport-month                                                                           |
| Retrieval             | script path, exact command, parameters, UTC retrieval timestamp, tool + library versions                                                                                             |
| Files                 | every raw file listed in`data/external/MANIFEST.csv` (path, bytes, SHA256, retrieved_at) — the manifest **is committed**                                                    |
| Schema                | raw columns, units, time zone, missing-value markers — each verified by a saved query                                                                                               |
| Lineage               | DuckDB tables fed (`raw_` → `stg_` → `clean_` → `feat_`) and the SQL files that build them                                                                                |
| Quality               | checks run, outputs in`reports/checks/`, known issues                                                                                                                              |
| Value                 | features derived and the experiment IDs that measured them (kept**and** rejected)                                                                                              |
| Re-fetch policy       | what happens if upstream changed: checksum mismatch → stop and report, never overwrite silently                                                                                     |

`docs/DATA_SOURCES.md` is the index: one row per card plus the combined attribution block
that goes into the README and the paper.

**Fetching rules**

- One script per source in `scripts/fetch/<source_id>.py`: idempotent, resumable,
  rate-limited, logs to `logs/fetch/`, writes **unmodified raw bytes** to
  `data/external/<source_id>/raw/`, then updates the manifest. Parsing is a separate step.
- Feature code never touches the network; the pipeline reads only archived local files.
- Credentials (MinIO keys, CDS API key) come from `.env` / user config, are documented in
  the README by name only, and are never committed.
- Where the licence allows redistribution, propose to the user publishing the archived raw
  external files to a versioned public archive (e.g. a Zenodo record) and put the DOI in
  the card. adsb.lol is ODbL (share-alike on derived databases) — note obligations in its card.

**Environment & run reproducibility**

- Pinned Python (`.python-version`) and committed lockfile (`uv.lock`); `make env` rebuilds it.
- `reports/env.txt` records OS, CPU, RAM, library versions for every reported result.
- All randomness from seeds in `configs/*.yaml`; each experiment records its config hash.
- Use the library's determinism option for GBMs (check the parameter name in the installed
  version's docs); the 2024 winner found determinism only held on the same system — say so
  in the README if true for us.
- `make reproduce` = env → `verify-raw` (challenge-file checksums) → fetch/verify external data →
  ingest → clean → features → train → predict → validate submission → write report.
- `tests/test_reproduce_smoke.py` runs the whole chain on a tiny slice (e.g. one airport,
  two days) so a broken pipeline is caught on every commit, not on deadline day.
- README must cover: purpose, how to obtain challenge data (MinIO), how to obtain each
  external source (incl. accounts needed), hardware + runtime, commands, expected
  validation scores, data attributions, GPLv3 licence.

---

## 6. Weather data

**Why (hypotheses — each needs a citation in `docs/METHODS.md` before it becomes a feature
family; find it in literature, ICAO documents or airport AIPs, don't assert it):**
winter operations / de-icing in January (frozen or freezing precipitation, sub-zero
temperatures, fog/frost); low-visibility procedures reducing runway throughput (visibility,
RVR, ceiling); convective weather and gusts causing departure holds in July; wind driving
runway configuration (runway is already in the data, so wind may add little — measure it).
Whether de-icing happens *between* off-block and take-off is airport-specific; check it in
the data (taxi-out distribution on snow/freezing days vs others, per airport) before modelling.

**Sources (see ledger §4):**

1. **Primary — METAR/SPECI from the IEM ASOS archive** for the 10 airport ICAO stations.
   Request raw METAR text plus IEM's parsed fields, UTC, covering 2025 and Jan/Jul 2026 with
   a margin of at least one day on each side. Read IEM's current download-service
   documentation for endpoint, parameters and units — do not reuse URLs or field names from
   memory or old repos.
2. **Secondary — ERA5 hourly single levels** only if METAR gaps are material (measure first).
   Read the current CDS API documentation before writing the fetch script (old
   snippets in past repos may no longer work). Document the grid-to-airport
   method (nearest point vs interpolation) with its source.

**Pipeline (all in DuckDB, per §8):**

- `raw_metar` verbatim → `stg_metar` typed: station, observation time (UTC), report type
  (METAR/SPECI, AUTO, COR), wind, gust, visibility, RVR, ceiling, temperature, dew point,
  pressure, present-weather codes. Convert to SI with documented factors after verifying the
  source units.
- Present-weather parsing: use IEM's parsed fields where they exist; for weather groups
  either a maintained open-source METAR parser (licence checked) or SQL patterns built from
  the ICAO Annex 3 / WMO code tables — cite the table. Validate parser output against raw
  text on a random sample and save the comparison.
- Duplicates/corrections: one documented rule for multiple reports at the same time
  (e.g. COR supersedes original) — written in the card, enforced by a check.
- Join to departures with an as-of join on time (check DuckDB's ASOF JOIN syntax in the
  installed version) at documented reference times — e.g. take-off time and an estimated
  off-block time — plus window aggregates over a documented lookback (worst visibility, max
  gust, any freezing/snow/thunder). Store observation age; if it exceeds a documented limit,
  set the feature to missing with a flag — no silent imputation.
- Checks: report count and cadence per station-month, gaps, unit sanity ranges,
  2025 vs 2026 distribution drift per airport.

**Evaluation:** one ablation experiment per weather feature group, Jan-2025 and Jul-2025
reported separately and per airport. forum reports are mixed — one team saw METAR barely
move results at airports without ADS-B coverage [forum, a participant], while the rank-3
participant uses weather [forum, a participant]. Keep weather only if it helps on held-out months.

---

## 7. Repository layout

```
data/raw/                     # challenge files as downloaded — READ ONLY, never modified (gitignored)
data/raw/training/            #   training_2025-MM-01_….parquet (12 files)
data/raw/ranking/             #   ranking.parquet   (Jan+Jul 2026, DEP target blanked)
data/raw/submitting/          #   submitting.parquet (official template — never edited)
data/raw/MANIFEST.csv         #   file, bytes, SHA256, bucket path, downloaded_at — COMMITTED
data/archive/superseded/      # older copies replaced by an organizer reissue (gitignored)
data/external/       # archived raw external downloads, one folder per source (gitignored)
data/external/MANIFEST.csv  # path, bytes, SHA256, retrieved_at — COMMITTED
configs/             # run configs (seeds, feature flags, params); hashed into experiment logs
scripts/fetch/       # one idempotent download script per external source
data/prc.duckdb      # single DuckDB database; all cleaning happens here
sql/                 # numbered, idempotent SQL: 00_ingest, 10_stage, 20_clean, 30_features, 90_checks
src/prc/             # python package: db.py, features/, models/, validate.py, submit.py
tests/               # pytest: data contracts, leakage, feature parity, submission validity
reports/checks/      # saved outputs of verification queries (csv/md)
reports/tests/       # saved pytest summaries
docs/                # METHODS.md, EXPERIMENTS.md, DATA_SOURCES.md, DEPENDENCIES.md, SUBMISSIONS.md, OPEN_QUESTIONS.md
docs/data_sources/   # one data card per external source + _TEMPLATE.md
docs/references/     # forum export, organizer page snapshots, licences/, paper notes
logs/fetch/          # download logs (gitignored)
models/                       # trained models (gitignored)
submissions/                  # filled predictions <team>_vN.parquet + validation report (gitignored)
Makefile             # make env | verify-raw | fetch | ingest | clean | features | train | predict | validate | submit-check | reproduce
```

---

## 8. Data cleaning: everything in DuckDB

### 8.0 Challenge files: where they live and how they are trusted

- `ranking.parquet` → `data/raw/ranking/`; `submitting.parquet` → `data/raw/submitting/`;
  monthly training files → `data/raw/training/`. If they currently sit loose in `data/raw/`,
  move them (don't copy) and update the manifest in its own commit.
- `data/raw/` is read-only for code: open files read-only, never write next to them.
  Optionally `chmod -R a-w data/raw/` after verification.
- `data/raw/MANIFEST.csv` (committed) records file name, bytes, SHA256, source bucket path
  and download date. `make verify-raw` recomputes hashes and fails on any mismatch;
  `make ingest` runs it first.
- **Stale ranking file guard.** The ranking set was reissued on 2026-09-04. A participant
  posted the hashes of the *pre-reissue* files [forum, a participant, 2026-09-22]:
  `ranking.parquet` 28,002,147 bytes, SHA256 `25556E61C5F71020287CA130377CE079DC22D2FA7F7F1EAF4A2F22ACAFAB463D`;
  `submitting.parquet` 1,152,346 bytes, SHA256 `241724D8C234D2C34C96519EF1B6891646E694B142BFF2C3504E83A394EE8F73`.
  If either local file matches these, it is **stale**: stop, ask the user to re-download from
  the bucket. Independently, `tests/test_contracts.py` asserts the ranking DEP count and the
  submitting row count both equal 344,841 with identical `MVT_ID_mvt` sets.
- If the organizers reissue a file again: move the old copy to
  `data/archive/superseded/<YYYY-MM-DD>/`, add the new one, update the manifest, rebuild the
  DuckDB file from scratch, and log the change in `docs/DATA_SOURCES.md`.
- `submitting.parquet` is a **template**: it is read to get the ID list and dtypes, never
  filled in place. Predictions are written to `submissions/<team-name>_v<N>.parquet`.
- The challenge data licence is not stated on the site [forum, organizer: "ask the owner"];
  never commit or redistribute the raw files or row-level extracts. Only code, manifests,
  and aggregate statistics go into the repo.
- Load **all** raw parquet files into `data/prc.duckdb` (`raw_training`, `raw_ranking`,
  `raw_submitting`) keeping the source file name and month as columns. Python never cleans
  data in pandas; it only orchestrates SQL and reads finished feature tables via Arrow.
- Layers: `raw_*` (verbatim) → `stg_*` (typed, renamed, UTC timestamps, airport/phase split)
  → `clean_*` (flags, never silent deletes) → `feat_*` (model inputs) → `pred_*`.
- **Flag, don't drop.** Suspicious rows get boolean flags (`f_block_eq_sched`,
  `f_no_nm_match`, `f_negative_taxi`, `f_taxi_gt_3h`, `f_dup_mvt_id`, `f_round_minute_block`,
  `f_type_mismatch_mvt_flt`, `f_adep_mismatch` …). Whether to down-weight, hedge or exclude
  is a modelling decision logged as an experiment.
- Every SQL file is re-runnable (`CREATE OR REPLACE`). `sql/90_checks/*.sql` return zero
  rows when the data contract holds; `tests/test_contracts.py` runs them.
- First checks to write (save outputs to `reports/checks/`): row counts per file/airport/
  phase/month; DEP count in ranking = 344,841 and = row count of `submitting.parquet` with
  identical ID sets; uniqueness of `MVT_ID_mvt`; target identity; null rates per column per
  airport; target quantiles per airport; share of squared error from top 1% rows under a
  per-airport-median baseline.

---

## 9. Validation protocol

- **Primary:** train on 2025 excluding the held-out month, predict **January 2025** and
  **July 2025** separately (mirrors the Jan/Jul 2026 ranking set) [forum, a participant: random or
  day-based folds misled; month folds tracked the board in direction]. Report both and their
  combined RMSE.
- **Always report:** per-airport RMSE, RMSE on NM-matched vs unmatched rows, RMSE on flagged
  vs clean rows, and the top-20 rows by squared error. A few rows can dominate a month
  (one team: two rows ≈ 30% of squared error) — look at them before believing a gain.
- Any target encoding / out-of-fold base predictions use **month-grouped** folds.
- Small differences (< noise across 3 seeds) are not gains. Record seed spread.
- The public leaderboard is a sanity check, not an objective. Log every upload in
  `docs/SUBMISSIONS.md` with its local validation score; never choose features by board score.

---

## 10. Modelling roadmap (each phase ends with tests green + docs updated)

**P0 – setup:** env (`uv` with lockfile), `.gitignore`, GPLv3 `LICENSE`, Makefile skeleton
including `make reproduce`, README skeleton, `docs/data_sources/_TEMPLATE.md`, inventory of
`data/raw` (names, sizes, SHA256) → `reports/checks/inventory.md`.

**P1 – ingest & contracts:** §8. No modelling until contracts pass.

**P2 – baselines** (each is a documented reference point, provenance = simple statistics):
global median; per-airport median; per (airport, runway); per (airport, stand, runway) OOF
median; `MVT − AOBT_3_flt` where available with fallback.

**P3 – gradient-boosted trees** on challenge data only. LightGBM and/or CatBoost
(seed-averaged ensembles were the 2024 winning recipe [past repo: richardalligier/prc]).
Feature families, each added in its own commit + experiment:
time deltas of `MVT_TIME` vs `SCHED`, `LOBT`, `IOBT`, `EOBT_1`, `AOBT_3`, `ARVT_*`;
calendar/hour local time; airport/runway/stand/operator/type/wake/market segment;
congestion windows; runway sequence & preceding wake category; OOF stand-runway encoding;
label-defect indicators; NM-match status.

**P4 – external data**, one source at a time, each with a complete data card (§5), a config
flag and an ablation. Order: (1) METAR weather (§6) — cheap and well-understood;
(2) apt.dat stand coordinates and taxi-network distance; (3) adsb.lol surface features
(first movement, pushback, holding); (4) ERA5 only if METAR gaps justify it.
Drift check vs 2026 before keeping anything.

**P5 – correction & ensembling:** a corrector trained on OOF base predictions with month
folds [forum, a participant, a participant]; a second model family averaged [forum — mixed
results reported, must be validated here].

**P6 – deliverables:** `make reproduce` verified from a fresh clone on a clean machine/container,
final submission, README with how to
reproduce, `docs/METHODS.md` ready to become a JOAS paper outline.

Given the deadline, prefer finishing P1–P3 with clean validation over half-built P4/P5.

---

## 11. Libraries

Use well-maintained open-source libraries; prefer few. Candidates (verify version,
licence and GPLv3 compatibility before adding): `duckdb`, `pyarrow`, `polars` or `pandas`,
`numpy`, `scikit-learn`, `lightgbm`, `catboost`, `xgboost`, `pytest`, `pyproj`/`shapely`
(geometry), `traffic` (ADS-B handling), a METAR parser if IEM's parsed fields are not
enough, `cdsapi` + `xarray` (+ a GRIB/netCDF engine) only if ERA5 is used. Record each in `docs/DEPENDENCIES.md`
(name, pinned version, licence, why). Do not hand-roll what a library already does
correctly (e.g. CV splitters, haversine, parquet I/O).

---

## 12. Submission checklist (`make submit-check`)

1. Prediction file (in `submissions/`) has exactly the rows and `MVT_ID_mvt` set of
   `data/raw/submitting/submitting.parquet` (checksum verified against the manifest),
   same dtypes, no nulls, no inf, no negative values.
2. Predictions are clipped to a documented plausible range; record how many were clipped.
3. File named `<team-name>_v<next int>.parquet`; the next integer is read from
   `docs/SUBMISSIONS.md`, not guessed.
4. Upload with `mc` (check `mc --help` and the 2024 instructions at
   ansperformance.eu dc2024 data page); then read back `<file>_result.json` and record
   `score` and `used_pairs` (must equal 344,841).
5. Never upload without the user's explicit go-ahead. Respect the 5/day limit.

---

## 13. Past PRC solutions — inspiration, not source

- 2024 (`github.com/PRC-Data-Challenge-2024`) predicted take-off weight; 2025
  (`github.com/PRC-Data-Challenge-2025`) predicted fuel burn. Neither is taxi-out.
- Borrow **practices**, not code: Makefile pipelines, archived external data, deterministic
  training flags, seed averaging, honest reproducibility notes.
- The originality rule [site] means: do not copy implementations. If an idea comes from a past
  repo, cite repo + commit in `docs/METHODS.md` and write our own code.

---

## 14. Definition of done for any task

- [ ] Claims backed by saved queries/outputs.
- [ ] APIs checked against installed versions.
- [ ] Method has provenance in `docs/METHODS.md`.
- [ ] Experiment logged (if it touches model or features), including failures.
- [ ] `pytest` run and summary saved; leakage + parity tests included for new features.
- [ ] Any new or changed data source: data card complete, manifest updated, licence snapshot saved.
- [ ] `make reproduce` (or its smoke test) still passes; README updated if commands changed.
- [ ] One concern per commit; message explains *why*.
- [ ] Open questions added to `docs/OPEN_QUESTIONS.md` (incl. ones for the organizers).
