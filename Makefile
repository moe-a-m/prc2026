# PRC Data Challenge 2026 — taxi-out time. See README.md.
SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c
PY := uv run --frozen python
.PHONY: env download verify-raw fetch ingest clean features train predict validate submit-check reproduce test baselines

env:            ## rebuild the pinned environment from uv.lock
	uv sync --frozen
	$(PY) -m prc.envinfo > reports/env.txt

download:       ## download the challenge files from the organizers' S3 bucket into data/raw/ (keys from .env), verify
	$(PY) scripts/fetch/challenge.py

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

# Final model (submission v9, docs/SUBMISSIONS.md), on deterministic features: per-airport LightGBM + weather and
# per-airport CatBoost + weather with training labels > 3 h winsorized except at LIRF (M-030), 5 seeds each (42, 7, 99,
# 11, 23), cross-fitted NNLS blend EXP-098, three-regime hedge EXP-099 (M-026), ADS-B stand shrinkage with three
# sources EXP-100 (M-028; needs the adsb.lol
# extracts and sql/40_adsb). Blend weights and ADS-B parameters are read from the committed experiment reports, so
# `make train predict` does not need the hold-out files. ≈ 16 h CPU on 4 threads for train (≈ 2.5 h per seed on Modal).
LGB := configs/m030_lgb.yaml
CAT := configs/m030_cat.yaml

train:          ## final fits on all 2025 -> models/EXP-086..095 (ranking predictions)
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 42 --exp-id EXP-086
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 7 --exp-id EXP-087
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 99 --exp-id EXP-088
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 11 --exp-id EXP-089
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 23 --exp-id EXP-090
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 42 --exp-id EXP-091
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 7 --exp-id EXP-092
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 99 --exp-id EXP-093
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 11 --exp-id EXP-094
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 23 --exp-id EXP-095

predict:        ## seed averages, blend (weights: EXP-098 report), hedge, ADS-B step (parameters: EXP-100 report), submission
	$(PY) -m prc.models.blend --average EXP-086:1 EXP-087:1 EXP-088:1 EXP-089:1 EXP-090:1 --exp-id EXP-096
	$(PY) -m prc.models.blend --average EXP-091:1 EXP-092:1 EXP-093:1 EXP-094:1 EXP-095:1 --exp-id EXP-097
	$(PY) -m prc.models.blend --final --exp-id EXP-098
	mkdir -p models/EXP-099 models/EXP-100
	$(PY) -m prc.models.hedge final3 --pred models/EXP-098/pred_rank.parquet --out models/EXP-099/pred_rank.parquet
	$(PY) -m prc.models.adsb_stack final --base EXP-099 --pred models/EXP-099/pred_rank.parquet --out models/EXP-100/pred_rank.parquet --sources still,moving,near --from-report EXP-100
	$(PY) -m prc.submit build models/EXP-100/pred_rank.parquet

validate:       ## hold-out validation of the final recipe (Jan/Jul 2025) ≈ 30 h CPU on 4 threads
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 42 --exp-id EXP-086
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 7 --exp-id EXP-087
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 99 --exp-id EXP-088
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 11 --exp-id EXP-089
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 23 --exp-id EXP-090
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 42 --exp-id EXP-091
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 7 --exp-id EXP-092
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 99 --exp-id EXP-093
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 11 --exp-id EXP-094
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 23 --exp-id EXP-095
	$(PY) -m prc.models.blend --average EXP-086:1 EXP-087:1 EXP-088:1 EXP-089:1 EXP-090:1 --exp-id EXP-096
	$(PY) -m prc.models.blend --average EXP-091:1 EXP-092:1 EXP-093:1 EXP-094:1 EXP-095:1 --exp-id EXP-097
	$(PY) -m prc.models.blend --members EXP-096 EXP-097 --exp-id EXP-098
	$(PY) -m prc.models.hedge eval3 --base EXP-098 --exp-id EXP-099
	$(PY) -m prc.models.adsb_stack eval --base EXP-099 --exp-id EXP-100 --sources still,moving,near

submit-check:
	$(PY) -m prc.submit check

test:           ## run tests and save the summary (CLAUDE.md §1.5)
	@mkdir -p reports/tests
	uv run --frozen pytest -q -rA --color=no 2>&1 | tee reports/tests/$$(date -u +%F)_$$(git rev-parse --short HEAD).txt

reproduce: env download fetch ingest clean features train predict submit-check
