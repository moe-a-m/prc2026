# Dependencies

Pinned versions are in `uv.lock`; this table records licence and purpose. Licences were read from
installed package metadata (`importlib.metadata`) on 2026-10-02. All are GPLv3-compatible.
Some packages are in `pyproject.toml` (so `uv sync` installs them) but are not imported anywhere under `src/` or
`scripts/` (checked with `git grep` on 2026-10-13); they are marked **installed, not used by the final pipeline**.
Removing them would change `uv.lock`, which every reported run used, so they are left in place.

| Package | Version | Licence | Why |
|---|---|---|---|
| duckdb | 1.5.6 | MIT | all ingest/cleaning/feature SQL (all data cleaning happens in DuckDB) |
| pyarrow | 25.0.1 | Apache-2.0 | parquet I/O, Arrow hand-off DuckDB → Python |
| pandas | 3.0.6 | BSD-3-Clause | model-side frames (no cleaning) |
| numpy | 2.5.3 | BSD-3-Clause (+0BSD/MIT/Zlib/CC0 parts) | numerics |
| scikit-learn | 1.9.1 | BSD-3-Clause | `HistGradientBoostingClassifier` in the rejected echo classifier (M-032, `prc.models.echo_clf`) and exploration scripts; not used by the final pipeline |
| lightgbm | 4.7.0 | MIT | gradient-boosted trees (base learner of the final model) |
| catboost | 1.2.10 | Apache-2.0 | gradient-boosted trees, second model family (base learner of the final model) |
| pyyaml | 6.0.3 | MIT | run configs in `configs/*.yaml` |
| duckdb spatial extension | built for duckdb 1.5.6 (`INSTALL spatial` from extensions.duckdb.org) | MIT | ST_Distance_Sphere for ADS-B taxi distance; axis order (lat, lon) verified on EDDF 07C–25C (3,980 m vs 4,000 m published) |
| tabulate | 0.10.0 | MIT | markdown tables in `reports/checks/` (pandas `to_markdown`) |
| torch | 2.14.1+cpu | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT (all GPLv3-compatible) | neural tabular model (M-013, rejected: EXP-019 / EXP-027; `prc.models.nn` only); **installed, not used by the final pipeline**; CPU wheel from the explicit `pytorch-cpu` uv index |
| orjson | 3.12.0 | MPL-2.0 AND (Apache-2.0 OR MIT) | fast JSON parsing of adsb.lol traces (8 vs 3 MB/s) |
| pytest | 9.1.1 | MIT | tests |
| scipy | 1.18.1 | BSD-3-Clause | NNLS blend weights (`prc.models.blend`), Wilson intervals (`scripts/checks/m026_stability.py`) |
| matplotlib | 3.11.2 | PSF-based | **installed, not used by the final pipeline** (not imported) |
| traffic | 2.13.post75 (git) | MIT | **installed, not used by the final pipeline** (not imported; the ADS-B processing is our own code in `scripts/fetch/adsblol.py` and `sql/40_adsb/`) |
| geopandas / shapely | 1.2.0 / 2.1.2 | BSD-3-Clause | **installed, not used by the final pipeline** (not imported; stand geometry is done in DuckDB SQL) |
| openap | 2.6.2 | LGPL-3.0 | **installed, not used by the final pipeline** (not imported) |
| pitot | 0.3.2 | MIT | **installed, not used by the final pipeline** (not imported) |
| requests | 2.34.2 | Apache-2.0 | external-data fetch scripts (`scripts/fetch/`, `src/prc/fetchutil.py`) |
| minio | 7.2.20 | Apache-2.0 (package metadata) | `make download`: challenge files from the organizers' S3 bucket (`scripts/fetch/challenge.py`); also used by pyopensky |
| tqdm | 4.70.1 | MPL-2.0 AND MIT | **installed, not used by the final pipeline** (not imported) |
| jupyterlab / ipywidgets | 4.6.4 / 8.1.9 | BSD-3-Clause | **installed, not used by the final pipeline** (no notebooks in the repo) |
| pyrefly | 1.3.2 | MIT | type checker (development tool); **installed, not used by the final pipeline** |

### Optional (not in `uv.lock`, not needed for `make reproduce`)
| Tool | Version | Licence | Why |
|---|---|---|---|
| modal (client) | 1.5.3 | Apache-2.0 (package metadata) | optional cloud runs of the same commands (`scripts/modal/`); installed outside the project venv (Python 3.13). The container image is built from this repo's `uv.lock` (Python 3.14.7, uv 0.12.20) + Debian `libgomp1`, so library versions match the local run |

The MinIO command-line client `mc` is not needed by the pipeline; the team uses it only to upload submissions.
