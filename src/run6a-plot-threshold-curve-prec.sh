cd /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings

python plot_agc_precision_curve.py \
  --detail-csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1_aiP0.90/svm_summary_detail.csv \
  --summary-csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1_aiP0.90/svm_summary.csv \
  --dataset codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_2700 \
  --emb ast_ \
  --split test


# python plot_agc_precision_curve.py \
#   --detail-csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1_aiP0.90/svm_summary_detail.csv \
#   --summary-csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1_aiP0.90/svm_summary.csv \
#   --dataset codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_2700 \
#   --emb ast_ \
#   --split both  