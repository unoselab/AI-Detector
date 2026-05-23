#!/usr/bin/env bash
set -euo pipefail

# Build mixed-sample grid in one Python invocation.
# Python handles BLOCKS_PER_SAMPLE iteration internally.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

MODEL_NAME="starcoder2-15b-instruct-v0.1"
DATASET_SIZE="2700"

SRC_CSV="src/code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/ast/codesearchnet_${MODEL_NAME}_python_merged_${DATASET_SIZE}.csv"
SPLITS_DIR="src/ml_embeddings/data_codesearchnet/splits/${MODEL_NAME}/codesearchnet_${MODEL_NAME}_python_merged_${DATASET_SIZE}"

GRID_OUT_ROOT="src/app/data_mixed_samples_grid_480"
GRID_CONFIGS="2:240,4:120,6:80,8:60,10:48"

SEED="42"
LM_RATIO="0.5"
INCLUDE_CORNERS="1"

ALLOW_REUSE="0"
NO_SPLIT_FILTER="0"

TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run0b-build-mixed-samples-grid_${TS}.log}"
mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "============================================================"
echo " run0b-build-mixed-samples-grid.sh"
echo "   model name      : ${MODEL_NAME}"
echo "   dataset size    : ${DATASET_SIZE}"
echo "   src csv         : ${SRC_CSV}"
echo "   splits dir      : ${SPLITS_DIR}"
echo "   grid out root   : ${GRID_OUT_ROOT}"
echo "   grid configs    : ${GRID_CONFIGS}"
echo "   lm ratio        : ${LM_RATIO}"
echo "   include corners : ${INCLUDE_CORNERS}"
echo "   allow reuse     : ${ALLOW_REUSE}"
echo "   no split filter : ${NO_SPLIT_FILTER}"
echo "   log file        : ${LOG_FILE}"
echo "============================================================"
echo

EXTRA_ARGS=(
  --src-csv "${SRC_CSV}"
  --splits-dir "${SPLITS_DIR}"
  --grid-out-root "${GRID_OUT_ROOT}"
  --grid-configs "${GRID_CONFIGS}"
  --seed "${SEED}"
  --lm-ratio "${LM_RATIO}"
  --validate-python
)

if [ "${INCLUDE_CORNERS}" = "1" ]; then
  EXTRA_ARGS+=(--include-corners)
fi

if [ "${ALLOW_REUSE}" = "1" ]; then
  EXTRA_ARGS+=(--allow-reuse)
fi

if [ "${NO_SPLIT_FILTER}" = "1" ]; then
  EXTRA_ARGS+=(--no-split-filter)
fi

python src/app/build_mixed_samples.py "${EXTRA_ARGS[@]}"

echo
echo "============================================================"
echo "Done"
echo "Output root: ${GRID_OUT_ROOT}"
echo "Log file   : ${LOG_FILE}"
echo "============================================================"
