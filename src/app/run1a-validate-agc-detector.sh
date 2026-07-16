#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1a-validate-agc-detector.sh
# -----------------------------------------------------------------------------
# Validate one of two fixed paper configurations through
# analyze_did_python_snapshots.py:
#   1. CodeLlama-7B + SVM + AST
#   2. GPT-OSS-120B + MLP + AST
#
# Usage:
#   bash src/app/run1a-validate-agc-detector.sh svm_ast
#   bash src/app/run1a-validate-agc-detector.sh mlp_ast
#
# Optional:
#   DEVICE=cuda:0 bash src/app/run1a-validate-agc-detector.sh mlp_ast
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PY_SCRIPT="src/app/py/analyze_did_python_snapshots.py"
PROFILE="${1:-${VALIDATION_PROFILE:-svm_ast}}"

case "${PROFILE}" in
  svm_ast)
    EXPERIMENT="codellama-7b_4500_complexity_stratified_maxlen2048"
    CLASSIFIER="svm"
    MODEL_PICKLE="src/ml_embeddings/data_codesearchnet/models/${EXPERIMENT}/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"
    MODEL_KEY="codesearchnet_codellama-7b_python_merged_4500ast_"
    SCORE_MODE="decision"
    TEST_CSV="src/ml_embeddings/data_codesearchnet/splits/${EXPERIMENT}/codesearchnet_codellama-7b_python_merged_4500/test_.csv"
    EXPECTED_ACC="0.7178"
    EXPECTED_HUMAN_F1="0.7221"
    EXPECTED_AI_F1="0.7133"
    EXPECTED_AVG_F1="0.7177"
    EXPECTED_AUROC="0.7950"
    ;;
  mlp_ast)
    EXPERIMENT="gpt-oss_4500_complexity_stratified_maxlen2048"
    CLASSIFIER="mlp"
    MODEL_PICKLE="src/ml_embeddings/data_codesearchnet/models/${EXPERIMENT}/tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_maxlen2048_mlp_20260527_192034.pkl"
    MODEL_KEY="codesearchnet_gpt-oss_python_merged_4500ast_"
    SCORE_MODE="proba"
    TEST_CSV="src/ml_embeddings/data_codesearchnet/splits/${EXPERIMENT}/codesearchnet_gpt-oss_python_merged_4500/test_.csv"
    EXPECTED_ACC="0.8089"
    EXPECTED_HUMAN_F1="0.8072"
    EXPECTED_AI_F1="0.8106"
    EXPECTED_AVG_F1="0.8089"
    EXPECTED_AUROC="0.8837"
    ;;
  *)
    echo "[ERROR] unsupported profile: ${PROFILE}" >&2
    echo "        Expected: svm_ast or mlp_ast" >&2
    exit 2
    ;;
esac

REPRESENTATION="ast"
MAX_LEN="2048"
OUT_ROOT="src/app/data_did_agc_analysis/${EXPERIMENT}_${CLASSIFIER}_${REPRESENTATION}/strict"

for path in "${PY_SCRIPT}" "${TEST_CSV}" "${MODEL_PICKLE}"; do
  if [[ ! -f "${path}" ]]; then
    echo "[ERROR] required file not found: ${path}" >&2
    exit 2
  fi
done

TS="$(date +'%Y%m%d_%H%M%S')"
LOG_FILE="src/logs/run1a-validate-agc-detector_${PROFILE}_${TS}.log"
mkdir -p "$(dirname "${LOG_FILE}")"
exec > >(tee -a "${LOG_FILE}") 2>&1

cat <<INFO
============================================================
 run1a-validate-agc-detector.sh
   profile        : ${PROFILE}
   experiment     : ${EXPERIMENT}
   classifier     : ${CLASSIFIER}
   representation : ${REPRESENTATION}
   score mode     : ${SCORE_MODE}
   test csv       : ${TEST_CSV}
   model pickle   : ${MODEL_PICKLE}
   model key      : ${MODEL_KEY}
   max len        : ${MAX_LEN}
   output root    : ${OUT_ROOT}
   device         : ${DEVICE:-<auto>}
   log file       : ${LOG_FILE}
============================================================
INFO

ARGS=(
  --experiment "${EXPERIMENT}"
  --classifier "${CLASSIFIER}"
  --representation "${REPRESENTATION}"
  --model-pickle "${MODEL_PICKLE}"
  --expected-model-key "${MODEL_KEY}"
  --expected-score-mode "${SCORE_MODE}"
  --max-len "${MAX_LEN}"
  --validation-test-csv "${TEST_CSV}"
  --validation-only
  --expected-test-rows 900
  --expected-acc "${EXPECTED_ACC}"
  --expected-human-f1 "${EXPECTED_HUMAN_F1}"
  --expected-ai-f1 "${EXPECTED_AI_F1}"
  --expected-avg-f1 "${EXPECTED_AVG_F1}"
  --expected-auroc "${EXPECTED_AUROC}"
  --output-root "${OUT_ROOT}"
)

if [[ -n "${DEVICE:-}" ]]; then
  ARGS+=(--device "${DEVICE}")
fi

"${PYTHON_BIN}" "${PY_SCRIPT}" "${ARGS[@]}"

echo "Log: ${LOG_FILE}"
