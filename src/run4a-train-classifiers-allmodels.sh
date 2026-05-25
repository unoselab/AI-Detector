#!/usr/bin/env bash
set -u
set -o pipefail

# Run all available ML model families for CodeSearchNet RQ2-D.
# Standalone version: does NOT call run4-train-classifiers.sh.
#
# This avoids split-brain MODEL_NAME bugs where run4a and run4 disagree.
#
# Usage:
#   ./run4a-train-classifiers-allmodels.sh
#   MODEL_NAME=starcoder2-15b-instruct-v0.1_maxlen2048_baseline ./run4a-train-classifiers-allmodels.sh
#   MODEL_NAME=starcoder2-15b-instruct-v0.1_size_sweep_maxlen2048 ./run4a-train-classifiers-allmodels.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

cd "${REPO_ROOT}" || exit 1

N_ITER="${N_ITER:-30}"
CV="${CV:-5}"
SEED="${SEED:-42}"

# msong 2026-05-24
# MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1_size_sweep_maxlen2048}"
MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1_complexity_sweep_maxlen2048}"

PYTHON="${PYTHON:-python}"

SPLITS_DIR="${SPLITS_DIR:-data_codesearchnet/splits/${MODEL_NAME}}"
MODEL_DIR="${MODEL_DIR:-data_codesearchnet/models/${MODEL_NAME}}"
PREDICTIONS_ROOT="${PREDICTIONS_ROOT:-data_codesearchnet/predictions/${MODEL_NAME}}"
EXPERIMENT_TAG="${EXPERIMENT_TAG:-codesearchnet_${MODEL_NAME}}"

MODELS="${MODELS:-lr svm mlp rf gb knn dt}"

TS="$(date +'%Y%m%d_%H%M%S')"
LOGDIR="src/logs/rq2d_codesearchnet_${MODEL_NAME}_allmodels_${TS}"
SUMMARY="$LOGDIR/model_run_summary_${TS}.tsv"

mkdir -p "$LOGDIR"
mkdir -p "${TARGET_DIR}/${MODEL_DIR}" "${TARGET_DIR}/${PREDICTIONS_ROOT}"

echo -e "model_name\tmodel\tstatus\tstart_time\tend_time\tseconds\tlog_file" > "$SUMMARY"

echo "============================================================"
echo " run4a-train-classifiers-allmodels.sh"
echo "   script dir      : $SCRIPT_DIR"
echo "   repo root       : $REPO_ROOT"
echo "   target dir      : $TARGET_DIR"
echo "   model name      : $MODEL_NAME"
echo "   splits dir      : $SPLITS_DIR"
echo "   model dir       : $MODEL_DIR"
echo "   predictions root: $PREDICTIONS_ROOT"
echo "   n_iter          : $N_ITER"
echo "   cv              : $CV"
echo "   seed            : $SEED"
echo "   log dir         : $LOGDIR"
echo "   summary         : $SUMMARY"
echo "============================================================"

cd "${TARGET_DIR}" || exit 1

if [ ! -f "hyperparameter_tuning.py" ]; then
  echo "[ERROR] hyperparameter_tuning.py not found in ${TARGET_DIR}" >&2
  exit 1
fi

if [ ! -f "test_embedding.py" ]; then
  echo "[ERROR] test_embedding.py not found in ${TARGET_DIR}" >&2
  exit 1
fi

if [ ! -d "${SPLITS_DIR}" ]; then
  echo "[ERROR] missing splits dir: ${TARGET_DIR}/${SPLITS_DIR}" >&2
  exit 1
fi

# Optional xgboost.
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

echo
echo "Models: $MODELS"
echo

{
  echo "============================================================"
  echo "Data check"
  echo "Started: $(date -Is)"
  echo "Target dir: $(pwd)"
  echo "Model name: ${MODEL_NAME}"
  echo "Splits dir: ${SPLITS_DIR}"
  echo "============================================================"
  find "${SPLITS_DIR}" -maxdepth 2 -type f | sort
  echo
  echo "Dataset folders:"
  find "${SPLITS_DIR}" -mindepth 1 -maxdepth 1 -type d | sort
  echo
  echo "Finished: $(date -Is)"
} 2>&1 | tee "${REPO_ROOT}/${LOGDIR}/data_check_${TS}.log"

for m in $MODELS; do
  MODEL_TS="$(date +'%Y%m%d_%H%M%S')"
  RUN_TAG="${EXPERIMENT_TAG}_${m}_${MODEL_TS}"
  MODEL_LOG="${REPO_ROOT}/${LOGDIR}/run4_${MODEL_NAME}_${m}_${MODEL_TS}.log"

  PICKLE="${MODEL_DIR}/tuned_models_${RUN_TAG}.pkl"
  PREDICTIONS_DIR="${PREDICTIONS_ROOT}/${RUN_TAG}"

  START_ISO="$(date -Is)"
  START_SEC="$(date +%s)"

  echo "============================================================"
  echo "Running model: $m"
  echo "Model name: $MODEL_NAME"
  echo "Run tag   : $RUN_TAG"
  echo "Started   : $START_ISO"
  echo "Log       : $MODEL_LOG"
  echo "============================================================"

  {
    echo "============================================================"
    echo " run4a standalone model run"
    echo "   model name      : ${MODEL_NAME}"
    echo "   classifier      : ${m}"
    echo "   splits dir      : ${SPLITS_DIR}"
    echo "   tuned pickle    : ${PICKLE}"
    echo "   predictions dir : ${PREDICTIONS_DIR}"
    echo "   n_iter          : ${N_ITER}"
    echo "   cv              : ${CV}"
    echo "   seed            : ${SEED}"
    echo "============================================================"
    echo

    echo "[stage 1/2] tuning ..."
    "${PYTHON}" hyperparameter_tuning.py \
      --splits-dir "${SPLITS_DIR}" \
      --out-pickle "${PICKLE}" \
      --model      "${m}" \
      --n-iter     "${N_ITER}" \
      --cv         "${CV}" \
      --seed       "${SEED}"

    echo
    echo "[stage 2/2] testing ..."
    "${PYTHON}" test_embedding.py \
      --splits-dir      "${SPLITS_DIR}" \
      --models-pickle   "${PICKLE}" \
      --predictions-dir "${PREDICTIONS_DIR}"

  } 2>&1 | tee "$MODEL_LOG"

  PIPE_STATUS=("${PIPESTATUS[@]}")
  if [ "${PIPE_STATUS[0]}" -eq 0 ]; then
    STATUS="OK"
  else
    STATUS="FAIL"
  fi

  END_ISO="$(date -Is)"
  END_SEC="$(date +%s)"
  ELAPSED="$((END_SEC - START_SEC))"

  echo -e "${MODEL_NAME}\t${m}\t${STATUS}\t${START_ISO}\t${END_ISO}\t${ELAPSED}\t${MODEL_LOG}" >> "${REPO_ROOT}/${SUMMARY}"

  echo "Finished model: $m"
  echo "Status: $STATUS"
  echo "Elapsed seconds: $ELAPSED"
  echo

  # Continue to next model even if one fails.
done

cd "${REPO_ROOT}" || exit 1

echo "============================================================"
echo "All done"
echo "Log dir: $LOGDIR"
echo "Summary: $SUMMARY"
echo "============================================================"
cat "$SUMMARY"