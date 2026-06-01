#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run4-compute-agc-transfer-allclassifiers.sh
# -----------------------------------------------------------------------------
# Wrapper script to sequentially evaluate all 5 distinct generators' classifiers
# across cross-domain datasets by overriding run3-compute-agc-transfer.sh variables.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# Ensure output directories exist for unified tracking
mkdir -p src/logs

echo "========================================================================="
echo " Starting Global Cross-Generator Transfer Evaluation Framework"
echo "========================================================================="

# Define the evaluation matrices for the 5 target classifiers
# Columns: CLF_GEN | CLF_EXP | ALGO | MODEL_PICKLE
CLASSIFIERS=(
    "codellama-7b|codellama-7b_4500_complexity_stratified_maxlen2048|svm|src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"
    "gemma|gemma_4500_complexity_stratified_maxlen2048|svm|src/ml_embeddings/data_codesearchnet/models/gemma_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gemma_4500_complexity_stratified_maxlen2048_svm_20260529_163611.pkl"
    "gpt-oss|gpt-oss_4500_complexity_stratified_maxlen2048|svm|src/ml_embeddings/data_codesearchnet/models/gpt-oss_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_maxlen2048_svm_20260527_191841.pkl"
    "starcoder2-15b-instruct-v0.1|starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048|svm|src/ml_embeddings/data_codesearchnet/models/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048_svm_20260526_033005.pkl"
    "starcoder2-7b|starcoder2-7b_4500_complexity_stratified_maxlen2048|mlp|src/ml_embeddings/data_codesearchnet/models/starcoder2-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_starcoder2-7b_4500_complexity_stratified_maxlen2048_mlp_20260528_142140.pkl"
)

# Loop over each trained model configuration systematically
for entry in "${CLASSIFIERS[@]}"; do
    IFS='|' read -r CLF_GEN CLF_EXP ALGO MODEL_PICKLE <<< "${entry}"
    
    TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
    LOG_FILE="src/logs/transfer_run_${CLF_GEN}_${TIMESTAMP}.log"
    
    echo ">>> Launching pipeline for Pinned Classifier: [${CLF_GEN}]"
    echo "    Experiment Directory : ${CLF_EXP}"
    echo "    Selected Model Pickle: ${MODEL_PICKLE}"
    echo "    Logging output to    : ${LOG_FILE}"
    
    # Export parameters into environment scope to override run3 defaults securely
    export CLF_GEN
    export CLF_EXP
    export ALGO
    export MODEL_PICKLE
    export INCLUDE_OWN=1 # Ensure full cross-validation grid is captured
    
    # Execute the downstream runner script and redirect output to the designated log
    bash src/app/run3-compute-agc-transfer.sh > "${LOG_FILE}" 2>&1
    
    echo "✓ [Success] Completed evaluation loop for [${CLF_GEN}]."
    echo "-------------------------------------------------------------------------"
done

echo "========================================================================="
echo " All transfer evaluation matrix workflows finalized successfully."
echo "========================================================================="