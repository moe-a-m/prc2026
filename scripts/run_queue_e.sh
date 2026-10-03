#!/usr/bin/env bash
# Queue E: CatBoost seed spread (for a seed-averaged CatBoost in the blend), then the a-priori lr variant.
set -u
cd "$(dirname "$0")/.."
while pgrep -f "prc.models.(gbm|nn) (validate|train)" >/dev/null; do sleep 30; done
run() { [ -f "reports/experiments/$3.md" ] && return; .venv/bin/python -m "prc.models.$1" validate --config "$2" ${4:-} > "logs/$3.log" 2>&1; }
run gbm configs/cat_pa_wx.yaml EXP-041 "--seeds 7 99 --exp-id EXP-041"
run gbm configs/ablations/EXP-037_cat_lr005.yaml EXP-037
echo QUEUE_E_DONE > logs/queue_e.done
