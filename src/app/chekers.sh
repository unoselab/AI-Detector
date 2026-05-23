cp run1-agc-detector.sh bak/run1-agc-detector.sh.bak_$(date +%Y%m%d_%H%M%S)

cat > run1-agc-detector.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

# Run agc_detector.py on one file or one directory.
# The Python process handles directory iteration, so CodeT5+ loads only once.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Editable detector configuration
# -----------------------------------------------------------------------------
INPUT_DIR="${INPUT_DIR:-src/app/mixed_samples_50x6}"
INPUT_FILE="${INPUT_FILE:-}"

EMBEDDING="${EMBEDDING:-ast}"

USE_HIGH_CONF_THRESHOLD="${USE_HIGH_CONF_THRESHOLD:-1}"
HIGH_CONF_THRESHOLD="${HIGH_CONF_THRESHOLD:--1.3439}"

if [ "${USE_HIGH_CONF_THRESHOLD}" = "1" ] && [ -z "${THRESHOLD:-}" ]; then
  THRESHOLD="${HIGH_CONF_THRESHOLD}"
fi

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
echo "   input dir    : ${INPUT_DIR}"
echo "   input file   : ${INPUT_FILE:-<none; directory mode>}"
echo "   model pickle : ${MODEL_PICKLE:-<default: latest SVM>}"
echo "   embedding    : ${EMBEDDING}"
echo "   threshold    : ${THRESHOLD:-<default: 0.5/0.0>}"
echo "   device       : ${DEVICE:-<auto>}"
echo "   out dir      : ${OUT_DIR}"
echo "============================================================"
echo

if [ -n "${INPUT_FILE}" ]; then
  # Resolve a single file path.
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
else
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
SH

chmod +x run1-agc-detector.sh