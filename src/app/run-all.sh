# Case 1
# src/ml_embeddings/data_codesearchnet/splits/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_4500/test_.csv
# ========================================
# Step 1: build test dataset
# ---
# INPUT_CSV="src/ml_embeddings/data_codesearchnet/splits/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_4500/test_.csv" \
# OUT_DIR="src/app/data_mixed_samples/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/50x6" \
# bash src/app/run0-build-mixed-samples.sh
# ========================================
# Step 2: prediction
# ---
EXP_NAME="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048" \
bash src/app/run1-agc-detector.sh
# ========================================
# Step 3: test
# ---
EXP_NAME="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048"
python src/app/compute_metrics_mixedcode.py \
  --pred-dir src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions \
  --out-csv src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv