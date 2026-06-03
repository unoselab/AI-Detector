#!/usr/bin/env python3
"""
plot_transfer_results.py
========================

Plot cross-generator transfer results from per-classifier agc_transfer.csv files.

Expected input layout, from the repository root or paper directory:

  src/app/data_mixed_samples_transfer/clf-<MODEL>/agc_transfer.csv

or

  data_mixed_samples_transfer/clf-<MODEL>/agc_transfer.csv

Each agc_transfer.csv is expected to contain at least:
  target, auroc, agc_f1
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Fixed model order and paper-friendly display names.
MODEL_ORDER = [
    "codellama-7b",
    "gemma",
    "gpt-oss",
    "starcoder2-15b-instruct-v0.1",
    "starcoder2-7b",
]

SHORT_NAMES = {
    "codellama-7b": "CodeLlama-7B",
    "gemma": "Gemma",
    "gpt-oss": "GPT-OSS",
    "starcoder2-15b-instruct-v0.1": "SC2-15B",
    "starcoder2-7b": "SC2-7B",
}

# Extra aliases that may appear in CSVs, directory names, or earlier plots.
ALIASES = {
    "codellama": "codellama-7b",
    "codellama-7b": "codellama-7b",
    "cl-7b": "codellama-7b",
    "codellama7b": "codellama-7b",
    "gemma": "gemma",
    "gemma4-31b": "gemma",
    "gm-31b": "gemma",
    "gpt-oss": "gpt-oss",
    "gptoss": "gpt-oss",
    "go-120b": "gpt-oss",
    "starcoder2-15b": "starcoder2-15b-instruct-v0.1",
    "starcoder2-15b-instruct-v0.1": "starcoder2-15b-instruct-v0.1",
    "sc-15b": "starcoder2-15b-instruct-v0.1",
    "sc2-15b": "starcoder2-15b-instruct-v0.1",
    "starcoder2-7b": "starcoder2-7b",
    "sc-7b": "starcoder2-7b",
    "sc2-7b": "starcoder2-7b",
}


def canonical_model_name(value):
    """
    Map a raw target/classifier string to one canonical model id.

    The old code called tgt.startswith(m.split('-')), but m.split('-') returns
    a list, and str.startswith() only accepts a string or tuple of strings.
    This helper avoids that type error and handles full experiment directory
    names such as:

      starcoder2-7b_4500_complexity_stratified_maxlen2048
      src/app/data_mixed_samples/.../gpt-oss_4500.../50x6
    """
    raw = str(value or "").strip()
    low = raw.lower()

    # Remove common path and experiment wrappers while keeping enough text for
    # substring matching.
    low = low.replace("clf-", "")
    low = low.replace("/50x6", "")

    # Exact alias match first.
    if low in ALIASES:
        return ALIASES[low]

    # Exact canonical match, prefix match, or substring match. This covers long
    # experiment names like <model>_4500_complexity_stratified_maxlen2048.
    for model in sorted(MODEL_ORDER, key=len, reverse=True):
        if low == model or low.startswith(model) or model in low:
            return model

    # Last-resort alias substring match.
    for alias, model in sorted(ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if alias in low:
            return model

    return None


def find_transfer_csv(clf):
    """Return the first existing agc_transfer.csv path for a classifier."""
    candidates = [
        Path("src/app/data_mixed_samples_transfer") / f"clf-{clf}" / "agc_transfer.csv",
        Path("data_mixed_samples_transfer") / f"clf-{clf}" / "agc_transfer.csv",
    ]

    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def load_and_stitch_data():
    """Read the five agc_transfer.csv files and combine them into one long DataFrame."""
    all_rows = []

    for clf in MODEL_ORDER:
        csv_path = find_transfer_csv(clf)

        if not csv_path.exists():
            print(f"[Warning] Missing file: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        required = {"target", "auroc", "agc_f1"}
        missing = required - set(df.columns)
        if missing:
            print(f"[Warning] Skipping {csv_path}; missing columns: {sorted(missing)}")
            continue

        for _, row in df.iterrows():
            tgt_matched = canonical_model_name(row["target"])

            if tgt_matched is None:
                print(f"[Warning] Could not match target={row['target']!r} in {csv_path}")
                continue

            all_rows.append(
                {
                    "Classifier": SHORT_NAMES[clf],
                    "Target": SHORT_NAMES[tgt_matched],
                    "AUROC": float(row["auroc"]),
                    "AGC_F1": float(row["agc_f1"]),
                    "is_diagonal": clf == tgt_matched,
                }
            )

    return pd.DataFrame(all_rows)


def make_pivot(df, metric="AUROC"):
    """Return a complete classifier-by-target matrix for the requested metric."""
    clfs = [SHORT_NAMES[m] for m in MODEL_ORDER]
    pivot_df = df.pivot_table(
        index="Classifier",
        columns="Target",
        values=metric,
        aggfunc="mean",
    )
    return pivot_df.reindex(index=clfs, columns=clfs)


def plot_candidate_a_heatmap(df, metric="AUROC"):
    """Candidate A: plot the cross-generator transfer heatmap matrix."""
    pivot_df = make_pivot(df, metric=metric)

    plt.figure(figsize=(7, 5.5))
    sns.set_theme(style="white")

    ax = sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".4f",
        cmap="Blues",
        cbar_kws={"label": metric},
        linewidths=0.5,
        annot_kws={"size": 11, "weight": "bold"},
    )

    # Highlight same-source cells.
    for i in range(len(pivot_df)):
        ax.add_patch(
            plt.Rectangle((i, i), 1, 1, fill=False, edgecolor="red", lw=2.5, clip_on=False)
        )

    plt.title(f"Cross-Generator Transfer Matrix ({metric})", fontsize=13, pad=15, weight="bold")
    plt.ylabel("Trained Classifier (Source)", fontsize=11, labelpad=10)
    plt.xlabel("Tested Generator (Target)", fontsize=11, labelpad=10)
    plt.tight_layout()

    filename = f"transfer_heatmap_{metric.lower()}.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"[Success] Saved Heatmap Matrix to: {filename}")
    plt.close()


def plot_candidate_b_gap_chart(df, metric="AUROC"):
    """Candidate B: plot same-source vs off-diagonal transfer-average gap."""
    classifiers = [SHORT_NAMES[m] for m in MODEL_ORDER]

    rows = []
    for clf in classifiers:
        self_series = df[(df["Classifier"] == clf) & (df["Target"] == clf)][metric]
        transfer_series = df[(df["Classifier"] == clf) & (df["Target"] != clf)][metric]

        self_val = float(self_series.iloc[0]) if not self_series.empty else np.nan
        transfer_mean = float(transfer_series.mean()) if not transfer_series.empty else np.nan

        rows.append(
            {
                "Classifier": clf,
                "Self": self_val,
                "Transfer_Avg": transfer_mean,
                "Gap": self_val - transfer_mean,
            }
        )

    gap_df = pd.DataFrame(rows).dropna(subset=["Self", "Transfer_Avg"])
    gap_df = gap_df.sort_values("Transfer_Avg", ascending=True)

    if gap_df.empty:
        print(f"[Warning] No usable rows for {metric} gap chart.")
        return

    plt.figure(figsize=(6.5, 4.5))
    sns.set_style("whitegrid")

    plt.hlines(
        y=gap_df["Classifier"],
        xmin=gap_df["Transfer_Avg"],
        xmax=gap_df["Self"],
        color="grey",
        alpha=0.5,
        linewidth=2.5,
    )

    plt.scatter(
        gap_df["Self"],
        gap_df["Classifier"],
        color="darkblue",
        alpha=0.9,
        s=120,
        marker="*",
        label="In-Distribution (Self)",
    )
    plt.scatter(
        gap_df["Transfer_Avg"],
        gap_df["Classifier"],
        color="darkorange",
        alpha=0.9,
        s=100,
        marker="o",
        label="Pure Transfer Avg (Off-Diag)",
    )

    for _, row in gap_df.iterrows():
        mid_x = (row["Self"] + row["Transfer_Avg"]) / 2.0
        plt.text(
            mid_x,
            row["Classifier"],
            f"  Gap: {row['Gap']:.3f}",
            va="bottom",
            ha="center",
            fontsize=9,
            color="brown",
            weight="bold",
        )

    plt.title(f"Generalization Gap Analysis ({metric})", fontsize=12, pad=15, weight="bold")
    plt.xlabel(f"{metric} Score", fontsize=11)

    xmin = max(0.0, float(df[metric].min()) - 0.05)
    xmax = min(1.0, float(df[metric].max()) + 0.05)
    if xmax <= xmin:
        xmax = min(1.0, xmin + 0.1)
    plt.xlim(xmin, xmax)

    plt.legend(loc="lower left", frameon=True)
    plt.tight_layout()

    filename = f"transfer_gap_{metric.lower()}.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"[Success] Saved Generalization Gap Chart to: {filename}")
    plt.close()


def fmt_cell(value, bold=False):
    """Format one numeric LaTeX table cell, preserving missing values as '--'."""
    if pd.isna(value):
        text = "--"
    else:
        text = f"{float(value):.4f}"
    return f"\\textbf{{{text}}}" if bold else text


def print_latex_matrix(df, metric="AUROC"):
    """Print LaTeX code for the transfer matrix table."""
    pivot_df = make_pivot(df, metric=metric)
    clfs = [SHORT_NAMES[m] for m in MODEL_ORDER]

    print("\n" + "=" * 80)
    print(f" LaTeX Code for {metric} Transfer Matrix Table")
    print("=" * 80)
    print("\\begin{table}[htbp]")
    print("\\centering")
    print(f"\\caption{{Cross-generator transfer matrix measured by function-level {metric}.}}")
    print(f"\\label{{tab:transfer_matrix_{metric.lower()}}}")
    print("\\begin{tabular}{lcccccc}")
    print("\\hline")
    print(
        "\\textbf{Classifier} & "
        + " & ".join([f"\\textbf{{{c}}}" for c in clfs])
        + " & \\textbf{Pure Transfer Avg} \\\\ \\hline"
    )

    for clf in clfs:
        row_str = f"\\textbf{{{clf}}}"
        pure_vals = []
        for tgt in clfs:
            val = pivot_df.loc[clf, tgt]
            row_str += " & " + fmt_cell(val, bold=(clf == tgt))
            if clf != tgt and not pd.isna(val):
                pure_vals.append(float(val))

        pure_avg = np.mean(pure_vals) if pure_vals else np.nan
        row_str += " & " + fmt_cell(pure_avg) + " \\\\"
        print(row_str)

    print("\\hline")
    print("\\end{tabular}")
    print("\\end{table}\n")


def main():
    data = load_and_stitch_data()
    if data.empty:
        print("[Error] No data loaded. Check your file paths.")
        return

    plot_candidate_a_heatmap(data, metric="AUROC")
    plot_candidate_b_gap_chart(data, metric="AUROC")
    print_latex_matrix(data, metric="AUROC")

    # Generate AGC F1 versions only if the column is available.
    if "AGC_F1" in data.columns:
        plot_candidate_a_heatmap(data, metric="AGC_F1")
        plot_candidate_b_gap_chart(data, metric="AGC_F1")


if __name__ == "__main__":
    main()
