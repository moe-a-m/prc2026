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
| tqdm | 4.70.1 | MPL-2.0 AND MIT | progress bars |
| jupyterlab / ipywidgets | 4.6.4 / 8.1.9 | BSD-3-Clause | exploration notebooks only |
| pyrefly | 1.3.2 | MIT | type checking (dev) |
