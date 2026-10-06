# PRC Data Challenge 2026 — taxi-out time prediction (team `motivated-engine`)

Open, reproducible model predicting departure taxi-out time (take-off − off-block, seconds) at
EDDF, EDDM, EGLL, EHAM, LEBL, LEMD, LFPG, LIRF, LTFM and LSZH, for the EUROCONTROL PRC Data Challenge 2026.
Licence: GNU GPLv3 (`LICENSE`).

## Approach in one paragraph
At ranking time the take-off is known, so the task is to estimate the airport-recorded off-block. Per-airport
LightGBM and CatBoost models (5 seeds each, cross-fitted blend) use NM time deltas, congestion and runway-sequence
counts from both arrivals and departures, stand occupancy, month-grouped target encodings, label-defect indicators
and METAR weather. Two post-processing steps follow: a calibrated three-regime hedge for very late flights whose
airport block time may echo the schedule, and — where adsb.lol surface tracks show the aircraft leaving its own stand
— a gated, cross-fitted shrinkage toward that observed off-block. Validation is month hold-out (Jan-2025, Jul-2025),
mirroring the Jan/Jul-2026 ranking months; current submission v7 scores 335.9 / 326.7 locally and 279.40 on the board.

Documentation: methods with provenance and a stage-by-stage overview `docs/METHODS.md`; every experiment, kept and
rejected, `docs/EXPERIMENTS.md`; submissions `docs/SUBMISSIONS.md`; data sources and licences `docs/DATA_SOURCES.md`;
dependencies `docs/DEPENDENCIES.md`; open questions `docs/OPEN_QUESTIONS.md`; paper outline `docs/PAPER_OUTLINE.md`.

## Getting the challenge data
Challenge files are not redistributed (licence not stated by the organizers). Registered teams download them from the
organizers' MinIO bucket with their team keys:

```
cp .env.example .env          # then fill in ACCESS_KEY and SECRET_KEY (never commit .env)
make data                     # = uv run python scripts/fetch/challenge.py
```

`scripts/fetch/challenge.py` needs the MinIO client `mc`. It reads the object paths from the committed
`data/raw/MANIFEST.csv`, downloads each missing file to a temporary name, checks size and SHA256 against the manifest and
only then moves it into place:

```
data/raw/training/training_2025-MM-01_….parquet   (12 files)
data/raw/ranking/ranking.parquet                  (reissued 2026-09-04)
data/raw/submitting/submitting.parquet
```

A changed or stale (pre-reissue) upstream file stops the run; nothing is overwritten. `--check` lists what is missing
without downloading. Keys are passed to `mc` as a temporary alias (`MC_HOST_<alias>`), so no `mc` config file is written.
`make verify-raw` re-checks every file against the manifest at any time.

## External data
All sources are fetched by scripts that store unmodified raw bytes under `data/external/<source>/raw/` and record
path, bytes and SHA256 in `data/external/MANIFEST.csv` (committed). No account is needed for any of them.

| source | licence | command | size / time |
|---|---|---|---|
| METAR (IEM ASOS archive) | public domain | `uv run python scripts/fetch/iem_metar.py` | ~70 MB, ~15 min |
| OurAirports runways/airports | public domain | `uv run python scripts/fetch/ourairports.py` | 17 MB |
| OpenStreetMap aeroway (Overpass, date-pinned) | ODbL | `uv run python scripts/fetch/osm_aeroway.py` | ~1 MB |
| EUROCONTROL AIU airport files | EUROCONTROL terms (organizer-approved; see card) | `uv run python scripts/fetch/eurocontrol_apt.py` | 45 MB |
| adsb.lol globe_history (Jan+Jul 2025/2026) | ODbL | `uv run python scripts/fetch/adsblol.py download` and, in parallel, `... extract` | ~388 GB streamed, ~3.5 days at ~1.7 MB/s; only ~1.3 GB of airport-surface extracts kept |

Cards with licence text, coverage and lineage: `docs/data_sources/`. The DuckDB `spatial` extension is needed for the
ADS-B features (`INSTALL spatial` once; downloaded from extensions.duckdb.org).

## Running
Requires `uv` and Python 3.14 (`.python-version`).

```
make env          # uv sync --frozen from uv.lock, writes reports/env.txt
make ingest       # verify-raw, then load raw parquet into data/prc.duckdb and stage
make clean        # flags (never deletes rows)
make fetch        # all external sources (see table above)
make features     # feature tables (all SQL, DuckDB); ADS-B stage runs when extracts exist
make baselines    # P2 reference baselines
make train        # final fits on all 2025: per-airport LightGBM + per-airport CatBoost, 5 seeds each, ≈ 16 h on 4 threads
make predict      # blend (weights from reports/experiments/EXP-044.md) + hedge + ADS-B step → submissions/
make validate     # hold-out validation of the final recipe (Jan-2025, Jul-2025), ≈ 20 h
make test         # pytest: data contracts, leakage, parity
make reproduce    # end-to-end
```

## Optional: cloud runs on Modal
`scripts/modal/` runs the same pipeline commands in a container built from `uv.lock` (needs a Modal account and the
`modal` client; challenge data go to a private Modal volume — never public). Every launch passes a budget guard
(`scripts/modal/budget.py`: billed usage + worst-case cost of recent jobs must stay under a fixed cap) and has a hard
timeout. `scripts/modal/sync.py <run_id>` copies a run's reports/logs back into the repo. Not needed to reproduce.

```
PYENV_VERSION=3.13.15 MODAL_IMAGE_BUILDER_VERSION=2025.06 modal run scripts/modal/app.py \
    --run-id <id> --timeout-h 6 --cmd "python -m prc.models.gbm validate --config configs/cat_pa_wx.yaml"
```

## Hardware and runtime
Compute: Modal containers (2 physical cores = 4 threads, 16 GiB, no GPU).
Feature build ≈ 8 min. One validation fold: global LightGBM ≈ 12–13 min, per-airport ≈ 25 min (4 threads);
final fit on all 2025 ≈ 14 min (global). Measured times are in `logs/EXP-*.log`.
The v7 models were trained on Modal containers (2 physical cores = 4 threads, 16 GiB; `scripts/modal/`): per seed,
per-airport LightGBM ≈ 38 min validation (both folds) + 22 min final fit, per-airport CatBoost ≈ 75–90 min + 43 min;
database rebuild from raw ≈ 15 min. The thread count (4) is fixed in the configs, so the same commands run locally.

## Expected validation scores
Final recipe (submission v7 = EXP-079): Jan-2025 hold-out RMSE 335.9 s, Jul-2025 326.7 s; public board 279.40
(v6 279.83, v5 283.18, v4 287.50; `docs/SUBMISSIONS.md`).

Determinism: feature SQL is order-independent (tie-inclusive counts, unique tie-breaks; `tests/test_sql_determinism.py`),
LightGBM runs with `deterministic=true, force_row_wise=true` and 4 threads, CatBoost with a fixed `random_seed` and 4
threads. **Verified 2026-10-06:** a clean `git clone` of commit 96108a9 on a fresh Modal container ran
`make verify-raw ingest clean features train predict submit-check` from the raw files (3.5 h) and produced a submission
byte-identical to the uploaded v7 (SHA256 e40eedd0…b474; `scripts/modal/reproduce.sh`, run repro-v7-3, log in
`logs/modal/runs/repro-v7-3/`). Other CPU types or thread counts may change GBM results in the last digits.

## Attributions
Challenge data: EUROCONTROL PRC / OpenSky Network (movements from APDF, `_flt` columns from EUROCONTROL NM).
Weather: Iowa Environmental Mesonet (IEM), Iowa State University. Full attribution block: `docs/DATA_SOURCES.md`.
