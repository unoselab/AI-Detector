#!/usr/bin/env python3
"""
plot_transfer.py
================

Build the cross-generator AUROC transfer figures + LaTeX table from the
per-classifier agc_transfer.csv files produced by compute_agc_transfer.py.

Inputs (one per pinned classifier):
    <root>/clf-<gen>/agc_transfer.csv
each with columns: classifier, target, is_diagonal, ..., auroc, ...

Outputs (into --out-dir):
    auroc_transfer_heatmap.png   (Candidate A) 5x5 matrix, diagonal boxed
    auroc_generalization_gap.png (Candidate B) self vs off-diagonal mean
    auroc_transfer_matrix.tex    LaTeX 5x5 table + off-diagonal "Transfer" col

Reading the matrix
------------------
Rows = the trained (pinned) classifier; columns = the target generator whose
code was scored. The diagonal is the matched in-distribution cell; the
off-diagonal mean is true out-of-distribution generalization. AUROC is
threshold-free, so a bright diagonal with a dim off-diagonal row is the
signature of a generator-overfit detector.

Usage
-----
  python plot_transfer.py \
      --glob "src/app/data_mixed_samples_transfer/clf-*/agc_transfer.csv" \
      --out-dir figures
"""

import argparse
import glob as globmod
import os

import matplotlib
matplotlib.use("Agg")                 # headless: write files, never open a window
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

# Fixed row/column order so the figures match the paper's Table-4 layout, and
# pretty labels for axes/LaTeX. Models not present are dropped from the order.
ORDER = ["starcoder2-15b-instruct-v0.1", "starcoder2-7b",
         "codellama-7b", "gemma", "gpt-oss"]
DISPLAY = {
    "starcoder2-15b-instruct-v0.1": "StarCoder2-15B",
    "starcoder2-7b":                "StarCoder2-7B",
    "codellama-7b":                 "CodeLlama-7B",
    "gemma":                        "Gemma",
    "gpt-oss":                      "GPT-OSS",
}


def disp(tag):
    """Pretty label for a model tag, falling back to the raw tag if unknown."""
    return DISPLAY.get(tag, tag)


def load_all(glob_pattern):
    """
    Read and concatenate every agc_transfer.csv matched by `glob_pattern`.

    Returns one long DataFrame (rows = classifier x target cells). Exits if no
    files match. Each file already carries `classifier`, `target`,
    `is_diagonal`, and the metric columns, so a plain concat is sufficient.
    """
    files = sorted(globmod.glob(glob_pattern))
    if not files:
        raise SystemExit(f"[error] no CSVs matched: {glob_pattern}")
    frames = [pd.read_csv(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    print(f"[info] loaded {len(files)} file(s), {len(df)} cells")
    return df


def build_matrix(df, metric):
    """
    Pivot the long table into a dense classifier x target matrix for `metric`.

    Returns (M, rows, cols):
      rows / cols : model tags present, ordered by ORDER (others appended).
      M           : 2-D float array, M[i, j] = metric for classifier rows[i]
                    on target cols[j]; NaN where a cell is absent.
    """
    present = set(df["classifier"]) | set(df["target"])
    ordered = [m for m in ORDER if m in present] + \
              [m for m in sorted(present) if m not in ORDER]
    rows = [m for m in ordered if m in set(df["classifier"])]
    cols = [m for m in ordered if m in set(df["target"])]

    # Fast lookup of (classifier, target) -> metric value.
    lut = {(r.classifier, r.target): getattr(r, metric)
           for r in df.itertuples(index=False)}
    M = np.full((len(rows), len(cols)), np.nan)
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            if (r, c) in lut:
                M[i, j] = lut[(r, c)]
    return M, rows, cols


def offdiag_mean(M, rows, cols):
    """
    Per-classifier off-diagonal mean (true transfer): for each row, average the
    cells whose target != that classifier. Returns a list aligned with `rows`,
    NaN where a row has no off-diagonal values.
    """
    means = []
    for i, r in enumerate(rows):
        vals = [M[i, j] for j, c in enumerate(cols) if c != r and not np.isnan(M[i, j])]
        means.append(float(np.mean(vals)) if vals else np.nan)
    return means


def diag_values(M, rows, cols):
    """
    Per-classifier diagonal (self / in-distribution) value: the cell where the
    target equals the classifier. Returns a list aligned with `rows`, NaN if
    that self cell is missing.
    """
    out = []
    for i, r in enumerate(rows):
        out.append(M[i, cols.index(r)] if (r in cols and not np.isnan(M[i, cols.index(r)])) else np.nan)
    return out


def plot_heatmap(M, rows, cols, metric, out_dir, dpi):
    """
    Candidate A - AUROC transfer heatmap.

    Colour-encodes M, annotates every present cell with its value, and draws a
    box around each matched-diagonal cell so in-distribution stands out from
    transfer. Missing cells are left blank. Saves a PNG.
    """
    fig, ax = plt.subplots(figsize=(1.3 * len(cols) + 2.5, 1.0 * len(rows) + 2.0),
                           dpi=dpi)
    # Range tuned for AUROC (0.5 = chance .. 1.0 = perfect).
    vmin = np.nanmin([0.5, np.nanmin(M)])
    im = ax.imshow(M, cmap="YlGnBu", vmin=vmin, vmax=1.0, aspect="equal")

    ax.set_xticks(range(len(cols)), [disp(c) for c in cols], rotation=30, ha="right")
    ax.set_yticks(range(len(rows)), [disp(r) for r in rows])
    ax.set_xlabel("Target generator (code scored)")
    ax.set_ylabel("Trained classifier")
    ax.set_title(f"Cross-generator {metric.upper()} transfer matrix")

    # Annotate cells; pick black/white text for contrast against the fill.
    for i in range(len(rows)):
        for j in range(len(cols)):
            if np.isnan(M[i, j]):
                continue
            txt_color = "white" if M[i, j] > (vmin + 1.0) / 2 + 0.08 else "black"
            ax.text(j, i, f"{M[i, j]:.3f}", ha="center", va="center",
                    color=txt_color, fontsize=9)
            # Box the matched diagonal (classifier == target).
            if rows[i] == cols[j]:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                       edgecolor="crimson", lw=2.2))

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(metric.upper())
    fig.tight_layout()
    path = os.path.join(out_dir, f"{metric}_transfer_heatmap.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[info] wrote {path}")


def plot_gap(M, rows, cols, metric, out_dir, dpi):
    """
    Candidate B - generalization-gap dumbbell chart.

    For each classifier, plots the self (diagonal) value and the off-diagonal
    mean as two markers joined by a line; the line length is the generalization
    drop. Sorted by self value descending, with a 0.5 chance reference. Saves a
    PNG.
    """
    selfv = diag_values(M, rows, cols)
    offv = offdiag_mean(M, rows, cols)

    # Sort classifiers by self value (desc) for a tidy ladder.
    idx = sorted(range(len(rows)),
                 key=lambda i: (selfv[i] if not np.isnan(selfv[i]) else -1),
                 reverse=True)
    labels = [disp(rows[i]) for i in idx]
    s = [selfv[i] for i in idx]
    o = [offv[i] for i in idx]
    y = np.arange(len(idx))[::-1]

    fig, ax = plt.subplots(figsize=(7.6, 0.7 * len(rows) + 2.0), dpi=dpi)
    for yi, sv, ov in zip(y, s, o):
        if not (np.isnan(sv) or np.isnan(ov)):
            ax.plot([ov, sv], [yi, yi], color="#bbbbbb", lw=2, zorder=1)
            # Annotate the drop midway along the connector.
            ax.text((ov + sv) / 2, yi + 0.12, f"\u0394{sv - ov:+.3f}",
                    ha="center", fontsize=8, color="#555555")
    ax.scatter(o, y, s=90, color="#d95f02", zorder=3, label="Off-diagonal mean (transfer)")
    ax.scatter(s, y, s=90, color="#1b9e77", zorder=3, label="Diagonal (self / in-distribution)")

    ax.axvline(0.5, ls="--", color="grey", lw=1)
    ax.text(0.5, len(idx) - 0.4, "chance 0.5", color="grey", fontsize=8, ha="center")
    ax.set_yticks(y, labels)
    ax.set_xlabel(metric.upper())
    ax.set_title(f"{metric.upper()} generalization gap (self vs transfer)")
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path = os.path.join(out_dir, f"{metric}_generalization_gap.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[info] wrote {path}")


def emit_latex(M, rows, cols, metric, out_dir):
    """
    Write a LaTeX table: the classifier x target matrix with each matched
    diagonal value \\textbf-bolded and a trailing "Transfer" column holding the
    off-diagonal mean per classifier. Mirrors the paper's Table-4 format.
    """
    offv = offdiag_mean(M, rows, cols)
    colspec = "l|" + "c" * len(cols) + "|c"
    lines = [
        "\\begin{table}[htbp]",
        "\\centering",
        f"\\caption{{Cross-Generator {metric.upper()} Transfer Matrix "
        "(diagonal = in-distribution; Transfer = off-diagonal mean)}",
        f"\\label{{tab:cross_generator_{metric}}}",
        f"\\begin{{tabular}}{{{colspec}}}",
        "\\hline",
    ]
    header = ["\\textbf{Trained Classifier}"] + \
             [f"\\textbf{{{disp(c)}}}" for c in cols] + ["\\textbf{Transfer}"]
    lines.append(" & ".join(header) + " \\\\ \\hline")

    for i, r in enumerate(rows):
        cells = []
        for j, c in enumerate(cols):
            v = M[i, j]
            if np.isnan(v):
                cells.append("--")
            elif rows[i] == cols[j]:
                cells.append(f"\\textbf{{{v:.4f}}}")   # bold the diagonal
            else:
                cells.append(f"{v:.4f}")
        tr = "--" if np.isnan(offv[i]) else f"{offv[i]:.4f}"
        lines.append(f"{disp(r):<16} & " + " & ".join(cells) + f" & {tr} \\\\")

    lines += ["\\hline", "\\end{tabular}", "\\end{table}", ""]
    path = os.path.join(out_dir, f"{metric}_transfer_matrix.tex")
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
    print(f"[info] wrote {path}")
    # Echo to console so it can be copied straight from the run output.
    print("\n" + "\n".join(lines))


def parse_args():
    """Define the CLI: input glob, metric, output dir, and raster dpi."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glob",
                    default="src/app/data_mixed_samples_transfer/clf-*/agc_transfer.csv",
                    help="Glob for the per-classifier agc_transfer.csv files.")
    ap.add_argument("--metric", default="auroc",
                    help="Metric column to plot (default: auroc).")
    ap.add_argument("--out-dir", default="figures")
    ap.add_argument("--dpi", type=int, default=150)
    return ap.parse_args()


def main():
    """Load CSVs, build the matrix, then emit heatmap + gap PNGs and LaTeX."""
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    df = load_all(args.glob)
    if args.metric not in df.columns:
        raise SystemExit(f"[error] metric '{args.metric}' not in columns: {list(df.columns)}")

    M, rows, cols = build_matrix(df, args.metric)
    plot_heatmap(M, rows, cols, args.metric, args.out_dir, args.dpi)   # Candidate A
    plot_gap(M, rows, cols, args.metric, args.out_dir, args.dpi)       # Candidate B
    emit_latex(M, rows, cols, args.metric, args.out_dir)              # LaTeX table


if __name__ == "__main__":
    main()