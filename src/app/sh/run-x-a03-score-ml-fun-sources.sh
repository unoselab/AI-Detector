#!/usr/bin/env bash
# Score the exact A02 standalone Python FUN sources with the frozen A01 detector.
#
# Workspace:
#   ai_detector repository root
#
# Canonical deployment paths:
#   src/app/sh/run-x-a03-score-ml-fun-sources.sh
#   src/app/py/score_ml_fun_sources.py
#
# Upstream frozen inputs:
#   1. A01 detector freeze output:
#        src/app/data_did_agc_analysis/run-x-a01
#   2. A02 repaired exact FUN-to-standalone-source mapping:
#        src/app/data_did_agc_analysis/run-x-a02
#
# Purpose:
#   - Reuse the detector implementation frozen by A01.
#   - Score each unique A02 ml_source_sha256 exactly once.
#   - Preserve the native SVM human decision boundary at 0.0.
#   - Save ml_agc_score = -human_decision_score.
#   - Expand each unique-source prediction back to all exact A02 FUN occurrences.
#
# Primary full-run input counts frozen by A02:
#   - 117,560 unique standalone ML function sources.
#   - 921,762 exact A05 primary FUN occurrences.
#   - 105,635 unique NPR function-body SHA values.
#
# Modes:
#   MODE=smoke   Score the first SMOKE_MAX_SOURCES unique A02 sources and expand
#                only occurrences that reference those sources. Uses a separate
#                output root and does not modify the full A03 output.
#   MODE=full    Score all 117,560 unique sources and expand predictions to all
#                921,762 FUN occurrences.
#   MODE=verify  Read-only verification of the completed full A03 output.
#
# Resume behavior:
#   The Python program stores deterministic source-prediction chunks. If a full
#   run is interrupted, rerun with RESUME=1 and OVERWRITE=0. A chunk is reused
#   only when its exact source-SHA list and frozen detector fingerprint match.
#
# Outputs:
#   src/app/data_did_agc_analysis/run-x-a03[/ or -smoke]/
#     ml_fun_unique_source_predictions.csv
#     ml_fun_occurrence_predictions.csv
#     scoring_failures.csv
#     source_prediction_chunks/
#     checks.csv
#     summary.json
#     metadata.json
#
# This experiment does NOT:
#   - retrain or tune the SVM,
#   - calibrate a new threshold,
#   - aggregate predictions to files,
#   - access SonarQube outcomes,
#   - estimate a DiD model.
#
# Typical usage:
#   Smoke test:
#     MODE=smoke OVERWRITE=1 \
#       bash src/app/sh/run-x-a03-score-ml-fun-sources.sh
#
#   First full run:
#     MODE=full OVERWRITE=1 \
#       bash src/app/sh/run-x-a03-score-ml-fun-sources.sh
#
#   Resume an interrupted full run:
#     MODE=full RESUME=1 OVERWRITE=0 \
#       bash src/app/sh/run-x-a03-score-ml-fun-sources.sh
#
#   Read-only verification:
#     MODE=verify \
#       bash src/app/sh/run-x-a03-score-ml-fun-sources.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a03-v1"
MODE="${MODE:-smoke}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/score_ml_fun_sources.py}"
A01_ROOT="${A01_ROOT:-src/app/data_did_agc_analysis/run-x-a01}"
A02_ROOT="${A02_ROOT:-src/app/data_did_agc_analysis/run-x-a02}"
TREE_SITTER_LIB="${TREE_SITTER_LIB:-src/code-analyzer-tree-sitter/build/my-languages.so}"
AST_HELPER_DIR="${AST_HELPER_DIR:-src/code-analyzer-tree-sitter}"
FULL_OUTPUT_ROOT="${FULL_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a03}"
SMOKE_OUTPUT_ROOT="${SMOKE_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a03-smoke}"
EXPECTED_OCCURRENCES="${EXPECTED_OCCURRENCES:-921762}"
EXPECTED_UNIQUE_ML_SOURCES="${EXPECTED_UNIQUE_ML_SOURCES:-117560}"
EXPECTED_UNIQUE_NPR_BODY_SHA="${EXPECTED_UNIQUE_NPR_BODY_SHA:-105635}"
SMOKE_MAX_SOURCES="${SMOKE_MAX_SOURCES:-500}"
CHUNK_SIZE="${CHUNK_SIZE:-500}"
PROGRESS_EVERY="${PROGRESS_EVERY:-500}"
COMPATIBILITY_CHECK_ROWS="${COMPATIBILITY_CHECK_ROWS:-32}"
COMPATIBILITY_SCORE_TOLERANCE="${COMPATIBILITY_SCORE_TOLERANCE:-0.00001}"
DEVICE="${DEVICE:-}"
RESUME="${RESUME:-1}"
OVERWRITE="${OVERWRITE:-0}"

case "${MODE}" in
  smoke)
    OUTPUT_ROOT="${SMOKE_OUTPUT_ROOT}"
    MAX_SOURCES="${SMOKE_MAX_SOURCES}"
    ;;
  full)
    OUTPUT_ROOT="${FULL_OUTPUT_ROOT}"
    MAX_SOURCES="0"
    ;;
  verify)
    OUTPUT_ROOT="${FULL_OUTPUT_ROOT}"
    MAX_SOURCES="0"
    ;;
  *)
    echo "[ERROR] unsupported MODE=${MODE}; expected smoke, full, or verify" >&2
    exit 2
    ;;
esac

require_file() {
  local path="$1"
  local label="$2"
  if [[ ! -f "${path}" ]]; then
    echo "[ERROR] ${label} not found: ${path}" >&2
    exit 2
  fi
}

require_dir() {
  local path="$1"
  local label="$2"
  if [[ ! -d "${path}" ]]; then
    echo "[ERROR] ${label} not found: ${path}" >&2
    exit 2
  fi
}

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

require_file "${PY_SCRIPT}" "run-x-a03 Python program"
require_file "${A01_ROOT}/detector_freeze_summary.json" "A01 freeze summary"
require_file "${A01_ROOT}/detector_freeze_metadata.json" "A01 freeze metadata"
require_file "${A01_ROOT}/validation/validation_predictions.csv" "A01 validation predictions"
require_file "${A02_ROOT}/summary.json" "A02 summary"
require_file "${A02_ROOT}/python_ml_fun_unique_source_manifest.csv" "A02 unique-source manifest"
require_file "${A02_ROOT}/python_ml_fun_occurrence_manifest.csv" "A02 occurrence manifest"
require_file "${A02_ROOT}/python_ml_fun_mapping_failures.csv" "A02 mapping failure manifest"

if [[ "${MODE}" != "verify" ]]; then
  require_file "${TREE_SITTER_LIB}" "Tree-sitter language library"
  require_dir "${AST_HELPER_DIR}" "AST helper directory"
fi

RUN_TS="${RUN_TS:-$(date +'%Y%m%d-%H%M%S')}"
LOG_DIR="${LOG_DIR:-src/logs/run-x-a03}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a03-v1-${MODE}-score-ml-fun-sources-${RUN_TS}.log}"
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

START_EPOCH="$(date +%s)"
STARTED_AT="$(date)"

cat <<INFO
============================================================================
${RUN_ID}: score frozen CodeLlama-7B SVM+AST on exact A02 FUN sources
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Python script:                   ${PY_SCRIPT}
Python script SHA256:            $(sha256_of "${PY_SCRIPT}")
A01 freeze root:                 ${A01_ROOT}
A01 summary SHA256:              $(sha256_of "${A01_ROOT}/detector_freeze_summary.json")
A01 metadata SHA256:             $(sha256_of "${A01_ROOT}/detector_freeze_metadata.json")
A02 repaired root:               ${A02_ROOT}
A02 summary SHA256:              $(sha256_of "${A02_ROOT}/summary.json")
A02 unique-source SHA256:        $(sha256_of "${A02_ROOT}/python_ml_fun_unique_source_manifest.csv")
Expected unique ML sources:      ${EXPECTED_UNIQUE_ML_SOURCES}
Expected FUN occurrences:        ${EXPECTED_OCCURRENCES}
Expected unique NPR body SHA:    ${EXPECTED_UNIQUE_NPR_BODY_SHA}
Current max sources:             ${MAX_SOURCES}
Chunk size:                      ${CHUNK_SIZE}
Compatibility rows:              ${COMPATIBILITY_CHECK_ROWS}
Compatibility score tolerance:   ${COMPATIBILITY_SCORE_TOLERANCE}
Tree-sitter library:             ${TREE_SITTER_LIB}
Device override:                 ${DEVICE:-<auto>}
Resume prediction chunks:        ${RESUME}
Overwrite output:                ${OVERWRITE}
Output root:                     ${OUTPUT_ROOT}
File-level aggregation:          disabled; deferred to run-x-a04
SonarQube/DiD outcome access:    disabled
Log file:                        ${LOG_FILE}
============================================================================
INFO

COMMON_ARGS=(
  --a01-root "${A01_ROOT}"
  --a02-root "${A02_ROOT}"
  --output-root "${OUTPUT_ROOT}"
  --max-sources "${MAX_SOURCES}"
  --expected-occurrences "${EXPECTED_OCCURRENCES}"
  --expected-unique-ml-sources "${EXPECTED_UNIQUE_ML_SOURCES}"
  --expected-unique-npr-body-sha "${EXPECTED_UNIQUE_NPR_BODY_SHA}"
)

if [[ "${MODE}" == "verify" ]]; then
  echo
  echo "** Step 1: Strictly verify completed A03 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
else
  echo
  echo "** Step 1: Run A03 structural self-test"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" --self-test

  echo
  echo "** Step 2: Compile A03 Python program"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

  echo
  echo "** Step 3: Score unique A02 standalone-function sources and expand to FUN occurrences"
  echo "----------------------------------------------------------------------------"
  SCORE_ARGS=(
    "${COMMON_ARGS[@]}"
    --tree-sitter-lib "${TREE_SITTER_LIB}"
    --ast-helper-dir "${AST_HELPER_DIR}"
    --chunk-size "${CHUNK_SIZE}"
    --progress-every "${PROGRESS_EVERY}"
    --compatibility-check-rows "${COMPATIBILITY_CHECK_ROWS}"
    --compatibility-score-tolerance "${COMPATIBILITY_SCORE_TOLERANCE}"
  )
  if [[ -n "${DEVICE}" ]]; then
    SCORE_ARGS+=(--device "${DEVICE}")
  fi
  if [[ "${RESUME}" == "1" ]]; then
    SCORE_ARGS+=(--resume)
  fi
  if [[ "${OVERWRITE}" == "1" ]]; then
    SCORE_ARGS+=(--overwrite)
  fi
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${SCORE_ARGS[@]}"

  echo
  echo "** Step 4: Strictly verify A03 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
fi

END_EPOCH="$(date +%s)"
COMPLETED_AT="$(date)"
ELAPSED="$((END_EPOCH - START_EPOCH))"
printf -v ELAPSED_FMT '%02d:%02d:%02d' "$((ELAPSED / 3600))" "$(((ELAPSED % 3600) / 60))" "$((ELAPSED % 60))"

cat <<INFO

============================================================================
${RUN_ID} execution summary
Mode:             ${MODE}
Started:          ${STARTED_AT}
Completed:        ${COMPLETED_AT}
Elapsed:          ${ELAPSED_FMT}
Exit code:        0
Output root:      ${OUTPUT_ROOT}
Log file:         ${LOG_FILE}
============================================================================
INFO
