#!/usr/bin/env bash
# =============================================================================
# run5-threshold-sweep.sh
# -----------------------------------------------------------------------------
# Decision-threshold sweep across tuned classifiers for RQ2-D, using dev-set
# threshold selection and test-set evaluation.
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
# Classifier selection
#   By default, sweeps ALL classifiers found under PICKLES_DIR (one latest
#   pickle per classifier short-name). To restrict, pass classifier names
#   as positional args:
#       bash run5-threshold-sweep.sh                # all (default)
#       bash run5-threshold-sweep.sh all            # explicit all
#       bash run5-threshold-sweep.sh svm            # just SVM
#       bash run5-threshold-sweep.sh svm mlp lr     # those three
#   Unknown names cause an early exit before any work begins.
#
# Multiple pickles per classifier
#   When the tuning stage has been re-run (e.g., LR three times, MLP twice),
#   multiple timestamped pickles exist per classifier. This script picks
#   the LATEST pickle per classifier short-name so each classifier appears
#   exactly once in the combined output.
#
# Inputs
#   * Splits dir : data_codesearchnet/splits/<MODEL_NAME>/
#   * Pickles    : data_codesearchnet/models/<MODEL_NAME>/tuned_models_*.pkl
#
# Outputs (under data_codesearchnet/threshold_sweep/<MODEL_NAME>/)
#   * <classifier>_summary.csv          one row per (dataset, embedding)
#   * <classifier>_summary_detail.csv   full sweep curve for plotting
#   * threshold_sweep_combined.csv      union across the swept classifiers
#
# Usage
#   bash src/run5-threshold-sweep.sh                              # all, 15B (default)
#   bash src/run5-threshold-sweep.sh svm                          # just SVM
#   bash src/run5-threshold-sweep.sh svm mlp lr                   # subset
#   MODEL_NAME=starcoder2-7b bash src/run5-threshold-sweep.sh     # 7B base, all
#   MODEL_NAME=starcoder2-7b bash src/run5-threshold-sweep.sh svm # 7B base, just SVM
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

# Recognized classifier short-names. Used to validate positional args.
KNOWN_CLASSIFIERS=(lr knn mlp svm rf dt gb xgb)

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
# Selection: which classifiers to sweep
# -----------------------------------------------------------------------------
# REQUESTED_CLASSIFIERS:
#   empty array  -> "sweep all found" (set below, after discovery)
#   non-empty    -> sweep exactly these (validated against KNOWN_CLASSIFIERS)
REQUESTED_CLASSIFIERS=()

if [ "$#" -gt 0 ]; then
  case "$1" in
    all)
      # leave REQUESTED_CLASSIFIERS empty (treated as "all found")
      ;;
    *)
      REQUESTED_CLASSIFIERS=("$@")
      ;;
  esac
fi

# Validate any explicit names against the known list.
if [ "${#REQUESTED_CLASSIFIERS[@]}" -gt 0 ]; then
  for clf in "${REQUESTED_CLASSIFIERS[@]}"; do
    found=0
    for known in "${KNOWN_CLASSIFIERS[@]}"; do
      if [ "${clf}" = "${known}" ]; then found=1; break; fi
    done
    if [ "${found}" -eq 0 ]; then
      echo "[ERROR] unknown classifier '${clf}'." >&2
      echo "        Known classifiers: ${KNOWN_CLASSIFIERS[*]}" >&2
      echo "        Or pass 'all' (or no args) to sweep every classifier found." >&2
      exit 2
    fi
  done
fi

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

declare -A LATEST_PICKLE_FOR_CLF

while IFS= read -r -d '' pkl; do
  fname="$(basename "${pkl}")"
  stem="${fname#tuned_models_}"
  stem="${stem%.pkl}"
  # Strip trailing _YYYYMMDD_HHMMSS
  stem_no_ts="$(echo "${stem}" | sed -E 's/_[0-9]{8}_[0-9]{6}$//')"
  # Classifier short-name is the last underscore-separated token.
  clf="${stem_no_ts##*_}"
  # find output is sorted; later assignments overwrite earlier -> last
  # (latest timestamp) wins per classifier.
  LATEST_PICKLE_FOR_CLF["${clf}"]="${pkl}"
done < <(find "${PICKLES_DIR}" -maxdepth 1 -name 'tuned_models_*.pkl' -print0 | sort -z)

if [ "${#LATEST_PICKLE_FOR_CLF[@]}" -eq 0 ]; then
  echo "[ERROR] no tuned_models_*.pkl found in ${PICKLES_DIR}" >&2
  exit 1
fi

# -----------------------------------------------------------------------------
# Resolve the final list of classifiers to sweep
# -----------------------------------------------------------------------------
SWEEP_CLASSIFIERS=()

if [ "${#REQUESTED_CLASSIFIERS[@]}" -eq 0 ]; then
  # No explicit selection -> all that we found.
  while IFS= read -r clf; do
    SWEEP_CLASSIFIERS+=("${clf}")
  done < <(printf '%s\n' "${!LATEST_PICKLE_FOR_CLF[@]}" | sort)
else
  # Explicit selection -> intersect with what was found, error if missing.
  missing=()
  for clf in "${REQUESTED_CLASSIFIERS[@]}"; do
    if [ -n "${LATEST_PICKLE_FOR_CLF[${clf}]+_}" ]; then
      SWEEP_CLASSIFIERS+=("${clf}")
    else
      missing+=("${clf}")
    fi
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    echo "[ERROR] No pickle found for these classifier(s) in ${PICKLES_DIR}:" >&2
    printf '          %s\n' "${missing[@]}" >&2
    echo "        Available: ${!LATEST_PICKLE_FOR_CLF[*]}" >&2
    exit 1
  fi
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
echo "   pickles found    : ${#LATEST_PICKLE_FOR_CLF[@]}"
echo "   classifiers req. : ${REQUESTED_CLASSIFIERS[*]:-<all found>}"
echo "   classifiers run  : ${SWEEP_CLASSIFIERS[*]}  (${#SWEEP_CLASSIFIERS[@]})"
echo "============================================================"
echo

# Print the picked pickles for transparency.
echo "Selected pickles (latest per classifier):"
for clf in "${SWEEP_CLASSIFIERS[@]}"; do
  echo "  ${clf}  ->  $(basename "${LATEST_PICKLE_FOR_CLF[${clf}]}")"
done
echo

# -----------------------------------------------------------------------------
# Per-classifier sweep
# -----------------------------------------------------------------------------
for clf in "${SWEEP_CLASSIFIERS[@]}"; do
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
# Aggregate (only over the classifiers we just swept)
# -----------------------------------------------------------------------------
# Note: aggregate_threshold_sweeps.py reads ALL <clf>_summary.csv in OUT_DIR.
# If you swept a subset but want the combined CSV to reflect ONLY this run,
# move the older per-classifier summaries elsewhere or use a fresh OUT_DIR.
# If you swept a subset on top of existing files, the combined output will
# include stale entries from previous runs -- by design, so you can build it
# up incrementally (e.g., sweep SVM today, MLP tomorrow, then aggregate).

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