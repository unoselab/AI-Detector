#!/usr/bin/env bash
set -euo pipefail

# Build nested train-size splits with the same fixed dev/test pairs.
# This replaces run3 only for paper-ready size/complexity comparisons.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
PREFIX="${PREFIX:-codesearchnet_${MODEL_NAME}_python}"
SIZES="${SIZES:-500,1000,1500,2000,2500}"
SEED="${SEED:-42}"
DEV_PAIRS="${DEV_PAIRS:-100}"
TEST_PAIRS="${TEST_PAIRS:-100}"
ORDER_MODE="${ORDER_MODE:-random}"

INPUT_CSV="${INPUT_CSV:-ml_embeddings/data_codesearchnet/embeddings/${MODEL_NAME}_maxlen2048_baseline/${PREFIX}_merged_2700.csv}"

if [ "${ORDER_MODE}" = "complexity" ]; then
  DEFAULT_OUT="ml_embeddings/data_codesearchnet/splits/${MODEL_NAME}_complexity_fixedtest_maxlen2048"
else
  DEFAULT_OUT="ml_embeddings/data_codesearchnet/splits/${MODEL_NAME}_size_fixedtest_maxlen2048"
fi

OUT_DIR="${OUT_DIR:-${DEFAULT_OUT}}"

COMPLEXITY_REPORT="${COMPLEXITY_REPORT:-code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_complexity_sweep/${PREFIX}_complexity_sweep_candidate_report.csv}"

echo "============================================================"
echo " run3b-split-fixed-eval-data.sh"
echo "   model name       : ${MODEL_NAME}"
echo "   input csv        : ${INPUT_CSV}"
echo "   output dir       : ${OUT_DIR}"
echo "   prefix           : ${PREFIX}"
echo "   sizes            : ${SIZES}"
echo "   dev pairs        : ${DEV_PAIRS}"
echo "   test pairs       : ${TEST_PAIRS}"
echo "   seed             : ${SEED}"
echo "   order mode       : ${ORDER_MODE}"
echo "   complexity report: ${COMPLEXITY_REPORT}"
echo "============================================================"

ARGS=(
  --input-csv "${INPUT_CSV}"
  --output-dir "${OUT_DIR}"
  --prefix "${PREFIX}"
  --sizes "${SIZES}"
  --dev-pairs "${DEV_PAIRS}"
  --test-pairs "${TEST_PAIRS}"
  --seed "${SEED}"
  --order-mode "${ORDER_MODE}"
)

if [ "${ORDER_MODE}" = "complexity" ]; then
  ARGS+=(--complexity-report "${COMPLEXITY_REPORT}")
fi

python ml_embeddings/split_fixed_eval.py "${ARGS[@]}"
