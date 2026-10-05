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

# Final model (submission v5, docs/SUBMISSIONS.md): blend EXP-044 of per-airport LightGBM + weather (seeds 42, 7, 99)
# and per-airport CatBoost + weather (seeds 42, 7, 99), three-regime hedge (M-026), then ADS-B stand shrinkage EXP-050
# (M-028; needs the adsb.lol extracts and sql/40_adsb). ≈ 9 h CPU on 4 threads.
LGB := configs/ablations/EXP-025_per_airport_weather.yaml
CAT := configs/cat_pa_wx.yaml

train:          ## final fits on all 2025 -> models/EXP-025, EXP-029, EXP-028, EXP-041 (ranking predictions)
	$(PY) -m prc.models.gbm train --config $(LGB)
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 7 99 --exp-id EXP-029
	$(PY) -m prc.models.gbm train --config $(CAT)
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 7 99 --exp-id EXP-041

predict:        ## seed averages, blend (weights from reports/experiments/EXP-044.md), hedge, ADS-B step, submission
	$(PY) -m prc.models.blend --average EXP-025:1 EXP-029:2 --exp-id EXP-030
	$(PY) -m prc.models.blend --average EXP-028:1 EXP-041:2 --exp-id EXP-043
	$(PY) -m prc.models.blend --final --exp-id EXP-044
	mkdir -p models/EXP-045 models/EXP-050
	$(PY) -m prc.models.hedge final3 --pred models/EXP-044/pred_rank.parquet --out models/EXP-045/pred_rank.parquet
	$(PY) -m prc.models.adsb_stack final --base EXP-045 --pred models/EXP-045/pred_rank.parquet --out models/EXP-050/pred_rank.parquet
	$(PY) -m prc.submit build models/EXP-050/pred_rank.parquet

validate:       ## hold-out validation of the final recipe (Jan/Jul 2025) ≈ 20 h CPU
	$(PY) -m prc.models.gbm validate --config $(LGB)
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 7 99 --exp-id EXP-029
	$(PY) -m prc.models.gbm validate --config $(CAT)
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 7 99 --exp-id EXP-041
	$(PY) -m prc.models.blend --average EXP-025:1 EXP-029:2 --exp-id EXP-030
	$(PY) -m prc.models.blend --average EXP-028:1 EXP-041:2 --exp-id EXP-043
	$(PY) -m prc.models.blend --members EXP-030 EXP-043 --exp-id EXP-044
	$(PY) -m prc.models.hedge eval3 --base EXP-044 --exp-id EXP-045
	$(PY) -m prc.models.adsb_stack eval --base EXP-045 --exp-id EXP-050

submit-check:
	$(PY) -m prc.submit check

test:           ## run tests and save the summary (CLAUDE.md §1.5)
	@mkdir -p reports/tests
	uv run --frozen pytest -q -rA 2>&1 | tee reports/tests/$$(date -u +%F)_$$(git rev-parse --short HEAD).txt

reproduce: env fetch ingest clean features train predict submit-check
