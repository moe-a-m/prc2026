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

# Final model (submission v11, docs/SUBMISSIONS.md), on deterministic features: per-airport LightGBM + weather and
# per-airport CatBoost + weather with training labels > 3 h winsorized except at LIRF (M-030) and recent departures'
# NM taxi-out proxy (M-033, feat_dep_recent), 5 seeds each (42, 7, 99,
# 11, 23), cross-fitted NNLS blend EXP-115, three-regime hedge EXP-116 (M-026), ADS-B stand shrinkage with three
# sources EXP-117 (M-028; needs the adsb.lol extracts and sql/40_adsb), LOBT feasible-interval projection EXP-118 (M-031). Blend weights and ADS-B parameters are read from the committed experiment reports, so
# `make train predict` does not need the hold-out files. ≈ 16 h CPU on 4 threads for train (≈ 2.5 h per seed on Modal).
LGB := configs/ablations/EXP-103_recent_lgb.yaml
CAT := configs/ablations/EXP-104_recent_cat.yaml

train:          ## final fits on all 2025 -> models/EXP-103..112 (ranking predictions)
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 42 --exp-id EXP-103
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 7 --exp-id EXP-105
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 99 --exp-id EXP-106
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 11 --exp-id EXP-107
	$(PY) -m prc.models.gbm train --config $(LGB) --seeds 23 --exp-id EXP-108
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 42 --exp-id EXP-104
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 7 --exp-id EXP-109
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 99 --exp-id EXP-110
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 11 --exp-id EXP-111
	$(PY) -m prc.models.gbm train --config $(CAT) --seeds 23 --exp-id EXP-112

predict:        ## seed averages, blend (weights: EXP-115 report), hedge, ADS-B step (parameters: EXP-117 report), LOBT window, submission
	$(PY) -m prc.models.blend --average EXP-103:1 EXP-105:1 EXP-106:1 EXP-107:1 EXP-108:1 --exp-id EXP-113
	$(PY) -m prc.models.blend --average EXP-104:1 EXP-109:1 EXP-110:1 EXP-111:1 EXP-112:1 --exp-id EXP-114
	$(PY) -m prc.models.blend --final --exp-id EXP-115
	mkdir -p models/EXP-116 models/EXP-117 models/EXP-118
	$(PY) -m prc.models.hedge final3 --pred models/EXP-115/pred_rank.parquet --out models/EXP-116/pred_rank.parquet
	$(PY) -m prc.models.adsb_stack final --base EXP-116 --pred models/EXP-116/pred_rank.parquet --out models/EXP-117/pred_rank.parquet --sources still,moving,near --from-report EXP-117
	$(PY) -m prc.models.lobt_window final --pred models/EXP-117/pred_rank.parquet --out models/EXP-118/pred_rank.parquet
	$(PY) -m prc.submit final models/EXP-118/pred_rank.parquet  # final phase: one file, motivated-engine_final.parquet

validate:       ## hold-out validation of the final recipe (Jan/Jul 2025) ≈ 30 h CPU on 4 threads
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 42 --exp-id EXP-103
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 7 --exp-id EXP-105
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 99 --exp-id EXP-106
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 11 --exp-id EXP-107
	$(PY) -m prc.models.gbm validate --config $(LGB) --seeds 23 --exp-id EXP-108
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 42 --exp-id EXP-104
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 7 --exp-id EXP-109
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 99 --exp-id EXP-110
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 11 --exp-id EXP-111
	$(PY) -m prc.models.gbm validate --config $(CAT) --seeds 23 --exp-id EXP-112
	$(PY) -m prc.models.blend --average EXP-103:1 EXP-105:1 EXP-106:1 EXP-107:1 EXP-108:1 --exp-id EXP-113
	$(PY) -m prc.models.blend --average EXP-104:1 EXP-109:1 EXP-110:1 EXP-111:1 EXP-112:1 --exp-id EXP-114
	$(PY) -m prc.models.blend --members EXP-113 EXP-114 --exp-id EXP-115
	$(PY) -m prc.models.hedge eval3 --base EXP-115 --exp-id EXP-116
	$(PY) -m prc.models.adsb_stack eval --base EXP-116 --exp-id EXP-117 --sources still,moving,near
	$(PY) -m prc.models.lobt_window eval --base EXP-117 --exp-id EXP-118

submit-check:
	$(PY) -m prc.submit check

test:           ## run tests and save the summary (CLAUDE.md §1.5)
	@mkdir -p reports/tests
	uv run --frozen pytest -q -rA --color=no 2>&1 | tee reports/tests/$$(date -u +%F)_$$(git rev-parse --short HEAD).txt

reproduce: env download fetch ingest clean features train predict submit-check
