#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run4b-compute-agc-transfer-table1-selected-v1.sh
# -----------------------------------------------------------------------------
# Recompute the full 5x5 cross-generator transfer matrix using exactly the
# classifier + representation configurations selected for Table (1).
#
# This script is intentionally standalone. It reuses the existing Python
# inference implementation (src/app/agc_detector.py), but it does NOT call the
# older run3-compute-agc-transfer.sh or run4-compute-agc-transfer-allclassifiers.sh
# wrappers. This prevents the new experiment from inheriting their older fixed
# classifier choices.
#
# INPUTS
#   1. Existing mixed-authorship evaluation sets:
#      src/app/data_mixed_samples/<target_experiment>/50x6/
#      Each target is expected to contain 50 mixed_sample_*.py files and their
#      corresponding ground-truth label TSV files.
#
#   2. Table (1)-selected frozen classifier pickles:
#      CL-7B    : SVM + AST
#      SC2-7B   : SVM + AST
#      SC2-15B  : SVM + AST
#      GO-120B  : MLP + AST
#      GM4-31B  : LR  + AST
#
#   3. Existing inference implementation:
#      src/app/agc_detector.py
#
# OUTPUTS
#   Predictions:
#     src/app/data_mixed_samples_transfer_table1_selected_v1/
#       clf-<training-source>/<target-experiment>/50x6/predictions/
#
#   Provenance manifest:
#     <output-root>/table1_selected_config_manifest.csv
#
#   Logs:
#     src/logs/run4b-table1-selected-v1/<timestamp>/
#       master.log
#       transfer_<training-source>.log
#
# The old transfer output tree is never modified.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Frozen experiment geometry and representation.
# Table (1) selected AST for all five training sources.
# -----------------------------------------------------------------------------
DATA_ROOT="${DATA_ROOT:-src/app/data_mixed_samples}"
GEOMETRY="${GEOMETRY:-50x6}"
EMBEDDING="${EMBEDDING:-ast}"
MAX_LEN="${MAX_LEN:-2048}"
EXPECTED_MIXED_FILES="${EXPECTED_MIXED_FILES:-50}"

# Use a new output root so the June 1 transfer matrix remains immutable.
OUTPUT_ROOT="${OUTPUT_ROOT:-src/app/data_mixed_samples_transfer_table1_selected_v1}"
ALLOW_OVERWRITE="${ALLOW_OVERWRITE:-0}"

# Natural classifier decision boundaries are used, matching the original
# transfer experiment. Set THRESHOLD only for an explicit sensitivity run.
THRESHOLD="${THRESHOLD:-}"

# -----------------------------------------------------------------------------
# Target datasets, ordered to match the revised Table (2).
# Paper labels:
#   CL-7B, SC2-7B, SC2-15B, GO-120B, GM4-31B
# -----------------------------------------------------------------------------
TARGETS=(
  "codellama-7b_4500_complexity_stratified_maxlen2048"
  "starcoder2-7b_4500_complexity_stratified_maxlen2048"
  "starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048"
  "gpt-oss_4500_complexity_stratified_maxlen2048"
  "gemma_4500_complexity_stratified_maxlen2048"
)

# -----------------------------------------------------------------------------
# Table (1)-selected frozen configurations.
# Columns:
#   paper_label | clf_gen | clf_exp | algorithm | embedding | model_pickle
#
# These exact pickles are the held-out test configurations reported in Table (1).
# -----------------------------------------------------------------------------
CLASSIFIERS=(
  "CL-7B|codellama-7b|codellama-7b_4500_complexity_stratified_maxlen2048|svm|ast|src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"
  "SC2-7B|starcoder2-7b|starcoder2-7b_4500_complexity_stratified_maxlen2048|svm|ast|src/ml_embeddings/data_codesearchnet/models/starcoder2-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_starcoder2-7b_4500_complexity_stratified_maxlen2048_svm_20260528_142045.pkl"
  "SC2-15B|starcoder2-15b-instruct-v0.1|starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048|svm|ast|src/ml_embeddings/data_codesearchnet/models/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048_svm_20260526_033005.pkl"
  "GO-120B|gpt-oss|gpt-oss_4500_complexity_stratified_maxlen2048|mlp|ast|src/ml_embeddings/data_codesearchnet/models/gpt-oss_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_maxlen2048_mlp_20260527_192034.pkl"
  "GM4-31B|gemma|gemma_4500_complexity_stratified_maxlen2048|lr|ast|src/ml_embeddings/data_codesearchnet/models/gemma_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gemma_4500_complexity_stratified_maxlen2048_lr_20260529_163559.pkl"
)

# -----------------------------------------------------------------------------
# Logging and experiment manifest.
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
RUN_LOG_DIR="${LOG_DIR:-src/logs/run4b-table1-selected-v1/${TS}}"
MASTER_LOG="${RUN_LOG_DIR}/master.log"
MANIFEST="${OUTPUT_ROOT}/table1_selected_config_manifest.csv"

mkdir -p "${RUN_LOG_DIR}"

if [ -d "${OUTPUT_ROOT}" ] && find "${OUTPUT_ROOT}" -type f -print -quit 2>/dev/null | grep -q .; then
  if [ "${ALLOW_OVERWRITE}" != "1" ]; then
    echo "[ERROR] Output root already contains files: ${OUTPUT_ROOT}" >&2
    echo "        Refusing to mix runs. Use a new OUTPUT_ROOT or set ALLOW_OVERWRITE=1." >&2
    exit 2
  fi
fi
mkdir -p "${OUTPUT_ROOT}"

exec > >(tee -a "${MASTER_LOG}") 2>&1

printf '%s\n' \
  "paper_label,clf_gen,clf_exp,algorithm,embedding,max_len,model_pickle,model_sha256" \
  > "${MANIFEST}"

# -----------------------------------------------------------------------------
# Preflight checks: inference script, 5 target datasets, and 5 frozen pickles.
# -----------------------------------------------------------------------------
if [ ! -f "src/app/agc_detector.py" ]; then
  echo "[ERROR] Missing inference script: src/app/agc_detector.py" >&2
  exit 3
fi

for target in "${TARGETS[@]}"; do
  in_dir="${DATA_ROOT}/${target}/${GEOMETRY}"
  if [ ! -d "${in_dir}" ]; then
    echo "[ERROR] Missing target input directory: ${in_dir}" >&2
    exit 3
  fi

  n_py="$(find "${in_dir}" -maxdepth 1 -type f -name 'mixed_sample_*.py' | wc -l | tr -d ' ')"
  if [ "${n_py}" -ne "${EXPECTED_MIXED_FILES}" ]; then
    echo "[ERROR] ${target}: expected ${EXPECTED_MIXED_FILES} mixed Python files, found ${n_py}" >&2
    exit 3
  fi
done

for entry in "${CLASSIFIERS[@]}"; do
  IFS='|' read -r paper_label clf_gen clf_exp algo embedding model_pickle <<< "${entry}"
  if [ ! -f "${model_pickle}" ]; then
    echo "[ERROR] Missing frozen model pickle for ${paper_label}: ${model_pickle}" >&2
    exit 3
  fi

done

echo "========================================================================="
echo " Table (1)-Aligned Cross-Generator Transfer Evaluation"
echo " Version       : v1"
echo " Geometry      : ${GEOMETRY}"
echo " Embedding     : ${EMBEDDING}"
echo " Max length    : ${MAX_LEN}"
echo " Output root   : ${OUTPUT_ROOT}"
echo " Manifest      : ${MANIFEST}"
echo " Started       : $(date -Is)"
echo "========================================================================="

# -----------------------------------------------------------------------------
# Full 5x5 evaluation.
# Every row uses exactly one Table (1)-selected frozen classifier and scores all
# five target generation sources, including the diagonal target.
# -----------------------------------------------------------------------------
cell_count=0
for entry in "${CLASSIFIERS[@]}"; do
  IFS='|' read -r paper_label clf_gen clf_exp algo embedding model_pickle <<< "${entry}"

  model_sha256="$(sha256sum "${model_pickle}" | awk '{print $1}')"
  printf '%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "${paper_label}" "${clf_gen}" "${clf_exp}" "${algo}" "${embedding}" \
    "${MAX_LEN}" "${model_pickle}" "${model_sha256}" >> "${MANIFEST}"

  row_log="${RUN_LOG_DIR}/transfer_${clf_gen}.log"
  : > "${row_log}"

  {
    echo "========================================================================="
    echo " Training source : ${paper_label}"
    echo " Classifier gen  : ${clf_gen}"
    echo " Experiment      : ${clf_exp}"
    echo " Algorithm       : ${algo}"
    echo " Embedding       : ${embedding}"
    echo " Max length      : ${MAX_LEN}"
    echo " Model pickle    : ${model_pickle}"
    echo " Model SHA256    : ${model_sha256}"
    echo "========================================================================="
  } | tee -a "${row_log}"

  for target in "${TARGETS[@]}"; do
    in_dir="${DATA_ROOT}/${target}/${GEOMETRY}"
    out_dir="${OUTPUT_ROOT}/clf-${clf_gen}/${target}/${GEOMETRY}/predictions"
    mkdir -p "${out_dir}"

    echo ">>> SCORE ${paper_label} -> ${target}" | tee -a "${row_log}"
    echo "    input  : ${in_dir}" | tee -a "${row_log}"
    echo "    output : ${out_dir}" | tee -a "${row_log}"

    extra=(
      --model-pickle "${model_pickle}"
      --embedding "${embedding}"
      --max-len "${MAX_LEN}"
    )
    [ -n "${THRESHOLD}" ] && extra+=(--threshold "${THRESHOLD}")
    [ -n "${DEVICE:-}" ] && extra+=(--device "${DEVICE}")

    python src/app/agc_detector.py \
      --input-dir "${in_dir}" \
      --out-dir "${out_dir}" \
      "${extra[@]}" \
      2>&1 | tee -a "${row_log}"

    n_pred="$(find "${out_dir}" -maxdepth 1 -type f -name 'mixed_sample_*.predictions.tsv' | wc -l | tr -d ' ')"
    if [ "${n_pred}" -ne "${EXPECTED_MIXED_FILES}" ]; then
      echo "[ERROR] ${paper_label} -> ${target}: expected ${EXPECTED_MIXED_FILES} prediction TSVs, found ${n_pred}" | tee -a "${row_log}" >&2
      exit 4
    fi

    echo "    prediction TSV audit: ${n_pred}/${EXPECTED_MIXED_FILES} PASS" | tee -a "${row_log}"
    echo | tee -a "${row_log}"
    cell_count=$((cell_count + 1))
  done

  # Reuse the existing Java log summarizer logic if its source is available.
  # This is optional for scoring correctness; the prediction TSVs remain the
  # authoritative outputs for the final AUROC matrix.
  SUMMARY_DIR="${SCRIPT_DIR}/compute-agc-transfer-summary"
  if [ -f "${SUMMARY_DIR}/LogSummarizer.java" ]; then
    if [ ! -f "${SUMMARY_DIR}/LogSummarizer.class" ]; then
      javac -encoding UTF-8 -d "${SUMMARY_DIR}" "${SUMMARY_DIR}/LogSummarizer.java"
    fi
    row_summary="${RUN_LOG_DIR}/summary_${clf_gen}.txt"
    echo ">>> Row summary for ${paper_label}" | tee -a "${row_log}"
    java -cp "${SUMMARY_DIR}" LogSummarizer "${row_log}" | tee "${row_summary}"
    echo "    summary file: ${row_summary}" | tee -a "${row_log}"
  else
    echo "[WARN] LogSummarizer.java not found; skipping optional row-log summary." | tee -a "${row_log}"
  fi

done

if [ "${cell_count}" -ne 25 ]; then
  echo "[ERROR] Expected 25 completed matrix cells, observed ${cell_count}" >&2
  exit 5
fi

echo "========================================================================="
echo " COMPLETE"
echo " Matrix cells   : ${cell_count}/25"
echo " Output root    : ${OUTPUT_ROOT}"
echo " Manifest       : ${MANIFEST}"
echo " Log directory  : ${RUN_LOG_DIR}"
echo " Finished       : $(date -Is)"
echo "========================================================================="
