#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1b2-agc-detector-did-analyzer.sh
# -----------------------------------------------------------------------------
# Run fresh AGC inference for commit-function change events.
#
# Workspace:
#   ai_detector
#
# Canonical path:
#   src/app/sh/run1b2-agc-detector-did-analyzer.sh
#
# Analysis unit:
#   One structurally added or modified named Python function in one commit.
#   Repeated changes to the same function in different commits remain separate
#   events. Reverted changes are retained as regular events.
#
# Safe inference mode:
#   - Prediction/content cache disabled.
#   - Checkpoint resume disabled.
#   - Function artifact hashes verified.
#   - Existing trained detector model reused without retraining.
#
# Pilot usage:
#   bash src/app/sh/run1b2-agc-detector-did-analyzer.sh
#
# Full usage:
#   DATASET_SOURCE=all \
#   MAX_FUNCTION_EVENTS=0 \
#   OUTPUT_ROOT=../ai_code_complexity_study_python/python_commit_function_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict \
#   bash src/app/sh/run1b2-agc-detector-did-analyzer.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/analyze_did_python_commit_functions.py}"

EXPERIMENT="${EXPERIMENT:-codellama-7b_4500_complexity_stratified_maxlen2048}"
CLASSIFIER="${CLASSIFIER:-svm}"
REPRESENTATION="${REPRESENTATION:-ast}"
MODEL_PICKLE="${MODEL_PICKLE:-src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl}"
EXPECTED_MODEL_KEY="${EXPECTED_MODEL_KEY:-codesearchnet_codellama-7b_python_merged_4500ast_}"
EXPECTED_SCORE_MODE="${EXPECTED_SCORE_MODE:-decision}"
MAX_LEN="${MAX_LEN:-2048}"
DATASET_SOURCE="${DATASET_SOURCE:-treatment}"

FUNCTION_EVENT_MANIFEST="${FUNCTION_EVENT_MANIFEST:-../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a/strict/commit_function_detection_manifest.csv}"
FUNCTION_SOURCE_ROOT="${FUNCTION_SOURCE_ROOT:-../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a/strict/commit_function_sources}"
MAX_FUNCTION_EVENTS="${MAX_FUNCTION_EVENTS:-50}"

OUTPUT_ROOT="${OUTPUT_ROOT:-../ai_code_complexity_study_python/python_commit_function_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/pilot-50-function-events-fresh}"

RUN_TS="${RUN_TS:-$(date +'%Y-%m%d-%H%M%P')}"
LOG_DIR="${LOG_DIR:-src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run1b2-agc-detector-did-analyzer-${RUN_TS}.log}"

mkdir -p "${LOG_DIR}" "${OUTPUT_ROOT}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERROR: Python executable not found: ${PYTHON_BIN}" >&2
    exit 2
fi

for required_file in "${PY_SCRIPT}" "${MODEL_PICKLE}" "${FUNCTION_EVENT_MANIFEST}"; do
    if [[ ! -f "${required_file}" ]]; then
        echo "ERROR: Required file not found: ${required_file}" >&2
        exit 2
    fi
done

if [[ ! -d "${FUNCTION_SOURCE_ROOT}" ]]; then
    echo "ERROR: Required directory not found: ${FUNCTION_SOURCE_ROOT}" >&2
    exit 2
fi

START_EPOCH="$(date +%s)"
START_TEXT="$(date)"

finish() {
    local exit_code=$?
    local end_epoch elapsed hours minutes seconds
    end_epoch="$(date +%s)"
    elapsed=$((end_epoch - START_EPOCH))
    hours=$((elapsed / 3600))
    minutes=$(((elapsed % 3600) / 60))
    seconds=$((elapsed % 60))

    echo
    echo "============================================================"
    echo "run1b2 timing summary"
    echo "Started:          ${START_TEXT}"
    echo "Completed:        $(date)"
    printf 'Elapsed:          %02d:%02d:%02d\n' "${hours}" "${minutes}" "${seconds}"
    echo "Exit code:        ${exit_code}"
    echo "Log file:         ${LOG_FILE}"
    echo "Output root:      ${OUTPUT_ROOT}"
    echo "============================================================"

    exit "${exit_code}"
}

trap finish EXIT
exec > >(tee -a "${LOG_FILE}") 2>&1

cat <<INFO
============================================================
run1b2-agc-detector-did-analyzer.sh
Started:                 ${START_TEXT}
Analysis unit:           commit-function change event
Function scope:          module, class method, nested, async
Inference mode:          fresh; cache disabled; resume disabled
Experiment:              ${EXPERIMENT}
Classifier:              ${CLASSIFIER}
Representation:          ${REPRESENTATION}
Model pickle:            ${MODEL_PICKLE}
Expected model key:      ${EXPECTED_MODEL_KEY}
Expected score mode:     ${EXPECTED_SCORE_MODE}
Max length:              ${MAX_LEN}
Dataset source:          ${DATASET_SOURCE}
Function event manifest: ${FUNCTION_EVENT_MANIFEST}
Function source root:    ${FUNCTION_SOURCE_ROOT}
Max function events:     ${MAX_FUNCTION_EVENTS}
Output root:             ${OUTPUT_ROOT}
Device:                  ${DEVICE:-<auto>}
Log file:                ${LOG_FILE}
============================================================
INFO

"${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

ARGS=(
    --experiment "${EXPERIMENT}"
    --classifier "${CLASSIFIER}"
    --representation "${REPRESENTATION}"
    --model-pickle "${MODEL_PICKLE}"
    --expected-model-key "${EXPECTED_MODEL_KEY}"
    --expected-score-mode "${EXPECTED_SCORE_MODE}"
    --max-len "${MAX_LEN}"
    --dataset-source "${DATASET_SOURCE}"
    --function-event-manifest "${FUNCTION_EVENT_MANIFEST}"
    --function-source-root "${FUNCTION_SOURCE_ROOT}"
    --max-function-events "${MAX_FUNCTION_EVENTS}"
    --output-root "${OUTPUT_ROOT}"
    --verify-hashes
    --no-cache
    --no-resume
)

if [[ -n "${DEVICE:-}" ]]; then
    ARGS+=(--device "${DEVICE}")
fi

"${PYTHON_BIN}" "${PY_SCRIPT}" "${ARGS[@]}"
