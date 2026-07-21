#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1b2-pre3-agc-detector-did-analyzer-full.sh
# -----------------------------------------------------------------------------
# Run full fresh AGC inference for all Python 3.12 commit-function change events.
#
# Workspace:
#   ai_detector
#
# Canonical paths after installation:
#   src/app/py/analyze_did_python_commit_functions.py
#   src/app/sh/run1b2-pre3-agc-detector-did-analyzer-full.sh
#
# Required inputs:
#   - Python 3.12 commit-function detection manifest with 450,548 events.
#   - Python 3.12 standalone function source artifacts.
#   - Existing trained CodeT5+ embedding and SVM+AST detector model.
#
# Expected outputs under OUTPUT_ROOT:
#   - function_event_predictions_all.csv
#   - failed_function_events_all.csv
#   - commit_function_event_summary_all.csv
#   - repo_month_function_event_summary_all.csv
#   - run_metadata_all.json
#   - qc_summary_all.json
#
# Safe inference policy:
#   - Use the Python 3.12 extraction manifest explicitly.
#   - Verify every function source SHA-256 hash.
#   - Run fresh inference without cache reuse or checkpoint resume.
#   - Reuse the existing trained detector model without retraining.
#   - Treat runtime CPython AST incompatibility as diagnostic only.
#   - Treat tree-sitter recovery nodes as warnings when scoring succeeds.
#
# Full-run logging policy:
#   - Print one compact progress line every 1,000 events by default.
#   - Print warning and failure events in detail.
#   - Refresh cumulative partial CSV outputs every 50,000 events by default.
#   - Partial outputs are inspection artifacts and are never used for resume.
#
# Usage:
#   bash src/app/sh/run1b2-pre3-agc-detector-did-analyzer-full.sh
#
# Optional overrides:
#   DEVICE=cuda:1 bash src/app/sh/run1b2-pre3-agc-detector-did-analyzer-full.sh
#   PROGRESS_EVERY=5000 CHECKPOINT_EVERY=100000 \
#     bash src/app/sh/run1b2-pre3-agc-detector-did-analyzer-full.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
ANALYZER_SCRIPT="${ANALYZER_SCRIPT:-src/app/py/analyze_did_python_commit_functions.py}"

EXPERIMENT="${EXPERIMENT:-codellama-7b_4500_complexity_stratified_maxlen2048}"
CLASSIFIER="${CLASSIFIER:-svm}"
REPRESENTATION="${REPRESENTATION:-ast}"
MODEL_PICKLE="${MODEL_PICKLE:-src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl}"
EXPECTED_MODEL_KEY="${EXPECTED_MODEL_KEY:-codesearchnet_codellama-7b_python_merged_4500ast_}"
EXPECTED_SCORE_MODE="${EXPECTED_SCORE_MODE:-decision}"
MAX_LEN="${MAX_LEN:-2048}"
DATASET_SOURCE="all"
DEVICE="${DEVICE:-cuda:0}"

FUNCTION_EVENT_MANIFEST="${FUNCTION_EVENT_MANIFEST:-../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a-py312/strict/commit_function_detection_manifest.csv}"
FUNCTION_SOURCE_ROOT="${FUNCTION_SOURCE_ROOT:-../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a-py312/strict/commit_function_sources}"

EXPECTED_MANIFEST_ROWS="${EXPECTED_MANIFEST_ROWS:-450548}"
EXPECTED_SELECTED_EVENTS="${EXPECTED_SELECTED_EVENTS:-450548}"
EXPECTED_RUNTIME_AST_WARNINGS="${EXPECTED_RUNTIME_AST_WARNINGS:-124}"
EXPECTED_TREE_SITTER_WARNINGS="${EXPECTED_TREE_SITTER_WARNINGS:-42}"
MAX_FUNCTION_EVENTS="0"
PROGRESS_EVERY="${PROGRESS_EVERY:-1000}"
CHECKPOINT_EVERY="${CHECKPOINT_EVERY:-50000}"

OUTPUT_ROOT="${OUTPUT_ROOT:-../ai_code_complexity_study_python/python_commit_function_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312-full-450548-fresh}"
ALLOW_EXISTING_OUTPUT="${ALLOW_EXISTING_OUTPUT:-0}"

RUN_TS="${RUN_TS:-$(date +'%Y-%m%d-%H%M%P')}"
LOG_DIR="${LOG_DIR:-src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run1b2-agc-detector-did-analyzer-${RUN_TS}.log}"


if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERROR: Python executable not found: ${PYTHON_BIN}" >&2
    exit 2
fi

for required_file in \
    "${ANALYZER_SCRIPT}" \
    "${MODEL_PICKLE}" \
    "${FUNCTION_EVENT_MANIFEST}"; do
    if [[ ! -f "${required_file}" ]]; then
        echo "ERROR: Required file not found: ${required_file}" >&2
        exit 2
    fi
done

if [[ ! -d "${FUNCTION_SOURCE_ROOT}" ]]; then
    echo "ERROR: Required directory not found: ${FUNCTION_SOURCE_ROOT}" >&2
    exit 2
fi

for integer_value in \
    "${EXPECTED_MANIFEST_ROWS}" \
    "${EXPECTED_SELECTED_EVENTS}" \
    "${EXPECTED_RUNTIME_AST_WARNINGS}" \
    "${EXPECTED_TREE_SITTER_WARNINGS}" \
    "${PROGRESS_EVERY}" \
    "${CHECKPOINT_EVERY}"; do
    if [[ ! "${integer_value}" =~ ^[0-9]+$ ]]; then
        echo "ERROR: Expected a non-negative integer, received: ${integer_value}" >&2
        exit 2
    fi
done

if (( EXPECTED_MANIFEST_ROWS <= 0 )); then
    echo "ERROR: EXPECTED_MANIFEST_ROWS must be positive." >&2
    exit 2
fi
if (( EXPECTED_SELECTED_EVENTS <= 0 )); then
    echo "ERROR: EXPECTED_SELECTED_EVENTS must be positive." >&2
    exit 2
fi
if (( PROGRESS_EVERY <= 0 )); then
    echo "ERROR: PROGRESS_EVERY must be positive." >&2
    exit 2
fi
if (( CHECKPOINT_EVERY <= 0 )); then
    echo "ERROR: CHECKPOINT_EVERY must be positive." >&2
    exit 2
fi

case "${ALLOW_EXISTING_OUTPUT}" in
    0|1)
        ;;
    *)
        echo "ERROR: ALLOW_EXISTING_OUTPUT must be 0 or 1." >&2
        exit 2
        ;;
esac

if [[ "${ALLOW_EXISTING_OUTPUT}" == "0" && -d "${OUTPUT_ROOT}" ]]; then
    if find "${OUTPUT_ROOT}" -mindepth 1 -print -quit | grep -q .; then
        echo "ERROR: Output directory is not empty: ${OUTPUT_ROOT}" >&2
        echo "Use a new OUTPUT_ROOT or set ALLOW_EXISTING_OUTPUT=1 explicitly." >&2
        exit 2
    fi
fi

mkdir -p "${LOG_DIR}" "${OUTPUT_ROOT}"

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
    echo "run1b2-pre3 full-inference timing summary"
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
run1b2-pre3-agc-detector-did-analyzer-full.sh
Started:                     ${START_TEXT}
Analysis unit:               commit-function change event
Inference mode:              fresh; cache disabled; resume disabled
Python analyzer:             ${ANALYZER_SCRIPT}
Experiment:                  ${EXPERIMENT}
Classifier:                  ${CLASSIFIER}
Representation:              ${REPRESENTATION}
Model pickle:                ${MODEL_PICKLE}
Expected model key:          ${EXPECTED_MODEL_KEY}
Expected score mode:         ${EXPECTED_SCORE_MODE}
Max length:                  ${MAX_LEN}
Dataset source:              ${DATASET_SOURCE}
Function event manifest:     ${FUNCTION_EVENT_MANIFEST}
Function source root:        ${FUNCTION_SOURCE_ROOT}
Expected manifest rows:      ${EXPECTED_MANIFEST_ROWS}
Expected selected events:    ${EXPECTED_SELECTED_EVENTS}
Expected runtime AST warns:  ${EXPECTED_RUNTIME_AST_WARNINGS}
Expected tree-sitter warns:  ${EXPECTED_TREE_SITTER_WARNINGS}
Progress every:              ${PROGRESS_EVERY}
Checkpoint every:            ${CHECKPOINT_EVERY}
Output root:                 ${OUTPUT_ROOT}
Allow existing output:       ${ALLOW_EXISTING_OUTPUT}
Device:                      ${DEVICE}
Log file:                    ${LOG_FILE}
============================================================
INFO

"${PYTHON_BIN}" -m py_compile "${ANALYZER_SCRIPT}"
"${PYTHON_BIN}" -c "import sys, torch; print('Python:', sys.version.split()[0]); print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"

if [[ "${DEVICE}" == cuda:* ]]; then
    CUDA_INDEX="${DEVICE#cuda:}"
    if [[ ! "${CUDA_INDEX}" =~ ^[0-9]+$ ]]; then
        echo "ERROR: CUDA device must use the form cuda:<index>: ${DEVICE}" >&2
        exit 2
    fi
    "${PYTHON_BIN}" -c "import torch; idx=int('${CUDA_INDEX}'); assert torch.cuda.is_available(), 'CUDA is not available'; assert idx < torch.cuda.device_count(), f'CUDA device index out of range: {idx}'; print('CUDA device count:', torch.cuda.device_count()); print('Selected CUDA device:', idx, torch.cuda.get_device_name(idx))"
fi

ANALYZER_ARGS=(
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
    --expected-manifest-rows "${EXPECTED_MANIFEST_ROWS}"
    --expected-selected-events "${EXPECTED_SELECTED_EVENTS}"
    --expected-runtime-ast-failures "${EXPECTED_RUNTIME_AST_WARNINGS}"
    --expected-tree-sitter-warning-events "${EXPECTED_TREE_SITTER_WARNINGS}"
    --output-root "${OUTPUT_ROOT}"
    --device "${DEVICE}"
    --progress-every "${PROGRESS_EVERY}"
    --checkpoint-every "${CHECKPOINT_EVERY}"
    --verify-hashes
    --no-cache
    --no-resume
)

"${PYTHON_BIN}" "${ANALYZER_SCRIPT}" "${ANALYZER_ARGS[@]}"
