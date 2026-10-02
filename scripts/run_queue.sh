#!/usr/bin/env bash
# Sequential experiment queue (one at a time: 4-thread machine).
set -u
cd "$(dirname "$0")/.."
.venv/bin/python -m prc.models.gbm validate --config configs/gbm.yaml --seeds 7 99 --exp-id EXP-012 > logs/EXP-012.log 2>&1
.venv/bin/python -m prc.models.gbm validate --config configs/cat.yaml > logs/EXP-013.log 2>&1
echo QUEUE_DONE >> logs/EXP-013.log
