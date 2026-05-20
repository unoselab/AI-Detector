#!/usr/bin/env bash
set -euo pipefail

# Run from repo src/ directory, or from anywhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${PYTHON:-python}"

MODEL_DIR="output/CodeSearchNet/starcoder2-7b-3000-tp0.2"
INPUT_FILE="${MODEL_DIR}/outputs-512token.txt"
OUT_DIR="code-analyzer-tree-sitter/data_temp1_codesearchnet/validsyntax/"

N_SMALL="${N_SMALL:-400}"
N_LARGE="${N_LARGE:-2250}"
SEED="${SEED:-42}"

echo "============================================================"
echo " run0b-find-validsyntax-mgc.sh"
echo "   input   : ${INPUT_FILE}"
echo "   out dir : ${OUT_DIR}"
echo "   n-small : ${N_SMALL}"
echo "   n-large : ${N_LARGE}"
echo "   seed    : ${SEED}"
echo "============================================================"

"${PYTHON}" code-generation/find_validsyntax_mgc.py \
  --input "${INPUT_FILE}" \
  --ai-detector-data-temp "${OUT_DIR}" \
  --n-small "${N_SMALL}" \
  --n-large "${N_LARGE}" \
  --seed "${SEED}"