## Run status

All seven available classifiers completed successfully.

| Model | Status | Runtime |
| ----- | ------ | ------: |
| LR    | OK     |   7 sec |
| SVM   | OK     |  12 sec |
| MLP   | OK     |  86 sec |
| RF    | OK     |  15 sec |
| GB    | OK     | 456 sec |
| KNN   | OK     |   5 sec |
| DT    | OK     |  11 sec |

Total wall-clock time:

```text
23:20:05 → 23:29:57 = about 9 min 52 sec
```

The slowest model was:

```text
GB = 456 sec
```

## Overall model ranking

Ranking by the script’s per-LLM average `Avg F1`, averaged across both dataset sizes and all three embedding types:

| Rank | Model |     Avg F1 |
| ---: | ----- | ---------: |
|    1 | LR    | **0.6542** |
|    2 | SVM   |     0.6462 |
|    3 | MLP   |     0.6383 |
|    4 | RF    |     0.5961 |
|    5 | GB    |     0.5793 |
|    6 | KNN   |     0.5587 |
|    7 | DT    |     0.5192 |

So for **StarCoder2-7B**, the best overall model is:

```text
Logistic Regression, Avg F1 = 0.6542
```

## Best individual results

### 400-pair dataset

Dataset:

```text
codesearchnet_starcoder2-7b_python_merged
```

Best result:

| Rank | Model | Embedding |    ACC |    TPR |    TNR | Human F1 |  AI F1 |     Avg F1 |
| ---: | ----- | --------- | -----: | -----: | -----: | -------: | -----: | ---------: |
|    1 | LR    | AST       | 0.6875 | 0.7500 | 0.6250 |   0.7059 | 0.6667 | **0.6863** |
|    2 | MLP   | AST       | 0.6500 | 0.7000 | 0.6000 |   0.6667 | 0.6316 |     0.6491 |
|    3 | RF    | AST       | 0.6250 | 0.6250 | 0.6250 |   0.6250 | 0.6250 |     0.6250 |

Best 400-pair headline:

```text
LR + AST, Avg F1 = 0.6863
```

### 2250-pair dataset

Dataset:

```text
codesearchnet_starcoder2-7b_python_merged_2250
```

Best result:

| Rank | Model | Embedding |    ACC |    TPR |    TNR | Human F1 |  AI F1 |     Avg F1 |
| ---: | ----- | --------- | -----: | -----: | -----: | -------: | -----: | ---------: |
|    1 | SVM   | Combined  | 0.6756 | 0.7022 | 0.6489 |   0.6840 | 0.6667 | **0.6753** |
|    2 | LR    | AST       | 0.6756 | 0.7156 | 0.6356 |   0.6880 | 0.6620 |     0.6750 |
|    3 | MLP   | Combined  | 0.6711 | 0.6978 | 0.6444 |   0.6797 | 0.6621 |     0.6709 |

Best 2250-pair headline:

```text
SVM + Combined, Avg F1 = 0.6753
```

But this is almost tied with:

```text
LR + AST, Avg F1 = 0.6750
```

The difference is only:

```text
0.0003
```

So I would not strongly claim SVM is meaningfully better for the large set. It is basically a tie.

## Best embedding trend

Average `Avg F1` across all seven models and both dataset sizes:

| Embedding | Mean Avg F1 |
| --------- | ----------: |
| AST       |  **0.6236** |
| Code      |      0.5924 |
| Combined  |      0.5805 |

So for StarCoder2-7B, **AST is the most reliable embedding type overall**.

Per-model embedding averages:

| Model | Best Embedding | Mean Avg F1 |
| ----- | -------------- | ----------: |
| LR    | AST            |  **0.6807** |
| SVM   | Combined       |      0.6501 |
| MLP   | AST            |      0.6577 |
| RF    | AST            |      0.6270 |
| GB    | AST            |      0.6262 |
| KNN   | AST            |      0.5884 |
| DT    | AST            |      0.5386 |

## Main conclusion for StarCoder2-7B

Use this as the clean summary:

```text
For the CodeSearchNet Python / StarCoder2-7B experiment, Logistic Regression achieved the best overall average performance across dataset sizes and embedding types, with Avg F1 = 0.6542. The best 400-pair result was LR with AST embeddings, Avg F1 = 0.6863. The best 2250-pair result was SVM with Combined embeddings, Avg F1 = 0.6753, nearly tied with LR using AST embeddings at Avg F1 = 0.6750. Overall, AST embeddings were the most reliable representation across models.
```

## Markdown-ready section

````md
## All-Model Results: CodeSearchNet / StarCoder2-7B

This section summarizes the all-model RQ2-D classifier experiment for the CodeSearchNet Python / StarCoder2-7B setting.

### Experiment Configuration

| Item | Value |
|---|---|
| Dataset | CodeSearchNet Python |
| MGC model | `starcoder2-7b` |
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

| Model | Status | Runtime |
|---|---|---:|
| LR | OK | 7 sec |
| SVM | OK | 12 sec |
| MLP | OK | 86 sec |
| RF | OK | 15 sec |
| GB | OK | 456 sec |
| KNN | OK | 5 sec |
| DT | OK | 11 sec |

### Overall Model Ranking

The following table ranks models by the per-LLM average `Avg F1`, averaged across both dataset sizes and all three embedding types.

| Rank | Model | Avg F1 |
|---:|---|---:|
| 1 | LR | **0.6542** |
| 2 | SVM | 0.6462 |
| 3 | MLP | 0.6383 |
| 4 | RF | 0.5961 |
| 5 | GB | 0.5793 |
| 6 | KNN | 0.5587 |
| 7 | DT | 0.5192 |

The best overall classifier was Logistic Regression.

### Best Results by Dataset Size

#### 400-Pair Dataset

| Rank | Model | Embedding | ACC | TPR | TNR | Human F1 | AI F1 | Avg F1 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | LR | AST | 0.6875 | 0.7500 | 0.6250 | 0.7059 | 0.6667 | **0.6863** |
| 2 | MLP | AST | 0.6500 | 0.7000 | 0.6000 | 0.6667 | 0.6316 | 0.6491 |
| 3 | RF | AST | 0.6250 | 0.6250 | 0.6250 | 0.6250 | 0.6250 | 0.6250 |

Best 400-pair result:

```text
LR + AST, Avg F1 = 0.6863
````

#### 2250-Pair Dataset

| Rank | Model | Embedding |    ACC |    TPR |    TNR | Human F1 |  AI F1 |     Avg F1 |
| ---: | ----- | --------- | -----: | -----: | -----: | -------: | -----: | ---------: |
|    1 | SVM   | Combined  | 0.6756 | 0.7022 | 0.6489 |   0.6840 | 0.6667 | **0.6753** |
|    2 | LR    | AST       | 0.6756 | 0.7156 | 0.6356 |   0.6880 | 0.6620 |     0.6750 |
|    3 | MLP   | Combined  | 0.6711 | 0.6978 | 0.6444 |   0.6797 | 0.6621 |     0.6709 |

Best 2250-pair result:

```text
SVM + Combined, Avg F1 = 0.6753
```

This is nearly tied with:

```text
LR + AST, Avg F1 = 0.6750
```

### Embedding-Type Trend

Average `Avg F1` across all models and both dataset sizes:

| Embedding | Mean Avg F1 |
| --------- | ----------: |
| AST       |  **0.6236** |
| Code      |      0.5924 |
| Combined  |      0.5805 |

Overall, AST embeddings were the most reliable representation for StarCoder2-7B.

### Main Finding

For the CodeSearchNet Python / StarCoder2-7B experiment, Logistic Regression achieved the best overall average performance. The strongest paper-like 400-pair result was:

```text
LR + AST, Avg F1 = 0.6863
```

The strongest 2250-pair result was:

```text
SVM + Combined, Avg F1 = 0.6753
```

However, the 2250-pair result is effectively tied with:

```text
LR + AST, Avg F1 = 0.6750
```

Therefore, the most stable conclusion is that AST embeddings remain the most reliable representation, and Logistic Regression is the strongest overall classifier for the StarCoder2-7B experiment.

