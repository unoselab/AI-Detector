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
# ==========================================
# Step 1
# ---
## conda activate aidetector
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="codellama-7b" \
# INPUT_FILE="output/CodeSearchNet/CodeLlama-7b-hf-7000-tp0.2/outputs.txt" \
# DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/validsyntax" \
# PREFIX="codesearchnet_codellama-7b_python" \
# N_SMALL=400 \
# N_LARGE=4500 \
# bash run0b-find-validsyntax-mgc.sh
# ==========================================
# Step 1a
# ---
# cd ~/project-workspace/ai_detector/src
# bash run0a-generate-more.sh
# ==========================================
# Step 2: checking validity
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME=CodeLlama-7b-hf \
# MODEL_DIR=output/CodeSearchNet/CodeLlama-7b-hf-9000-tp0.2 \
# INPUT_FILE=output/CodeSearchNet/CodeLlama-7b-hf-9000-tp0.2/outputs.txt \
# PREFIX=codesearchnet_codellama-7b_python \
# N_SMALL=400 N_LARGE=4500 SEED=42 \
# bash run0b-find-validsyntax-mgc.sh
# ==============================================
# Step 3: : generating ASTs.
# ---
## conda activate aidetector
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="codellama-7b" \
# INPUT_FILE="data_codesearchnet/codellama-7b/validsyntax/codesearchnet_codellama-7b_python_merged_4500.csv" \
# OUT_BASELINE="data_codesearchnet/codellama-7b/ast_4500" \
# bash run1-ast-generator.sh baseline
# ==============================================
# Step 4: generating embeddings
# ---
# cd ~/project-workspace/ai_detector/
# MODEL_NAME="codellama-7b" \
# AST_BASELINE_DIR="${PWD}/src/code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/ast_4500" \
# OUT_BASELINE="data_codesearchnet/embeddings/codellama-7b_4500_maxlen2048" \
# MAX_LEN=2048 \
# BATCH_SIZE=32 \
# OVERWRITE=1 \
# bash src/run2-generate-embeddings.sh baseline
# ==============================================
# Step 5: calculating complexity
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="codellama-7b"
# PREFIX="codesearchnet_${MODEL_NAME}_python"
# MODEL_NAME="${MODEL_NAME}" \
# PREFIX="${PREFIX}" \
# INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax/${PREFIX}_merged_4500.csv" \
# OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
# SIZES="4500" \
# bash run0d-build-complexity-sweep-pairs.sh
# ==============================================
# Step 6: spliting
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="codellama-7b" \
# INPUT_CSV="ml_embeddings/data_codesearchnet/embeddings/codellama-7b_4500_maxlen2048/codesearchnet_codellama-7b_python_merged_4500.csv" \
# ./run3c-split-complexity-stratified.sh
# ==============================================
# Step 7: training
# ---
cd ~/project-workspace/ai_detector/src
MODEL_NAME="codellama-7b_4500_complexity_stratified_maxlen2048" \
bash run4a-train-classifiers-allmodels.sh
