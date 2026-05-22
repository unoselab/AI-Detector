"""
aggregate_threshold_sweeps.py
=============================

Combine per-classifier threshold-sweep summary CSVs into a single CSV with
a classifier column and a sorted overview of mean improvement.

Used by run5-threshold-sweep.sh after threshold_sweep.py has produced one
summary CSV per classifier.

Input
-----
A directory containing files named `<classifier>_summary.csv` (e.g.
`lr_summary.csv`, `svm_summary.csv`). Each summary has columns:
    dataset, emb, score_mode, default_threshold, default_avgf1,
    default_humanf1, default_aif1, best_threshold, tuned_avgf1,
    tuned_humanf1, tuned_aif1, improvement, dev_avgf1_at_t

Output
------
A combined CSV at the path given by --out-csv with all summary rows plus
a `classifier` column. Stdout shows per-classifier means and the best
single (classifier, dataset, embedding) operating point overall.
"""

import argparse
import glob
import os
import sys

import pandas as pd


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep-dir", required=True,
                    help="Directory containing <classifier>_summary.csv files.")
    ap.add_argument("--out-csv",   required=True,
                    help="Where to write the combined summary CSV.")
    return ap.parse_args()


def main():
    args = parse_args()

    summary_files = sorted(glob.glob(os.path.join(args.sweep_dir, "*_summary.csv")))
    # Exclude detail files (they end with _summary_detail.csv).
    summary_files = [f for f in summary_files if not f.endswith("_summary_detail.csv")]

    if not summary_files:
        print(f"[WARN] no *_summary.csv files in {args.sweep_dir}", file=sys.stderr)
        sys.exit(0)

    rows = []
    for f in summary_files:
        df = pd.read_csv(f)
        clf = os.path.basename(f).replace("_summary.csv", "")
        df.insert(0, "classifier", clf)
        rows.append(df)

    combined_df = pd.concat(rows, ignore_index=True)
    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    combined_df.to_csv(args.out_csv, index=False)
    print(f"Wrote -> {args.out_csv}  ({len(combined_df)} rows)\n")

    # Per-classifier mean improvement.
    print("Per-classifier mean improvement (dev-tuned threshold - default 0.5):")
    agg = (combined_df
           .groupby("classifier")
           .agg(n=("default_avgf1", "size"),
                default=("default_avgf1", "mean"),
                tuned=("tuned_avgf1",   "mean"),
                delta=("improvement",    "mean"))
           .round(4)
           .sort_values("tuned", ascending=False))
    print(agg.to_string())
    print()

    # Best single operating point overall.
    best_idx = combined_df["tuned_avgf1"].idxmax()
    best = combined_df.loc[best_idx]
    print(f"Best overall: classifier={best['classifier']}, "
          f"dataset={best['dataset']}, emb={best['emb']}, "
          f"threshold={best['best_threshold']:.3f}, "
          f"AvgF1={best['tuned_avgf1']:.4f}  "
          f"(default 0.5: {best['default_avgf1']:.4f}, "
          f"delta {best['improvement']:+.4f})")


if __name__ == "__main__":
    main()