#!/usr/bin/env bash
set -euo pipefail

# Build cumulative complexity-ordered datasets from the full cleaned 2700-pair
# validsyntax CSV. This runs after run0b and before run1.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
PREFIX="${PREFIX:-codesearchnet_${MODEL_NAME}_python}"
SIZES="${SIZES:-500,1000,1500,2000,2500}"

INPUT_CSV="${INPUT_CSV:-code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax/${PREFIX}_merged_2700.csv}"
OUT_DIR="${OUT_DIR:-code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_complexity_sweep}"

TREE_SITTER_LIB="${TREE_SITTER_LIB:-code-analyzer-tree-sitter/build/my-languages.so}"
AST_HELPER_DIR="${AST_HELPER_DIR:-code-analyzer-tree-sitter}"

echo "============================================================"
echo " run0d-build-complexity-sweep-pairs.sh"
echo "   model name      : ${MODEL_NAME}"
echo "   input csv       : ${INPUT_CSV}"
echo "   output dir      : ${OUT_DIR}"
echo "   prefix          : ${PREFIX}"
echo "   sizes           : ${SIZES}"
echo "   tree-sitter lib : ${TREE_SITTER_LIB}"
echo "   ast helper dir  : ${AST_HELPER_DIR}"
echo "============================================================"

python code-generation/build_complexity_sweep_pairs.py \
  --input-csv "${INPUT_CSV}" \
  --out-dir "${OUT_DIR}" \
  --prefix "${PREFIX}" \
  --sizes "${SIZES}" \
  --tree-sitter-lib "${TREE_SITTER_LIB}" \
  --ast-helper-dir "${AST_HELPER_DIR}"
