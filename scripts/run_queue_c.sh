#!/usr/bin/env bash
# Third queue: starts when queue B is done.
set -u
cd "$(dirname "$0")/.."
until [ -f logs/queue_b.done ]; do sleep 60; done
while pgrep -f "prc.models.(gbm|nn) (validate|train)" >/dev/null; do sleep 30; done
run() { [ -f "reports/experiments/$3.md" ] && return; .venv/bin/python -m "prc.models.$1" validate --config "$2" > "logs/$3.log" 2>&1; }
run gbm configs/ablations/EXP-035_arr_stand.yaml EXP-035
echo QUEUE_C_DONE > logs/queue_c.done
