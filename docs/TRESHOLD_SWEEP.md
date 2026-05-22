## Threshold sweep

**Goal.** Find best F1 by tuning the decision threshold (currently default 0.5).

**Method.** threshold tuning — select threshold on **dev** split (no test leakage), report F1 on **test** at that threshold. No retraining.

**Files added.**
- `src/ml_embeddings/threshold_sweep.py` — per-pickle sweep, dev → test
- `src/ml_embeddings/aggregate_threshold_sweeps.py` — combines per-classifier CSVs
- `src/run5-threshold-sweep.sh` — driver (latest pickle per classifier; supports `all`, subset, or single)

**Output.** `data_codesearchnet/threshold_sweep/<MODEL_NAME>/threshold_sweep_combined.csv` + per-classifier summaries.

**Run.**
```bash
bash src/run5-threshold-sweep.sh            # all (default)
bash src/run5-threshold-sweep.sh svm        # one
bash src/run5-threshold-sweep.sh svm mlp lr # subset
```

**Expected.** +1.5 to +3.0 F1 across classifiers if threshold tuning helps; flat means classifiers are already 0.5-calibrated and we move to the next lever.
