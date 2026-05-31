#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1-agc-detector.sh
# -----------------------------------------------------------------------------
# Run agc_detector.py on one of three input shapes:
#   1. INPUT_FILE  (or positional arg)  -> single .py
#   2. INPUT_GRID                       -> root containing blocks_*/ subdirs
#                                          (single Python process, one CodeT5+ load)
#   3. INPUT_DIR                        -> one directory of mixed_sample_*.py  [DEFAULT]
#
# Precedence: positional arg / INPUT_FILE > INPUT_GRID > INPUT_DIR.
# INPUT_GRID is now OPT-IN (empty by default), so single-dir mode runs unless
# you explicitly set INPUT_GRID.
#
# IMPORTANT - train/test provenance:
#   The classifier MUST be the one trained on the SAME experiment that produced
#   the input mixed samples. This script resolves a concrete SVM pickle from the
#   experiment's models dir and passes it with --model-pickle. It does NOT fall
#   back to the detector's generic default glob. If no experiment-matched pickle
#   is found, it errors out and asks you to set MODEL_PICKLE.
#
# IMPORTANT - max_len:
#   The tokenizer truncation length must match what the classifier trained on.
#   The *_maxlen2048 experiments embed at 2048; this script defaults MAX_LEN=2048.
#
# IMPORTANT - threshold:
#   The old -1.3439 high-confidence cutoff was calibrated for the 2700 SVM+AST
#   model and is NOT valid for a different model. High-conf mode is OFF by
#   default; enable it (USE_HIGH_CONF_THRESHOLD=1) only after re-deriving a
#   cutoff for THIS model on its own dev split.
#
# Examples
#   bash src/app/run1-agc-detector.sh                         # single-dir default
#   INPUT_GRID=src/app/data_mixed_samples_grid/... bash src/app/run1-agc-detector.sh
#   bash src/app/run1-agc-detector.sh path/to/one_file.py
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Experiment identity (drives BOTH the input dir and the model selection so
# they stay consistent).
# -----------------------------------------------------------------------------
MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
EXP_NAME="${EXP_NAME:-starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048}"

NUM_SAMPLES="${NUM_SAMPLES:-50}"
BLOCKS_PER_SAMPLE="${BLOCKS_PER_SAMPLE:-6}"
GEOMETRY="${GEOMETRY:-${NUM_SAMPLES}x${BLOCKS_PER_SAMPLE}}"

# -----------------------------------------------------------------------------
# Input shapes. Single-dir is the default; matches run0's output layout:
#   src/app/data_mixed_samples/<EXP_NAME>/<NxK>
# -----------------------------------------------------------------------------
INPUT_DIR="${INPUT_DIR:-src/app/data_mixed_samples/${EXP_NAME}/${GEOMETRY}}"
INPUT_FILE="${INPUT_FILE:-}"
INPUT_GRID="${INPUT_GRID:-}"            # empty => single-dir mode wins
SUBDIR_PATTERN="${SUBDIR_PATTERN:-blocks_*}"

# -----------------------------------------------------------------------------
# Detector configuration
# -----------------------------------------------------------------------------
EMBEDDING="${EMBEDDING:-ast}"

# Tokenizer truncation length. Must match the classifier's training length.
MAX_LEN="${MAX_LEN:-2048}"

# Threshold: high-conf mode OFF by default (see header note).
USE_HIGH_CONF_THRESHOLD="${USE_HIGH_CONF_THRESHOLD:-0}"
HIGH_CONF_THRESHOLD="${HIGH_CONF_THRESHOLD:--1.3439}"
if [ "${USE_HIGH_CONF_THRESHOLD}" = "1" ] && [ -z "${THRESHOLD:-}" ]; then
  THRESHOLD="${HIGH_CONF_THRESHOLD}"
fi

# -----------------------------------------------------------------------------
# Model selection: resolve an SVM pickle from THIS experiment's models dir.
# -----------------------------------------------------------------------------
ALGO="${ALGO:-svm}"
MODEL_EXP="${MODEL_EXP:-${EXP_NAME}}"
MODELS_ROOT="${MODELS_ROOT:-src/ml_embeddings/data_codesearchnet/models}"
MODEL_GLOB="${MODEL_GLOB:-${MODELS_ROOT}/${MODEL_EXP}/tuned_models_*_${ALGO}_*.pkl}"
MODEL_PICKLE="${MODEL_PICKLE:-}"

if [ -z "${MODEL_PICKLE}" ]; then
  shopt -s nullglob
  cands=( ${MODEL_GLOB} )
  shopt -u nullglob
  if [ "${#cands[@]}" -eq 0 ]; then
    echo "[ERROR] no ${ALGO} pickle matched: ${MODEL_GLOB}" >&2
    echo "        The detector must use a classifier trained on the SAME" >&2
    echo "        experiment as the input data:" >&2
    echo "          EXP_NAME = ${EXP_NAME}" >&2
    echo "        The model-dir name may differ from EXP_NAME (e.g. a" >&2
    echo "        'complexity_fixedtest_maxlen2048' tag). Fix one of:" >&2
    echo "          MODEL_EXP=<models-subdir>   (currently: ${MODEL_EXP})" >&2
    echo "          MODEL_GLOB=<full glob>" >&2
    echo "          MODEL_PICKLE=<exact .pkl>" >&2
    echo "        Available model dirs:" >&2
    ls -1 "${MODELS_ROOT}" 2>/dev/null | sed 's/^/          /' >&2 || true
    exit 1
  fi
  # Timestamped filenames sort chronologically; take the latest.
  MODEL_PICKLE="$(printf '%s\n' "${cands[@]}" | sort | tail -n1)"
fi

# OUT_DIR applies to single-dir mode only. In grid mode predictions go to
# each subdir's own <subdir>/predictions/ folder automatically.
OUT_DIR="${OUT_DIR:-${INPUT_DIR}/predictions}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run1-agc-detector_${TS}.log}"
mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

# -----------------------------------------------------------------------------
# Build detector arguments
# -----------------------------------------------------------------------------
EXTRA_ARGS=()
EXTRA_ARGS+=(--model-pickle "${MODEL_PICKLE}")
EXTRA_ARGS+=(--embedding "${EMBEDDING}")
EXTRA_ARGS+=(--max-len "${MAX_LEN}")

if [ -n "${THRESHOLD:-}" ]; then
  EXTRA_ARGS+=(--threshold "${THRESHOLD}")
fi

if [ -n "${DEVICE:-}" ]; then
  EXTRA_ARGS+=(--device "${DEVICE}")
fi

# Positional arg wins over INPUT_FILE.
if [ "$#" -gt 0 ]; then
  INPUT_FILE="$1"
fi

echo "Log file : ${LOG_FILE}"
echo "Started  : $(date -Is)"
echo "Repo root: ${REPO_ROOT}"
echo

echo "============================================================"
echo " run1-agc-detector.sh"
echo "   experiment   : ${EXP_NAME}"
echo "   input file   : ${INPUT_FILE:-<none>}"
echo "   input grid   : ${INPUT_GRID:-<none>}"
echo "   input dir    : ${INPUT_DIR}"
echo "   subdir glob  : ${SUBDIR_PATTERN}  (used only with INPUT_GRID)"
echo "   model pickle : ${MODEL_PICKLE}"
echo "   embedding    : ${EMBEDDING}"
echo "   max len      : ${MAX_LEN}"
echo "   threshold    : ${THRESHOLD:-<default: 0.5/0.0>}"
echo "   high-conf    : ${USE_HIGH_CONF_THRESHOLD}"
echo "   device       : ${DEVICE:-<auto>}"
echo "   out dir      : ${OUT_DIR}  (single-dir mode only)"
echo "============================================================"
echo

if [ -n "${INPUT_FILE}" ]; then
  # ---- Single-file mode ----
  if [[ "${INPUT_FILE}" = /* ]]; then
    RESOLVED_INPUT="${INPUT_FILE}"
  elif [ -f "${REPO_ROOT}/${INPUT_FILE}" ]; then
    RESOLVED_INPUT="${REPO_ROOT}/${INPUT_FILE}"
  elif [ -f "${SCRIPT_DIR}/${INPUT_FILE}" ]; then
    RESOLVED_INPUT="${SCRIPT_DIR}/${INPUT_FILE}"
  else
    echo "[ERROR] input file not found: ${INPUT_FILE}" >&2
    exit 1
  fi

  mkdir -p "${OUT_DIR}"
  base="$(basename "${RESOLVED_INPUT}" .py)"
  python src/app/agc_detector.py \
    --input "${RESOLVED_INPUT}" \
    --out-tsv "${OUT_DIR}/${base}.predictions.tsv" \
    "${EXTRA_ARGS[@]}"

elif [ -n "${INPUT_GRID}" ]; then
  # ---- Grid mode: single Python process scans all matching subdirs ----
  if [ ! -d "${INPUT_GRID}" ]; then
    echo "[ERROR] input grid not found: ${INPUT_GRID}" >&2
    exit 1
  fi

  python src/app/agc_detector.py \
    --input-grid "${INPUT_GRID}" \
    --subdir-pattern "${SUBDIR_PATTERN}" \
    "${EXTRA_ARGS[@]}"

else
  # ---- Single-dir mode ----
  if [ ! -d "${INPUT_DIR}" ]; then
    echo "[ERROR] input dir not found: ${INPUT_DIR}" >&2
    exit 1
  fi

  mkdir -p "${OUT_DIR}"
  python src/app/agc_detector.py \
    --input-dir "${INPUT_DIR}" \
    --out-dir "${OUT_DIR}" \
    "${EXTRA_ARGS[@]}"
fi

echo
echo "Finished : $(date -Is)"
echo "Log file : ${LOG_FILE}"