# PRC Data Challenge 2026 — taxi-out time. See README.md.
SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c
PY := uv run --frozen python
.PHONY: env verify-raw fetch ingest clean features train predict validate submit-check reproduce test baselines

env:            ## rebuild the pinned environment from uv.lock
	uv sync --frozen
	$(PY) -m prc.envinfo > reports/env.txt

verify-raw:     ## recompute SHA256 of challenge files against data/raw/MANIFEST.csv
	$(PY) -m prc.manifest verify

fetch:          ## external data, archived raw + checksummed (docs/DATA_SOURCES.md); adsb.lol is separate (days, optional)
	$(PY) scripts/fetch/iem_metar.py
	$(PY) scripts/fetch/ourairports.py
	$(PY) scripts/fetch/eurocontrol_apt.py
	$(PY) scripts/fetch/osm_aeroway.py

ingest: verify-raw
	$(PY) -m prc.pipeline 00_ingest 10_stage

clean:
	$(PY) -m prc.pipeline 20_clean

features:       ## all feature SQL; sql/40_adsb runs only when adsb.lol extracts exist
	$(PY) -m prc.pipeline 30_features 40_adsb

baselines:
	$(PY) -m prc.models.baselines

# Final model (submission v7, docs/SUBMISSIONS.md), on deterministic features (data f3abfc38ce80): per-airport LightGBM +
# weather and per-airport CatBoost + weather, 5 seeds each (42, 7, 99, 11, 23), cross-fitted NNLS blend EXP-077,
# three-regime hedge EXP-078 (M-026), ADS-B stand shrinkage with two sources EXP-079 (M-028; needs the adsb.lol
# extracts and sql/40_adsb). Blend weights and ADS-B parameters are read from the committed experiment reports, so
# `make train predict` does not need the hold-out files. ≈ 16 h CPU on 4 threads for train (≈ 2.5 h per seed on Modal).
LGB := configs/ablations/EXP-025_per_airport_weather.yaml
CAT := configs/cat_pa_wx.yaml

train:          ## final fits on all 2025 -> models/EXP-060..069 (ranking predictions)
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 42 --exp-id EXP-060
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 7 --exp-id EXP-061
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 99 --exp-id EXP-062
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 11 --exp-id EXP-063
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 23 --exp-id EXP-064
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 42 --exp-id EXP-065
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 7 --exp-id EXP-066
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 99 --exp-id EXP-067
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 11 --exp-id EXP-068
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 23 --exp-id EXP-069

predict:        ## seed averages, blend (weights: EXP-077 report), hedge, ADS-B step (parameters: EXP-079 report), submission
	$(PY) -m prc.models.blend --average EXP-060:1 EXP-061:1 EXP-062:1 EXP-063:1 EXP-064:1 --exp-id EXP-072
	$(PY) -m prc.models.blend --average EXP-065:1 EXP-066:1 EXP-067:1 EXP-068:1 EXP-069:1 --exp-id EXP-073
	$(PY) -m prc.models.blend --final --exp-id EXP-077
	mkdir -p models/EXP-078 models/EXP-079
	$(PY) -m prc.models.hedge final3 --pred models/EXP-077/pred_rank.parquet --out models/EXP-078/pred_rank.parquet
	$(PY) -m prc.models.adsb_stack final --base EXP-078 --pred models/EXP-078/pred_rank.parquet --out models/EXP-079/pred_rank.parquet --sources still,moving --from-report EXP-079
	$(PY) -m prc.submit build models/EXP-079/pred_rank.parquet

validate:       ## hold-out validation of the final recipe (Jan/Jul 2025) ≈ 30 h CPU on 4 threads
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 42 --exp-id EXP-060
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 7 --exp-id EXP-061
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 99 --exp-id EXP-062
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 11 --exp-id EXP-063
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 23 --exp-id EXP-064
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 42 --exp-id EXP-065
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 7 --exp-id EXP-066
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 99 --exp-id EXP-067
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 11 --exp-id EXP-068
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 23 --exp-id EXP-069
	$(PY) -m prc.models.blend --average EXP-060:1 EXP-061:1 EXP-062:1 EXP-063:1 EXP-064:1 --exp-id EXP-072
	$(PY) -m prc.models.blend --average EXP-065:1 EXP-066:1 EXP-067:1 EXP-068:1 EXP-069:1 --exp-id EXP-073
	$(PY) -m prc.models.blend --members EXP-072 EXP-073 --exp-id EXP-077
	$(PY) -m prc.models.hedge eval3 --base EXP-077 --exp-id EXP-078
	$(PY) -m prc.models.adsb_stack eval --base EXP-078 --exp-id EXP-079 --sources still,moving

submit-check:
	$(PY) -m prc.submit check

test:           ## run tests and save the summary (CLAUDE.md §1.5)
	@mkdir -p reports/tests
	uv run --frozen pytest -q -rA --color=no 2>&1 | tee reports/tests/$$(date -u +%F)_$$(git rev-parse --short HEAD).txt

reproduce: env fetch ingest clean features train predict submit-check
