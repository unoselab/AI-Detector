# Step 0
# ---
## conda activate aidetector-gen
# cd ~/project-workspace/ai_detector/src
# GEN_MODEL="codellama-7b" \
# GEN_MODEL_HF="codellama/CodeLlama-7b-hf" \
# GEN_TEMPERATURE=0.2 \
# GEN_MAX_LENGTH=512 \
# GEN_MAX_NUM=7000 \
# GEN_BATCH_SIZE=1 \
# bash run0a-generate.sh
## conda activate aidetector-gen
# cd ~/project-workspace/ai_detector/src
# GEN_MODEL="codellama-7b" \
# GEN_MODEL_HF="codellama/CodeLlama-7b-hf" \
# GEN_TEMPERATURE=0.2 \
# GEN_MAX_LENGTH=512 \
# GEN_MAX_NUM=7000 \
# GEN_BATCH_SIZE=1 \
# bash run0a-generate.sh
# ==========================================
# Step 0a
cd ~/project-workspace/ai_detector
DRY_RUN=1 bash src/run0a-generate-llm-api-more-gemma.sh

# ==========================================
# Step 1
# ---
## conda activate aidetector
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gemma" \
# MODEL_DIR="output/CodeSearchNet/gemma-9000-tp0.0" \
# INPUT_FILE="output/CodeSearchNet/gemma-9000-tp0.0/outputs-512token.txt" \
# PREFIX="codesearchnet_gemma_python" \
# DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/gemma/validsyntax" \
# N_SMALL=400 \
# N_LARGE=4500 \
# SEED=42 \
# bash run0b-find-validsyntax-mgc.sh
# 
# rm /home/user1-system12/project-workspace/ai_detector/src/code-analyzer-tree-sitter/data_codesearchnet/starcoder2-7b/validsyntax/codesearchnet_starcoder2-7b_python_merged.csv
# 
# ==============================================
# Step 2
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gemma" \
# INPUT_DIR="data_codesearchnet/gemma/validsyntax" \
# OUT_BASELINE="data_codesearchnet/gemma/ast" \
# bash run1-ast-generator.sh baseline
# ==============================================
# Step 3
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gemma"
# PREFIX="codesearchnet_${MODEL_NAME}_python"
# MODEL_NAME="${MODEL_NAME}" \
# PREFIX="${PREFIX}" \
# INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax/${PREFIX}_merged_4500.csv" \
# OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
# SIZES="4500" \
# ./run0d-build-complexity-sweep-pairs.sh
# ---
## will create `code-analyzer-tree-sitter/data_../.._complexity_sweep_candidate_report.csv`
# ==============================================
# Step 4
# ---
# cd ~/project-workspace/ai_detector
# MODEL_NAME="gemma" \
# AST_BASELINE_DIR="${PWD}/src/code-analyzer-tree-sitter/data_codesearchnet/gemma/ast" \
# OUT_BASELINE="data_codesearchnet/embeddings/gemma_maxlen2048_baseline" \
# MAX_LEN=2048 \
# BATCH_SIZE=32 \
# OVERWRITE=1 \
# bash src/run2-generate-embeddings.sh baseline
# ==============================================
# Step 5
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gemma" \
# ./run3c-split-complexity-stratified.sh
# ==============================================
# Step 6
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gemma_4500_complexity_stratified_maxlen2048" \
# MODELS="lr svm mlp rf gb knn dt et ada hgb xgb" \
# ./run4a-train-classifiers-allmodels.sh
# cd ~/project-workspace/ai_detector/src 
# MODEL_NAME="starcoder2-7b_4500_complexity_stratified_maxlen2048" \
# MODELS="lr svm mlp rf gb knn dt et ada hgb xgb" \
# ./run4a-train-classifiers-allmodels.sh
#