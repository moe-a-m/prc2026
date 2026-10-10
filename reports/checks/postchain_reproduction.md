# Post-chain reproduction of the final file

Run postchain-1 (Modal, 2026-10-10; `scripts/modal/postchain_check.sh`): clean `git clone` of 172bd3e, the original
base-model predictions EXP-103–112 (`/vol/models`, final fits of 2026-10-08) and the volume DB that build-final-1 read,
then `make predict`. Every post-chain stage is compared with the original on the 670,790 ranking rows.

| stage | step | rows differing | max \|d\| (s) |
|:--|:--|--:|--:|
| EXP-113 | LightGBM 5-seed average | 0 | 0 |
| EXP-114 | CatBoost 5-seed average | 0 | 0 |
| EXP-115 | blend (weights 0.4641 / 0.535 from the EXP-115 report) | 0 | 0 |
| EXP-116 | three-regime hedge (34 rows changed) | 0 | 0 |
| EXP-117 | ADS-B step (203,997 rows changed) | 0 | 0 |
| EXP-118 | LOBT window (276 rows changed) | 0 | 0 |

`submissions/motivated-engine_final.parquet` SHA256 `2bb107fcb72e0ad0d922d5f35cb8a8279b984caf0835a2d5b5b8d3bc8c00d7fa`,
identical to the built final file.

Together with `refit_determinism.md` (all ten members refit bit-identically on fresh containers) and
`db_determinism.md` (model input tables identical after a rebuild from raw), the difference of repro-final-1
(48,731 EHAM rows, RMS 3.5 s) is not in the code path: it arose inside that run's own base-model fits. The sandbox
hides the CPU model; `reproduce.sh` now prints the CPU feature flags and keeps every member's predictions so a rerun
can name the member.
