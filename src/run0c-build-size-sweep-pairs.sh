#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
PREFIX="codesearchnet_${MODEL_NAME}_python"
SIZES="${SIZES:-500,1000,1500,2000,2500}"
SEED="${SEED:-42}"

INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax/${PREFIX}_merged_2700.csv"
OUTPUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_size_sweep"

python code-generation/build_size_sweep_pairs.py \
  --input-csv "${INPUT_CSV}" \
  --output-dir "${OUTPUT_DIR}" \
  --prefix "${PREFIX}" \
  --sizes "${SIZES}" \
  --seed "${SEED}"