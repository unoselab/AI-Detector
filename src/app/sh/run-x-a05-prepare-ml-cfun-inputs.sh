#!/usr/bin/env bash
# Prepare frozen historical C_FUN occurrences for the existing ML AGC detector.
#
# Workspace:
#   /home/user1-system12/project-workspace/ai_detector
#
# Delivery source names:
#   src/app/sh/run-x-a05-prepare-ml-cfun-inputs-v2.sh
#   src/app/py/prepare_ml_cfun_inputs-v1.py
#
# Canonical production deployment names:
#   src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh
#   src/app/py/prepare_ml_cfun_inputs.py
#
# Frozen upstream inputs:
#   1. A01 ML detector freeze:
#        src/app/data_did_agc_analysis/run-x-a01
#   2. detect_code_gpt NPR A05 historical Python preparation:
#        ../detect_code_gpt/output/snapshot_npr/run-x-a05
#   3. detect_code_gpt NPR A13 C_FUN membership audit:
#        ../detect_code_gpt/output/snapshot_npr/run-x-a13/summary.json
#
# Scientific purpose:
#   - Reuse the exact A05 historical repository/snapshot/Python-file universe.
#   - Select only A05 primary method_body occurrences (C_FUN).
#   - Reverify the historical file SHA-256, method-body SHA-256, and frozen
#     literal-space-token count before constructing an ML detector input.
#   - Reconstruct a detector-native standalone method source from the matching
#     direct class method, including decorators when present.
#   - Validate that the existing frozen Tree-sitter/AST detector pipeline sees
#     exactly one full-source function_definition with the expected method name.
#   - Deduplicate standalone method sources by ml_source_sha256 for A06 scoring.
#
# Frozen full-corpus gates:
#   C_FUN occurrences:             1,677,916
#   Unique C_FUN body SHA values:    195,193
#   Snapshot/files with C_FUN:        196,190
#   NPR A05 code manifest SHA256:
#     1acb3726f5c62e6154672f1aff592973c65a13e58dbfd37f8058560d1a474e6c
#
# Modes:
#   MODE=smoke
#     Scan the complete frozen C_FUN universe and map SMOKE_MAX_OCCURRENCES
#     deterministic positions spread across that order into run-x-a05-smoke.
#     Use this first to validate method-source reconstruction across the corpus.
#
#   MODE=full
#     Prepare all 1,677,916 C_FUN occurrences into canonical run-x-a05.
#     Full mode enables strict frozen-count gates.
#
#   MODE=verify
#     Read-only verification of the completed canonical run-x-a05 output.
#
# Outputs for MODE=full:
#   src/app/data_did_agc_analysis/run-x-a05/
#     python_ml_cfun_occurrence_manifest.csv
#     python_ml_cfun_unique_source_manifest.csv
#     python_ml_cfun_mapping_failures.csv
#     ml_cfun_sources/<sha-prefix>/<sha256>.py
#     checks.csv
#     summary.json
#     metadata.json
#
# This experiment does NOT:
#   - retrain or tune the frozen SVM,
#   - load CodeT5+ or run classifier inference,
#   - change the A01 decision boundary,
#   - change the A05 method-body identity or size weights,
#   - access SonarQube quality outcomes,
#   - estimate a DiD model.
#
# Typical first run:
#   MODE=smoke OVERWRITE=1 \
#     bash src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh
#
# Full production after smoke review:
#   MODE=full OVERWRITE=1 \
#     bash src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh
#
# Read-only verification:
#   MODE=verify \
#     bash src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a05-v2"
MODE="${MODE:-smoke}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/prepare_ml_cfun_inputs.py}"
A01_ROOT="${A01_ROOT:-src/app/data_did_agc_analysis/run-x-a01}"
TREE_SITTER_LIB="${TREE_SITTER_LIB:-src/code-analyzer-tree-sitter/build/my-languages.so}"
AST_HELPER_DIR="${AST_HELPER_DIR:-src/code-analyzer-tree-sitter}"

EXPECTED_CFUN_OCCURRENCES="${EXPECTED_CFUN_OCCURRENCES:-1677916}"
EXPECTED_UNIQUE_CFUN_BODY_SHA="${EXPECTED_UNIQUE_CFUN_BODY_SHA:-195193}"
EXPECTED_FILES_WITH_CFUN="${EXPECTED_FILES_WITH_CFUN:-196190}"
EXPECTED_A05_MANIFEST_SHA256="${EXPECTED_A05_MANIFEST_SHA256:-1acb3726f5c62e6154672f1aff592973c65a13e58dbfd37f8058560d1a474e6c}"
SMOKE_MAX_OCCURRENCES="${SMOKE_MAX_OCCURRENCES:-1000}"
MAX_OPEN_GIT_PROCESSES="${MAX_OPEN_GIT_PROCESSES:-4}"
PROGRESS_EVERY="${PROGRESS_EVERY:-10000}"
OVERWRITE="${OVERWRITE:-0}"
CLONE_PATH_PREFIX_FROM="${CLONE_PATH_PREFIX_FROM:-}"
CLONE_PATH_PREFIX_TO="${CLONE_PATH_PREFIX_TO:-}"

case "${MODE}" in
  smoke)
    OUTPUT_ROOT="${OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a05-smoke}"
    MAX_OCCURRENCES="${SMOKE_MAX_OCCURRENCES}"
    STRICT_EXPECTED_COUNTS=0
    ;;
  full)
    OUTPUT_ROOT="${OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a05}"
    MAX_OCCURRENCES=0
    STRICT_EXPECTED_COUNTS=1
    ;;
  verify)
    OUTPUT_ROOT="${OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a05}"
    MAX_OCCURRENCES=0
    STRICT_EXPECTED_COUNTS=1
    ;;
  *)
    echo "[ERROR] unsupported MODE=${MODE}; expected smoke, full, or verify" >&2
    exit 2
    ;;
esac

# Locate the frozen detect_code_gpt NPR A05 and A13 artifacts without depending
# on another wrapper script. Explicit environment variables always win.
NPR_A05_ROOT="${NPR_A05_ROOT:-}"
if [[ -z "${NPR_A05_ROOT}" ]]; then
  A05_CANDIDATES=(
    "${REPO_ROOT}/../detect_code_gpt/output/snapshot_npr/run-x-a05"
    "/home/user1-system12/project-workspace/detect_code_gpt/output/snapshot_npr/run-x-a05"
    "/home/user1-system11/project-workspace/detect_code_gpt/output/snapshot_npr/run-x-a05"
  )
  for candidate in "${A05_CANDIDATES[@]}"; do
    if [[ -f "${candidate}/python_code_unit_manifest.csv" && -f "${candidate}/snapshot_status.csv" ]]; then
      NPR_A05_ROOT="${candidate}"
      break
    fi
  done
fi

NPR_A13_ROOT="${NPR_A13_ROOT:-}"
if [[ -z "${NPR_A13_ROOT}" ]]; then
  A13_CANDIDATES=(
    "${REPO_ROOT}/../detect_code_gpt/output/snapshot_npr/run-x-a13"
    "/home/user1-system12/project-workspace/detect_code_gpt/output/snapshot_npr/run-x-a13"
    "/home/user1-system11/project-workspace/detect_code_gpt/output/snapshot_npr/run-x-a13"
  )
  for candidate in "${A13_CANDIDATES[@]}"; do
    if [[ -f "${candidate}/summary.json" ]]; then
      NPR_A13_ROOT="${candidate}"
      break
    fi
  done
fi

if [[ -z "${NPR_A05_ROOT}" ]]; then
  echo "[ERROR] could not locate detect_code_gpt NPR run-x-a05." >&2
  echo "        Set NPR_A05_ROOT to the directory containing:" >&2
  echo "          snapshot_status.csv" >&2
  echo "          python_code_unit_manifest.csv" >&2
  exit 2
fi
if [[ -z "${NPR_A13_ROOT}" ]]; then
  echo "[ERROR] could not locate detect_code_gpt NPR run-x-a13." >&2
  echo "        Set NPR_A13_ROOT to the directory containing summary.json." >&2
  exit 2
fi
A13_SUMMARY_FILE="${A13_SUMMARY_FILE:-${NPR_A13_ROOT}/summary.json}"

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

csv_records() {
  "${PYTHON_BIN}" - "$1" <<'PY'
import csv
import sys
with open(sys.argv[1], "r", encoding="utf-8", newline="") as handle:
    print(sum(1 for _ in csv.DictReader(handle)))
PY
}

require_file "${PY_SCRIPT}" "run-x-a05 Python program"
require_file "${A01_ROOT}/detector_freeze_summary.json" "A01 freeze summary"
require_file "${A01_ROOT}/detector_freeze_metadata.json" "A01 freeze metadata"
require_file "${NPR_A05_ROOT}/snapshot_status.csv" "NPR A05 snapshot status"
require_file "${NPR_A05_ROOT}/python_code_unit_manifest.csv" "NPR A05 code-unit manifest"
require_file "${A13_SUMMARY_FILE}" "NPR A13 C_FUN summary"

if [[ "${MODE}" != "verify" ]]; then
  require_file "${TREE_SITTER_LIB}" "Tree-sitter language library"
  require_dir "${AST_HELPER_DIR}" "Tree-sitter AST helper directory"
fi

if [[ -n "${CLONE_PATH_PREFIX_FROM}" || -n "${CLONE_PATH_PREFIX_TO}" ]]; then
  if [[ -z "${CLONE_PATH_PREFIX_FROM}" || -z "${CLONE_PATH_PREFIX_TO}" ]]; then
    echo "[ERROR] both CLONE_PATH_PREFIX_FROM and CLONE_PATH_PREFIX_TO are required together." >&2
    exit 2
  fi
fi

if [[ "${MODE}" != "verify" && -e "${OUTPUT_ROOT}" && "${OVERWRITE}" != "1" ]]; then
  echo "[ERROR] output already exists: ${OUTPUT_ROOT}" >&2
  echo "        Use OVERWRITE=1 for an intentional clean rerun." >&2
  exit 2
fi

RUN_TS="${RUN_TS:-$(date +'%Y%m%d-%H%M%S')}"
LOG_DIR="${LOG_DIR:-src/logs/run-x-a05}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a05-v2-${MODE}-prepare-ml-cfun-inputs-${RUN_TS}.log}"
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
${RUN_ID}: prepare frozen C_FUN sources for ML detector inference
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Python script:                   ${PY_SCRIPT}
Python script SHA256:            $(sha256_of "${PY_SCRIPT}")
A01 freeze root:                 ${A01_ROOT}
A01 summary SHA256:              $(sha256_of "${A01_ROOT}/detector_freeze_summary.json")
NPR A05 root:                    ${NPR_A05_ROOT}
A05 manifest SHA256:             $(sha256_of "${NPR_A05_ROOT}/python_code_unit_manifest.csv")
Expected A05 manifest SHA256:    ${EXPECTED_A05_MANIFEST_SHA256}
NPR A13 root:                    ${NPR_A13_ROOT}
A13 summary SHA256:              $(sha256_of "${A13_SUMMARY_FILE}")
C_FUN filter:                    aggregation_role=primary; code_unit_type=method_body
Expected C_FUN occurrences:      ${EXPECTED_CFUN_OCCURRENCES}
Expected unique C_FUN body SHA:  ${EXPECTED_UNIQUE_CFUN_BODY_SHA}
Expected files with C_FUN:       ${EXPECTED_FILES_WITH_CFUN}
Current max occurrences:         ${MAX_OCCURRENCES}
Smoke selection:                 deterministic spread over full C_FUN order
Standalone normalization:        physical-line start -> dedent; decorator/def column-0 gate
Tree-sitter library:             ${TREE_SITTER_LIB}
Max open Git batch processes:    ${MAX_OPEN_GIT_PROCESSES}
Clone path prefix from:          ${CLONE_PATH_PREFIX_FROM:-<none>}
Clone path prefix to:            ${CLONE_PATH_PREFIX_TO:-<none>}
Progress every:                  ${PROGRESS_EVERY}
Output root:                     ${OUTPUT_ROOT}
Standalone source root:          ${OUTPUT_ROOT}/ml_cfun_sources
CodeT5+ embedding:               disabled; deferred to A06
SVM inference:                   disabled; deferred to A06
File aggregation:                disabled; deferred to A07
SonarQube/DiD outcome access:    disabled
Log file:                        ${LOG_FILE}
============================================================================
INFO

echo
echo "** Step 1: Run A05 structural self-test"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" "${PY_SCRIPT}" --self-test

echo
echo "** Step 2: Compile A05 Python program"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

COMMON_ARGS=(
  --mode "${MODE}"
  --repo-root "${REPO_ROOT}"
  --a01-root "${A01_ROOT}"
  --npr-a05-root "${NPR_A05_ROOT}"
  --a13-summary-file "${A13_SUMMARY_FILE}"
  --output-root "${OUTPUT_ROOT}"
  --tree-sitter-lib "${TREE_SITTER_LIB}"
  --ast-helper-dir "${AST_HELPER_DIR}"
  --expected-occurrences "${EXPECTED_CFUN_OCCURRENCES}"
  --expected-unique-body-sha "${EXPECTED_UNIQUE_CFUN_BODY_SHA}"
  --expected-files-with-cfun "${EXPECTED_FILES_WITH_CFUN}"
  --expected-a05-manifest-sha256 "${EXPECTED_A05_MANIFEST_SHA256}"
  --max-occurrences "${MAX_OCCURRENCES}"
  --max-open-git-processes "${MAX_OPEN_GIT_PROCESSES}"
  --progress-every "${PROGRESS_EVERY}"
)

if [[ "${STRICT_EXPECTED_COUNTS}" == "1" ]]; then
  COMMON_ARGS+=(--strict-expected-counts)
fi
if [[ "${OVERWRITE}" == "1" && "${MODE}" != "verify" ]]; then
  COMMON_ARGS+=(--overwrite)
fi
if [[ -n "${CLONE_PATH_PREFIX_FROM}" ]]; then
  COMMON_ARGS+=(
    --clone-path-prefix-from "${CLONE_PATH_PREFIX_FROM}"
    --clone-path-prefix-to "${CLONE_PATH_PREFIX_TO}"
  )
fi

if [[ "${MODE}" == "verify" ]]; then
  echo
  echo "** Step 3: Read-only verification of canonical A05 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}"
else
  echo
  echo "** Step 3: Prepare exact historical C_FUN standalone ML sources"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}"

  echo
  echo "** Step 4: Verify generated A05 artifacts"
  echo "----------------------------------------------------------------------------"
  require_file "${OUTPUT_ROOT}/summary.json" "A05 summary"
  require_file "${OUTPUT_ROOT}/metadata.json" "A05 metadata"
  require_file "${OUTPUT_ROOT}/checks.csv" "A05 checks"
  require_file "${OUTPUT_ROOT}/python_ml_cfun_occurrence_manifest.csv" "A05 C_FUN occurrence manifest"
  require_file "${OUTPUT_ROOT}/python_ml_cfun_unique_source_manifest.csv" "A05 C_FUN unique source manifest"
  require_file "${OUTPUT_ROOT}/python_ml_cfun_mapping_failures.csv" "A05 mapping failure manifest"

  OCCURRENCE_ROWS="$(csv_records "${OUTPUT_ROOT}/python_ml_cfun_occurrence_manifest.csv")"
  UNIQUE_SOURCE_ROWS="$(csv_records "${OUTPUT_ROOT}/python_ml_cfun_unique_source_manifest.csv")"
  FAILURE_ROWS="$(csv_records "${OUTPUT_ROOT}/python_ml_cfun_mapping_failures.csv")"
  echo "Occurrence manifest records:    ${OCCURRENCE_ROWS}"
  echo "Unique-source manifest records: ${UNIQUE_SOURCE_ROWS}"
  echo "Mapping failure records:        ${FAILURE_ROWS}"

  "${PYTHON_BIN}" - "${OUTPUT_ROOT}/summary.json" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    s = json.load(handle)
print("A05 summary status:             " + str(s.get("status")))
print("Selected C_FUN occurrences:     " + str(s.get("selected_occurrences")))
print("Mapped C_FUN occurrences:       " + str(s.get("mapped_occurrences")))
print("Unique C_FUN body SHA:          " + str(s.get("unique_npr_body_sha")))
print("Unique standalone ML sources:   " + str(s.get("unique_ml_source_sha")))
print("Files with C_FUN:               " + str(s.get("files_with_cfun")))
print("Mapping warnings:               " + str(s.get("warning_occurrences")))
print("Mapping failures:               " + str(s.get("mapping_failures")))
print("A05-end override occurrences:   " + str(s.get("a05_end_override_occurrences")))
print("Decorated method occurrences:   " + str(s.get("decorated_method_occurrences")))
print("Decorator alignment failures:   " + str(s.get("decorator_alignment_failures")))
print("Definition alignment failures:  " + str(s.get("definition_alignment_failures")))
print("Sample dataset-source counts:   " + str(s.get("sample_dataset_source_counts")))
print("Sample repositories:            " + str(s.get("sample_repositories")))
print("Full C_FUN universe scanned:    " + str(s.get("universe_cfun_occurrences_scanned")))
print("Hard QC failures:               " + str(s.get("failed_hard_checks")))
PY
fi

END_EPOCH="$(date +%s)"
ELAPSED="$((END_EPOCH - START_EPOCH))"
printf -v ELAPSED_TEXT '%02d:%02d:%02d' "$((ELAPSED / 3600))" "$(((ELAPSED % 3600) / 60))" "$((ELAPSED % 60))"

echo
cat <<INFO
============================================================================
${RUN_ID} execution summary
Mode:             ${MODE}
Started:          ${STARTED_AT}
Completed:        $(date)
Elapsed:          ${ELAPSED_TEXT}
Exit code:        0
Output root:      ${OUTPUT_ROOT}
Log file:         ${LOG_FILE}
Next after PASS:  run-x-a06 score frozen ML detector on unique C_FUN sources
============================================================================
INFO
