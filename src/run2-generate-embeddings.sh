#!/usr/bin/env bash
# =============================================================================
# run2-generate-embeddings.sh
# -----------------------------------------------------------------------------
# Driver script for the CodeT5+ embedding stage of the AI-Detector replication.
#
# Reference paper:
#   Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
#   Source Code: How Far Are We?", ICSE 2025, Section IV.D (RQ2).
#
# What this script does
#   Wraps src/ml_embeddings/generate_embeddings.py and runs it once per mode
#   requested. For each input AST CSV (one per dataset/LLM/language combo),
#   the wrapped script produces three 256-dim embeddings using
#   Salesforce/codet5p-110m-embedding:
#       - Code Only
#       - AST Only
#       - Code + AST (concatenation)
#   and writes a wide CSV with columns code_0..255, ast_0..255,
#   combined_0..255, plus an integer `actual label` column
#   (1 = human, 0 = AI).
#
# Modes (input source -> output source)
#   baseline                -> RQ2-D. Reads data_main/ (no transformation).
#   uniform_variables_name  -> RQ3 ablation. Reads
#                              data_ablation_study_code_embedding/uniform_variables_name/
#   uniform_methods_name    -> RQ3 ablation.
#   no_comments             -> RQ3 ablation.
#
# Outputs
#   - baseline               -> ml_embeddings/data_main_with_embeddings/
#   - uniform_variables_name -> ml_embeddings/data_ablation_with_embeddings/uniform_variables_name/
#   - uniform_methods_name   -> ml_embeddings/data_ablation_with_embeddings/uniform_methods_name/
#   - no_comments            -> ml_embeddings/data_ablation_with_embeddings/no_comments/
#
# Prerequisites
#   1. conda env active with transformers, torch, tqdm, pandas, numpy
#      (see requirements.txt; tested with transformers==4.36.2 + Python 3.11).
#   2. run1-ast-generator.sh has already produced the corresponding AST CSVs.
#   3. Internet access on first run (downloads ~440MB CodeT5+ checkpoint).
#   4. GPU recommended -- 110M params on CUDA is ~10x faster than CPU.
#
# Usage
#   From repository root:
#     bash src/run2-generate-embeddings.sh                # default: baseline
#     bash src/run2-generate-embeddings.sh all            # baseline + ablations
#     bash src/run2-generate-embeddings.sh ablations      # only ablations
#     bash src/run2-generate-embeddings.sh baseline uniform_variables_name
#
# Customization (via env vars)
#   AST_BASELINE_DIR   - where baseline AST CSVs live
#   AST_ABLATION_ROOT  - where ablation AST CSV subfolders live
#   OUT_BASELINE       - where baseline-mode embeddings go
#   OUT_ABLATION_ROOT  - where ablation-mode embedding subfolders go
#   BATCH_SIZE         - tokenizer/model batch size (default 32)
#   MAX_LEN            - tokenizer max_length for CodeT5+ inputs (default 512)
#   DEVICE             - cuda | cuda:0 | cpu (default: auto-detect)
#   OVERWRITE=1        - re-embed even if output CSV exists
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Path resolution
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# generate_embeddings.py is expected at src/ml_embeddings/generate_embeddings.py
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

# The AST CSVs produced by run1-ast-generator.sh live under
MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
# AST_BASELINE_DIR="${AST_BASELINE_DIR:-${SCRIPT_DIR}/code-analyzer-tree-sitter/data_main}" # Original path.
AST_BASELINE_DIR="${AST_BASELINE_DIR:-${SCRIPT_DIR}/code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/ast}" # CodeSearchNet corpus.
AST_ABLATION_ROOT="${AST_ABLATION_ROOT:-${SCRIPT_DIR}/code-analyzer-tree-sitter/data_ablation_study_code_embedding}"

# Embedding output locations (relative to TARGET_DIR after the cd).
# OUT_BASELINE="${OUT_BASELINE:-data_main_with_embeddings}"   # Original path.
OUT_BASELINE="${OUT_BASELINE:-data_codesearchnet/embeddings/${MODEL_NAME}_maxlen2048_baseline}" # CodeSearchNet corpus, max-len experiment.
OUT_ABLATION_ROOT="${OUT_ABLATION_ROOT:-data_ablation_with_embeddings}"

BATCH_SIZE="${BATCH_SIZE:-32}"
MAX_LEN="${MAX_LEN:-2048}"
OVERWRITE="${OVERWRITE:-1}"
PYTHON="${PYTHON:-python}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run2-generate-embeddings_${TS}.log}"

mkdir -p "${LOG_DIR}"

# Log everything to both terminal and timestamped log file.
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "Log file: ${LOG_FILE}"
echo "Started : $(date -Is)"
echo

# -----------------------------------------------------------------------------
# Mode selection
# -----------------------------------------------------------------------------
ALL_MODES=(baseline uniform_variables_name uniform_methods_name no_comments)
ABLATION_MODES=(uniform_variables_name uniform_methods_name no_comments)

if [ "$#" -eq 0 ]; then
  MODES=(baseline)
else
  case "$1" in
    all)       MODES=("${ALL_MODES[@]}") ;;
    ablations) MODES=("${ABLATION_MODES[@]}") ;;
    *)         MODES=("$@") ;;
  esac
fi

# -----------------------------------------------------------------------------
# Per-mode I/O mapping
# -----------------------------------------------------------------------------
input_for_mode() {
  case "$1" in
    baseline)               echo "${AST_BASELINE_DIR}" ;;
    uniform_variables_name) echo "${AST_ABLATION_ROOT}/uniform_variables_name" ;;
    uniform_methods_name)   echo "${AST_ABLATION_ROOT}/uniform_methods_name" ;;
    no_comments)            echo "${AST_ABLATION_ROOT}/no_comments" ;;
    *) echo "[ERROR] unknown mode: $1" >&2; exit 2 ;;
  esac
}

output_for_mode() {
  case "$1" in
    baseline)               echo "${OUT_BASELINE}" ;;
    uniform_variables_name) echo "${OUT_ABLATION_ROOT}/uniform_variables_name" ;;
    uniform_methods_name)   echo "${OUT_ABLATION_ROOT}/uniform_methods_name" ;;
    no_comments)            echo "${OUT_ABLATION_ROOT}/no_comments" ;;
  esac
}

# -----------------------------------------------------------------------------
# Pre-flight checks
# -----------------------------------------------------------------------------
if [ ! -d "${TARGET_DIR}" ]; then
  echo "[ERROR] TARGET_DIR does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

cd "${TARGET_DIR}"

if [ ! -f "generate_embeddings.py" ]; then
  echo "[ERROR] generate_embeddings.py not found in ${TARGET_DIR}" >&2
  exit 1
fi

for mode in "${MODES[@]}"; do
  in_dir="$(input_for_mode "${mode}")"
  if [ ! -d "${in_dir}" ] || [ -z "$(ls -A "${in_dir}" 2>/dev/null)" ]; then
    echo "[ERROR] AST input for mode '${mode}' missing or empty: ${in_dir}" >&2
    echo "        Run run1-ast-generator.sh ${mode} first." >&2
    exit 1
  fi
done

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
DEVICE_ARG=()
if [ -n "${DEVICE:-}" ]; then
  DEVICE_ARG=(--device "${DEVICE}")
fi

OVERWRITE_ARG=()
if [ "${OVERWRITE:-0}" = "1" ]; then
  OVERWRITE_ARG=(--overwrite)
fi

echo "============================================================"
echo " run2-generate-embeddings.sh"
echo "   target dir : ${TARGET_DIR}"
echo "   model name : ${MODEL_NAME}"
echo "   batch size : ${BATCH_SIZE}"
echo "   device     : ${DEVICE:-auto}"
echo "   max len    : ${MAX_LEN}"
echo "   modes      : ${MODES[*]}"
echo "============================================================"

for mode in "${MODES[@]}"; do
  in_dir="$(input_for_mode "${mode}")"
  out_dir="$(output_for_mode "${mode}")"
  echo
  echo "------------------------------------------------------------"
  echo " mode       : ${mode}"
  echo " input dir  : ${in_dir}"
  echo " output dir : ${out_dir}"
  echo "------------------------------------------------------------"
  "${PYTHON}" generate_embeddings.py \
    --input-dir  "${in_dir}" \
    --output-dir "${out_dir}" \
    --batch-size "${BATCH_SIZE}" \
    --max-len    "${MAX_LEN}" \
    "${DEVICE_ARG[@]}" \
    "${OVERWRITE_ARG[@]}"
done

echo
echo "============================================================"
echo " Done. Summary of outputs:"
for mode in "${MODES[@]}"; do
  out_dir="$(output_for_mode "${mode}")"
  count=$(find "${out_dir}" -name '*.csv' 2>/dev/null | wc -l)
  printf "   %-26s -> %3d CSV(s) in %s\n" "${mode}" "${count}" "${out_dir}"
done
echo "============================================================"


echo
echo "Finished: $(date -Is)"
echo "Log file: ${LOG_FILE}"

