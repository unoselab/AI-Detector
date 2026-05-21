# CodeSearchNet StarCoder2-7B Results

This document records the CodeSearchNet Python / StarCoder2-7B extension experiment for the AI-Detector RQ2-D embedding pipeline.

The experiment uses CodeT5+ embeddings and machine learning classifiers to distinguish human-written code from machine-generated code.

## Experiment Summary

| Item | Value |
|---|---|
| Dataset | CodeSearchNet Python |
| Human-written code source | CodeSearchNet |
| Machine-generated code model | `bigcode/starcoder2-7b` |
| Generation temperature | `0.2` |
| Generation max length | `512` |
| Classifier | Logistic Regression |
| Hyperparameter search | RandomizedSearchCV |
| Search iterations | `30` |
| CV folds | `5` |
| Random seed | `42` |
| Split strategy | Grouped 80/10/10 split by pair id |
| Positive label | Human-written code |
| Negative label | AI-generated code |

## Important Methodological Note

This is not an exact reproduction of the paper's StarCoder2-Instruct setting.

The paper used:

```text
Starcoder2-Instruct 15B
````

This experiment used:

```text
bigcode/starcoder2-7b
```

Therefore, these results should be reported as:

```text
CodeSearchNet Python / StarCoder2-7B extension experiment
```

not as the paper's original StarCoder2-Instruct result.

## Data Preparation

Raw StarCoder2 generations were first syntax-filtered and post-processed.

Two datasets were produced:

| Dataset file                                         | Pairs | Rows | Purpose                     |
| ---------------------------------------------------- | ----: | ---: | --------------------------- |
| `codesearchnet_starcoder2-7b_python_merged.csv`      |   400 |  800 | Paper-like sample size      |
| `codesearchnet_starcoder2-7b_python_merged_2250.csv` |  2250 | 4500 | Larger extension experiment |

The 2250-pair dataset was selected from the paired-valid pool after syntax validation.

## Syntax and Pair Filtering Summary

The syntax filtering stage produced the following summary:

```text
total_lines:       3000
json_errors:       0
mgc_valid_total:   2306
raw_valid:         147
salvaged_valid:    2159
mgc_invalid:       694
paired_valid:      2257
mgc_valid_rate:    0.7687
paired_valid_rate: 0.7523
```

The final large dataset used 2250 paired-valid samples.

## Pipeline Stages

### Stage 0a: Generate MGC

Script:

```text
src/run0a-generate.sh
```

Output:

```text
src/output/CodeSearchNet/starcoder2-7b-3000-tp0.2/outputs-512token.txt
```

### Stage 0b: Find Valid-Syntax MGC

Script:

```text
src/run0b-find-validsyntax-mgc.sh
```

Outputs:

```text
src/code-analyzer-tree-sitter/data_codesearchnet/validsyntax/codesearchnet_starcoder2-7b_python_merged.csv
src/code-analyzer-tree-sitter/data_codesearchnet/validsyntax/codesearchnet_starcoder2-7b_python_merged_2250.csv
```

### Stage 1: AST Generation

Script:

```text
src/run1-ast-generator.sh
```

Output directory:

```text
src/code-analyzer-tree-sitter/data_codesearchnet/ast/
```

AST generation summary:

```text
codesearchnet_starcoder2-7b_python_merged.csv      not parsed: 0/800
codesearchnet_starcoder2-7b_python_merged_2250.csv not parsed: 0/4500
```

### Stage 2: CodeT5+ Embedding Generation

Script:

```text
src/run2-generate-embeddings.sh
```

Output directory:

```text
src/ml_embeddings/data_codesearchnet/embeddings/
```

Each embedding CSV contains:

```text
idx
code
ast
code_0 ... code_255
ast_0 ... ast_255
combined_0 ... combined_255
actual label
```

Expected column count:

```text
772 columns
```

### Stage 3: Grouped Train/Dev/Test Split

Script:

```text
src/run3-split-data.sh
```

Output directory:

```text
src/ml_embeddings/data_codesearchnet/splits/
```

Split strategy:

```text
Grouped by pair id
```

This keeps matched pairs such as:

```text
line217_human
line217_lm
```

in the same split.

Split summary:

```text
codesearchnet_starcoder2-7b_python_merged:
  train = 640 rows = 320 human + 320 AI
  dev   =  80 rows =  40 human +  40 AI
  test  =  80 rows =  40 human +  40 AI

codesearchnet_starcoder2-7b_python_merged_2250:
  train = 3600 rows = 1800 human + 1800 AI
  dev   =  450 rows =  225 human +  225 AI
  test  =  450 rows =  225 human +  225 AI
```

### Stage 4: Classifier Training and Evaluation

Script:

```text
src/run4-train-classifiers.sh
```

Run configuration:

```text
model      : lr
n_iter     : 30
cv         : 5
seed       : 42
llm keys   : auto
```

Output files:

```text
src/logs/run4-train-classifiers_codesearchnet_lr_20260520_223815.log
src/ml_embeddings/data_codesearchnet/models/tuned_models_codesearchnet_lr_20260520_223815.pkl
src/ml_embeddings/data_codesearchnet/predictions/codesearchnet_lr_20260520_223815/
```

## Hyperparameter Tuning Results

### 400-Pair Dataset

Dataset:

```text
codesearchnet_starcoder2-7b_python_merged
```

Training rows:

```text
640
```

| Embedding | Dimension | Best CV Macro F1 | Best Parameters            |
| --------- | --------: | ---------------: | -------------------------- |
| AST Only  |       256 |           0.6616 | `solver=liblinear, C=10.0` |
| Combined  |       256 |           0.6468 | `solver=lbfgs, C=10.0`     |
| Code Only |       256 |           0.6378 | `solver=lbfgs, C=10.0`     |

### 2250-Pair Dataset

Dataset:

```text
codesearchnet_starcoder2-7b_python_merged_2250
```

Training rows:

```text
3600
```

| Embedding | Dimension | Best CV Macro F1 | Best Parameters             |
| --------- | --------: | ---------------: | --------------------------- |
| AST Only  |       256 |           0.6899 | `solver=liblinear, C=100.0` |
| Combined  |       256 |           0.6824 | `solver=liblinear, C=100.0` |
| Code Only |       256 |           0.6671 | `solver=lbfgs, C=100.0`     |

## Test Results

### 400-Pair Dataset

Dataset:

```text
codesearchnet_starcoder2-7b_python_merged
```

Test rows:

```text
80
```

| Embedding |    ACC |    TPR |    TNR | Human F1 |  AI F1 | Avg F1 |
| --------- | -----: | -----: | -----: | -------: | -----: | -----: |
| AST Only  | 0.6875 | 0.7500 | 0.6250 |   0.7059 | 0.6667 | 0.6863 |
| Combined  | 0.6125 | 0.6500 | 0.5750 |   0.6265 | 0.5974 | 0.6120 |
| Code Only | 0.6250 | 0.7000 | 0.5500 |   0.6512 | 0.5946 | 0.6229 |

Best result:

```text
AST Only, Avg F1 = 0.6863
```

### 2250-Pair Dataset

Dataset:

```text
codesearchnet_starcoder2-7b_python_merged_2250
```

Test rows:

```text
450
```

| Embedding |    ACC |    TPR |    TNR | Human F1 |  AI F1 | Avg F1 |
| --------- | -----: | -----: | -----: | -------: | -----: | -----: |
| AST Only  | 0.6756 | 0.7156 | 0.6356 |   0.6880 | 0.6620 | 0.6750 |
| Combined  | 0.6667 | 0.6978 | 0.6356 |   0.6767 | 0.6560 | 0.6663 |
| Code Only | 0.6644 | 0.7378 | 0.5911 |   0.6874 | 0.6379 | 0.6626 |

Best result:

```text
AST Only, Avg F1 = 0.6750
```

## Aggregate Results

### Per-LLM Average

The script auto-inferred the LLM bucket as:

```text
starcoder2-7b
```

Aggregate across both datasets and all three embedding types:

| LLM           |    ACC |    TPR |    TNR | Human F1 |  AI F1 | Avg F1 |  n |
| ------------- | -----: | -----: | -----: | -------: | -----: | -----: | -: |
| starcoder2-7b | 0.6553 | 0.7085 | 0.6020 |   0.6726 | 0.6358 | 0.6542 |  6 |

This value is useful as a compact summary, but it averages the 400-pair and 2250-pair datasets together. For reporting, the two dataset sizes should be kept separate.

### Per-Embedding Average

Across both datasets:

| Embedding | Mean Avg F1 |  n |
| --------- | ----------: | -: |
| AST Only  |      0.6807 |  2 |
| Combined  |      0.6391 |  2 |
| Code Only |      0.6428 |  2 |

## Interpretation

The main finding is that AST-only embeddings performed best in both dataset sizes.

```text
400-pair dataset:
  AST Only Avg F1 = 0.6863

2250-pair dataset:
  AST Only Avg F1 = 0.6750
```

This is consistent with the paper's general trend that AST-based embeddings are highly useful for AI-generated source code detection.

However, the absolute scores are lower than the paper's best reported embedding-based result. This is expected because the experimental setup is different.

Key differences:

| Paper Setting                       | This Experiment                        |
| ----------------------------------- | -------------------------------------- |
| Starcoder2-Instruct 15B             | StarCoder2-7B base                     |
| Paper generation setup              | Local generation with `max_length=512` |
| Paper curated CodeSearchNet samples | Syntax-salvaged CodeSearchNet samples  |
| Paper exact replication setting     | Extension experiment                   |
| Original per-dataset split design   | Grouped pair split by sample id        |

## Reporting Recommendation

For paper-like reporting, use the 400-pair result:

```text
CodeSearchNet Python / StarCoder2-7B / Logistic Regression / AST Only:
Avg F1 = 0.6863
```

For the larger extension experiment, report:

```text
CodeSearchNet Python / StarCoder2-7B / Logistic Regression / AST Only:
Avg F1 = 0.6750
```


