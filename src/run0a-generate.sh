#!/bin/bash
# Run this script from inside a tmux session
# Generation Phase — StarCoder2-7B on CodeSearchNet at T=0.2
#                  - CodeLlama-7B-HF for the first evaluation
# Scaled run: 2000 samples (target ~500 after filter pass rate)

set -euo pipefail

cd ~/project-workspace/ai_detector/src

mkdir -p logs

# =====================================================================
# Configuration
# =====================================================================
DATA_PATH="${DATA_PATH:-../data}"
DATASET_NAME="${DATASET_NAME:-CodeSearchNet}"
GEN_MODEL="${GEN_MODEL:-starcoder2-7b}"
GEN_MODEL_HF="${GEN_MODEL_HF:-bigcode/starcoder2-7b}"
GEN_MAX_NUM="${GEN_MAX_NUM:-7000}"
GEN_TEMPERATURE="${GEN_TEMPERATURE:-0.2}"
GEN_MAX_LENGTH="${GEN_MAX_LENGTH:-512}"
GEN_BATCH_SIZE="${GEN_BATCH_SIZE:-1}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export CUDA_VISIBLE_DEVICES

# The FIRST EVALUATION
# GEN_MODEL_HF="codellama/CodeLlama-7b-hf"
# GEN_MAX_NUM=2000      # ColdLlama used 2000
                        # StarCoder needed 3000
# GEN_MAX_LENGTH=128    # Original value
# 512 used to generate more valid MGC for ai-detector (icse '25)

RUN_TS="$(date +%Y%m%d_%H%M%S)"
TEMP_TAG="${GEN_TEMPERATURE/./}"
LOG_FILE="logs/generate_${GEN_MODEL}_csn_t${TEMP_TAG}_n${GEN_MAX_NUM}_${RUN_TS}.log"

# =====================================================================
# Run
# =====================================================================

echo "=== Generation configuration ==="
echo "  Dataset:        ${DATASET_NAME}"
echo "  HF model:       ${GEN_MODEL_HF}"
echo "  Model label:    ${GEN_MODEL}"
echo "  Max samples:    ${GEN_MAX_NUM}"
echo "  Temperature:    ${GEN_TEMPERATURE}"
echo "  Max length:     ${GEN_MAX_LENGTH}"
echo "  Batch size:     ${GEN_BATCH_SIZE}"
echo "  CUDA device:    ${CUDA_VISIBLE_DEVICES}"
echo "  Log file:       ${LOG_FILE}"
echo "================================"
echo ""

python code-generation/generate.py \
    --path "${DATA_PATH}/${DATASET_NAME}" \
    --model_name "${GEN_MODEL_HF}" \
    --max_num "${GEN_MAX_NUM}" \
    --temperature "${GEN_TEMPERATURE}" \
    --max_length "${GEN_MAX_LENGTH}" \
    --batch_size "${GEN_BATCH_SIZE}" \
    2>&1 | tee "${LOG_FILE}"