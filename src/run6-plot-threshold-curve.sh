CSV="data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1/svm_summary_detail.csv"
DATASET="codesearchnet_starcoder2-15b-instruct-v0.1_python_merged"
SPLIT="both" # test, dev, or both

python plot_threshold_curve.py \
  --csv "${CSV}" \
  --dataset "${DATASET}" \
  --emb ast_ \
  --metric ai_f1 \
  --split "${SPLIT}"
