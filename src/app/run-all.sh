# Case 1 - StartCoder2-15B
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
# EXP_NAME="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048" \
# bash src/app/run1-agc-detector.sh
# ========================================
# Step 3: test
# ---
# EXP_NAME="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048"
# python src/app/compute_metrics_mixedcode.py \
#   --pred-dir src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions \
#   --out-csv src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv
# ========================================
# Case 2 — CodeLlama-7B
# EXP_NAME="codellama-7b_4500_complexity_stratified_maxlen2048"
# ========================================
# Step 1: build test dataset
# INPUT_CSV="src/ml_embeddings/data_codesearchnet/splits/${EXP_NAME}/codesearchnet_codellama-7b_python_merged_4500/test_.csv" \
# OUT_DIR="src/app/data_mixed_samples/${EXP_NAME}/50x6" \
# bash src/app/run0-build-mixed-samples.sh
# Step 2: prediction
# EXP_NAME="codellama-7b_4500_complexity_stratified_maxlen2048" \
# bash src/app/run1-agc-detector.sh
# Step 3: test
# python src/app/compute_metrics_mixedcode.py \
#   --pred-dir src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions \
#   --out-csv  src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv
# ========================================
# Case 3 — Gemma
# ---
# EXP_NAME="gemma_4500_complexity_stratified_maxlen2048"
# # Step 1: build test dataset
# INPUT_CSV="src/ml_embeddings/data_codesearchnet/splits/${EXP_NAME}/codesearchnet_gemma_python_merged_4500/test_.csv" \
# OUT_DIR="src/app/data_mixed_samples/${EXP_NAME}/50x6" \
# bash src/app/run0-build-mixed-samples.sh
# # Step 2: prediction
# EXP_NAME="gemma_4500_complexity_stratified_maxlen2048" \
# bash src/app/run1-agc-detector.sh
# # Step 3: test
# python src/app/compute_metrics_mixedcode.py \
#   --pred-dir src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions \
#   --out-csv  src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv
# ========================================
# Case 4 — GPT-OSS
# ---
# MODEL_NAME="GPT-OSS" 
# EXP_NAME="gpt-oss_4500_complexity_stratified_maxlen2048"
# # Step 1
# MODEL_NAME="${MODEL_NAME}" \
# INPUT_CSV="src/ml_embeddings/data_codesearchnet/splits/${EXP_NAME}/codesearchnet_gpt-oss_python_merged_4500/test_.csv" \
# OUT_DIR="src/app/data_mixed_samples/${EXP_NAME}/50x6" \
# bash src/app/run0-build-mixed-samples.sh
# # Step 2
# MODEL_NAME="${MODEL_NAME}" \
# EXP_NAME="gpt-oss_4500_complexity_stratified_maxlen2048" \
# bash src/app/run1-agc-detector.sh
# # Step 3
# python src/app/compute_metrics_mixedcode.py \
#   --pred-dir src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions \
#   --out-csv  src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv
# ========================================
# # Case 5 — StarCoder2-7B
# # ---
# # Step 1
# MODEL_NAME="starcoder2-7b"
# EXP_NAME="starcoder2-7b_4500_complexity_stratified_maxlen2048"
# # Step 2
# MODEL_NAME="${MODEL_NAME}" \
# INPUT_CSV="src/ml_embeddings/data_codesearchnet/splits/${EXP_NAME}/codesearchnet_starcoder2-7b_python_merged_4500/test_.csv" \
# OUT_DIR="src/app/data_mixed_samples/${EXP_NAME}/50x6" \
# bash src/app/run0-build-mixed-samples.sh
# # Step 3
# MODEL_NAME="${MODEL_NAME}" \
# EXP_NAME="starcoder2-7b_4500_complexity_stratified_maxlen2048" \
# bash src/app/run1-agc-detector.sh
# # Step 4
# python src/app/compute_metrics_mixedcode.py \
#   --pred-dir src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions \
#   --out-csv  src/app/data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv
# ========================================
# 1. /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl
# 2. /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/models/gemma_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gemma_4500_complexity_stratified_maxlen2048_svm_20260529_163611.pkl
# 3. /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/models/gpt-oss_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_maxlen2048_svm_20260527_191841.pkl
# 4. /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/models/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048_svm_20260526_033005.pkl
# 5. /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/models/starcoder2-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_starcoder2-7b_4500_complexity_stratified_maxlen2048_mlp_20260528_142140.pkl
# ========================================
# Step 6
# Evaluate all 5 distinct generators' classifiers sequentially 
# across cross-domain datasets, computing the full 5x5 evaluation matrix
# with the matched diagonal (self-dataset performance profiles).

# bash src/app/run4-compute-agc-transfer-allclassifiers.sh

# ========================================
# Step 7 - Cross-generator domain transfer generalization performance (block-level accuracy)
cd ~/project-workspace/ai_detector/src/app/compute-agc-transfer-summary
java MatrixSummarizer ../../../src/logs/
