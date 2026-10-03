#!/usr/bin/env bash
# Queue F: after queue E, final fits of CatBoost seeds 7/99 on all 2025 (for the 3-seed CatBoost in v5, EXP-045).
set -u
cd "$(dirname "$0")/.."
until [ -f logs/queue_e.done ]; do sleep 60; done
while pgrep -f "prc.models.(gbm|nn) (validate|train)" >/dev/null; do sleep 30; done
[ -f models/EXP-041/pred_rank.parquet ] || .venv/bin/python -m prc.models.gbm train --config configs/cat_pa_wx.yaml --seeds 7 99 --exp-id EXP-041 > logs/EXP-041_train.log 2>&1
echo QUEUE_F_DONE > logs/queue_f.done
