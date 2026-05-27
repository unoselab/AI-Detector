# Step 0
# ---
cd ~/project-workspace/ai_detector/src

GEN_MAX_NUM=7000 \
GEN_TEMPERATURE=0.0 \
GEN_MODEL="gpt-oss" \
./run0a-generate-llm-api.sh

# Step 1 
# ---
# MODEL_NAME="gpt-oss" \
# MODEL_DIR="output/CodeSearchNet/gpt-oss-7000-tp0.0" \
# INPUT_FILE="output/CodeSearchNet/gpt-oss-7000-tp0.0/outputs-512token.txt" \
# PREFIX="codesearchnet_gpt-oss_python" \
# DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax" \
# N_SMALL=400 \
# N_LARGE=4500 \
# SEED=42 \
# bash run0b-find-validsyntax-mgc.sh

