# Step 0
# ---
# cd ~/project-workspace/ai_detector/src
# GEN_MAX_NUM=7000 \
# GEN_TEMPERATURE=0.0 \
# GEN_MODEL="gpt-oss" \
# ./run0a-generate-llm-api.sh
# ==============================================
# Step 0a
cd ~/project-workspace/ai_detector
python src/code-generate-llm/generate-more.py \
  src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax/codesearchnet_gpt-oss_python_merged_4500.csv \
  4500 \
  --codesearchnet-root data/CodeSearchNet \
  --model-name gpt-oss \
  --retry-forever

# ==============================================
# Step 1 
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gpt-oss" \
# MODEL_DIR="output/CodeSearchNet/gpt-oss-7000-tp0.0" \
# INPUT_FILE="output/CodeSearchNet/gpt-oss-7000-tp0.0/outputs-512token.txt" \
# PREFIX="codesearchnet_gpt-oss_python" \
# DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax" \
# N_SMALL=400 \
# N_LARGE=4500 \
# SEED=42 \
# bash run0b-find-validsyntax-mgc.sh
# ==============================================
# Step 2
# ---
# cd ~/project-workspace/ai_detector
# MODEL_NAME="gpt-oss" \
# INPUT_DIR="data_codesearchnet/gpt-oss/validsyntax" \
# OUT_BASELINE="data_codesearchnet/gpt-oss/ast" \
# bash src/run1-ast-generator.sh baseline
# ==============================================
# Step 3
# ---
# cd ~/project-workspace/ai_detector
# MODEL_NAME="gpt-oss" \
# AST_BASELINE_DIR="${PWD}/src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/ast" \
# OUT_BASELINE="data_codesearchnet/embeddings/gpt-oss_maxlen2048_baseline" \
# MAX_LEN=2048 \
# BATCH_SIZE=32 \
# OVERWRITE=1 \
# bash src/run2-generate-embeddings.sh baseline
# ==============================================
# Step 4
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gpt-oss"
# PREFIX="codesearchnet_${MODEL_NAME}_python"
# MODEL_NAME="${MODEL_NAME}" \
# PREFIX="${PREFIX}" \
# INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax/${PREFIX}_merged_4500.csv" \
# OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
# SIZES="4500" \
# ./run0d-build-complexity-sweep-pairs.sh
# ==============================================
# Step 5
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gpt-oss"
# PREFIX="codesearchnet_${MODEL_NAME}_python"
# EXP_NAME="${MODEL_NAME}_4500_complexity_stratified_maxlen2048"
# python ml_embeddings/split_complexity_stratified.py \
#   --input-csv "ml_embeddings/data_codesearchnet/embeddings/${MODEL_NAME}_maxlen2048_baseline/${PREFIX}_merged_4500.csv" \
#   --complexity-report "code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity/${PREFIX}_complexity_sweep_candidate_report.csv" \
#   --output-dir "ml_embeddings/data_codesearchnet/splits/${EXP_NAME}" \
#   --dataset-name "${PREFIX}_merged_4500" \
#   --seed 42 \
#   --block-size 10 \
#   --train-per-block 8 \
#   --dev-per-block 1
# ==============================================
# Step 6
# ---
# cd ~/project-workspace/ai_detector/src
# MODEL_NAME="gpt-oss_4500_complexity_stratified_maxlen2048" \
# MODELS="lr svm mlp rf gb knn dt et ada hgb xgb" \
# ./run4a-train-classifiers-allmodels.sh
