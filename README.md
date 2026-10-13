# PRC Data Challenge 2026 — taxi-out time prediction (team `motivated-engine`)

Open, reproducible model predicting departure taxi-out time (take-off − off-block, seconds) at
EDDF, EDDM, EGLL, EHAM, LEBL, LEMD, LFPG, LIRF, LTFM and LSZH, for the EUROCONTROL PRC Data Challenge 2026.
Licence: GNU GPLv3 (`LICENSE`).

## Approach
At ranking time the take-off is known, so the task is to estimate the off-block time the airport recorded. The final
model has five stages:

1. **Base models:** per-airport LightGBM and per-airport CatBoost, 5 seeds each, averaged per family. Inputs:
   - NM time deltas (take-off vs schedule, LOBT, NM off-block);
   - congestion and runway-sequence counts from both arrivals and departures;
   - the recent departures' NM taxi-out proxy and stand occupancy;
   - month-grouped target encodings, label-defect indicators and METAR weather.

   Training labels above 3 h are winsorized, except at LIRF.
2. **Blend:** the two families, with weights fitted on hold-out predictions from other months (cross-fitted).
3. **Hedge:** a calibrated three-regime correction for very late flights whose airport block time may echo the schedule.
4. **ADS-B step:** where adsb.lol surface tracks show the aircraft leaving (or near) its own stand, a gated,
   cross-fitted shrinkage toward that observed off-block.
5. **LOBT window:** every prediction is projected onto take-off − LOBT ± 3,606 s, a bound that holds for every
   NM-matched 2025 departure.

**Validation** holds out whole months (Jan-2025, Jul-2025), mirroring the Jan/Jul-2026 ranking months. Submission v11
scores 334.2 / 300.8 locally and 268.25 on the public board.

**Final phase** (Jan, Feb, Jun, Jul 2026; single submission `motivated-engine_final.parquet`): the v11 design is
unchanged. We checked it with every 2025 month held out in turn: 289.8 s on Feb/Jun-2025 and 250.1 s over all twelve
months, with the parameters fitted on Jan + Jul. Refitting them on all months changes the 10 unseen months by
≤ 0.3 s (`reports/checks/fullyear_v11_recipe.md`).

## Documentation
- `docs/METHODS.md`: **start here.** Glossary, a stage-by-stage overview of the final model with the code behind each
  stage, and one entry per method (kept or rejected) with its provenance.
- `docs/EXPERIMENTS.md`: every experiment, kept and rejected, with hold-out scores.
- `docs/SUBMISSIONS.md`: every submission and its board score.
- `docs/DATA_SOURCES.md` and `docs/data_sources/`: data sources, licences and attributions.
- `docs/DEPENDENCIES.md`: libraries and their licences.
- `docs/OPEN_QUESTIONS.md`: open questions.
- `docs/PAPER_OUTLINE.md`: paper outline.

## Getting the challenge data
Challenge files are not redistributed (licence not stated by the organizers). Registered teams download them from the
organizers' S3 bucket (OpenSky MinIO, `prc-2026-datasets`) with their team keys:

```
cp .env.example .env          # fill in ACCESS_KEY and SECRET_KEY (never commit .env)
make download                 # = uv run python scripts/fetch/challenge.py   (--check: list only, no download)
```

`scripts/fetch/challenge.py` follows the PRC 2024 recipe (pyopensky's `S3Client`: a `minio` client on
`s3.opensky-network.org:443`, `list_objects(..., recursive=True)`, one download per object) — the Python equivalent of
`mc cp --recursive <alias>/prc-2026-datasets data` — and sorts every object into the layout the pipeline expects:

```
data/raw/training/training_2025-MM-01_….parquet   (12 files)
data/raw/ranking/ranking.parquet                  (public phase, Jan + Jul 2026; reissued 2026-09-04)
data/raw/submitting/submitting.parquet
data/raw/ranking/final_ranking.parquet            (final phase, Jan + Feb + Jun + Jul 2026; uploaded 2026-10-08 11:04 UTC)
data/raw/submitting/final_submitting.parquet      (670,790 departures)
```

The pipeline predicts the **final-phase** set (`src/prc/paths.py`, `sql/00_ingest/`): one final submission
`submissions/motivated-engine_final.parquet` (organizer e-mail and forum rulings of 2026-10-08,
`docs/OPEN_QUESTIONS.md`). The public-phase files stay in the manifest for the record.

Each file is downloaded to a temporary name and checked against the committed `data/raw/MANIFEST.csv` (bytes + SHA256)
before it is moved into place; files already present and verified are skipped. A changed or stale (pre-reissue) upstream
file, or an object that is not in the manifest, stops the run with a report — nothing verified is overwritten.
`make verify-raw` re-checks every file at any time.

## External data
Every source is fetched by a script that stores unmodified raw bytes under `data/external/<source>/raw/` and records
path, bytes and SHA256 in `data/external/MANIFEST.csv` (committed). If an upstream file no longer matches its manifest
checksum, the script stops and reports it instead of overwriting. No account is needed for any source.

| source | licence | used by the final model | command | size / time |
|---|---|---|---|---|
| METAR (IEM ASOS archive) | public domain | yes: weather features | `make fetch` | ~56 MB, ~15 min |
| OurAirports runways/airports | public domain | yes: airport boxes for the adsb.lol extraction | `make fetch` | ~16 MB |
| OpenStreetMap aeroway (Overpass, date-pinned) | ODbL | yes: stand positions for the ADS-B step | `make fetch` | ~1 MB |
| adsb.lol globe_history | ODbL | yes: ADS-B off-block step | `make fetch-adsblol ADSB_DAYS=final` | see below |
| EUROCONTROL AIU airport files | EUROCONTROL terms (organizer-approved; see card) | no: rejected experiments only | `make fetch-optional` | 45 MB |

**adsb.lol** is the slow part. Each day is a ~3 GB archive on GitHub, streamed at 1–2 MB/s, reduced to the points
near the ten airports, then deleted (`scripts/fetch/adsblol.py`; download and extraction run in parallel, about
3 days in the temporary folder at once, ~4 GB each). `ADSB_DAYS` selects the days:

| `ADSB_DAYS` | days | needed for |
|---|---|---|
| `final` (default) | Jan, Feb, Jun, Jul 2026 (120) | `make predict` (the final file) |
| `janjul` | Jan, Jul 2025 and 2026 (124) | `make validate` |
| `all` | every 2025 day + the four 2026 months (485) | `make validate-fullyear` |

At 1–2 MB/s, 120 days take about 3–4 days; the extracts kept for those days are ~1.5 GB (all 485 days: ~4.9 GB). We
fetched Jan/Jul locally and the other days on the Modal cloud service for bandwidth
(`scripts/modal/app.py::fetch_adsblol`, then `adsblol.py merge`); both paths download the same release files and check
them against the SHA256 digests GitHub publishes. Our verified reproductions (below) used all 485 days; we have not
checked that a database built from the `final` days only gives byte-identical ADS-B features for the 2026 departures
(the features are computed per flight from that flight's own surface track, so we expect it, but it is not tested).

Cards with licence text, coverage and lineage: `docs/data_sources/`, index `docs/DATA_SOURCES.md`.

## Running it yourself
Requirements: Linux or macOS, [`uv`](https://docs.astral.sh/uv/) (it installs Python 3.14 from `.python-version` and
the exact library versions from `uv.lock`), `make`, ≈ 24 GB RAM, ≈ 60 GB free disk, internet access for the downloads.
No GPU. Nothing in the pipeline needs an AI assistant or a cloud account; every step is a `make` target.

```
cp .env.example .env              # team keys for the challenge bucket (see "Getting the challenge data")
make reproduce                    # everything below, in order
```

or step by step:

```
make env              # uv sync --frozen from uv.lock; writes reports/env.txt
make download         # challenge files → data/raw/, checked against data/raw/MANIFEST.csv
make fetch            # METAR, OurAirports, OSM (minutes)
make fetch-adsblol    # adsb.lol days for the final file (ADSB_DAYS=final; days, see above)
make ingest           # verify-raw, then load raw files into data/prc.duckdb and stage them
make clean            # flags suspicious rows (never deletes)
make features         # feature tables, all in SQL (DuckDB); installs DuckDB's spatial extension for the ADS-B stage
make train            # final fits on all 2025: per-airport LightGBM + CatBoost, 5 seeds each → models/EXP-103..112
make predict          # seed averages, blend, hedge, ADS-B step, LOBT window → submissions/motivated-engine_final.parquet
make submit-check     # checks the file against the official template (IDs, dtypes, no nulls/negatives)
make test             # pytest: data contracts, leakage, train/serve parity, smoke test on a small slice
```

Optional:

```
make validate             # Jan-2025 and Jul-2025 hold-out check of the same recipe (needs ADSB_DAYS=janjul)
make validate-fullyear    # every 2025 month held out in turn (needs ADSB_DAYS=all)
make baselines            # simple reference baselines (medians)
make fetch-optional       # EUROCONTROL files, only for re-running the rejected experiments that used them
```

`make predict` reads the blend weights and ADS-B parameters from the committed reports
`reports/experiments/EXP-115.md` and `EXP-117.md`, so the final file does not need `make validate` first.
Running `make validate` rewrites those reports from your own hold-out run.

**Where things are:** SQL in `sql/` (numbered stages, run by `python -m prc.pipeline`), models and post-steps in
`src/prc/models/`, configs in `configs/` (the final configs are `configs/ablations/EXP-103_recent_lgb.yaml` and
`EXP-104_recent_cat.yaml`; each inherits from the file named in its `base:` line), checks in `sql/90_checks/` and
`tests/`, saved outputs in `reports/`.

**About `CLAUDE.md`:** the project was developed with an AI coding assistant. `CLAUDE.md` holds the working rules it
followed (verify every claim with a saved query, cite a source for every method, log every experiment including
failures, keep `make reproduce` working). Code comments that cite "CLAUDE.md §N" refer to those rules. Running the
pipeline does not involve it.

## Optional: cloud runs on Modal
We ran our experiments on Modal (`scripts/modal/`), using the same `make` targets in a container built from `uv.lock`.
You don't need it to reproduce. It needs a Modal account and the `modal` client (we ran the client under Python 3.13;
the container itself uses `uv.lock`). Challenge data go to a private Modal volume and are never made public. Every
launch passes a budget guard (`scripts/modal/budget.py`) and has a hard timeout. `scripts/modal/sync.py <run_id>`
copies a run's reports back. Names such as `repro-final-2` in the docs are labels of these runs; their logs are not in
the repository, and the results they produced are in `reports/`.

```
PYENV_VERSION=3.13.15 MODAL_IMAGE_BUILDER_VERSION=2025.06 modal run scripts/modal/app.py \
    --run-id <id> --timeout-h 6 --cmd "python -m prc.models.gbm validate --config configs/cat_pa_wx.yaml"
```

## Hardware and runtime
All runs used Modal containers: 2 physical cores (4 threads), no GPU. The thread count (4) is fixed in the configs.
Times measured on the verified clean-clone run of the final file (repro-final-2, 24 GiB RAM, 5.6 h in all):

| step | time |
|---|---|
| `make ingest clean` | ≈ 1 min |
| `make features` without ADS-B / ADS-B stage over 485 days | ≈ 2 min / ≈ 26 min |
| `make train`: LightGBM, per seed | 17–22 min (5 seeds ≈ 1.6 h) |
| `make train`: CatBoost, per seed | 39–42 min (5 seeds ≈ 3.4 h) |
| `make predict submit-check` | a few minutes |
| `make validate` (earlier runs: LightGBM ≈ 38 min, CatBoost ≈ 75–90 min per seed) | ≈ 10 h (estimated from the per-seed times) |
| `make validate-fullyear` | ≈ 6× `make validate` |

Memory: the ADS-B stage over all 485 days ran out of memory with 15 GB and completed with 24 GiB; the final
reproduction used 24 GiB. Disk: `data/prc.duckdb` grows to ≈ 23 GB; add the extracts and ~12 GB of temporary space
while adsb.lol downloads.

## Expected validation scores
Final recipe (submission v11 = EXP-118): Jan-2025 hold-out RMSE 334.2 s, Jul-2025 300.8 s; public board 268.25.

| version | change (method) | hold-out Jan / Jul | board |
|---|---|---|---|
| v7 (EXP-079) | 5 seeds per family, deterministic features | 335.9 / 326.7 | 279.40 |
| v8 (EXP-080) | ADS-B "near stand" source, 150 m (M-028) | 335.5 / 326.3 | 278.54 |
| v9 (EXP-100) | training labels > 3 h winsorized except LIRF (M-030) | 335.4 / 325.4 | 276.75 |
| v10 (EXP-101) | projection onto take-off − LOBT ± 3,606 s (M-031) | 334.5 / 301.0 | 269.25 |
| v11 (EXP-118) | recent departures' NM taxi-out proxy features (M-033) | 334.2 / 300.8 | 268.25 |

Earlier: v6 279.83, v5 283.18, v4 287.50 (`docs/SUBMISSIONS.md`).

**Final phase — full-year check of the final recipe** (EXP-135–150, `make validate-fullyear`; every 2025 month held out
in turn, models trained on the other eleven; RMSE in seconds):

| months | v11 parameters (as in the final file) | post-step parameters refit leave-one-month-out |
|---|---|---|
| Jan / Jul | 311.85 (parameters fit on these months) | 310.82 |
| Feb / Jun | 289.77 | 289.54 |
| other eight months | 221.61 | 221.50 |
| all twelve | 250.06 | 249.73 |

The final file uses the v11 parameters (blend weights EXP-115, ADS-B step EXP-117), which transfer to the ten months
they were not fitted on. Per month: Jan 334.4, Feb 279.5, Mar 183.9, Apr 193.1, May 284.4, Jun 297.6, Jul 292.5,
Aug 249.1, Sep 236.5, Oct 207.7, Nov 190.8, Dec 194.9.

## Reproducibility
How results are kept deterministic:
- Feature SQL does not depend on row order (counts include ties, ties are broken on unique keys;
  `tests/test_sql_determinism.py`).
- LightGBM runs with `deterministic=true, force_row_wise=true` and 4 threads; CatBoost with a fixed `random_seed` and
  4 threads.
- `make predict` reads its fitted parameters from committed reports, so it does not depend on a validation run.

Clean-clone checks: a fresh `git clone` of the commit, run with `scripts/modal/reproduce.sh` on a new container
(`make verify-raw ingest clean features train predict submit-check` from the raw files):

| date | target | commit | run | time | result |
|---|---|---|---|---|---|
| 2026-10-11 | final file | 2d93222 | repro-final-2 | 5.6 h | byte-identical (SHA256 2bb107fc…d7fa); every stage EXP-103–118 identical on all 670,790 rows (`reports/checks/final_reproduction.md`) |
| 2026-10-09 | final file | 9fa2ca8 | repro-final-1 | | 48,731 EHAM rows differ (RMS 3.5 s); see below |
| 2026-10-08 | v11 | b9a9d8b | repro-v11-1 | 5.1 h | byte-identical (SHA256 ccbece7e…5e77) |
| 2026-10-07 | v10 | 7369983 | repro-v10-1 | 3.6 h | 344,840 of 344,841 identical; one LEMD row differs by 1 s (integer-rounding boundary) |
| 2026-10-06 | v7 | e925575 | repro-v7-3 | 3.5 h | byte-identical (SHA256 e40eedd0…b474) |

repro-final-1: its input tables (`scripts/checks/db_determinism.py`; output not saved to the repository, summarized in
`reports/checks/refit_determinism.md`), a refit of every member (`reports/checks/refit_determinism.md`) and the
post-steps (`reports/checks/postchain_reproduction.md`) all reproduce exactly, so the difference arose in that run's
own base-model fits. We attribute it to the container's CPU, but that run did not record its CPU flags, so the cause is
not proven (`docs/OPEN_QUESTIONS.md`).

Documented tolerance: identical, or up to ±1 s on isolated rows; other CPU types or thread counts may change GBM
results in the last digits.

What the checks did **not** cover: they used our archived external files, not a fresh download. A fresh
`make fetch fetch-adsblol` gets the same bytes only while upstream files are unchanged; the checksum check stops the
run if one changed (the METAR periods are in the past but IEM may still add late reports; OSM is pinned to a date; adsb.lol release files are fixed and checked
against GitHub's SHA256 digests).

## Attributions
Challenge data: EUROCONTROL PRC / OpenSky Network (movements from APDF, `_flt` columns from EUROCONTROL NM).
Weather: Iowa Environmental Mesonet (IEM), Iowa State University. Full attribution block: `docs/DATA_SOURCES.md`.
