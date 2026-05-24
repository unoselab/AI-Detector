#!/usr/bin/env bash
set -u
set -o pipefail

# Run all available ML model families for CodeSearchNet RQ2-D.
# This script lives in src/ and can be launched from anywhere.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$REPO_ROOT" || exit 1

# MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
# MODEL_NAME="starcoder2-15b-instruct-v0.1_maxlen2048_baseline"
MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1_size_sweep_maxlen2048}"
N_ITER="${N_ITER:-30}"
CV="${CV:-5}"
SEED="${SEED:-42}"

TS="$(date +'%Y%m%d_%H%M%S')"
LOGDIR="src/logs/rq2d_codesearchnet_${MODEL_NAME}_allmodels_${TS}"
mkdir -p "$LOGDIR"

SUMMARY="$LOGDIR/model_run_summary_${TS}.tsv"
echo -e "model_name\tmodel\tstatus\tstart_time\tend_time\tseconds\tlog_file" > "$SUMMARY"

echo "============================================================"
echo " run4a-train-classifiers-allmodels.sh"
echo "   script dir : $SCRIPT_DIR"
echo "   repo root  : $REPO_ROOT"
echo "   model name : $MODEL_NAME"
echo "   n_iter     : $N_ITER"
echo "   cv         : $CV"
echo "   seed       : $SEED"
echo "   log dir    : $LOGDIR"
echo "   summary    : $SUMMARY"
echo "============================================================"

MODELS="${MODELS:-lr svm mlp rf gb knn dt}"

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

SPLITS_DIR="src/ml_embeddings/data_codesearchnet/splits/${MODEL_NAME}"

{
  echo "============================================================"
  echo "Data check"
  echo "Started: $(date -Is)"
  echo "Repo root: $(pwd)"
  echo "Model name: ${MODEL_NAME}"
  echo "Splits dir: ${SPLITS_DIR}"
  echo "============================================================"

  if [ ! -d "$SPLITS_DIR" ]; then
    echo "[ERROR] missing splits dir: $SPLITS_DIR"
    exit 1
  fi

  find "$SPLITS_DIR" -maxdepth 2 -type f | sort
  echo
  echo "Finished: $(date -Is)"
} 2>&1 | tee "$LOGDIR/data_check_${TS}.log"

for m in $MODELS; do
  MODEL_TS="$(date +'%Y%m%d_%H%M%S')"
  MODEL_LOG="$LOGDIR/run4_${MODEL_NAME}_${m}_${MODEL_TS}.log"
  START_ISO="$(date -Is)"
  START_SEC="$(date +%s)"

  echo "============================================================"
  echo "Running model: $m"
  echo "Model name: $MODEL_NAME"
  echo "Started: $START_ISO"
  echo "Log: $MODEL_LOG"
  echo "============================================================"

  if MODEL_NAME="$MODEL_NAME" \
     MODEL="$m" \
     N_ITER="$N_ITER" \
     CV="$CV" \
     SEED="$SEED" \
     bash src/run4-train-classifiers.sh 2>&1 | tee "$MODEL_LOG"; then
    STATUS="OK"
  else
    STATUS="FAIL"
  fi

  END_ISO="$(date -Is)"
  END_SEC="$(date +%s)"
  ELAPSED="$((END_SEC - START_SEC))"

  echo -e "${MODEL_NAME}\t${m}\t${STATUS}\t${START_ISO}\t${END_ISO}\t${ELAPSED}\t${MODEL_LOG}" >> "$SUMMARY"

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
