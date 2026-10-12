#!/usr/bin/env bash
# =============================================================================
# run-x-02-generate-cl7b-t00-pilot.sh
# Independent T=0.0 (greedy) CodeLlama-7B generation pilot.
#
# Adapted from the parameter-passing / logging / validation pattern of
# src/run0a-generate-more.sh. Does not invoke the original shell wrapper.
#
# Read-only inputs:
#   - Original 4,500-pair CodeLlama-7B complexity-balanced HWC/AGC CSV
#   - Original 4,500-pair complexity-stratified split manifest
#   - Existing find_validsyntax_mgc.py (reused by the Python implementation)
#   - Hugging Face CodeLlama-7B weights (read through transformers)
#
# New outputs ONLY:
#   src/output/run-x-02/<RUN_ID>/   (selection, raw generations, QC, pairs)
#   src/logs/run-x-02/             (console log)
#
# Usage from repository root:
#   DRY_RUN=1 bash src/sh/run-x-02-generate-cl7b-t00-pilot.sh
#   bash src/sh/run-x-02-generate-cl7b-t00-pilot.sh
#   CUDA_VISIBLE_DEVICES=1 bash src/sh/run-x-02-generate-cl7b-t00-pilot.sh
#   RUN_ID=<existing_id> RESUME=1 bash src/sh/run-x-02-generate-cl7b-t00-pilot.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "${SRC_DIR}/.." && pwd)}"
PYTHON="${PYTHON:-python}"

# Existing experiment inputs. Paths can be overridden for a mirrored workspace.
EXPERIMENT="codellama-7b_4500_complexity_stratified_maxlen2048"
ORIGINAL_PAIRS="${ORIGINAL_PAIRS:-${SRC_DIR}/code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/validsyntax_4500_complexity/codesearchnet_codellama-7b_python_merged_4500.csv}"
SPLIT_MANIFEST="${SPLIT_MANIFEST:-${SRC_DIR}/ml_embeddings/data_codesearchnet/splits/${EXPERIMENT}/complexity_stratified_pair_manifest.csv}"
VALIDATOR_PY="${VALIDATOR_PY:-${SRC_DIR}/code-generation/find_validsyntax_mgc.py}"

# Generation parameters: T=0.0 is GREEDY decoding (do_sample=False).
# Do not pass temperature=0.0 or top_p to model.generate(): sampling is OFF.
MODEL_NAME="${MODEL_NAME:-codellama/CodeLlama-7b-hf}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export CUDA_VISIBLE_DEVICES
PROMPT_MAX_TOKENS="${PROMPT_MAX_TOKENS:-128}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-512}"
PILOT_PAIRS="${PILOT_PAIRS:-100}"
PILOT_SEED="${PILOT_SEED:-42}"
MIN_VALID_RATE="${MIN_VALID_RATE:-0.70}"
MODEL_LOCAL_ONLY="${MODEL_LOCAL_ONLY:-0}"
DRY_RUN="${DRY_RUN:-0}"
RESUME="${RESUME:-0}"

# Unique, non-overwriting output/log directories. RESUME requires the same RUN_ID.
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${SRC_DIR}/output/run-x-02/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${SRC_DIR}/logs/run-x-02}"
LOG_FILE="${LOG_DIR}/run-x-02-${RUN_ID}.log"

if [[ ! -f "${SRC_DIR}/py/generate_cl7b_t00_pilot.py" ]]; then
  echo "[ERROR] Missing Python implementation: ${SRC_DIR}/py/generate_cl7b_t00_pilot.py" >&2
  exit 2
fi
for input in "${ORIGINAL_PAIRS}" "${SPLIT_MANIFEST}" "${VALIDATOR_PY}"; do
  if [[ ! -f "${input}" ]]; then
    echo "[ERROR] Missing required input: ${input}" >&2
    exit 2
  fi
done
if [[ "${RESUME}" == "1" ]]; then
  if [[ ! -d "${OUT_DIR}" ]]; then
    echo "[ERROR] Resume output directory missing: ${OUT_DIR}" >&2
    exit 2
  fi
else
  if [[ -e "${OUT_DIR}" || -e "${LOG_FILE}" ]]; then
    echo "[ERROR] Existing output or log for RUN_ID=${RUN_ID}; refusing overwrite" >&2
    exit 2
  fi
fi
mkdir -p "${OUT_DIR}" "${LOG_DIR}"

EXTRA_ARGS=()
if [[ "${DRY_RUN}" == "1" ]]; then
  EXTRA_ARGS+=(--dry-run)
fi
if [[ "${RESUME}" == "1" ]]; then
  EXTRA_ARGS+=(--resume)
fi
if [[ "${MODEL_LOCAL_ONLY}" == "1" ]]; then
  EXTRA_ARGS+=(--local-files-only)
fi

# tee -a in resume mode; tee on a fresh run creates a new log file.
if [[ "${RESUME}" == "1" ]]; then
  TEE_ARGS=(-a "${LOG_FILE}")
else
  TEE_ARGS=("${LOG_FILE}")
fi
{
  echo "================================================================="
  echo "run-x-02 | CodeLlama-7B temperature=0.0 pilot"
  echo "run_id=${RUN_ID}"
  echo "repo_root=${REPO_ROOT}"
  echo "original_pairs=${ORIGINAL_PAIRS}"
  echo "split_manifest=${SPLIT_MANIFEST}"
  echo "model=${MODEL_NAME} gpu_visible=${CUDA_VISIBLE_DEVICES}"
  echo "decoding=greedy do_sample=false temperature=not_passed top_p=not_passed"
  echo "pilot_pairs=${PILOT_PAIRS} selection_seed=${PILOT_SEED}"
  echo "prompt_max_tokens=${PROMPT_MAX_TOKENS} max_new_tokens=${MAX_NEW_TOKENS}"
  echo "out_dir=${OUT_DIR} dry_run=${DRY_RUN} resume=${RESUME}"
  echo "================================================================="
  "${PYTHON}" -u "${SRC_DIR}/py/generate_cl7b_t00_pilot.py" \
    --original-pairs "${ORIGINAL_PAIRS}" \
    --split-manifest "${SPLIT_MANIFEST}" \
    --validator-script "${VALIDATOR_PY}" \
    --output-dir "${OUT_DIR}" \
    --model-name "${MODEL_NAME}" \
    --pilot-pairs "${PILOT_PAIRS}" \
    --seed "${PILOT_SEED}" \
    --prompt-max-tokens "${PROMPT_MAX_TOKENS}" \
    --max-new-tokens "${MAX_NEW_TOKENS}" \
    --min-valid-rate "${MIN_VALID_RATE}" \
    "${EXTRA_ARGS[@]}"
} 2>&1 | tee "${TEE_ARGS[@]}"
printf '\nSaved outputs: %s\nSaved log: %s\n' "${OUT_DIR}" "${LOG_FILE}"
