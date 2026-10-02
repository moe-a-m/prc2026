#!/usr/bin/env bash
# Ablation queue; waits for the first queue to finish (one job at a time on a 4-thread machine).
set -u
cd "$(dirname "$0")/.."
while pgrep -f run_queue.sh >/dev/null; do sleep 30; done
for f in configs/ablations/EXP-01[4-7]_*.yaml; do
  id=$(basename "$f" | cut -d_ -f1)
  .venv/bin/python -m prc.models.gbm validate --config "$f" > "logs/$id.log" 2>&1
done
echo QUEUE2_DONE >> logs/EXP-017.log
