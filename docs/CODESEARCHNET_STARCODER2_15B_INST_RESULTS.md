## Main all-model result

Overall ranking by the script’s per-LLM `avg_f1`:

| Rank | Model |     Avg F1 |
| ---: | ----- | ---------: |
|    1 | SVM   | **0.6725** |
|    2 | MLP   |     0.6614 |
|    3 | LR    |     0.6468 |
|    4 | GB    |     0.6037 |
|    5 | RF    |     0.5999 |
|    6 | KNN   |     0.5549 |
|    7 | DT    |     0.5427 |

So for **StarCoder2-15B-Instruct**, the best overall model is:

```text
SVM, Avg F1 = 0.6725
```

## Best result by dataset size

### 400-pair dataset

Best results:

| Rank | Model | Embedding |     Avg F1 |
| ---: | ----- | --------- | ---------: |
|    1 | SVM   | AST       | **0.6871** |
|    1 | SVM   | Code      | **0.6871** |
|    3 | MLP   | Code      |     0.6863 |

For the paper-like 400-pair setting, report:

```text
SVM + AST or SVM + Code, Avg F1 = 0.6871
```

### 2250-pair dataset

Best results:

| Rank | Model | Embedding |     Avg F1 |
| ---: | ----- | --------- | ---------: |
|    1 | SVM   | AST       | **0.6932** |
|    2 | LR    | Combined  |     0.6889 |
|    3 | MLP   | Code      |     0.6888 |

For the larger 2250-pair extension, report:

```text
SVM + AST, Avg F1 = 0.6932
```

## Best embedding trend

Across both dataset sizes, by model:

| Model | Best embedding average |     Avg F1 |
| ----- | ---------------------- | ---------: |
| SVM   | AST                    | **0.6901** |
| MLP   | Code                   |     0.6875 |
| LR    | Code                   |     0.6596 |
| RF    | AST                    |     0.6055 |
| GB    | Combined               |     0.6126 |
| KNN   | AST                    |     0.5896 |
| DT    | AST                    |     0.5526 |

Main takeaway:

```text
For StarCoder2-15B-Instruct, SVM with AST embeddings is the strongest setting.
```

That is different from the earlier LR-only result, where the 2250-pair best was LR + Combined. Once all models are included, **SVM + AST wins**.

## All-Model Classifier Results

This section summarizes the all-model RQ2-D classifier experiment for the CodeSearchNet Python / StarCoder2-15B-Instruct setting.

### Experiment Configuration

| Item | Value |
|---|---|
| Dataset | CodeSearchNet Python |
| MGC model | `starcoder2-15b-instruct-v0.1` |
| Classifiers | LR, SVM, MLP, RF, GB, KNN, DT |
| XGBoost | Skipped, not installed |
| Embedding model | `Salesforce/codet5p-110m-embedding` |
| Embedding types | Code, AST, Combined |
| Split strategy | Grouped 80/10/10 split by pair id |
| Search iterations | 30 |
| CV folds | 5 |
| Seed | 42 |

### Run Summary

All seven available ML classifiers completed successfully.

| Model | Status |
|---|---|
| LR | OK |
| SVM | OK |
| MLP | OK |
| RF | OK |
| GB | OK |
| KNN | OK |
| DT | OK |

### Overall Model Ranking

The following table ranks models by the per-LLM average `Avg F1`, averaged across both dataset sizes and all three embedding types.

| Rank | Model | Avg F1 |
|---:|---|---:|
| 1 | SVM | **0.6725** |
| 2 | MLP | 0.6614 |
| 3 | LR | 0.6468 |
| 4 | GB | 0.6037 |
| 5 | RF | 0.5999 |
| 6 | KNN | 0.5549 |
| 7 | DT | 0.5427 |

The best overall classifier was SVM.

### Best Results by Dataset Size

#### 400-Pair Dataset

| Rank | Model | Embedding | ACC | TPR | TNR | Human F1 | AI F1 | Avg F1 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | SVM | AST | 0.6875 | 0.6500 | 0.7250 | 0.6753 | 0.6988 | **0.6871** |
| 1 | SVM | Code | 0.6875 | 0.6500 | 0.7250 | 0.6753 | 0.6988 | **0.6871** |
| 3 | MLP | Code | 0.6875 | 0.6250 | 0.7500 | 0.6667 | 0.7059 | 0.6863 |

Best 400-pair result:

```text
SVM + AST or SVM + Code, Avg F1 = 0.6871
````

#### 2250-Pair Dataset

| Rank | Model | Embedding |    ACC |    TPR |    TNR | Human F1 |  AI F1 |     Avg F1 |
| ---: | ----- | --------- | -----: | -----: | -----: | -------: | -----: | ---------: |
|    1 | SVM   | AST       | 0.6933 | 0.7156 | 0.6711 |   0.7000 | 0.6864 | **0.6932** |
|    2 | LR    | Combined  | 0.6889 | 0.6844 | 0.6933 |   0.6875 | 0.6903 |     0.6889 |
|    3 | MLP   | Code      | 0.6889 | 0.6711 | 0.7067 |   0.6833 | 0.6943 |     0.6888 |

Best 2250-pair result:

```text
SVM + AST, Avg F1 = 0.6932
```

### Per-Embedding-Type Observations

The strongest model/embedding combinations were:

| Model | Best Embedding Type | Mean Avg F1 Across Dataset Sizes |
| ----- | ------------------- | -------------------------------: |
| SVM   | AST                 |                       **0.6901** |
| MLP   | Code                |                           0.6875 |
| LR    | Code                |                           0.6596 |
| GB    | Combined            |                           0.6126 |
| RF    | AST                 |                           0.6055 |
| KNN   | AST                 |                           0.5896 |
| DT    | AST                 |                           0.5526 |

### Main Finding

For the CodeSearchNet Python / StarCoder2-15B-Instruct experiment, SVM is the best overall classifier. The strongest single result is:

```text
SVM + AST embeddings on the 2250-pair dataset:
Avg F1 = 0.6932
```

The best paper-like 400-pair result is:

```text
SVM + AST or SVM + Code:
Avg F1 = 0.6871
```

### Interpretation

The all-model run changes the conclusion from the LR-only run. In the LR-only run, the best large-dataset result was LR with Combined embeddings. After evaluating all available ML classifiers, SVM with AST embeddings performs best overall.

This means the final reported StarCoder2-15B-Instruct result should use SVM rather than LR.

