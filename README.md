# PRC Data Challenge 2026 — taxi-out time prediction (team `motivated-engine`)

Open, reproducible model predicting departure taxi-out time (take-off − off-block, seconds) at
EDDF, EDDM, EGLL, EHAM, LEBL, LEMD, LFPG, LIRF, LTFM and LSZH, for the EUROCONTROL PRC Data Challenge 2026.
Licence: GNU GPLv3 (`LICENSE`).

## Status
Work in progress. Methods: `docs/METHODS.md`; experiment log with validation scores: `docs/EXPERIMENTS.md`;
data sources: `docs/DATA_SOURCES.md`; dependencies and licences: `docs/DEPENDENCIES.md`.

## Getting the challenge data
Challenge files are not redistributed (licence not stated by the organizers). Registered teams download them with
the MinIO client (`mc`) using their OpenSky credentials, then place them as:

```
data/raw/training/training_2025-MM-01_….parquet   (12 files)
data/raw/ranking/ranking.parquet                  (reissued 2026-09-04)
data/raw/submitting/submitting.parquet
```

`make verify-raw` checks every file against `data/raw/MANIFEST.csv` (bytes + SHA256) and refuses stale
pre-reissue copies.

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
make train        # final fits on all 2025: per-airport LightGBM (3 seeds) + per-airport CatBoost (3 seeds), ≈ 9 h
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

## Expected validation scores
Final recipe (submission v5 = EXP-050): Jan-2025 hold-out RMSE 337.2 s, Jul-2025 328.2 s (v4 = EXP-039: 339.8 / 330.5,
public board 287.50; `docs/SUBMISSIONS.md`). Full log of every experiment, kept and rejected: `docs/EXPERIMENTS.md`.

Determinism: LightGBM runs with `deterministic=true, force_row_wise=true`; CatBoost with a fixed `random_seed`. On the
development machine `make predict` regenerates the v4 file byte-for-byte (same SHA256 as the uploaded file); results on
other CPUs/thread counts may differ in the last digits.

## Attributions
Challenge data: EUROCONTROL PRC / OpenSky Network (movements from APDF, `_flt` columns from EUROCONTROL NM).
Weather: Iowa Environmental Mesonet (IEM), Iowa State University. Full attribution block: `docs/DATA_SOURCES.md`.
