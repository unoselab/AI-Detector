#!/usr/bin/env bash
set -euo pipefail

# Plot threshold-sweep curves.
#
# Default:
#   - StarCoder2-15B-Instruct
#   - SVM
#   - 400-pair dataset
#   - AST embedding
#   - test split
#   - AI precision / recall / F1 plot
#
# Examples:
#   ./run6-plot-threshold-curve.sh
#   DATASET_SIZE=2250 ./run6-plot-threshold-curve.sh
#   SPLIT=both ./run6-plot-threshold-curve.sh
#   PLOT=single METRIC=ai_f1 SPLIT=both ./run6-plot-threshold-curve.sh
#   MODEL_NAME=starcoder2-7b CLASSIFIER=svm DATASET_SIZE=2250 ./run6-plot-threshold-curve.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
CLASSIFIER="${CLASSIFIER:-svm}"
EMB="${EMB:-ast_}"

# 400 or 2250. Used only when DATASET is not explicitly provided.
DATASET_SIZE="${DATASET_SIZE:-400}"

# Plot mode:
#   ai-prf  = AI precision, AI recall, AI F1 together
#   single  = one metric only, controlled by METRIC
PLOT="${PLOT:-ai-prf}"
METRIC="${METRIC:-ai_f1}"

# For report figures, use test.
# For debugging, use both.
SPLIT="${SPLIT:-test}"

BASE_DIR="data_codesearchnet/threshold_sweep/${MODEL_NAME}"
CSV="${CSV:-${BASE_DIR}/${CLASSIFIER}_summary_detail.csv}"
SUMMARY_CSV="${SUMMARY_CSV:-${BASE_DIR}/${CLASSIFIER}_summary.csv}"

if [ -z "${DATASET:-}" ]; then
  if [ "${DATASET_SIZE}" = "2250" ]; then
    DATASET="codesearchnet_${MODEL_NAME}_python_merged_2250"
  else
    DATASET="codesearchnet_${MODEL_NAME}_python_merged"
  fi
fi

cd "${TARGET_DIR}"

if [ ! -f "plot_threshold_curve.py" ]; then
  echo "[ERROR] plot_threshold_curve.py not found in ${TARGET_DIR}" >&2
  exit 1
fi

if [ ! -f "${CSV}" ]; then
  echo "[ERROR] detail CSV not found: ${TARGET_DIR}/${CSV}" >&2
  exit 1
fi

if [ ! -f "${SUMMARY_CSV}" ]; then
  echo "[WARN] summary CSV not found: ${TARGET_DIR}/${SUMMARY_CSV}" >&2
  echo "       Plot will run without dev-selected threshold line." >&2
  SUMMARY_ARG=()
else
  SUMMARY_ARG=(--summary-csv "${SUMMARY_CSV}")
fi

OUT_ARG=()
if [ -n "${OUT:-}" ]; then
  OUT_ARG=(--out "${OUT}")
fi

echo "============================================================"
echo " run6-plot-threshold-curve.sh"
echo "   target dir  : ${TARGET_DIR}"
echo "   model name  : ${MODEL_NAME}"
echo "   classifier  : ${CLASSIFIER}"
echo "   dataset     : ${DATASET}"
echo "   emb         : ${EMB}"
echo "   plot        : ${PLOT}"
echo "   metric      : ${METRIC}"
echo "   split       : ${SPLIT}"
echo "   detail csv  : ${CSV}"
echo "   summary csv : ${SUMMARY_CSV}"
echo "============================================================"
echo

python plot_threshold_curve.py \
  --csv "${CSV}" \
  "${SUMMARY_ARG[@]}" \
  --dataset "${DATASET}" \
  --emb "${EMB}" \
  --plot "${PLOT}" \
  --metric "${METRIC}" \
  --split "${SPLIT}" \
  "${OUT_ARG[@]}"
