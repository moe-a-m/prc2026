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
- METAR (IEM ASOS archive, public domain, no account needed): `uv run python scripts/fetch/iem_metar.py`
  → `data/external/iem_metar/raw/`, checksums in `data/external/MANIFEST.csv`. Card: `docs/data_sources/iem_metar.md`.

## Running
Requires `uv` and Python 3.14 (`.python-version`).

```
make env          # uv sync --frozen from uv.lock, writes reports/env.txt
make ingest       # verify-raw, then load raw parquet into data/prc.duckdb and stage
make clean        # flags (never deletes rows)
make features     # feature tables (all SQL, DuckDB)
make baselines    # P2 reference baselines
make validate     # LightGBM month hold-out validation (Jan-2025, Jul-2025)
make test         # pytest: data contracts, leakage, parity
make reproduce    # end-to-end
```

## Hardware and runtime
Compute: Modal containers (2 physical cores = 4 threads, 16 GiB, no GPU).
Feature build ≈ 5 min; one LightGBM validation fold ≈ see `docs/EXPERIMENTS.md`.

## Expected validation scores
See `docs/EXPERIMENTS.md` (Jan-2025 and Jul-2025 hold-outs).

## Attributions
Challenge data: EUROCONTROL PRC / OpenSky Network (movements from APDF, `_flt` columns from EUROCONTROL NM).
Weather: Iowa Environmental Mesonet (IEM), Iowa State University.
