#!/bin/bash
# =============================================================================
# run0a-generate_starcoder15b.sh
# -----------------------------------------------------------------------------
# Generation stage for StarCoder2-15B-Instruct-v0.1 on CodeSearchNet (Path C).
#
# How this differs from run0a-generate.sh
#   * Uses instruction-tuned model (15B-Instruct) instead of base (7B).
#   * Path C prompting: feeds the docstring as a natural-language instruction
#     ("Write a Python function that ..."), not a code prefix.
#   * Uses generate_starcoder15b.py (chat template + bf16 + ### terminator)
#     instead of generate.py.
#
# Why
#   The paper's RQ2 ChatGPT/Gemini results are on chat models doing
#   instruction-following code generation. To compare detectability of
#   instruction-tuned vs base code LLMs on equal footing, we must use the
#   same prompting style the paper used. This script implements that.
#
# Defaults
#   Pilot mode: 200 samples. Inspect outputs before scaling.
#   For the full run, set GEN_MAX_NUM=3000 (matches the StarCoder2-7B run).
#
# Usage
#   bash src/run0a-generate_starcoder15b.sh                 # pilot (200 samples)
#   GEN_MAX_NUM=3000 bash src/run0a-generate_starcoder15b.sh   # full run
# =============================================================================

set -euo pipefail

cd ~/project-workspace/ai_detector/src

mkdir -p logs

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

# =====================================================================
# Configuration
# =====================================================================

DATA_PATH="${DATA_PATH:-../data}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${HOME}/project-workspace/ai_detector/src/output}"
DATASET_NAME="${DATASET_NAME:-CodeSearchNet}"
GEN_MODEL="${GEN_MODEL:-starcoder2-15b-instruct-v0.1}"
GEN_MODEL_HF="${GEN_MODEL_HF:-bigcode/starcoder2-15b-instruct-v0.1}"

# Pilot defaults to 200; override to 3000 for full run.
#GEN_MAX_NUM="${GEN_MAX_NUM:-3000}"
GEN_MAX_NUM="${GEN_MAX_NUM:-5000}"  # msong 2026-05-24 more data for 500, 1000, 1500, 2000, 2500, 3000
GEN_TEMPERATURE="${GEN_TEMPERATURE:-0.2}"
GEN_MAX_LENGTH="${GEN_MAX_LENGTH:-512}"

LOG_FILE="logs/generate_${GEN_MODEL}_csn_t${GEN_TEMPERATURE}_n${GEN_MAX_NUM}.log"

# =====================================================================
# Run
# =====================================================================

echo "=== Generation configuration (instruction-tuned) ==="
echo "  Dataset:        ${DATASET_NAME}"
echo "  HF model:       ${GEN_MODEL_HF}"
echo "  Model label:    ${GEN_MODEL}"
echo "  Max samples:    ${GEN_MAX_NUM}   (set GEN_MAX_NUM=3000 for full run)"
echo "  Temperature:    ${GEN_TEMPERATURE}"
echo "  Max new tokens: ${GEN_MAX_LENGTH}"
echo "  CUDA device:    ${CUDA_VISIBLE_DEVICES}"
echo "  Log file:       ${LOG_FILE}"
echo "  Output root:    ${OUTPUT_ROOT}"
echo "===================================================="
echo ""

python code-generation/generate_starcoder15b.py \
    --path "${DATA_PATH}/${DATASET_NAME}" \
    --model_name "${GEN_MODEL_HF}" \
    --max_num "${GEN_MAX_NUM}" \
    --temperature "${GEN_TEMPERATURE}" \
    --max_length "${GEN_MAX_LENGTH}" \
    --output-root "${OUTPUT_ROOT}" \
    2>&1 | tee "${LOG_FILE}"

echo ""
echo "=== Pilot inspection checklist ==="
echo " 1. Open the human-readable companion file:"
OUTPUT_DIR="${OUTPUT_ROOT}/${DATASET_NAME}/${GEN_MODEL}-${GEN_MAX_NUM}-tp${GEN_TEMPERATURE}"
echo "      ${OUTPUT_DIR}/outputs-${GEN_MAX_LENGTH}token_v2.txt"
echo " 2. Verify in the first 10-20 samples:"
echo "    - Output starts with 'def ' or 'class ' (not prose)"
echo "    - No leftover triple-backtick python fences or 'Here is a function...' preamble"
echo "    - Code is syntactically valid Python"
echo " 3. If issues are widespread, tighten the prompt or post-processing"
echo "    in generate_starcoder15b.py before scaling to 3000."
