#!/usr/bin/env bash
# Diagnose and repair the residual Tree-sitter full-function mappings from A02 v2.
#
# Workspace:
#   ai_detector repository root
#
# Canonical deployment paths:
#   src/app/sh/run-x-a02-prepare-ml-fun-inputs.sh
#   src/app/py/prepare_ml_fun_inputs.py
#
# Upstream frozen inputs:
#   1. A01 detector freeze output:
#        src/app/data_did_agc_analysis/run-x-a01
#   2. NPR A05 historical Python preparation output:
#        <detect_code_gpt>/output/snapshot_npr/run-x-a05
#   3. A02 v2 failed full output:
#        src/app/data_did_agc_analysis/run-x-a02
#
# Purpose:
#   A02 v2 mapped 913,558 of 921,762 exact A05 primary FUN occurrences and
#   failed 8,204 rows only at the Tree-sitter occurrence/boundary stage. This
#   v3 wrapper targets those failed code_unit_id values only. It does not rerun
#   the already-successful 913,558 mappings.
#
# Safe repair policy:
#   - Reverify the historical Git file SHA-256 against A05.
#   - Reverify the exact A05 function-body SHA-256 and literal-space-token count.
#   - Require exactly one same-name direct module-level Tree-sitter function
#     containing the verified A05 body-start anchor.
#   - When Tree-sitter's recovered function end extends beyond A05, use only the
#     Tree-sitter header/decorator START and the authoritative A05 function END.
#   - Require the reconstructed standalone source to yield exactly one expected
#     detector function block with full-source coverage and a non-empty AST.
#
# Modes:
#   MODE=diagnose  Read only the 8,204 v2 failures, create detailed candidate
#                  diagnostics and safe repair rows. The v2 base output is not
#                  modified. This is the required first run.
#   MODE=repair    Require a completed diagnose run with repair_ready=true,
#                  back up the failed v2 core files, merge v2 successes with
#                  recovered rows, rebuild the unique-source manifest, and
#                  verify the canonical A02 output.
#   MODE=verify    Read-only verification of the repaired canonical A02 output.
#
# Outputs for MODE=diagnose:
#   src/app/data_did_agc_analysis/run-x-a02-v3-diagnose/
#     repair_occurrences.csv
#     repair_failures.csv
#     tree_sitter_mapping_diagnostics.csv
#     checks.csv
#     summary.json
#     metadata.json
#     ml_function_sources/<sha-prefix>/<sha256>.py
#
# Outputs for MODE=repair:
#   Canonical repaired output remains:
#     src/app/data_did_agc_analysis/run-x-a02/
#   The failed v2 core manifests are frozen under:
#     src/app/data_did_agc_analysis/run-x-a02/provenance/run-x-a02-v2-failed/
#
# This experiment does NOT:
#   - load CodeT5+,
#   - run the frozen SVM classifier,
#   - alter the A01 detector boundary,
#   - alter the A05 NPR body identity,
#   - access SonarQube or DiD outcomes.
#
# Typical usage:
#   First diagnose the residual v2 failures:
#     MODE=diagnose OVERWRITE=1 \
#       bash src/app/sh/run-x-a02-prepare-ml-fun-inputs.sh
#
#   If the diagnosis reports repair_ready=True:
#     MODE=repair \
#       bash src/app/sh/run-x-a02-prepare-ml-fun-inputs.sh
#
#   Later read-only verification:
#     MODE=verify \
#       bash src/app/sh/run-x-a02-prepare-ml-fun-inputs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a02-v3"
MODE="${MODE:-diagnose}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/prepare_ml_fun_inputs.py}"
A01_ROOT="${A01_ROOT:-src/app/data_did_agc_analysis/run-x-a01}"
BASE_OUTPUT_ROOT="${BASE_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a02}"
DIAGNOSTIC_OUTPUT_ROOT="${DIAGNOSTIC_OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a02-v3-diagnose}"
TREE_SITTER_LIB="${TREE_SITTER_LIB:-src/code-analyzer-tree-sitter/build/my-languages.so}"
AST_HELPER_DIR="${AST_HELPER_DIR:-src/code-analyzer-tree-sitter}"

EXPECTED_FUN_OCCURRENCES="${EXPECTED_FUN_OCCURRENCES:-921762}"
EXPECTED_UNIQUE_FUN_BODY_SHA="${EXPECTED_UNIQUE_FUN_BODY_SHA:-105635}"
EXPECTED_V2_FAILURES="${EXPECTED_V2_FAILURES:-8204}"
MAX_OPEN_GIT_PROCESSES="${MAX_OPEN_GIT_PROCESSES:-4}"
PROGRESS_EVERY="${PROGRESS_EVERY:-500}"
OVERWRITE="${OVERWRITE:-0}"
CLONE_PATH_PREFIX_FROM="${CLONE_PATH_PREFIX_FROM:-}"
CLONE_PATH_PREFIX_TO="${CLONE_PATH_PREFIX_TO:-}"

case "${MODE}" in
  diagnose|repair|verify) ;;
  *)
    echo "[ERROR] unsupported MODE=${MODE}; expected diagnose, repair, or verify" >&2
    exit 2
    ;;
esac

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

if [[ -z "${NPR_A05_ROOT}" ]]; then
  echo "[ERROR] could not locate NPR A05 preparation artifacts." >&2
  echo "        Set NPR_A05_ROOT to the run-x-a05 directory containing:" >&2
  echo "          snapshot_status.csv" >&2
  echo "          python_code_unit_manifest.csv" >&2
  exit 2
fi

RUN_TS="${RUN_TS:-$(date +'%Y%m%d-%H%M%S')}"
LOG_DIR="${LOG_DIR:-src/logs/run-x-a02}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a02-v3-${MODE}-tree-sitter-repair-${RUN_TS}.log}"
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

file_bytes() {
  stat -c '%s' "$1"
}

require_file "${PY_SCRIPT}" "run-x-a02-v3 Python program"
require_file "${A01_ROOT}/detector_freeze_summary.json" "A01 freeze summary"
require_file "${A01_ROOT}/detector_freeze_metadata.json" "A01 freeze metadata"
require_file "${NPR_A05_ROOT}/snapshot_status.csv" "A05 snapshot status"
require_file "${NPR_A05_ROOT}/python_code_unit_manifest.csv" "A05 code-unit manifest"
require_file "${BASE_OUTPUT_ROOT}/summary.json" "A02 v2 summary/canonical summary"
require_file "${BASE_OUTPUT_ROOT}/python_ml_fun_occurrence_manifest.csv" "A02 occurrence manifest"
require_file "${BASE_OUTPUT_ROOT}/python_ml_fun_mapping_failures.csv" "A02 mapping failure manifest"
require_file "${TREE_SITTER_LIB}" "tree-sitter language library"
require_dir "${AST_HELPER_DIR}" "tree-sitter AST helper directory"

if [[ -n "${CLONE_PATH_PREFIX_FROM}" || -n "${CLONE_PATH_PREFIX_TO}" ]]; then
  if [[ -z "${CLONE_PATH_PREFIX_FROM}" || -z "${CLONE_PATH_PREFIX_TO}" ]]; then
    echo "[ERROR] both CLONE_PATH_PREFIX_FROM and CLONE_PATH_PREFIX_TO are required together." >&2
    exit 2
  fi
fi

if [[ "${MODE}" == "diagnose" && -e "${DIAGNOSTIC_OUTPUT_ROOT}" && "${OVERWRITE}" != "1" ]]; then
  echo "[ERROR] diagnostic output already exists: ${DIAGNOSTIC_OUTPUT_ROOT}" >&2
  echo "        Use OVERWRITE=1 for a clean targeted diagnosis rerun." >&2
  exit 2
fi

START_EPOCH="$(date +%s)"
STARTED_AT="$(date)"

cat <<INFO
============================================================================
${RUN_ID}: diagnose/repair residual Tree-sitter FUN mappings
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Python script:                   ${PY_SCRIPT}
Python script SHA256:            $(sha256_of "${PY_SCRIPT}")
A01 freeze root:                 ${A01_ROOT}
A01 metadata SHA256:             $(sha256_of "${A01_ROOT}/detector_freeze_metadata.json")
NPR A05 root:                    ${NPR_A05_ROOT}
A05 snapshot status SHA256:      $(sha256_of "${NPR_A05_ROOT}/snapshot_status.csv")
A05 code-unit manifest bytes:    $(file_bytes "${NPR_A05_ROOT}/python_code_unit_manifest.csv")
A02 v2/canonical root:           ${BASE_OUTPUT_ROOT}
A02 base summary SHA256:         $(sha256_of "${BASE_OUTPUT_ROOT}/summary.json")
A02 base failure SHA256:         $(sha256_of "${BASE_OUTPUT_ROOT}/python_ml_fun_mapping_failures.csv")
Diagnostic output root:          ${DIAGNOSTIC_OUTPUT_ROOT}
Expected full FUN occurrences:   ${EXPECTED_FUN_OCCURRENCES}
Expected unique FUN body SHA:    ${EXPECTED_UNIQUE_FUN_BODY_SHA}
Expected v2 mapping failures:    ${EXPECTED_V2_FAILURES}
Tree-sitter library:             ${TREE_SITTER_LIB}
Tree-sitter library SHA256:      $(sha256_of "${TREE_SITTER_LIB}")
AST helper directory:            ${AST_HELPER_DIR}
Clone path prefix from:          ${CLONE_PATH_PREFIX_FROM:-<none>}
Clone path prefix to:            ${CLONE_PATH_PREFIX_TO:-<none>}
Max open Git batch processes:    ${MAX_OPEN_GIT_PROCESSES}
Progress every:                  ${PROGRESS_EVERY}
Overwrite diagnosis:             ${OVERWRITE}
Model loading:                   disabled
CodeT5+ embedding:               disabled
SVM inference:                   disabled
SonarQube/DiD outcome access:    disabled
Log file:                        ${LOG_FILE}
============================================================================
INFO

echo
echo "** Step 1: Run A02 v3 structural self-test"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" "${PY_SCRIPT}" --self-test

echo
echo "** Step 2: Compile A02 v3 Python program"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

COMMON_ARGS=(
  --repo-root "${REPO_ROOT}"
  --a01-root "${A01_ROOT}"
  --a05-root "${NPR_A05_ROOT}"
  --base-output-root "${BASE_OUTPUT_ROOT}"
  --diagnostic-output-root "${DIAGNOSTIC_OUTPUT_ROOT}"
  --tree-sitter-lib "${TREE_SITTER_LIB}"
  --ast-helper-dir "${AST_HELPER_DIR}"
  --expected-occurrences "${EXPECTED_FUN_OCCURRENCES}"
  --expected-unique-body-sha "${EXPECTED_UNIQUE_FUN_BODY_SHA}"
  --expected-v2-failures "${EXPECTED_V2_FAILURES}"
  --max-open-git-processes "${MAX_OPEN_GIT_PROCESSES}"
  --progress-every "${PROGRESS_EVERY}"
)

if [[ -n "${CLONE_PATH_PREFIX_FROM}" ]]; then
  COMMON_ARGS+=(
    --clone-path-prefix-from "${CLONE_PATH_PREFIX_FROM}"
    --clone-path-prefix-to "${CLONE_PATH_PREFIX_TO}"
  )
fi

case "${MODE}" in
  diagnose)
    echo
    echo "** Step 3: Diagnose only the residual A02 v2 Tree-sitter failures"
    echo "----------------------------------------------------------------------------"
    DIAG_ARGS=("${COMMON_ARGS[@]}" --mode diagnose)
    if [[ "${OVERWRITE}" == "1" ]]; then
      DIAG_ARGS+=(--overwrite)
    fi
    "${PYTHON_BIN}" "${PY_SCRIPT}" "${DIAG_ARGS[@]}"

    echo
    echo "** Step 4: Report diagnosis repair readiness"
    echo "----------------------------------------------------------------------------"
    "${PYTHON_BIN}" -c 'import json,sys; p=json.load(open(sys.argv[1])); print("Diagnosis status:             " + str(p.get("status"))); print("Target v2 failures:           " + str(p.get("target_failed_occurrences"))); print("Safely recovered:             " + str(p.get("safely_recovered_occurrences"))); print("Residual failures:            " + str(p.get("residual_repair_failures"))); print("Repair ready:                 " + str(p.get("repair_ready"))); print("Unique primary anchors:       " + str(p.get("target_unique_primary_anchor_occurrences"))); print("End-overrun targets:          " + str(p.get("target_unique_primary_anchor_end_overrun_occurrences"))); print("Full-file TS error targets:   " + str(p.get("target_full_file_tree_error_occurrences"))); print("A05 end-override recoveries:  " + str(p.get("recovered_with_a05_end_override")))' "${DIAGNOSTIC_OUTPUT_ROOT}/summary.json"
    ;;
  repair)
    echo
    echo "** Step 3: Merge only safely recovered v3 rows into the canonical A02 output"
    echo "----------------------------------------------------------------------------"
    "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --mode repair

    echo
    echo "** Step 4: Strictly verify repaired canonical A02 outputs"
    echo "----------------------------------------------------------------------------"
    "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --mode verify
    ;;
  verify)
    echo
    echo "** Step 3: Read-only verification of repaired canonical A02 outputs"
    echo "----------------------------------------------------------------------------"
    "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --mode verify
    ;;
esac

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
Base output root: ${BASE_OUTPUT_ROOT}
Diagnosis root:   ${DIAGNOSTIC_OUTPUT_ROOT}
Log file:         ${LOG_FILE}
============================================================================
INFO
