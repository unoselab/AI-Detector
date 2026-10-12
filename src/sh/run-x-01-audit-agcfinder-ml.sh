#!/usr/bin/env bash
# =============================================================================
# run-x-01-audit-agcfinder-ml.sh - AGCFinderML T=0.2 baseline audit before T=0.0 experiments
#
# Independent wrapper adapted from src/run5b-test-classifiers-allmodels.sh.
# It does NOT call any existing shell script, unpickle models, retrain, or
# generate code. Its only writes are inside NEW output/log directories.
#
# Inputs:
#   REPO_ROOT: existing ai_detector project root (auto-resolved by default)
#   The original run4c/run4d CSV manifests and prediction files, split CSVs,
#   CodeLlama trained classifier pickle, and original CodeLlama data.
#
# Outputs:
#   src/output/run-x-01/<RUN_ID>/{artifact_inventory.csv,baseline_cells.csv,
#     baseline_summary.csv,pair_split_manifest.csv,run_summary.json,findings.txt}
#   src/logs/run-x-01/run-x-01-<RUN_ID>.log
#
# Usage from the ai_detector project root:
#   bash src/sh/run-x-01-audit-agcfinder-ml.sh
#   HASH_MODELS=none bash src/sh/run-x-01-audit-agcfinder-ml.sh
#   STRICT_MISSING=1 bash src/sh/run-x-01-audit-agcfinder-ml.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "${SRC_DIR}/.." && pwd)}"
PYTHON="${PYTHON:-python}"

# Input settings: table reproduction uses all 25 existing run4c predictions.
TARGET_SOURCE="${TARGET_SOURCE:-CL-7B}"
EXPECTED_PAIRS="${EXPECTED_PAIRS:-4500}"
EXPECTED_TEST_PAIRS="${EXPECTED_TEST_PAIRS:-450}"
COMPARISON_TOLERANCE="${COMPARISON_TOLERANCE:-0.00000001}"
PAPER_TOLERANCE="${PAPER_TOLERANCE:-0.0001}"
HASH_MODELS="${HASH_MODELS:-selected}"  # selected | all | none
STRICT_MISSING="${STRICT_MISSING:-0}"

# Outputs are created separately; no existing model or dataset is overwritten.
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${REPO_ROOT}/src/output/run-x-01/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/src/logs/run-x-01}"
LOG_FILE="${LOG_DIR}/run-x-01-${RUN_ID}.log"

if [[ ! -f "${SRC_DIR}/py/audit_agcfinder_ml.py" ]]; then
  echo "[ERROR] Missing implementation: ${SRC_DIR}/py/audit_agcfinder_ml.py" >&2
  exit 2
fi
if [[ -e "${OUT_DIR}" ]]; then
  echo "[ERROR] Output directory already exists (refusing overwrite): ${OUT_DIR}" >&2
  exit 2
fi
if [[ -e "${LOG_FILE}" ]]; then
  echo "[ERROR] Log file already exists (refusing overwrite): ${LOG_FILE}" >&2
  exit 2
fi
mkdir -p "${OUT_DIR}" "${LOG_DIR}"

EXTRA_ARGS=()
if [[ "${STRICT_MISSING}" == "1" ]]; then
  EXTRA_ARGS+=(--strict-missing)
fi

{
  echo "================================================================="
  echo "run-x-01 | AGCFinderML baseline audit (read-only inputs)"
  echo "repo_root=${REPO_ROOT}"
  echo "output_dir=${OUT_DIR}"
  echo "target_source=${TARGET_SOURCE}"
  echo "hash_models=${HASH_MODELS} strict_missing=${STRICT_MISSING}"
  echo "log_file=${LOG_FILE}"
  echo "================================================================="
  "${PYTHON}" "${SRC_DIR}/py/audit_agcfinder_ml.py" \
    --repo-root "${REPO_ROOT}" \
    --output-dir "${OUT_DIR}" \
    --target-source "${TARGET_SOURCE}" \
    --expected-pairs "${EXPECTED_PAIRS}" \
    --expected-test-pairs "${EXPECTED_TEST_PAIRS}" \
    --comparison-tolerance "${COMPARISON_TOLERANCE}" \
    --paper-tolerance "${PAPER_TOLERANCE}" \
    --hash-models "${HASH_MODELS}" \
    "${EXTRA_ARGS[@]}"
} 2>&1 | tee "${LOG_FILE}"

printf '\nSaved results: %s\n' "${OUT_DIR}"
printf 'Saved log: %s\n' "${LOG_FILE}"
