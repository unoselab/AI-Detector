#!/usr/bin/env bash
# =============================================================================
# run5-threshold-sweep.sh
# -----------------------------------------------------------------------------
# Decision-threshold sweep across all tuned classifiers for RQ2-D, using
# dev-set threshold selection and test-set evaluation.
#
# What this does
#   For each tuned-models pickle produced by run4 / run4a, runs
#   threshold_sweep.py:
#     1. Selects the decision threshold that maximizes macro-F1 on the dev
#        split (not the test split -- avoids test-set leakage).
#     2. Reports macro-F1 on the test split at that threshold.
#     3. Compares to the default-0.5 baseline (== what test_embedding.py
#        reports).
#   No retraining is performed; this is a pure post-hoc analysis on the
#   existing classifiers.
#
# Multiple pickles per classifier
#   When the tuning stage has been re-run (e.g., LR three times, MLP twice),
#   multiple timestamped pickles exist per classifier. This script picks
#   the LATEST pickle per classifier short-name (lr/svm/mlp/...) so each
#   classifier appears exactly once in the combined output.
#
# Inputs
#   * Splits dir : data_codesearchnet/splits/<MODEL_NAME>/
#   * Pickles    : data_codesearchnet/models/<MODEL_NAME>/tuned_models_*.pkl
#
# Outputs (under data_codesearchnet/threshold_sweep/<MODEL_NAME>/)
#   * <classifier>_summary.csv          one row per (dataset, embedding)
#   * <classifier>_summary_detail.csv   full sweep curve for plotting
#   * threshold_sweep_combined.csv      union across classifiers
#
# Usage
#   bash src/run5-threshold-sweep.sh                              # latest 15B run
#   MODEL_NAME=starcoder2-7b bash src/run5-threshold-sweep.sh     # 7B run
#
# Env vars
#   MODEL_NAME       - which model's pickles to sweep
#                      (default: starcoder2-15b-instruct-v0.1)
#   TARGET_DIR       - ml_embeddings directory (default: src/ml_embeddings)
#   SPLITS_DIR       - per-dataset splits root (default derived from MODEL_NAME)
#   PICKLES_DIR      - tuned-model pickles root (default derived from MODEL_NAME)
#   OUT_DIR          - sweep output root (default derived from MODEL_NAME)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODEL_NAME="${MODEL_NAME:-starcoder2-15b-instruct-v0.1}"
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

SPLITS_DIR="${SPLITS_DIR:-data_codesearchnet/splits/${MODEL_NAME}}"
PICKLES_DIR="${PICKLES_DIR:-data_codesearchnet/models/${MODEL_NAME}}"
OUT_DIR="${OUT_DIR:-data_codesearchnet/threshold_sweep/${MODEL_NAME}}"

PYTHON="${PYTHON:-python}"

# Logging
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
LOG_FILE="${LOG_DIR}/run5-threshold-sweep_${MODEL_NAME}_${TS}.log"

mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "Log file: ${LOG_FILE}"
echo "Started : $(date -Is)"
echo

# -----------------------------------------------------------------------------
# Pre-flight
# -----------------------------------------------------------------------------
if [ ! -d "${TARGET_DIR}" ]; then
  echo "[ERROR] TARGET_DIR does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

cd "${TARGET_DIR}"

for f in threshold_sweep.py aggregate_threshold_sweeps.py; do
  if [ ! -f "${f}" ]; then
    echo "[ERROR] ${f} not found in ${TARGET_DIR}" >&2
    exit 1
  fi
done

if [ ! -d "${SPLITS_DIR}" ]; then
  echo "[ERROR] splits dir missing: ${SPLITS_DIR}" >&2
  exit 1
fi

if [ ! -d "${PICKLES_DIR}" ]; then
  echo "[ERROR] pickles dir missing: ${PICKLES_DIR}" >&2
  exit 1
fi

# -----------------------------------------------------------------------------
# Discover one pickle per classifier (the latest by filename timestamp)
# -----------------------------------------------------------------------------
# Filename pattern:
#   tuned_models_codesearchnet[_<MODEL_NAME>]_<clf>_<YYYYMMDD>_<HHMMSS>.pkl
# Classifier short-name is the token between "_<MODEL_NAME>_" (or
# "_codesearchnet_") and "_<YYYYMMDD>".
#
# Strategy: list pickles sorted by name (which puts the latest timestamp
# last), extract the <clf> token, and keep the last-seen file per <clf>.

declare -A LATEST_PICKLE_FOR_CLF

while IFS= read -r -d '' pkl; do
  fname="$(basename "${pkl}")"
  stem="${fname#tuned_models_}"
  stem="${stem%.pkl}"
  # Strip trailing _YYYYMMDD_HHMMSS
  stem_no_ts="$(echo "${stem}" | sed -E 's/_[0-9]{8}_[0-9]{6}$//')"
  # Classifier short-name is the last underscore-separated token.
  clf="${stem_no_ts##*_}"
  # Because the find output is sorted, later assignments overwrite earlier
  # ones -- so we end up with the lexicographically last (= latest
  # timestamp) pickle per classifier.
  LATEST_PICKLE_FOR_CLF["${clf}"]="${pkl}"
done < <(find "${PICKLES_DIR}" -maxdepth 1 -name 'tuned_models_*.pkl' -print0 | sort -z)

if [ "${#LATEST_PICKLE_FOR_CLF[@]}" -eq 0 ]; then
  echo "[ERROR] no tuned_models_*.pkl found in ${PICKLES_DIR}" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

# -----------------------------------------------------------------------------
# Banner
# -----------------------------------------------------------------------------
echo "============================================================"
echo " run5-threshold-sweep.sh"
echo "   target dir       : ${TARGET_DIR}"
echo "   model name       : ${MODEL_NAME}"
echo "   splits dir       : ${SPLITS_DIR}"
echo "   pickles dir      : ${PICKLES_DIR}"
echo "   out dir          : ${OUT_DIR}"
echo "   classifiers      : ${#LATEST_PICKLE_FOR_CLF[@]}  (one latest pickle each)"
echo "============================================================"
echo

# Print the picked pickles for transparency.
echo "Selected pickles (one per classifier, latest timestamp):"
for clf in $(printf '%s\n' "${!LATEST_PICKLE_FOR_CLF[@]}" | sort); do
  echo "  ${clf}  ->  $(basename "${LATEST_PICKLE_FOR_CLF[${clf}]}")"
done
echo

# -----------------------------------------------------------------------------
# Per-classifier sweep
# -----------------------------------------------------------------------------
for clf in $(printf '%s\n' "${!LATEST_PICKLE_FOR_CLF[@]}" | sort); do
  pkl="${LATEST_PICKLE_FOR_CLF[${clf}]}"
  out_csv="${OUT_DIR}/${clf}_summary.csv"

  echo
  echo "------------------------------------------------------------"
  echo " classifier : ${clf}"
  echo " pickle     : ${pkl}"
  echo " out csv    : ${out_csv}"
  echo "------------------------------------------------------------"

  "${PYTHON}" threshold_sweep.py \
    --splits-dir    "${SPLITS_DIR}" \
    --models-pickle "${pkl}" \
    --out-csv       "${out_csv}"
done

# -----------------------------------------------------------------------------
# Aggregate
# -----------------------------------------------------------------------------
echo
echo "============================================================"
echo " Combining per-classifier summaries"
echo "============================================================"

COMBINED="${OUT_DIR}/threshold_sweep_combined.csv"

"${PYTHON}" aggregate_threshold_sweeps.py \
  --sweep-dir "${OUT_DIR}" \
  --out-csv   "${COMBINED}"

echo
echo "Finished: $(date -Is)"
echo "Log file: ${LOG_FILE}"