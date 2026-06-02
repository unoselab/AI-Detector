cd src/app/   # run once, from repo root

for EXP_NAME in \
  "starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048" \
  "codellama-7b_4500_complexity_stratified_maxlen2048" \
  "gemma_4500_complexity_stratified_maxlen2048" \
  "gpt-oss_4500_complexity_stratified_maxlen2048" \
  "starcoder2-7b_4500_complexity_stratified_maxlen2048" ; do

  echo "==== ${EXP_NAME} ===="
  python ./compute_metrics_mixedcode.py \
    --pred-dir ./data_mixed_samples/${EXP_NAME}/50x6/predictions \
    --out-csv  ./data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv \
    --roc-csv  ./data_mixed_samples/${EXP_NAME}/50x6/predictions/roc_curve.csv
done

python -c "
import glob
import pandas as pd
from pathlib import Path

all_dfs = []
output_file = 'data_mixed_samples/combined_block_metrics.csv'

for f in sorted(glob.glob('data_mixed_samples/*/50x6/predictions/block_metrics.csv')):
    model_dir = Path(f).parts[1]          # directory after data_mixed_samples
    model_name = model_dir.split('_4500')[0]
    df = pd.read_csv(f)
    df.insert(0, 'model', model_name)
    all_dfs.append(df)

combined_df = pd.concat(all_dfs, ignore_index=True)
combined_df.to_csv(output_file, index=False)
print(f'Saved to: {output_file}, Rows: {len(combined_df)}, Files combined: {len(all_dfs)}')
"

python -c "
import glob
import pandas as pd
from pathlib import Path

all_dfs = []
input_pattern = 'data_mixed_samples/*/50x6/predictions/roc_curve.csv'
output_file = 'data_mixed_samples/combined_roc_curve.csv'

for f in sorted(glob.glob(input_pattern)):
    parts = Path(f).parts
    model_dir = parts[parts.index('data_mixed_samples') + 1]
    model_name = model_dir.split('_4500')[0]

    df = pd.read_csv(f)
    df.insert(0, 'model', model_name)
    all_dfs.append(df)

if not all_dfs:
    raise FileNotFoundError(f'No files matched: {input_pattern}')

combined_df = pd.concat(all_dfs, ignore_index=True)
combined_df.to_csv(output_file, index=False)

print(f'Saved to: {output_file}, Rows: {len(combined_df)}, Files combined: {len(all_dfs)}')
"


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
# cd ~/project-workspace/ai_detector/src/app/compute-agc-transfer-summary
# java MatrixSummarizer ../../../src/logs/
