#!/usr/bin/env bash
# Post-chain reproduction (2026-10-10): repro-final-1 differed from the final file on 48,731 EHAM rows although every
# base model (EXP-103–112) refits bit-identically (reports/checks/refit_determinism.md). This reruns only `make
# predict` in a clean clone of HEAD on the ORIGINAL base-model predictions and the volume DB (the one build-final-1
# read), then compares every post-chain stage (EXP-113–118) and the final file with the originals.
#   modal run --detach scripts/modal/app.py::main --spawn --run-id postchain-1 --cmd "bash scripts/modal/postchain_check.sh postchain-1"
set -euo pipefail
RUN_ID=${1:?run id}
CLEAN=/tmp/clean
rm -rf "$CLEAN"
git clone --quiet --no-local /repo "$CLEAN"
cd "$CLEAN"
export PYTHONPATH="$CLEAN/src"
python -c "import prc.paths as P; assert str(P.ROOT) == '$CLEAN', P.ROOT"
echo "commit $(git rev-parse --short HEAD)"
for d in /vol/raw/*/; do ln -s "${d%/}" "data/raw/$(basename "$d")"; done
for d in /vol/external/*/; do ln -s "${d%/}" "data/external/$(basename "$d")"; done
ln -s /repo/data/prc.duckdb data/prc.duckdb          # the runner's local copy of /vol/prc.duckdb
mkdir -p models
for e in $(seq 103 112); do cp -r /vol/models/EXP-$e models/; done
python -c "import duckdb; duckdb.sql('INSTALL spatial')"
make PY=python predict 2>&1 | tee logs_predict.txt
python - <<'EOF'
import numpy as np, pandas as pd
for e in range(113, 119):
    a = pd.read_parquet(f"/vol/models/EXP-{e}/pred_rank.parquet")
    b = pd.read_parquet(f"models/EXP-{e}/pred_rank.parquet")
    m = a.merge(b, on="mvt_id", suffixes=("_o", "_r"))
    d = m.pred_r - m.pred_o
    print(f"EXP-{e}: rows {len(m)} differing {(d != 0).sum()} max|d| {d.abs().max():.4f} rms {np.sqrt((d**2).mean()):.4f}")
EOF
sha256sum submissions/motivated-engine_final.parquet
OUT=/vol/runs/$RUN_ID/clean
mkdir -p "$OUT/models"
cp logs_predict.txt submissions/motivated-engine_final.parquet "$OUT"/
for e in $(seq 113 118); do cp -r models/EXP-$e "$OUT/models/"; done
