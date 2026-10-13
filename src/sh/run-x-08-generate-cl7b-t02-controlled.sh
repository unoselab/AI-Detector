#!/usr/bin/env bash
# =============================================================================
# run-x-08-generate-cl7b-t02-controlled.sh
# Independent two-GPU CONTROLLED T=0.2 CodeLlama-7B generation for the 450
# original test procedures. This wrapper was adapted from a COPY of the
# run-x-06 wrapper, NOT called from it. It invokes only its own v1 Python file.
#
# READ-ONLY INPUTS:
#   RUN06_DIR       - completed run-x-06/20261012-154334-48074 output; MUST
#                     contain full_prepared.jsonl, experiment_config.json,
#                     input_manifest.json, full_summary.json,
#                     extracted_functions.jsonl, extraction_qc.csv,
#                     gpu0_environment.json, gpu1_environment.json.
#                     The original benchmark/split paths come from its config.
#   VALIDATOR_PY    - src/code-generation/find_validsyntax_mgc.py; SHA checked.
#   Hugging Face weights for codellama/CodeLlama-7b-hf (read only).
#
# DECODING: T=0.2, do_sample=True, top_p=0.95, top_k=50, EOS ID [2],
#           prompt cap 128 tokens, max_new_tokens 512; per-procedure RNG seed.
#           Same EOS, prompt/truncation, continuation decoding and AST-boundary
#           extraction as run-x-06 (greedy baseline is reused, not regenerated).
#
# OUTPUTS (all under new OUT_DIR, never overwrite original run-x-06):
#   experiment_config.json, test_prepared.jsonl, test_selection.csv,
#   input_manifest.json, gpu[01]_environment.json,
#   seed<seed>_gpu[01]_generation.jsonl (append-only resumable checkpoints),
#   seed<seed>_generation.jsonl, seed<seed>_extracted_functions.jsonl,
#   seed<seed>_extraction_qc.csv, seed<seed>_comparison.csv,
#   seed<seed>_t02_valid_pairs.csv, seed<seed>_common_t0[02]_pairs.csv,
#   seed<seed>_summary.json, cross_seed_pair_qc.csv,
#   controlled_summary.json, controlled_findings.txt, runtime_environment.json.
#   GPU logs in src/logs/run-x-08/run-x-08-<RUN_ID>-{main,gpu0,gpu1}.log.
#
# USAGE from repository root:
#   DRY_RUN=1 bash src/sh/run-x-08-generate-cl7b-t02-controlled.sh
#   bash src/sh/run-x-08-generate-cl7b-t02-controlled.sh
#   RUN_ID=<same> RESUME=1 bash src/sh/run-x-08-generate-cl7b-t02-controlled.sh
#   RUN_ID=<same> FINALIZE_ONLY=1 bash src/sh/run-x-08-generate-cl7b-t02-controlled.sh
#   SEEDS=20260723,20260724,20260725 bash src/sh/run-x-08-generate-cl7b-t02-controlled.sh
#
# Default SEEDS is only 20260723. Verify first seed before running more seeds.
# Repeated seeds use a NEW run directory, not a partial change to an old run.
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SRC_DIR}/.." && pwd)"
PYTHON="${PYTHON:-python}"
SCRIPT_PY="${SRC_DIR}/py/generate_cl7b_t02_controlled-v1.py"
RUN06_DIR="${RUN06_DIR:-${SRC_DIR}/output/run-x-06/20261012-154334-48074}"
VALIDATOR_PY="${VALIDATOR_PY:-${SRC_DIR}/code-generation/find_validsyntax_mgc.py}"
SEEDS="${SEEDS:-20260723}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${SRC_DIR}/output/run-x-08/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${SRC_DIR}/logs/run-x-08}"
GPU0_DEVICE="${GPU0_DEVICE:-0}"
GPU1_DEVICE="${GPU1_DEVICE:-1}"
DRY_RUN="${DRY_RUN:-0}"
RESUME="${RESUME:-0}"
FINALIZE_ONLY="${FINALIZE_ONLY:-0}"
PREPARE_ONLY="${PREPARE_ONLY:-0}"
MODEL_LOCAL_ONLY="${MODEL_LOCAL_ONLY:-0}"
MAIN_LOG="${LOG_DIR}/run-x-08-${RUN_ID}-main.log"

for required in "${SCRIPT_PY}" "${VALIDATOR_PY}" \
  "${RUN06_DIR}/experiment_config.json" "${RUN06_DIR}/input_manifest.json" \
  "${RUN06_DIR}/full_summary.json" "${RUN06_DIR}/full_prepared.jsonl" \
  "${RUN06_DIR}/extracted_functions.jsonl" "${RUN06_DIR}/extraction_qc.csv" \
  "${RUN06_DIR}/gpu0_environment.json" "${RUN06_DIR}/gpu1_environment.json"; do
  if [[ ! -f "${required}" ]]; then
    echo "[ERROR] Missing read-only input: ${required}" >&2
    exit 2
  fi
done
if [[ "${GPU0_DEVICE}" == "${GPU1_DEVICE}" ]]; then
  echo "[ERROR] GPUs must be distinct physical devices" >&2
  exit 2
fi
COMMON=(--run06-dir "${RUN06_DIR}" --validator-script "${VALIDATOR_PY}"
        --out-dir "${OUT_DIR}" --seeds "${SEEDS}")
if [[ "${DRY_RUN}" == "1" ]]; then
  echo "[DRY-RUN] Verify run-x-06 provenance and all 450 original test prompts, without GPU inference."
  "${PYTHON}" -u "${SCRIPT_PY}" --phase prepare "${COMMON[@]}" --dry-run
  exit 0
fi
if [[ "${RESUME}" == "1" || "${FINALIZE_ONLY}" == "1" ]]; then
  [[ -f "${OUT_DIR}/experiment_config.json" ]] || {
    echo "[ERROR] RESUME/FINALIZE_ONLY requires existing RUN_ID=${RUN_ID}" >&2; exit 2; }
else
  [[ ! -e "${OUT_DIR}" ]] || {
    echo "[ERROR] Refusing to overwrite existing RUN_ID=${RUN_ID}" >&2; exit 2; }
fi
mkdir -p "${OUT_DIR}" "${LOG_DIR}"
{
  echo "================================================================="
  echo "run-x-08 | Controlled CodeLlama-7B T=0.2 original TEST 450"
  echo "repo_root=${REPO_ROOT} run_id=${RUN_ID} seeds=${SEEDS}"
  echo "model=codellama/CodeLlama-7b-hf temp=0.2 sample=true top_p=0.95 top_k=50"
  echo "EOS=[2] prompt_cap=128 max_new_tokens=512"
  echo "gpu0_device=${GPU0_DEVICE} gpu1_device=${GPU1_DEVICE} assignments=225+225"
  echo "run06_dir=${RUN06_DIR}"
  echo "out_dir=${OUT_DIR} resume=${RESUME} finalize_only=${FINALIZE_ONLY}"
  echo "original_inputs=READ_ONLY old_t00=READ_ONLY invalid_backfill=NO"
  echo "================================================================="
} | tee -a "${MAIN_LOG}"
PREPARE_ARGS=()
if [[ "${RESUME}" == "1" ]]; then PREPARE_ARGS+=(--resume); fi
WORKER_ARGS=()
if [[ "${MODEL_LOCAL_ONLY}" == "1" ]]; then WORKER_ARGS+=(--local-files-only); fi
if [[ "${FINALIZE_ONLY}" != "1" ]]; then
  "${PYTHON}" -u "${SCRIPT_PY}" --phase prepare "${COMMON[@]}" "${PREPARE_ARGS[@]}" \
    2>&1 | tee -a "${MAIN_LOG}"
fi
if [[ "${PREPARE_ONLY}" == "1" ]]; then
  echo "[PREPARE-ONLY] PASS; resume using RUN_ID=${RUN_ID} RESUME=1"
  exit 0
fi
if [[ "${FINALIZE_ONLY}" != "1" ]]; then
  echo "[WORKERS] Starting GPU0 and GPU1 concurrently..." | tee -a "${MAIN_LOG}"
  (
    export CUDA_VISIBLE_DEVICES="${GPU0_DEVICE}"
    "${PYTHON}" -u "${SCRIPT_PY}" --phase worker --gpu-index 0 \
      "${COMMON[@]}" "${WORKER_ARGS[@]}" 2>&1 | sed -u 's/^/[GPU0] /' | \
      tee -a "${LOG_DIR}/run-x-08-${RUN_ID}-gpu0.log"
  ) &
  PID0=$!
  (
    export CUDA_VISIBLE_DEVICES="${GPU1_DEVICE}"
    "${PYTHON}" -u "${SCRIPT_PY}" --phase worker --gpu-index 1 \
      "${COMMON[@]}" "${WORKER_ARGS[@]}" 2>&1 | sed -u 's/^/[GPU1] /' | \
      tee -a "${LOG_DIR}/run-x-08-${RUN_ID}-gpu1.log"
  ) &
  PID1=$!
  trap 'kill "${PID0}" "${PID1}" 2>/dev/null || true' INT TERM
  STATUS0=0
  STATUS1=0
  wait "${PID0}" || STATUS0=$?
  wait "${PID1}" || STATUS1=$?
  trap - INT TERM
  if [[ "${STATUS0}" -ne 0 || "${STATUS1}" -ne 0 ]]; then
    echo "[ERROR] GPU workers failed: gpu0=${STATUS0} gpu1=${STATUS1}" | tee -a "${MAIN_LOG}"
    echo "[ERROR] Resume with RUN_ID=${RUN_ID} RESUME=1" | tee -a "${MAIN_LOG}"
    exit 2
  fi
fi
"${PYTHON}" -u "${SCRIPT_PY}" --phase finalize "${COMMON[@]}" 2>&1 | tee -a "${MAIN_LOG}"
echo "[OUTPUT] ${OUT_DIR}" | tee -a "${MAIN_LOG}"
echo "[LOGS] ${LOG_DIR}/run-x-08-${RUN_ID}-*.log" | tee -a "${MAIN_LOG}"
