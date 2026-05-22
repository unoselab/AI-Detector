cd /home/user1-system12/project-workspace/ai_detector/src

for p in 0.80 0.85 0.90; do
  echo "============================================================"
  echo "Running high-ai-precision sweep: target=$p"
  echo "============================================================"

  MODEL_NAME=starcoder2-15b-instruct-v0.1 \
  OBJECTIVE=high-ai-precision \
  TARGET_AI_PRECISION="$p" \
  OUT_DIR="data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1_aiP${p}" \
  bash run5-threshold-sweep.sh svm
done