#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1b2-agc-detector-did-analyzer-mixed-pilot.sh
# -----------------------------------------------------------------------------
# Build and run a deterministic 266-event mixed AGC detection pilot.
#
# Workspace:
#   ai_detector
#
# Canonical paths after installation:
#   src/app/py/create_agc_mixed_pilot_event_ids.py
#   src/app/py/analyze_did_python_commit_functions.py
#   src/app/sh/run1b2-agc-detector-did-analyzer-mixed-pilot.sh
#
# Input composition:
#   - 124 runtime-CPython-AST compatibility edge events
#   - 42 tree-sitter recovery-node edge events
#   - 50 deterministic normal control events
#   - 50 deterministic normal treatment events
#
# Safe inference policy:
#   - Python 3.12 extraction manifest is used explicitly.
#   - Function source hashes are verified.
#   - Prediction and embedding caches are disabled.
#   - Checkpoint resume is disabled.
#   - The existing trained detector model is reused without retraining.
#
# Usage:
#   bash src/app/sh/run1b2-pre2-agc-detector-did-analyzer-mixed-pilot.sh
#
# Optional overrides:
#   DEVICE=cuda:1 bash src/app/sh/run1b2-agc-detector-did-analyzer-mixed-pilot.sh
#   SELECTION_SEED=my-fixed-seed bash src/app/sh/run1b2-agc-detector-did-analyzer-mixed-pilot.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
SELECT_SCRIPT="${SELECT_SCRIPT:-src/app/py/create_agc_mixed_pilot_event_ids.py}"
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
CHECKPOINT_EVERY="${CHECKPOINT_EVERY:-100}"

FUNCTION_EVENT_MANIFEST="${FUNCTION_EVENT_MANIFEST:-../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a-py312/strict/commit_function_detection_manifest.csv}"
FUNCTION_SOURCE_ROOT="${FUNCTION_SOURCE_ROOT:-../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a-py312/strict/commit_function_sources}"

RUNTIME_AST_EDGE_CSV="${RUNTIME_AST_EDGE_CSV:-../ai_code_complexity_study_python/python_commit_function_detect/input_compatibility/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312/detector_input_runtime_ast_failures.csv}"
TREE_SITTER_EDGE_CSV="${TREE_SITTER_EDGE_CSV:-../ai_code_complexity_study_python/python_commit_function_detect/input_compatibility/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312/detector_input_compatibility_failures.csv}"

EXPECTED_MANIFEST_ROWS="${EXPECTED_MANIFEST_ROWS:-450548}"
EXPECTED_RUNTIME_AST_EDGE_EVENTS="${EXPECTED_RUNTIME_AST_EDGE_EVENTS:-124}"
EXPECTED_TREE_SITTER_EDGE_EVENTS="${EXPECTED_TREE_SITTER_EDGE_EVENTS:-42}"
EXPECTED_EDGE_OVERLAP="${EXPECTED_EDGE_OVERLAP:-0}"
NORMAL_CONTROL_EVENTS="${NORMAL_CONTROL_EVENTS:-50}"
NORMAL_TREATMENT_EVENTS="${NORMAL_TREATMENT_EVENTS:-50}"
EXPECTED_SELECTED_EVENTS=$((
    EXPECTED_RUNTIME_AST_EDGE_EVENTS
    + EXPECTED_TREE_SITTER_EDGE_EVENTS
    - EXPECTED_EDGE_OVERLAP
    + NORMAL_CONTROL_EVENTS
    + NORMAL_TREATMENT_EVENTS
))
SELECTION_SEED="${SELECTION_SEED:-py312-mixed-pilot-v1}"

SELECTION_ROOT="${SELECTION_ROOT:-../ai_code_complexity_study_python/python_commit_function_detect/pilot_inputs/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312-mixed-pilot-266}"
EVENT_ID_FILE="${EVENT_ID_FILE:-${SELECTION_ROOT}/mixed_pilot_event_ids.csv}"
SELECTION_SUMMARY="${SELECTION_SUMMARY:-${SELECTION_ROOT}/mixed_pilot_selection_summary.json}"

OUTPUT_ROOT="${OUTPUT_ROOT:-../ai_code_complexity_study_python/python_commit_function_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312-mixed-pilot-266-fresh}"
ALLOW_EXISTING_OUTPUT="${ALLOW_EXISTING_OUTPUT:-0}"

RUN_TS="${RUN_TS:-$(date +'%Y-%m%d-%H%M%P')}"
LOG_DIR="${LOG_DIR:-src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run1b2-agc-detector-did-analyzer-mixed-pilot-${RUN_TS}.log}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERROR: Python executable not found: ${PYTHON_BIN}" >&2
    exit 2
fi

for required_file in \
    "${SELECT_SCRIPT}" \
    "${ANALYZER_SCRIPT}" \
    "${MODEL_PICKLE}" \
    "${FUNCTION_EVENT_MANIFEST}" \
    "${RUNTIME_AST_EDGE_CSV}" \
    "${TREE_SITTER_EDGE_CSV}"; do
    if [[ ! -f "${required_file}" ]]; then
        echo "ERROR: Required file not found: ${required_file}" >&2
        exit 2
    fi
done

if [[ ! -d "${FUNCTION_SOURCE_ROOT}" ]]; then
    echo "ERROR: Required directory not found: ${FUNCTION_SOURCE_ROOT}" >&2
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

mkdir -p "${LOG_DIR}" "${SELECTION_ROOT}" "${OUTPUT_ROOT}"

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
    echo "run1b2 mixed-pilot timing summary"
    echo "Started:          ${START_TEXT}"
    echo "Completed:        $(date)"
    printf 'Elapsed:          %02d:%02d:%02d\n' "${hours}" "${minutes}" "${seconds}"
    echo "Exit code:        ${exit_code}"
    echo "Log file:         ${LOG_FILE}"
    echo "Selection CSV:    ${EVENT_ID_FILE}"
    echo "Output root:      ${OUTPUT_ROOT}"
    echo "============================================================"

    exit "${exit_code}"
}

trap finish EXIT
exec > >(tee -a "${LOG_FILE}") 2>&1

cat <<INFO
============================================================
run1b2-agc-detector-did-analyzer-mixed-pilot.sh
Started:                    ${START_TEXT}
Analysis unit:              commit-function change event
Inference mode:             fresh; cache disabled; resume disabled
Python analyzer:            ${ANALYZER_SCRIPT}
Selection script:           ${SELECT_SCRIPT}
Experiment:                 ${EXPERIMENT}
Classifier:                 ${CLASSIFIER}
Representation:             ${REPRESENTATION}
Model pickle:               ${MODEL_PICKLE}
Expected model key:         ${EXPECTED_MODEL_KEY}
Expected score mode:        ${EXPECTED_SCORE_MODE}
Max length:                 ${MAX_LEN}
Dataset source:             ${DATASET_SOURCE}
Function event manifest:    ${FUNCTION_EVENT_MANIFEST}
Function source root:       ${FUNCTION_SOURCE_ROOT}
Runtime AST edge CSV:       ${RUNTIME_AST_EDGE_CSV}
Tree-sitter edge CSV:       ${TREE_SITTER_EDGE_CSV}
Runtime AST edge events:    ${EXPECTED_RUNTIME_AST_EDGE_EVENTS}
Tree-sitter edge events:    ${EXPECTED_TREE_SITTER_EDGE_EVENTS}
Normal control events:      ${NORMAL_CONTROL_EVENTS}
Normal treatment events:    ${NORMAL_TREATMENT_EVENTS}
Expected selected events:   ${EXPECTED_SELECTED_EVENTS}
Selection seed:             ${SELECTION_SEED}
Selection CSV:              ${EVENT_ID_FILE}
Selection summary:          ${SELECTION_SUMMARY}
Output root:                ${OUTPUT_ROOT}
Device:                     ${DEVICE}
Log file:                   ${LOG_FILE}
============================================================
INFO

"${PYTHON_BIN}" -m py_compile "${SELECT_SCRIPT}" "${ANALYZER_SCRIPT}"
"${PYTHON_BIN}" -c "import torch; print('PyTorch:', torch.__version__)"

"${PYTHON_BIN}" "${SELECT_SCRIPT}" \
    --manifest "${FUNCTION_EVENT_MANIFEST}" \
    --runtime-ast-edge-csv "${RUNTIME_AST_EDGE_CSV}" \
    --tree-sitter-edge-csv "${TREE_SITTER_EDGE_CSV}" \
    --output-csv "${EVENT_ID_FILE}" \
    --output-summary "${SELECTION_SUMMARY}" \
    --seed "${SELECTION_SEED}" \
    --normal-control-events "${NORMAL_CONTROL_EVENTS}" \
    --normal-treatment-events "${NORMAL_TREATMENT_EVENTS}" \
    --expected-manifest-rows "${EXPECTED_MANIFEST_ROWS}" \
    --expected-runtime-ast-edge-events "${EXPECTED_RUNTIME_AST_EDGE_EVENTS}" \
    --expected-tree-sitter-edge-events "${EXPECTED_TREE_SITTER_EDGE_EVENTS}" \
    --expected-edge-overlap "${EXPECTED_EDGE_OVERLAP}"

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
    --event-id-file "${EVENT_ID_FILE}"
    --max-function-events 0
    --expected-manifest-rows "${EXPECTED_MANIFEST_ROWS}"
    --expected-selected-events "${EXPECTED_SELECTED_EVENTS}"
    --expected-runtime-ast-failures "${EXPECTED_RUNTIME_AST_EDGE_EVENTS}"
    --expected-tree-sitter-warning-events "${EXPECTED_TREE_SITTER_EDGE_EVENTS}"
    --output-root "${OUTPUT_ROOT}"
    --device "${DEVICE}"
    --checkpoint-every "${CHECKPOINT_EVERY}"
    --verify-hashes
    --no-cache
    --no-resume
)

"${PYTHON_BIN}" "${ANALYZER_SCRIPT}" "${ANALYZER_ARGS[@]}"
