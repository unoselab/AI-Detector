#!/usr/bin/env python3
"""
compute_agc_transfer.py
=======================

AGC-only metrics for the cross-generator TRANSFER experiment, now including
a per-cell AUROC.

For one fixed (pinned) classifier scored over several target generators'
mixed-sample sets, compute, per target:
  * AGC (lm) precision / recall / F1  -- threshold-dependent, AGC = positive
  * AUROC                             -- threshold-independent ranking quality

HWC precision/recall/F1 are intentionally omitted: in transfer the question is
purely "can this detector catch AI code from a generator it was not trained
on?". AUROC is added because F1 reflects only the single decision threshold,
whereas AUROC measures whether the detector preserves its ability to SEPARATE
human from AI code on an unseen generator -- a stronger robustness claim.

Conventions
-----------
  AGC recall    == TNR in the paper's human-as-positive framing.
  AGC precision == of the blocks flagged AI, how many truly are AI.

  AUROC: the detector's `score` (written by agc_detector.py -> predict_one) is
  the score for class 1 = "human" -- the signed decision_function margin for
  SVM classifiers, or P(human) for the MLP. Either works for roc_curve, which
  only needs a consistent ranking. We therefore compute AUROC with HUMAN as
  the positive class and y_score = score (higher => more human). AUROC is
  orientation-independent, so this equals the AGC-positive AUROC; the P/R/F1
  above stay AGC-positive as before.

  Each transfer cell has 150 human + 150 lm blocks, so both classes are always
  present and AUROC is well defined; a single-class guard is kept anyway.

  IMPORTANT: AUROC is computed PER CELL only. Scores from different cells
  (different classifiers/runs) live on different scales and must not be pooled.

Diagonal note
-------------
With INCLUDE_OWN=1 upstream, the classifier's own generator (the matched
diagonal) is one of the targets. The means therefore report BOTH an
all-targets mean and an off-diagonal-only mean, so the off-diagonal mean can
be read as true out-of-distribution generalization.

Input
-----
  <root>/<target_exp>/<geometry>/predictions/*.predictions.tsv
TSV columns include: pred_label, truth_label, score (values: human / lm).

Usage
-----
  python compute_agc_transfer.py \
      --transfer-root src/app/data_mixed_samples_transfer/clf-gpt-oss \
      --clf-gen gpt-oss \
      --geometry 50x6 \
      --out-csv src/app/data_mixed_samples_transfer/clf-gpt-oss/agc_transfer.csv
"""

import argparse
import glob
import math
import os
import sys

import numpy as np
import pandas as pd

# roc_curve yields the (fpr, tpr, thresholds) sweep; auc integrates it.
from sklearn.metrics import roc_curve, auc

LM = "lm"        # AGC = positive class for precision/recall/F1
HUMAN = "human"
TRUTH_CANDS = ["truth_label", "TRUTH", "truth", "actual", "label"]
PRED_CANDS  = ["pred_label", "pred", "prediction", "y_pred"]
# `score` is the detector's primary column; the rest are graceful fallbacks.
SCORE_CANDS = ["score", "y_score", "proba", "probability", "confidence", "decision", "margin"]
MODE_CANDS  = ["score_mode", "mode"]


def pick(df, cands):
    """
    Return the first column name in `cands` that exists in `df`, else None.

    Lets the script accept TSVs whose headers use slightly different spellings
    (truth_label vs TRUTH, score vs decision, ...) without hard-coding one name.
    """
    for c in cands:
        if c in df.columns:
            return c
    return None


def load_dir(pred_dir):
    """
    Pool every *.predictions.tsv in one target's predictions/ folder.

    Returns a DataFrame with canonical columns truth, pred, and (when the
    producer supplied it) a numeric `score` plus `score_mode`; or None if no
    file had usable truth/pred columns.

    Changes vs the original: the continuous `score` is no longer discarded --
    it is resolved via pick() and coerced to numeric so AUROC can rank on it.
    Labels are lowercased/stripped, and rows without a valid truth label are
    dropped (so unlabeled blocks never enter the metrics).
    """
    tsvs = sorted(glob.glob(os.path.join(pred_dir, "*.predictions.tsv")))
    frames = []
    for f in tsvs:
        d = pd.read_csv(f, sep="\t")
        t, p = pick(d, TRUTH_CANDS), pick(d, PRED_CANDS)
        if not (t and p):
            continue  # this file lacks the labels we need; skip it

        # Canonical truth/pred as lowercase strings.
        out = pd.DataFrame({
            "truth": d[t].astype(str).str.strip().str.lower(),
            "pred":  d[p].astype(str).str.strip().str.lower(),
        })

        # Carry the continuous score (for AUROC) if present; non-numeric -> NaN.
        s = pick(d, SCORE_CANDS)
        if s is not None:
            out["score"] = pd.to_numeric(d[s], errors="coerce")

        # Carry score_mode (proba | decision | discrete) for an optional warning.
        m = pick(d, MODE_CANDS)
        if m is not None:
            out["score_mode"] = d[m].astype(str).str.strip().str.lower()

        # Keep only rows with a usable ground-truth label.
        out = out[out["truth"].isin([HUMAN, LM])]
        frames.append(out)

    if not frames:
        return None
    # Concatenating files within ONE target is valid (same pinned classifier,
    # one score scale). Do not concatenate across targets for AUROC.
    return pd.concat(frames, ignore_index=True)


def agc_prf(df):
    """
    AGC (lm) precision / recall / F1 / support, with lm as the positive class.

    tp = predicted lm & truly lm   (AI correctly caught)
    fp = predicted lm & truly human (human code false-flagged as AI)
    fn = predicted human & truly lm (AI missed)
    Each ratio guards against a zero denominator. Support = count of truly-lm
    blocks. Metrics are pooled over all blocks in the cell.
    """
    tp = ((df["pred"] == LM) & (df["truth"] == LM)).sum()
    fp = ((df["pred"] == LM) & (df["truth"] != LM)).sum()
    fn = ((df["pred"] != LM) & (df["truth"] == LM)).sum()
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, int((df["truth"] == LM).sum())


def compute_transfer_auroc(df, positive=HUMAN):
    """
    Per-cell AUROC from the continuous `score`.

    Returns (auroc, reason):
      auroc  : float, or float('nan') when it cannot be computed.
      reason : None on success, else a short explanation for the nan.

    Orientation: `positive` defaults to HUMAN because the detector's `score`
    increases with the human class, so y_score = score points the right way.
    The value is the same whichever class is nominated positive (ROC is
    symmetric), so we report it simply as "AUROC".

    Guards: returns nan if there is no `score` column, if every score is NaN,
    or if only one class is present (ROC undefined -- shouldn't happen with
    150/150 cells, but kept for safety).
    """
    if "score" not in df.columns:
        return float("nan"), "no score column (need continuous score for AUROC)"

    sub = df.dropna(subset=["score"])
    if len(sub) == 0:
        return float("nan"), "no numeric scores available"

    # Binary truth: 1 for the positive (human) class, 0 for lm.
    y_true = (sub["truth"] == positive).astype(int).to_numpy()
    if y_true.min() == y_true.max():
        return float("nan"), "only one class present; ROC undefined"

    # Higher score => more likely the positive (human) class.
    y_score = sub["score"].to_numpy()
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return auc(fpr, tpr), None


def short(exp):
    """
    Shorten an experiment dir name to its model tag.

    'gemma_4500_complexity_stratified_maxlen2048' -> 'gemma'. Splits on the
    hardcoded '_4500_' marker, so only 4500-size experiments are shortened
    (others fall through unchanged).
    """
    return exp.split("_4500_")[0]


def _fmt(v, nd=4):
    """Format a float for the console, printing 'n/a' for NaN values."""
    return "n/a" if (v is None or (isinstance(v, float) and math.isnan(v))) else f"{v:.{nd}f}"


def main():
    """
    Parse args, iterate the transfer root's target subdirs, compute AGC P/R/F1
    and AUROC per target, then print a table with all-targets and
    off-diagonal-only means and optionally write the CSV.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--transfer-root", required=True,
                    help="e.g. .../data_mixed_samples_transfer/clf-gpt-oss")
    ap.add_argument("--clf-gen", default="gpt-oss",
                    help="short tag of the fixed classifier's generator "
                         "(used to identify the matched diagonal).")
    ap.add_argument("--geometry", default="50x6")
    ap.add_argument("--out-csv", default=None)
    args = ap.parse_args()

    # Each immediate subdir of the transfer root is one target generator.
    targets = sorted(d for d in os.listdir(args.transfer_root)
                     if os.path.isdir(os.path.join(args.transfer_root, d)))
    if not targets:
        sys.exit(f"[error] no target subdirs under {args.transfer_root}")

    rows = []
    for tgt in targets:
        pred_dir = os.path.join(args.transfer_root, tgt, args.geometry, "predictions")
        if not os.path.isdir(pred_dir):
            print(f"[warn] no predictions dir for {tgt}; skipping")
            continue
        df = load_dir(pred_dir)
        if df is None or len(df) == 0:
            print(f"[warn] no usable blocks for {tgt}; skipping")
            continue

        # Threshold-dependent AGC metrics + threshold-free AUROC for this cell.
        p, r, f1, n = agc_prf(df)
        auroc, why = compute_transfer_auroc(df)
        if why:
            print(f"[warn] AUROC for {short(tgt)}: {why}")

        # A cell is the matched diagonal when its model tag equals the pinned
        # classifier's generator tag.
        is_diag = (short(tgt) == args.clf_gen)

        rows.append({
            "classifier": args.clf_gen,
            "target": short(tgt),
            "is_diagonal": is_diag,
            "agc_precision": round(p, 4),
            "agc_recall": round(r, 4),
            "agc_f1": round(f1, 4),
            "agc_auroc": (round(auroc, 4) if not math.isnan(auroc) else ""),
            "agc_support": n,
            "n_blocks": len(df),
        })

    if not rows:
        sys.exit("[error] no targets produced metrics.")

    # Sort by F1 descending (matches the original ordering).
    out = pd.DataFrame(rows).sort_values("agc_f1", ascending=False)

    # numeric AUROC series for averaging (blank -> NaN, skipped by nanmean).
    auroc_num = pd.to_numeric(out["agc_auroc"], errors="coerce")
    off = out[~out["is_diagonal"]]
    off_auroc_num = pd.to_numeric(off["agc_auroc"], errors="coerce")

    # ---- Console table ----
    print()
    print("=" * 86)
    print(f" AGC-only transfer metrics  (fixed classifier: {args.clf_gen})")
    print("=" * 86)
    print(f"  {'target':<30}{'AGC_prec':>10}{'AGC_rec':>10}{'AGC_F1':>10}"
          f"{'AGC_AUROC':>11}{'AGC_supp':>10}{'blocks':>9}")
    print("-" * 86)
    for _, x in out.iterrows():
        # Mark the matched diagonal with a trailing asterisk.
        name = x["target"] + (" *" if x["is_diagonal"] else "")
        print(f"  {name:<30}{x['agc_precision']:>10.4f}{x['agc_recall']:>10.4f}"
              f"{x['agc_f1']:>10.4f}{_fmt(pd.to_numeric(x['agc_auroc'], errors='coerce')):>11}"
              f"{x['agc_support']:>10d}{x['n_blocks']:>9d}")
    print("-" * 86)
    # All-targets mean (includes the diagonal when INCLUDE_OWN=1 upstream).
    print(f"  {'MEAN (all targets)':<30}{out['agc_precision'].mean():>10.4f}"
          f"{out['agc_recall'].mean():>10.4f}{out['agc_f1'].mean():>10.4f}"
          f"{_fmt(auroc_num.mean()):>11}")
    # Off-diagonal mean = true out-of-distribution generalization.
    if len(off) > 0:
        print(f"  {'MEAN (off-diagonal)':<30}{off['agc_precision'].mean():>10.4f}"
              f"{off['agc_recall'].mean():>10.4f}{off['agc_f1'].mean():>10.4f}"
              f"{_fmt(off_auroc_num.mean()):>11}")
    else:
        print(f"  {'MEAN (off-diagonal)':<30}{'n/a (no off-diagonal targets)':>10}")
    print("  (* = matched diagonal: classifier scored on its own generator)")
    print("=" * 86)

    if args.out_csv:
        out.to_csv(args.out_csv, index=False)
        print(f"[info] wrote {args.out_csv}")


if __name__ == "__main__":
    main()