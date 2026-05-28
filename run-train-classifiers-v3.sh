# Step 0
# ---
# conda activate aidetector-gen
# cd ~/project-workspace/ai_detector/src
# GEN_MODEL="starcoder2-7b" \
# GEN_MODEL_HF="bigcode/starcoder2-7b" \
# GEN_TEMPERATURE=0.2 \
# GEN_MAX_LENGTH=512 \
# GEN_MAX_NUM=7000 \
# GEN_BATCH_SIZE=1 \
# bash run0a-generate.sh
# ==========================================
# Step 1
# ---
# conda activate aidetector
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="starcoder2-7b" \
# MODEL_DIR="output/CodeSearchNet/starcoder2-7b-7000-tp0.2" \
# INPUT_FILE="output/CodeSearchNet/starcoder2-7b-7000-tp0.2/outputs.txt" \
# PREFIX="codesearchnet_starcoder2-7b_python" \
# DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/starcoder2-7b/validsyntax" \
# N_SMALL=400 \
# N_LARGE=4500 \
# SEED=42 \
# bash run0b-find-validsyntax-mgc.sh

rm /home/user1-system12/project-workspace/ai_detector/src/code-analyzer-tree-sitter/data_codesearchnet/starcoder2-7b/validsyntax/codesearchnet_starcoder2-7b_python_merged.csv

# ==============================================
# Step 2
# ---
cd ~/project-workspace/ai_detector
MODEL_NAME="starcoder2-7b" \
INPUT_DIR="data_codesearchnet/starcoder2-7b/validsyntax" \
OUT_BASELINE="data_codesearchnet/starcoder2-7b/ast" \
bash src/run1-ast-generator.sh baseline
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="starcoder2-15b-instruct-v0.1"
# PREFIX="codesearchnet_${MODEL_NAME}_python"
# INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_5000/${PREFIX}_merged_4500.csv" \
# OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
# SIZES="4500" \
# ./run0d-build-complexity-sweep-pairs.sh
# ==============================================
# Step 2
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="starcoder2-15b-instruct-v0.1"
# INPUT_DIR="data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
# OUT_BASELINE="data_codesearchnet/${MODEL_NAME}/ast_4500_complexity" \
# ./run1-ast-generator.sh baseline
# ==============================================
# Step 3
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="starcoder2-15b-instruct-v0.1"
# AST_BASELINE_DIR="${PWD}/code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/ast_4500_complexity" \
# OUT_BASELINE="data_codesearchnet/embeddings/${MODEL_NAME}_4500_complexity_maxlen2048" \
# ./run2-generate-embeddings.sh baseline
# ==============================================
# Step 4
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="starcoder2-15b-instruct-v0.1"
# PREFIX="codesearchnet_${MODEL_NAME}_python"
# EXP_NAME="${MODEL_NAME}_4500_complexity_stratified_maxlen2048"
# python ml_embeddings/split_complexity_stratified.py \
#   --input-csv "ml_embeddings/data_codesearchnet/embeddings/${MODEL_NAME}_4500_complexity_maxlen2048/${PREFIX}_merged_4500.csv" \
#   --complexity-report "code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity/${PREFIX}_complexity_sweep_candidate_report.csv" \
#   --output-dir "ml_embeddings/data_codesearchnet/splits/${EXP_NAME}" \
#   --dataset-name "${PREFIX}_merged_4500" \
#   --seed 42 \
#   --block-size 10 \
#   --train-per-block 8 \
#   --dev-per-block 1
# ==============================================
# Step 5 (b)
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048" \
# ./run4a-train-classifiers-allmodels.sh
# ==============================================
# Step 5 (a)
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="starcoder2-15b-instruct-v0.1_complexity_fixedtest_maxlen2048" \
# MODELS="lr svm mlp rf gb knn dt et ada hgb xgb" \
# ./run4a-train-classifiers-allmodels.sh
