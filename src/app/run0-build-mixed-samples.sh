#!/usr/bin/env bash
# =============================================================================
# run0-build-mixed-samples.sh
# -----------------------------------------------------------------------------
# Build the 10 synthetic mixed-authorship test files for agc_detector.py.
#
# Wraps src/app/build_mixed_samples.py. The Python script's default paths
# are expressed RELATIVE TO THE REPO ROOT (e.g.
# "src/code-analyzer-tree-sitter/data_codesearchnet/..."), so this driver
# `cd`s to the repo root before invoking it. Running this script from any
# directory therefore works.
#
# Outputs land in:
#   src/app/mixed_samples/
#       mixed_sample_001.py / .labels.tsv
#       ...
#       mixed_sample_010.py / .labels.tsv
#       manifest.csv
#
# Usage
#   bash src/app/run0-build-mixed-samples.sh
#
# Customization (env vars)
#   SRC_CSV            - override the source AST CSV (input)
#   SPLITS_DIR         - override split dir used for test-only sampling
#   OUT_DIR            - override output directory (default: src/app/mixed_samples)
#   SEED               - RNG seed (default: 42 inside the Python script)
#   NUM_SAMPLES        - number of mixed .py files to generate
#   BLOCKS_PER_SAMPLE  - number of top-level blocks per file
#   LM_RATIO           - fraction of blocks sampled from lm/AGC rows
#   INCLUDE_CORNERS=1  - sample 001 all-human, sample 002 all-lm
#   ALLOW_REUSE=1      - allow same source rows to be reused across samples
#   NO_SPLIT_FILTER=1  - draw from all rows, not just test split
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Resolve repo root from THIS script's location:
#   this script lives in src/app/, so repo root is two dirs above.
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run0-build-mixed-samples_${TS}.log}"
mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "Log file : ${LOG_FILE}"
echo "Started  : $(date -Is)"
echo "Repo root: ${REPO_ROOT}"
echo

# -----------------------------------------------------------------------------
# Editable configuration
# -----------------------------------------------------------------------------
MODEL_NAME="starcoder2-15b-instruct-v0.1"
DATASET_SIZE="2700"

SRC_CSV="src/code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/ast/codesearchnet_${MODEL_NAME}_python_merged_${DATASET_SIZE}.csv"
SPLITS_DIR="src/ml_embeddings/data_codesearchnet/splits/${MODEL_NAME}/codesearchnet_${MODEL_NAME}_python_merged_${DATASET_SIZE}"

OUT_DIR="src/app/mixed_samples_50x6"

SEED="42"
NUM_SAMPLES="50"
BLOCKS_PER_SAMPLE="6"
LM_RATIO="0.5"
INCLUDE_CORNERS="1"

# Keep these disabled for reportable evaluation.
ALLOW_REUSE="0"
NO_SPLIT_FILTER="0"

OUT_DIR_RESOLVED="${OUT_DIR}"

# -----------------------------------------------------------------------------
# Build Python arguments
# -----------------------------------------------------------------------------
EXTRA_ARGS=(
  --src-csv "${SRC_CSV}"
  --splits-dir "${SPLITS_DIR}"
  --out-dir "${OUT_DIR}"
  --seed "${SEED}"
  --num-samples "${NUM_SAMPLES}"
  --blocks-per-sample "${BLOCKS_PER_SAMPLE}"
  --lm-ratio "${LM_RATIO}"
)

if [ "${INCLUDE_CORNERS}" = "1" ]; then
  EXTRA_ARGS+=(--include-corners)
fi

if [ "${ALLOW_REUSE}" = "1" ]; then
  EXTRA_ARGS+=(--allow-reuse)
fi

if [ "${NO_SPLIT_FILTER}" = "1" ]; then
  EXTRA_ARGS+=(--no-split-filter)
fi

echo "============================================================"
echo " run0-build-mixed-samples.sh"
echo "   model name        : ${MODEL_NAME}"
echo "   dataset size      : ${DATASET_SIZE}"
echo "   src csv           : ${SRC_CSV}"
echo "   splits dir        : ${SPLITS_DIR}"
echo "   out dir           : ${OUT_DIR_RESOLVED}"
echo "   seed              : ${SEED}"
echo "   num samples       : ${NUM_SAMPLES}"
echo "   blocks per sample : ${BLOCKS_PER_SAMPLE}"
echo "   lm ratio          : ${LM_RATIO}"
echo "   include corners   : ${INCLUDE_CORNERS}"
echo "   allow reuse       : ${ALLOW_REUSE}"
echo "   no split filter   : ${NO_SPLIT_FILTER}"
echo "============================================================"
echo

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
python src/app/build_mixed_samples.py "${EXTRA_ARGS[@]}"

# -----------------------------------------------------------------------------
# Post-run summary
# -----------------------------------------------------------------------------
echo
echo "============================================================"
echo " Output summary"
echo "============================================================"

if [ -d "${OUT_DIR_RESOLVED}" ]; then
  n_py=$(  find "${OUT_DIR_RESOLVED}" -maxdepth 1 -name 'mixed_sample_*.py'         | wc -l)
  n_tsv=$( find "${OUT_DIR_RESOLVED}" -maxdepth 1 -name 'mixed_sample_*.labels.tsv' | wc -l)
  manifest="${OUT_DIR_RESOLVED}/manifest.csv"

  echo "  py files     : ${n_py}"
  echo "  tsv files    : ${n_tsv}"
  echo "  manifest     : $([ -f "${manifest}" ] && echo "${manifest}" || echo "<missing>")"
  echo

  # Sanity check: each generated .py must parse as valid Python.
  echo "Validating generated .py files parse as Python:"
  bad=0
  for f in "${OUT_DIR_RESOLVED}"/mixed_sample_*.py; do
    [ -f "${f}" ] || continue
    if python -c "import ast; ast.parse(open('${f}').read())" 2>/dev/null; then
      echo "  OK   ${f}"
    else
      echo "  BAD  ${f}"
      bad=$((bad+1))
    fi
  done
  if [ "${bad}" -gt 0 ]; then
    echo "[WARN] ${bad} file(s) failed to parse. Inspect them before running agc_detector.py."
  fi
fi

echo
echo "Finished : $(date -Is)"
echo "Log file : ${LOG_FILE}"