#!/usr/bin/env python3
"""
plot_threshold_curve.py

Plot threshold sweep curves from *_summary_detail.csv.

Example:
  python plot_threshold_curve.py \
    --csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1/svm_summary_detail.csv \
    --dataset codesearchnet_starcoder2-15b-instruct-v0.1_python_merged \
    --emb ast_ \
    --metric ai_f1 \
    --split both
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="Path to *_summary_detail.csv")
    p.add_argument("--dataset", required=True, help="Dataset name to plot")
    p.add_argument("--emb", default="ast_", choices=["ast_", "code_", "combined_"])
    p.add_argument("--metric", default="ai_f1",
                   choices=["avg_f1", "human_f1", "ai_f1"])
    p.add_argument("--split", default="both", choices=["dev", "test", "both"])
    p.add_argument("--out", default=None, help="Output PNG path")
    p.add_argument("--show", action="store_true", help="Show interactive plot")
    return p.parse_args()


def main():
    args = parse_args()

    csv_path = Path(args.csv)
    df = pd.read_csv(csv_path)

    required = {"dataset", "emb", "split", "threshold", args.metric}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] missing columns in {csv_path}: {sorted(missing)}")

    splits = ["dev", "test"] if args.split == "both" else [args.split]

    plt.figure(figsize=(9, 5.5))

    plotted = 0
    for split in splits:
        sub = df[
            (df["dataset"] == args.dataset) &
            (df["emb"] == args.emb) &
            (df["split"] == split)
        ].copy()

        if sub.empty:
            print(f"[WARN] no rows for split={split}, dataset={args.dataset}, emb={args.emb}")
            continue

        sub = sub.sort_values("threshold")
        plt.plot(
            sub["threshold"],
            sub[args.metric],
            marker="o",
            linewidth=1.8,
            markersize=4,
            label=split,
        )
        plotted += 1

        best_idx = sub[args.metric].idxmax()
        best = sub.loc[best_idx]
        print(
            f"{split}: best {args.metric}={best[args.metric]:.4f} "
            f"at threshold={best['threshold']:.4f}"
        )

    if plotted == 0:
        raise SystemExit("[ERROR] nothing plotted. Check --dataset, --emb, and --split.")

    metric_label = {
        "avg_f1": "Average F1",
        "human_f1": "Human F1",
        "ai_f1": "AI F1",
    }[args.metric]

    plt.xlabel("Decision threshold")
    plt.ylabel(metric_label)
    plt.title(f"{metric_label} vs Threshold\n{args.dataset} | {args.emb}")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    if args.out is None:
        out_dir = csv_path.parent / "plots"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_dataset = args.dataset.replace("/", "_")
        args.out = out_dir / f"{csv_path.stem}_{safe_dataset}_{args.emb}{args.metric}_{args.split}.png"
    else:
        args.out = Path(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(args.out, dpi=200)
    print(f"saved: {args.out}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
