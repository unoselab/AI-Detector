#!/usr/bin/env bash
# =============================================================================
# run0a-generate-llm-api-more.sh
# -----------------------------------------------------------------------------
# Generate additional valid MGC pairs for the gpt-oss CodeSearchNet dataset.
#
# This script calls:
#   src/code-generate-llm/generate-more.py
#
# It is intended for long API runs:
#   * creates a timestamped log file;
#   * runs with nohup in the background;
#   * uses --retry-forever by default;
#   * lets generate-more.py create a backup of the validsyntax directory.
#
# Example:
#   OPENAI_API_KEY=... bash src/run0a-generate-llm-api-more.sh
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

MODEL_NAME="${MODEL_NAME:-gpt-oss}"
TARGET_PAIRS="${TARGET_PAIRS:-4500}"

# Use the original 4500-pair backup CSV as input.
# This avoids using the partial 3011-pair CSV produced by the small test run.
EXISTING_CSV="${EXISTING_CSV:-src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax-bak-20260604-143721/codesearchnet_gpt-oss_python_merged_4500.csv}"

CODESEARCHNET_ROOT="${CODESEARCHNET_ROOT:-data/CodeSearchNet}"

# Long-run behavior.
RETRY_FOREVER="${RETRY_FOREVER:-1}"

# Optional safety/testing controls.
# Set MAX_API_CALLS=5 for a small test run.
MAX_API_CALLS="${MAX_API_CALLS:-}"

# Set DRY_RUN=1 to revalidate and print the plan without API calls.
DRY_RUN="${DRY_RUN:-0}"

# Set ADDITIONAL=1 if TARGET_PAIRS should mean "add this many new valid pairs"
# instead of "final target number of valid pairs".
ADDITIONAL="${ADDITIONAL:-0}"

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

MODEL_LABEL="${MODEL_NAME//\//_}"
MODEL_LABEL="${MODEL_LABEL//:/-}"
TS="$(date +'%Y%m%d_%H%M%S')"

LOG_FILE="${LOG_FILE:-logs/generate-more_${MODEL_LABEL}_target${TARGET_PAIRS}_${TS}.log}"

# ---------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------

if [ ! -f "${EXISTING_CSV}" ]; then
  echo "[ERROR] Existing CSV not found: ${EXISTING_CSV}" >&2
  exit 1
fi

if [ "${DRY_RUN}" != "1" ] && [ -z "${!API_KEY_ENV:-}" ]; then
  echo "[ERROR] Missing API key environment variable: ${API_KEY_ENV}" >&2
  echo "        Example: OPENAI_API_KEY=... bash src/run0a-generate-llm-api-more.sh" >&2
  exit 1
fi

# ---------------------------------------------------------------------
# Build optional arguments
# ---------------------------------------------------------------------

EXTRA_ARGS=()

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

# ---------------------------------------------------------------------
# Print configuration
# ---------------------------------------------------------------------

{
  echo "=== generate-more.py configuration ==="
  echo "  Started:             $(date -Is)"
  echo "  Repo root:           ${REPO_ROOT}"
  echo "  Existing CSV:        ${EXISTING_CSV}"
  echo "  Target pairs:        ${TARGET_PAIRS}"
  echo "  CodeSearchNet root:  ${CODESEARCHNET_ROOT}"
  echo "  Model:               ${MODEL_NAME}"
  echo "  API key env:         ${API_KEY_ENV}"
  echo "  Retry forever:       ${RETRY_FOREVER}"
  echo "  Max API calls:       ${MAX_API_CALLS:-<unlimited>}"
  echo "  Dry run:             ${DRY_RUN}"
  echo "  Additional mode:     ${ADDITIONAL}"
  echo "  Log file:            ${LOG_FILE}"
  echo "======================================="
  echo ""
} | tee "${LOG_FILE}"

env PYTHONUNBUFFERED=1 python -u src/code-generate-llm/generate-more.py \
  "${EXISTING_CSV}" \
  "${TARGET_PAIRS}" \
  --codesearchnet-root "${CODESEARCHNET_ROOT}" \
  --model-name "${MODEL_NAME}" \
  "${EXTRA_ARGS[@]}" \
  2>&1 | tee -a "${LOG_FILE}"

{
  echo "=== Finished generate-more.py ==="
  echo "Log file: ${LOG_FILE}"
} | tee -a "${LOG_FILE}"