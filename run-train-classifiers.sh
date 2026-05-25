cd ~/project-workspace/ai_detector/src

INPUT_FILE="output/CodeSearchNet/starcoder2-15b-instruct-v0.1-5000-tp0.2/outputs-512token.txt" \
DATA_OUT_DIR="code-analyzer-tree-sitter/data_codesearchnet/starcoder2-15b-instruct-v0.1/validsyntax_5000" \
N_SMALL=400 \
N_LARGE=4500 \
SEED=42 \
./run0b-find-validsyntax-mgc.sh