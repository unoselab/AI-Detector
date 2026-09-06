#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run4c-compute-agc-transfer-same-test.sh
# -----------------------------------------------------------------------------
# Compute the full 5x5 cross-generator transfer matrix using the EXACT held-out
# test splits used by Table (1).
#
# This wrapper was derived from the run4b transfer wrapper, but it is standalone:
# it does NOT call run3, run4, or run4b. The scoring logic needed for this new
# exact-test-support design is implemented in:
#
#   src/app/compute_agc_transfer_same_test.py
#
# WHY RUN4C EXISTS
#   run4b used a separately constructed 50x6 mixed-authorship subset. Run4c
#   removes that support difference from the cross-generator comparison by
#   applying every source-trained detector to the same five 900-row held-out
#   test CSVs used in Table (1). Thus, off-diagonal differences reflect target
#   generator shift rather than a change from isolated to mixed-file support.
#
# INPUTS
#   Table (1) held-out test sets:
#     src/ml_embeddings/data_codesearchnet/
#       splits/<source-experiment>/<source-dataset>/test_.csv
#
#   Table (1)-selected frozen classifier pickles:
#     CL-7B    : SVM + AST
#     SC2-7B   : SVM + AST
#     SC2-15B  : SVM + AST
#     GO-120B  : MLP + AST
#     GM4-31B  : LR  + AST
#
#   Each target test CSV must contain exactly:
#     900 rows = 450 HWC(label=1) + 450 AGC(label=0)
#
# OUTPUTS
#   Default result root:
#     src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c/
#
#   Key files:
#     matrix_auroc.csv
#     cell_metrics.csv
#     diagonal_qc.csv
#     source_config_manifest.csv
#     target_test_manifest.csv
#     table2_rows.tex
#     environment.txt
#     predictions/clf-<source>/target-<target>.csv
#
#   Logs:
#     src/logs/run4c-same-test/<timestamp>/master.log
#
# HARD QC
#   1. The runtime scikit-learn version is recorded and compared with the
#      pickle serialization version. A mismatch is a warning by default, not a
#      blocker, because the definitive reproducibility check is whether the
#      exact Table (1) diagonal AUROCs are reproduced on the same test support.
#      Set STRICT_SKLEARN_VERSION=1 only when an exact package-version match is
#      intentionally required.
#   2. All 25 source-target cells must complete.
#   3. Every diagonal cell must reproduce the Table (1) AST AUROC to 4 decimals:
#        CL-7B=0.7950, SC2-7B=0.7689, SC2-15B=0.7666,
#        GO-120B=0.8837, GM4-31B=0.7767.
#
# SERVER NAMING
#   The development file may carry -v1, -v2, ... outside the server package.
#   The server package intentionally removes the version suffix from this file
#   and from the corresponding Python script.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PY_SCRIPT="${PY_SCRIPT:-src/app/compute_agc_transfer_same_test.py}"
ML_ROOT="${ML_ROOT:-src/ml_embeddings/data_codesearchnet}"
OUTPUT_ROOT="${OUTPUT_ROOT:-src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c}"
EXPECTED_SKLEARN_VERSION="${EXPECTED_SKLEARN_VERSION:-1.4.2}"
STRICT_SKLEARN_VERSION="${STRICT_SKLEARN_VERSION:-0}"
ALLOW_OVERWRITE="${ALLOW_OVERWRITE:-0}"

TS="$(date +'%Y%m%d_%H%M%S')"
RUN_LOG_DIR="${LOG_DIR:-src/logs/run4c-same-test/${TS}}"
MASTER_LOG="${RUN_LOG_DIR}/master.log"
mkdir -p "${RUN_LOG_DIR}"

exec > >(tee -a "${MASTER_LOG}") 2>&1

echo "========================================================================="
echo " run4c: Exact Table (1) Test-Support Cross-Generator Transfer"
echo " Python script : ${PY_SCRIPT}"
echo " ML root       : ${ML_ROOT}"
echo " Output root   : ${OUTPUT_ROOT}"
echo " Log directory : ${RUN_LOG_DIR}"
echo " Pickle sklearn  : ${EXPECTED_SKLEARN_VERSION}"
echo " Strict sklearn  : ${STRICT_SKLEARN_VERSION}"
echo " Started        : $(date -Is)"
echo "========================================================================="

# -----------------------------------------------------------------------------
# Preflight 1: required Python analysis script.
# -----------------------------------------------------------------------------
if [ ! -f "${PY_SCRIPT}" ]; then
  echo "[ERROR] Missing run4c Python script: ${PY_SCRIPT}" >&2
  exit 2
fi

# -----------------------------------------------------------------------------
# Preflight 2: refuse to mix results from separate runs.
# -----------------------------------------------------------------------------
if [ -d "${OUTPUT_ROOT}" ] && find "${OUTPUT_ROOT}" -type f -print -quit 2>/dev/null | grep -q .; then
  if [ "${ALLOW_OVERWRITE}" != "1" ]; then
    echo "[ERROR] Output root already contains files: ${OUTPUT_ROOT}" >&2
    echo "        Use a new OUTPUT_ROOT, or explicitly set ALLOW_OVERWRITE=1." >&2
    exit 2
  fi
fi
mkdir -p "${OUTPUT_ROOT}"

# -----------------------------------------------------------------------------
# Preflight 3: record the runtime sklearn version. The frozen pickles report
# serialization under 1.4.2, while the existing detectcodegpt server environment
# may use 1.3.2. Run4c therefore warns on a mismatch and lets the exact Table (1)
# diagonal reproduction QC decide whether the environment is behaviorally valid.
# -----------------------------------------------------------------------------
RUNTIME_SKLEARN_VERSION="$(python -c 'import sklearn; print(sklearn.__version__)')"
echo "Runtime sklearn: ${RUNTIME_SKLEARN_VERSION}"

if [ "${RUNTIME_SKLEARN_VERSION}" != "${EXPECTED_SKLEARN_VERSION}" ]; then
  echo "[WARN] scikit-learn version differs from the pickle serialization version." >&2
  echo "       runtime : ${RUNTIME_SKLEARN_VERSION}" >&2
  echo "       pickle  : ${EXPECTED_SKLEARN_VERSION}" >&2
  echo "       Proceeding because run4c has an exact 5/5 diagonal reproduction gate." >&2
  if [ "${STRICT_SKLEARN_VERSION}" = "1" ]; then
    echo "[ERROR] STRICT_SKLEARN_VERSION=1; aborting on version mismatch." >&2
    exit 3
  fi
fi

PY_ARGS=(
  --ml-root "${ML_ROOT}"
  --output-root "${OUTPUT_ROOT}"
  --expected-sklearn-version "${EXPECTED_SKLEARN_VERSION}"
)

if [ "${STRICT_SKLEARN_VERSION}" = "1" ]; then
  PY_ARGS+=(--strict-sklearn-version)
fi

# -----------------------------------------------------------------------------
# Run the complete 5x5 experiment in one Python process so each frozen source
# classifier is loaded once and applied to all five exact target test supports.
# -----------------------------------------------------------------------------
python "${PY_SCRIPT}" "${PY_ARGS[@]}"

# -----------------------------------------------------------------------------
# Final artifact audit. The Python analysis already performs row counts,
# class-balance checks, 25-cell checks, and Table (1) diagonal reproduction.
# Here the shell wrapper verifies that the paper-facing summary artifacts exist.
# -----------------------------------------------------------------------------
REQUIRED_OUTPUTS=(
  "matrix_auroc.csv"
  "cell_metrics.csv"
  "diagonal_qc.csv"
  "source_config_manifest.csv"
  "target_test_manifest.csv"
  "table2_rows.tex"
  "environment.txt"
)

for rel in "${REQUIRED_OUTPUTS[@]}"; do
  if [ ! -s "${OUTPUT_ROOT}/${rel}" ]; then
    echo "[ERROR] Missing or empty expected output: ${OUTPUT_ROOT}/${rel}" >&2
    exit 4
  fi
done

PRED_COUNT="$(find "${OUTPUT_ROOT}/predictions" -type f -name 'target-*.csv' | wc -l | tr -d ' ')"
if [ "${PRED_COUNT}" -ne 25 ]; then
  echo "[ERROR] Expected 25 cell prediction CSVs, found ${PRED_COUNT}" >&2
  exit 4
fi

echo "========================================================================="
echo " COMPLETE"
echo " Prediction cells: ${PRED_COUNT}/25"
echo " Matrix          : ${OUTPUT_ROOT}/matrix_auroc.csv"
echo " Diagonal QC     : ${OUTPUT_ROOT}/diagonal_qc.csv"
echo " Table rows      : ${OUTPUT_ROOT}/table2_rows.tex"
echo " Master log      : ${MASTER_LOG}"
echo " Finished        : $(date -Is)"
echo "========================================================================="
