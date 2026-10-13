# PRC Data Challenge 2026 — taxi-out time. See README.md.
SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c
PY := uv run --frozen python
.PHONY: env download verify-raw fetch fetch-adsblol fetch-optional duckdb-ext ingest clean features train predict validate validate-fullyear fullyear-chain submit-check reproduce test baselines

env:            ## rebuild the pinned environment from uv.lock
	uv sync --frozen
	$(PY) -m prc.envinfo > reports/env.txt

download:       ## download the challenge files from the organizers' S3 bucket into data/raw/ (keys from .env), verify
	$(PY) scripts/fetch/challenge.py

verify-raw:     ## recompute SHA256 of challenge files against data/raw/MANIFEST.csv
	$(PY) -m prc.manifest verify

fetch:          ## external data used by the final model, archived raw + checksummed (docs/DATA_SOURCES.md); adsb.lol: fetch-adsblol
	$(PY) scripts/fetch/iem_metar.py
	$(PY) scripts/fetch/ourairports.py
	$(PY) scripts/fetch/osm_aeroway.py

# adsb.lol surface tracks (docs/data_sources/adsblol.md): download and extract run in parallel (network vs CPU).
# ADSB_DAYS: final = Jan, Feb, Jun, Jul 2026, needed by `make predict` (120 days, ~0.4 TB streamed, ~1-2 MB/s per day
# from GitHub); janjul = Jan + Jul 2025 and 2026, for `make validate`; all = every 2025 day too, for validate-fullyear.
ADSB_DAYS ?= final
fetch-adsblol:  ## adsb.lol days (ADSB_DAYS=final|janjul|all) -> data/external/adsblol/extract/
	rm -f data/external/adsblol/raw_tmp/DOWNLOAD_DONE
	$(PY) scripts/fetch/adsblol.py download $(ADSB_DAYS) & dl=$$!; \
	$(PY) scripts/fetch/adsblol.py extract; ex=$$?; wait $$dl; dl_rc=$$?; \
	test $$ex -eq 0 -a $$dl_rc -eq 0

fetch-optional: ## sources used only by rejected experiments (M-017, EXP-024, EXP-052); upstream updates them monthly
	$(PY) scripts/fetch/eurocontrol_apt.py

duckdb-ext:     ## DuckDB spatial extension for sql/40_adsb (downloaded once from extensions.duckdb.org)
	$(PY) -c "import duckdb; duckdb.sql('INSTALL spatial')"

ingest: verify-raw
	$(PY) -m prc.pipeline 00_ingest 10_stage

clean:
	$(PY) -m prc.pipeline 20_clean

features: duckdb-ext  ## all feature SQL; sql/40_adsb runs only when adsb.lol extracts exist
	$(PY) -m prc.pipeline 30_features 40_adsb

baselines:
	$(PY) -m prc.models.baselines

# Final model (submission v11, docs/SUBMISSIONS.md), on deterministic features: per-airport LightGBM + weather and
# per-airport CatBoost + weather with training labels > 3 h winsorized except at LIRF (M-030) and recent departures'
# NM taxi-out proxy (M-033, feat_dep_recent), 5 seeds each (42, 7, 99,
# 11, 23), cross-fitted NNLS blend EXP-115, three-regime hedge EXP-116 (M-026), ADS-B stand shrinkage with three
# sources EXP-117 (M-028; needs the adsb.lol extracts and sql/40_adsb), LOBT feasible-interval projection EXP-118 (M-031). Blend weights and ADS-B parameters are read from the committed experiment reports, so
# `make train predict` does not need the hold-out files. train ≈ 5 h on 2 cores / 4 threads (README, Hardware and runtime).
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

validate:       ## hold-out validation of the final recipe (Jan/Jul 2025), ≈ 10 h on 4 threads; needs ADSB_DAYS=janjul
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

# Full-year check (final phase, organizer e-mail 2026-10-08): the same recipe with every 2025 month held out in turn;
# own experiment IDs so the Jan/Jul reports that `predict` reads (EXP-115, EXP-117) are never overwritten.
validate-fullyear:  ## 12-month hold-out check of the final recipe -> reports/checks/fullyear_v11_recipe.md, ≈ 6× validate; ADSB_DAYS=all
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(LGB) --seeds 42 --exp-id EXP-135
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(LGB) --seeds 7 --exp-id EXP-136
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(LGB) --seeds 99 --exp-id EXP-137
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(LGB) --seeds 11 --exp-id EXP-138
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(LGB) --seeds 23 --exp-id EXP-139
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(CAT) --seeds 42 --exp-id EXP-140
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(CAT) --seeds 7 --exp-id EXP-141
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(CAT) --seeds 99 --exp-id EXP-142
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(CAT) --seeds 11 --exp-id EXP-143
	PRC_HOLDOUTS=all PRC_RESUME=1 $(PY) -m prc.models.gbm validate --config $(CAT) --seeds 23 --exp-id EXP-144
	$(MAKE) fullyear-chain

fullyear-chain:     ## post-steps of the full-year check on the EXP-135..144 hold-out predictions
	PRC_HOLDOUTS=all $(PY) -m prc.models.blend --average EXP-135:1 EXP-136:1 EXP-137:1 EXP-138:1 EXP-139:1 --exp-id EXP-145
	PRC_HOLDOUTS=all $(PY) -m prc.models.blend --average EXP-140:1 EXP-141:1 EXP-142:1 EXP-143:1 EXP-144:1 --exp-id EXP-146
	PRC_HOLDOUTS=all $(PY) -m prc.models.blend --members EXP-145 EXP-146 --exp-id EXP-147
	PRC_HOLDOUTS=all $(PY) -m prc.models.hedge eval3 --base EXP-147 --exp-id EXP-148
	PRC_HOLDOUTS=all $(PY) -m prc.models.adsb_stack eval --base EXP-148 --exp-id EXP-149 --sources still,moving,near
	PRC_HOLDOUTS=all $(PY) -m prc.models.lobt_window eval --base EXP-149 --exp-id EXP-150
	PRC_HOLDOUTS=all $(PY) scripts/checks/fullyear_summary.py

submit-check:
	$(PY) -m prc.submit check

test:           ## run tests and save the summary under reports/tests/
	@mkdir -p reports/tests
	uv run --frozen pytest -q -rA --color=no 2>&1 | tee reports/tests/$$(date -u +%F)_$$(git rev-parse --short HEAD).txt

reproduce: env download fetch fetch-adsblol ingest clean features train predict submit-check
