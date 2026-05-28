#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# run3c-split-complexity-stratified.sh
#
# Build a complexity-balanced train/dev/test split from a
# ABC-pair embedding CSV and its pair-level complexity report.
#
# Default split:
#   4,500 pairs total
#   block size = 10
#   train/dev/test per block = 8/1/1
#   train = 3,600 pairs
#   dev   =   450 pairs
#   test  =   450 pairs
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

MODEL_NAME="${MODEL_NAME:-starcoder2-7b}"
PREFIX="${PREFIX:-codesearchnet_${MODEL_NAME}_python}"
EXP_NAME="${EXP_NAME:-${MODEL_NAME}_4500_complexity_stratified_maxlen2048}"

SEED="${SEED:-42}"
BLOCK_SIZE="${BLOCK_SIZE:-10}"
TRAIN_PER_BLOCK="${TRAIN_PER_BLOCK:-8}"
DEV_PER_BLOCK="${DEV_PER_BLOCK:-1}"

INPUT_CSV="${INPUT_CSV:-ml_embeddings/data_codesearchnet/embeddings/${MODEL_NAME}_maxlen2048_baseline/${PREFIX}_merged_4500.csv}"
COMPLEXITY_REPORT="${COMPLEXITY_REPORT:-code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity/${PREFIX}_complexity_sweep_candidate_report.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-ml_embeddings/data_codesearchnet/splits/${EXP_NAME}}"
DATASET_NAME="${DATASET_NAME:-${PREFIX}_merged_4500}"

echo "============================================================"
echo " run3c-split-complexity-stratified.sh"
echo "   model name       : ${MODEL_NAME}"
echo "   prefix           : ${PREFIX}"
echo "   experiment name  : ${EXP_NAME}"
echo "   input csv        : ${INPUT_CSV}"
echo "   complexity report: ${COMPLEXITY_REPORT}"
echo "   output dir       : ${OUTPUT_DIR}"
echo "   dataset name     : ${DATASET_NAME}"
echo "   seed             : ${SEED}"
echo "   block size       : ${BLOCK_SIZE}"
echo "   allocation       : train=${TRAIN_PER_BLOCK}, dev=${DEV_PER_BLOCK}, test=$((BLOCK_SIZE - TRAIN_PER_BLOCK - DEV_PER_BLOCK))"
echo "============================================================"

python ml_embeddings/split_complexity_stratified.py \
  --input-csv "${INPUT_CSV}" \
  --complexity-report "${COMPLEXITY_REPORT}" \
  --output-dir "${OUTPUT_DIR}" \
  --dataset-name "${DATASET_NAME}" \
  --seed "${SEED}" \
  --block-size "${BLOCK_SIZE}" \
  --train-per-block "${TRAIN_PER_BLOCK}" \
  --dev-per-block "${DEV_PER_BLOCK}"
