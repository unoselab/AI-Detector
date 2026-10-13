#!/usr/bin/env bash
# =============================================================================
# run-x-10: Controlled CodeLlama-7B sampling at T=0.4 and T=0.6.
#
# INDEPENDENT WRAPPER. Adapted from a COPY of run-x-08's shell workflow;
# does not call or depend on any existing run-x-08 or run-x-06 shell wrapper.
# Its own versioned Python implementation is self-contained (except for
# the original read-only Python syntax validator and model weights).
#
# READ-ONLY INPUTS:
#   RUN06_DIR: audited T=0.0 full run, input prompts, complexity split,
#              extracted_functions, validator hash and GPU environment.
#   RUN08_DIR: audited T=0.2 generation for seed 20260723, including
#              test_prepared, generation, extraction, comparison and valid CSV.
#   VALIDATOR_PY: original Python validity checker; SHA-256 checked.
#   HF CodeLlama-7B model revision: checked against run-x-06 environment.
#
# OUTPUTS: under src/output/run-x-10/<RUN_ID>/, never overwrite sources.
#   Immutable 450-test input snapshot and provenance hashes;
#   seed<seed>_t04/t06_gpu0/gpu1_generation.jsonl append-only checkpoints;
#   per-temperature generated/extracted/valid-pair files;
#   seed<seed>_common_t02/t04/t06_pairs.csv (same common-valid test IDs);
#   seed<seed>_comparison.csv, multitemp_summary.json, multitemp_findings.txt.
#
# USAGE from ai_detector repository root:
#   DRY_RUN=1 bash src/sh/run-x-10-generate-cl7b-multitemp.sh
#   bash src/sh/run-x-10-generate-cl7b-multitemp.sh
#   RUN_ID=<existing> RESUME=1 bash src/sh/run-x-10-generate-cl7b-multitemp.sh
#   RUN_ID=<existing> FINALIZE_ONLY=1 bash src/sh/run-x-10-generate-cl7b-multitemp.sh
#
# Do not modify SEED: the reused run-x-08 T=0.2 data are seed 20260723.
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SRC_DIR}/.." && pwd)"
PYTHON="${PYTHON:-python}"
SCRIPT_PY="${SRC_DIR}/py/generate_cl7b_multitemp-v1.py"
RUN06_DIR="${RUN06_DIR:-${SRC_DIR}/output/run-x-06/20261012-154334-48074}"
RUN08_DIR="${RUN08_DIR:-${SRC_DIR}/output/run-x-08/20261012-224115-68731}"
VALIDATOR_PY="${VALIDATOR_PY:-${SRC_DIR}/code-generation/find_validsyntax_mgc.py}"
SEED="${SEED:-20260723}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${SRC_DIR}/output/run-x-10/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${SRC_DIR}/logs/run-x-10}"
GPU0_DEVICE="${GPU0_DEVICE:-0}"
GPU1_DEVICE="${GPU1_DEVICE:-1}"
DRY_RUN="${DRY_RUN:-0}"
RESUME="${RESUME:-0}"
FINALIZE_ONLY="${FINALIZE_ONLY:-0}"
PREPARE_ONLY="${PREPARE_ONLY:-0}"
MODEL_LOCAL_ONLY="${MODEL_LOCAL_ONLY:-0}"
MAIN_LOG="${LOG_DIR}/run-x-10-${RUN_ID}-main.log"

[[ "${SEED}" == "20260723" ]] || {
  echo '[ERROR] This version requires the existing T=0.2 reference seed=20260723' >&2; exit 2;
}
for required in "${SCRIPT_PY}" "${VALIDATOR_PY}" \
  "${RUN06_DIR}/experiment_config.json" "${RUN06_DIR}/input_manifest.json" \
  "${RUN06_DIR}/full_summary.json" "${RUN06_DIR}/full_prepared.jsonl" \
  "${RUN06_DIR}/extracted_functions.jsonl" "${RUN06_DIR}/extraction_qc.csv" \
  "${RUN06_DIR}/gpu0_environment.json" "${RUN06_DIR}/gpu1_environment.json" \
  "${RUN08_DIR}/experiment_config.json" "${RUN08_DIR}/input_manifest.json" \
  "${RUN08_DIR}/test_prepared.jsonl" "${RUN08_DIR}/seed${SEED}_summary.json" \
  "${RUN08_DIR}/seed${SEED}_generation.jsonl" \
  "${RUN08_DIR}/seed${SEED}_extracted_functions.jsonl" \
  "${RUN08_DIR}/seed${SEED}_comparison.csv" \
  "${RUN08_DIR}/seed${SEED}_t02_valid_pairs.csv"; do
  [[ -f "${required}" ]] || { echo "[ERROR] Missing read-only input: ${required}" >&2; exit 2; }
done
[[ "${GPU0_DEVICE}" != "${GPU1_DEVICE}" ]] || {
  echo '[ERROR] GPU0_DEVICE and GPU1_DEVICE must be different' >&2; exit 2;
}
COMMON=(--run06-dir "${RUN06_DIR}" --run08-dir "${RUN08_DIR}"
        --validator-script "${VALIDATOR_PY}" --out-dir "${OUT_DIR}" --seed "${SEED}")
if [[ "${DRY_RUN}" == "1" ]]; then
  echo '[DRY-RUN] Verify original 450 prompts, audited T=0.2 source and hashes (no GPU).'
  "${PYTHON}" -u "${SCRIPT_PY}" --phase prepare "${COMMON[@]}" --dry-run
  exit 0
fi
if [[ "${RESUME}" == "1" || "${FINALIZE_ONLY}" == "1" ]]; then
  [[ -f "${OUT_DIR}/experiment_config.json" ]] || {
    echo "[ERROR] RESUME/FINALIZE_ONLY needs existing RUN_ID=${RUN_ID}" >&2; exit 2;
  }
else
  [[ ! -e "${OUT_DIR}" ]] || {
    echo "[ERROR] Refusing to overwrite existing RUN_ID=${RUN_ID}" >&2; exit 2;
  }
fi
mkdir -p "${OUT_DIR}" "${LOG_DIR}"
{
  echo '================================================================='
  echo 'run-x-10 | CodeLlama-7B controlled sampling | T=0.4 and T=0.6'
  echo "run_id=${RUN_ID} repo_root=${REPO_ROOT} seed=${SEED}"
  echo 'model=codellama/CodeLlama-7b-hf do_sample=true top_p=0.95 top_k=50'
  echo 'EOS=[2] prompt_cap=128 max_new_tokens=512 test=450 per temperature'
  echo "gpu0_device=${GPU0_DEVICE} gpu1_device=${GPU1_DEVICE} assignments=225+225"
  echo "run06_dir=${RUN06_DIR} run08_dir=${RUN08_DIR}"
  echo "out_dir=${OUT_DIR} resume=${RESUME} finalize_only=${FINALIZE_ONLY}"
  echo 'original_sources=READ_ONLY reference_t02=READ_ONLY invalid_backfill=NO'
  echo '================================================================='
} | tee -a "${MAIN_LOG}"
PREPARE_ARGS=()
[[ "${RESUME}" == "1" ]] && PREPARE_ARGS+=(--resume)
WORKER_ARGS=()
[[ "${MODEL_LOCAL_ONLY}" == "1" ]] && WORKER_ARGS+=(--local-files-only)
if [[ "${FINALIZE_ONLY}" != "1" ]]; then
  "${PYTHON}" -u "${SCRIPT_PY}" --phase prepare "${COMMON[@]}" "${PREPARE_ARGS[@]}" \
    2>&1 | tee -a "${MAIN_LOG}"
fi
if [[ "${PREPARE_ONLY}" == "1" ]]; then
  echo "[PREPARE-ONLY] PASS; to resume use RUN_ID=${RUN_ID} RESUME=1"
  exit 0
fi
if [[ "${FINALIZE_ONLY}" != "1" ]]; then
  echo '[WORKERS] Starting GPU0 and GPU1 in parallel (two temperatures per GPU).' | tee -a "${MAIN_LOG}"
  (
    export CUDA_VISIBLE_DEVICES="${GPU0_DEVICE}"
    "${PYTHON}" -u "${SCRIPT_PY}" --phase worker --gpu-index 0 \
      "${COMMON[@]}" "${WORKER_ARGS[@]}" 2>&1 | sed -u 's/^/[GPU0] /' | \
      tee -a "${LOG_DIR}/run-x-10-${RUN_ID}-gpu0.log"
  ) &
  PID0=$!
  (
    export CUDA_VISIBLE_DEVICES="${GPU1_DEVICE}"
    "${PYTHON}" -u "${SCRIPT_PY}" --phase worker --gpu-index 1 \
      "${COMMON[@]}" "${WORKER_ARGS[@]}" 2>&1 | sed -u 's/^/[GPU1] /' | \
      tee -a "${LOG_DIR}/run-x-10-${RUN_ID}-gpu1.log"
  ) &
  PID1=$!
  trap 'kill "${PID0}" "${PID1}" 2>/dev/null || true' INT TERM
  STATUS0=0
  STATUS1=0
  wait "${PID0}" || STATUS0=$?
  wait "${PID1}" || STATUS1=$?
  trap - INT TERM
  if [[ "${STATUS0}" -ne 0 || "${STATUS1}" -ne 0 ]]; then
    echo "[ERROR] GPU worker failure gpu0=${STATUS0} gpu1=${STATUS1}" | tee -a "${MAIN_LOG}"
    echo "[ERROR] Resume using RUN_ID=${RUN_ID} RESUME=1" | tee -a "${MAIN_LOG}"
    exit 2
  fi
fi
"${PYTHON}" -u "${SCRIPT_PY}" --phase finalize "${COMMON[@]}" 2>&1 | tee -a "${MAIN_LOG}"
echo "[OUTPUT] ${OUT_DIR}" | tee -a "${MAIN_LOG}"
echo "[LOGS] ${LOG_DIR}/run-x-10-${RUN_ID}-*.log" | tee -a "${MAIN_LOG}"
