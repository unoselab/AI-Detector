#!/usr/bin/env bash
# =============================================================================
# run0-build-mixed-samples.sh
# -----------------------------------------------------------------------------
# Build the synthetic mixed-authorship test files for agc_detector.py.
#
# Wraps src/app/build_mixed_samples.py. The builder now takes a SINGLE input:
# the split's test_.csv. Every row in that file is already test data, so there
# is no separate split-filter step -- test-only sampling is guaranteed simply
# by which CSV is passed in. The author label of each block is taken from the
# row's `idx` suffix (`..._human` / `..._lm`), and only the `idx` and `code`
# columns are loaded (heavy embedding columns are skipped).
#
# The Python script's default paths are expressed RELATIVE TO THE REPO ROOT,
# so this driver `cd`s to the repo root before invoking it. Running this script
# from any directory therefore works.
#
# Outputs land in:
#   ${OUT_DIR}/
#       mixed_sample_001.py / .labels.tsv
#       ...
#       manifest.csv
#
# Usage
#   bash src/app/run0-build-mixed-samples.sh
#
# Customization (env vars)
#   INPUT_CSV          - override the single input CSV (default: the test_.csv)
#   OUT_DIR            - override output directory
#   SEED               - RNG seed
#   NUM_SAMPLES        - number of mixed .py files to generate
#   BLOCKS_PER_SAMPLE  - number of top-level blocks per file
#   LM_RATIO           - fraction of blocks sampled from lm/AGC rows
#   INCLUDE_CORNERS=1  - sample 001 all-human, sample 002 all-lm
#   ALLOW_REUSE=1      - allow same source rows to be reused across samples
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
MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
DATASET_SIZE="${DATASET_SIZE:-2700}"

# Single input: the split's test_.csv (idx + code; label from idx suffix).
INPUT_CSV="${INPUT_CSV:-src/ml_embeddings/data_codesearchnet/splits/${MODEL_NAME}/codesearchnet_${MODEL_NAME}_python_merged_${DATASET_SIZE}/test_.csv}"

SEED="${SEED:-42}"
NUM_SAMPLES="${NUM_SAMPLES:-50}"
BLOCKS_PER_SAMPLE="${BLOCKS_PER_SAMPLE:-6}"
LM_RATIO="${LM_RATIO:-0.5}"
INCLUDE_CORNERS="${INCLUDE_CORNERS:-1}"

# Keep this disabled for reportable evaluation.
ALLOW_REUSE="${ALLOW_REUSE:-0}"

# Output dir encodes model name + data size + sample geometry so runs with
# different settings do not overwrite one another:
#   src/app/data_mixed_samples/<model>/merged_<size>/<num>x<blocks>
# e.g. src/app/data_mixed_samples/starcoder2-15b-instruct-v0.1/merged_2700/50x6
#
# NOTE: only model, size, and the NxK geometry are in the path. If you also
# sweep LM_RATIO or SEED, append them to the leaf to avoid collisions, e.g.
#   .../${NUM_SAMPLES}x${BLOCKS_PER_SAMPLE}_lm${LM_RATIO}_seed${SEED}
OUT_DIR="${OUT_DIR:-src/app/data_mixed_samples/${MODEL_NAME}/merged_${DATASET_SIZE}/${NUM_SAMPLES}x${BLOCKS_PER_SAMPLE}}"

OUT_DIR_RESOLVED="${OUT_DIR}"

# -----------------------------------------------------------------------------
# Build Python arguments
# -----------------------------------------------------------------------------
EXTRA_ARGS=(
  --input-csv "${INPUT_CSV}"
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

echo "============================================================"
echo " run0-build-mixed-samples.sh"
echo "   model name        : ${MODEL_NAME}"
echo "   dataset size      : ${DATASET_SIZE}"
echo "   input csv         : ${INPUT_CSV}"
echo "   out dir           : ${OUT_DIR_RESOLVED}"
echo "   seed              : ${SEED}"
echo "   num samples       : ${NUM_SAMPLES}"
echo "   blocks per sample : ${BLOCKS_PER_SAMPLE}"
echo "   lm ratio          : ${LM_RATIO}"
echo "   include corners   : ${INCLUDE_CORNERS}"
echo "   allow reuse       : ${ALLOW_REUSE}"
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