#!/usr/bin/env bash
# Sequential job queue (one job at a time on a 4-thread Modal container). Waits for any running model job.
# Never list the job that is currently running — it would be run twice.
set -u
cd "$(dirname "$0")/.."
while pgrep -f "prc.models.(gbm|nn) (validate|train)" >/dev/null; do sleep 30; done
train() { [ -f "models/$2/pred_rank.parquet" ] && { echo "skip $2 (predictions exist)"; return; }
          .venv/bin/python -m prc.models.gbm train --config "$1" ${3:-} > "logs/$2_train.log" 2>&1; }
# v3 = cross-fitted blend (EXP-031): 0.490 × 3-seed LightGBM (EXP-025 seed 42 + EXP-029 seeds 7, 99) + 0.508 × CatBoost
train configs/cat_pa_wx.yaml EXP-028
train configs/ablations/EXP-025_per_airport_weather.yaml EXP-029 "--seeds 7 99 --exp-id EXP-029"
echo QUEUE_DONE > logs/queue.done
