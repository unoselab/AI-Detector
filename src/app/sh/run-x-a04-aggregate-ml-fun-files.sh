#!/usr/bin/env bash
# Aggregate exact run-x-a03 ML FUN predictions to the A05 historical Python-file universe.
#
# Workspace:
#   ai_detector repository root
#
# Canonical deployment paths:
#   src/app/sh/run-x-a04-aggregate-ml-fun-files.sh
#   src/app/py/aggregate_ml_fun_files.py
#
# Upstream frozen inputs:
#   1. A03 full ML function predictions:
#        src/app/data_did_agc_analysis/run-x-a03
#   2. A05 historical Python file manifest in the sibling NPR workspace:
#        ../detect_code_gpt/output/snapshot_npr/run-x-a05/python_file_manifest.csv
#
# Purpose:
#   - Reuse all 921,762 exact A03 FUN occurrence predictions.
#   - Aggregate them by snapshot_id + relative_path + file_sha256.
#   - Weight function predictions by the frozen A05/NPR function-body
#     literal-space-token count.
#   - Freeze the primary file rule before SonarQube/DiD outcomes:
#       file_ml_agc_share_space_by_token_weighted > 0.50
#   - Preserve prepared files with no FUN as unclassified (no_ml_fun), never HWC.
#   - Preserve A05 excluded/not-prepared files as unclassified.
#   - Report descriptive threshold support without selecting a threshold from outcomes.
#
# Frozen full-run counts:
#   - 921,762 A03 FUN occurrences.
#   - 290,926 AGC and 630,836 HWC function occurrences.
#   - 152,001,674 total FUN body literal-space tokens.
#   - 13,202,081 AGC FUN body literal-space tokens.
#   - 494,592 A05 Python file rows.
#   - 494,332 prepared Python file rows.
#   - 260 explicitly excluded/not-prepared file rows.
#   - 196,644 files with primary FUN occurrences.
#   - 297,688 prepared files with no primary FUN.
#
# Modes:
#   MODE=smoke   Emit the first SMOKE_MAX_FILES A05 file rows while still scanning
#                the complete A03 occurrence file for input/accounting validation.
#   MODE=full    Emit all 494,592 A05 Python file rows and the frozen primary
#                AGC-like file selection.
#   MODE=verify  Read-only strict verification of the completed full output.
#
# Outputs:
#   src/app/data_did_agc_analysis/run-x-a04[/ or -smoke]/
#     python_ml_fun_file_scores.csv
#     python_ml_fun_selected_files_primary.csv
#     python_ml_fun_threshold_support.csv
#     checks.csv
#     summary.json
#     metadata.json
#
# This experiment does NOT:
#   - rerun CodeT5+ or SVM inference,
#   - alter the function-level SVM decision boundary,
#   - select a file threshold using quality outcomes,
#   - access SonarQube outcomes,
#   - estimate a DiD model.
#
# Typical usage:
#   Smoke test:
#     MODE=smoke OVERWRITE=1 bash src/app/sh/run-x-a04-aggregate-ml-fun-files.sh
#
#   Full run:
#     MODE=full OVERWRITE=1 bash src/app/sh/run-x-a04-aggregate-ml-fun-files.sh
#
#   Read-only verification:
#     MODE=verify bash src/app/sh/run-x-a04-aggregate-ml-fun-files.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a04-v1"
MODE="${MODE:-smoke}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/aggregate_ml_fun_files.py}"
A03_ROOT="${A03_ROOT:-src/app/data_did_agc_analysis/run-x-a03}"
A05_ROOT="${A05_ROOT:-${REPO_ROOT}/../detect_code_gpt/output/snapshot_npr/run-x-a05}"
FULL_OUTPUT_ROOT="${FULL_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a04}"
SMOKE_OUTPUT_ROOT="${SMOKE_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a04-smoke}"
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

require_file "${PY_SCRIPT}" "run-x-a04 Python program"
require_file "${A03_ROOT}/summary.json" "A03 summary"
require_file "${A03_ROOT}/metadata.json" "A03 metadata"
require_file "${A03_ROOT}/ml_fun_occurrence_predictions.csv" "A03 occurrence predictions"
require_file "${A03_ROOT}/scoring_failures.csv" "A03 scoring failures"
require_file "${A05_ROOT}/python_file_manifest.csv" "A05 Python file manifest"

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
LOG_DIR="${LOG_DIR:-src/logs/run-x-a04}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a04-v1-${MODE}-aggregate-ml-fun-files-${RUN_TS}.log}"
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
${RUN_ID}: aggregate exact A03 ML FUN predictions to historical Python files
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Python script:                   ${PY_SCRIPT}
Python script SHA256:            $(sha256_of "${PY_SCRIPT}")
A03 root:                        ${A03_ROOT}
A03 summary SHA256:              $(sha256_of "${A03_ROOT}/summary.json")
A03 occurrence bytes:            $(stat -c '%s' "${A03_ROOT}/ml_fun_occurrence_predictions.csv")
A05 root:                        ${A05_ROOT}
A05 file manifest SHA256:        $(sha256_of "${A05_ROOT}/python_file_manifest.csv")
Current max files:               ${MAX_FILES}
Frozen primary metric:           file_ml_agc_share_space_by_token_weighted
Frozen primary threshold:        > ${PRIMARY_THRESHOLD}
Primary weight:                  npr_body_space_by_token_count
Descriptive support thresholds:  ${SUPPORT_THRESHOLDS}
No-FUN policy:                   blank / no_ml_fun (never HWC)
File-level quality access:       disabled
SonarQube/DiD outcome access:    disabled
Output root:                     ${OUTPUT_ROOT}
Log file:                        ${LOG_FILE}
============================================================================
INFO

COMMON_ARGS=(
  --a03-root "${A03_ROOT}"
  --a05-root "${A05_ROOT}"
  --output-root "${OUTPUT_ROOT}"
  --max-files "${MAX_FILES}"
  --primary-threshold "${PRIMARY_THRESHOLD}"
  --support-thresholds "${SUPPORT_THRESHOLDS}"
  --progress-every "${PROGRESS_EVERY}"
)

if [[ "${MODE}" == "verify" ]]; then
  echo
  echo "** Step 1: Strictly verify completed A04 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
else
  echo
  echo "** Step 1: Run A04 structural self-test"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" --self-test

  echo
  echo "** Step 2: Compile A04 Python program"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

  echo
  echo "** Step 3: Aggregate A03 FUN predictions to A05 historical Python files"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}"

  echo
  echo "** Step 4: Strictly verify A04 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
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
printf '============================================================================\n'
