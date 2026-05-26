"""
hyperparameter_tuning.py
========================

Hyperparameter tuning for ML classifiers on CodeT5+ embeddings (RQ2-D).

For each (dataset folder, embedding type) pair, performs a small random
search with k-fold CV on the training split and stores the best estimator.

Reference paper
---------------
Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
Source Code: How Far Are We?", ICSE 2025, Section IV.D ("RQ2: Machine
Learning Classifiers with Embeddings").

What changed from the upstream original
---------------------------------------
* Replaced PyCaret with sklearn RandomizedSearchCV. Same functional pattern
  (random search + CV), but uses libraries already in requirements.txt and
  avoids PyCaret's heavy transitive dependency tree.
* Empty path strings (`os.listdir('')`, `pd.read_csv('')`, `open('', 'wb')`)
  replaced with argparse-driven paths so the script no longer requires
  in-source edits to run.
* Default model is LogisticRegression rather than GradientBoostingClassifier.
  This matches what the upstream `test_embedding.py` actually refits
  (`model_type = 'lr'`), eliminating the LR/GB hyperparameter mismatch bug.
* Picks the train CSV by `'train' in name` (handles `train_.csv` and
  variants); previously hard-indexed `[0]` could pick the wrong file.

Input
-----
Splits produced by `split_data.py`:
    <splits-dir>/
        <dataset_name>/
            train_.csv
            dev_.csv
            test_.csv

Each `train_.csv` must contain columns starting with `code_`, `ast_`,
`combined_`, plus the integer `actual label` column.

Output
------
A pickle of tuned estimators keyed by `<dataset_name><emb_type>`, e.g.
`humaneval_chatgpt_python_merged` + `ast_`. Each value is a list containing
one fitted sklearn estimator (list-wrapped to preserve the upstream
indexing convention `tuned_models[key][0]`).

Example
-------
    python hyperparameter_tuning.py \\
        --splits-dir splits \\
        --out-pickle tuned_models_lr.pkl \\
        --model lr
"""

import argparse
import os
import pickle
import warnings
from collections import defaultdict
from typing import Tuple

import pandas as pd
# from sklearn.ensemble import (
#     GradientBoostingClassifier,
#     RandomForestClassifier,
# )
from sklearn.ensemble import (
    AdaBoostClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
EMB_TYPES = ["ast_", "combined_", "code_"]
LABEL_COL = "actual label"

MODEL_REGISTRY = {
    "lr":  (LogisticRegression(max_iter=2000),
            {"C": [0.01, 0.1, 1.0, 10.0, 100.0],
             "solver": ["lbfgs", "liblinear"]}),
    "knn": (KNeighborsClassifier(),
            {"n_neighbors": [3, 5, 7, 11, 15],
             "weights":     ["uniform", "distance"]}),
    "mlp": (MLPClassifier(max_iter=500),
            {"hidden_layer_sizes": [(64,), (128,), (64, 32)],
             "alpha":              [1e-4, 1e-3]}),
    "svm": (SVC(),
            {"C":      [0.1, 1.0, 10.0],
             "kernel": ["rbf", "linear"]}),
    "rf":  (RandomForestClassifier(n_jobs=-1),
            {"n_estimators": [100, 300],
             "max_depth":    [None, 10, 30]}),
    "dt":  (DecisionTreeClassifier(),
            {"max_depth": [None, 10, 30, 50]}),
    "gb":  (GradientBoostingClassifier(),
            {"n_estimators":  [100, 200],
             "learning_rate": [0.05, 0.1],
             "max_depth":     [3, 5]}),
# msong 2026-05-26 Added
    "et":  (ExtraTreesClassifier(n_jobs=-1, random_state=42),
            {"n_estimators": [100, 300, 500],
             "max_depth":    [None, 10, 30],
             "max_features": ["sqrt", "log2", None]}),

    "ada": (AdaBoostClassifier(random_state=42),
            {"n_estimators":  [50, 100, 200],
             "learning_rate": [0.05, 0.1, 0.5, 1.0]}),

    "hgb": (HistGradientBoostingClassifier(random_state=42),
            {"learning_rate":     [0.03, 0.05, 0.1],
             "max_iter":          [100, 200],
             "max_leaf_nodes":    [15, 31, 63],
             "l2_regularization": [0.0, 0.01, 0.1]}),
}

# Optional: XGBoost if available.
try:
    from xgboost import XGBClassifier

    MODEL_REGISTRY["xgb"] = (
        XGBClassifier(eval_metric="logloss", n_jobs=-1),
        {"n_estimators":  [100, 300],
         "max_depth":     [3, 6, 10],
         "learning_rate": [0.05, 0.1]},
    )
except ImportError:
    pass


# -----------------------------------------------------------------------------
# Core tuning
# -----------------------------------------------------------------------------
def tune_one(X, y, model_key, n_iter, cv, seed) -> Tuple[object, dict, float]:
    base, grid = MODEL_REGISTRY[model_key]
    search = RandomizedSearchCV(
        base, grid,
        n_iter=n_iter, cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
        random_state=seed,
    )
    search.fit(X, y)
    return search.best_estimator_, search.best_params_, search.best_score_


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--splits-dir", default="splits",
                    help="Root of per-dataset split folders from split_data.py.")
    ap.add_argument("--out-pickle", default="tuned_models.pkl",
                    help="Where to write the dict of tuned estimators.")
    ap.add_argument("--model", default="lr", choices=sorted(MODEL_REGISTRY.keys()),
                    help="Classifier family to tune.")
    ap.add_argument("--n-iter", type=int, default=6,
                    help="Number of random hyperparameter samples.")
    ap.add_argument("--cv", type=int, default=5,
                    help="Number of CV folds during tuning.")
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


def main():
    args = parse_args()

    folders = sorted(
        d for d in os.listdir(args.splits_dir)
        if os.path.isdir(os.path.join(args.splits_dir, d))
    )
    if not folders:
        raise SystemExit(f"[ERROR] no dataset folders under {args.splits_dir}")

    print(f"Splits dir : {args.splits_dir}")
    print(f"Model      : {args.model}")
    print(f"Search     : n_iter={args.n_iter}  cv={args.cv}  seed={args.seed}")
    print(f"Datasets   : {len(folders)}\n")

    tuned = defaultdict(list)

    for folder in folders:
        folder_path = os.path.join(args.splits_dir, folder)
        train_files = [f for f in os.listdir(folder_path) if "train" in f]
        if not train_files:
            print(f"[SKIP] no train file in {folder_path}")
            continue
        train_df = pd.read_csv(os.path.join(folder_path, train_files[0]))
        y = train_df[LABEL_COL].to_numpy()

        print(f"=== {folder} (n_train={len(train_df)}) ===")
        for emb in EMB_TYPES:
            cols = [c for c in train_df.columns if c.startswith(emb)]
            X = train_df[cols].to_numpy()
            est, params, score = tune_one(
                X, y, args.model, args.n_iter, args.cv, args.seed
            )
            print(f"  {emb:10s} dim={X.shape[1]:3d}  best F1_macro={score:.4f}  params={params}")
            tuned[folder + emb] = [est]
        print()

    with open(args.out_pickle, "wb") as f:
        pickle.dump(dict(tuned), f)
    print(f"Saved {len(tuned)} tuned estimators -> {args.out_pickle}")


if __name__ == "__main__":
    main()