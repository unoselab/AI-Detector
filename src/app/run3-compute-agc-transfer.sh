#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run3-compute-agc-transfer.sh
# -----------------------------------------------------------------------------
# Cross-generator TRANSFER evaluation.
#
# Holds ONE classifier fixed (default: GPT-OSS) and scores the existing 50x6
# mixed-sample .py sets of OTHER generators with it. This isolates the
# classifier as the only changed variable: the input .py files are reused
# unchanged from data_mixed_samples/<target>/50x6/.
#
# The classifier's OWN generator is skipped (that is the matched diagonal,
# already produced by run1-agc-detector.sh).
#
# Outputs (never collide with matched results):
#   data_mixed_samples_transfer/clf-<CLF_GEN>/<target>/50x6/predictions/
#
# Usage
#   bash src/app/run3-compute-agc-transfer.sh
#   CLF_GEN=starcoder2-15b-instruct-v0.1 bash src/app/run3-compute-agc-transfer.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Fixed classifier identity
# -----------------------------------------------------------------------------
# CLF_EXP = the models-dir experiment name for the fixed classifier.
# CLF_GEN = short tag used in the classifier's pickle key and output path.
CLF_EXP="${CLF_EXP:-gpt-oss_4500_complexity_stratified_maxlen2048}"
CLF_GEN="${CLF_GEN:-gpt-oss}"

ALGO="${ALGO:-svm}"
MODELS_ROOT="${MODELS_ROOT:-src/ml_embeddings/data_codesearchnet/models}"
MODEL_GLOB="${MODEL_GLOB:-${MODELS_ROOT}/${CLF_EXP}/tuned_models_*_${ALGO}_*.pkl}"
MODEL_PICKLE="${MODEL_PICKLE:-}"   # set explicitly to pin a specific timestamp

# -----------------------------------------------------------------------------
# Target generators (their existing 50x6 .py sets get re-scored).
# The classifier's own generator is excluded automatically.
# -----------------------------------------------------------------------------
TARGETS_DEFAULT=(
  "starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048"
  "codellama-7b_4500_complexity_stratified_maxlen2048"
  "starcoder2-7b_4500_complexity_stratified_maxlen2048"
  "gemma_4500_complexity_stratified_maxlen2048"
  "gpt-oss_4500_complexity_stratified_maxlen2048"
)
# Allow override: TARGETS="exp1 exp2 ..." bash run3-compute-agc-transfer.sh
if [ -n "${TARGETS:-}" ]; then
  read -r -a TARGETS_ARR <<< "${TARGETS}"
else
  TARGETS_ARR=("${TARGETS_DEFAULT[@]}")
fi

DATA_ROOT="${DATA_ROOT:-src/app/data_mixed_samples}"
TRANSFER_ROOT="${TRANSFER_ROOT:-src/app/data_mixed_samples_transfer/clf-${CLF_GEN}}"
GEOMETRY="${GEOMETRY:-50x6}"

EMBEDDING="${EMBEDDING:-ast}"
MAX_LEN="${MAX_LEN:-2048}"
# Transfer uses the natural decision boundary unless overridden.
THRESHOLD="${THRESHOLD:-}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run3-compute-agc-transfer_${TS}.log}"
mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

# -----------------------------------------------------------------------------
# Resolve the fixed classifier pickle ONCE.
# -----------------------------------------------------------------------------
if [ -z "${MODEL_PICKLE}" ]; then
  shopt -s nullglob
  cands=( ${MODEL_GLOB} )
  shopt -u nullglob
  if [ "${#cands[@]}" -eq 0 ]; then
    echo "[ERROR] no ${ALGO} pickle matched: ${MODEL_GLOB}" >&2
    echo "        Set MODEL_PICKLE / CLF_EXP. Available model dirs:" >&2
    ls -1 "${MODELS_ROOT}" 2>/dev/null | sed 's/^/          /' >&2 || true
    exit 1
  fi
  if [ "${#cands[@]}" -gt 1 ]; then
    echo "[WARN] ${#cands[@]} pickles matched; using the latest. Pin MODEL_PICKLE" >&2
    echo "       to report a specific one. Candidates:" >&2
    printf '       %s\n' "${cands[@]}" >&2
  fi
  MODEL_PICKLE="$(printf '%s\n' "${cands[@]}" | sort | tail -n1)"
fi

echo "Log file : ${LOG_FILE}"
echo "Started  : $(date -Is)"
echo "============================================================"
echo " run3-compute-agc-transfer.sh"
echo "   fixed classifier exp : ${CLF_EXP}"
echo "   fixed classifier gen : ${CLF_GEN}"
echo "   model pickle         : ${MODEL_PICKLE}"
echo "   embedding            : ${EMBEDDING}"
echo "   max len              : ${MAX_LEN}"
echo "   threshold            : ${THRESHOLD:-<default>}"
echo "   transfer root        : ${TRANSFER_ROOT}"
echo "   geometry             : ${GEOMETRY}"
echo "============================================================"
echo

EXTRA=()
EXTRA+=(--model-pickle "${MODEL_PICKLE}")
EXTRA+=(--embedding "${EMBEDDING}")
EXTRA+=(--max-len "${MAX_LEN}")
[ -n "${THRESHOLD}" ] && EXTRA+=(--threshold "${THRESHOLD}")
[ -n "${DEVICE:-}" ] && EXTRA+=(--device "${DEVICE}")

# INCLUDE_OWN=1 also scores the classifier's own generator (the matched
# diagonal), using the SAME pinned pickle so the whole row is comparable.
INCLUDE_OWN="${INCLUDE_OWN:-1}"

n_done=0
for target in "${TARGETS_ARR[@]}"; do
  if [ "${target}" = "${CLF_EXP}" ] && [ "${INCLUDE_OWN}" != "1" ]; then
    echo ">>> SKIP ${target} (classifier's own generator = matched diagonal)"
    echo
    continue
  fi
  if [ "${target}" = "${CLF_EXP}" ]; then
    echo ">>> DIAGONAL  clf=${CLF_GEN}  ->  own generator (matched, same pickle)"
  fi

  in_dir="${DATA_ROOT}/${target}/${GEOMETRY}"
  out_dir="${TRANSFER_ROOT}/${target}/${GEOMETRY}/predictions"

  if [ ! -d "${in_dir}" ]; then
    echo "[WARN] missing input dir, skipping: ${in_dir}"
    echo
    continue
  fi

  echo ">>> TRANSFER  clf=${CLF_GEN}  ->  target=${target}"
  echo "    in : ${in_dir}"
  echo "    out: ${out_dir}"
  mkdir -p "${out_dir}"

  python src/app/agc_detector.py \
    --input-dir "${in_dir}" \
    --out-dir "${out_dir}" \
    "${EXTRA[@]}"

  echo
  n_done=$((n_done+1))
done

echo "============================================================"
echo "Transfer runs completed: ${n_done}"
echo "Finished : $(date -Is)"
echo "Log file : ${LOG_FILE}"
echo "============================================================"