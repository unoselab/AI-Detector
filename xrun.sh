python src/app/analyze_did_python_snapshots.py \
  --experiment gpt-oss_4500_complexity_stratified_maxlen2048 \
  --classifier mlp \
  --representation ast \
  --model-pickle src/ml_embeddings/data_codesearchnet/models/gpt-oss_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_maxlen2048_mlp_20260527_192034.pkl \
  --expected-model-key codesearchnet_gpt-oss_python_merged_4500ast_ \
  --expected-score-mode proba \
  --max-len 2048 \
  --validation-test-csv src/ml_embeddings/data_codesearchnet/splits/gpt-oss_4500_complexity_stratified_maxlen2048/codesearchnet_gpt-oss_python_merged_4500/test_.csv \
  --validation-only \
  --expected-test-rows 900 \
  --expected-acc 0.8089 \
  --expected-human-f1 0.8072 \
  --expected-ai-f1 0.8106 \
  --expected-avg-f1 0.8089 \
  --expected-auroc 0.8837 \
  --output-root src/app/data_did_agc_analysis/gpt-oss_4500_complexity_stratified_maxlen2048_mlp_ast/strict


========================================================================
analyze_did_python_snapshots.py
  experiment          : gpt-oss_4500_complexity_stratified_maxlen2048
  classifier          : mlp
  representation      : ast
  model pickle        : /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/models/gpt-oss_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_maxlen2048_mlp_20260527_192034.pkl
  expected model key  : codesearchnet_gpt-oss_python_merged_4500ast_
  expected score mode : proba
  max len             : 2048
  threshold           : <classifier default>
  dataset source      : treatment
  output root         : /home/user1-system12/project-workspace/ai_detector/src/app/data_did_agc_analysis/gpt-oss_4500_complexity_stratified_maxlen2048_mlp_ast/strict
  validation test CSV : /home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/splits/gpt-oss_4500_complexity_stratified_maxlen2048/codesearchnet_gpt-oss_python_merged_4500/test_.csv
  validation only     : True
========================================================================
Loading Salesforce/codet5p-110m-embedding on cuda ...
[validation] 100/900 rows scored
[validation] 200/900 rows scored
[validation] 300/900 rows scored
[validation] 400/900 rows scored
[validation] 500/900 rows scored
[validation] 600/900 rows scored
[validation] 700/900 rows scored
[validation] 800/900 rows scored
[validation] 900/900 rows scored

gpt-oss_4500_complexity_stratified_maxlen2048 MLP + AST validation
==================================================================
Test rows : 900
ACC       : 0.8089  expected 0.8089
Human F1  : 0.8072  expected 0.8072
AI F1     : 0.8106  expected 0.8106
Avg. F1   : 0.8089  expected 0.8089
AUROC     : 0.8842  expected 0.8837
Score mode: proba
Status    : FAIL
Predictions: /home/user1-system12/project-workspace/ai_detector/src/app/data_did_agc_analysis/gpt-oss_4500_complexity_stratified_maxlen2048_mlp_ast/strict/validation/validation_predictions.csv
Metrics    : /home/user1-system12/project-workspace/ai_detector/src/app/data_did_agc_analysis/gpt-oss_4500_complexity_stratified_maxlen2048_mlp_ast/strict/validation/validation_metrics.csv
Summary    : /home/user1-system12/project-workspace/ai_detector/src/app/data_did_agc_analysis/gpt-oss_4500_complexity_stratified_maxlen2048_mlp_ast/strict/validation/validation_summary.txt
(aidetector) OISSE-IST173C01:ai_detector$ 
(aidetector) OISSE-IST173C01:ai_detector$ 