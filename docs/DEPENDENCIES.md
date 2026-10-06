# Dependencies

Pinned versions are in `uv.lock`; this table records licence and purpose. Licences were read from
installed package metadata (`importlib.metadata`) on 2026-10-02. All are GPLv3-compatible.

| Package | Version | Licence | Why |
|---|---|---|---|
| duckdb | 1.5.6 | MIT | all ingest/cleaning/feature SQL (CLAUDE.md §8) |
| pyarrow | 25.0.1 | Apache-2.0 | parquet I/O, Arrow hand-off DuckDB → Python |
| pandas | 3.0.6 | BSD-3-Clause | model-side frames (no cleaning) |
| numpy | 2.5.3 | BSD-3-Clause (+0BSD/MIT/Zlib/CC0 parts) | numerics |
| scikit-learn | 1.9.1 | BSD-3-Clause | metrics, CV utilities |
| lightgbm | 4.7.0 | MIT | gradient-boosted trees (P3) |
| catboost | 1.2.10 | Apache-2.0 | gradient-boosted trees, second family (P3/P5) |
| pyyaml | 6.0.3 | MIT | run configs in `configs/*.yaml` |
| duckdb spatial extension | built for duckdb 1.5.6 (`INSTALL spatial` from extensions.duckdb.org) | MIT | ST_Distance_Sphere for ADS-B taxi distance; axis order (lat, lon) verified on EDDF 07C–25C (3,980 m vs 4,000 m published) |
| tabulate | 0.10.0 | MIT | markdown tables in `reports/checks/` (pandas `to_markdown`) |
| torch | 2.14.1+cpu | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT (all GPLv3-compatible) | neural tabular model (M-013); CPU wheel from the explicit `pytorch-cpu` uv index |
| orjson | 3.12.0 | MPL-2.0 AND (Apache-2.0 OR MIT) | fast JSON parsing of adsb.lol traces (8 vs 3 MB/s) |
| pytest | 9.1.1 | MIT | tests |
| scipy | 1.18.1 | BSD-3-Clause | pre-existing (exploration) |
| matplotlib | 3.11.2 | PSF-based | pre-existing (exploration plots) |
| traffic | 2.13.post75 (git) | MIT | pre-existing; reserved for ADS-B work (P4) |
| geopandas / shapely | 1.2.0 / 2.1.2 | BSD-3-Clause | pre-existing; reserved for stand geometry (P4) |
| openap | 2.6.2 | LGPL-3.0 | pre-existing; not used by the pipeline |
| pitot | 0.3.2 | MIT | pre-existing; not used by the pipeline |
| requests | 2.34.2 | Apache-2.0 | external fetch scripts (P4) |
| minio | 7.2.20 | Apache-2.0 (package metadata) | `make download`: challenge files from the organizers' S3 bucket (`scripts/fetch/challenge.py`); also used by pyopensky |
| tqdm | 4.70.1 | MPL-2.0 AND MIT | progress bars |
| jupyterlab / ipywidgets | 4.6.4 / 8.1.9 | BSD-3-Clause | exploration notebooks only |
| pyrefly | 1.3.2 | MIT | type checking (dev) |

### Optional (not in `uv.lock`, not needed for `make reproduce`)
| Tool | Version | Licence | Why |
|---|---|---|---|
| modal (client) | 1.5.3 | Apache-2.0 (package metadata) | optional cloud runs of the same commands (`scripts/modal/`); installed outside the project venv (Python 3.13). The container image is built from this repo's `uv.lock` (Python 3.14.7, uv 0.12.20) + Debian `libgomp1`, so library versions match the local run |

The MinIO command-line client `mc` is not needed by the pipeline; the team uses it only to upload submissions.
