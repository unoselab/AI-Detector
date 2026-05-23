# Summary

## Current task: application / detector track

We are working under:

```text
src/app/
```

Main files:

```text
build_mixed_samples.py
agc_detector.py
run0-build-mixed-samples.sh
run0b-build-mixed-samples-grid.sh
run1-agc-detector.sh
```

## 1. Mixed-sample generation was fixed and expanded

`build_mixed_samples.py` now supports configurable generation:

```text
--num-samples
--blocks-per-sample
--lm-ratio
--include-corners
--allow-reuse
--grid-out-root
--grid-configs
--validate-python
```

Important safety behavior:

```text
NO_SPLIT_FILTER=0
ALLOW_REUSE=0
```

So generated mixed samples use only held-out `test_.csv` rows, not train data.

We also made it fail if `test_.csv` is missing, instead of silently using all rows.

## 2. Built a clean 50×6 mixed sample set

Generated:

```text
src/app/mixed_samples_50x6/
```

Result:

```text
50 files
300 total blocks
150 human
150 lm
300 unique source idxs
all .py files parse successfully
```

Detector result on this set using high-confidence AST threshold:

```text
files scored  : 50
blocks scored : 300
truth blocks  : 300
correct       : 174
accuracy      : 0.5800
```

This was expected because the threshold is conservative and misses many AGC blocks.

## 3. Fixed detector for multi-file directory processing

`agc_detector.py` was updated so it can process:

```text
--input one_file.py
```

or:

```text
--input-dir some_directory
```

This avoids calling Python once per file. CodeT5+ now loads once per directory run.

`run1-agc-detector.sh` was simplified to call Python once and pass either a file or a directory.

Current default detector mode:

```text
INPUT_DIR=src/app/mixed_samples_50x6
EMBEDDING=ast
THRESHOLD=-1.3439
```

This is the high-confidence AGC threshold from the SVM + AST 2700-pair setting.

## 4. Fixed block extraction mismatch issue

Earlier sample 002 had mismatched function names after a Chinese docstring. Cause:

```text
tree-sitter byte offsets were used as Python string indexes
```

Fix in `agc_detector.py`:

```text
slice UTF-8 bytes first, then decode
```

Ground truth is now attached primarily by block order, which is safer for generated mixed samples.

## 5. Added / planned Java checker

We planned/created:

```text
checker_mixed_samples.java
run0a-checker-mixed-samples.sh
```

Purpose:

```text
Check .py markers vs .labels.tsv alignment
Verify block_idx, label, source_idx, function_name, start_line, end_line
```

Target successful result:

```text
files checked : 50
blocks checked: 300
errors        : 0
```

## 6. Built a block-size grid with equal total blocks

We decided to compare different `BLOCKS_PER_SAMPLE` values using a fixed total of 480 blocks per setting.

Chosen grid:

```text
BLOCKS_PER_SAMPLE = 2, 4, 6, 8, 10
TOTAL_BLOCKS      = 480
```

Generated root:

```text
src/app/data_mixed_samples_grid_480/
```

`grid_manifest.csv` result:

```text
blocks_02: 240 samples, 480 blocks, 240 human, 240 lm
blocks_04: 120 samples, 480 blocks, 240 human, 240 lm
blocks_06:  80 samples, 480 blocks, 240 human, 240 lm
blocks_08:  60 samples, 480 blocks, 240 human, 240 lm
blocks_10:  48 samples, 480 blocks, 240 human, 240 lm
```

Each setting has:

```text
unique_source_idxs = 480
```

So there is no reuse within each block-size setting.

## 7. Next steps

Tomorrow, continue from here:

1. Create or run detector-grid script:

```text
run1b-agc-detector-grid.sh
```

It should run:

```bash
INPUT_DIR=src/app/data_mixed_samples_grid_480/blocks_02 ./run1-agc-detector.sh
INPUT_DIR=src/app/data_mixed_samples_grid_480/blocks_04 ./run1-agc-detector.sh
INPUT_DIR=src/app/data_mixed_samples_grid_480/blocks_06 ./run1-agc-detector.sh
INPUT_DIR=src/app/data_mixed_samples_grid_480/blocks_08 ./run1-agc-detector.sh
INPUT_DIR=src/app/data_mixed_samples_grid_480/blocks_10 ./run1-agc-detector.sh
```

2. Then create aggregation / plot script:

```text
plot_threshold_blocks_f1.py
```

It should read all prediction TSVs and sweep thresholds offline using the saved SVM `score`.

3. Desired graph:

```text
x-axis: threshold
y-axis: BLOCKS_PER_SAMPLE
color: F1
```

Main metric should probably be:

```text
AI F1
```

Optionally also generate Avg F1 and AI precision heatmaps.

## Important interpretation

The detector has two modes:

```text
Balanced mode:
  SVM + AST, default threshold
  better overall F1

High-confidence AGC mode:
  SVM + AST, threshold = -1.3439
  higher AGC precision, lower AGC recall
```

The current app-level experiments are focused on the second mode: conservative AGC flagging.
