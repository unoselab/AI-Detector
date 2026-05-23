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
#   SRC_CSV     - override the source AST CSV (input)
#   OUT_DIR     - override the output directory (default: src/app/mixed_samples)
#   SEED        - RNG seed (default: 42 inside the Python script)
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
# Optional overrides
# -----------------------------------------------------------------------------
EXTRA_ARGS=()
if [ -n "${SRC_CSV:-}" ]; then EXTRA_ARGS+=(--src-csv "${SRC_CSV}"); fi
if [ -n "${OUT_DIR:-}" ]; then EXTRA_ARGS+=(--out-dir "${OUT_DIR}"); fi
if [ -n "${SEED:-}" ];    then EXTRA_ARGS+=(--seed    "${SEED}");    fi

OUT_DIR_RESOLVED="${OUT_DIR:-src/app/mixed_samples}"

echo "============================================================"
echo " run0-build-mixed-samples.sh"
echo "   src csv      : ${SRC_CSV:-<default>}"
echo "   out dir      : ${OUT_DIR_RESOLVED}"
echo "   seed         : ${SEED:-<default 42>}"
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