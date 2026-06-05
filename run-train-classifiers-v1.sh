# Step 0
# ---
# cd ~/project-workspace/ai_detector/src

# INPUT_FILE="output/CodeSearchNet/starcoder2-15b-instruct-v0.1-5000-tp0.2/outputs-512token.txt" \
# DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/starcoder2-15b-instruct-v0.1/validsyntax_5000" \
# N_SMALL=400 \
# N_LARGE=4500 \
# SEED=42 \
# ./run0b-find-validsyntax-mgc.sh
# ==========================================
# Step 0 - extra generation
# ---
DRY_RUN=1 \
CUDA_VISIBLE_DEVICES="1" \
GEN_MODEL="starcoder2-15b" \
GEN_MODEL_HF="bigcode/starcoder2-15b" \
bash run0a-generate-more.sh
# cd ~/project-workspace/ai_detector/src
# bash run0a-generate-more.sh


# Step 1
# ---
# cd ~/project-workspace/ai_detector/src

# MODEL_NAME="starcoder2-15b-instruct-v0.1"
# PREFIX="codesearchnet_${MODEL_NAME}_python"

# INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_5000/${PREFIX}_merged_4500.csv" \
# OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
# SIZES="4500" \
# ./run0d-build-complexity-sweep-pairs.sh

# Step 2
# ---
# cd ~/project-workspace/ai_detector/src

# MODEL_NAME="starcoder2-15b-instruct-v0.1"

# INPUT_DIR="data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
# OUT_BASELINE="data_codesearchnet/${MODEL_NAME}/ast_4500_complexity" \
# ./run1-ast-generator.sh baseline

# Step 3
# ---
# cd ~/project-workspace/ai_detector/src

# MODEL_NAME="starcoder2-15b-instruct-v0.1"

# AST_BASELINE_DIR="${PWD}/code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/ast_4500_complexity" \
# OUT_BASELINE="data_codesearchnet/embeddings/${MODEL_NAME}_4500_complexity_maxlen2048" \
# ./run2-generate-embeddings.sh baseline

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

# Step 5 (b)
# ---
# cd ~/project-workspace/ai_detector/src

# MODEL_NAME="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048" \
# ./run4a-train-classifiers-allmodels.sh

# Step 5 (a)
# ---
# cd ~/project-workspace/ai_detector/src

# MODEL_NAME="starcoder2-15b-instruct-v0.1_complexity_fixedtest_maxlen2048" \
# MODELS="lr svm mlp rf gb knn dt et ada hgb xgb" \
# ./run4a-train-classifiers-allmodels.sh
