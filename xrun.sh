tar -czf run-x-a03-v1-diagnostics-20260816.tar.gz \
  --exclude='src/app/data_did_agc_analysis/run-x-a03/ml_fun_occurrence_predictions.csv' \
  --exclude='src/app/data_did_agc_analysis/run-x-a03/ml_fun_unique_source_predictions.csv' \
  --exclude='src/app/data_did_agc_analysis/run-x-a03/source_prediction_chunks' \
  src/app/data_did_agc_analysis/run-x-a03 \
  src/logs/run-x-a03/run-x-a03-v1-full-score-ml-fun-sources-20260816-010848.log
  