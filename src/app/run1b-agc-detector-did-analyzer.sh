#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1b-agc-detector-did-analyzer.sh
# -----------------------------------------------------------------------------
# Run a 50-commit CodeLlama-7B SVM+AST timing pilot on DiD Python snapshots.
#
# The output root is intentionally separate from the earlier two-commit pilot
# so that prior checkpoints and cache files do not bias the runtime estimate.
#
# Usage for Full Run
# MAX_COMMITS=0 OUTPUT_ROOT=../ai_code_complexity_study_python/python_snapshots_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict bash src/app/run1b-agc-detector-did-analyzer.sh
# 
# Usage:
#   bash src/app/run1b-agc-detector-did-analyzer.sh
#
# Optional overrides:
#   MAX_COMMITS=50 bash src/app/run1b-agc-detector-did-analyzer.sh
#   DEVICE=cuda:0 bash src/app/run1b-agc-detector-did-analyzer.sh
#   OUTPUT_ROOT=/path/to/output bash src/app/run1b-agc-detector-did-analyzer.sh
# 
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/analyze_did_python_snapshots.py}"

EXPERIMENT="${EXPERIMENT:-codellama-7b_4500_complexity_stratified_maxlen2048}"
CLASSIFIER="${CLASSIFIER:-svm}"
REPRESENTATION="${REPRESENTATION:-ast}"
MODEL_PICKLE="${MODEL_PICKLE:-src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl}"
EXPECTED_MODEL_KEY="${EXPECTED_MODEL_KEY:-codesearchnet_codellama-7b_python_merged_4500ast_}"
EXPECTED_SCORE_MODE="${EXPECTED_SCORE_MODE:-decision}"
MAX_LEN="${MAX_LEN:-2048}"
DATASET_SOURCE="${DATASET_SOURCE:-treatment}"
SNAPSHOT_ROOT="${SNAPSHOT_ROOT:-../ai_code_complexity_study_python/python_snapshots}"
MAX_COMMITS="${MAX_COMMITS:-50}"

# Keep this timing pilot separate from the previous two-commit pilot.
OUTPUT_ROOT="${OUTPUT_ROOT:-../ai_code_complexity_study_python/python_snapshots_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/pilot-50commits}"

RUN_TS="${RUN_TS:-$(date +'%Y-%m%d-%H%M%P')}"
LOG_DIR="${LOG_DIR:-src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run1b-agc-detector-did-analyzer-${RUN_TS}.log}"

mkdir -p "${LOG_DIR}" "${OUTPUT_ROOT}"

for required_path in "${PY_SCRIPT}" "${MODEL_PICKLE}" "${SNAPSHOT_ROOT}"; do
  if [[ ! -e "${required_path}" ]]; then
    echo "ERROR: Required input not found: ${required_path}" >&2
    exit 2
  fi
done

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
  echo "run1b timing summary"
  echo "Started:        ${START_TEXT}"
  echo "Completed:      $(date)"
  printf 'Elapsed:        %02d:%02d:%02d\n' "${hours}" "${minutes}" "${seconds}"
  echo "Exit code:      ${exit_code}"
  echo "Log file:       ${LOG_FILE}"
  echo "Output root:    ${OUTPUT_ROOT}"
  echo "============================================================"

  exit "${exit_code}"
}

trap finish EXIT
exec > >(tee -a "${LOG_FILE}") 2>&1

cat <<INFO
============================================================
run1b-agc-detector-did-analyzer.sh
Started:            ${START_TEXT}
Experiment:         ${EXPERIMENT}
Classifier:         ${CLASSIFIER}
Representation:     ${REPRESENTATION}
Model pickle:       ${MODEL_PICKLE}
Expected model key: ${EXPECTED_MODEL_KEY}
Expected score mode:${EXPECTED_SCORE_MODE}
Max length:         ${MAX_LEN}
Dataset source:     ${DATASET_SOURCE}
Snapshot root:      ${SNAPSHOT_ROOT}
Max commits:        ${MAX_COMMITS}
Output root:        ${OUTPUT_ROOT}
Device:             ${DEVICE:-<auto>}
Log file:           ${LOG_FILE}
============================================================
INFO

ARGS=(
  --experiment "${EXPERIMENT}"
  --classifier "${CLASSIFIER}"
  --representation "${REPRESENTATION}"
  --model-pickle "${MODEL_PICKLE}"
  --expected-model-key "${EXPECTED_MODEL_KEY}"
  --expected-score-mode "${EXPECTED_SCORE_MODE}"
  --max-len "${MAX_LEN}"
  --dataset-source "${DATASET_SOURCE}"
  --snapshot-root "${SNAPSHOT_ROOT}"
  --max-commits "${MAX_COMMITS}"
  --output-root "${OUTPUT_ROOT}"
)

if [[ -n "${DEVICE:-}" ]]; then
  ARGS+=(--device "${DEVICE}")
fi

"${PYTHON_BIN}" "${PY_SCRIPT}" "${ARGS[@]}"
