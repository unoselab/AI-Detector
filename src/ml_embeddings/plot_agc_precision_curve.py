#!/usr/bin/env python3
"""
plot_agc_precision_curve.py

Plot AGC/AI precision versus decision threshold.

This is intended for high-confidence AGC detection analysis:
  x-axis: SVM decision threshold
  y-axis: AI precision

The selected threshold should come from dev-set tuning, while the curve can
show test-set behavior for reporting.
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def parse_args():
    p = argparse.ArgumentParser()

    p.add_argument("--detail-csv", required=True,
                   help="Path to svm_summary_detail.csv")
    p.add_argument("--summary-csv", default=None,
                   help="Optional svm_summary.csv for dev-selected threshold")
    p.add_argument("--dataset", required=True)
    p.add_argument("--emb", default="ast_", choices=["ast_", "code_", "combined_"])
    p.add_argument("--split", default="test", choices=["dev", "test", "both"])
    p.add_argument("--out", default=None)
    p.add_argument("--show", action="store_true")

    return p.parse_args()


def load_selected_threshold(summary_csv, dataset, emb):
    if summary_csv is None:
        return None, None

    df = pd.read_csv(summary_csv)
    row = df[(df["dataset"] == dataset) & (df["emb"] == emb)]

    if row.empty:
        print(f"[WARN] no selected threshold found for dataset={dataset}, emb={emb}")
        return None, None

    row = row.iloc[0]
    return float(row["best_threshold"]), row


def main():
    args = parse_args()

    detail_path = Path(args.detail_csv)
    df = pd.read_csv(detail_path)

    required = {
        "dataset",
        "emb",
        "split",
        "threshold",
        "ai_precision",
        "ai_recall",
        "ai_f1",
    }
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] missing columns: {sorted(missing)}")

    splits = ["dev", "test"] if args.split == "both" else [args.split]

    selected_threshold, selected_row = load_selected_threshold(
        args.summary_csv, args.dataset, args.emb
    )

    plt.figure(figsize=(9, 5.5))

    plotted = 0
    for split in splits:
        sub = df[
            (df["dataset"] == args.dataset)
            & (df["emb"] == args.emb)
            & (df["split"] == split)
        ].copy()

        if sub.empty:
            print(f"[WARN] no rows for split={split}")
            continue

        sub = sub.sort_values("threshold")

        plt.plot(
            sub["threshold"],
            sub["ai_precision"],
            marker="o",
            linewidth=1.8,
            markersize=4,
            label=f"{split} AI precision",
        )

        best_idx = sub["ai_precision"].idxmax()
        best = sub.loc[best_idx]
        print(
            f"{split}: max AI precision={best['ai_precision']:.4f} "
            f"at threshold={best['threshold']:.4f}; "
            f"AI recall={best['ai_recall']:.4f}, AI F1={best['ai_f1']:.4f}"
        )

        plotted += 1

    if plotted == 0:
        raise SystemExit("[ERROR] nothing plotted")

    if selected_threshold is not None:
        plt.axvline(
            selected_threshold,
            linestyle="--",
            linewidth=1.8,
            label=f"dev-selected threshold = {selected_threshold:.4f}",
        )

        # Mark selected threshold on test curve if available.
        test_sub = df[
            (df["dataset"] == args.dataset)
            & (df["emb"] == args.emb)
            & (df["split"] == "test")
        ].copy()

        if not test_sub.empty:
            nearest_idx = (test_sub["threshold"] - selected_threshold).abs().idxmin()
            selected_test = test_sub.loc[nearest_idx]

            plt.scatter(
                [selected_test["threshold"]],
                [selected_test["ai_precision"]],
                s=80,
                zorder=5,
                label=(
                    "selected test point "
                    f"(P={selected_test['ai_precision']:.4f}, "
                    f"R={selected_test['ai_recall']:.4f})"
                ),
            )

            print()
            print("Selected threshold test-side metrics:")
            print(f"  threshold    : {selected_test['threshold']:.4f}")
            print(f"  AI precision : {selected_test['ai_precision']:.4f}")
            print(f"  AI recall    : {selected_test['ai_recall']:.4f}")
            print(f"  AI F1        : {selected_test['ai_f1']:.4f}")

    plt.axvline(
        0.0,
        linestyle=":",
        linewidth=1.5,
        label="default SVM threshold = 0.0",
    )

    plt.xlabel("Decision threshold")
    plt.ylabel("AI precision")
    plt.title(
        "AI Precision vs Decision Threshold\n"
        f"{args.dataset} | {args.emb}"
    )
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    if args.out is None:
        out_dir = detail_path.parent / "plots"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_dataset = args.dataset.replace("/", "_")
        args.out = out_dir / f"{detail_path.stem}_{safe_dataset}_{args.emb}ai_precision_{args.split}.png"
    else:
        args.out = Path(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(args.out, dpi=200)
    print()
    print(f"saved: {args.out}")

    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
