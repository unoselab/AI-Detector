# Step 1
# ---
# cd ~/project-workspace/ai_detector/src

# INPUT_FILE="output/CodeSearchNet/starcoder2-15b-instruct-v0.1-5000-tp0.2/outputs-512token.txt" \
# DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/starcoder2-15b-instruct-v0.1/validsyntax_5000" \
# N_SMALL=400 \
# N_LARGE=4500 \
# SEED=42 \
# ./run0b-find-validsyntax-mgc.sh

# Step 2
# ---
cd ~/project-workspace/ai_detector/src

MODEL_NAME="starcoder2-15b-instruct-v0.1"
PREFIX="codesearchnet_${MODEL_NAME}_python"

INPUT_CSV="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_5000/${PREFIX}_merged_4500.csv" \
OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/${MODEL_NAME}/validsyntax_4500_complexity" \
SIZES="4500" \
./run0d-build-complexity-sweep-pairs.sh