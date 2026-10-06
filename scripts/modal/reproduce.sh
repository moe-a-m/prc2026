#!/usr/bin/env bash
# Clean-checkout reproduction on Modal: `git clone` of the committed HEAD (no working-tree files), challenge + external
# data from the volume (checksums verified by verify-raw), then `make` ingest → clean → features → train → predict →
# submit-check with the image's uv.lock environment. `make fetch` is skipped: the archived external files are used.
# Outputs: runs/<run_id>/clean/{submissions,reports,logs} on the volume.
#   modal run scripts/modal/app.py --run-id repro-1 --timeout-h 14 --cmd "bash scripts/modal/reproduce.sh repro-1"
set -euo pipefail
RUN_ID=${1:?run id}
CLEAN=/tmp/clean
rm -rf "$CLEAN"
git clone --quiet --no-local /repo "$CLEAN"   # --no-local: copy objects (hardlinking from the mounted /repo fails)
cd "$CLEAN"
# the image sets PYTHONPATH=/repo/src; point it at the clone so code AND output paths (prc.paths.ROOT) are the clone's
# (repro-1, 2026-10-05, ran /repo's package and wrote into the shared volume through /repo's symlinks)
export PYTHONPATH="$CLEAN/src"
python -c "import prc.paths as P; assert str(P.ROOT) == '$CLEAN', P.ROOT; print('ROOT', P.ROOT)"
echo "commit $(git rev-parse --short HEAD), status: $(git status --porcelain | wc -l) changed files"
# data/raw and data/external exist in the clone (their MANIFEST.csv are committed): link the data folders inside them
for d in /vol/raw/*/; do ln -s "${d%/}" "data/raw/$(basename "$d")"; done
for d in /vol/external/*/; do ln -s "${d%/}" "data/external/$(basename "$d")"; done
ls -la data/raw data/external
python -c "import duckdb; duckdb.sql('INSTALL spatial')"
start=$(date +%s)
make PY=python verify-raw ingest clean features train predict submit-check 2>&1 | tee logs_make.txt
echo "elapsed $(( $(date +%s) - start )) s"
sha256sum submissions/*.parquet
OUT=/vol/runs/$RUN_ID/clean
mkdir -p "$OUT"
cp -r submissions reports logs_make.txt "$OUT"/
[ -d logs ] && cp -r logs "$OUT"/ || true
