# =============================================================================
# Per-model block metrics -> combined CSVs for the in-distribution evaluation.
#
# This is the "matched" (diagonal) evaluation: each generator's detector scored
# on its OWN generator's mixed-sample test set. It runs AFTER the build (run0)
# and detector (run1) steps have populated each experiment's predictions/ dir
# with *.predictions.tsv files. Order matters: nothing here builds inputs.
#
# Produces, per experiment:
#   block_metrics.csv  HWC/AGC/avg P/R/F1 + accuracy + AUROC (one table)
#   roc_curve.csv      the (fpr, tpr, threshold) sweep for ROC plotting
# Then stitches all five experiments into two combined CSVs for figures/tables.
# =============================================================================

cd src/app/   # run once, from repo root. ALL paths below are relative to src/app,
              # so do NOT prefix them with src/app/ again (that double-prefix bug
              # would resolve to src/app/src/app/... and fail).

# Iterate the five experiment directories (one per generator). The EXP_NAME
# string is also the on-disk folder name produced by the build/detect steps;
# it encodes <model>_<dataset-size>_<sampling>_<maxlen>, e.g.
# "gpt-oss_4500_complexity_stratified_maxlen2048". Add/remove a line here to
# include/exclude a generator from the sweep.
for EXP_NAME in \
  "starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048" \
  "codellama-7b_4500_complexity_stratified_maxlen2048" \
  "gemma_4500_complexity_stratified_maxlen2048" \
  "gpt-oss_4500_complexity_stratified_maxlen2048" \
  "starcoder2-7b_4500_complexity_stratified_maxlen2048" ; do

  echo "==== ${EXP_NAME} ===="
  # Compute block-level metrics for this experiment. --pred-dir is the folder of
  # *.predictions.tsv written by agc_detector.py (50 samples x 6 blocks = 300
  # blocks). Both output CSVs are written back INTO that same predictions/ dir
  # so each experiment stays self-contained. The metrics script exits if the
  # predictions dir is missing/empty, so a skipped detector run surfaces here.
  python ./compute_metrics_mixedcode.py \
    --pred-dir ./data_mixed_samples/${EXP_NAME}/50x6/predictions \
    --out-csv  ./data_mixed_samples/${EXP_NAME}/50x6/predictions/block_metrics.csv \
    --roc-csv  ./data_mixed_samples/${EXP_NAME}/50x6/predictions/roc_curve.csv
done

# -----------------------------------------------------------------------------
# Stitch 1/2: combine every experiment's block_metrics.csv into one tidy CSV,
# tagging each row with a short model name. This combined file is the input to
# the AUROC/F1 figure scripts (e.g. plot_auroc.py).
# -----------------------------------------------------------------------------
python -c "
import glob
import pandas as pd
from pathlib import Path

all_dfs = []
output_file = 'data_mixed_samples/combined_block_metrics.csv'

# Glob every per-experiment metrics file. The '*' is the EXP_NAME directory.
for f in sorted(glob.glob('data_mixed_samples/*/50x6/predictions/block_metrics.csv')):
    # Path layout: data_mixed_samples / <EXP_NAME> / 50x6 / predictions / file.csv
    # parts[1] is the EXP_NAME directory (parts[0] == 'data_mixed_samples').
    model_dir = Path(f).parts[1]
    # Derive a short model tag by cutting at the dataset-size token '_4500'.
    # e.g. 'starcoder2-15b-instruct-v0.1_4500_..._maxlen2048' -> 'starcoder2-15b-instruct-v0.1'.
    # NOTE: this is hardcoded to the 4500-sample experiments; change '_4500'
    # if you sweep a different dataset size, or it will not shorten correctly.
    model_name = model_dir.split('_4500')[0]
    df = pd.read_csv(f)
    df.insert(0, 'model', model_name)   # prepend the model column for grouping
    all_dfs.append(df)

# Concatenate all experiments; one combined table keyed by 'model'.
combined_df = pd.concat(all_dfs, ignore_index=True)
combined_df.to_csv(output_file, index=False)
print(f'Saved to: {output_file}, Rows: {len(combined_df)}, Files combined: {len(all_dfs)}')
"

# -----------------------------------------------------------------------------
# Stitch 2/2: same idea for the ROC curve points (combined_roc_curve.csv), which
# feeds the ROC-overlay figure. Two robustness differences from Stitch 1:
#   * the EXP_NAME index is found via parts.index('data_mixed_samples')+1 rather
#     than a fixed parts[1], so it survives a longer/relative path prefix;
#   * it raises if nothing matched, instead of writing an empty file.
# -----------------------------------------------------------------------------
python -c "
import glob
import pandas as pd
from pathlib import Path

all_dfs = []
input_pattern = 'data_mixed_samples/*/50x6/predictions/roc_curve.csv'
output_file = 'data_mixed_samples/combined_roc_curve.csv'

for f in sorted(glob.glob(input_pattern)):
    parts = Path(f).parts
    # Locate the EXP_NAME directory relative to the 'data_mixed_samples' anchor,
    # so this works even if the path is prefixed differently than expected.
    model_dir = parts[parts.index('data_mixed_samples') + 1]
    model_name = model_dir.split('_4500')[0]   # short tag; see note in Stitch 1

    df = pd.read_csv(f)
    df.insert(0, 'model', model_name)
    all_dfs.append(df)

# Fail loudly if the glob matched nothing (e.g. roc_curve.csv never written
# because --roc-csv was omitted in the loop above) rather than silently
# producing an empty combined file.
if not all_dfs:
    raise FileNotFoundError(f'No files matched: {input_pattern}')

combined_df = pd.concat(all_dfs, ignore_index=True)
combined_df.to_csv(output_file, index=False)

print(f'Saved to: {output_file}, Rows: {len(combined_df)}, Files combined: {len(all_dfs)}')
"

# 
# Comment out below if the above code works.
# 


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
