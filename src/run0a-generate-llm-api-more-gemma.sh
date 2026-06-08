#!/usr/bin/env bash
# =============================================================================
# run0a-generate-llm-api-more-gemma.sh
# -----------------------------------------------------------------------------
# Generate additional valid MGC pairs for the Gemma CodeSearchNet dataset.
#
# This script calls:
#   src/code-generate-llm/generate-more.py
#
# It is the Gemma counterpart of:
#   src/run0a-generate-llm-api-more.sh
#
# Important:
#   generate-more.py currently defaults --out-dir to the gpt-oss validsyntax
#   directory, so this wrapper always passes the Gemma --out-dir explicitly.
#
# Example dry run:
#   DRY_RUN=1 bash src/run0a-generate-llm-api-more-gemma.sh
#
# Example full run, final target of 5000 valid pairs:
#   OPENAI_API_KEY=... TARGET_PAIRS=5000 bash src/run0a-generate-llm-api-more-gemma.sh
#
# Example add exactly 500 new valid pairs, regardless of current valid count:
#   OPENAI_API_KEY=... ADDITIONAL=1 TARGET_PAIRS=500 bash src/run0a-generate-llm-api-more-gemma.sh
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}"
REPO_ROOT="$(cd "${SRC_DIR}/.." && pwd)"

cd "${REPO_ROOT}"
mkdir -p logs

# ---------------------------------------------------------------------
# Configuration
# Override any of these from the command line if needed.
# ---------------------------------------------------------------------

API_KEY_ENV="${API_KEY_ENV:-OPENAI_API_KEY}"
API_URL="${API_URL:-https://ellm.nrp-nautilus.io/v1/chat/completions}"

# Gemma API/model defaults. generate_single_gemma.py uses model=gemma,
# temperature=1.0, top_p=0.95, max_tokens=512.
MODEL_NAME="${MODEL_NAME:-gemma}"
TEMPERATURE="${TEMPERATURE:-0.2}"
TOP_P="${TOP_P:-0.95}"
MAX_TOKENS="${MAX_TOKENS:-512}"
TIMEOUT="${TIMEOUT:-120}"

LANGUAGE="${LANGUAGE:-python}"
CODESEARCHNET_ROOT="${CODESEARCHNET_ROOT:-data/CodeSearchNet}"

# Dataset path controls. DATA_MODEL_DIR is intentionally separate from
# MODEL_NAME so MODEL_NAME can be changed to a provider-specific Gemma alias
# while outputs still land under data_codesearchnet/gemma by default.
DATA_ROOT="${DATA_ROOT:-src/code-analyzer-tree-sitter/data_codesearchnet}"
DATA_MODEL_DIR="${DATA_MODEL_DIR:-gemma}"
CSV_MODEL_PREFIX="${CSV_MODEL_PREFIX:-gemma}"
DATA_DIR="${DATA_DIR:-${DATA_ROOT}/${DATA_MODEL_DIR}}"
OUT_DIR="${OUT_DIR:-${DATA_DIR}/validsyntax}"

# Default input is the existing Gemma 4500-pair CSV. Override EXISTING_CSV
# if you want to seed from another baseline, for example:
#   src/code-analyzer-tree-sitter/data_codesearchnet/gemma/validsyntax_4500_complexity/codesearchnet_gemma_python_merged_4500.csv
EXISTING_CSV="${EXISTING_CSV:-${OUT_DIR}/codesearchnet_${CSV_MODEL_PREFIX}_${LANGUAGE}_merged_4500.csv}"

# By default, make the Gemma dataset larger than the existing 4500-pair CSV.
# Set TARGET_PAIRS=4500 to only repair/fill back to 4500 after revalidation.
# Set ADDITIONAL=1 to treat TARGET_PAIRS as the number of new valid pairs to add.
TARGET_PAIRS="${TARGET_PAIRS:-4500}"
ADDITIONAL="${ADDITIONAL:-0}"

# Optional explicit output CSV. When unset, generate-more.py writes:
#   ${OUT_DIR}/$(basename "${EXISTING_CSV}")
OUT_CSV="${OUT_CSV:-}"

# Long-run behavior.
RETRIES="${RETRIES:-20}"
RETRY_SLEEP="${RETRY_SLEEP:-5}"
RETRY_SLEEP_MAX="${RETRY_SLEEP_MAX:-120}"
RETRY_FOREVER="${RETRY_FOREVER:-1}"

# Optional safety/testing controls.
# Set MAX_API_CALLS=5 for a small test run.
MAX_API_CALLS="${MAX_API_CALLS:-}"

# Set DRY_RUN=1 to revalidate and print the plan without API calls.
DRY_RUN="${DRY_RUN:-0}"

# Optional candidate filters; defaults match generate-more.py / generate.py.
MIN_PROMPT_LEN="${MIN_PROMPT_LEN:-5}"
MAX_PROMPT_LEN="${MAX_PROMPT_LEN:-128}"
MIN_SOLUTION_LEN="${MIN_SOLUTION_LEN:-5}"
MAX_SOLUTION_LEN="${MAX_SOLUTION_LEN:-256}"

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

MODEL_LABEL="${MODEL_NAME//\//_}"
MODEL_LABEL="${MODEL_LABEL//:/-}"
TS="$(date +'%Y%m%d_%H%M%S')"

LOG_FILE="${LOG_FILE:-logs/generate-more_${MODEL_LABEL}_gemma_target${TARGET_PAIRS}_${TS}.log}"

# ---------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------

if [ ! -f "${EXISTING_CSV}" ]; then
  echo "[ERROR] Existing CSV not found: ${EXISTING_CSV}" >&2
  echo "        Override EXISTING_CSV to point at the Gemma baseline CSV." >&2
  exit 1
fi

if [ ! -f "${CODESEARCHNET_ROOT}/${LANGUAGE}/train.jsonl" ]; then
  echo "[ERROR] CodeSearchNet train.jsonl not found: ${CODESEARCHNET_ROOT}/${LANGUAGE}/train.jsonl" >&2
  echo "        Override CODESEARCHNET_ROOT if your dataset is elsewhere." >&2
  exit 1
fi

if [ "${DRY_RUN}" != "1" ] && [ -z "${!API_KEY_ENV:-}" ]; then
  echo "[ERROR] Missing API key environment variable: ${API_KEY_ENV}" >&2
  echo "        Example: OPENAI_API_KEY=... bash src/run0a-generate-llm-api-more-gemma.sh" >&2
  exit 1
fi

# ---------------------------------------------------------------------
# Build optional arguments
# ---------------------------------------------------------------------

EXTRA_ARGS=()

if [ -n "${TOP_P}" ]; then
  EXTRA_ARGS+=(--top-p "${TOP_P}")
fi

if [ "${RETRY_FOREVER}" = "1" ]; then
  EXTRA_ARGS+=(--retry-forever)
fi

if [ -n "${MAX_API_CALLS}" ]; then
  EXTRA_ARGS+=(--max-api-calls "${MAX_API_CALLS}")
fi

if [ "${DRY_RUN}" = "1" ]; then
  EXTRA_ARGS+=(--dry-run)
fi

if [ "${ADDITIONAL}" = "1" ]; then
  EXTRA_ARGS+=(--additional)
fi

if [ -n "${OUT_CSV}" ]; then
  EXTRA_ARGS+=(--out-csv "${OUT_CSV}")
fi

# ---------------------------------------------------------------------
# Print configuration
# ---------------------------------------------------------------------

{
  echo "=== generate-more.py Gemma configuration ==="
  echo "  Started:             $(date -Is)"
  echo "  Repo root:           ${REPO_ROOT}"
  echo "  Existing CSV:        ${EXISTING_CSV}"
  echo "  Target pairs:        ${TARGET_PAIRS}"
  echo "  Additional mode:     ${ADDITIONAL}"
  echo "  CodeSearchNet root:  ${CODESEARCHNET_ROOT}"
  echo "  Language:            ${LANGUAGE}"
  echo "  Output dir:          ${OUT_DIR}"
  echo "  Output CSV:          ${OUT_CSV:-${OUT_DIR}/$(basename "${EXISTING_CSV}")}"
  echo "  Model:               ${MODEL_NAME}"
  echo "  API URL:             ${API_URL}"
  echo "  API key env:         ${API_KEY_ENV}"
  echo "  Temperature:         ${TEMPERATURE}"
  echo "  Top-p:               ${TOP_P:-<model default>}"
  echo "  Max tokens:          ${MAX_TOKENS}"
  echo "  Timeout:             ${TIMEOUT}"
  echo "  Retries:             ${RETRIES}"
  echo "  Retry forever:       ${RETRY_FOREVER}"
  echo "  Retry sleep:         ${RETRY_SLEEP}s (max ${RETRY_SLEEP_MAX}s)"
  echo "  Max API calls:       ${MAX_API_CALLS:-<unlimited>}"
  echo "  Dry run:             ${DRY_RUN}"
  echo "  Candidate filters:   prompt ${MIN_PROMPT_LEN}-${MAX_PROMPT_LEN} words; solution ${MIN_SOLUTION_LEN}-${MAX_SOLUTION_LEN} words"
  echo "  Log file:            ${LOG_FILE}"
  echo "============================================="
  echo ""
} | tee "${LOG_FILE}"

env PYTHONUNBUFFERED=1 python -u src/code-generate-llm/generate-more.py \
  "${EXISTING_CSV}" \
  "${TARGET_PAIRS}" \
  --codesearchnet-root "${CODESEARCHNET_ROOT}" \
  --language "${LANGUAGE}" \
  --out-dir "${OUT_DIR}" \
  --model-name "${MODEL_NAME}" \
  --api-url "${API_URL}" \
  --api-key-env "${API_KEY_ENV}" \
  --temperature "${TEMPERATURE}" \
  --max-tokens "${MAX_TOKENS}" \
  --timeout "${TIMEOUT}" \
  --retries "${RETRIES}" \
  --retry-sleep "${RETRY_SLEEP}" \
  --retry-sleep-max "${RETRY_SLEEP_MAX}" \
  --min-prompt-len "${MIN_PROMPT_LEN}" \
  --max-prompt-len "${MAX_PROMPT_LEN}" \
  --min-solution-len "${MIN_SOLUTION_LEN}" \
  --max-solution-len "${MAX_SOLUTION_LEN}" \
  "${EXTRA_ARGS[@]}" \
  2>&1 | tee -a "${LOG_FILE}"

{
  echo "=== Finished generate-more.py Gemma run ==="
  echo "Log file: ${LOG_FILE}"
} | tee -a "${LOG_FILE}"
