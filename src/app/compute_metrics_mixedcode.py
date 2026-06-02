#!/usr/bin/env python3
"""
compute_metrics_mixedcode.py
============================

Compute per-class precision / recall / F1 for block-level AGC detection,
the unweighted Avg-F1 used in Suh et al. (ICSE 2025, Sec IV.D) and in this
project's test_embedding.py, AND the threshold-independent AUROC.

Classes
-------
  HWC = human-written code   (label string "human")
  AGC = AI-generated code    (label string "lm")

Avg-F1 = (F1_HWC + F1_AGC) / 2     # macro F1, unweighted

AUROC
-----
Precision / recall / F1 / accuracy all depend on a single decision
threshold (the sign of the SVM margin at 0.0, or proba >= 0.5). AUROC
sweeps every possible threshold and reports how well the model SEPARATES
the two classes by its continuous `score`, independent of any one cutoff
(0.5 = coin flip, 1.0 = perfect separation).

The detector (agc_detector.py -> predict_one) writes a per-block `score`
that is the *score for class 1 = "human"*: the signed decision_function
margin when score_mode == "decision", or P(human) when score_mode ==
"proba". So AUROC is computed with HUMAN as the positive class and
y_score = score (higher => more human). AUROC is symmetric, so the value
is identical whichever class is nominated positive, provided the score
direction is consistent with that choice.

Input resolution
----------------
1. If --summary points at a CSV that already has block-level truth/pred
   columns, use it directly.
2. Otherwise, fall back to globbing the per-block prediction TSVs in the
   same predictions/ directory. The detector writes these with columns:
   file, block_idx, start_line, end_line, kind, name,
   pred_label, score, score_mode, truth_label, correct

Usage
-----
  python compute_metrics_mixedcode.py \
      --pred-dir .../50x6/predictions

  python compute_metrics_mixedcode.py \
      --summary .../50x6/predictions/summary.csv \
      --out-csv .../50x6/predictions/block_metrics.csv \
      --roc-csv .../50x6/predictions/roc_curve.csv
"""

import argparse
import glob
import os
import sys

import pandas as pd

# sklearn provides the ROC machinery. roc_curve() yields the (fpr, tpr,
# thresholds) sweep across every distinct score; auc() integrates that
# curve via the trapezoidal rule to give the single AUROC number.
from sklearn.metrics import roc_curve, auc


HUMAN = "human"   # HWC
LM     = "lm"     # AGC

# Accept a few plausible column spellings for truth / prediction / score so
# this script tolerates TSVs or summaries from slightly different producers.
TRUTH_CANDS = ["truth_label", "TRUTH", "truth", "actual", "actual label", "label", "gold"]
PRED_CANDS  = ["pred_label", "pred", "prediction", "PRED", "y_pred"]
# `score` is the detector's primary column; the others are graceful fallbacks.
SCORE_CANDS = ["score", "y_score", "proba", "probability", "confidence", "decision", "margin"]
MODE_CANDS  = ["score_mode", "mode"]


def pick_col(df, candidates):
    """
    Return the first column name from `candidates` that actually exists in
    `df`, or None if none are present.

    Used to map the many possible header spellings (truth_label vs TRUTH,
    pred_label vs y_pred, score vs decision, ...) onto the single canonical
    name this script works with internally.
    """
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _normalize(df, t, p, s=None, m=None):
    """
    Build a clean two-/four-column frame (truth, pred, [score], [score_mode])
    from an arbitrary input frame.

    Parameters
    ----------
    df : source DataFrame (one summary file or one prediction TSV).
    t  : name of the truth column in `df`.
    p  : name of the prediction column in `df`.
    s  : name of the continuous score column in `df`, or None if absent.
    m  : name of the score_mode column in `df`, or None if absent.

    Normalisation steps:
      * lowercase + strip the label strings so "Human", " LM " etc. unify;
      * map any integer-coded labels (human=1, lm=0) back to strings, in case
        a producer emitted ints;
      * coerce the score column to numeric (non-numeric -> NaN) so AUROC can
        use it; rows with NaN scores are dropped later only for AUROC, not
        for P/R/F1;
      * keep only rows whose TRUTH is a valid class (drops unlabeled "?"
        blocks the detector could not match to ground truth).
    """
    out = pd.DataFrame()
    out["truth"] = df[t].astype(str).str.strip().str.lower()
    out["pred"]  = df[p].astype(str).str.strip().str.lower()

    # Map any integer-coded labels (human=1, lm=0) to strings, just in case.
    int_map = {"1": HUMAN, "0": LM}
    out["truth"] = out["truth"].replace(int_map)
    out["pred"]  = out["pred"].replace(int_map)

    # Carry the continuous score through for AUROC if the producer supplied
    # one. errors="coerce" turns blanks/garbage into NaN instead of raising.
    if s is not None and s in df.columns:
        out["score"] = pd.to_numeric(df[s], errors="coerce")

    # Carry score_mode (proba | decision | discrete) so main() can warn when
    # the score is degenerate (discrete 0/1) and AUROC is not meaningful.
    if m is not None and m in df.columns:
        out["score_mode"] = df[m].astype(str).str.strip().str.lower()

    # Keep only rows with a usable ground-truth label.
    out = out[out["truth"].isin([HUMAN, LM])].copy()
    return out


def load_blocks(args):
    """
    Resolve the block-level scoring table from whichever input is available.

    Precedence:
      1. --summary, but ONLY if it carries genuine block-level truth/pred
         columns. The detector's own summary.csv is file-level
         (input, blocks, truth, correct, accuracy): its `truth` column is a
         COUNT, and it has no pred column, so the `t and p` test fails and we
         correctly fall through.
      2. The per-block *.predictions.tsv files in --pred-dir (or, if only
         --summary was given, the directory that contains it). Every TSV is
         normalised and the frames are concatenated into one pooled table.

    Exits with an error if neither source yields usable truth/pred columns.
    """
    # --- Try the summary file first (only if it has block-level cols) ---
    if args.summary and os.path.isfile(args.summary):
        df = pd.read_csv(args.summary)
        t = pick_col(df, TRUTH_CANDS)
        p = pick_col(df, PRED_CANDS)
        if t and p:
            s = pick_col(df, SCORE_CANDS)
            m = pick_col(df, MODE_CANDS)
            print(f"[info] using block-level columns from summary: "
                  f"truth='{t}', pred='{p}', score='{s}'")
            return _normalize(df, t, p, s, m)
        print(f"[info] summary.csv columns {list(df.columns)} are not "
              "block-level; falling back to per-block TSVs.")

    # --- Fall back to per-block prediction TSVs ---
    pred_dir = args.pred_dir
    if not pred_dir and args.summary:
        pred_dir = os.path.dirname(args.summary)
    if not pred_dir or not os.path.isdir(pred_dir):
        sys.exit(f"[error] no usable input. summary='{args.summary}', "
                 f"pred_dir='{pred_dir}'")

    tsvs = sorted(glob.glob(os.path.join(pred_dir, "*.predictions.tsv")))
    if not tsvs:
        sys.exit(f"[error] no *.predictions.tsv files in {pred_dir}")

    frames = []
    for f in tsvs:
        d = pd.read_csv(f, sep="\t")
        t = pick_col(d, TRUTH_CANDS)
        p = pick_col(d, PRED_CANDS)
        if not (t and p):
            print(f"[warn] skipping {f}: no truth/pred columns "
                  f"(has {list(d.columns)})")
            continue
        s = pick_col(d, SCORE_CANDS)
        m = pick_col(d, MODE_CANDS)
        frames.append(_normalize(d, t, p, s, m))
    if not frames:
        sys.exit("[error] no prediction TSVs had usable truth/pred columns.")
    print(f"[info] aggregated {len(frames)} prediction files from {pred_dir}")

    # Pooling across files is valid because all rows in one run come from the
    # SAME classifier, so their scores share one scale. Concatenating TSVs
    # produced by DIFFERENT classifiers would make the pooled AUROC invalid.
    return pd.concat(frames, ignore_index=True)


def prf(df, positive):
    """
    Precision / recall / F1 / support treating `positive` as the positive class.

    Counts the confusion-matrix cells directly:
      tp = predicted positive AND truly positive
      fp = predicted positive BUT truly the other class
      fn = predicted the other class BUT truly positive
    Each ratio guards against division by zero (returns 0.0 when the
    denominator is empty). `support` is the number of truly-positive rows.

    Called twice in main(): once with HUMAN positive, once with LM positive.
    """
    tp = ((df["pred"] == positive) & (df["truth"] == positive)).sum()
    fp = ((df["pred"] == positive) & (df["truth"] != positive)).sum()
    fn = ((df["pred"] != positive) & (df["truth"] == positive)).sum()
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    support = int((df["truth"] == positive).sum())
    return prec, rec, f1, support


def compute_auroc(df, positive=HUMAN):
    """
    Compute the threshold-independent AUROC from the continuous `score`.

    Returns a 3-tuple: (auroc, curve, reason)
      * auroc : float, or None if it cannot be computed.
      * curve : (fpr, tpr, thresholds) arrays from roc_curve, or None.
      * reason: human-readable string explaining why auroc is None, else None.

    Orientation
    -----------
    `positive` defaults to HUMAN to match the rest of this script's
    "human = positive" convention (TPR = human recall). The detector's
    `score` is already the score for class 1 = human, so higher score must
    map to the positive class -> we pass y_score = score directly.
    Because ROC is symmetric, choosing LM as positive together with the
    LM-oriented score (-score / 1-score) yields the identical AUROC value.

    Guards
    ------
      * no `score` column            -> cannot rank; return None.
      * all scores NaN               -> nothing to rank; return None.
      * only one class in the truth  -> ROC undefined (need both); return None.
    """
    # Need a continuous score to rank predictions; pred_label alone is not enough.
    if "score" not in df.columns:
        return None, None, "no score column in predictions (need continuous score for AUROC)"

    # Drop rows whose score could not be parsed to a number.
    sub = df.dropna(subset=["score"])
    if len(sub) == 0:
        return None, None, "no numeric scores available"

    # Binary ground truth: 1 for the positive class, 0 for the other.
    y_true = (sub["truth"] == positive).astype(int).to_numpy()

    # ROC needs both a positive and a negative example to be defined.
    if y_true.min() == y_true.max():
        return None, None, "only one class present in truth; ROC is undefined"

    # y_score: higher => more likely the positive (human) class.
    y_score = sub["score"].to_numpy()

    # Sweep all thresholds, then integrate the curve to a single number.
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    auroc = auc(fpr, tpr)
    return auroc, (fpr, tpr, thresholds), None


def main():
    """
    Parse arguments, load the pooled block table, compute and print all
    metrics (per-class P/R/F1, macro Avg-F1, accuracy, TPR/TNR, AUROC), and
    optionally write a metrics CSV and a ROC-curve CSV.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=None,
                    help="predictions/summary.csv (used only if it has "
                         "block-level truth/pred; else its dir locates TSVs).")
    ap.add_argument("--pred-dir", default=None,
                    help="Directory of *.predictions.tsv (overrides summary dir).")
    ap.add_argument("--out-csv", default=None,
                    help="Optional path to write the metrics table as CSV.")
    ap.add_argument("--roc-csv", default=None,
                    help="Optional path to write the ROC curve points "
                         "(fpr,tpr,threshold) for plotting.")
    args = ap.parse_args()

    # 1) Load the pooled, normalised block table.
    df = load_blocks(args)
    n = len(df)
    if n == 0:
        sys.exit("[error] no labeled blocks to score.")

    # 2) Threshold-dependent metrics.
    acc = (df["pred"] == df["truth"]).mean()

    h_p, h_r, h_f, h_n = prf(df, HUMAN)   # HWC positive
    a_p, a_r, a_f, a_n = prf(df, LM)      # AGC positive
    avg_f1 = (h_f + a_f) / 2.0

    tpr = h_r   # human recall  (paper: human = positive)
    tnr = a_r   # AGC recall    (= TNR in that convention)

    # 3) Threshold-independent metric.
    auroc, roc_pts, auroc_reason = compute_auroc(df, positive=HUMAN)

    # Warn when scores are discrete predict() outputs: AUROC then degenerates
    # because there is effectively only one interior threshold.
    if "score_mode" in df.columns and (df["score_mode"] == "discrete").all():
        print("[warn] all scores are discrete predict() outputs; AUROC is "
              "degenerate (no real ranking). Re-run the detector with a model "
              "that exposes predict_proba or decision_function.")

    # 4) Report.
    print()
    print("=" * 60)
    print(" Block-level metrics (HWC = human, AGC = lm)")
    print("=" * 60)
    print(f"  blocks scored : {n}")
    print(f"  HWC / AGC supp: {h_n} / {a_n}")
    print(f"  accuracy      : {acc:.4f}")
    print(f"  TPR (HWC rec) : {tpr:.4f}")
    print(f"  TNR (AGC rec) : {tnr:.4f}")
    print("-" * 60)
    print(f"  {'class':<6}{'precision':>12}{'recall':>10}{'f1':>10}{'support':>10}")
    print(f"  {'HWC':<6}{h_p:>12.4f}{h_r:>10.4f}{h_f:>10.4f}{h_n:>10d}")
    print(f"  {'AGC':<6}{a_p:>12.4f}{a_r:>10.4f}{a_f:>10.4f}{a_n:>10d}")
    print("-" * 60)
    print(f"  {'Avg-F1 (macro = (HWC_F1+AGC_F1)/2)':<48}{avg_f1:>8.4f}")
    if auroc is not None:
        print(f"  {'AUROC (threshold-independent, HUMAN=positive)':<48}{auroc:>8.4f}")
    else:
        print(f"  AUROC: n/a ({auroc_reason})")
    print("=" * 60)

    # 5) Optional metrics CSV. AUROC is stored on its own row, following the
    #    existing convention of putting accuracy in the f1 column.
    if args.out_csv:
        rows = [
            {"class": "HWC", "precision": round(h_p, 4), "recall": round(h_r, 4),
             "f1": round(h_f, 4), "support": h_n},
            {"class": "AGC", "precision": round(a_p, 4), "recall": round(a_r, 4),
             "f1": round(a_f, 4), "support": a_n},
            {"class": "avg", "precision": round((h_p + a_p) / 2, 4),
             "recall": round((h_r + a_r) / 2, 4), "f1": round(avg_f1, 4), "support": n},
            {"class": "accuracy", "precision": "", "recall": "",
             "f1": round(acc, 4), "support": n},
        ]
        if auroc is not None:
            rows.append(
                {"class": "auroc", "precision": "", "recall": "",
                 "f1": round(auroc, 4), "support": n}
            )
        pd.DataFrame(rows).to_csv(args.out_csv, index=False)
        print(f"[info] wrote {args.out_csv}")

    # 6) Optional ROC-curve dump for plotting (one row per threshold point).
    if args.roc_csv and roc_pts is not None:
        fpr, tpr_pts, thr = roc_pts
        pd.DataFrame({"fpr": fpr, "tpr": tpr_pts, "threshold": thr}) \
          .to_csv(args.roc_csv, index=False)
        print(f"[info] wrote {args.roc_csv}")
    elif args.roc_csv:
        print(f"[warn] --roc-csv given but no ROC curve available "
              f"({auroc_reason}); nothing written.")


if __name__ == "__main__":
    main()
