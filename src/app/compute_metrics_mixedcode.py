#!/usr/bin/env python3
"""
compute_block_metrics.py
========================

Compute per-class precision / recall / F1 for block-level AGC detection,
plus the unweighted Avg-F1 used in Suh et al. (ICSE 2025, Sec IV.D) and
in this project's test_embedding.py.

Classes
-------
  HWC = human-written code   (label string "human")
  AGC = AI-generated code    (label string "lm")

Avg-F1 = (F1_HWC + F1_AGC) / 2     # macro F1, unweighted

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
  python compute_block_metrics.py \
      --pred-dir .../50x6/predictions

  python compute_block_metrics.py \
      --summary .../50x6/predictions/summary.csv \
      --out-csv .../50x6/predictions/block_metrics.csv
"""

import argparse
import glob
import os
import sys

import pandas as pd


HUMAN = "human"   # HWC
LM     = "lm"     # AGC

# Accept a few plausible column spellings for truth / prediction.
TRUTH_CANDS = ["truth_label", "TRUTH", "truth", "actual", "actual label", "label", "gold"]
PRED_CANDS  = ["pred_label", "pred", "prediction", "PRED", "y_pred"]


def pick_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _normalize(df, t, p):
    out = pd.DataFrame()
    out["truth"] = df[t].astype(str).str.strip().str.lower()
    out["pred"]  = df[p].astype(str).str.strip().str.lower()
    # Map any integer-coded labels (human=1, lm=0) to strings, just in case.
    int_map = {"1": HUMAN, "0": LM}
    out["truth"] = out["truth"].replace(int_map)
    out["pred"]  = out["pred"].replace(int_map)
    out = out[out["truth"].isin([HUMAN, LM])].copy()
    return out


def load_blocks(args):
    # --- Try the summary file first (only if it has block-level cols) ---
    if args.summary and os.path.isfile(args.summary):
        df = pd.read_csv(args.summary)
        t = pick_col(df, TRUTH_CANDS)
        p = pick_col(df, PRED_CANDS)
        if t and p:
            print(f"[info] using block-level columns from summary: "
                  f"truth='{t}', pred='{p}'")
            return _normalize(df, t, p)
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
        frames.append(_normalize(d, t, p))
    if not frames:
        sys.exit("[error] no prediction TSVs had usable truth/pred columns.")
    print(f"[info] aggregated {len(frames)} prediction files from {pred_dir}")
    return pd.concat(frames, ignore_index=True)


def prf(df, positive):
    """Precision/recall/F1 treating `positive` as the positive class."""
    tp = ((df["pred"] == positive) & (df["truth"] == positive)).sum()
    fp = ((df["pred"] == positive) & (df["truth"] != positive)).sum()
    fn = ((df["pred"] != positive) & (df["truth"] == positive)).sum()
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    support = int((df["truth"] == positive).sum())
    return prec, rec, f1, support


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=None,
                    help="predictions/summary.csv (used only if it has "
                         "block-level truth/pred; else its dir locates TSVs).")
    ap.add_argument("--pred-dir", default=None,
                    help="Directory of *.predictions.tsv (overrides summary dir).")
    ap.add_argument("--out-csv", default=None,
                    help="Optional path to write the metrics table as CSV.")
    args = ap.parse_args()

    df = load_blocks(args)
    n = len(df)
    if n == 0:
        sys.exit("[error] no labeled blocks to score.")

    acc = (df["pred"] == df["truth"]).mean()

    h_p, h_r, h_f, h_n = prf(df, HUMAN)   # HWC positive
    a_p, a_r, a_f, a_n = prf(df, LM)      # AGC positive
    avg_f1 = (h_f + a_f) / 2.0

    tpr = h_r   # human recall  (paper: human = positive)
    tnr = a_r   # AGC recall    (= TNR in that convention)

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
    print("=" * 60)

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
        pd.DataFrame(rows).to_csv(args.out_csv, index=False)
        print(f"[info] wrote {args.out_csv}")


if __name__ == "__main__":
    main()