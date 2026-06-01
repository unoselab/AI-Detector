cd src/app/
MODEL_AND_TAG="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048"
python ./compute_metrics_mixedcode.py \
  --pred-dir ./data_mixed_samples/${MODEL_AND_TAG}/50x6/predictions \
  --out-csv ./data_mixed_samples/${MODEL_AND_TAG}/50x6/predictions/block_metrics.csv