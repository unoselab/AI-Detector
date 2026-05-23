## 1. Confirmed and diagnosed the extra-block bug

We started from the grid detector anomaly:

| Grid setting            | Expected truth blocks | Detector scored blocks | Problem                             |
| ----------------------- | --------------------: | ---------------------: | ----------------------------------- |
| each `blocks_*` setting |                   480 |                    481 | one extra top-level block extracted |

We investigated one concrete case:

```text
src/app/data_mixed_samples_grid_480/blocks_02/mixed_sample_174.py
```

Its labels file showed only two intended blocks:

```text
block 1: checkargs, lm, source_idx=line2179_lm
block 2: start, human, source_idx=line1799_human
```

Then we traced `line2179_lm` back to the merged source CSV and confirmed it contained **two top-level `def checkargs(...)` functions** in one row. That violated the mixed-sample assumption: one CSV row should correspond to one top-level function/class block.

## 2. Identified the raw-generation source of the bug

We compared raw StarCoder2 samples:

| Sample                 | Output behavior                                    | Status |
| ---------------------- | -------------------------------------------------- | ------ |
| Sample 2177            | output was a true function body                    | clean  |
| Sample 2178 / line2179 | output body re-emitted the full function signature | bad    |

The bad pattern was:

```python
def checkargs(...):
    """docstring"""
def checkargs(...):
    ...
```

This is syntactically valid Python, so the old syntax checker accepted it, but it creates two top-level functions.

## 3. Patched `find_validsyntax_mgc.py`

We added logic to the raw-validity/salvage script so that it now:

| Fix                                                                           | Purpose                                                   |
| ----------------------------------------------------------------------------- | --------------------------------------------------------- |
| strips repeated outer `def` / `class` signatures from generated “body” output | salvages outputs like Sample 2178 when possible           |
| checks the composed MGC code has exactly one top-level function/class         | rejects syntactically valid but structurally invalid rows |
| preserves true nested helper functions                                        | nested functions inside the intended body are still okay  |

After rerunning:

```bash
./run0b-find-validsyntax-mgc.sh
```

the script produced:

| Metric                 |     Value |
| ---------------------- | --------: |
| total raw lines        |      3000 |
| MGC valid total        |      2786 |
| paired valid           |      2724 |
| paired valid rate      |    0.9080 |
| exported 400-pair CSV  |  800 rows |
| exported 2700-pair CSV | 5400 rows |

Most importantly, we verified:

```text
bad rows: 0
line2179_lm present: False
```

for the regenerated `*_merged_2700.csv`.

## 4. Regenerated the cleaned baseline pipeline

We reran the baseline data pipeline after the syntax-validity fix:

```bash
./run1-ast-generator.sh
OVERWRITE=1 ./run2-generate-embeddings.sh
./run3-split-data.sh
```

At first, we found a stale `*_merged_2250.csv` branch still contained `line2179_lm`. We removed stale `2250` artifacts from:

```text
validsyntax
ast
embeddings
splits
```

Then reran `run3-split-data.sh`.

Final active baseline datasets:

| Dataset         |     Rows |    Train |     Dev |    Test | Balance  |
| --------------- | -------: | -------: | ------: | ------: | -------- |
| `*_merged`      |      800 |      640 |      80 |      80 | 50/50    |
| `*_merged_2700` |     5400 |     4320 |     540 |     540 | 50/50    |
| **Total**       | **6200** | **4960** | **620** | **620** | balanced |

We verified:

```text
OK: line2179_lm not found
```

across active `validsyntax`, `ast`, `embeddings`, and `splits`.

## 5. Trained the cleaned baseline models

We ran all model families on the cleaned baseline `512` pipeline.

All seven completed:

| Classifier | Status | Runtime |
| ---------- | ------ | ------: |
| `lr`       | OK     |   8 sec |
| `svm`      | OK     |  17 sec |
| `mlp`      | OK     | 102 sec |
| `rf`       | OK     |  16 sec |
| `gb`       | OK     | 407 sec |
| `knn`      | OK     |   5 sec |
| `dt`       | OK     |  12 sec |

For `*_merged_2700`, the strongest AST-only results after cleaning were:

| Classifier | Embedding |     Avg F1 |
| ---------- | --------- | ---------: |
| `lr`       | `ast_`    | **0.6812** |
| `mlp`      | `ast_`    | **0.6776** |
| `svm`      | `ast_`    | **0.6735** |

The best individual `*_merged_2700` result overall was:

| Dataset         | Classifier | Embedding |     Avg F1 |
| --------------- | ---------- | --------- | ---------: |
| `*_merged_2700` | `lr`       | `code_`   | **0.6833** |

So AST-only LR was very close to the best overall result.

## 6. Decided on the next experiment: max length only

We discussed the ICSE 2025 ablation text about removing comments. The paper reported that removing comments reduced mean Avg F1 by 3.82, though the effect was statistically insignificant and small. So we decided **not** to remove comments for the improvement experiment.

The experiment we chose:

| Experiment            | Comments  | CodeT5+ max length |
| --------------------- | --------- | -----------------: |
| `baseline_maxlen512`  | unchanged |                512 |
| `baseline_maxlen1024` | unchanged |               1024 |

Goal: test whether reducing AST truncation improves `ast_` performance.

## 7. Patched embedding generation for configurable max length

We edited:

```text
src/ml_embeddings/generate_embeddings.py
src/run2-generate-embeddings.sh
```

The changes added:

| File                          | Change                                  |
| ----------------------------- | --------------------------------------- |
| `generate_embeddings.py`      | `--max-len` CLI argument                |
| `generate_embeddings.py`      | `embed_batch(..., max_len=...)`         |
| `generate_embeddings.py`      | tokenizer now uses `max_length=max_len` |
| `run2-generate-embeddings.sh` | `MAX_LEN` env/default variable          |
| `run2-generate-embeddings.sh` | passes `--max-len "${MAX_LEN}"`         |

Then we edited `run2-generate-embeddings.sh` directly for the `1024` experiment:

| Variable       | Value                                                             |
| -------------- | ----------------------------------------------------------------- |
| `MODEL_NAME`   | `starcoder2-15b-instruct-v0.1`                                    |
| `OUT_BASELINE` | `data_codesearchnet/embeddings/${MODEL_NAME}_maxlen1024_baseline` |
| `MAX_LEN`      | `1024`                                                            |
| `OVERWRITE`    | `1`                                                               |

## 8. Generated `baseline_maxlen1024` embeddings

We ran:

```bash
./run2-generate-embeddings.sh baseline
```

It completed cleanly:

| Dataset             | Rows | Columns | Output  |
| ------------------- | ---: | ------: | ------- |
| `*_merged.csv`      |  800 |     772 | written |
| `*_merged_2700.csv` | 5400 |     772 | written |

Output directory:

```text
src/ml_embeddings/data_codesearchnet/embeddings/starcoder2-15b-instruct-v0.1_maxlen1024_baseline
```

Runtime was about 4 minutes 17 seconds.

## 9. Generated `baseline_maxlen1024` splits

We edited `run3-split-data.sh` to read/write the maxlen1024 directories:

| Variable           | Value                                                             |
| ------------------ | ----------------------------------------------------------------- |
| `EMB_BASELINE_DIR` | `data_codesearchnet/embeddings/${MODEL_NAME}_maxlen1024_baseline` |
| `OUT_BASELINE`     | `data_codesearchnet/splits/${MODEL_NAME}_maxlen1024_baseline`     |

Then ran:

```bash
./run3-split-data.sh baseline
```

Result:

| Dataset         |    Train |     Dev |    Test |    Total |
| --------------- | -------: | ------: | ------: | -------: |
| `*_merged`      |      640 |      80 |      80 |      800 |
| `*_merged_2700` |     4320 |     540 |     540 |     5400 |
| **Total**       | **4960** | **620** | **620** | **6200** |

The file check showed exactly six split files.

## 10. Started training `baseline_maxlen1024`

Finally, we edited:

```text
run4a-train-classifiers-allmodels.sh
```

to use:

```bash
MODEL_NAME="starcoder2-15b-instruct-v0.1_maxlen1024_baseline"
```

That points training to:

```text
src/ml_embeddings/data_codesearchnet/splits/starcoder2-15b-instruct-v0.1_maxlen1024_baseline
```

and outputs models/logs under the same experiment name.

Training is currently running now.

## Current state

| Pipeline                             | Status        |
| ------------------------------------ | ------------- |
| cleaned baseline `MAX_LEN=512`       | complete      |
| cleaned baseline model training      | complete      |
| `baseline_maxlen1024` embeddings     | complete      |
| `baseline_maxlen1024` splits         | complete      |
| `baseline_maxlen1024` model training | running       |
| threshold sweep                      | not run yet   |
| mixed-grid rebuild after cleaning    | not rerun yet |

## Next after training finishes

When the training completes, we should compare `*_merged_2700 + ast_`:

| Classifier | Avg F1 @ 512 | Avg F1 @ 1024 |   Delta |
| ---------- | -----------: | ------------: | ------: |
| `lr`       |       0.6812 |       pending | pending |
| `mlp`      |       0.6776 |       pending | pending |
| `svm`      |       0.6735 |       pending | pending |

If `1024` improves AST-only performance, we can use it for the next detector/grid experiment.
