#!/usr/bin/env bash
# Fourth queue: CatBoost capacity variants, after queue C.
set -u
cd "$(dirname "$0")/.."
until [ -f logs/queue_c.done ]; do sleep 60; done
while pgrep -f "prc.models.(gbm|nn) (validate|train)" >/dev/null; do sleep 30; done
run() { [ -f "reports/experiments/$3.md" ] && return; .venv/bin/python -m "prc.models.$1" validate --config "$2" > "logs/$3.log" 2>&1; }
run gbm configs/ablations/EXP-036_cat_depth10.yaml EXP-036
run gbm configs/ablations/EXP-037_cat_lr005.yaml EXP-037
echo QUEUE_D_DONE > logs/queue_d.done
