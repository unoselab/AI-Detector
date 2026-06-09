#!/usr/bin/env bash
set -u
set -o pipefail

# =============================================================================
# run5b-test-classifiers-allmodels.sh
# =============================================================================
# TEST-ONLY counterpart of run4a-train-classifiers-allmodels.sh.
#
# run4a does two stages per family m:
#     stage 1: hyperparameter_tuning.py  -> writes tuned_models_<RUN_TAG>.pkl
#     stage 2: test_embedding.py         -> scores that pickle
# This script does STAGE 2 ONLY. It discovers the tuned_models_*.pkl files
# already sitting in MODEL_DIR, and for each one runs test_embedding.py with
# --no-refit (score the pickled, already-fitted estimator as-is) and
# --score-method auto (so AUROC is computed alongside the six base metrics).
# No tuning, no retraining.
#
# It deliberately clones run4a's directory layout (SCRIPT_DIR / REPO_ROOT /
# TARGET_DIR=ml_embeddings, relative SPLITS_DIR/MODEL_DIR/PREDICTIONS_ROOT,
# logs under REPO_ROOT/src/logs) so paths resolve identically.
#
# Pickle naming (from run4a)
#   tuned_models_<EXPERIMENT_TAG>_<family>_<YYYYMMDD>_<HHMMSS>.pkl
#   EXPERIMENT_TAG = codesearchnet_<MODEL_NAME>
# The family token is the alphanumeric field just before the date/time suffix.
#
# Usage
#   ./run5b-test-classifiers-allmodels.sh
#   MODEL_NAME=codellama-7b_4500_complexity_stratified_maxlen2048 \
#       ./run5b-test-classifiers-allmodels.sh
#   MODELS="lr svm rf" ./run5b-test-classifiers-allmodels.sh   # subset only
#   SELECT=all  ./run5b-test-classifiers-allmodels.sh          # every pickle
#   REFIT=1     ./run5b-test-classifiers-allmodels.sh          # refit instead
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

cd "${REPO_ROOT}" || exit 1

PYTHON="${PYTHON:-python}"

# Which experiment to score. Defaulted to the codellama-7b set from the
# directory listing so this runs out of the box; override via MODEL_NAME.
MODEL_NAME="${MODEL_NAME:-codellama-7b_4500_complexity_stratified_maxlen2048}"

# Paths are RELATIVE to TARGET_DIR (we cd into it below), matching run4a.
SPLITS_DIR="${SPLITS_DIR:-data_codesearchnet/splits/${MODEL_NAME}}"
MODEL_DIR="${MODEL_DIR:-data_codesearchnet/models/${MODEL_NAME}}"
PREDICTIONS_ROOT="${PREDICTIONS_ROOT:-data_codesearchnet/predictions/${MODEL_NAME}}"

# Behaviour knobs.
#   MODELS : optional space-separated family filter; empty = every family found
#   SELECT : latest (newest pickle per family) | all (every pickle)
#   SCORE_METHOD : auto | proba | decision  (passed to test_embedding.py)
#   REFIT  : 1 -> refit before scoring; default 0 -> pass --no-refit
MODELS="${MODELS:-}"
SELECT="${SELECT:-latest}"
SCORE_METHOD="${SCORE_METHOD:-auto}"
REFIT="${REFIT:-0}"

# Canonical family tokens, used to validate the token parsed from a filename
# (so unrelated files in MODEL_DIR are ignored rather than misread).
KNOWN_FAMILIES="lr svm mlp rf gb knn dt et ada hgb xgb"

TS="$(date +'%Y%m%d_%H%M%S')"
LOGDIR="src/logs/rq2d_test_codesearchnet_${MODEL_NAME}_allmodels_${TS}"
SUMMARY="${LOGDIR}/test_run_summary_${TS}.tsv"

mkdir -p "${LOGDIR}"

# Decide whether xgboost can be imported. An xgb pickle cannot be unpickled
# without xgboost installed, so we skip xgb pickles when it is missing.
if "${PYTHON}" - <<'PY'
try:
    import xgboost  # noqa: F401
except ImportError:
    raise SystemExit(1)
PY
then
  HAVE_XGB=1
else
  HAVE_XGB=0
fi

# -----------------------------------------------------------------------------
# parse_family <run_tag>
#   Echo the classifier family token embedded in a run4a pickle's RUN_TAG.
#   RUN_TAG looks like <EXPERIMENT_TAG>_<family>_<YYYYMMDD>_<HHMMSS>, so the
#   family is the [A-Za-z0-9]+ token immediately preceding the 8-digit date and
#   6-digit time. Echoes nothing if the tag does not match the pattern.
# -----------------------------------------------------------------------------
parse_family() {
  local runtag="$1"
  echo "${runtag}" | sed -nE 's/.*_([A-Za-z0-9]+)_[0-9]{8}_[0-9]{6}$/\1/p'
}

# -----------------------------------------------------------------------------
# is_known_family <family>
#   Return success (0) if <family> is one of KNOWN_FAMILIES, else failure (1).
#   Used to drop stray files whose trailing token is not a real classifier.
# -----------------------------------------------------------------------------
is_known_family() {
  local f="$1"
  [[ " ${KNOWN_FAMILIES} " == *" ${f} "* ]]
}

# -----------------------------------------------------------------------------
# in_models_filter <family>
#   Return success if MODELS is empty (no filter) or contains <family>.
# -----------------------------------------------------------------------------
in_models_filter() {
  local f="$1"
  [ -z "${MODELS// /}" ] && return 0
  [[ " ${MODELS} " == *" ${f} "* ]]
}

echo "============================================================"
echo " run5b-test-classifiers-allmodels.sh (test-only)"
echo "   script dir      : ${SCRIPT_DIR}"
echo "   repo root       : ${REPO_ROOT}"
echo "   target dir      : ${TARGET_DIR}"
echo "   model name      : ${MODEL_NAME}"
echo "   splits dir      : ${SPLITS_DIR}"
echo "   model dir       : ${MODEL_DIR}"
echo "   predictions root: ${PREDICTIONS_ROOT}"
echo "   models filter   : ${MODELS:-(all found)}"
echo "   select          : ${SELECT}"
echo "   score-method    : ${SCORE_METHOD}"
echo "   refit           : ${REFIT}  (0 => --no-refit)"
echo "   have xgboost    : ${HAVE_XGB}"
echo "   log dir         : ${LOGDIR}"
echo "   summary         : ${SUMMARY}"
echo "============================================================"

# Move into the scripts root so test_embedding.py and the relative data paths
# resolve exactly as they do for run4a.
cd "${TARGET_DIR}" || exit 1

if [ ! -f "test_embedding.py" ]; then
  echo "[ERROR] test_embedding.py not found in ${TARGET_DIR}" >&2
  exit 1
fi
if [ ! -d "${SPLITS_DIR}" ]; then
  echo "[ERROR] missing splits dir: ${TARGET_DIR}/${SPLITS_DIR}" >&2
  exit 1
fi
if [ ! -d "${MODEL_DIR}" ]; then
  echo "[ERROR] missing model dir: ${TARGET_DIR}/${MODEL_DIR}" >&2
  exit 1
fi

# Translate REFIT into the flag passed to test_embedding.py.
if [ "${REFIT}" = "1" ]; then
  NO_REFIT_FLAG=""
else
  NO_REFIT_FLAG="--no-refit"
fi

# -----------------------------------------------------------------------------
# Discover pickles and decide which to score.
#   - Walk MODEL_DIR for tuned_models_*.pkl.
#   - Parse + validate the family token; apply the MODELS filter; skip xgb if
#     xgboost is unavailable.
#   - SELECT=latest keeps the newest pickle per family (timestamps embedded in
#     the name sort lexically, so the last one wins); SELECT=all keeps them all.
# -----------------------------------------------------------------------------
declare -A LATEST_PATH      # family -> newest pickle path (for SELECT=latest)
PICKLES_TO_RUN=()           # ordered list of pickle paths to score

shopt -s nullglob
for pf in "${MODEL_DIR}"/tuned_models_*.pkl; do
  bn="$(basename "${pf}")"
  runtag="${bn#tuned_models_}"
  runtag="${runtag%.pkl}"
  fam="$(parse_family "${runtag}")"

  [ -z "${fam}" ] && { echo "[skip] unrecognised name: ${bn}"; continue; }
  is_known_family "${fam}" || { echo "[skip] unknown family '${fam}': ${bn}"; continue; }
  in_models_filter "${fam}" || continue
  if [ "${fam}" = "xgb" ] && [ "${HAVE_XGB}" != "1" ]; then
    echo "[skip] xgboost not importable; cannot load ${bn}"
    continue
  fi

  if [ "${SELECT}" = "all" ]; then
    PICKLES_TO_RUN+=("${pf}")
  else
    # Keep the lexically greatest filename per family (= newest timestamp).
    prev="${LATEST_PATH[${fam}]:-}"
    if [ -z "${prev}" ] || [[ "${bn}" > "$(basename "${prev}")" ]]; then
      LATEST_PATH[${fam}]="${pf}"
    fi
  fi
done
shopt -u nullglob

# For SELECT=latest, flatten the per-family map into the run list (family order
# sorted for determinism).
if [ "${SELECT}" != "all" ]; then
  for fam in $(printf '%s\n' "${!LATEST_PATH[@]}" | sort); do
    PICKLES_TO_RUN+=("${LATEST_PATH[${fam}]}")
  done
fi

if [ "${#PICKLES_TO_RUN[@]}" -eq 0 ]; then
  echo "[ERROR] no matching tuned_models_*.pkl in ${TARGET_DIR}/${MODEL_DIR}" >&2
  exit 1
fi

echo
echo "Pickles to score (${#PICKLES_TO_RUN[@]}):"
for p in "${PICKLES_TO_RUN[@]}"; do echo "  $(basename "${p}")"; done
echo

# Summary header (mirrors run4a's columns, with family + pickle added).
echo -e "model_name\tfamily\tstatus\tstart_time\tend_time\tseconds\tpickle\tlog_file" \
  > "${REPO_ROOT}/${SUMMARY}"

# -----------------------------------------------------------------------------
# Score each pickle. Continue past failures so one bad family never aborts the
# whole batch (matches run4a's continue-on-fail behaviour).
# -----------------------------------------------------------------------------
for PICKLE in "${PICKLES_TO_RUN[@]}"; do
  bn="$(basename "${PICKLE}")"
  RUN_TAG="${bn#tuned_models_}"
  RUN_TAG="${RUN_TAG%.pkl}"
  fam="$(parse_family "${RUN_TAG}")"

  # Reuse the pickle's RUN_TAG for the predictions dir so outputs land in the
  # same layout run4a would have produced for this family.
  PREDICTIONS_DIR="${PREDICTIONS_ROOT}/${RUN_TAG}"
  MODEL_LOG="${REPO_ROOT}/${LOGDIR}/run5b_${MODEL_NAME}_${fam}_${TS}.log"

  mkdir -p "${PREDICTIONS_DIR}"

  START_ISO="$(date -Is)"
  START_SEC="$(date +%s)"

  echo "============================================================"
  echo "Testing family : ${fam}"
  echo "Pickle         : ${bn}"
  echo "Predictions    : ${PREDICTIONS_DIR}"
  echo "Log            : ${MODEL_LOG}"
  echo "Started        : ${START_ISO}"
  echo "============================================================"

  {
    echo "============================================================"
    echo " run5b standalone test run"
    echo "   model name      : ${MODEL_NAME}"
    echo "   classifier      : ${fam}"
    echo "   splits dir      : ${SPLITS_DIR}"
    echo "   tuned pickle    : ${PICKLE}"
    echo "   predictions dir : ${PREDICTIONS_DIR}"
    echo "   score-method    : ${SCORE_METHOD}"
    echo "   refit           : ${REFIT}"
    echo "============================================================"
    echo

    "${PYTHON}" test_embedding.py \
      --splits-dir      "${SPLITS_DIR}" \
      --models-pickle   "${PICKLE}" \
      --predictions-dir "${PREDICTIONS_DIR}" \
      --score-method    "${SCORE_METHOD}" \
      ${NO_REFIT_FLAG}

  } 2>&1 | tee "${MODEL_LOG}"

  # PIPESTATUS[0] is the python exit code (tee is element 1).
  PIPE_STATUS=("${PIPESTATUS[@]}")
  if [ "${PIPE_STATUS[0]}" -eq 0 ]; then
    STATUS="OK"
  else
    STATUS="FAIL"
  fi

  END_ISO="$(date -Is)"
  END_SEC="$(date +%s)"
  ELAPSED="$((END_SEC - START_SEC))"

  echo -e "${MODEL_NAME}\t${fam}\t${STATUS}\t${START_ISO}\t${END_ISO}\t${ELAPSED}\t${PICKLE}\t${MODEL_LOG}" \
    >> "${REPO_ROOT}/${SUMMARY}"

  echo "Finished family: ${fam}"
  echo "Status: ${STATUS}"
  echo "Elapsed seconds: ${ELAPSED}"
  echo
done

cd "${REPO_ROOT}" || exit 1

echo "============================================================"
echo "All done"
echo "Log dir: ${LOGDIR}"
echo "Summary: ${SUMMARY}"
echo "============================================================"
cat "${SUMMARY}"