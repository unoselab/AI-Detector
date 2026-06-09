#!/usr/bin/env bash
set -u
set -o pipefail

# =============================================================================
# run6-analyze-results-testedclassifiers.sh
# =============================================================================
# Aggregate the per-sample prediction CSVs that run5b produced into ONE tidy
# metrics CSV across all classifier families, recomputing ACC/TPR/TNR/F1s/
# Avg_F1/AUROC straight from the stored columns (no model is re-run), and
# ALSO emit a paper-ready LaTeX table.
#
# It clones run4a/run5b's directory layout (SCRIPT_DIR / REPO_ROOT /
# TARGET_DIR=ml_embeddings, relative data paths, logs under REPO_ROOT/src/logs)
# and calls analyze_results.py to do the work.
#
# Usage
#   ./run6-analyze-results-testedclassifiers.sh
#   MODEL_NAME=codellama-7b_4500_complexity_stratified_maxlen2048 \
#       ./run6-analyze-results-testedclassifiers.sh
#   LATEX_METRICS="avg_f1,auroc" ./run6-analyze-results-testedclassifiers.sh
#   NO_LATEX=1 ./run6-analyze-results-testedclassifiers.sh    # CSV only
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/ml_embeddings}"

cd "${REPO_ROOT}" || exit 1

PYTHON="${PYTHON:-python}"

# Which experiment to analyze. Same default as run5b so they chain cleanly.
MODEL_NAME="${MODEL_NAME:-codellama-7b_4500_complexity_stratified_maxlen2048}"

# Paths RELATIVE to TARGET_DIR (we cd into it below), matching run5b.
PREDICTIONS_ROOT="${PREDICTIONS_ROOT:-data_codesearchnet/predictions/${MODEL_NAME}}"
ANALYSIS_DIR="${ANALYSIS_DIR:-data_codesearchnet/analysis/${MODEL_NAME}}"

TS="$(date +'%Y%m%d_%H%M%S')"
# Final tidy metrics table + LaTeX table. Override either to relocate.
OUT_CSV="${OUT_CSV:-${ANALYSIS_DIR}/metrics_allmodels_${MODEL_NAME}_${TS}.csv}"
LATEX_OUT="${LATEX_OUT:-${ANALYSIS_DIR}/metrics_table_${MODEL_NAME}_${TS}.tex}"

# LaTeX controls.
#   LATEX_METRICS : comma-separated metrics per embedding column group
#   LATEX_CAPTION : caption text (model name is folded in by default)
#   LATEX_LABEL   : \label for the table
#   NO_LATEX=1     : skip the LaTeX table (CSV only)
LATEX_METRICS="${LATEX_METRICS:-avg_f1,auroc}"
LATEX_CAPTION="${LATEX_CAPTION:-Detection metrics by classifier and embedding type for ${MODEL_NAME}.}"
LATEX_LABEL="${LATEX_LABEL:-tab:rq2d_${MODEL_NAME}}"

LOGDIR="src/logs/rq2d_analyze_codesearchnet_${MODEL_NAME}_${TS}"
LOG="${LOGDIR}/analyze_${TS}.log"

mkdir -p "${LOGDIR}"

echo "============================================================"
echo " run6-analyze-results-testedclassifiers.sh"
echo "   script dir      : ${SCRIPT_DIR}"
echo "   repo root       : ${REPO_ROOT}"
echo "   target dir      : ${TARGET_DIR}"
echo "   model name      : ${MODEL_NAME}"
echo "   predictions root: ${PREDICTIONS_ROOT}"
echo "   analysis dir    : ${ANALYSIS_DIR}"
echo "   out csv         : ${OUT_CSV}"
echo "   latex out       : ${LATEX_OUT}"
echo "   latex metrics   : ${LATEX_METRICS}"
echo "   no latex        : ${NO_LATEX:-0}"
echo "   log             : ${LOG}"
echo "============================================================"

# Move into the scripts root so analyze_results.py and the relative data paths
# resolve exactly as they do for run5b.
cd "${TARGET_DIR}" || exit 1

if [ ! -f "analyze_results.py" ]; then
  echo "[ERROR] analyze_results.py not found in ${TARGET_DIR}" >&2
  exit 1
fi
if [ ! -d "${PREDICTIONS_ROOT}" ]; then
  echo "[ERROR] missing predictions root: ${TARGET_DIR}/${PREDICTIONS_ROOT}" >&2
  exit 1
fi

mkdir -p "${ANALYSIS_DIR}"

# Assemble the optional LaTeX arguments unless NO_LATEX is set.
LATEX_ARGS=()
if [ "${NO_LATEX:-0}" != "1" ]; then
  LATEX_ARGS=(--latex-out "${LATEX_OUT}"
              --latex-metrics "${LATEX_METRICS}"
              --latex-caption "${LATEX_CAPTION}"
              --latex-label   "${LATEX_LABEL}")
fi

# Run the aggregator; tee its full output (table + ranking) to the log.
{
  echo "============================================================"
  echo " run6 analyze"
  echo "   predictions root: ${PREDICTIONS_ROOT}"
  echo "   out csv         : ${OUT_CSV}"
  echo "   latex out       : ${LATEX_OUT}"
  echo "   started         : $(date -Is)"
  echo "============================================================"
  echo

  "${PYTHON}" analyze_results.py \
    --predictions-root "${PREDICTIONS_ROOT}" \
    --out-csv          "${OUT_CSV}" \
    "${LATEX_ARGS[@]}"

  echo
  echo "   finished        : $(date -Is)"
} 2>&1 | tee "${REPO_ROOT}/${LOG}"

# PIPESTATUS[0] is the python exit code (tee is element 1).
PIPE_STATUS=("${PIPESTATUS[@]}")
if [ "${PIPE_STATUS[0]}" -ne 0 ]; then
  echo "[ERROR] analyze_results.py failed (see ${LOG})" >&2
  exit 1
fi

cd "${REPO_ROOT}" || exit 1

echo "============================================================"
echo "All done"
echo "Metrics CSV: ${TARGET_DIR}/${OUT_CSV}"
if [ "${NO_LATEX:-0}" != "1" ]; then
  echo "LaTeX table: ${TARGET_DIR}/${LATEX_OUT}"
fi
echo "Log        : ${LOG}"
echo "============================================================"