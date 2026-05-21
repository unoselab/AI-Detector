#!/usr/bin/env bash
# =============================================================================
# run3-split-data.sh
# -----------------------------------------------------------------------------
# Driver script for the stratified train/dev/test split stage.
#
# Reference paper:
#   Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
#   Source Code: How Far Are We?", ICSE 2025, Section IV.D.
#   "We split each dataset into 80% training, 10% validation, and 10% testing
#    sets" (stratified on label).
#
# What this script does
#   Wraps src/ml_embeddings/split_data.py and runs it once per mode requested.
#   For each embedding-augmented CSV produced by run2-generate-embeddings.sh,
#   produces three files in a per-dataset folder:
#       <dataset_name>/
#           train_.csv   (80%)
#           dev_.csv     (10%)
#           test_.csv    (10%)
#
# Modes (input source -> output source)
#   baseline                -> splits the baseline embeddings (RQ2-D).
#   uniform_variables_name  -> splits the RQ3 ablation embeddings.
#   uniform_methods_name    -> idem.
#   no_comments             -> idem.
#
# Outputs (under src/ml_embeddings/)
#   - baseline               -> splits/
#   - uniform_variables_name -> splits_ablation/uniform_variables_name/
#   - uniform_methods_name   -> splits_ablation/uniform_methods_name/
#   - no_comments            -> splits_ablation/no_comments/
#
# Prerequisites
#   1. run2-generate-embeddings.sh has already produced the matching mode.
#   2. conda env active with pandas, scikit-learn.
#
# Usage
#   From repository root:
#     bash src/run3-split-data.sh                       # default: baseline
#     bash src/run3-split-data.sh all                   # baseline + ablations
#     bash src/run3-split-data.sh ablations             # only ablations
#     bash src/run3-split-data.sh baseline no_comments
#
# Customization (via env vars)
#   EMB_BASELINE_DIR   - where baseline embedding CSVs live
#   EMB_ABLATION_ROOT  - where ablation embedding subfolders live
#   OUT_BASELINE       - where baseline-mode splits go
#   OUT_ABLATION_ROOT  - where ablation-mode splits go
#   SEED               - RNG seed (default 42)
#   TRAIN_FRAC / DEV_FRAC / TEST_FRAC - override split fractions (must sum to 1)
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Path resolution
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

# Embedding CSVs from run2-generate-embeddings.sh
# EMB_BASELINE_DIR="${EMB_BASELINE_DIR:-data_main_with_embeddings}"   # Original path.
EMB_BASELINE_DIR="${EMB_BASELINE_DIR:-data_codesearchnet/embeddings}" # CodeSearchNet corpus.
EMB_ABLATION_ROOT="${EMB_ABLATION_ROOT:-data_ablation_with_embeddings}"

# Split outputs
# OUT_BASELINE="${OUT_BASELINE:-splits}"                  # Orginal path.
OUT_BASELINE="${OUT_BASELINE:-data_codesearchnet/splits}" # CodeSearchNet corpus. 
GROUP_BY_PAIR_ID="${GROUP_BY_PAIR_ID:-1}"
OUT_ABLATION_ROOT="${OUT_ABLATION_ROOT:-splits_ablation}"

# Hyperparameters
SEED="${SEED:-42}"
TRAIN_FRAC="${TRAIN_FRAC:-0.80}"
DEV_FRAC="${DEV_FRAC:-0.10}"
TEST_FRAC="${TEST_FRAC:-0.10}"

PYTHON="${PYTHON:-python}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run3-split-data_${TS}.log}"

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
    baseline)               echo "${EMB_BASELINE_DIR}" ;;
    uniform_variables_name) echo "${EMB_ABLATION_ROOT}/uniform_variables_name" ;;
    uniform_methods_name)   echo "${EMB_ABLATION_ROOT}/uniform_methods_name" ;;
    no_comments)            echo "${EMB_ABLATION_ROOT}/no_comments" ;;
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

GROUP_ARG=()
if [ "${GROUP_BY_PAIR_ID}" = "1" ]; then
  GROUP_ARG=(--group-by-pair-id)
fi

# -----------------------------------------------------------------------------
# Pre-flight
# -----------------------------------------------------------------------------
if [ ! -d "${TARGET_DIR}" ]; then
  echo "[ERROR] TARGET_DIR does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

cd "${TARGET_DIR}"

if [ ! -f "split_data.py" ]; then
  echo "[ERROR] split_data.py not found in ${TARGET_DIR}" >&2
  exit 1
fi

for mode in "${MODES[@]}"; do
  in_dir="$(input_for_mode "${mode}")"
  if [ ! -d "${in_dir}" ] || [ -z "$(ls -A "${in_dir}" 2>/dev/null)" ]; then
    echo "[ERROR] Embedding input for mode '${mode}' missing or empty: ${in_dir}" >&2
    echo "        Run run2-generate-embeddings.sh ${mode} first." >&2
    exit 1
  fi
done

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
echo "============================================================"
echo " run3-split-data.sh"
echo "   target dir : ${TARGET_DIR}"
echo "   fractions  : train=${TRAIN_FRAC}  dev=${DEV_FRAC}  test=${TEST_FRAC}"
echo "   seed       : ${SEED}"
echo "   grouped    : ${GROUP_BY_PAIR_ID}"
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
  "${PYTHON}" split_data.py \
    --input-dir  "${in_dir}" \
    --output-dir "${out_dir}" \
    --train-frac "${TRAIN_FRAC}" \
    --dev-frac   "${DEV_FRAC}" \
    --test-frac  "${TEST_FRAC}" \
    --seed       "${SEED}" \
    "${GROUP_ARG[@]}"
done

echo
echo "============================================================"
echo " Done. Summary of outputs:"
for mode in "${MODES[@]}"; do
  out_dir="$(output_for_mode "${mode}")"
  count=$(find "${out_dir}" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
  printf "   %-26s -> %3d dataset folder(s) in %s\n" "${mode}" "${count}" "${out_dir}"
done
echo "============================================================"

echo
echo "Finished: $(date -Is)"
echo "Log file: ${LOG_FILE}"


