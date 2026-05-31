# Case 1
# src/ml_embeddings/data_codesearchnet/splits/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_4500/test_.csv
# ---
# Step 1
# INPUT_CSV="src/ml_embeddings/data_codesearchnet/splits/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_4500/test_.csv" \
# OUT_DIR="src/app/data_mixed_samples/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/50x6" \
# bash src/app/run0-build-mixed-samples.sh
# 
# Step 2
# ---
EXP_NAME="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048" \
MODEL_PICKLE="src/ml_embeddings/data_codesearchnet/models/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048_svm_20260526_033005.pkl" \
bash src/app/run1-agc-detector.sh