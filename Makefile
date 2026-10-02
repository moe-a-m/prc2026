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

fetch:          ## external data, archived raw + checksummed (docs/DATA_SOURCES.md)
	$(PY) scripts/fetch/iem_metar.py

ingest: verify-raw
	$(PY) -m prc.pipeline 00_ingest 10_stage

clean:
	$(PY) -m prc.pipeline 20_clean

features:       ## all feature SQL; sql/40_adsb runs only when adsb.lol extracts exist
	$(PY) -m prc.pipeline 30_features 40_adsb

baselines:
	$(PY) -m prc.models.baselines

train:
	$(PY) -m prc.models.gbm train --config configs/gbm.yaml

predict:
	$(PY) -m prc.models.gbm predict --config configs/gbm.yaml

validate:
	$(PY) -m prc.models.gbm validate --config configs/gbm.yaml

submit-check:
	$(PY) -m prc.submit check

test:           ## run tests and save the summary (CLAUDE.md §1.5)
	@mkdir -p reports/tests
	uv run --frozen pytest -q -rA 2>&1 | tee reports/tests/$$(date -u +%F)_$$(git rev-parse --short HEAD).txt

reproduce: env fetch ingest clean features train predict submit-check
