#!/usr/bin/env python3
"""
plot_threshold_curve.py

Plot threshold sweep curves from *_summary_detail.csv.

Typical usage:

  # Plot AI-F1 only, dev + test
  python plot_threshold_curve.py \
    --csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1/svm_summary_detail.csv \
    --dataset codesearchnet_starcoder2-15b-instruct-v0.1_python_merged \
    --emb ast_ \
    --metric ai_f1 \
    --split both

  # Plot AI precision / recall / F1 together on test split
  python plot_threshold_curve.py \
    --csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1/svm_summary_detail.csv \
    --dataset codesearchnet_starcoder2-15b-instruct-v0.1_python_merged \
    --emb ast_ \
    --plot ai-prf \
    --split test

  # Same plot, with dev-selected threshold line from summary CSV
  python plot_threshold_curve.py \
    --csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1/svm_summary_detail.csv \
    --summary-csv data_codesearchnet/threshold_sweep/starcoder2-15b-instruct-v0.1/svm_summary.csv \
    --dataset codesearchnet_starcoder2-15b-instruct-v0.1_python_merged \
    --emb ast_ \
    --plot ai-prf \
    --split test
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


METRIC_LABELS = {
    "avg_f1": "Average F1",
    "human_precision": "Human Precision",
    "human_recall": "Human Recall",
    "human_f1": "Human F1",
    "ai_precision": "AI Precision",
    "ai_recall": "AI Recall",
    "ai_f1": "AI F1",
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Plot threshold sweep curves from *_summary_detail.csv."
    )

    p.add_argument("--csv", required=True, help="Path to *_summary_detail.csv")
    p.add_argument("--dataset", required=True, help="Dataset name to plot")
    p.add_argument("--emb", default="ast_", choices=["ast_", "code_", "combined_"])

    p.add_argument(
        "--plot",
        default="single",
        choices=["single", "ai-prf"],
        help="single = plot one metric; ai-prf = plot AI precision/recall/F1 together.",
    )

    p.add_argument(
        "--metric",
        default="ai_f1",
        choices=list(METRIC_LABELS.keys()),
        help="Metric to plot when --plot single.",
    )

    p.add_argument(
        "--split",
        default="test",
        choices=["dev", "test", "both"],
        help="Which split to plot. For paper/report figures, use test.",
    )

    p.add_argument(
        "--summary-csv",
        default=None,
        help="Optional *_summary.csv. If provided, draws best_threshold from this file.",
    )

    p.add_argument(
        "--vline-threshold",
        type=float,
        default=None,
        help="Optional manual vertical threshold line.",
    )

    p.add_argument("--out", default=None, help="Output PNG path")
    p.add_argument("--show", action="store_true", help="Show interactive plot")

    return p.parse_args()


def load_best_threshold(summary_csv, dataset, emb):
    if not summary_csv:
        return None

    path = Path(summary_csv)
    if not path.exists():
        raise SystemExit(f"[ERROR] summary CSV not found: {path}")

    df = pd.read_csv(path)
    required = {"dataset", "emb", "best_threshold"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] missing columns in {path}: {sorted(missing)}")

    sub = df[(df["dataset"] == dataset) & (df["emb"] == emb)]
    if sub.empty:
        print(f"[WARN] no best_threshold row for dataset={dataset}, emb={emb}")
        return None

    return float(sub.iloc[0]["best_threshold"])


def get_filtered(df, dataset, emb, split):
    sub = df[
        (df["dataset"] == dataset) &
        (df["emb"] == emb) &
        (df["split"] == split)
    ].copy()

    if sub.empty:
        return sub

    return sub.sort_values("threshold")


def plot_single_metric(df, args, splits):
    plotted = 0

    for split in splits:
        sub = get_filtered(df, args.dataset, args.emb, split)

        if sub.empty:
            print(f"[WARN] no rows for split={split}, dataset={args.dataset}, emb={args.emb}")
            continue

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

    return plotted, METRIC_LABELS[args.metric]


def plot_ai_prf(df, args, splits):
    metrics = ["ai_precision", "ai_recall", "ai_f1"]
    plotted = 0

    for split in splits:
        sub = get_filtered(df, args.dataset, args.emb, split)

        if sub.empty:
            print(f"[WARN] no rows for split={split}, dataset={args.dataset}, emb={args.emb}")
            continue

        suffix = "" if len(splits) == 1 else f" ({split})"

        for metric in metrics:
            plt.plot(
                sub["threshold"],
                sub[metric],
                marker="o",
                linewidth=1.8,
                markersize=4,
                label=f"{METRIC_LABELS[metric]}{suffix}",
            )

            best_idx = sub[metric].idxmax()
            best = sub.loc[best_idx]
            print(
                f"{split}: best {metric}={best[metric]:.4f} "
                f"at threshold={best['threshold']:.4f}"
            )

        plotted += 1

    return plotted, "AI Precision / Recall / F1"


def main():
    args = parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"[ERROR] detail CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    base_required = {"dataset", "emb", "split", "threshold"}
    if args.plot == "single":
        required = base_required | {args.metric}
    else:
        required = base_required | {"ai_precision", "ai_recall", "ai_f1"}

    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] missing columns in {csv_path}: {sorted(missing)}")

    splits = ["dev", "test"] if args.split == "both" else [args.split]

    plt.figure(figsize=(9, 5.5))

    if args.plot == "single":
        plotted, y_label = plot_single_metric(df, args, splits)
        plot_tag = args.metric
    else:
        plotted, y_label = plot_ai_prf(df, args, splits)
        plot_tag = "ai_prf"

    if plotted == 0:
        raise SystemExit("[ERROR] nothing plotted. Check --dataset, --emb, and --split.")

    # Vertical threshold line.
    vline = args.vline_threshold
    if vline is None:
        vline = load_best_threshold(args.summary_csv, args.dataset, args.emb)

    if vline is not None:
        plt.axvline(
            x=vline,
            linestyle="--",
            linewidth=1.8,
            label=f"dev-selected threshold = {vline:.4f}",
        )
        print(f"vertical line threshold: {vline:.4f}")

    plt.xlabel("Decision threshold")
    plt.ylabel(y_label)

    if args.plot == "single":
        title = f"{y_label} vs Threshold"
    else:
        title = "AI Precision / Recall / F1 vs Threshold"

    plt.title(f"{title}\n{args.dataset} | {args.emb}")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    if args.out is None:
        out_dir = csv_path.parent / "plots"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_dataset = args.dataset.replace("/", "_")
        args.out = out_dir / (
            f"{csv_path.stem}_{safe_dataset}_{args.emb}{plot_tag}_{args.split}.png"
        )
    else:
        args.out = Path(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(args.out, dpi=200)
    print(f"saved: {args.out}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
