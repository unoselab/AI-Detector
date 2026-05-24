#!/usr/bin/env bash
set -euo pipefail

# Select a quality-controlled N-pair dataset after run1-ast-generator.sh.
#
# Usage:
#   ./run1b-select-quality-pairs.sh
#   N_PAIRS=600 ./run1b-select-quality-pairs.sh
#   MAX_AST_TOKENS=1024 ./run1b-select-quality-pairs.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}/src"

MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
N_PAIRS="${N_PAIRS:-400}"
MAX_AST_TOKENS="${MAX_AST_TOKENS:-2048}"
MIN_AST_TOKENS="${MIN_AST_TOKENS:-80}"
MAX_CODE_LINES="${MAX_CODE_LINES:-120}"
MAX_PAIR_TOKEN_RATIO="${MAX_PAIR_TOKEN_RATIO:-2.5}"
SEED="${SEED:-42}"

DATASET_TAG="${DATASET_TAG:-quality${N_PAIRS}}"
PREFIX="codesearchnet_${MODEL_NAME}_python"

SELECTOR="ml_embeddings/select_quality_pairs.py"

INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/ast/${PREFIX}_merged_2700.csv"
OUT_AST_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/ast_${DATASET_TAG}"
OUT_VALIDSYNTAX_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_${DATASET_TAG}"

TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-logs}"
LOG_FILE="${LOG_DIR}/run1b-select-quality-pairs_${DATASET_TAG}_${TS}.log"
mkdir -p "${LOG_DIR}"

if [ ! -f "${SELECTOR}" ]; then
  echo "[ERROR] selector script not found: ${SELECTOR}" >&2
  exit 1
fi

if [ ! -f "${INPUT_CSV}" ]; then
  echo "[ERROR] input CSV not found: ${INPUT_CSV}" >&2
  exit 1
fi

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "============================================================"
echo " run1b-select-quality-pairs.sh"
echo "   repo root             : ${REPO_ROOT}"
echo "   model name            : ${MODEL_NAME}"
echo "   input csv             : ${INPUT_CSV}"
echo "   output AST dir        : ${OUT_AST_DIR}"
echo "   output validsyntax dir: ${OUT_VALIDSYNTAX_DIR}"
echo "   prefix                : ${PREFIX}"
echo "   dataset tag           : ${DATASET_TAG}"
echo "   n pairs               : ${N_PAIRS}"
echo "   min AST tokens        : ${MIN_AST_TOKENS}"
echo "   max AST tokens        : ${MAX_AST_TOKENS}"
echo "   max code lines        : ${MAX_CODE_LINES}"
echo "   max pair token ratio  : ${MAX_PAIR_TOKEN_RATIO}"
echo "   seed                  : ${SEED}"
echo "   log file              : ${LOG_FILE}"
echo "============================================================"
echo

python "${SELECTOR}" \
  --input-csv "${INPUT_CSV}" \
  --out-ast-dir "${OUT_AST_DIR}" \
  --out-validsyntax-dir "${OUT_VALIDSYNTAX_DIR}" \
  --prefix "${PREFIX}" \
  --n-pairs "${N_PAIRS}" \
  --dataset-tag "${DATASET_TAG}" \
  --max-ast-tokens "${MAX_AST_TOKENS}" \
  --min-ast-tokens "${MIN_AST_TOKENS}" \
  --max-code-lines "${MAX_CODE_LINES}" \
  --max-pair-token-ratio "${MAX_PAIR_TOKEN_RATIO}" \
  --seed "${SEED}" \
  --write-candidate-report

echo
echo "Done."
echo "Outputs:"
echo "  AST CSV dir        : ${OUT_AST_DIR}"
echo "  Validsyntax CSV dir: ${OUT_VALIDSYNTAX_DIR}"
echo "  Log file           : ${LOG_FILE}"