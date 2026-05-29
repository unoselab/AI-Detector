#!/bin/bash
# Run from inside a tmux session.
# Additional generation: 2000 MORE CodeLlama-7B samples on CodeSearchNet @ T=0.2,
# disjoint from the existing 7000-sample batch, then merged for run0b.
#
# Why 2000: current run0b reports paired_valid = 4165 at paired_valid_rate ~= 0.595.
# Target is 4500 paired-valid. 2000 new raw * 0.595 ~= 1190 new paired-valid,
# giving ~5355 total -- a safe buffer over 4500.

set -euo pipefail

cd ~/project-workspace/ai_detector/src

mkdir -p logs
export CUDA_VISIBLE_DEVICES=0

# =====================================================================
# Configuration  (match the original CodeLlama-7B run)
# =====================================================================
DATA_PATH="../data"
DATASET_NAME="CodeSearchNet"
GEN_MODEL="CodeLlama-7b-hf"
GEN_MODEL_HF="codellama/CodeLlama-7b-hf"

GEN_TEMPERATURE=0.2
GEN_MAX_LENGTH=512          # same generation length as the first 7000 batch
GEN_BATCH_SIZE=1
SEED=42

ADD_NUM=2000                # additional raw samples to generate

# Existing batch to exclude + merge against.
EXISTING_DIR="output/${DATASET_NAME}/${GEN_MODEL}-7000-tp${GEN_TEMPERATURE}"
EXISTING_FILE="${EXISTING_DIR}/outputs.txt"

# Merged output (existing 7000 + new 2000 = 9000) for run0b to read directly.
COMBINED_DIR="output/${DATASET_NAME}/${GEN_MODEL}-9000-tp${GEN_TEMPERATURE}"
COMBINED_FILE="${COMBINED_DIR}/outputs.txt"

LOG_FILE="logs/generate_${GEN_MODEL}_csn_t02_additional_n${ADD_NUM}.log"

# =====================================================================
echo "=== Additional generation configuration ==="
echo "  HF model:        ${GEN_MODEL_HF}"
echo "  Additional num:  ${ADD_NUM}"
echo "  Exclude file:    ${EXISTING_FILE}"
echo "  Combined out:    ${COMBINED_FILE}"
echo "  Temperature:     ${GEN_TEMPERATURE}"
echo "  Max length:      ${GEN_MAX_LENGTH}"
echo "  Seed:            ${SEED}"
echo "==========================================="
echo ""

if [[ ! -f "${EXISTING_FILE}" ]]; then
  echo "[ERROR] existing batch not found: ${EXISTING_FILE}" >&2
  exit 1
fi

python code-generation/generate.py \
    --path "${DATA_PATH}/${DATASET_NAME}" \
    --model_name "${GEN_MODEL_HF}" \
    --max_num "${ADD_NUM}" \
    --temperature "${GEN_TEMPERATURE}" \
    --max_length "${GEN_MAX_LENGTH}" \
    --batch_size "${GEN_BATCH_SIZE}" \
    --seed "${SEED}" \
    --exclude_file "${EXISTING_FILE}" \
    --combined_out "${COMBINED_FILE}" \
    2>&1 | tee "${LOG_FILE}"

echo ""
echo "Merged file ready: ${COMBINED_FILE}"
echo "Line count:"
wc -l "${COMBINED_FILE}"

echo ""
echo "Next, validate the merged batch (expects >= 4500 paired-valid):"
echo "  MODEL_NAME=${GEN_MODEL} \\"
echo "  MODEL_DIR=${COMBINED_DIR} \\"
echo "  INPUT_FILE=${COMBINED_FILE} \\"
echo "  PREFIX=codesearchnet_codellama-7b_python \\"
echo "  N_SMALL=400 N_LARGE=4500 SEED=42 \\"
echo "  bash run0b-find-validsyntax-mgc.sh"
