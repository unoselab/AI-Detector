#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1c-validate-detection-result.sh
# -----------------------------------------------------------------------------
# Validate final treatment/control outputs produced by run1b.
#
# Default behavior:
#   - Validate both treatment and control final artifacts.
#   - Do not require cache/ or parts/ directories.
#   - Write validation summaries under <OUTPUT_ROOT>/qc/run1c/.
#
# Usage:
#   bash src/app/run1c-validate-detection-result.sh (recommended)
#   SOURCE=treatment bash src/app/run1c-validate-detection-result.sh
#   REQUIRE_PARTS=1 bash src/app/run1c-validate-detection-result.sh
# 
#   SOURCE=treatment bash src/app/run1c-validate-detection-result.sh
#   SOURCE=control bash src/app/run1c-validate-detection-result.sh
# 
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/validate_did_detection_results.py}"

OUTPUT_ROOT="${OUTPUT_ROOT:-../ai_code_complexity_study_python/python_snapshots_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict}"
SOURCE="${SOURCE:-both}"

EXPECTED_TREATMENT_COMMITS="${EXPECTED_TREATMENT_COMMITS:-863}"
EXPECTED_CONTROL_COMMITS="${EXPECTED_CONTROL_COMMITS:-800}"

EXPECTED_EXPERIMENT="${EXPECTED_EXPERIMENT:-codellama-7b_4500_complexity_stratified_maxlen2048}"
EXPECTED_CLASSIFIER="${EXPECTED_CLASSIFIER:-svm}"
EXPECTED_REPRESENTATION="${EXPECTED_REPRESENTATION:-ast}"
EXPECTED_SCORE_MODE="${EXPECTED_SCORE_MODE:-decision}"
EXPECTED_MODEL_KEY="${EXPECTED_MODEL_KEY:-codesearchnet_codellama-7b_python_merged_4500ast_}"

REQUIRE_PARTS="${REQUIRE_PARTS:-0}"
VALIDATION_OUTPUT_DIR="${VALIDATION_OUTPUT_DIR:-${OUTPUT_ROOT}/qc/run1c}"

RUN_TS="${RUN_TS:-$(date +'%Y-%m%d-%H%M%P')}"
LOG_DIR="${LOG_DIR:-src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run1c-validate-detection-result-${RUN_TS}.log}"

mkdir -p "${LOG_DIR}" "${VALIDATION_OUTPUT_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

START_EPOCH="$(date +%s)"
START_TEXT="$(date)"

finish() {
  status=$?
  end_epoch="$(date +%s)"
  elapsed=$((end_epoch - START_EPOCH))
  printf -v elapsed_text '%02d:%02d:%02d' \
    $((elapsed / 3600)) \
    $(((elapsed % 3600) / 60)) \
    $((elapsed % 60))

  echo
  echo "============================================================"
  echo "run1c validation timing summary"
  echo "Started:        ${START_TEXT}"
  echo "Completed:      $(date)"
  echo "Elapsed:        ${elapsed_text}"
  echo "Exit code:      ${status}"
  echo "Log file:       ${LOG_FILE}"
  echo "Output root:    ${OUTPUT_ROOT}"
  echo "Validation dir: ${VALIDATION_OUTPUT_DIR}"
  echo "============================================================"

  trap - EXIT
  exit "${status}"
}
trap finish EXIT

echo "============================================================"
echo "run1c-validate-detection-result.sh"
echo "Started:                    ${START_TEXT}"
echo "Python script:              ${PY_SCRIPT}"
echo "Output root:                ${OUTPUT_ROOT}"
echo "Source:                     ${SOURCE}"
echo "Expected treatment commits: ${EXPECTED_TREATMENT_COMMITS}"
echo "Expected control commits:   ${EXPECTED_CONTROL_COMMITS}"
echo "Expected experiment:        ${EXPECTED_EXPERIMENT}"
echo "Expected classifier:        ${EXPECTED_CLASSIFIER}"
echo "Expected representation:    ${EXPECTED_REPRESENTATION}"
echo "Expected score mode:        ${EXPECTED_SCORE_MODE}"
echo "Expected model key:         ${EXPECTED_MODEL_KEY}"
echo "Require parts:              ${REQUIRE_PARTS}"
echo "Validation output:          ${VALIDATION_OUTPUT_DIR}"
echo "Log file:                   ${LOG_FILE}"
echo "============================================================"

if [[ ! -f "${PY_SCRIPT}" ]]; then
  echo "[ERROR] Python validator not found: ${PY_SCRIPT}" >&2
  exit 2
fi

if [[ ! -d "${OUTPUT_ROOT}" ]]; then
  echo "[ERROR] detector output root not found: ${OUTPUT_ROOT}" >&2
  exit 2
fi

"${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

ARGS=(
  --root "${OUTPUT_ROOT}"
  --source "${SOURCE}"
  --expected-treatment-commits "${EXPECTED_TREATMENT_COMMITS}"
  --expected-control-commits "${EXPECTED_CONTROL_COMMITS}"
  --expected-experiment "${EXPECTED_EXPERIMENT}"
  --expected-classifier "${EXPECTED_CLASSIFIER}"
  --expected-representation "${EXPECTED_REPRESENTATION}"
  --expected-score-mode "${EXPECTED_SCORE_MODE}"
  --expected-model-key "${EXPECTED_MODEL_KEY}"
  --output-dir "${VALIDATION_OUTPUT_DIR}"
)

if [[ "${REQUIRE_PARTS}" == "1" ]]; then
  ARGS+=(--require-parts)
fi

"${PYTHON_BIN}" "${PY_SCRIPT}" "${ARGS[@]}"
