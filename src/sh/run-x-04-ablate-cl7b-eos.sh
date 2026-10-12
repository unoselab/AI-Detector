#!/usr/bin/env bash
# =============================================================================
# run-x-04-ablate-cl7b-eos.sh
# Independently runs a matched-prompt EOS ablation at fixed CodeLlama-7B T=0.0.
# Adapted from a COPY of run-x-02-generate-cl7b-t00-pilot.sh.
# It DOES NOT invoke run-x-02 or any other existing shell wrapper.
#
# READ-ONLY INPUTS:
#   - PILOT_DIR from the completed run-x-02 (100 matched prompts and A results)
#   - VALIDATOR_PY from existing src/code-generation (Python functions imported)
#   - Original model weights from Hugging Face cache / model repository
#   - Original 4,500-pair CSV and split manifest (hash verification only)
#
# ABLATION CONDITIONS (all T=0.0 / greedy / do_sample=False):
#   A: original [2,822,29871]; reuses stored run-x-02 generations (no rerun)
#   B: no-boundary [2,822]; newly generated and end-token ID recorded
#   C: standard EOS [2]; newly generated and end-token ID recorded
#
# OUTPUTS (created under OUT_DIR only):
#   experiment_config.json, ablation_generation.jsonl, ablation_qc.csv,
#   ablation_comparison.csv, last_token_counts.csv, ablation_summary.json,
#   ablation_findings.txt, model_environment.json
# LOGS (created under LOG_DIR only):
#   run-x-04-<RUN_ID>.log
#
# USAGE from repository root:
#   DRY_RUN=1 bash src/sh/run-x-04-ablate-cl7b-eos.sh
#   bash src/sh/run-x-04-ablate-cl7b-eos.sh
#   CUDA_VISIBLE_DEVICES=1 bash src/sh/run-x-04-ablate-cl7b-eos.sh
#   RUN_ID=<same-id> RESUME=1 bash src/sh/run-x-04-ablate-cl7b-eos.sh
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "${SRC_DIR}/.." && pwd)}"
PYTHON="${PYTHON:-python}"

# Default reference run ID is the successful pilot shared on 2026-10-12.
# Override PILOT_DIR when evaluating another original pilot.
PILOT_DIR="${PILOT_DIR:-${SRC_DIR}/output/run-x-02/20261012-140235-6379}"
VALIDATOR_PY="${VALIDATOR_PY:-${SRC_DIR}/code-generation/find_validsyntax_mgc.py}"
MODEL_NAME="${MODEL_NAME:-codellama/CodeLlama-7b-hf}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export CUDA_VISIBLE_DEVICES
MODEL_LOCAL_ONLY="${MODEL_LOCAL_ONLY:-0}"
DRY_RUN="${DRY_RUN:-0}"
RESUME="${RESUME:-0}"

RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${SRC_DIR}/output/run-x-04/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${SRC_DIR}/logs/run-x-04}"
LOG_FILE="${LOG_DIR}/run-x-04-${RUN_ID}.log"
SCRIPT_PY="${SRC_DIR}/py/ablate_cl7b_eos.py"

for path in "${SCRIPT_PY}" "${VALIDATOR_PY}" \
  "${PILOT_DIR}/experiment_config.json" \
  "${PILOT_DIR}/pilot_selection.csv" \
  "${PILOT_DIR}/pilot_prepared.jsonl" \
  "${PILOT_DIR}/pilot_generation.jsonl"; do
  if [[ ! -f "${path}" ]]; then
    echo "[ERROR] Missing required read-only input: ${path}" >&2
    exit 2
  fi
done
if [[ "${RESUME}" == "1" ]]; then
  if [[ ! -d "${OUT_DIR}" ]]; then
    echo "[ERROR] Resume directory does not exist: ${OUT_DIR}" >&2
    exit 2
  fi
else
  if [[ -e "${OUT_DIR}" || -e "${LOG_FILE}" ]]; then
    echo "[ERROR] Output/log exists; refusing overwrite for RUN_ID=${RUN_ID}" >&2
    exit 2
  fi
fi
mkdir -p "${OUT_DIR}" "${LOG_DIR}"

ARGS=()
if [[ "${DRY_RUN}" == "1" ]]; then ARGS+=(--dry-run); fi
if [[ "${RESUME}" == "1" ]]; then ARGS+=(--resume); fi
if [[ "${MODEL_LOCAL_ONLY}" == "1" ]]; then ARGS+=(--local-files-only); fi
if [[ "${RESUME}" == "1" ]]; then
  TEE_ARGS=(-a "${LOG_FILE}")
else
  TEE_ARGS=("${LOG_FILE}")
fi
{
  echo "================================================================="
  echo "run-x-04 | CodeLlama-7B T=0.0 EOS ablation"
  echo "repo_root=${REPO_ROOT}"
  echo "run_id=${RUN_ID}"
  echo "pilot_dir=${PILOT_DIR}"
  echo "validator=${VALIDATOR_PY}"
  echo "model=${MODEL_NAME} gpu_visible=${CUDA_VISIBLE_DEVICES}"
  echo "legacy=[2,822,29871] REUSE | no_boundary=[2,822] | standard=[2]"
  echo "do_sample=false temperature=not_passed top_p=not_passed"
  echo "out_dir=${OUT_DIR} dry_run=${DRY_RUN} resume=${RESUME}"
  echo "================================================================="
  "${PYTHON}" -u "${SCRIPT_PY}" \
    --pilot-dir "${PILOT_DIR}" \
    --validator-script "${VALIDATOR_PY}" \
    --output-dir "${OUT_DIR}" \
    --model-name "${MODEL_NAME}" \
    "${ARGS[@]}"
} 2>&1 | tee "${TEE_ARGS[@]}"
printf '\nSaved outputs: %s\nSaved log: %s\n' "${OUT_DIR}" "${LOG_FILE}"
