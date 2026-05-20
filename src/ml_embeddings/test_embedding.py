"""
test_embedding.py
=================

Evaluate tuned ML classifiers on CodeT5+ embeddings (RQ2-D test phase).

Loads the pickle written by `hyperparameter_tuning.py`, refits each tuned
estimator on the corresponding training split, predicts on the held-out
test split, and reports six metrics from Section IV.D of Suh et al.
(ICSE 2025): ACC, TPR, TNR, Human_F1, AI_F1, Avg_F1.

What changed from the upstream original
---------------------------------------
* Fixed the LR/GB hyperparameter bridge bug at original lines 107-110:
  the upstream instantiated `LogisticRegression()` and tried to set
  GradientBoosting parameters on it via `set_params`, which raises.
  The fix is to use the already-tuned estimator directly:
      clf = tuned_models[key][0]; clf.fit(X_train, y_train)
* Fixed the per-LLM aggregation: the upstream `for dataset in [...]` loop
  did not filter `folder_name` by `dataset`, so metrics for "chatgpt" also
  included gemini/chatgpt4 folds. Now folders are explicitly bucketed by
  LLM substring.
* Replaced empty path strings with argparse-driven options.
* Replaced the unused `replace_label` helper -- label conversion now
  happens during embedding generation, so test_embedding.py reads
  ready-made integer labels.

Input
-----
* --splits-dir         Directory of per-dataset split folders (from
                       split_data.py). Each folder must contain train_.csv
                       and test_.csv with the same column schema.
* --models-pickle      Pickle file from hyperparameter_tuning.py.

Output
------
* Per-(dataset, embedding type) prediction CSV in --predictions-dir
  with columns [idx, code, ast, actual label, pred].
* Stdout summary: per-LLM averages and per-embedding-type averages.
"""

import argparse
import os
import pickle
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

warnings.filterwarnings("ignore")


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
EMB_TYPES = ["ast_", "combined_", "code_"]
LABEL_COL = "actual label"

# Substrings identifying each LLM in dataset folder names. Order matters --
# "chatgpt4" must be matched before "chatgpt_" to disambiguate.
LLM_KEYS = ["chatgpt4", "chatgpt_", "gemini"]


# -----------------------------------------------------------------------------
# Metrics (per paper Section IV.D)
# -----------------------------------------------------------------------------
def calculate_metrics(y_true, y_pred):
    acc      = accuracy_score(y_true, y_pred)
    human_f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    ai_f1    = f1_score(y_true, y_pred, pos_label=0, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    tpr = tp / max(tp + fn, 1)
    tnr = tn / max(tn + fp, 1)
    return {
        "acc":      acc,
        "tpr":      tpr,
        "tnr":      tnr,
        "human_f1": human_f1,
        "ai_f1":    ai_f1,
        "avg_f1":   (human_f1 + ai_f1) / 2,
    }


def llm_bucket(folder_name):
    """Return the LLM substring that matches this folder, or None."""
    for k in LLM_KEYS:
        if k in folder_name:
            return k
    return None


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--splits-dir", default="splits",
                    help="Root of per-dataset split folders.")
    ap.add_argument("--models-pickle", default="tuned_models.pkl",
                    help="Pickle of tuned estimators from hyperparameter_tuning.py.")
    ap.add_argument("--predictions-dir", default="predictions",
                    help="Where to dump per-(dataset, emb) prediction CSVs.")
    return ap.parse_args()


def main():
    args = parse_args()

    with open(args.models_pickle, "rb") as f:
        tuned_models = pickle.load(f)
    print(f"Loaded {len(tuned_models)} tuned estimator(s) from {args.models_pickle}\n")

    os.makedirs(args.predictions_dir, exist_ok=True)

    folders = sorted(
        d for d in os.listdir(args.splits_dir)
        if os.path.isdir(os.path.join(args.splits_dir, d))
    )

    per_llm = {k: defaultdict(list) for k in LLM_KEYS}   # bucket -> metric -> [scores]
    per_emb = {emb: [] for emb in EMB_TYPES}             # emb -> [avg_f1 scores]

    for folder in folders:
        folder_path = os.path.join(args.splits_dir, folder)
        files = os.listdir(folder_path)
        train_file = next(f for f in files if "train" in f)
        test_file  = next(f for f in files if "test"  in f)

        train_df = pd.read_csv(os.path.join(folder_path, train_file))
        test_df  = pd.read_csv(os.path.join(folder_path, test_file))
        y_train  = train_df[LABEL_COL].to_numpy()
        y_test   = test_df[LABEL_COL].to_numpy()
        bucket   = llm_bucket(folder)

        print(f"=== {folder} (train={len(train_df)}, test={len(test_df)}) ===")
        for emb in EMB_TYPES:
            cols = [c for c in train_df.columns if c.startswith(emb)]
            X_train = train_df[cols].to_numpy()
            X_test  = test_df[cols].to_numpy()

            key = folder + emb
            if key not in tuned_models:
                print(f"  [WARN] no tuned model for {key}; skipping")
                continue

            # Use the tuned estimator directly and refit on the full train split.
            clf  = tuned_models[key][0]
            clf.fit(X_train, y_train)
            pred = clf.predict(X_test)
            m    = calculate_metrics(y_test, pred)

            print(f"  {emb:10s}  ACC={m['acc']:.4f}  TPR={m['tpr']:.4f}  TNR={m['tnr']:.4f}  "
                  f"HF1={m['human_f1']:.4f}  AF1={m['ai_f1']:.4f}  AvgF1={m['avg_f1']:.4f}")

            per_emb[emb].append(m["avg_f1"])
            if bucket is not None:
                for k_, v_ in m.items():
                    per_llm[bucket][k_].append(v_)

            # Persist predictions for inspection.
            out_df = test_df[["idx", "code", "ast", LABEL_COL]].copy()
            out_df["pred"] = pred
            out_path = os.path.join(
                args.predictions_dir, f"{folder}__{emb.rstrip('_')}.csv"
            )
            out_df.to_csv(out_path, index=False)
        print()

    # -----------------------------------------------------------------------------
    # Aggregates
    # -----------------------------------------------------------------------------
    print("=" * 78)
    print("Per-LLM averages (across datasets + embedding types in that LLM bucket)")
    print("=" * 78)
    for llm in LLM_KEYS:
        metrics = per_llm[llm]
        if not metrics:
            print(f"  {llm:10s} : (no datasets matched)")
            continue
        line = f"  {llm:10s}"
        for k_ in ("acc", "tpr", "tnr", "human_f1", "ai_f1", "avg_f1"):
            line += f"  {k_}={np.mean(metrics[k_]):.4f}"
        line += f"  (n={len(metrics['avg_f1'])})"
        print(line)

    print()
    print("=" * 78)
    print("Per-embedding-type averages (across all datasets)")
    print("=" * 78)
    for emb in EMB_TYPES:
        scores = per_emb[emb]
        if scores:
            print(f"  {emb:10s}  Avg_F1 mean = {np.mean(scores):.4f}  (n={len(scores)})")


if __name__ == "__main__":
    main()