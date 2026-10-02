#!/usr/bin/env bash
# Sequential experiment queue (one job at a time on a 4-thread machine). Waits for any running validation.
set -u
cd "$(dirname "$0")/.."
while pgrep -f "prc.models.gbm validate" >/dev/null; do sleep 30; done
run() { .venv/bin/python -m prc.models.gbm validate --config "$1" > "logs/$2.log" 2>&1; }
run configs/ablations/EXP-018_weather.yaml EXP-018
run configs/cat.yaml EXP-013
for f in configs/ablations/EXP-01[4-7]_*.yaml; do run "$f" "$(basename "$f" | cut -d_ -f1)"; done
echo QUEUE_DONE > logs/queue.done
