#!/usr/bin/env bash
# =============================================================================
# run4-train-classifiers.sh
# -----------------------------------------------------------------------------
# Driver script for the ML-classifier tuning + evaluation stage.
#
# Reference paper:
#   Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
#   Source Code: How Far Are We?", ICSE 2025, Section IV.D (RQ2).
#
# What this script does
#   Sequentially invokes the two stages of RQ2-D ML evaluation:
#     1. hyperparameter_tuning.py : random hyperparameter search with CV on
#        the train split. Produces a pickle of tuned estimators, one per
#        (dataset, embedding_type) pair.
#     2. test_embedding.py        : refits each tuned estimator on its train
#        split, predicts on the held-out test split, prints metrics, and
#        writes per-(dataset, embedding) prediction CSVs.
#
# Modes (input source -> output source)
#   baseline                -> evaluates on splits/ (default).
#   uniform_variables_name  -> evaluates the RQ3 ablation.
#   uniform_methods_name    -> idem.
#   no_comments             -> idem.
#
# Default outputs (under src/ml_embeddings/, per mode)
#   - baseline               -> tuned_models_<MODEL>.pkl
#                               predictions/
#   - uniform_variables_name -> tuned_models_ablation_uniform_variables_name_<MODEL>.pkl
#                               predictions_ablation/uniform_variables_name/
#   - ...
#
# Prerequisites
#   1. run3-split-data.sh has produced the matching splits.
#   2. conda env active with scikit-learn, pandas, numpy.
#      xgboost is optional (only required for --model xgb).
#
# Usage
#   From repository root:
#     bash src/run4-train-classifiers.sh                  # baseline, default model
#     MODEL=svm bash src/run4-train-classifiers.sh        # baseline with SVM
#     bash src/run4-train-classifiers.sh all              # baseline + ablations
#     bash src/run4-train-classifiers.sh ablations
#     SKIP_TUNE=1 bash src/run4-train-classifiers.sh      # reuse existing pickle
#
# Customization (env vars)
#   MODEL          - lr | knn | mlp | svm | rf | dt | gb | xgb (default lr)
#   N_ITER         - random search samples (default 6)
#   CV             - CV folds during tuning  (default 5)
#   SEED           - RNG seed                (default 42)
#   SKIP_TUNE=1    - reuse existing tuned-model pickle, just run test step
#   SKIP_TEST=1    - run tuning only (skip test_embedding.py)
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Path resolution
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

# Inputs (split directories) and outputs (pickle + predictions) per mode.
# SPLITS_BASELINE="${SPLITS_BASELINE:-splits}"                  # Original path.
SPLITS_BASELINE="${SPLITS_BASELINE:-data_codesearchnet/splits}" # CodeSearchNet grouped splits.
SPLITS_ABLATION_ROOT="${SPLITS_ABLATION_ROOT:-splits_ablation}"

# Output organization under src/ml_embeddings/
EXPERIMENT_TAG="${EXPERIMENT_TAG:-codesearchnet}"
MODEL_DIR="${MODEL_DIR:-data_codesearchnet/models}"
PREDICTIONS_ROOT="${PREDICTIONS_ROOT:-data_codesearchnet/predictions}"

# Hyperparameters
MODEL="${MODEL:-lr}"
N_ITER="${N_ITER:-30}"
CV="${CV:-5}"
SEED="${SEED:-42}"

PYTHON="${PYTHON:-python}"

# Optional LLM aggregation buckets for test_embedding.py.
# Space-separated. If empty, test_embedding.py infers LLM names from folder names.
LLM_KEYS="${LLM_KEYS:-starcoder2-7b}"   # Explicit LLM keys for starcoder2-7b
# LLM_KEYS="chatgpt4 chatgpt_ gemini starcoder2-7b" # For the larger mixed dataset

LLM_KEYS_ARG=()
if [ -n "${LLM_KEYS}" ]; then
  read -r -a _LLM_KEYS_ARRAY <<< "${LLM_KEYS}"
  LLM_KEYS_ARG=(--llm-keys "${_LLM_KEYS_ARRAY[@]}")
fi

# Logging
TS="$(date +'%Y%m%d_%H%M%S')"
RUN_TAG="${RUN_TAG:-${EXPERIMENT_TAG}_${MODEL}_${TS}}"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run4-train-classifiers_${RUN_TAG}.log}"

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
# Per-mode mapping
# -----------------------------------------------------------------------------
splits_for_mode() {
  case "$1" in
    baseline)               echo "${SPLITS_BASELINE}" ;;
    uniform_variables_name) echo "${SPLITS_ABLATION_ROOT}/uniform_variables_name" ;;
    uniform_methods_name)   echo "${SPLITS_ABLATION_ROOT}/uniform_methods_name" ;;
    no_comments)            echo "${SPLITS_ABLATION_ROOT}/no_comments" ;;
    *) echo "[ERROR] unknown mode: $1" >&2; exit 2 ;;
  esac
}

pickle_for_mode() {
  case "$1" in
    baseline)               echo "${MODEL_DIR}/tuned_models_${RUN_TAG}.pkl" ;;
    *)                      echo "${MODEL_DIR}/tuned_models_ablation_${1}_${RUN_TAG}.pkl" ;;
  esac
}

predictions_for_mode() {
  case "$1" in
    baseline)               echo "${PREDICTIONS_ROOT}/${RUN_TAG}" ;;
    *)                      echo "${PREDICTIONS_ROOT}/ablation_${1}_${RUN_TAG}" ;;
  esac
}

# -----------------------------------------------------------------------------
# Pre-flight
# -----------------------------------------------------------------------------
if [ ! -d "${TARGET_DIR}" ]; then
  echo "[ERROR] TARGET_DIR does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

cd "${TARGET_DIR}"
mkdir -p "${MODEL_DIR}" "${PREDICTIONS_ROOT}"

for f in hyperparameter_tuning.py test_embedding.py; do
  if [ ! -f "${f}" ]; then
    echo "[ERROR] ${f} not found in ${TARGET_DIR}" >&2
    exit 1
  fi
done

for mode in "${MODES[@]}"; do
  sp="$(splits_for_mode "${mode}")"
  if [ ! -d "${sp}" ] || [ -z "$(ls -A "${sp}" 2>/dev/null)" ]; then
    echo "[ERROR] splits for mode '${mode}' missing or empty: ${sp}" >&2
    echo "        Run run3-split-data.sh ${mode} first." >&2
    exit 1
  fi
done

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
echo "============================================================"
echo " run4-train-classifiers.sh"
echo "   target dir : ${TARGET_DIR}"
echo "   experiment : ${EXPERIMENT_TAG}"
echo "   run tag    : ${RUN_TAG}"
echo "   log file   : ${LOG_FILE}"
echo "   model      : ${MODEL}"
echo "   n_iter     : ${N_ITER}"
echo "   cv         : ${CV}"
echo "   seed       : ${SEED}"
echo "   llm keys   : ${LLM_KEYS:-auto}"
echo "   skip_tune  : ${SKIP_TUNE:-0}"
echo "   skip_test  : ${SKIP_TEST:-0}"
echo "   modes      : ${MODES[*]}"
echo "============================================================"

for mode in "${MODES[@]}"; do
  splits_dir="$(splits_for_mode  "${mode}")"
  pickle="$(pickle_for_mode      "${mode}")"
  predictions="$(predictions_for_mode "${mode}")"

  echo
  echo "------------------------------------------------------------"
  echo " mode            : ${mode}"
  echo " splits dir      : ${splits_dir}"
  echo " tuned pickle    : ${pickle}"
  echo " predictions dir : ${predictions}"
  echo "------------------------------------------------------------"

  if [ "${SKIP_TUNE:-0}" != "1" ]; then
    echo "[stage 1/2] tuning ..."
    "${PYTHON}" hyperparameter_tuning.py \
      --splits-dir "${splits_dir}" \
      --out-pickle "${pickle}" \
      --model      "${MODEL}" \
      --n-iter     "${N_ITER}" \
      --cv         "${CV}" \
      --seed       "${SEED}"
  else
    echo "[stage 1/2] tuning skipped (SKIP_TUNE=1); reusing ${pickle}"
    if [ ! -f "${pickle}" ]; then
      echo "[ERROR] SKIP_TUNE=1 but pickle missing: ${pickle}" >&2
      exit 1
    fi
  fi

  if [ "${SKIP_TEST:-0}" != "1" ]; then
    echo
    echo "[stage 2/2] testing ..."
    "${PYTHON}" test_embedding.py \
      --splits-dir       "${splits_dir}" \
      --models-pickle    "${pickle}" \
      --predictions-dir  "${predictions}" \
      "${LLM_KEYS_ARG[@]}"
  else
    echo "[stage 2/2] testing skipped (SKIP_TEST=1)"
  fi
done

echo
echo "============================================================"
echo " Done. Outputs:"
for mode in "${MODES[@]}"; do
  pickle="$(pickle_for_mode "${mode}")"
  predictions="$(predictions_for_mode "${mode}")"
  pred_count=$(find "${predictions}" -name '*.csv' 2>/dev/null | wc -l)
  printf "   %-26s pickle=%s  predictions=%d files in %s\n" \
         "${mode}" "${pickle}" "${pred_count}" "${predictions}"
done
echo "============================================================"
echo
echo "Finished: $(date -Is)"
echo "Log file: ${LOG_FILE}"


