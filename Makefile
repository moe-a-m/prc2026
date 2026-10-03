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

# Final model (submission v4, docs/SUBMISSIONS.md): blend EXP-031 of per-airport LightGBM + weather (seeds 42, 7, 99)
# and per-airport CatBoost + weather, then the three-regime hedge EXP-039 (M-026). ≈ 4 h CPU on 4 threads.
LGB := configs/ablations/EXP-025_per_airport_weather.yaml
CAT := configs/cat_pa_wx.yaml

train:          ## final fits on all 2025 -> models/EXP-025, EXP-029, EXP-028 (ranking predictions)
	$(PY) -m prc.models.gbm train --config $(LGB)
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 7 99 --exp-id EXP-029
	$(PY) -m prc.models.gbm train --config $(CAT)

predict:        ## seed average, blend with weights from reports/experiments/EXP-031.md, hedge, submission file
	$(PY) -m prc.models.blend --average EXP-025:1 EXP-029:2 --exp-id EXP-030
	$(PY) -m prc.models.blend --final --exp-id EXP-031
	mkdir -p models/EXP-039
	$(PY) -m prc.models.hedge final3 --pred models/EXP-031/pred_rank.parquet --out models/EXP-039/pred_rank.parquet
	$(PY) -m prc.submit build models/EXP-039/pred_rank.parquet

validate:       ## hold-out validation of the final recipe (Jan/Jul 2025) ≈ 10 h CPU
	$(PY) -m prc.models.gbm validate --config $(LGB)
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 7 99 --exp-id EXP-029
	$(PY) -m prc.models.gbm validate --config $(CAT)
	$(PY) -m prc.models.blend --average EXP-025:1 EXP-029:2 --exp-id EXP-030
	$(PY) -m prc.models.blend --members EXP-030 EXP-028 --exp-id EXP-031
	$(PY) -m prc.models.hedge eval3 --base EXP-031 --exp-id EXP-039

submit-check:
	$(PY) -m prc.submit check

test:           ## run tests and save the summary (CLAUDE.md §1.5)
	@mkdir -p reports/tests
	uv run --frozen pytest -q -rA 2>&1 | tee reports/tests/$$(date -u +%F)_$$(git rev-parse --short HEAD).txt

reproduce: env fetch ingest clean features train predict submit-check
