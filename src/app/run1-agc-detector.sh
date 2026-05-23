#!/usr/bin/env bash
# =============================================================================
# run1-agc-detector.sh
# -----------------------------------------------------------------------------
# Run agc_detector.py against one or more .py files.
#
# What this does
#   Wraps src/app/agc_detector.py. For each input file, the detector:
#     1. Parses the file with tree-sitter, extracts top-level def/class blocks.
#     2. Generates an AST sequence + CodeT5+ embedding per block from scratch.
#     3. Loads a tuned classifier pickle and predicts HWC vs AGC per block.
#     4. Compares against <input>.labels.tsv if present.
#
#   The embedder model loads once per invocation; multi-file scans share it.
#
# Default behavior
#   With no args, scans ALL mixed_sample_*.py files in src/app/mixed_samples/.
#   With explicit args, scans just those files.
#
# Usage
#   bash src/app/run1-agc-detector.sh                                 # all samples
#   bash src/app/run1-agc-detector.sh src/app/mixed_samples/mixed_sample_003.py
#   bash src/app/run1-agc-detector.sh src/app/mixed_samples/mixed_sample_0{03,06}.py
#
# Customization (env vars)
#   MODEL_PICKLE  - tuned classifier pickle path
#                   (default: latest SVM under data_codesearchnet/models/.../)
#   EMBEDDING     - ast | code | combined  (default: ast)
#   THRESHOLD     - decision threshold; default 0.5 (proba) or 0.0 (SVM margin)
#   DEVICE        - cuda | cuda:0 | cpu (default: auto-detect)
#   OUT_DIR       - where to write per-input prediction TSVs
#                   (default: src/app/mixed_samples/predictions)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run1-agc-detector_${TS}.log}"
mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "Log file : ${LOG_FILE}"
echo "Started  : $(date -Is)"
echo "Repo root: ${REPO_ROOT}"
echo

# -----------------------------------------------------------------------------
# Inputs: positional args, INPUT_FILE, or default to all mixed_sample_*.py
# -----------------------------------------------------------------------------
DEFAULT_INPUT_GLOB="src/app/mixed_samples/mixed_sample_*.py"

INPUTS=()

# Allow single-file env-var usage:
#   INPUT_FILE=mixed_samples/mixed_sample_002.py bash run1-agc-detector.sh
if [ "$#" -eq 0 ] && [ -n "${INPUT_FILE:-}" ]; then
  set -- "${INPUT_FILE}"
fi

if [ "$#" -eq 0 ]; then
  while IFS= read -r -d '' f; do
    INPUTS+=("${f}")
  done < <(find src/app/mixed_samples -maxdepth 1 -name 'mixed_sample_*.py' -print0 2>/dev/null | sort -z)
else
  for f in "$@"; do
    if [[ "${f}" = /* ]]; then
      # Already absolute.
      INPUTS+=("${f}")
    elif [ -f "${REPO_ROOT}/${f}" ]; then
      # Relative to repo root, e.g. src/app/mixed_samples/mixed_sample_002.py
      INPUTS+=("${REPO_ROOT}/${f}")
    elif [ -f "${SCRIPT_DIR}/${f}" ]; then
      # Relative to src/app, e.g. mixed_samples/mixed_sample_002.py
      INPUTS+=("${SCRIPT_DIR}/${f}")
    else
      # Keep a useful path for the error message.
      INPUTS+=("${SCRIPT_DIR}/${f}")
    fi
  done
fi

# -----------------------------------------------------------------------------
# Optional overrides assembled into args
# -----------------------------------------------------------------------------
EXTRA_ARGS=()
if [ -n "${MODEL_PICKLE:-}" ]; then EXTRA_ARGS+=(--model-pickle "${MODEL_PICKLE}"); fi
if [ -n "${EMBEDDING:-}" ];    then EXTRA_ARGS+=(--embedding    "${EMBEDDING}");    fi
if [ -n "${THRESHOLD:-}" ];    then EXTRA_ARGS+=(--threshold    "${THRESHOLD}");    fi
if [ -n "${DEVICE:-}" ];       then EXTRA_ARGS+=(--device       "${DEVICE}");       fi

OUT_DIR="${OUT_DIR:-src/app/mixed_samples/predictions}"
mkdir -p "${OUT_DIR}"

# -----------------------------------------------------------------------------
# Banner
# -----------------------------------------------------------------------------
echo "============================================================"
echo " run1-agc-detector.sh"
echo "   inputs       : ${#INPUTS[@]} file(s)"
echo "   model pickle : ${MODEL_PICKLE:-<default: latest SVM>}"
echo "   embedding    : ${EMBEDDING:-<default: ast>}"
echo "   threshold    : ${THRESHOLD:-<default: 0.5/0.0>}"
echo "   device       : ${DEVICE:-<auto>}"
echo "   out dir      : ${OUT_DIR}"
echo "============================================================"
echo

# -----------------------------------------------------------------------------
# Per-input scan
# -----------------------------------------------------------------------------
for f in "${INPUTS[@]}"; do
  if [ ! -f "${f}" ]; then
    echo "[ERROR] not a file: ${f}" >&2
    continue
  fi

  base="$(basename "${f}" .py)"
  out_tsv="${OUT_DIR}/${base}.predictions.tsv"

  echo
  echo "------------------------------------------------------------"
  echo " scanning : ${f}"
  echo " out tsv  : ${out_tsv}"
  echo "------------------------------------------------------------"

  python src/app/agc_detector.py \
    --input "${f}" \
    --out-tsv "${out_tsv}" \
    "${EXTRA_ARGS[@]}"
done

echo
echo "Finished : $(date -Is)"
echo "Log file : ${LOG_FILE}"