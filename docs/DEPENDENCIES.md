# Dependencies

Pinned versions are in `uv.lock`; this table records licence and purpose. Licences were read from
installed package metadata (`importlib.metadata`) on 2026-10-02. All are GPLv3-compatible.
On 2026-10-13 every package not imported by the final pipeline was removed from `pyproject.toml` and `uv.lock`
(194 → 42 locked packages; the versions of all remaining packages are unchanged, so the reported runs still apply).
See "Removed" below.

| Package | Version | Licence | Why |
|---|---|---|---|
| duckdb | 1.5.6 | MIT | all ingest/cleaning/feature SQL (all data cleaning happens in DuckDB) |
| pyarrow | 25.0.1 | Apache-2.0 | parquet I/O, Arrow hand-off DuckDB → Python |
| pandas | 3.0.6 | BSD-3-Clause | model-side frames (no cleaning) |
| numpy | 2.5.3 | BSD-3-Clause (+0BSD/MIT/Zlib/CC0 parts) | numerics |
| lightgbm | 4.7.0 | MIT | gradient-boosted trees (base learner of the final model) |
| catboost | 1.2.10 | Apache-2.0 | gradient-boosted trees, second model family (base learner of the final model) |
| pyyaml | 6.0.3 | MIT | run configs in `configs/*.yaml` |
| duckdb spatial extension | built for duckdb 1.5.6 (`INSTALL spatial` from extensions.duckdb.org) | MIT | ST_Distance_Sphere for ADS-B taxi distance; axis order (lat, lon) verified on EDDF 07C–25C (3,980 m vs 4,000 m published) |
| tabulate | 0.10.0 | MIT | markdown tables in `reports/checks/` (pandas `to_markdown`) |
| orjson | 3.12.0 | MPL-2.0 AND (Apache-2.0 OR MIT) | fast JSON parsing of adsb.lol traces (8 vs 3 MB/s) |
| pytest | 9.1.1 | MIT | tests |
| scipy | 1.18.1 | BSD-3-Clause | NNLS blend weights (`prc.models.blend`), Wilson intervals (`scripts/checks/m026_stability.py`) |
| requests | 2.34.2 | Apache-2.0 | external-data fetch scripts (`scripts/fetch/`, `src/prc/fetchutil.py`) |
| minio | 7.2.20 | Apache-2.0 (package metadata) | `make download`: challenge files from the organizers' S3 bucket (`scripts/fetch/challenge.py`); also used by pyopensky |

### Removed on 2026-10-13 (not used by the final pipeline)
scikit-learn, torch, matplotlib (still installed: a dependency of catboost), traffic, geopandas, shapely, openap, pitot,
tqdm, jupyterlab, ipywidgets, pyrefly. Rejected-experiment code that needs one of them no longer runs as-is:
`prc.models.nn` (M-013, torch 2.14.1+cpu), `prc.models.echo_clf` (M-032, scikit-learn 1.9.1) and
`scripts/explore/p6/q16.py`, `q30.py`, `q31.py` (scikit-learn); install that package with `uv pip install` to rerun them.
Their NN smoke test skips when torch is absent.

### Optional (not in `uv.lock`, not needed for `make reproduce`)
| Tool | Version | Licence | Why |
|---|---|---|---|
| modal (client) | 1.5.3 | Apache-2.0 (package metadata) | optional cloud runs of the same commands (`scripts/modal/`); installed outside the project venv (Python 3.13). The container image is built from this repo's `uv.lock` (Python 3.14.7, uv 0.12.20) + Debian `libgomp1`, so library versions match the local run |

The MinIO command-line client `mc` is not needed by the pipeline; the team uses it only to upload submissions.
