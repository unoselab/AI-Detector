#!/usr/bin/env python3
"""
compute_agc_transfer.py
=======================

Full block-level metrics for the cross-generator TRANSFER experiment.

For one fixed (pinned) classifier scored over several target generators'
mixed-sample sets, compute, PER TARGET cell:
  * HWC  (human) precision / recall / F1     -- human as positive
  * AGC  (lm)    precision / recall / F1     -- lm as positive
  * BOTH         precision / recall / F1     -- macro average of HWC & AGC
                                                (BOTH_F1 == Avg-F1)
  * accuracy                                 -- fraction of blocks correct
  * AUROC                                    -- threshold-free separation

Why all four:
  HWC/AGC give the per-class behaviour, BOTH gives the macro summary used in
  the paper, accuracy reproduces the Table-4 accuracy matrix, and AUROC shows
  whether the detector keeps its ability to SEPARATE human from AI code on an
  unseen generator (F1/accuracy only reflect the single decision threshold).

This per-cell report is a superset of compute_metrics_mixedcode.py, so each
matched-diagonal cell here should equal that script's result for the same
model -- a useful consistency check.

Conventions
-----------
  AGC recall    == TNR in the paper's human-as-positive framing.
  With balanced 150/150 cells, BOTH_recall and accuracy coincide (both equal
  the mean of the two class recalls); that agreement is expected, not a bug.

  AUROC: the detector's `score` (agc_detector.py -> predict_one) is the score
  for class 1 = "human" (signed decision_function margin for SVM, P(human) for
  the MLP). roc_curve accepts either; we use HUMAN as positive with
  y_score = score (higher => more human). AUROC is orientation-independent.
  It is computed PER CELL only -- scores from different cells live on
  different scales and must never be pooled.

Diagonal note
-------------
With INCLUDE_OWN=1 upstream, the classifier's own generator (the matched
diagonal) is one of the targets. Means are reported BOTH all-targets and
off-diagonal-only, so the off-diagonal mean reads as true out-of-distribution
generalization.

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

import pandas as pd

# roc_curve yields the (fpr, tpr, thresholds) sweep; auc integrates it.
from sklearn.metrics import roc_curve, auc

LM = "lm"          # AGC
HUMAN = "human"    # HWC
TRUTH_CANDS = ["truth_label", "TRUTH", "truth", "actual", "label"]
PRED_CANDS  = ["pred_label", "pred", "prediction", "y_pred"]
# `score` is the detector's primary column; the rest are graceful fallbacks.
SCORE_CANDS = ["score", "y_score", "proba", "probability", "confidence", "decision", "margin"]
MODE_CANDS  = ["score_mode", "mode"]

# Metric columns shared by target rows and the mean rows, with display headers.
METRIC_COLS = [
    "hwc_precision", "hwc_recall", "hwc_f1",
    "agc_precision", "agc_recall", "agc_f1",
    "both_precision", "both_recall", "both_f1",
    "accuracy", "auroc",
]
METRIC_HEADERS = [
    "HWC_P", "HWC_R", "HWC_F1",
    "AGC_P", "AGC_R", "AGC_F1",
    "BOTH_P", "BOTH_R", "BOTH_F1",
    "Acc", "AUROC",
]


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

    Returns a DataFrame with canonical columns truth, pred, and (when present)
    a numeric `score` plus `score_mode`; or None if no file had usable
    truth/pred columns. Labels are lowercased/stripped, the score is coerced to
    numeric for AUROC, and rows without a valid truth label are dropped.
    """
    tsvs = sorted(glob.glob(os.path.join(pred_dir, "*.predictions.tsv")))
    frames = []
    for f in tsvs:
        d = pd.read_csv(f, sep="\t")
        t, p = pick(d, TRUTH_CANDS), pick(d, PRED_CANDS)
        if not (t and p):
            continue  # this file lacks the labels we need; skip it

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

        out = out[out["truth"].isin([HUMAN, LM])]
        frames.append(out)

    if not frames:
        return None
    # Concatenating files within ONE target is valid (same pinned classifier,
    # one score scale). Do not concatenate across targets for AUROC.
    return pd.concat(frames, ignore_index=True)


def prf(df, positive):
    """
    Precision / recall / F1 / support treating `positive` as the positive class.

    tp = predicted positive & truly positive
    fp = predicted positive & truly the other class
    fn = predicted the other class & truly positive
    Each ratio guards against a zero denominator. Support = count of truly
    positive blocks. Called once with HUMAN (HWC) and once with LM (AGC).
    """
    tp = ((df["pred"] == positive) & (df["truth"] == positive)).sum()
    fp = ((df["pred"] == positive) & (df["truth"] != positive)).sum()
    fn = ((df["pred"] != positive) & (df["truth"] == positive)).sum()
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, int((df["truth"] == positive).sum())


def compute_transfer_auroc(df, positive=HUMAN):
    """
    Per-cell AUROC from the continuous `score`.

    Returns (auroc, reason): auroc is a float, or float('nan') when it cannot
    be computed (reason then explains why; None on success).

    Orientation: `positive` defaults to HUMAN because the detector's `score`
    increases with the human class, so y_score = score points the right way.
    AUROC is symmetric, so the value is the same whichever class is positive.

    Guards: nan if there is no `score` column, if every score is NaN, or if
    only one class is present (ROC undefined -- shouldn't happen with 150/150
    cells, but kept for safety).
    """
    if "score" not in df.columns:
        return float("nan"), "no score column (need continuous score for AUROC)"

    sub = df.dropna(subset=["score"])
    if len(sub) == 0:
        return float("nan"), "no numeric scores available"

    y_true = (sub["truth"] == positive).astype(int).to_numpy()
    if y_true.min() == y_true.max():
        return float("nan"), "only one class present; ROC undefined"

    y_score = sub["score"].to_numpy()      # higher => more positive (human)
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return auc(fpr, tpr), None


def cell_metrics(df):
    """
    Compute the full metric set for one target cell.

    Returns a dict with HWC, AGC, BOTH (macro) precision/recall/F1, plus
    accuracy, AUROC, per-class supports and block count. BOTH_* is the simple
    macro average of the HWC and AGC values (BOTH_f1 == Avg-F1). `auroc` is
    NaN when it cannot be computed.
    """
    h_p, h_r, h_f, h_n = prf(df, HUMAN)
    a_p, a_r, a_f, a_n = prf(df, LM)
    acc = (df["pred"] == df["truth"]).mean()
    auroc, _ = compute_transfer_auroc(df)
    return {
        "hwc_precision": h_p, "hwc_recall": h_r, "hwc_f1": h_f,
        "agc_precision": a_p, "agc_recall": a_r, "agc_f1": a_f,
        "both_precision": (h_p + a_p) / 2, "both_recall": (h_r + a_r) / 2,
        "both_f1": (h_f + a_f) / 2,
        "accuracy": float(acc), "auroc": auroc,
        "support_hwc": h_n, "support_agc": a_n, "n_blocks": len(df),
    }


def short(exp):
    """
    Shorten an experiment dir name to its model tag.

    'gemma_4500_complexity_stratified_maxlen2048' -> 'gemma'. Splits on the
    hardcoded '_4500_' marker, so only 4500-size experiments are shortened.
    """
    return exp.split("_4500_")[0]


def _fmt(v, nd=4):
    """Format a number for the console; 'n/a' for NaN/None."""
    return "n/a" if (v is None or (isinstance(v, float) and math.isnan(v))) else f"{v:.{nd}f}"


def _print_row(label, values, label_w=30):
    """
    Print one formatted table line: a left-aligned label followed by every
    METRIC_COLS value (right-aligned). `values` maps metric col -> number.
    """
    cells = "".join(f"{_fmt(values.get(c)):>9}" for c in METRIC_COLS)
    print(f"  {label:<{label_w}}{cells}")


def main():
    """
    Parse args, iterate the transfer root's target subdirs, compute the full
    HWC/AGC/BOTH/accuracy/AUROC set per target, then print a table with
    all-targets and off-diagonal-only means and optionally write the CSV.
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

        mt = cell_metrics(df)
        if math.isnan(mt["auroc"]):
            print(f"[warn] AUROC for {short(tgt)} unavailable")

        # A cell is the matched diagonal when its model tag == the pinned gen.
        row = {"classifier": args.clf_gen, "target": short(tgt),
               "is_diagonal": (short(tgt) == args.clf_gen)}
        row.update(mt)
        rows.append(row)

    if not rows:
        sys.exit("[error] no targets produced metrics.")

    # Sort by AGC F1 descending (preserves the original transfer-focused order).
    out = pd.DataFrame(rows).sort_values("agc_f1", ascending=False)
    off = out[~out["is_diagonal"]]

    # ---- Console table ----
    width = 32 + 9 * len(METRIC_COLS)
    print()
    print("=" * width)
    print(f" Full transfer metrics  (fixed classifier: {args.clf_gen})")
    print("=" * width)
    header_cells = "".join(f"{h:>9}" for h in METRIC_HEADERS)
    print(f"  {'target':<30}{header_cells}")
    print("-" * width)
    for _, x in out.iterrows():
        name = x["target"] + (" *" if x["is_diagonal"] else "")
        _print_row(name, x.to_dict())
    print("-" * width)

    # Means over each metric column (NaN AUROC values are skipped by .mean()).
    _print_row("MEAN (all targets)", {c: out[c].mean() for c in METRIC_COLS})
    if len(off) > 0:
        _print_row("MEAN (off-diagonal)", {c: off[c].mean() for c in METRIC_COLS})
    else:
        print(f"  {'MEAN (off-diagonal)':<30}{'n/a (no off-diagonal targets)':>9}")
    print("  (* = matched diagonal; BOTH_* = macro avg of HWC & AGC; "
          "supports 150/150, 300 blocks)")
    print("=" * width)

    if args.out_csv:
        # CSV keeps the supports and block count that the console omits.
        cols = (["classifier", "target", "is_diagonal"] + METRIC_COLS
                + ["support_hwc", "support_agc", "n_blocks"])
        out.to_csv(args.out_csv, index=False, columns=cols)
        print(f"[info] wrote {args.out_csv}")


if __name__ == "__main__":
    main()