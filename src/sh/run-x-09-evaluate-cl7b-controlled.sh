#!/usr/bin/env bash
# =============================================================================
# run-x-09: Evaluate the original paper CL-7B SVM+AST detector on controlled
# CodeLlama-7B decoding-regime test outputs (T=0.0 greedy versus T=0.2 sample).
#
# Inputs (read-only):
#   src/output/run-x-06/<RUN06_ID>/   - verified T=0.0 reference/provenance
#   src/output/run-x-08/<RUN08_ID>/   - controlled T=0.2 test seeds, matched
#                                     HWC/AGC CSVs, extraction and warning QC
#   src/ml_embeddings/data_codesearchnet/splits/.../test_.csv
#                                   - original 450-pair CodeT5+ AST baseline
#   src/ml_embeddings/data_codesearchnet/models/.../*.pkl
#                                   - SHA-256-pinned pretrained SVM classifier
#   src/code-analyzer-tree-sitter/{tree_sitter_ast_python.py,build/my-languages.so}
#                                   - original AST representation and grammar
#   src/ml_embeddings/generate_embeddings.py
#                                   - original CodeT5+ encoder and batching
#
# Outputs (new files only, nothing written to input locations):
#   src/output/run-x-09/<RUN_ID>/preflight_summary.json
#   src/output/run-x-09/<RUN_ID>/baseline_predictions.csv
#   src/output/run-x-09/<RUN_ID>/ast_embeddings.npz
#   src/output/run-x-09/<RUN_ID>/seed<SEED>/paired_predictions.csv
#   src/output/run-x-09/<RUN_ID>/seed<SEED>/paired_metrics.csv
#   src/output/run-x-09/<RUN_ID>/seed<SEED>/bootstrap_replicates.csv
#   src/output/run-x-09/<RUN_ID>/evaluation_summary.json and findings.txt
#   src/logs/run-x-09/run-x-09-<RUN_ID>.log
#
# This wrapper copies and adapts the run-x-07 execution pattern but NEVER calls
# prior experiment wrappers. The existing fitted classifier is not retrained,
# the original benchmark split is not changed, and no generation is performed.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON="${PYTHON:-python}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
RUN06_ID="${RUN06_ID:-20261012-154334-48074}"
RUN08_ID="${RUN08_ID:-20261012-224115-68731}"
RUN06_DIR="${RUN06_DIR:-${REPO_ROOT}/src/output/run-x-06/${RUN06_ID}}"
RUN08_DIR="${RUN08_DIR:-${REPO_ROOT}/src/output/run-x-08/${RUN08_ID}}"
OUTPUT_DIR="${OUTPUT_DIR:-${REPO_ROOT}/src/output/run-x-09/${RUN_ID}}"
LOG_DIR="${REPO_ROOT}/src/logs/run-x-09"
DRY_RUN="${DRY_RUN:-0}"
RESUME="${RESUME:-0}"
SEEDS="${SEEDS:-20260723}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
BATCH_SIZE="${BATCH_SIZE:-16}"
BOOTSTRAP="${BOOTSTRAP:-20000}"
STAT_SEED="${STAT_SEED:-20260723}"
DEVICE="${DEVICE:-cuda}"

if [[ "${DRY_RUN}" != "0" && "${DRY_RUN}" != "1" ]]; then
  echo "[ERROR] DRY_RUN must be 0 or 1" >&2; exit 2
fi
if [[ "${RESUME}" != "0" && "${RESUME}" != "1" ]]; then
  echo "[ERROR] RESUME must be 0 or 1" >&2; exit 2
fi
if [[ "${DRY_RUN}" == "0" ]]; then
  if [[ -e "${OUTPUT_DIR}" && "${RESUME}" != "1" ]]; then
    echo "[ERROR] Output already exists. To resume, use RESUME=1 RUN_ID=${RUN_ID}" >&2; exit 2
  fi
  if [[ "${RESUME}" == "1" && ! -d "${OUTPUT_DIR}" ]]; then
    echo "[ERROR] Cannot resume missing output directory: ${OUTPUT_DIR}" >&2; exit 2
  fi
  mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}"
  PHASE="run"
else
  # Dry-run validates source metadata and paired samples without writing output.
  PHASE="preflight"
fi

ARGS=(
  --repo-root "${REPO_ROOT}"
  --output-dir "${OUTPUT_DIR}"
  --run06-dir "${RUN06_DIR}"
  --run08-dir "${RUN08_DIR}"
  --phase "${PHASE}"
  --seeds "${SEEDS}"
  --embedding-max-len 2048
  --batch-size "${BATCH_SIZE}"
  --device "${DEVICE}"
  --bootstrap "${BOOTSTRAP}"
  --seed "${STAT_SEED}"
)
if [[ "${RESUME}" == "1" ]]; then ARGS+=(--resume); fi

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "[DRY-RUN] Check historical SVM/hash, baseline 450 and controlled common-valid sets."
  CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}" "${PYTHON}" \
    "${REPO_ROOT}/src/py/evaluate_cl7b_controlled-v1.py" "${ARGS[@]}"
  exit 0
fi

LOG_FILE="${LOG_DIR}/run-x-09-${RUN_ID}.log"
{
  echo "================================================================="
  echo "run-x-09 | Controlled CL-7B/SVM+AST decoding robustness"
  echo "run_id=${RUN_ID} seeds=${SEEDS} repo_root=${REPO_ROOT}"
  echo "run06_dir=${RUN06_DIR} run08_dir=${RUN08_DIR}"
  echo "output_dir=${OUTPUT_DIR} resume=${RESUME}"
  echo "python=${PYTHON} cuda_visible_devices=${CUDA_VISIBLE_DEVICES} device=${DEVICE}"
  echo "batch_size=${BATCH_SIZE} bootstrap=${BOOTSTRAP} statistical_seed=${STAT_SEED}"
  echo "sources=READ_ONLY retraining=NO reselection=NO generation=NO"
  echo "================================================================="
  CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}" "${PYTHON}" \
    "${REPO_ROOT}/src/py/evaluate_cl7b_controlled-v1.py" "${ARGS[@]}"
} 2>&1 | tee "${LOG_FILE}"

printf 'Saved outputs: %s\nSaved log: %s\n' "${OUTPUT_DIR}" "${LOG_FILE}"
