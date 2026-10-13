#!/usr/bin/env bash
# Reproduce the paper's CL-7B SVM+AST baseline and evaluate T=0.0 AGC.
#
# Inputs (read-only):
# - src/ml_embeddings/data_codesearchnet/splits/codellama-7b_4500_complexity_stratified_maxlen2048/
#     codesearchnet_codellama-7b_python_merged_4500/test_.csv
#     complexity_stratified_pair_manifest.csv
# - src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/
#     tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl
# - src/output/run-x-06/<RUN06_ID>/common_valid_pairs_full.csv, extraction_qc.csv, etc.
# - Original tree_sitter_ast_python.py and ml_embeddings/generate_embeddings.py.
#
# Outputs (ONLY under src/output/run-x-07/<RUN_ID>):
# - baseline and matched prediction CSVs, AUROC and bootstrap summaries,
#   preflight QC, AST consistency QC, embedding cache and provenance.
# - logs under src/logs/run-x-07/.
#
# No prior experiment shell script is called, and no classifier is refitted.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON="${PYTHON:-python}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
RUN06_ID="${RUN06_ID:-20261012-154334-48074}"
RUN06_DIR="${RUN06_DIR:-${REPO_ROOT}/src/output/run-x-06/${RUN06_ID}}"
OUTPUT_DIR="${OUTPUT_DIR:-${REPO_ROOT}/src/output/run-x-07/${RUN_ID}}"
LOG_DIR="${REPO_ROOT}/src/logs/run-x-07"
DRY_RUN="${DRY_RUN:-0}"
RESUME="${RESUME:-0}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
BATCH_SIZE="${BATCH_SIZE:-16}"
BOOTSTRAP="${BOOTSTRAP:-20000}"
SEED="${SEED:-20260723}"
DEVICE="${DEVICE:-cuda}"
ALLOW_BASELINE_DRIFT="${ALLOW_BASELINE_DRIFT:-0}"

if [[ "${DRY_RUN}" != "0" && "${DRY_RUN}" != "1" ]]; then echo "[ERROR] DRY_RUN must be 0/1" >&2; exit 2; fi
if [[ "${RESUME}" != "0" && "${RESUME}" != "1" ]]; then echo "[ERROR] RESUME must be 0/1" >&2; exit 2; fi
if [[ -e "${OUTPUT_DIR}" && "${RESUME}" != "1" ]]; then
  echo "[ERROR] Output exists; specify RESUME=1 RUN_ID=${RUN_ID} to reuse: ${OUTPUT_DIR}" >&2
  exit 2
fi
if [[ "${RESUME}" == "1" && ! -d "${OUTPUT_DIR}" ]]; then
  echo "[ERROR] Cannot resume a missing output directory: ${OUTPUT_DIR}" >&2; exit 2
fi
mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/run-x-07-${RUN_ID}.log"

if [[ "${DRY_RUN}" == "1" ]]; then PHASE="preflight"; else PHASE="run"; fi
FLAGS=()
if [[ "${RESUME}" == "1" ]]; then FLAGS+=(--resume); fi
if [[ "${ALLOW_BASELINE_DRIFT}" == "1" ]]; then FLAGS+=(--allow-baseline-drift); fi

{
  echo "================================================================="
  echo "run-x-07 | CL-7B SVM+AST original baseline + matched T=0.0 evaluation"
  echo "repo_root=${REPO_ROOT} run_id=${RUN_ID} phase=${PHASE}"
  echo "run06_dir=${RUN06_DIR}"
  echo "output_dir=${OUTPUT_DIR}"
  echo "python=${PYTHON} cuda_visible_devices=${CUDA_VISIBLE_DEVICES} device=${DEVICE}"
  echo "batch_size=${BATCH_SIZE} bootstrap=${BOOTSTRAP} seed=${SEED}"
  echo "source_inputs=READ_ONLY; model_retraining=NO; model_selection=NO"
  echo "================================================================="

  CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}" "${PYTHON}" \
    "${REPO_ROOT}/src/py/evaluate_cl7b_temperature.py" \
    --repo-root "${REPO_ROOT}" \
    --output-dir "${OUTPUT_DIR}" \
    --run06-dir "${RUN06_DIR}" \
    --phase "${PHASE}" \
    --embedding-max-len 2048 \
    --batch-size "${BATCH_SIZE}" \
    --device "${DEVICE}" \
    --bootstrap "${BOOTSTRAP}" \
    --seed "${SEED}" \
    "${FLAGS[@]}"
} 2>&1 | tee "${LOG_FILE}"

printf 'Saved outputs: %s\nSaved log: %s\n' "${OUTPUT_DIR}" "${LOG_FILE}"
