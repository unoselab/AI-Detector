"""
threshold_sweep.py
==================

Decision-threshold sweep for tuned classifiers (RQ2-D, post-hoc analysis).

Background
----------
`test_embedding.py` evaluates classifiers using `clf.predict(X_test)`, which
applies the default decision threshold of 0.5 (probability >= 0.5 -> class 1).
A classifier tuned for macro-F1 during CV is not necessarily optimal at the
0.5 cutoff: the probability calibration can be biased toward one class,
leaving F1 on the table.

This script sweeps the decision threshold and reports the best operating
point, without retraining. To avoid test-set leakage, the threshold is
selected on the **dev split** and the F1 number reported is computed on the
**test split** at that selected threshold. This is the legitimate practice
for threshold tuning and is comparable to the test_embedding.py numbers.

What it does
------------
For each tuned estimator in the input pickle:
  1. Refit on train (same as test_embedding.py).
  2. Get probabilities (or decision scores) on dev and test.
  3. Sweep thresholds in [0.30, 0.70] in steps of 0.02.
  4. Pick the threshold that maximizes macro-F1 on dev.
  5. Report macro-F1 on test at that threshold (and at 0.5 baseline).

The result is a CSV + a stdout table comparing the default-0.5 F1 (the
existing test_embedding.py number) against the dev-tuned-threshold F1.

Supported classifiers
---------------------
* Probability-emitting: LR, MLP, RF, GB, KNN, DT, XGB. Uses predict_proba.
* SVM (SVC default): does NOT emit probabilities unless trained with
  probability=True. Falls back to decision_function and uses a 0-centered
  threshold sweep ([-1.0, 1.0] in steps of 0.05). The semantics are the
  same -- we're picking a decision boundary on a continuous score.

Usage
-----
    python threshold_sweep.py \\
        --splits-dir   data_codesearchnet/splits/starcoder2-15b-instruct-v0.1 \\
        --models-pickle data_codesearchnet/models/.../tuned_models_..._svm_....pkl \\
        --out-csv      threshold_sweep_svm.csv

    # Or batch over multiple pickles:
    for pkl in data_codesearchnet/models/.../tuned_models_*.pkl; do
      python threshold_sweep.py --splits-dir ... --models-pickle "$pkl" \\
                                --out-csv "${pkl%.pkl}_threshold.csv"
    done
"""

import argparse
import os
import pickle
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

warnings.filterwarnings("ignore")


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
EMB_TYPES = ["ast_", "combined_", "code_"]
LABEL_COL = "actual label"


# -----------------------------------------------------------------------------
# Scoring + threshold sweep
# -----------------------------------------------------------------------------
def get_scores(clf, X):
    """
    Return a 1-D array of "score for class 1" suitable for thresholding.
    Prefers predict_proba; falls back to decision_function.
    """
    if hasattr(clf, "predict_proba"):
        try:
            proba = clf.predict_proba(X)
            # Find which column is class 1.
            col = list(clf.classes_).index(1)
            return proba[:, col], "proba"
        except Exception:
            pass
    if hasattr(clf, "decision_function"):
        scores = clf.decision_function(X)
        # decision_function for binary returns shape (n,) where >0 => class 1.
        if scores.ndim == 2 and scores.shape[1] == 2:
            scores = scores[:, 1] - scores[:, 0]
        return scores, "decision"
    raise RuntimeError("Classifier has neither predict_proba nor decision_function.")


def sweep_threshold(scores, y_true, mode="proba"):
    """
    Try a range of thresholds and return list of (threshold, avg_f1_macro).
    For 'proba' mode, sweep [0.30, 0.70] step 0.02.
    For 'decision' mode, sweep around the score median +/- 1 std step 0.05.
    """
    if mode == "proba":
        thresholds = np.arange(0.30, 0.7001, 0.02)
    else:
        # Center the sweep on the data: median +- 1.5 std, 41 points.
        med, std = float(np.median(scores)), float(np.std(scores))
        lo, hi = med - 1.5 * std, med + 1.5 * std
        thresholds = np.linspace(lo, hi, 41)

    results = []
    for t in thresholds:
        pred = (scores >= t).astype(int)
        # avg_f1 = (human_f1 + ai_f1) / 2 -- same definition test_embedding.py uses
        h_f1 = f1_score(y_true, pred, pos_label=1, zero_division=0)
        a_f1 = f1_score(y_true, pred, pos_label=0, zero_division=0)
        results.append((float(t), 0.5 * (h_f1 + a_f1), h_f1, a_f1))
    return results


def f1_at_threshold(scores, y_true, t):
    pred = (scores >= t).astype(int)
    h_f1 = f1_score(y_true, pred, pos_label=1, zero_division=0)
    a_f1 = f1_score(y_true, pred, pos_label=0, zero_division=0)
    return 0.5 * (h_f1 + a_f1), h_f1, a_f1


def default_threshold(mode):
    """The threshold that clf.predict() would use."""
    return 0.5 if mode == "proba" else 0.0


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--splits-dir",    required=True,
                    help="Root of per-dataset split folders (train_/dev_/test_).")
    ap.add_argument("--models-pickle", required=True,
                    help="Pickle from hyperparameter_tuning.py.")
    ap.add_argument("--out-csv",       default=None,
                    help="Write detailed per-(dataset, emb, threshold) results.")
    ap.add_argument("--quiet",         action="store_true",
                    help="Only print the final summary line per (dataset, emb).")
    return ap.parse_args()


def main():
    args = parse_args()

    with open(args.models_pickle, "rb") as f:
        tuned = pickle.load(f)
    print(f"Loaded {len(tuned)} tuned estimator(s) from {args.models_pickle}\n")

    folders = sorted(
        d for d in os.listdir(args.splits_dir)
        if os.path.isdir(os.path.join(args.splits_dir, d))
    )

    summary_rows = []
    detail_rows  = []

    for folder in folders:
        folder_path = os.path.join(args.splits_dir, folder)
        files = os.listdir(folder_path)
        train_file = next(f for f in files if "train" in f)
        dev_file   = next(f for f in files if "dev"   in f)
        test_file  = next(f for f in files if "test"  in f)

        train_df = pd.read_csv(os.path.join(folder_path, train_file))
        dev_df   = pd.read_csv(os.path.join(folder_path, dev_file))
        test_df  = pd.read_csv(os.path.join(folder_path, test_file))

        y_train = train_df[LABEL_COL].to_numpy()
        y_dev   = dev_df[LABEL_COL].to_numpy()
        y_test  = test_df[LABEL_COL].to_numpy()

        print(f"=== {folder} "
              f"(train={len(train_df)}, dev={len(dev_df)}, test={len(test_df)}) ===")

        for emb in EMB_TYPES:
            key = folder + emb
            if key not in tuned:
                print(f"  [WARN] {key} missing in pickle, skipping")
                continue

            cols = [c for c in train_df.columns if c.startswith(emb)]
            X_train = train_df[cols].to_numpy()
            X_dev   = dev_df[cols].to_numpy()
            X_test  = test_df[cols].to_numpy()

            clf = tuned[key][0]

            # SVM stored without probability=True won't have predict_proba.
            # Decision_function still works -- get_scores handles both.
            clf.fit(X_train, y_train)

            dev_scores,  mode = get_scores(clf, X_dev)
            test_scores, _    = get_scores(clf, X_test)

            # Default-0.5 baseline (what test_embedding.py reports).
            t0 = default_threshold(mode)
            f1_default, h0, a0 = f1_at_threshold(test_scores, y_test, t0)

            # Sweep on dev, pick best, evaluate on test.
            sweep = sweep_threshold(dev_scores, y_dev, mode=mode)
            best_t, best_dev_f1, _, _ = max(sweep, key=lambda r: r[1])
            f1_tuned, h1, a1 = f1_at_threshold(test_scores, y_test, best_t)

            improvement = f1_tuned - f1_default

            if args.quiet:
                pass
            else:
                print(f"  {emb:10s}  score-mode={mode}  "
                      f"default(t={t0:.2f}): AvgF1={f1_default:.4f}  "
                      f"-> dev-tuned(t={best_t:.3f}): AvgF1={f1_tuned:.4f}  "
                      f"({improvement:+.4f})")

            summary_rows.append({
                "dataset":          folder,
                "emb":              emb,
                "score_mode":       mode,
                "default_threshold": t0,
                "default_avgf1":    round(f1_default, 4),
                "default_humanf1":  round(h0, 4),
                "default_aif1":     round(a0, 4),
                "best_threshold":   round(best_t, 4),
                "tuned_avgf1":      round(f1_tuned, 4),
                "tuned_humanf1":    round(h1, 4),
                "tuned_aif1":       round(a1, 4),
                "improvement":      round(improvement, 4),
                "dev_avgf1_at_t":   round(best_dev_f1, 4),
            })

            if args.out_csv:
                for t, avg, hf, af in sweep:
                    detail_rows.append({
                        "dataset":   folder,
                        "emb":       emb,
                        "split":     "dev",
                        "threshold": round(t, 4),
                        "avg_f1":    round(avg, 4),
                        "human_f1":  round(hf, 4),
                        "ai_f1":     round(af, 4),
                    })
                # Also record test sweep for plotting / inspection.
                for t in (r[0] for r in sweep):
                    avg, hf, af = f1_at_threshold(test_scores, y_test, t)
                    detail_rows.append({
                        "dataset":   folder,
                        "emb":       emb,
                        "split":     "test",
                        "threshold": round(t, 4),
                        "avg_f1":    round(avg, 4),
                        "human_f1":  round(hf, 4),
                        "ai_f1":     round(af, 4),
                    })

        print()

    # -----------------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------------
    summary_df = pd.DataFrame(summary_rows)
    print("=" * 90)
    print("Summary")
    print("=" * 90)
    if not summary_df.empty:
        print(summary_df[["dataset", "emb", "default_avgf1",
                          "best_threshold", "tuned_avgf1", "improvement"]]
              .to_string(index=False))
        print()
        print(f"Mean improvement across all (dataset, emb) pairs: "
              f"{summary_df['improvement'].mean():+.4f}")
        print(f"Max improvement:  {summary_df['improvement'].max():+.4f}  "
              f"at {summary_df.loc[summary_df['improvement'].idxmax(), ['dataset','emb']].to_dict()}")
        print(f"Best tuned F1:    {summary_df['tuned_avgf1'].max():.4f}  "
              f"at {summary_df.loc[summary_df['tuned_avgf1'].idxmax(), ['dataset','emb']].to_dict()}")

    if args.out_csv:
        os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
        summary_path = args.out_csv
        detail_path  = args.out_csv.replace(".csv", "_detail.csv")
        summary_df.to_csv(summary_path, index=False)
        pd.DataFrame(detail_rows).to_csv(detail_path, index=False)
        print(f"\nSummary -> {summary_path}")
        print(f"Detail  -> {detail_path}")


if __name__ == "__main__":
    main()