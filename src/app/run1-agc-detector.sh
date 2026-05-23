#!/usr/bin/env bash
set -euo pipefail

# Run agc_detector.py on one of three input shapes:
#   1. INPUT_FILE  (or positional arg)  → single .py
#   2. INPUT_GRID                       → root containing blocks_*/ subdirs
#                                         (single Python process, one CodeT5+ load)
#   3. INPUT_DIR                        → one directory of mixed_sample_*.py
#
# Precedence: positional arg / INPUT_FILE > INPUT_GRID > INPUT_DIR.
#
# Examples
#   ./run1-agc-detector.sh                                    # uses INPUT_DIR default
#   INPUT_GRID=src/app/data_mixed_samples_grid_480 ./run1-agc-detector.sh
#   ./run1-agc-detector.sh path/to/one_file.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Editable detector configuration
# -----------------------------------------------------------------------------
INPUT_DIR="${INPUT_DIR:-src/app/mixed_samples_50x6}"
INPUT_FILE="${INPUT_FILE:-}"

# Set INPUT_GRID to a root that contains blocks_*/ subdirs to run the full grid
# in one Python process. Predictions land in each subdir's own predictions/
# folder, plus a grid-level predictions_summary.csv at the root.
INPUT_GRID="${INPUT_GRID:-src/app/data_mixed_samples_grid_480}"
SUBDIR_PATTERN="${SUBDIR_PATTERN:-blocks_*}"

EMBEDDING="${EMBEDDING:-ast}"

USE_HIGH_CONF_THRESHOLD="${USE_HIGH_CONF_THRESHOLD:-1}"
HIGH_CONF_THRESHOLD="${HIGH_CONF_THRESHOLD:--1.3439}"

if [ "${USE_HIGH_CONF_THRESHOLD}" = "1" ] && [ -z "${THRESHOLD:-}" ]; then
  THRESHOLD="${HIGH_CONF_THRESHOLD}"
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
# Optional overrides
# -----------------------------------------------------------------------------
EXTRA_ARGS=()

if [ -n "${MODEL_PICKLE:-}" ]; then
  EXTRA_ARGS+=(--model-pickle "${MODEL_PICKLE}")
fi

if [ -n "${EMBEDDING:-}" ]; then
  EXTRA_ARGS+=(--embedding "${EMBEDDING}")
fi

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
echo "   input file   : ${INPUT_FILE:-<none>}"
echo "   input grid   : ${INPUT_GRID:-<none>}"
echo "   input dir    : ${INPUT_DIR}"
echo "   subdir glob  : ${SUBDIR_PATTERN}  (used only with INPUT_GRID)"
echo "   model pickle : ${MODEL_PICKLE:-<default: latest SVM>}"
echo "   embedding    : ${EMBEDDING}"
echo "   threshold    : ${THRESHOLD:-<default: 0.5/0.0>}"
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