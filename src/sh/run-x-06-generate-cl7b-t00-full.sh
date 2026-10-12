#!/usr/bin/env bash
# =============================================================================
# run-x-06-generate-cl7b-t00-full.sh
# Independent full 4,500 matched-prompt CodeLlama-7B T=0.0 generation.
# Adapted from a COPY of run-x-04-ablate-cl7b-eos.sh; does NOT invoke any
# existing shell wrapper. The Python implementation includes a COPIED,
# independently maintained copy of the run-x-05 AST-boundary extraction logic.
#
# READ-ONLY INPUTS:
#   - ORIGINAL_PAIRS: existing 4,500 HWC/AGC pairs (idx,code,label).
#   - SPLIT_MANIFEST: 450 ten-pair complexity blocks; each 8 train/1 dev/1 test.
#   - PILOT_DIR, ABLATION_DIR, EXTRACTION_DIR: prior verified pilot metadata.
#   - VALIDATOR_PY: existing original Python syntax/structure validator.
#   - Hugging Face CodeLlama-7B weights + tokenizer (GPU inference only).
#
# OUTPUTS (new RUN_ID, never overwrite original data):
#   - full_prepared.jsonl, full_selection.csv, experiment_config.json
#   - gpu0_generation.jsonl, gpu1_generation.jsonl (append-only checkpoints)
#   - gpu0_environment.json, gpu1_environment.json
#   - generation_full.jsonl, extracted_functions.jsonl, extraction_qc.csv
#   - valid_pairs_full.csv, common_valid_pairs_full.csv
#   - generation_reference_qc.csv, full_summary.json, full_findings.txt
#   - logs/run-x-06/run-x-06-<RUN_ID>-{main,gpu0,gpu1}.log
#
# DECODING:  T=0.0 greedy; do_sample=False; EOS [2]; 128 prompt tokens,
#            max_new_tokens=512. Sampling-only arguments are NOT passed.
# DATA:     4,500 originals; GPU 0 gets even complexity blocks (2,250 IDs);
#           GPU 1 gets odd complexity blocks (2,250 IDs). No backfilling.
#
# USAGE (from the repository root):
#   DRY_RUN=1 bash src/sh/run-x-06-generate-cl7b-t00-full.sh
#   bash src/sh/run-x-06-generate-cl7b-t00-full.sh
#   RUN_ID=<id> RESUME=1 bash src/sh/run-x-06-generate-cl7b-t00-full.sh
#   RUN_ID=<id> FINALIZE_ONLY=1 bash src/sh/run-x-06-generate-cl7b-t00-full.sh
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "${SRC_DIR}/.." && pwd)}"
PYTHON="${PYTHON:-python}"
SCRIPT_PY="${SRC_DIR}/py/generate_cl7b_t00_full.py"
ORIGINAL_PAIRS="${ORIGINAL_PAIRS:-${SRC_DIR}/code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/validsyntax_4500_complexity/codesearchnet_codellama-7b_python_merged_4500.csv}"
SPLIT_MANIFEST="${SPLIT_MANIFEST:-${SRC_DIR}/ml_embeddings/data_codesearchnet/splits/codellama-7b_4500_complexity_stratified_maxlen2048/complexity_stratified_pair_manifest.csv}"
VALIDATOR_PY="${VALIDATOR_PY:-${SRC_DIR}/code-generation/find_validsyntax_mgc.py}"
PILOT_DIR="${PILOT_DIR:-${SRC_DIR}/output/run-x-02/20261012-140235-6379}"
ABLATION_DIR="${ABLATION_DIR:-${SRC_DIR}/output/run-x-04/20261012-143925-17683}"
EXTRACTION_DIR="${EXTRACTION_DIR:-${SRC_DIR}/output/run-x-05/20261012-152937-41999}"
MODEL_NAME="codellama/CodeLlama-7b-hf"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${SRC_DIR}/output/run-x-06/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${SRC_DIR}/logs/run-x-06}"
DRY_RUN="${DRY_RUN:-0}"
RESUME="${RESUME:-0}"
FINALIZE_ONLY="${FINALIZE_ONLY:-0}"
PREPARE_ONLY="${PREPARE_ONLY:-0}"
MODEL_LOCAL_ONLY="${MODEL_LOCAL_ONLY:-0}"
GPU0_DEVICE="${GPU0_DEVICE:-0}"
GPU1_DEVICE="${GPU1_DEVICE:-1}"
MAIN_LOG="${LOG_DIR}/run-x-06-${RUN_ID}-main.log"

for required in "${SCRIPT_PY}" "${ORIGINAL_PAIRS}" "${SPLIT_MANIFEST}" "${VALIDATOR_PY}" \
  "${PILOT_DIR}/experiment_config.json" "${PILOT_DIR}/pilot_prepared.jsonl" \
  "${ABLATION_DIR}/experiment_config.json" "${ABLATION_DIR}/ablation_generation.jsonl" \
  "${EXTRACTION_DIR}/extraction_summary.json"; do
  if [[ ! -f "${required}" ]]; then
    echo "[ERROR] Missing read-only input: ${required}" >&2
    exit 2
  fi
done
if [[ "${GPU0_DEVICE}" == "${GPU1_DEVICE}" ]]; then
  echo "[ERROR] GPU devices must be distinct" >&2
  exit 2
fi
if [[ "${DRY_RUN}" != "1" ]]; then
  if [[ "${RESUME}" == "1" || "${FINALIZE_ONLY}" == "1" ]]; then
    [[ -f "${OUT_DIR}/experiment_config.json" ]] || {
      echo "[ERROR] Missing original run for resume/finalize: ${OUT_DIR}" >&2; exit 2; }
  else
    [[ ! -e "${OUT_DIR}" ]] || {
      echo "[ERROR] Refusing to overwrite existing RUN_ID: ${RUN_ID}" >&2; exit 2; }
  fi
  mkdir -p "${OUT_DIR}" "${LOG_DIR}"
fi

COMMON=(--original-pairs "${ORIGINAL_PAIRS}" --split-manifest "${SPLIT_MANIFEST}"
  --validator-script "${VALIDATOR_PY}" --pilot-dir "${PILOT_DIR}"
  --ablation-dir "${ABLATION_DIR}" --extraction-dir "${EXTRACTION_DIR}"
  --out-dir "${OUT_DIR}" --model-name "${MODEL_NAME}")
PREPARE_ARGS=()
if [[ "${RESUME}" == "1" ]]; then PREPARE_ARGS+=(--resume); fi
if [[ "${DRY_RUN}" == "1" ]]; then PREPARE_ARGS+=(--dry-run); fi
WORKER_ARGS=()
if [[ "${MODEL_LOCAL_ONLY}" == "1" ]]; then WORKER_ARGS+=(--local-files-only); fi

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "[DRY-RUN] Python 3.11, all 4,500 prompts and pilot provenance will be checked."
  "${PYTHON}" -u "${SCRIPT_PY}" --phase prepare "${COMMON[@]}" --dry-run
  exit 0
fi

{
  echo "================================================================="
  echo "run-x-06 | Full 4,500 CodeLlama-7B T=0.0 Standard-EOS generation"
  echo "run_id=${RUN_ID} repo_root=${REPO_ROOT}"
  echo "model=${MODEL_NAME} EOS=[2] do_sample=false prompt_cap=128 max_new_tokens=512"
  echo "gpu0_device=${GPU0_DEVICE} gpu1_device=${GPU1_DEVICE}"
  echo "output_dir=${OUT_DIR} resume=${RESUME} prepare_only=${PREPARE_ONLY} finalize_only=${FINALIZE_ONLY}"
  echo "source_inputs=READ_ONLY invalid_backfill=NO"
  echo "================================================================="
} | tee -a "${MAIN_LOG}"

if [[ "${FINALIZE_ONLY}" != "1" ]]; then
  "${PYTHON}" -u "${SCRIPT_PY}" --phase prepare "${COMMON[@]}" "${PREPARE_ARGS[@]}" \
    2>&1 | tee -a "${MAIN_LOG}"
fi
if [[ "${PREPARE_ONLY}" == "1" ]]; then
  echo "[PREPARE-ONLY] PASS; run with RUN_ID=${RUN_ID} RESUME=1 to generate."
  exit 0
fi
if [[ "${FINALIZE_ONLY}" != "1" ]]; then
  echo "[WORKERS] Starting two independent GPU workers in parallel..." | tee -a "${MAIN_LOG}"
  (
    export CUDA_VISIBLE_DEVICES="${GPU0_DEVICE}"
    "${PYTHON}" -u "${SCRIPT_PY}" --phase worker --gpu-index 0 "${COMMON[@]}" "${WORKER_ARGS[@]}" \
      2>&1 | sed -u 's/^/[GPU0] /' | tee -a "${LOG_DIR}/run-x-06-${RUN_ID}-gpu0.log"
  ) &
  PID0=$!
  (
    export CUDA_VISIBLE_DEVICES="${GPU1_DEVICE}"
    "${PYTHON}" -u "${SCRIPT_PY}" --phase worker --gpu-index 1 "${COMMON[@]}" "${WORKER_ARGS[@]}" \
      2>&1 | sed -u 's/^/[GPU1] /' | tee -a "${LOG_DIR}/run-x-06-${RUN_ID}-gpu1.log"
  ) &
  PID1=$!
  trap 'kill "${PID0}" "${PID1}" 2>/dev/null || true' INT TERM
  STATUS0=0
  STATUS1=0
  wait "${PID0}" || STATUS0=$?
  wait "${PID1}" || STATUS1=$?
  trap - INT TERM
  if [[ "${STATUS0}" -ne 0 || "${STATUS1}" -ne 0 ]]; then
    echo "[ERROR] GPU workers: gpu0=${STATUS0} gpu1=${STATUS1}." | tee -a "${MAIN_LOG}"
    echo "[ERROR] Restart with RUN_ID=${RUN_ID} RESUME=1 to continue checkpoints." | tee -a "${MAIN_LOG}"
    exit 2
  fi
fi

"${PYTHON}" -u "${SCRIPT_PY}" --phase finalize "${COMMON[@]}" 2>&1 | tee -a "${MAIN_LOG}"
echo "Saved outputs: ${OUT_DIR}" | tee -a "${MAIN_LOG}"
echo "Logs: ${LOG_DIR}/run-x-06-${RUN_ID}-*.log" | tee -a "${MAIN_LOG}"
