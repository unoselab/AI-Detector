# Embedding CSV Format Explained

This document explains the structure and purpose of the embedding CSV files generated during the CodeT5+ embedding stage of the AI-generated source code detection pipeline.

---

# Overview

The embedding CSVs are produced by:

```bash
run2-generate-embeddings.sh
````

which internally calls:

```bash
src/ml_embeddings/generate_embeddings.py
```

The purpose of this stage is to convert source code and AST representations into dense vector embeddings using:

```text
Salesforce/codet5p-110m-embedding
```

Each embedding CSV becomes the direct input for:

* train/dev/test splitting
* ML classifier training
* evaluation experiments

---

# Pipeline Context

The embedding generation stage is part of the following pipeline:

```text
Raw Code CSVs
    ↓
AST Generation
(run1-ast-generator.sh)
    ↓
AST CSVs
    ↓
Embedding Generation
(run2-generate-embeddings.sh)
    ↓
Embedding CSVs
    ↓
Train/Test Split
(run3-split-data.sh)
    ↓
Classifier Training
(run4-train-classifiers.sh)
```

---

# Input CSV Format

The embedding generator expects AST CSV files produced by:

```bash
run1-ast-generator.sh
```

Each input CSV typically contains:

| Column | Description              |
| ------ | ------------------------ |
| idx    | Unique sample identifier |
| code   | Original source code     |
| ast    | AST token sequence       |
| label  | human or lm              |

Example:

```csv
idx,code,ast,label
line217_human,"def add(a,b): return a+b","module function_definition ...",human
```

---

# Generated Embedding CSV Structure

The output embedding CSV expands each sample into multiple 256-dimensional embeddings.

Example output columns:

```text
idx
code
ast

code_0
code_1
...
code_255

ast_0
ast_1
...
ast_255

combined_0
combined_1
...
combined_255

actual label
```

---

# Embedding Types

Three separate embeddings are generated for every sample.

## 1. Code Embedding

Generated from:

```text
Original source code only
```

Columns:

```text
code_0 → code_255
```

Dimension:

```text
256
```

---

## 2. AST Embedding

Generated from:

```text
AST token sequence only
```

Columns:

```text
ast_0 → ast_255
```

Dimension:

```text
256
```

---

## 3. Combined Embedding

Generated from:

```text
code + "</s>" + ast
```

Columns:

```text
combined_0 → combined_255
```

Dimension:

```text
256
```

The separator token used is:

```python
SEP = " </s> "
```

---

# Label Encoding

The original labels are converted into integer values.

| Original Label | Encoded Value |
| -------------- | ------------- |
| human          | 1             |
| lm             | 0             |

The output column name becomes:

```text
actual label
```

This convention is used throughout the downstream ML pipeline.

---

# Total Column Count

Each embedding file contains:

| Component          | Columns |
| ------------------ | ------- |
| Metadata           | 3–4     |
| Code Embedding     | 256     |
| AST Embedding      | 256     |
| Combined Embedding | 256     |
| Label              | 1       |

Typical total:

```text
772 columns
```

Example verification:

```text
emb shape: (800, 772)
```

---

# Example Verification Output

Example validation script output:

```text
AST: code-analyzer-tree-sitter/data_codesearchnet/ast/codesearchnet_starcoder2-7b_python_merged.csv

EMB: ml_embeddings/data_codesearchnet/embeddings/codesearchnet_starcoder2-7b_python_merged.csv

ast shape: (800, 4)
emb shape: (800, 772)

row count match: True
idx preserved: True

labels: {1: 400, 0: 400}

emb cols:
256 code embeddings
256 ast embeddings
256 combined embeddings
```

---

# Why Embeddings Are Used

The ML classifiers cannot directly consume raw source code or AST text.

The embedding stage converts code representations into dense numerical vectors that preserve semantic and structural information.

These vectors are later used by classifiers such as:

* Logistic Regression
* Random Forest
* SVM
* MLP
* Gradient Boosting
* XGBoost

---

# Downstream Usage

The generated embedding CSVs are consumed by:

## Train/Test Splitting

```bash
run3-split-data.sh
```

which internally calls:

```bash
split_data.py
```

Output:

```text
train_.csv
dev_.csv
test_.csv
```

---

## Classifier Training

```bash
run4-train-classifiers.sh
```

which internally calls:

```bash
hyperparameter_tuning.py
test_embedding.py
```

---

# Important Notes

## 1. Row Order Is Preserved

The embedding generator preserves:

* row order
* sample identifiers (`idx`)
* labels

This guarantees consistent train/test mapping.

---

## 2. Missing Rows Are Removed

Rows with invalid or unparsable ASTs are automatically removed.

Specifically:

```python
data.dropna(subset=['ast'], inplace=True)
```

---

## 3. Maximum Token Length

CodeT5+ embeddings use:

```python
MAX_LEN = 512
```

Longer inputs are truncated.

---

# Reference Files

Main implementation files:

```text
src/ml_embeddings/generate_embeddings.py
src/run2-generate-embeddings.sh
src/ml_embeddings/split_data.py
src/ml_embeddings/hyperparameter_tuning.py
src/ml_embeddings/test_embedding.py
```

---

# Research Context

This embedding pipeline implements the "Machine Learning Classifiers with Embeddings" approach described in:

> Suh et al.,
> "An Empirical Study on Automatically Detecting AI-Generated Source Code: How Far Are We?"
> ICSE 2025

Specifically:

```text
RQ2-D: Machine Learning Classifiers with Embeddings
```

The study evaluates whether embeddings derived from:

* source code
* AST representations
* combined representations

can effectively distinguish:

```text
Human-written code
vs
AI-generated code
```
