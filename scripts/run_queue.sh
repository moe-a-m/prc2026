#!/usr/bin/env bash
# Sequential experiment queue (one job at a time on a 4-thread machine). Waits for any running job.
# Never list the job that is currently running — it would be run twice.
set -u
cd "$(dirname "$0")/.."
while pgrep -f "prc.models.(gbm|nn) (validate|train)" >/dev/null; do sleep 30; done
run() { [ -f "reports/experiments/$3.md" ] && { echo "skip $3 (report exists)"; return; }
        .venv/bin/python -m "prc.models.$1" validate --config "$2" ${4:-} > "logs/$3.log" 2>&1; }
run gbm configs/cat_pa_wx.yaml EXP-028
run gbm configs/ablations/EXP-025_per_airport_weather.yaml EXP-029 "--seeds 7 99 --exp-id EXP-029"
for f in configs/ablations/EXP-01[4-7]_*.yaml; do run gbm "$f" "$(basename "$f" | cut -d_ -f1)"; done
echo QUEUE_DONE > logs/queue.done
