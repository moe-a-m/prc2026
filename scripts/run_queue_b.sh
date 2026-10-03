#!/usr/bin/env bash
# Second queue: starts when the v3 final-fit queue is done.
set -u
cd "$(dirname "$0")/.."
until [ -f logs/queue.done ]; do sleep 60; done
while pgrep -f "prc.models.(gbm|nn) (validate|train)" >/dev/null; do sleep 30; done
run() { [ -f "reports/experiments/$3.md" ] && return; .venv/bin/python -m "prc.models.$1" validate --config "$2" > "logs/$3.log" 2>&1; }
run gbm configs/ablations/EXP-034_nm_offset.yaml EXP-034
run gbm configs/ablations/EXP-033_linear_tree.yaml EXP-033
echo QUEUE_B_DONE > logs/queue_b.done
