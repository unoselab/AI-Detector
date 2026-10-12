#!/usr/bin/env bash
# =============================================================================
# run-x-05-extract-cl7b-t00-functions.sh
# Recover one structurally valid Python target function per CodeLlama prompt
# from run-x-04's existing T=0.0 / Standard-EOS [2] raw generations.
#
# Adapted from a COPY of run-x-04-ablate-cl7b-eos.sh; fully independent.
# This wrapper NEVER calls run-x-02/run-x-04 or other existing shell scripts.
# Reuses only the original Python validator functions (read-only import).
#
# READ-ONLY INPUTS:
#   PILOT_DIR:    run-x-02 experiment_config.json, pilot_prepared.jsonl,
#                 pilot_selection.csv and pilot_generation.jsonl.
#   ABLATION_DIR: run-x-04 experiment_config.json, ablation_generation.jsonl,
#                 ablation_summary.json. Exactly 100 Standard-EOS records.
#   VALIDATOR_PY: original code-generation/find_validsyntax_mgc.py.
#   Original 4,500-pair data and split manifest: SHA-256 verification only.
#
# OUTPUTS (created in OUT_DIR; no existing data modified):
#   extracted_functions.jsonl     extracted continuations, code and errors
#   extracted_valid_pairs.csv     paired HWC/AGC for eligible procedures
#   extraction_qc.csv             outcome/reason for all 100 procedures
#   extraction_comparison.csv     matched legacy/B/C comparison per ID
#   extraction_summary.json       totals and split counts
#   extraction_findings.txt       readable overview
#   input_manifest.json           input SHA-256 provenance
#   runtime_environment.json      exact Python executable and version
#
# LOGS (written only inside LOG_DIR): run-x-05-<RUN_ID>.log
#
# RUN FROM REPO ROOT:
#   DRY_RUN=1 bash src/sh/run-x-05-extract-cl7b-t00-functions.sh
#   bash src/sh/run-x-05-extract-cl7b-t00-functions.sh
#
# Python 3.11 is REQUIRED for server results. No GPU is used.
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "${SRC_DIR}/.." && pwd)}"
PYTHON="${PYTHON:-python}"
PILOT_DIR="${PILOT_DIR:-${SRC_DIR}/output/run-x-02/20261012-140235-6379}"
ABLATION_DIR="${ABLATION_DIR:-${SRC_DIR}/output/run-x-04/20261012-143925-17683}"
VALIDATOR_PY="${VALIDATOR_PY:-${SRC_DIR}/code-generation/find_validsyntax_mgc.py}"
DRY_RUN="${DRY_RUN:-0}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${SRC_DIR}/output/run-x-05/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${SRC_DIR}/logs/run-x-05}"
LOG_FILE="${LOG_DIR}/run-x-05-${RUN_ID}.log"
SCRIPT_PY="${SRC_DIR}/py/extract_cl7b_t00_functions.py"

for required in \
  "${SCRIPT_PY}" "${VALIDATOR_PY}" \
  "${PILOT_DIR}/experiment_config.json" \
  "${PILOT_DIR}/pilot_prepared.jsonl" \
  "${PILOT_DIR}/pilot_selection.csv" \
  "${PILOT_DIR}/pilot_generation.jsonl" \
  "${ABLATION_DIR}/experiment_config.json" \
  "${ABLATION_DIR}/ablation_generation.jsonl" \
  "${ABLATION_DIR}/ablation_summary.json"; do
  if [[ ! -f "${required}" ]]; then
    echo "[ERROR] Missing read-only input: ${required}" >&2
    exit 2
  fi
done
if [[ -e "${OUT_DIR}" || -e "${LOG_FILE}" ]]; then
  echo "[ERROR] Refusing to overwrite an existing run: ${RUN_ID}" >&2
  exit 2
fi
mkdir -p "${OUT_DIR}" "${LOG_DIR}"

# These two overrides are ONLY for off-server fixture testing.
# Production/reproducibility runs must leave both unset.
ARGS=()
if [[ "${DRY_RUN}" == "1" ]]; then ARGS+=(--dry-run); fi
if [[ "${ALLOW_OTHER_PYTHON:-0}" == "1" ]]; then ARGS+=(--allow-other-python); fi
if [[ "${ALLOW_UNMOUNTED_SOURCES:-0}" == "1" ]]; then ARGS+=(--allow-unmounted-sources); fi

{
  echo "================================================================="
  echo "run-x-05 | Extract target Python procedures from Standard-EOS T=0.0"
  echo "repo_root=${REPO_ROOT}"
  echo "run_id=${RUN_ID}"
  echo "pilot_dir=${PILOT_DIR}"
  echo "ablation_dir=${ABLATION_DIR}"
  echo "validator=${VALIDATOR_PY}"
  echo "python=${PYTHON}"
  echo "gpu_inference=NO source_inputs=READ_ONLY"
  echo "out_dir=${OUT_DIR} dry_run=${DRY_RUN}"
  echo "================================================================="
  "${PYTHON}" -u "${SCRIPT_PY}" \
    --pilot-dir "${PILOT_DIR}" \
    --ablation-dir "${ABLATION_DIR}" \
    --validator-script "${VALIDATOR_PY}" \
    --output-dir "${OUT_DIR}" \
    "${ARGS[@]}"
} 2>&1 | tee "${LOG_FILE}"
printf '\nSaved outputs: %s\nSaved log: %s\n' "${OUT_DIR}" "${LOG_FILE}"
