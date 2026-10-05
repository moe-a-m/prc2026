#!/usr/bin/env bash
# Clean-checkout reproduction on Modal: `git clone` of the committed HEAD (no working-tree files), challenge + external
# data from the volume (checksums verified by verify-raw), then `make` ingest → clean → features → train → predict →
# submit-check with the image's uv.lock environment. `make fetch` is skipped: the archived external files are used.
# Outputs: runs/<run_id>/clean/{submissions,reports,logs} on the volume.
#   modal run scripts/modal/app.py --run-id repro-1 --timeout-h 14 --cmd "bash scripts/modal/reproduce.sh repro-1"
set -euo pipefail
RUN_ID=${1:?run id}
CLEAN=/tmp/clean
rm -rf "$CLEAN" && git clone --quiet /repo "$CLEAN" && cd "$CLEAN"
echo "commit $(git rev-parse --short HEAD), status: $(git status --porcelain | wc -l) changed files"
mkdir -p data && ln -s /vol/raw data/raw && ln -s /vol/external data/external
python -c "import duckdb; duckdb.sql('INSTALL spatial')"
start=$(date +%s)
make PY=python verify-raw ingest clean features train predict submit-check 2>&1 | tee logs_make.txt
echo "elapsed $(( $(date +%s) - start )) s"
sha256sum submissions/*.parquet
OUT=/vol/runs/$RUN_ID/clean
mkdir -p "$OUT"
cp -r submissions reports logs_make.txt "$OUT"/
[ -d logs ] && cp -r logs "$OUT"/ || true
