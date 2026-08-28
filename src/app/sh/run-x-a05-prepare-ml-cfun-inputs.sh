#!/usr/bin/env bash
# Residual diagnostics and safe repair for run-x-a05 C_FUN ML input preparation.
#
# Workspace:
#   /home/user1-system12/project-workspace/ai_detector
#
# Delivery source names:
#   src/app/sh/run-x-a05-prepare-ml-cfun-inputs-v3.sh
#   src/app/py/prepare_ml_cfun_inputs-v3.py
#
# Canonical deployment names:
#   src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh
#   src/app/py/prepare_ml_cfun_inputs.py
#
# This wrapper is standalone. It reuses the validated run-x-a05-v2 logic by
# source adaptation, but it does not call any older shell wrapper or Python
# program.
#
# Frozen upstream inputs:
#   1. Failed v2 A05 output with exactly 946 residual mapping failures:
#        src/app/data_did_agc_analysis/run-x-a05
#   2. A01 frozen ML detector provenance:
#        src/app/data_did_agc_analysis/run-x-a01
#   3. detect_code_gpt NPR A05 historical source manifest/status:
#        ../detect_code_gpt/output/snapshot_npr/run-x-a05
#   4. detect_code_gpt NPR A13 C_FUN membership audit:
#        ../detect_code_gpt/output/snapshot_npr/run-x-a13/summary.json
#
# Frozen residual-failure provenance from run-x-a05-v2:
#   total residual failures:                 946
#   ml_source_indentation:                   862
#   tree_sitter_occurrence_map:               84
#
# v3 recovery policy:
#   - For the 862 indentation failures, remove the exact enclosing-class
#     indentation prefix only from structural source lines. Multiline-string
#     continuation rows keep their literal leading whitespace.
#   - For the 84 full-file Tree-sitter mapping failures, use the independently
#     verified A05 method body as the anchor, search a bounded local region for
#     the nearest same-name def/async def header, and accept recovery only when
#     the reconstructed standalone source is exactly one detector-visible
#     function block with the expected name and a non-empty AST sequence.
#
# Modes:
#   MODE=diagnose
#     Reprocess only the 946 v2 residual failures. Write recovered rows and
#     diagnostics to run-x-a05-v3-diagnose. Do not modify the failed v2 output.
#
#   MODE=repair
#     Requires diagnose PASS with 946/946 recovered. Merge the v2 successful
#     1,676,970 rows plus 946 v3 recovered rows in the frozen NPR A05 order.
#     Build a self-contained repaired artifact root using hardlinks by default.
#     Output goes to run-x-a05-v3-repaired; the failed v2 root is not modified.
#
#   MODE=verify
#     Read-only verification of run-x-a05-v3-repaired.
#
# This experiment does NOT:
#   - rerun the 1.68M full mapping in diagnose mode,
#   - retrain or tune the ML detector,
#   - load CodeT5+ or run SVM inference,
#   - change C_FUN membership, method-body SHA, or size weights,
#   - access SonarQube outcomes,
#   - estimate DiD models.
#
# Typical sequence:
#   MODE=diagnose OVERWRITE=1 bash src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh
#   # Review diagnosis first.
#   MODE=repair OVERWRITE=1 bash src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh
#   MODE=verify bash src/app/sh/run-x-a05-prepare-ml-cfun-inputs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

RUN_ID="run-x-a05-v3"
MODE="${MODE:-diagnose}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="${PY_SCRIPT:-src/app/py/prepare_ml_cfun_inputs.py}"
A01_ROOT="${A01_ROOT:-src/app/data_did_agc_analysis/run-x-a01}"
V2_ROOT="${V2_ROOT:-src/app/data_did_agc_analysis/run-x-a05}"
DIAGNOSE_ROOT="${DIAGNOSE_ROOT:-src/app/data_did_agc_analysis/run-x-a05-v3-diagnose}"
REPAIR_ROOT="${REPAIR_ROOT:-src/app/data_did_agc_analysis/run-x-a05-v3-repaired}"
TREE_SITTER_LIB="${TREE_SITTER_LIB:-src/code-analyzer-tree-sitter/build/my-languages.so}"
AST_HELPER_DIR="${AST_HELPER_DIR:-src/code-analyzer-tree-sitter}"
EXPECTED_CFUN_OCCURRENCES="${EXPECTED_CFUN_OCCURRENCES:-1677916}"
EXPECTED_UNIQUE_CFUN_BODY_SHA="${EXPECTED_UNIQUE_CFUN_BODY_SHA:-195193}"
EXPECTED_FILES_WITH_CFUN="${EXPECTED_FILES_WITH_CFUN:-196190}"
EXPECTED_A05_MANIFEST_SHA256="${EXPECTED_A05_MANIFEST_SHA256:-1acb3726f5c62e6154672f1aff592973c65a13e58dbfd37f8058560d1a474e6c}"
EXPECTED_V2_FAILURES="${EXPECTED_V2_FAILURES:-946}"
EXPECTED_V2_INDENTATION_FAILURES="${EXPECTED_V2_INDENTATION_FAILURES:-862}"
EXPECTED_V2_OCCURRENCE_FAILURES="${EXPECTED_V2_OCCURRENCE_FAILURES:-84}"
MAX_OPEN_GIT_PROCESSES="${MAX_OPEN_GIT_PROCESSES:-4}"
OVERWRITE="${OVERWRITE:-0}"
ALLOW_COPY_FALLBACK="${ALLOW_COPY_FALLBACK:-0}"
CLONE_PATH_PREFIX_FROM="${CLONE_PATH_PREFIX_FROM:-}"
CLONE_PATH_PREFIX_TO="${CLONE_PATH_PREFIX_TO:-}"

case "${MODE}" in
  diagnose)
    OUTPUT_ROOT="${OUTPUT_ROOT:-${DIAGNOSE_ROOT}}"
    PROGRESS_EVERY="${PROGRESS_EVERY:-100}"
    ;;
  repair)
    OUTPUT_ROOT="${OUTPUT_ROOT:-${REPAIR_ROOT}}"
    PROGRESS_EVERY="${PROGRESS_EVERY:-10000}"
    ;;
  verify)
    OUTPUT_ROOT="${OUTPUT_ROOT:-${REPAIR_ROOT}}"
    PROGRESS_EVERY="${PROGRESS_EVERY:-10000}"
    ;;
  *)
    echo "[ERROR] unsupported MODE=${MODE}; expected diagnose, repair, or verify" >&2
    exit 2
    ;;
esac

# Locate frozen detect_code_gpt inputs without calling any legacy wrapper.
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

if [[ -z "${NPR_A05_ROOT}" || -z "${NPR_A13_ROOT}" ]]; then
  echo "[ERROR] could not locate frozen detect_code_gpt A05/A13 inputs." >&2
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

require_file "${PY_SCRIPT}" "run-x-a05-v3 Python program"
require_file "${A01_ROOT}/detector_freeze_summary.json" "A01 freeze summary"
require_file "${A01_ROOT}/detector_freeze_metadata.json" "A01 freeze metadata"
require_file "${NPR_A05_ROOT}/snapshot_status.csv" "NPR A05 snapshot status"
require_file "${NPR_A05_ROOT}/python_code_unit_manifest.csv" "NPR A05 code-unit manifest"
require_file "${A13_SUMMARY_FILE}" "NPR A13 summary"
require_dir "${V2_ROOT}" "failed run-x-a05-v2 root"
require_file "${V2_ROOT}/summary.json" "failed v2 summary"
require_file "${V2_ROOT}/python_ml_cfun_mapping_failures.csv" "failed v2 residual mapping CSV"

if [[ "${MODE}" == "diagnose" ]]; then
  require_file "${TREE_SITTER_LIB}" "Tree-sitter language library"
  require_dir "${AST_HELPER_DIR}" "Tree-sitter AST helper directory"
elif [[ "${MODE}" == "repair" ]]; then
  require_file "${DIAGNOSE_ROOT}/summary.json" "v3 diagnose summary"
  require_file "${DIAGNOSE_ROOT}/python_ml_cfun_recovered_occurrences.csv" "v3 recovered occurrence rows"
  require_file "${DIAGNOSE_ROOT}/python_ml_cfun_recovery_failures.csv" "v3 remaining recovery failures"
  require_file "${V2_ROOT}/python_ml_cfun_occurrence_manifest.csv" "v2 successful occurrence manifest"
  require_file "${V2_ROOT}/python_ml_cfun_unique_source_manifest.csv" "v2 unique-source manifest"
fi

if [[ -n "${CLONE_PATH_PREFIX_FROM}" || -n "${CLONE_PATH_PREFIX_TO}" ]]; then
  if [[ -z "${CLONE_PATH_PREFIX_FROM}" || -z "${CLONE_PATH_PREFIX_TO}" ]]; then
    echo "[ERROR] both CLONE_PATH_PREFIX_FROM and CLONE_PATH_PREFIX_TO are required together." >&2
    exit 2
  fi
fi

RUN_TS="${RUN_TS:-$(date +'%Y%m%d-%H%M%S')}"
LOG_DIR="${LOG_DIR:-src/logs/run-x-a05}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run-x-a05-v3-${MODE}-${RUN_TS}.log}"
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
${RUN_ID}: residual diagnostics/repair for C_FUN ML source preparation
Mode:                            ${MODE}
Started:                         ${STARTED_AT}
Project root:                    ${REPO_ROOT}
Python:                          $(${PYTHON_BIN} -c 'import sys; print(sys.executable + " (" + sys.version.split()[0] + ")")')
Python script:                   ${PY_SCRIPT}
Python script SHA256:            $(sha256_of "${PY_SCRIPT}")
Failed v2 root:                 ${V2_ROOT}
Diagnose root:                   ${DIAGNOSE_ROOT}
Repair root:                     ${REPAIR_ROOT}
NPR A05 root:                    ${NPR_A05_ROOT}
NPR A13 summary:                 ${A13_SUMMARY_FILE}
Expected residual failures:      ${EXPECTED_V2_FAILURES}
  ml_source_indentation:         ${EXPECTED_V2_INDENTATION_FAILURES}
  tree_sitter_occurrence_map:    ${EXPECTED_V2_OCCURRENCE_FAILURES}
Expected full C_FUN occurrences: ${EXPECTED_CFUN_OCCURRENCES}
Expected unique C_FUN body SHA:  ${EXPECTED_UNIQUE_CFUN_BODY_SHA}
Expected files with C_FUN:       ${EXPECTED_FILES_WITH_CFUN}
Output root:                     ${OUTPUT_ROOT}
CodeT5+ embedding:               disabled; deferred to A06
SVM inference:                   disabled; deferred to A06
SonarQube/DiD outcome access:    disabled
Log file:                        ${LOG_FILE}
============================================================================
INFO

echo
echo "** Step 1: Run A05-v3 structural self-test"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" "${PY_SCRIPT}" --self-test --output-root "${OUTPUT_ROOT}" --npr-a05-root "${NPR_A05_ROOT}" --a13-summary-file "${A13_SUMMARY_FILE}"

echo
echo "** Step 2: Compile A05-v3 Python program"
echo "----------------------------------------------------------------------------"
"${PYTHON_BIN}" -m py_compile "${PY_SCRIPT}"

echo
echo "** Step 3: ${MODE} residual C_FUN ML source mappings"
echo "----------------------------------------------------------------------------"

ARGS=(
  --mode "${MODE}"
  --repo-root "${REPO_ROOT}"
  --a01-root "${A01_ROOT}"
  --v2-root "${V2_ROOT}"
  --diagnose-root "${DIAGNOSE_ROOT}"
  --npr-a05-root "${NPR_A05_ROOT}"
  --a13-summary-file "${A13_SUMMARY_FILE}"
  --output-root "${OUTPUT_ROOT}"
  --tree-sitter-lib "${TREE_SITTER_LIB}"
  --ast-helper-dir "${AST_HELPER_DIR}"
  --expected-occurrences "${EXPECTED_CFUN_OCCURRENCES}"
  --expected-unique-body-sha "${EXPECTED_UNIQUE_CFUN_BODY_SHA}"
  --expected-files-with-cfun "${EXPECTED_FILES_WITH_CFUN}"
  --expected-a05-manifest-sha256 "${EXPECTED_A05_MANIFEST_SHA256}"
  --expected-v2-failures "${EXPECTED_V2_FAILURES}"
  --expected-v2-indentation-failures "${EXPECTED_V2_INDENTATION_FAILURES}"
  --expected-v2-occurrence-failures "${EXPECTED_V2_OCCURRENCE_FAILURES}"
  --max-open-git-processes "${MAX_OPEN_GIT_PROCESSES}"
  --progress-every "${PROGRESS_EVERY}"
  --clone-path-prefix-from "${CLONE_PATH_PREFIX_FROM}"
  --clone-path-prefix-to "${CLONE_PATH_PREFIX_TO}"
)

if [[ "${OVERWRITE}" == "1" ]]; then
  ARGS+=(--overwrite)
fi
if [[ "${ALLOW_COPY_FALLBACK}" == "1" ]]; then
  ARGS+=(--allow-copy-fallback)
fi

"${PYTHON_BIN}" "${PY_SCRIPT}" "${ARGS[@]}"

END_EPOCH="$(date +%s)"
ELAPSED="$((END_EPOCH - START_EPOCH))"
printf -v ELAPSED_FMT '%02d:%02d:%02d' "$((ELAPSED / 3600))" "$(((ELAPSED % 3600) / 60))" "$((ELAPSED % 60))"

echo
cat <<INFO
============================================================================
${RUN_ID} execution summary
Mode:             ${MODE}
Started:          ${STARTED_AT}
Completed:        $(date)
Elapsed:          ${ELAPSED_FMT}
Exit code:        0
Output root:      ${OUTPUT_ROOT}
Log file:         ${LOG_FILE}
INFO
if [[ "${MODE}" == "diagnose" ]]; then
  echo "Next after PASS:  review 946/946 recovery diagnostics, then run MODE=repair"
elif [[ "${MODE}" == "repair" ]]; then
  echo "Next after PASS:  run MODE=verify, then review before promoting repaired root to canonical run-x-a05"
else
  echo "Next after PASS:  repaired A05-v3 is ready for promotion/A06 input review"
fi
echo "============================================================================"
