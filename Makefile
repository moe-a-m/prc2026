# PRC Data Challenge 2026 — taxi-out time. See README.md.
PY := uv run --frozen python
.PHONY: env verify-raw fetch ingest clean features train predict validate submit-check reproduce test baselines

env:            ## rebuild the pinned environment from uv.lock
	uv sync --frozen
	$(PY) -m prc.envinfo > reports/env.txt

verify-raw:     ## recompute SHA256 of challenge files against data/raw/MANIFEST.csv
	$(PY) -m prc.manifest verify

fetch:          ## external data (none used yet)
	@echo "no external sources in the pipeline yet (docs/DATA_SOURCES.md)"

ingest: verify-raw
	$(PY) -m prc.pipeline 00_ingest 10_stage

clean:
	$(PY) -m prc.pipeline 20_clean

features:
	$(PY) -m prc.pipeline 30_features

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

test:
	uv run --frozen pytest -q -rA

reproduce: env ingest clean features train predict submit-check
