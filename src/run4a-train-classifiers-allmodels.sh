#!/usr/bin/env bash
set -u
set -o pipefail

# Run all available ML model families for CodeSearchNet RQ2-D.
# This script lives in src/ and can be launched from anywhere.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$REPO_ROOT" || exit 1

TS="$(date +'%Y%m%d_%H%M%S')"
LOGDIR="src/logs/rq2d_codesearchnet_allmodels_${TS}"
mkdir -p "$LOGDIR"

SUMMARY="$LOGDIR/model_run_summary_${TS}.tsv"
echo -e "model\tstatus\tstart_time\tend_time\tseconds\tlog_file" > "$SUMMARY"

echo "============================================================"
echo " run4a-train-classifiers-allmodels.sh"
echo "   script dir : $SCRIPT_DIR"
echo "   repo root  : $REPO_ROOT"
echo "   log dir    : $LOGDIR"
echo "   summary    : $SUMMARY"
echo "============================================================"

MODELS="lr svm mlp rf gb knn dt"

if python - <<'PY'
try:
    import xgboost
except ImportError:
    raise SystemExit(1)
PY
then
  MODELS="$MODELS xgb"
else
  echo "[INFO] xgboost not installed; skipping xgb"
fi

echo "Models: $MODELS"
echo

{
  echo "============================================================"
  echo "Data check"
  echo "Started: $(date -Is)"
  echo "Repo root: $(pwd)"
  echo "============================================================"
  find src/ml_embeddings/data_codesearchnet/splits -maxdepth 2 -type f | sort
  echo
  echo "Finished: $(date -Is)"
} 2>&1 | tee "$LOGDIR/data_check_${TS}.log"

for m in $MODELS; do
  MODEL_TS="$(date +'%Y%m%d_%H%M%S')"
  MODEL_LOG="$LOGDIR/run4_${m}_${MODEL_TS}.log"
  START_ISO="$(date -Is)"
  START_SEC="$(date +%s)"

  echo "============================================================"
  echo "Running model: $m"
  echo "Started: $START_ISO"
  echo "Log: $MODEL_LOG"
  echo "============================================================"

  if MODEL="$m" N_ITER=30 CV=5 bash src/run4-train-classifiers.sh 2>&1 | tee "$MODEL_LOG"; then
    STATUS="OK"
  else
    STATUS="FAIL"
  fi

  END_ISO="$(date -Is)"
  END_SEC="$(date +%s)"
  ELAPSED="$((END_SEC - START_SEC))"

  echo -e "${m}\t${STATUS}\t${START_ISO}\t${END_ISO}\t${ELAPSED}\t${MODEL_LOG}" >> "$SUMMARY"

  echo "Finished model: $m"
  echo "Status: $STATUS"
  echo "Elapsed seconds: $ELAPSED"
  echo
done

echo "============================================================"
echo "All done"
echo "Log dir: $LOGDIR"
echo "Summary: $SUMMARY"
echo "============================================================"
cat "$SUMMARY"