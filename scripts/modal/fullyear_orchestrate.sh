#!/usr/bin/env bash
# Full-year check, CatBoost part (2026-10-09): wait for the 15 resumable jobs fy2-cat-s<seed>-<jan|may|sep>
# (EXP-140..144, PRC_HOLDOUTS = 4-month groups, PRC_RESUME=1), relaunch a group whose run ended without all its folds
# (resume keeps finished folds; at most 2 relaunches each), then run on Modal: full CatBoost reports (resume = load
# only) + `make fullyear-chain`, and sync the outputs into the working tree. Detached:
#   setsid nohup bash scripts/modal/fullyear_orchestrate.sh > logs/modal/fullyear_orchestrate.log 2>&1 < /dev/null &
# Done-marker: logs/modal/fullyear_orchestrate.done
set -uo pipefail
cd "$(dirname "$0")/../.."
export PYENV_VERSION=${PYENV_VERSION:-3.13.15} MODAL_IMAGE_BUILDER_VERSION=2025.06
PRE="python -c \"import duckdb; duckdb.sql('INSTALL spatial')\""
CAT=configs/ablations/EXP-104_recent_cat.yaml
SEEDS="42:140 7:141 99:142 11:143 23:144"
MONTH_GROUPS="jan,feb,mar,apr may,jun,jul,aug sep,oct,nov,dec"
log() { echo "$(date -u +%FT%TZ) $*"; }
declare -A tries curr
oof_list() { modal volume ls prc2026-data models/oof 2>/dev/null | grep -oE "EXP-14[0-4]_[a-z]{3}\.json" | sort -u; }

while true; do
  have=$(oof_list); pending=0
  for sx in $SEEDS; do
    s=${sx%:*}; e=EXP-${sx#*:}
    for g in $MONTH_GROUPS; do
      tag=${g%%,*}; key=fy2-cat-s$s-$tag; run=${curr[$key]:-$key}
      missing=0
      for m in ${g//,/ }; do grep -qx "${e}_$m.json" <<< "$have" || missing=$((missing + 1)); done
      [ $missing -eq 0 ] && continue
      code=$(modal volume get prc2026-data "runs/$run/exit_code" - 2>/dev/null | head -c 1)
      if [ -z "$code" ]; then pending=$((pending + 1)); continue; fi
      # run ended (or a relaunch finished) without all folds: relaunch with resume
      t=${tries[$key]:-0}
      if [ "$t" -ge 2 ]; then log "GIVING UP $run ($missing folds missing, exit $code)"; continue; fi
      tries[$key]=$((t + 1)); newrun=$key-r$((t + 1))
      log "relaunch $run as $newrun ($missing folds missing, exit $code)"
      timeout 400 modal run --detach scripts/modal/app.py::main --spawn --run-id "$newrun" --timeout-h 4 \
        --cmd "$PRE && PRC_HOLDOUTS=$g PRC_RESUME=1 python -m prc.models.gbm validate --config $CAT --seeds $s --exp-id $e" \
        2>&1 | grep -E "budget|spawned|refus"
      curr[$key]=$newrun   # follow the relaunch from now on
      pending=$((pending + 1))
    done
  done
  n=$(grep -c "EXP-14[0-4]_" <<< "$have")
  log "CatBoost folds with sidecar: $n/60; groups still running: $pending"
  [ "$n" -ge 60 ] && break
  [ "$pending" -eq 0 ] && { log "nothing running and folds missing — stopping"; echo failed > logs/modal/fullyear_orchestrate.done; exit 1; }
  sleep 300
done

log "all 60 CatBoost folds present; launching the chain on Modal"
CMD="$PRE"
for sx in $SEEDS; do s=${sx%:*}; e=EXP-${sx#*:}
  CMD="$CMD && PRC_HOLDOUTS=all PRC_RESUME=1 python -m prc.models.gbm validate --config $CAT --seeds $s --exp-id $e"
done
CMD="$CMD && make PY=python fullyear-chain"
for try in 1 2 3; do
  out=$(timeout 400 modal run --detach scripts/modal/app.py::main --spawn --run-id fy-chain-1 --timeout-h 1.5 --cmd "$CMD" 2>&1)
  echo "$out" | grep -E "budget|spawned|refus"
  echo "$out" | grep -q spawned && break
  sleep 30
done
until modal volume ls prc2026-data runs/fy-chain-1 2>/dev/null | grep -q exit_code; do sleep 120; done
code=$(modal volume get prc2026-data runs/fy-chain-1/exit_code - 2>/dev/null | head -c 1)
log "chain exit $code; syncing outputs"
for r in fy-chain-1 fy-lgb-np-s42 fy-lgb-np-s7 fy-lgb-np-s99 fy-lgb-np-s11 fy-lgb-np-s23; do
  uv run --frozen python scripts/modal/sync.py "$r" || log "sync $r failed"
done
echo "exit $code" > logs/modal/fullyear_orchestrate.done
log done
