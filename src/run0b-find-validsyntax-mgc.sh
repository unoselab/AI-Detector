#!/usr/bin/env bash
set -euo pipefail

# Run from repo src/ directory, or from anywhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${PYTHON:-python}"

# MODEL_DIR="output/CodeSearchNet/starcoder2-7b-3000-tp0.2"
MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
MODEL_DIR="${MODEL_DIR:-output/CodeSearchNet/${MODEL_NAME}-3000-tp0.2}"
INPUT_FILE="${INPUT_FILE:-${MODEL_DIR}/outputs-512token.txt}"
DATA_OUT_DIR="${DATA_OUT_DIR:-code-analyzer-tree-sitter/data_codesearchnet/validsyntax}"
PREFIX="${PREFIX:-codesearchnet_${MODEL_NAME}_python}"

N_SMALL="${N_SMALL:-400}"
N_LARGE="${N_LARGE:-2250}"
SEED="${SEED:-42}"

echo "============================================================"
echo " run0b-find-validsyntax-mgc.sh"
echo "   model        : ${MODEL_NAME}"
echo "   input        : ${INPUT_FILE}"
echo "   data out dir : ${DATA_OUT_DIR}"
echo "   prefix       : ${PREFIX}"
echo "   n-small      : ${N_SMALL}"
echo "   n-large      : ${N_LARGE}"
echo "   seed         : ${SEED}"
echo "============================================================"

"${PYTHON}" code-generation/find_validsyntax_mgc.py \
  --input "${INPUT_FILE}" \
  --data-out-dir "${DATA_OUT_DIR}" \
  --prefix "${PREFIX}" \
  --n-small "${N_SMALL}" \
  --n-large "${N_LARGE}" \
  --seed "${SEED}"