#!/usr/bin/env bash
# Sequential experiment queue (one job at a time on a 4-thread machine). Waits for any running validation.
set -u
cd "$(dirname "$0")/.."
while pgrep -f "prc.models.(gbm|nn) validate" >/dev/null; do sleep 30; done
run() { .venv/bin/python -m "prc.models.$1" validate --config "$2" > "logs/$3.log" 2>&1; }
run gbm configs/ablations/EXP-022_per_airport.yaml EXP-022
run gbm configs/ablations/EXP-023_queue_rw_p10.yaml EXP-023
run gbm configs/ablations/EXP-024_weather_ec.yaml EXP-024
run nn  configs/nn.yaml EXP-019
run gbm configs/ablations/EXP-020_nm_default.yaml EXP-020
run gbm configs/cat.yaml EXP-013
for f in configs/ablations/EXP-01[4-7]_*.yaml; do run gbm "$f" "$(basename "$f" | cut -d_ -f1)"; done
echo QUEUE_DONE > logs/queue.done
