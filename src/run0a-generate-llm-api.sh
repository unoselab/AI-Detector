#!/usr/bin/env bash
# =============================================================================
# run0a-generate-llm-api.sh
# -----------------------------------------------------------------------------
# Generation stage for OpenAI-compatible chat LLMs on CodeSearchNet (Path C).
#
# How this differs from run0a-generate_starcoder15b.sh
#   * Uses a remote OpenAI-compatible /v1/chat/completions endpoint instead of
#     loading a local Hugging Face model.
#   * Keeps Path C prompting: feeds the function signature + docstring as a
#     natural-language instruction and asks the chat model to write only the
#     function body.
#   * Uses code-generate-llm/generate.py and writes prompt/output/solution JSONL
#     in the same downstream shape expected by find_validsyntax_mgc.py.
#
# Why
#   The ICSE 2025 paper's RQ2 ChatGPT/Gemini results are based on chat models
#   doing instruction-following code generation. This script provides the same
#   style for API-served GPT-like models before syntax filtering and embedding.
#
# Defaults
#   Pilot mode: 10 samples. Inspect outputs before scaling.
#   For larger runs, set GEN_MAX_NUM=3000 or GEN_MAX_NUM=5000.
#
# Usage
#   OPENAI_API_KEY=... bash src/code-generate-llm/run0a-generate-llm-api.sh
#   OPENAI_API_KEY=... GEN_MAX_NUM=3000 bash src/code-generate-llm/run0a-generate-llm-api.sh
#   OPENAI_API_KEY=... GEN_MODEL=gpt-oss GEN_TEMPERATURE=0.0 bash src/code-generate-llm/run0a-generate-llm-api.sh
# =============================================================================

set -euo pipefail

# Resolve repository paths robustly whether this script is run from repo root,
# src/, or another working directory. This script is intended to live at:
#   src/code-generate-llm/run0a-generate-llm-api.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SRC_DIR}/.." && pwd)"

cd "${SRC_DIR}"
mkdir -p logs

# =====================================================================
# Configuration
# =====================================================================

DATA_PATH="${DATA_PATH:-../data}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${SRC_DIR}/output}"
DATASET_NAME="${DATASET_NAME:-CodeSearchNet}"

# OpenAI-compatible API configuration.
API_KEY_ENV="${API_KEY_ENV:-OPENAI_API_KEY}"
API_URL="${API_URL:-https://ellm.nrp-nautilus.io/v1/chat/completions}"
GEN_MODEL="${GEN_MODEL:-gpt-oss}"

# Pilot defaults to 10; override to 3000/5000 for full runs.
GEN_MAX_NUM="${GEN_MAX_NUM:-10}"
GEN_TEMPERATURE="${GEN_TEMPERATURE:-0.0}"
GEN_MAX_LENGTH="${GEN_MAX_LENGTH:-512}"
GEN_LANGUAGE="${GEN_LANGUAGE:-python}"
GEN_TOP_P="${GEN_TOP_P:-}"
GEN_TIMEOUT="${GEN_TIMEOUT:-120}"
GEN_RETRIES="${GEN_RETRIES:-2}"
GEN_SEED="${GEN_SEED:-42}"

# Keep logs filesystem-safe when model names contain slashes/colons.
GEN_MODEL_LABEL="${GEN_MODEL//\//_}"
GEN_MODEL_LABEL="${GEN_MODEL_LABEL//:/-}"
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_FILE="${LOG_FILE:-logs/generate_${GEN_MODEL_LABEL}_api_csn_t${GEN_TEMPERATURE}_n${GEN_MAX_NUM}_${TS}.log}"

if [ -z "${!API_KEY_ENV:-}" ]; then
  echo "[ERROR] Missing API key environment variable: ${API_KEY_ENV}" >&2
  echo "        Example: OPENAI_API_KEY=... bash src/code-generate-llm/run0a-generate-llm-api.sh" >&2
  exit 1
fi

# Optional arguments.
EXTRA_ARGS=()
if [ -n "${GEN_TOP_P}" ]; then
  EXTRA_ARGS+=(--top_p "${GEN_TOP_P}")
fi

# =====================================================================
# Run
# =====================================================================

{
  echo "=== Generation configuration (OpenAI-compatible API) ==="
  echo "  Started:        $(date -Is)"
  echo "  Dataset:        ${DATASET_NAME}"
  echo "  Language:       ${GEN_LANGUAGE}"
  echo "  API URL:        ${API_URL}"
  echo "  API key env:    ${API_KEY_ENV}"
  echo "  Model label:    ${GEN_MODEL}"
  echo "  Max samples:    ${GEN_MAX_NUM}   (set GEN_MAX_NUM=3000 for full run)"
  echo "  Temperature:    ${GEN_TEMPERATURE}"
  echo "  Max new tokens: ${GEN_MAX_LENGTH}"
  echo "  Top-p:          ${GEN_TOP_P:-<model default>}"
  echo "  Timeout:        ${GEN_TIMEOUT}"
  echo "  Retries:        ${GEN_RETRIES}"
  echo "  Seed:           ${GEN_SEED}"
  echo "  Log file:       ${LOG_FILE}"
  echo "  Output root:    ${OUTPUT_ROOT}"
  echo "========================================================"
  echo ""
} | tee "${LOG_FILE}"

python code-generate-llm/generate.py \
    --path "${DATA_PATH}/${DATASET_NAME}" \
    --language "${GEN_LANGUAGE}" \
    --model_name "${GEN_MODEL}" \
    --api-url "${API_URL}" \
    --api-key-env "${API_KEY_ENV}" \
    --max_num "${GEN_MAX_NUM}" \
    --temperature "${GEN_TEMPERATURE}" \
    --max_length "${GEN_MAX_LENGTH}" \
    --timeout "${GEN_TIMEOUT}" \
    --retries "${GEN_RETRIES}" \
    --seed "${GEN_SEED}" \
    --output-root "${OUTPUT_ROOT}" \
    "${EXTRA_ARGS[@]}" \
    2>&1 | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "=== Pilot inspection checklist ===" | tee -a "${LOG_FILE}"
# Mirror Python's safe_model_label: strip path prefix, then replace ':' with '-'.
# Without the colon swap, tagged models like 'gpt-oss:7b' would print a path
# that doesn't actually exist on disk.
_GEN_MODEL_TAIL="${GEN_MODEL##*/}"
_GEN_MODEL_FS="${_GEN_MODEL_TAIL//:/-}"
DATA_OUT_DIR="${DATA_OUT_DIR:-code-analyzer-tree-sitter/data_codesearchnet/${_GEN_MODEL_FS}/validsyntax}"

OUTPUT_DIR="${OUTPUT_ROOT}/${DATASET_NAME}/${_GEN_MODEL_FS}-${GEN_MAX_NUM}-tp${GEN_TEMPERATURE}"
echo " 1. Open the human-readable companion file:" | tee -a "${LOG_FILE}"
echo "      ${OUTPUT_DIR}/outputs-${GEN_MAX_LENGTH}token_v2.txt" | tee -a "${LOG_FILE}"
echo " 2. Verify in the first 10-20 samples:" | tee -a "${LOG_FILE}"
echo "    - Output is only the function body continuation, not prose" | tee -a "${LOG_FILE}"
echo "    - No leftover triple-backtick python fences or repeated def/class signature" | tee -a "${LOG_FILE}"
echo "    - prompt + output is syntactically valid Python" | tee -a "${LOG_FILE}"
echo " 3. If issues are widespread, tighten build_messages() or extract_body()" | tee -a "${LOG_FILE}"
echo "    in code-generate-llm/generate.py before scaling." | tee -a "${LOG_FILE}"
echo " 4. Once outputs look good, run downstream syntax validation:" | tee -a "${LOG_FILE}"
echo "      python code-generation/find_validsyntax_mgc.py \\" | tee -a "${LOG_FILE}"
echo "        --input ${OUTPUT_DIR}/outputs-${GEN_MAX_LENGTH}token.txt \\" | tee -a "${LOG_FILE}"
echo "        --data-out-dir ${DATA_OUT_DIR} \\" | tee -a "${LOG_FILE}"
echo "        --prefix codesearchnet_${_GEN_MODEL_FS}_python" | tee -a "${LOG_FILE}"