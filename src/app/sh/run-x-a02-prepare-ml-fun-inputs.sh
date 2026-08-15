#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run-x-a02-prepare-ml-fun-inputs-v2.sh
# -----------------------------------------------------------------------------
# Purpose
#   Prepare and audit full standalone Python function sources for the exact A05
#   NPR FUN occurrence universe. This is the identity/compatibility bridge
#   between the perturbation-based NPR analysis and the frozen CodeLlama-7B
#   SVM+AST detector from run-x-a01.
#
# Methodological contract
#   The current primary ML quality analysis must use the same historical units
#   as the current FUN NPR quality analysis:
#     same repository
#       -> same historical commit
#       -> same Python file
#       -> same A05 primary function_body occurrence
#
#   NPR input:
#     exact A05 function implementation body
#
#   ML input:
#     full standalone function source -> AST -> CodeT5+ -> frozen SVM
#
#   A02 does NOT load CodeT5+, does NOT run SVM inference, and does NOT read any
#   SonarQube or downstream DiD quality outcome.
#
# Frozen current scope
#   aggregation_role = primary
#   code_unit_type   = function_body
#   expected occurrence rows = 921,762
#   expected unique body SHA memberships = 105,635
#
#   Class methods (C_FUN / method_body) are deliberately not mixed into this
#   first ML-vs-NPR quality comparison. The Python implementation supports a
#   later prespecified extension, but this wrapper hard-pins FUN only.
#
# Required inputs
#   1. run-x-a01 freeze artifacts under A01_ROOT:
#        detector_freeze_summary.json
#        detector_freeze_metadata.json
#   2. run-x-a05 NPR preparation artifacts under NPR_A05_ROOT:
#        snapshot_status.csv
#        python_code_unit_manifest.csv
#   3. Historical Git clones referenced by A05 snapshot_status.csv.
#   4. The existing ai_detector tree-sitter parser files:
#        src/code-analyzer-tree-sitter/build/my-languages.so
#        src/code-analyzer-tree-sitter/
#
# Outputs under OUTPUT_ROOT
#   python_ml_fun_occurrence_manifest.csv
#   python_ml_fun_unique_source_manifest.csv
#   python_ml_fun_mapping_failures.csv
#   checks.csv
#   summary.json
#   metadata.json
#   ml_function_sources/<sha-prefix>/<sha256>.py
#   snapshot_chunks/<snapshot_id>/...
#
# Resume policy
#   A02 is CPU-only but can process many historical files. Full runs are
#   snapshot-resumable. Existing chunks are reused only when their selected
#   A05 occurrence fingerprint and frozen A01/A05 provenance match exactly.
#
# Modes
#   MODE=smoke  : map the first SMOKE_MAX_OCCURRENCES selected FUN occurrences.
#                 Uses a separate output root and does not enforce full counts.
#   MODE=full   : process all 921,762 FUN occurrences and enforce frozen counts.
#   MODE=verify : read-only verification of an existing full output.
#
# Cross-server clone path remapping
#   A05 snapshot_status.csv preserves the clone paths used during NPR input
#   preparation. If the same repository tree is mirrored under another home
#   prefix on the current server, explicitly provide both variables:
#
#     CLONE_PATH_PREFIX_FROM=/home/user1-system11
#     CLONE_PATH_PREFIX_TO=/home/user1-system12
#
#   No path prefix is silently rewritten unless both variables are supplied.
#
# Typical usage
#   Smoke first:
#     NPR_A05_ROOT=/path/to/detect_code_gpt/output/snapshot_npr/run-x-a05 MODE=smoke OVERWRITE=1 bash src/app/sh/run-x-a02-prepare-ml-fun-inputs.sh
#
#   Full after smoke PASS:
#     NPR_A05_ROOT=/path/to/detect_code_gpt/output/snapshot_npr/run-x-a05 \
#       MODE=full RESUME=1 \
#       bash src/app/sh/run-x-a02-prepare-ml-fun-inputs.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a02-v2"
MODE="${MODE:-smoke}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="src/app/py/prepare_ml_fun_inputs.py"
A01_ROOT="${A01_ROOT:-src/app/data_did_agc_analysis/run-x-a01}"
TREE_SITTER_LIB="${TREE_SITTER_LIB:-src/code-analyzer-tree-sitter/build/my-languages.so}"
AST_HELPER_DIR="${AST_HELPER_DIR:-src/code-analyzer-tree-sitter}"

EXPECTED_FUN_OCCURRENCES="921762"
EXPECTED_UNIQUE_FUN_BODY_SHA="105635"
SMOKE_MAX_OCCURRENCES="${SMOKE_MAX_OCCURRENCES:-500}"
RESUME="${RESUME:-1}"
OVERWRITE="${OVERWRITE:-0}"
MAX_OPEN_GIT_PROCESSES="${MAX_OPEN_GIT_PROCESSES:-4}"
CLONE_PATH_PREFIX_FROM="${CLONE_PATH_PREFIX_FROM:-}"
CLONE_PATH_PREFIX_TO="${CLONE_PATH_PREFIX_TO:-}"

case "${MODE}" in
  smoke|full|verify) ;;
  *)
    echo "[ERROR] unsupported MODE=${MODE}; expected smoke, full, or verify" >&2
    exit 2
    ;;
esac

# Resolve the NPR A05 input root. An explicit NPR_A05_ROOT always wins.
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
  echo "[ERROR] could not locate run-x-a05 NPR preparation artifacts." >&2
  echo "        Set NPR_A05_ROOT to the directory containing:" >&2
  echo "          snapshot_status.csv" >&2
  echo "          python_code_unit_manifest.csv" >&2
  exit 2
fi

if [[ "${MODE}" == "smoke" ]]; then
  OUTPUT_ROOT="${OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a02-smoke}"
  MAX_OCCURRENCES="${SMOKE_MAX_OCCURRENCES}"
else
  OUTPUT_ROOT="${OUTPUT_ROOT:-src/app/data_did_agc_analysis/run-x-a02}"
  MAX_OCCURRENCES="0"
fi

RUN_TS="${RUN_TS:-$(date +'%Y%m%d-%H%M%S')}"
LOG_DIR="${LOG_DIR:-src/logs/run-x-a02}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a02-v2-${MODE}-prepare-ml-fun-inputs-${RUN_TS}.log}"
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

require_file "${PY_SCRIPT}" "run-x-a02 Python program"
require_file "${A01_ROOT}/detector_freeze_summary.json" "A01 freeze summary"
require_file "${A01_ROOT}/detector_freeze_metadata.json" "A01 freeze metadata"
require_file "${NPR_A05_ROOT}/snapshot_status.csv" "A05 snapshot status"
require_file "${NPR_A05_ROOT}/python_code_unit_manifest.csv" "A05 code-unit manifest"
require_file "${TREE_SITTER_LIB}" "tree-sitter language library"
require_dir "${AST_HELPER_DIR}" "tree-sitter AST helper directory"

if [[ "${MODE}" == "verify" ]]; then
  if [[ ! -d "${OUTPUT_ROOT}" ]]; then
    echo "[ERROR] MODE=verify requires existing output root: ${OUTPUT_ROOT}" >&2
    exit 2
  fi
else
  if [[ -e "${OUTPUT_ROOT}" && "${OVERWRITE}" == "1" ]]; then
    rm -rf "${OUTPUT_ROOT}"
  elif [[ -e "${OUTPUT_ROOT}" && "${RESUME}" != "1" ]]; then
    echo "[ERROR] output root already exists and RESUME!=1: ${OUTPUT_ROOT}" >&2
    echo "        Use RESUME=1 to reuse exact matching snapshot chunks, or OVERWRITE=1 for a clean rerun." >&2
    exit 2
  fi
fi

START_EPOCH="$(date +%s)"
STARTED_AT="$(date)"

cat <<INFO
============================================================================
${RUN_ID}: prepare exact ML standalone-function inputs for NPR FUN occurrences
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Python script:                   ${PY_SCRIPT}
Python script SHA256:            $(sha256_of "${PY_SCRIPT}")
A01 freeze root:                 ${A01_ROOT}
A01 summary SHA256:              $(sha256_of "${A01_ROOT}/detector_freeze_summary.json")
A01 metadata SHA256:             $(sha256_of "${A01_ROOT}/detector_freeze_metadata.json")
NPR A05 root:                    ${NPR_A05_ROOT}
A05 snapshot status SHA256:      $(sha256_of "${NPR_A05_ROOT}/snapshot_status.csv")
A05 code-unit manifest bytes:    $(file_bytes "${NPR_A05_ROOT}/python_code_unit_manifest.csv")
A05 code-unit manifest SHA256:   computed and frozen by the A02 Python program
Selected aggregation role:      primary
Selected code-unit type:        function_body (FUN)
Expected full FUN occurrences:   ${EXPECTED_FUN_OCCURRENCES}
Expected unique FUN body SHA:    ${EXPECTED_UNIQUE_FUN_BODY_SHA}
Smoke max occurrences:          ${SMOKE_MAX_OCCURRENCES}
Current max occurrences:        ${MAX_OCCURRENCES}
Tree-sitter library:             ${TREE_SITTER_LIB}
Tree-sitter library SHA256:      $(sha256_of "${TREE_SITTER_LIB}")
AST helper directory:            ${AST_HELPER_DIR}
Clone path prefix from:          ${CLONE_PATH_PREFIX_FROM:-<none>}
Clone path prefix to:            ${CLONE_PATH_PREFIX_TO:-<none>}
Resume snapshot chunks:          ${RESUME}
Overwrite output:                ${OVERWRITE}
Output root:                     ${OUTPUT_ROOT}
Model loading:                   disabled
CodeT5+ embedding:               disabled
SVM inference:                   disabled
SonarQube/DiD outcome access:    disabled
Log file:                        ${LOG_FILE}
============================================================================
INFO

echo
echo "** Step 1: Run A02 structural self-test"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" "${PY_SCRIPT}" --self-test

echo
echo "** Step 2: Compile A02 Python program"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

COMMON_ARGS=(
  --repo-root "${REPO_ROOT}"
  --a01-root "${A01_ROOT}"
  --a05-root "${NPR_A05_ROOT}"
  --output-root "${OUTPUT_ROOT}"
  --tree-sitter-lib "${TREE_SITTER_LIB}"
  --ast-helper-dir "${AST_HELPER_DIR}"
  --unit-type function_body
  --aggregation-role primary
  --expected-occurrences "${EXPECTED_FUN_OCCURRENCES}"
  --expected-unique-body-sha "${EXPECTED_UNIQUE_FUN_BODY_SHA}"
  --max-occurrences "${MAX_OCCURRENCES}"
  --max-open-git-processes "${MAX_OPEN_GIT_PROCESSES}"
)

if [[ -n "${CLONE_PATH_PREFIX_FROM}" || -n "${CLONE_PATH_PREFIX_TO}" ]]; then
  if [[ -z "${CLONE_PATH_PREFIX_FROM}" || -z "${CLONE_PATH_PREFIX_TO}" ]]; then
    echo "[ERROR] both CLONE_PATH_PREFIX_FROM and CLONE_PATH_PREFIX_TO are required together." >&2
    exit 2
  fi
  COMMON_ARGS+=(
    --clone-path-prefix-from "${CLONE_PATH_PREFIX_FROM}"
    --clone-path-prefix-to "${CLONE_PATH_PREFIX_TO}"
  )
fi

if [[ "${MODE}" == "verify" ]]; then
  echo
  echo "** Step 3: Read-only verification of existing A02 full outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
else
  echo
  echo "** Step 3: Build exact NPR-FUN to ML standalone-function mapping"
  echo "----------------------------------------------------------------------------"
  PREP_ARGS=("${COMMON_ARGS[@]}")
  if [[ "${RESUME}" == "1" ]]; then
    PREP_ARGS+=(--resume)
  fi
  if [[ "${OVERWRITE}" == "1" ]]; then
    PREP_ARGS+=(--overwrite)
  fi
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${PREP_ARGS[@]}"

  echo
  echo "** Step 4: Verify A02 outputs"
  echo "----------------------------------------------------------------------------"
  "${PYTHON_BIN}" "${PY_SCRIPT}" "${COMMON_ARGS[@]}" --verify-output
fi

END_EPOCH="$(date +%s)"
COMPLETED_AT="$(date)"
ELAPSED=$((END_EPOCH - START_EPOCH))
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
