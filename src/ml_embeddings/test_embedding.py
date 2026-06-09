"""
test_embedding.py
=================

Evaluate tuned ML classifiers on CodeT5+ embeddings (RQ2-D test phase).

Loads the pickle written by `hyperparameter_tuning.py`, (optionally) refits
each tuned estimator on the corresponding training split, predicts on the
held-out test split, and reports the six metrics from Section IV.D of Suh
et al. (ICSE 2025): ACC, TPR, TNR, Human_F1, AI_F1, Avg_F1 -- PLUS a
threshold-independent AUROC appended alongside them.

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

What changed in THIS revision (AUROC support)
---------------------------------------------
* AUROC is APPENDED to the existing metric set; `calculate_metrics` and the
  six values it returns are left exactly as they were, so no previously
  reported number can shift. AUROC is computed separately and merged into the
  per-fold metric dict under the key "auroc".
* New `--score-method {auto,proba,decision}` flag controls where the
  continuous, rankable score for AUROC comes from. `auto` (default) tries
  `predict_proba` first, falls back to `decision_function` (this is what makes
  the SVM pickle work, since it was tuned with probability=False), and only
  then degrades to a discrete score (AUROC -> NaN).
* New `--no-refit` flag (default OFF, preserving the old behaviour for callers
  such as run4a) lets a test-only run score the pickled, already-fitted
  estimator as-is instead of refitting it on the train split.
* The per-(dataset, emb) prediction CSV now ALSO carries `score` and
  `score_mode` columns (appended after `pred`), so the ranking behind AUROC
  can be inspected or recomputed downstream.

Input
-----
* --splits-dir         Directory of per-dataset split folders (from
                       split_data.py). Each folder must contain train_.csv
                       and test_.csv with the same column schema.
* --models-pickle      Pickle file from hyperparameter_tuning.py.
* --score-method       auto | proba | decision  (AUROC score source).
* --no-refit           Skip the refit and score the pickled estimator as-is.

Output
------
* Per-(dataset, embedding type) prediction CSV in --predictions-dir with
  columns [idx, code, ast, actual label, pred, score, score_mode].
* Stdout summary: per-LLM averages and per-embedding-type averages, each now
  including AUROC.
"""

import argparse
import os
import pickle
import re
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd
# roc_auc_score added for the appended threshold-independent metric.
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score

warnings.filterwarnings("ignore")


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
EMB_TYPES = ["ast_", "combined_", "code_"]
LABEL_COL = "actual label"

# Language tokens used to infer the LLM name from folder names such as:
#   mbpp_chatgpt_python_merged
#   humaneval_chatgpt4_java_merged
#   codesearchnet_starcoder2-7b_python_merged
LANGUAGE_TOKENS = {"python", "java", "cpp", "c++"}


# -----------------------------------------------------------------------------
# Metrics (per paper Section IV.D)
# -----------------------------------------------------------------------------
def calculate_metrics(y_true, y_pred):
    """
    Compute the six threshold-dependent metrics from Suh et al. Sec IV.D.

    UNCHANGED from the original on purpose: keeping this function byte-for-byte
    identical guarantees the AUROC addition cannot perturb any of the numbers
    that were already being reported.

    Convention: label 1 == human (the positive class), label 0 == AI.
      acc      : overall accuracy.
      tpr      : true-positive rate  = human recall.
      tnr      : true-negative rate  = AI recall.
      human_f1 : F1 with human (1) as the positive class.
      ai_f1    : F1 with AI (0) as the positive class.
      avg_f1   : unweighted macro F1 = (human_f1 + ai_f1) / 2.
    """
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


def predict_scores(clf, X, method="auto"):
    """
    Produce a continuous, rankable score per sample for AUROC.

    AUROC needs a score it can sort by; a hard 0/1 prediction carries no
    ranking, so this helper extracts a real-valued score from the estimator.

    Parameters
    ----------
    clf    : a fitted sklearn-style estimator.
    X      : feature matrix for the rows to score.
    method : "auto"     -> try predict_proba, then decision_function, then give
                           up (returns None, "discrete").
             "proba"    -> force predict_proba; None on failure.
             "decision" -> force decision_function; None on failure.

    Returns
    -------
    (scores, score_mode) where
      scores     : 1-D np.ndarray of float, or None when only a discrete
                   prediction was possible (no usable ranking).
      score_mode : "proba" | "decision" | "discrete", mirroring the AGC
                   detector's score_mode convention so downstream tooling can
                   tell how the score was produced.

    Orientation: scores increase with the positive class (label 1 = human),
    matching calculate_metrics' pos_label=1, so AUROC treats human as positive.
    """
    # Inner helper: pull out the predict_proba column for class 1 (human).
    # sklearn sorts classes ascending, so for integer labels {0, 1} this is
    # column index 1, but we resolve the index explicitly to stay correct even
    # if an estimator ever reports classes in another order.
    def _proba_pos(estimator, feats):
        proba = estimator.predict_proba(feats)
        classes = list(estimator.classes_)
        idx = classes.index(1) if 1 in classes else proba.shape[1] - 1
        return proba[:, idx]

    want = (method or "auto").lower()

    # Explicit probability request: use predict_proba or report failure.
    if want == "proba":
        try:
            return _proba_pos(clf, X), "proba"
        except Exception:
            return None, "discrete"

    # Explicit margin request: use the signed decision_function value.
    if want == "decision":
        try:
            # np.ravel: binary decision_function returns shape (n,), but ravel
            # also flattens the rare (n, 1) case defensively.
            return np.ravel(clf.decision_function(X)), "decision"
        except Exception:
            return None, "discrete"

    # auto: prefer calibrated probabilities, then the SVM-style margin, then
    # concede that only a discrete label is available (AUROC will be NaN).
    try:
        return _proba_pos(clf, X), "proba"
    except Exception:
        pass
    try:
        return np.ravel(clf.decision_function(X)), "decision"
    except Exception:
        pass
    return None, "discrete"


def compute_auroc(y_true, scores):
    """
    Threshold-independent AUROC with human (label 1) as the positive class.

    Returns a float in [0, 1], or float('nan') when AUROC is undefined. The
    NaN cases are deliberately swallowed (not raised) so that one odd split or
    one estimator family without scores can never abort the whole evaluation
    loop -- the six base metrics still print for that fold.

    NaN is returned when:
      * scores is None            -> only discrete predictions exist; nothing
                                     to rank.
      * y_true has a single class -> ROC is undefined without both classes.
      * roc_auc_score raises       -> any other unexpected condition.
    """
    if scores is None:
        return float("nan")
    # roc_auc_score needs at least one sample of each class to define the curve.
    if len(np.unique(y_true)) < 2:
        return float("nan")
    try:
        return roc_auc_score(y_true, scores)
    except Exception:
        return float("nan")


def infer_llm_from_folder(folder_name):
    """
    Infer the LLM token from dataset folder names.

    Expected examples:
      mbpp_chatgpt_python_merged                  -> chatgpt
      humaneval_chatgpt4_java_merged              -> chatgpt4
      codesearchnet_starcoder2-7b_python_merged   -> starcoder2-7b

    Strategy: split on '_' and return the token immediately before the first
    recognised language token (python/java/cpp/c++), which by the project's
    naming convention is always the generator name.
    """
    parts = str(folder_name).lower().split("_")
    for i, part in enumerate(parts):
        if part in LANGUAGE_TOKENS and i > 0:
            return parts[i - 1]
    return "unknown"


def llm_bucket(folder_name, llm_keys=None):
    """
    Return the LLM bucket for this folder.

    If --llm-keys is provided, use ordered substring matching (first key that
    is a substring of the folder name wins; None if none match). If --llm-keys
    is not provided, fall back to inferring the LLM from the folder name.
    """
    if llm_keys:
        for k in llm_keys:
            if k in folder_name:
                return k
        return None

    return infer_llm_from_folder(folder_name)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    """
    Parse command-line arguments.

    Adds two new options on top of the original interface:
      --score-method : where the AUROC ranking score comes from.
      --no-refit     : reuse the pickled fitted estimator instead of refitting.
    Both have defaults chosen so existing callers (e.g. run4a) are unaffected.
    """
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
    ap.add_argument(
                    "--llm-keys", nargs="*", default=None, help=(
                        "Optional ordered LLM bucket keys for aggregation, e.g. "
                        "--llm-keys chatgpt4 chatgpt_ gemini starcoder2-7b. "
                        "If omitted, LLM names are inferred from folder names."
                    ))
    # --- new options -------------------------------------------------------
    ap.add_argument("--score-method", default="auto",
                    choices=["auto", "proba", "decision"],
                    help="Source of the continuous score used for AUROC. "
                         "auto: predict_proba -> decision_function -> discrete.")
    ap.add_argument("--no-refit", action="store_true",
                    help="Do NOT refit on the train split; score the pickled "
                         "(already-fitted) estimator as-is. Default off keeps "
                         "the original refit behaviour for callers like run4a.")
    return ap.parse_args()


def main():
    """
    Drive the test phase: load the pickle, score each (dataset, emb) fold,
    print per-fold metrics (now including AUROC), persist predictions with
    scores, and report per-LLM and per-embedding aggregates with AUROC.
    """
    args = parse_args()

    with open(args.models_pickle, "rb") as f:
        tuned_models = pickle.load(f)
    print(f"Loaded {len(tuned_models)} tuned estimator(s) from {args.models_pickle}")
    print(f"score-method={args.score_method}  no-refit={args.no_refit}\n")

    os.makedirs(args.predictions_dir, exist_ok=True)

    folders = sorted(
        d for d in os.listdir(args.splits_dir)
        if os.path.isdir(os.path.join(args.splits_dir, d))
    )

    llm_keys = args.llm_keys if args.llm_keys else None

    if llm_keys:
        print(f"LLM buckets: {llm_keys}")
    else:
        print("LLM buckets: inferred from dataset folder names")

    per_llm = defaultdict(lambda: defaultdict(list))      # bucket -> metric -> [scores]
    seen_llms = []                                        # preserve reporting order
    per_emb = {emb: [] for emb in EMB_TYPES}              # emb -> [avg_f1 scores]
    per_emb_auroc = {emb: [] for emb in EMB_TYPES}        # emb -> [auroc scores]  (NEW)

    for folder in folders:
        folder_path = os.path.join(args.splits_dir, folder)
        files = os.listdir(folder_path)
        train_file = next(f for f in files if "train" in f)
        test_file  = next(f for f in files if "test"  in f)

        train_df = pd.read_csv(os.path.join(folder_path, train_file))
        test_df  = pd.read_csv(os.path.join(folder_path, test_file))
        y_train  = train_df[LABEL_COL].to_numpy()
        y_test   = test_df[LABEL_COL].to_numpy()
        bucket   = llm_bucket(folder, llm_keys)
        if bucket is not None and bucket not in seen_llms:
            seen_llms.append(bucket)

        print(f"=== {folder} (train={len(train_df)}, test={len(test_df)}) ===")
        for emb in EMB_TYPES:
            cols = [c for c in train_df.columns if c.startswith(emb)]
            X_train = train_df[cols].to_numpy()
            X_test  = test_df[cols].to_numpy()

            key = folder + emb
            if key not in tuned_models:
                print(f"  [WARN] no tuned model for {key}; skipping")
                continue

            clf = tuned_models[key][0]
            # Reuse the pickled estimator by default in test-only runs
            # (--no-refit). RandomizedSearchCV used refit=True, so the saved
            # object is already trained on the full split; refitting would be
            # redundant and, for estimators without a fixed random_state (e.g.
            # RandomForest), would yield a slightly different model than the one
            # that was actually tuned and saved.
            if not args.no_refit:
                clf.fit(X_train, y_train)

            pred = clf.predict(X_test)

            # Continuous score for AUROC (None + "discrete" if unavailable).
            scores, score_mode = predict_scores(clf, X_test, args.score_method)

            # Six base metrics first (unchanged), then APPEND AUROC.
            m = calculate_metrics(y_test, pred)
            m["auroc"] = compute_auroc(y_test, scores)

            print(f"  {emb:10s}  ACC={m['acc']:.4f}  TPR={m['tpr']:.4f}  TNR={m['tnr']:.4f}  "
                  f"HF1={m['human_f1']:.4f}  AF1={m['ai_f1']:.4f}  AvgF1={m['avg_f1']:.4f}  "
                  f"AUROC={m['auroc']:.4f}")

            per_emb[emb].append(m["avg_f1"])
            per_emb_auroc[emb].append(m["auroc"])
            if bucket is not None:
                # m now carries "auroc" too, so this loop aggregates it for free.
                for k_, v_ in m.items():
                    per_llm[bucket][k_].append(v_)

            # Persist predictions for inspection. score/score_mode are appended
            # after the original columns so any existing reader of [idx, code,
            # ast, actual label, pred] keeps working unchanged.
            out_df = test_df[["idx", "code", "ast", LABEL_COL]].copy()
            out_df["pred"]       = pred
            out_df["score"]      = scores if scores is not None else np.nan
            out_df["score_mode"] = score_mode
            out_path = os.path.join(
                args.predictions_dir, f"{folder}__{emb.rstrip('_')}.csv"
            )
            out_df.to_csv(out_path, index=False)
        print()

    # -----------------------------------------------------------------------------
    # Aggregates
    # -----------------------------------------------------------------------------
    print("=" * 90)
    print("Per-LLM averages (across datasets + embedding types in that LLM bucket)")
    print("=" * 90)
    report_llms = llm_keys if llm_keys else seen_llms

    for llm in report_llms:
        metrics = per_llm.get(llm)
        if not metrics or "avg_f1" not in metrics:
            print(f"  {llm:10s} : (no datasets matched)")
            continue

        line = f"  {llm:10s}"
        for k_ in ("acc", "tpr", "tnr", "human_f1", "ai_f1", "avg_f1", "auroc"):
            # nanmean for AUROC so folds where it was undefined (NaN) are
            # skipped rather than poisoning the whole average; plain mean for
            # the others preserves the original aggregation exactly.
            agg = np.nanmean(metrics[k_]) if k_ == "auroc" else np.mean(metrics[k_])
            line += f"  {k_}={agg:.4f}"
        line += f"  (n={len(metrics['avg_f1'])})"
        print(line)

    print()
    print("=" * 90)
    print("Per-embedding-type averages (across all datasets)")
    print("=" * 90)
    for emb in EMB_TYPES:
        scores = per_emb[emb]
        if scores:
            auroc_mean = np.nanmean(per_emb_auroc[emb])
            print(f"  {emb:10s}  Avg_F1 mean = {np.mean(scores):.4f}  "
                  f"AUROC mean = {auroc_mean:.4f}  (n={len(scores)})")


if __name__ == "__main__":
    main()