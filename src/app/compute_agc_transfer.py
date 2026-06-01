#!/usr/bin/env python3
"""
compute_agc_transfer.py
=======================

AGC-only metrics for the cross-generator TRANSFER experiment.

For one fixed classifier (e.g. GPT-OSS) scored over several target generators'
mixed-sample sets, compute precision / recall / F1 of the AGC (lm) class only.
HWC metrics are intentionally omitted: in transfer, the question is purely
"can this detector catch AI code from a generator it was not trained on?"

Note on convention:
  AGC recall    == TNR in the paper's human-as-positive framing
  AGC precision == of the blocks flagged AI, how many truly are AI

Input
-----
A transfer root laid out as:
  <root>/<target_exp>/<geometry>/predictions/*.predictions.tsv
TSV columns include: pred_label, truth_label  (values: human / lm)

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
import os
import sys

import pandas as pd

LM = "lm"        # AGC = positive class here
HUMAN = "human"
TRUTH_CANDS = ["truth_label", "TRUTH", "truth", "actual", "label"]
PRED_CANDS  = ["pred_label", "pred", "prediction", "y_pred"]


def pick(df, cands):
    for c in cands:
        if c in df.columns:
            return c
    return None


def load_dir(pred_dir):
    tsvs = sorted(glob.glob(os.path.join(pred_dir, "*.predictions.tsv")))
    frames = []
    for f in tsvs:
        d = pd.read_csv(f, sep="\t")
        t, p = pick(d, TRUTH_CANDS), pick(d, PRED_CANDS)
        if not (t and p):
            continue
        out = pd.DataFrame({
            "truth": d[t].astype(str).str.strip().str.lower(),
            "pred":  d[p].astype(str).str.strip().str.lower(),
        })
        out = out[out["truth"].isin([HUMAN, LM])]
        frames.append(out)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def agc_prf(df):
    tp = ((df["pred"] == LM) & (df["truth"] == LM)).sum()
    fp = ((df["pred"] == LM) & (df["truth"] != LM)).sum()
    fn = ((df["pred"] != LM) & (df["truth"] == LM)).sum()
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, int((df["truth"] == LM).sum())


def short(exp):
    # "gemma_4500_complexity_stratified_maxlen2048" -> "gemma"
    return exp.split("_4500_")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transfer-root", required=True,
                    help="e.g. .../data_mixed_samples_transfer/clf-gpt-oss")
    ap.add_argument("--clf-gen", default="gpt-oss",
                    help="short tag of the fixed classifier's generator.")
    ap.add_argument("--geometry", default="50x6")
    ap.add_argument("--out-csv", default=None)
    args = ap.parse_args()

    # Each immediate subdir of transfer-root is a target generator.
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
        p, r, f1, n = agc_prf(df)
        rows.append({
            "classifier": args.clf_gen,
            "target": short(tgt),
            "agc_precision": round(p, 4),
            "agc_recall": round(r, 4),
            "agc_f1": round(f1, 4),
            "agc_support": n,
            "n_blocks": len(df),
        })

    if not rows:
        sys.exit("[error] no targets produced metrics.")

    out = pd.DataFrame(rows).sort_values("agc_f1", ascending=False)

    print()
    print("=" * 72)
    print(f" AGC-only transfer metrics  (fixed classifier: {args.clf_gen})")
    print("=" * 72)
    print(f"  {'target':<16}{'AGC_prec':>10}{'AGC_rec':>10}{'AGC_F1':>10}"
          f"{'AGC_supp':>10}{'blocks':>9}")
    print("-" * 72)
    for _, x in out.iterrows():
        print(f"  {x['target']:<16}{x['agc_precision']:>10.4f}"
              f"{x['agc_recall']:>10.4f}{x['agc_f1']:>10.4f}"
              f"{x['agc_support']:>10d}{x['n_blocks']:>9d}")
    print("-" * 72)
    print(f"  {'MEAN (transfer)':<16}{out['agc_precision'].mean():>10.4f}"
          f"{out['agc_recall'].mean():>10.4f}{out['agc_f1'].mean():>10.4f}")
    print("=" * 72)

    if args.out_csv:
        out.to_csv(args.out_csv, index=False)
        print(f"[info] wrote {args.out_csv}")


if __name__ == "__main__":
    main()