#!/usr/bin/env bash
# Aggregate exact run-x-a06 ML C_FUN predictions to the NPR A05 historical Python-file universe.
#
# Workspace:
#   ai_detector repository root
#
# Canonical deployment paths:
#   src/app/sh/run-x-a07-aggregate-ml-cfun-files.sh
#   src/app/py/aggregate_ml_cfun_files.py
#
# Upstream frozen inputs:
#   1. A06 full ML C_FUN method predictions:
#        src/app/data_did_agc_analysis/run-x-a06
#   2. NPR A05 historical Python file manifest in the sibling NPR workspace:
#        ../detect_code_gpt/output/snapshot_npr/run-x-a05/python_file_manifest.csv
#
# Purpose:
#   - Reuse all 1,677,916 exact A06 C_FUN occurrence predictions.
#   - Aggregate them by snapshot_id + relative_path + file_sha256.
#   - Weight C_FUN method predictions by the frozen NPR A05 method-body
#     literal-space-token count.
#   - Freeze the primary file rule before SonarQube/DiD outcomes:
#       file_ml_cfun_agc_share_space_by_token_weighted > 0.50
#   - Preserve prepared files with no C_FUN as unclassified (no_ml_cfun), never HWC.
#   - Preserve NPR A05 excluded/not-prepared files as unclassified.
#   - Report descriptive threshold support without selecting a threshold from outcomes.
#
# Frozen full-run counts:
#   - 232,653 unique A06 standalone ML sources (all scored exactly once upstream).
#   - 1,677,916 A06 C_FUN occurrences.
#   - 526,910 AGC and 1,151,006 HWC C_FUN method occurrences.
#   - 327,251,880 total C_FUN method-body literal-space tokens.
#   - 23,686,235 AGC C_FUN method-body literal-space tokens.
#   - 494,592 NPR A05 Python file rows.
#   - 494,332 prepared Python file rows.
#   - 260 explicitly excluded/not-prepared file rows.
#   - 196,190 files with primary C_FUN occurrences.
#   - 298,142 prepared files with no primary C_FUN.
#
# Modes:
#   MODE=smoke   Emit the first SMOKE_MAX_FILES NPR A05 file rows while still scanning
#                the complete A06 occurrence file for input/accounting validation.
#   MODE=full    Emit all 494,592 NPR A05 Python file rows and the frozen primary
#                AGC-like file selection.
#   MODE=verify  Read-only strict verification of the completed full output.
#
# Outputs:
#   src/app/data_did_agc_analysis/run-x-a07[/ or -smoke]/
#     python_ml_cfun_file_scores.csv
#     python_ml_cfun_selected_files_primary.csv
#     python_ml_cfun_threshold_support.csv
#     checks.csv
#     summary.json
#     metadata.json
#
# This experiment does NOT:
#   - rerun CodeT5+ or SVM inference,
#   - alter the C_FUN method-level SVM decision boundary,
#   - select a file threshold using quality outcomes,
#   - access SonarQube outcomes,
#   - estimate a DiD model.
#
# Typical usage:
#   Smoke test:
#     MODE=smoke OVERWRITE=1 bash src/app/sh/run-x-a07-aggregate-ml-cfun-files.sh
#
#   Full run:
#     MODE=full OVERWRITE=1 bash src/app/sh/run-x-a07-aggregate-ml-cfun-files.sh
#
#   Read-only verification:
#     MODE=verify bash src/app/sh/run-x-a07-aggregate-ml-cfun-files.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a07-v1"
MODE="${MODE:-smoke}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/aggregate_ml_cfun_files.py}"
A06_ROOT="${A06_ROOT:-src/app/data_did_agc_analysis/run-x-a06}"
A05_ROOT="${A05_ROOT:-${REPO_ROOT}/../detect_code_gpt/output/snapshot_npr/run-x-a05}"
FULL_OUTPUT_ROOT="${FULL_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a07}"
SMOKE_OUTPUT_ROOT="${SMOKE_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a07-smoke}"
SMOKE_MAX_FILES="${SMOKE_MAX_FILES:-2000}"
PRIMARY_THRESHOLD="${PRIMARY_THRESHOLD:-0.50}"
SUPPORT_THRESHOLDS="${SUPPORT_THRESHOLDS:-0.00,0.25,0.50,0.75}"
PROGRESS_EVERY="${PROGRESS_EVERY:-100000}"
OVERWRITE="${OVERWRITE:-0}"

case "${MODE}" in
  smoke)
    OUTPUT_ROOT="${SMOKE_OUTPUT_ROOT}"
    MAX_FILES="${SMOKE_MAX_FILES}"
    ;;
  full)
    OUTPUT_ROOT="${FULL_OUTPUT_ROOT}"
    MAX_FILES="0"
    ;;
  verify)
    OUTPUT_ROOT="${FULL_OUTPUT_ROOT}"
    MAX_FILES="0"
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

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

require_file "${PY_SCRIPT}" "run-x-a07 Python program"
require_file "${A06_ROOT}/summary.json" "A06 summary"
require_file "${A06_ROOT}/metadata.json" "A06 metadata"
require_file "${A06_ROOT}/ml_cfun_occurrence_predictions.csv" "A06 occurrence predictions"
require_file "${A06_ROOT}/scoring_failures.csv" "A06 scoring failures"
require_file "${A05_ROOT}/python_file_manifest.csv" "NPR A05 Python file manifest"

if [[ "${MODE}" != "verify" ]]; then
  if [[ -e "${OUTPUT_ROOT}" ]]; then
    if [[ "${OVERWRITE}" == "1" ]]; then
      rm -rf "${OUTPUT_ROOT}"
    else
      echo "[ERROR] output root exists; use OVERWRITE=1 for an intentional fresh run: ${OUTPUT_ROOT}" >&2
      exit 2
    fi
  fi
  mkdir -p "${OUTPUT_ROOT}"
fi

RUN_TS="${RUN_TS:-$(date +'%Y%m%d-%H%M%S')}"
LOG_DIR="${LOG_DIR:-src/logs/run-x-a07}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a07-v1-${MODE}-aggregate-ml-cfun-files-${RUN_TS}.log}"
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
${RUN_ID}: aggregate exact A06 ML C_FUN predictions to historical Python files
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Python script:                   ${PY_SCRIPT}
Python script SHA256:            $(sha256_of "${PY_SCRIPT}")
A06 root:                        ${A06_ROOT}
A06 summary SHA256:              $(sha256_of "${A06_ROOT}/summary.json")
A06 occurrence bytes:            $(stat -c '%s' "${A06_ROOT}/ml_cfun_occurrence_predictions.csv")
NPR A05 root:                    ${A05_ROOT}
NPR A05 file manifest SHA256:   $(sha256_of "${A05_ROOT}/python_file_manifest.csv")
Current max files:               ${MAX_FILES}
Frozen primary metric:           file_ml_cfun_agc_share_space_by_token_weighted
Frozen primary threshold:        > ${PRIMARY_THRESHOLD}
Primary weight:                  npr_body_space_by_token_count
Descriptive support thresholds:  ${SUPPORT_THRESHOLDS}
No-C_FUN policy:                 blank / no_ml_cfun (never HWC)
File-level quality access:       disabled
SonarQube/DiD outcome access:    disabled
Output root:                     ${OUTPUT_ROOT}
Log file:                        ${LOG_FILE}
============================================================================
INFO

COMMON_ARGS=(
  --a06-root "${A06_ROOT}"
  --a05-root "${A05_ROOT}"
  --output-root "${OUTPUT_ROOT}"
  --max-files "${MAX_FILES}"
  --primary-threshold "${PRIMARY_THRESHOLD}"
  --support-thresholds "${SUPPORT_THRESHOLDS}"
  --progress-every "${PROGRESS_EVERY}"
)

if [[ "${MODE}" == "verify" ]]; then
  echo
  echo "** Step 1: Strictly verify completed A07 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" -u "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
else
  echo
  echo "** Step 1: Run A07 structural self-test"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" -u "${PY_SCRIPT}" --self-test

  echo
  echo "** Step 2: Compile A07 Python program"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

  echo
  echo "** Step 3: Aggregate A06 C_FUN predictions to NPR A05 historical Python files"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" -u "${PY_SCRIPT}" "${COMMON_ARGS[@]}"

  echo
  echo "** Step 4: Strictly verify A07 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" -u "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
fi

END_EPOCH="$(date +%s)"
ELAPSED="$((END_EPOCH - START_EPOCH))"
HOURS="$((ELAPSED / 3600))"
MINUTES="$(((ELAPSED % 3600) / 60))"
SECONDS="$((ELAPSED % 60))"
COMPLETED_AT="$(date)"

printf '\n============================================================================\n'
printf '%s\n' "${RUN_ID} execution summary"
printf 'Mode:             %s\n' "${MODE}"
printf 'Started:          %s\n' "${STARTED_AT}"
printf 'Completed:        %s\n' "${COMPLETED_AT}"
printf 'Elapsed:          %02d:%02d:%02d\n' "${HOURS}" "${MINUTES}" "${SECONDS}"
printf 'Exit code:        0\n'
printf 'Output root:      %s\n' "${OUTPUT_ROOT}"
printf 'Log file:         %s\n' "${LOG_FILE}"
printf 'Next after PASS:  run-x-h05 build C_FUN ML quality-burden panel\n'
printf '============================================================================\n'
