#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run-x-a01-freeze-agc-ml-detector-v2.sh
# -----------------------------------------------------------------------------
# Purpose
#   Reproduce and freeze the CodeLlama-7B + SVM + AST AGC detector before any
#   downstream open-source GitHub quality analysis.
#
# Revision v2
#   - Replaces the fragile inline Step-5 Python verifier with the freeze
#     auditor's explicit --verify-output mode.
#   - Adds MODE=repair so an already completed 900-row benchmark can reuse its
#     validation artifacts and rerun only the cheap freeze/audit/verification
#     steps. No CodeT5+ embedding or SVM inference is repeated in repair mode.
#   - Ensures any verification exception is a hard shell failure.
#
# Core detector inference
#   This wrapper intentionally reuses the existing validated Python analyzer:
#     src/app/py/analyze_did_python_snapshots.py
#   It does NOT call or depend on the older run1a shell wrapper.
#
# Frozen detector configuration
#   Generation source : CodeLlama-7B
#   Classifier        : SVM
#   Representation    : AST
#   Embedding model   : Salesforce/codet5p-110m-embedding
#   Max length        : 2048
#   Score mode        : decision
#   Human label       : 1
#   AGC label         : 0
#   SVM boundary      : 0.0
#   AGC score         : -human_decision_score
#
# Ground-truth validation input
#   A complexity-balanced held-out test split with 900 labeled functions
#   (450 HWC and 450 AGC functions).
#
# Expected reference metrics
#   ACC       = 0.7178
#   HWC F1    = 0.7221
#   AGC F1    = 0.7133
#   Avg. F1   = 0.7177
#   AUROC     = 0.7950
#
# Outputs under OUTPUT_ROOT
#   validation/validation_predictions.csv
#   validation/validation_metrics.csv
#   validation/validation_summary.txt
#   detector_freeze_checks.csv
#   detector_freeze_summary.json
#   detector_freeze_metadata.json
#
# Modes
#   MODE=full
#     Run the 900-row reference inference, freeze provenance, and verify.
#     If OUTPUT_ROOT exists, OVERWRITE=1 is required and the old output is
#     removed before the full run.
#
#   MODE=repair
#     Reuse the already completed validation artifacts under OUTPUT_ROOT,
#     rerun the v2 freeze auditor, and verify outputs. This is the recommended
#     mode for repairing the v1 Step-5 verification bug without repeating GPU
#     inference.
#
#   MODE=verify
#     Read-only verification of existing v2 freeze artifacts.
#
# Usage
#   MODE=repair bash src/app/sh/run-x-a01-freeze-agc-ml-detector.sh
#
# Full fresh rerun
#   MODE=full OVERWRITE=1 bash src/app/sh/run-x-a01-freeze-agc-ml-detector.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a01-v2"
MODE="${MODE:-full}"
PYTHON_BIN="${PYTHON_BIN:-python}"
ANALYZER_SCRIPT="src/app/py/analyze_did_python_snapshots.py"
FREEZE_AUDITOR="src/app/py/freeze_agc_ml_detector.py"

EXPERIMENT="codellama-7b_4500_complexity_stratified_maxlen2048"
CLASSIFIER="svm"
REPRESENTATION="ast"
SCORE_MODE="decision"
MAX_LEN="2048"
FUNCTION_THRESHOLD="0.0"
MODEL_KEY="codesearchnet_codellama-7b_python_merged_4500ast_"

MODEL_PICKLE="src/ml_embeddings/data_codesearchnet/models/${EXPERIMENT}/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"
TEST_CSV="src/ml_embeddings/data_codesearchnet/splits/${EXPERIMENT}/codesearchnet_codellama-7b_python_merged_4500/test_.csv"

EXPECTED_TEST_ROWS="900"
EXPECTED_ACC="0.7178"
EXPECTED_HUMAN_F1="0.7221"
EXPECTED_AI_F1="0.7133"
EXPECTED_AVG_F1="0.7177"
EXPECTED_AUROC="0.7950"

OUTPUT_ROOT="${OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a01}"
OVERWRITE="${OVERWRITE:-0}"

case "${MODE}" in
  full|repair|verify) ;;
  *)
    echo "[ERROR] unsupported MODE=${MODE}; expected full, repair, or verify" >&2
    exit 2
    ;;
esac

RUN_TS="${RUN_TS:-$(date +'%Y%m%d-%H%M%S')}"
LOG_DIR="${LOG_DIR:-src/logs/run-x-a01}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a01-v2-${MODE}-agc-ml-detector-${RUN_TS}.log}"
mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

on_error() {
  local rc=$?
  echo
  echo "[ERROR] ${RUN_ID} failed in MODE=${MODE} with exit code ${rc}." >&2
  echo "Log file: ${LOG_FILE}" >&2
  exit "${rc}"
}
trap on_error ERR

require_file() {
  local path="$1"
  local label="$2"
  if [[ ! -f "${path}" ]]; then
    echo "[ERROR] ${label} not found: ${path}" >&2
    exit 2
  fi
}

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

require_file "${ANALYZER_SCRIPT}" "existing validated analyzer"
require_file "${FREEZE_AUDITOR}" "run-x-a01 freeze auditor"
require_file "${MODEL_PICKLE}" "frozen SVM model pickle"
require_file "${TEST_CSV}" "complexity-balanced held-out test CSV"

if [[ "${MODE}" == "full" ]]; then
  if [[ -e "${OUTPUT_ROOT}" ]]; then
    if [[ "${OVERWRITE}" != "1" ]]; then
      echo "[ERROR] output root already exists: ${OUTPUT_ROOT}" >&2
      echo "        Use MODE=repair to repair/audit an existing A01 run." >&2
      echo "        Use MODE=full OVERWRITE=1 only for an intentional fresh rerun." >&2
      exit 2
    fi
    rm -rf "${OUTPUT_ROOT}"
  fi
  mkdir -p "${OUTPUT_ROOT}"
else
  if [[ ! -d "${OUTPUT_ROOT}" ]]; then
    echo "[ERROR] MODE=${MODE} requires existing output root: ${OUTPUT_ROOT}" >&2
    exit 2
  fi
fi

START_EPOCH="$(date +%s)"
STARTED_AT="$(date)"

cat <<INFO
============================================================================
${RUN_ID}: freeze CodeLlama-7B SVM+AST AGC detector
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Existing analyzer:               ${ANALYZER_SCRIPT}
Existing analyzer SHA256:        $(sha256_of "${ANALYZER_SCRIPT}")
A01 freeze auditor:              ${FREEZE_AUDITOR}
A01 freeze auditor SHA256:       $(sha256_of "${FREEZE_AUDITOR}")
Model pickle:                    ${MODEL_PICKLE}
Model pickle SHA256:             $(sha256_of "${MODEL_PICKLE}")
Validation test CSV:             ${TEST_CSV}
Validation test CSV SHA256:      $(sha256_of "${TEST_CSV}")
Experiment:                      ${EXPERIMENT}
Classifier:                      ${CLASSIFIER}
Representation:                  ${REPRESENTATION}
Score mode:                      ${SCORE_MODE}
Function threshold:              ${FUNCTION_THRESHOLD} (native SVM boundary)
Expected model key:              ${MODEL_KEY}
Max length:                      ${MAX_LEN}
Expected test rows:              ${EXPECTED_TEST_ROWS}
Expected ACC:                    ${EXPECTED_ACC}
Expected HWC F1:                 ${EXPECTED_HUMAN_F1}
Expected AGC F1:                 ${EXPECTED_AI_F1}
Expected Avg. F1:                ${EXPECTED_AVG_F1}
Expected AUROC:                  ${EXPECTED_AUROC}
Output root:                     ${OUTPUT_ROOT}
Device override:                 ${DEVICE:-<auto>}
Log file:                        ${LOG_FILE}
============================================================================
INFO

echo
echo "** Step 1: Run A01 freeze-auditor structural self-test"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" "${FREEZE_AUDITOR}" --self-test

echo
echo "** Step 2: Compile A01 Python freeze auditor"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" -m py_compile "${FREEZE_AUDITOR}"

VALIDATION_ROOT="${OUTPUT_ROOT}/validation"
VALIDATION_PREDICTIONS="${VALIDATION_ROOT}/validation_predictions.csv"
VALIDATION_METRICS="${VALIDATION_ROOT}/validation_metrics.csv"
VALIDATION_SUMMARY="${VALIDATION_ROOT}/validation_summary.txt"

if [[ "${MODE}" == "full" ]]; then
  echo
  echo "** Step 3: Reproduce the frozen CodeLlama-7B SVM+AST ground-truth benchmark"
  echo "----------------------------------------------------------------------------"
  ANALYZER_ARGS=(
    --experiment "${EXPERIMENT}"
    --classifier "${CLASSIFIER}"
    --representation "${REPRESENTATION}"
    --model-pickle "${MODEL_PICKLE}"
    --expected-model-key "${MODEL_KEY}"
    --expected-score-mode "${SCORE_MODE}"
    --threshold "${FUNCTION_THRESHOLD}"
    --max-len "${MAX_LEN}"
    --validation-test-csv "${TEST_CSV}"
    --validation-only
    --expected-test-rows "${EXPECTED_TEST_ROWS}"
    --expected-acc "${EXPECTED_ACC}"
    --expected-human-f1 "${EXPECTED_HUMAN_F1}"
    --expected-ai-f1 "${EXPECTED_AI_F1}"
    --expected-avg-f1 "${EXPECTED_AVG_F1}"
    --expected-auroc "${EXPECTED_AUROC}"
    --output-root "${OUTPUT_ROOT}"
  )

  if [[ -n "${DEVICE:-}" ]]; then
    ANALYZER_ARGS+=(--device "${DEVICE}")
  fi

  "${PYTHON_BIN}" "${ANALYZER_SCRIPT}" "${ANALYZER_ARGS[@]}"
else
  echo
  echo "** Step 3: Reuse existing ground-truth validation artifacts"
  echo "----------------------------------------------------------------------------"
  echo "MODE=${MODE}; CodeT5+ embedding and SVM inference are not rerun."
fi

require_file "${VALIDATION_PREDICTIONS}" "validation predictions"
require_file "${VALIDATION_METRICS}" "validation metrics"
require_file "${VALIDATION_SUMMARY}" "validation summary"

if [[ "${MODE}" != "verify" ]]; then
  echo
  echo "** Step 4: Freeze detector provenance, decision rule, and downstream contract"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${FREEZE_AUDITOR}" \
    --validation-predictions "${VALIDATION_PREDICTIONS}" \
    --validation-metrics "${VALIDATION_METRICS}" \
    --validation-summary "${VALIDATION_SUMMARY}" \
    --model-pickle "${MODEL_PICKLE}" \
    --test-csv "${TEST_CSV}" \
    --analyzer-script "${ANALYZER_SCRIPT}" \
    --expected-model-key "${MODEL_KEY}" \
    --max-len "${MAX_LEN}" \
    --output-root "${OUTPUT_ROOT}"
else
  echo
  echo "** Step 4: Skip freeze rewrite in read-only verify mode"
  echo "----------------------------------------------------------------------------"
fi

echo
echo "** Step 5: Verify A01 freeze outputs"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" "${FREEZE_AUDITOR}" \
  --verify-output \
  --expected-test-rows "${EXPECTED_TEST_ROWS}" \
  --expected-human-rows 450 \
  --expected-agc-rows 450 \
  --expected-acc "${EXPECTED_ACC}" \
  --expected-human-f1 "${EXPECTED_HUMAN_F1}" \
  --expected-ai-f1 "${EXPECTED_AI_F1}" \
  --expected-avg-f1 "${EXPECTED_AVG_F1}" \
  --expected-auroc "${EXPECTED_AUROC}" \
  --output-root "${OUTPUT_ROOT}"

END_EPOCH="$(date +%s)"
ELAPSED="$((END_EPOCH - START_EPOCH))"
COMPLETED_AT="$(date)"
printf -v ELAPSED_HMS '%02d:%02d:%02d' "$((ELAPSED / 3600))" "$(((ELAPSED % 3600) / 60))" "$((ELAPSED % 60))"

trap - ERR
cat <<INFO

============================================================================
${RUN_ID} execution summary
Mode:             ${MODE}
Started:          ${STARTED_AT}
Completed:        ${COMPLETED_AT}
Elapsed:          ${ELAPSED_HMS}
Exit code:        0
Output root:      ${OUTPUT_ROOT}
Log file:         ${LOG_FILE}
============================================================================
INFO
