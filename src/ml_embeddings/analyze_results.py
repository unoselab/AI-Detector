"""
analyze_results.py
==================

Aggregate the per-sample prediction CSVs written by test_embedding.py (via
run5b) into ONE tidy metrics table across all classifier families, and
optionally emit a paper-ready LaTeX table.

It does NOT re-run any model. It reads each prediction CSV and RECOMPUTES the
seven metrics directly from the stored columns, so the result is fully
reproducible from disk:
  ACC, TPR, TNR, Human_F1, AI_F1, Avg_F1   (from `actual label` vs `pred`)
  AUROC                                    (from `actual label` vs `score`)

Input layout (produced by run5b)
--------------------------------
  <predictions-root>/
      <RUN_TAG>/                                  # e.g. codesearchnet_<model>_<family>_<TS>
          <dataset_folder>__<emb>.csv             # emb in {ast, code, combined}
Each CSV has columns:
  idx, code, ast, actual label, pred, score, score_mode

Output
------
* --out-csv    : tidy long table, one row per (family, dataset, emb):
      run_tag, family, dataset, emb, n_test,
      acc, tpr, tnr, human_f1, ai_f1, avg_f1, auroc, score_mode
* --latex-out  : (optional) a booktabs LaTeX table, families x embedding-type,
      with the chosen metrics per embedding and the best value per column
      bolded. Rows are ordered by mean AUROC (best first).
* Stdout       : the table sorted by AUROC, plus a per-family mean-AUROC rank.

Convention: label 1 == human (positive class), label 0 == AI -- identical to
test_embedding.py, so these numbers match the logged ones.

Usage
-----
  python analyze_results.py \
      --predictions-root data_codesearchnet/predictions/<MODEL_NAME> \
      --out-csv          data_codesearchnet/analysis/<MODEL_NAME>/metrics.csv \
      --latex-out        data_codesearchnet/analysis/<MODEL_NAME>/metrics.tex \
      --latex-metrics    avg_f1,auroc
"""

import argparse
import os
import re

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score


# Only these columns are needed; reading just them avoids pulling the large,
# multi-line `code` / `ast` text into memory.
NEEDED_COLS = ["actual label", "pred", "score", "score_mode"]

# A RUN_TAG ends with <family>_<YYYYMMDD>_<HHMMSS>; this captures the family.
FAMILY_RE = re.compile(r"_([A-Za-z0-9]+)_\d{8}_\d{6}$")

# Canonical emb display order for the printed/LaTeX summaries.
EMB_ORDER = ["ast", "combined", "code"]

# Metrics that may legally be requested in the LaTeX table.
ALLOWED_METRICS = ["acc", "tpr", "tnr", "human_f1", "ai_f1", "avg_f1", "auroc"]

# Display labels for the LaTeX table (underscores already TeX-escaped).
DISPLAY_FAMILY = {
    "lr": "LR", "svm": "SVM", "mlp": "MLP", "rf": "RF", "gb": "GB",
    "knn": "KNN", "dt": "DT", "et": "ET", "ada": "AdaBoost",
    "hgb": "HGB", "xgb": "XGBoost",
}
DISPLAY_EMB = {"ast": "AST", "combined": "Combined", "code": "Code"}
DISPLAY_METRIC = {
    "acc": "ACC", "tpr": "TPR", "tnr": "TNR",
    "human_f1": "Human\\_F1", "ai_f1": "AI\\_F1",
    "avg_f1": "Avg\\_F1", "auroc": "AUROC",
}

# Number of decimals used in the LaTeX cells.
LATEX_DECIMALS = 5


def parse_family(run_tag):
    """
    Extract the classifier family token from a RUN_TAG directory name.

    run5b/run4a name the dir <EXPERIMENT_TAG>_<family>_<YYYYMMDD>_<HHMMSS>, so
    the family is the alphanumeric token right before the date/time suffix
    (e.g. ..._lr_20260530_202123 -> "lr"). Returns None if the name does not
    match, which lets the caller skip non-run dirs (logs, the analysis dir).
    """
    m = FAMILY_RE.search(run_tag)
    return m.group(1) if m else None


def parse_dataset_emb(filename):
    """
    Split a prediction CSV filename into (dataset_folder, emb).

    test_embedding.py writes "<dataset_folder>__<emb>.csv" with emb stripped of
    its trailing underscore (ast / code / combined). We rsplit on the LAST
    "__" so dataset names that themselves contain "__" are handled correctly.
    Returns (dataset, emb), or (stem, "") if no "__" separator is present.
    """
    stem = filename[:-4] if filename.endswith(".csv") else filename
    if "__" in stem:
        dataset, emb = stem.rsplit("__", 1)
        return dataset, emb
    return stem, ""


def metrics_from_frame(df):
    """
    Recompute the seven metrics for one prediction CSV.

    Threshold-dependent metrics come from `actual label` vs `pred`; AUROC is
    threshold-independent and comes from `actual label` vs the continuous
    `score`. AUROC degrades to NaN (never raises) when it is undefined:
      * no usable `score` column / all scores NaN -> nothing to rank;
      * only one class present in the truth       -> ROC undefined.

    Returns a dict of {n_test, acc, tpr, tnr, human_f1, ai_f1, avg_f1, auroc,
    score_mode}. score_mode is taken from the first row (constant within a
    file) for transparency about how AUROC was scored.
    """
    y_true = df["actual label"].to_numpy()
    y_pred = df["pred"].to_numpy()

    acc      = accuracy_score(y_true, y_pred)
    human_f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    ai_f1    = f1_score(y_true, y_pred, pos_label=0, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    tpr = tp / max(tp + fn, 1)   # human recall
    tnr = tn / max(tn + fp, 1)   # AI recall

    # score_mode is informational; default to "n/a" if the column is absent.
    score_mode = "n/a"
    if "score_mode" in df.columns and len(df):
        score_mode = str(df["score_mode"].iloc[0])

    # AUROC, guarded against the undefined cases.
    auroc = float("nan")
    if "score" in df.columns:
        scores = pd.to_numeric(df["score"], errors="coerce").to_numpy()
        both_classes = len(np.unique(y_true)) >= 2
        if both_classes and not np.isnan(scores).all():
            try:
                auroc = roc_auc_score(y_true, scores)
            except Exception:
                auroc = float("nan")

    return {
        "n_test":   int(len(df)),
        "acc":      acc,
        "tpr":      tpr,
        "tnr":      tnr,
        "human_f1": human_f1,
        "ai_f1":    ai_f1,
        "avg_f1":   (human_f1 + ai_f1) / 2,
        "auroc":    auroc,
        "score_mode": score_mode,
    }


def collect_rows(predictions_root):
    """
    Walk every RUN_TAG dir under predictions_root and build one metrics row per
    prediction CSV.

    Skips any subdirectory whose name does not parse as a RUN_TAG (so stray
    files or an analysis dir nested here are ignored). For each valid CSV it
    reads only NEEDED_COLS and appends a row tagged with run_tag/family/
    dataset/emb. Returns a list of dict rows (possibly empty).
    """
    rows = []
    for entry in sorted(os.listdir(predictions_root)):
        run_dir = os.path.join(predictions_root, entry)
        if not os.path.isdir(run_dir):
            continue
        family = parse_family(entry)
        if family is None:
            continue  # not a run5b/run4a predictions dir

        for fname in sorted(os.listdir(run_dir)):
            if not fname.endswith(".csv"):
                continue
            dataset, emb = parse_dataset_emb(fname)
            fpath = os.path.join(run_dir, fname)

            # Read only the columns we need; tolerate older CSVs that may lack
            # score/score_mode by intersecting with the actual header.
            header = pd.read_csv(fpath, nrows=0).columns
            usecols = [c for c in NEEDED_COLS if c in header]
            df = pd.read_csv(fpath, usecols=usecols)

            m = metrics_from_frame(df)
            row = {"run_tag": entry, "family": family,
                   "dataset": dataset, "emb": emb}
            row.update(m)
            rows.append(row)
    return rows


def _tex_escape_caption(text):
    """
    Minimal TeX-escaping for caption text.

    The model name carries underscores that would otherwise be interpreted as
    subscripts in LaTeX; escape them. (Labels keep underscores, which are legal
    inside \\label, so they are handled separately by the caller.)
    """
    return text.replace("\\", r"\textbackslash{}").replace("_", r"\_")


def _fmt_tex(v):
    """Format a metric value for a LaTeX cell; NaN -> en-dash placeholder."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "--"
    return f"{v:.{LATEX_DECIMALS}f}"


def build_latex_table(df, metrics, caption, label):
    """
    Build a booktabs LaTeX table: rows = classifier family, columns grouped by
    embedding type, with the requested `metrics` under each group.

    Aggregation: values are the MEAN of each metric over all (dataset, run_tag)
    rows for a given (family, emb). With a single dataset and one run per
    family this mean is just the value itself; with several it collapses them
    sensibly so the table stays families x embeddings.

    Layout details:
      * Families are ordered by mean AUROC (best first), matching the stdout
        ranking.
      * The best value in each (embedding, metric) column is bolded.
      * NaN cells render as "--".
    Requires booktabs (\\toprule/\\midrule/\\bottomrule/\\cmidrule) in the
    document preamble. Returns the full table as a string.
    """
    # Work on a copy with emb as plain strings (avoids categorical surprises).
    d = df.copy()
    d["emb"] = d["emb"].astype(str)

    # Embedding columns actually present, in canonical order.
    present = set(d["emb"])
    embs = [e for e in EMB_ORDER if e in present]

    # Row order: families by mean AUROC, descending.
    order = (d.groupby("family")["auroc"].mean()
               .sort_values(ascending=False).index.tolist())

    # One families x embeddings pivot per requested metric (mean-aggregated).
    pivots = {}
    for mt in metrics:
        p = d.groupby(["family", "emb"])[mt].mean().unstack("emb")
        pivots[mt] = p.reindex(index=order, columns=embs)

    # Per-column maxima for bolding (NaN-safe).
    col_max = {}
    for e in embs:
        for mt in metrics:
            col = pivots[mt][e]
            col_max[(e, mt)] = (np.nanmax(col.to_numpy())
                                if col.notna().any() else float("nan"))

    nmet = len(metrics)

    # tabular column spec: a left-aligned label column, then nmet centered
    # columns per embedding group.
    spec = "l" + "".join(" " + "c" * nmet for _ in embs)

    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(r"\caption{" + _tex_escape_caption(caption) + "}")
    lines.append(r"\label{" + label + "}")
    lines.append(r"\begin{tabular}{" + spec + "}")
    lines.append(r"\toprule")

    # Top header: one multicolumn per embedding group.
    top = [""]
    for e in embs:
        top.append(r"\multicolumn{%d}{c}{%s}" % (nmet, DISPLAY_EMB.get(e, e.title())))
    lines.append(" & ".join(top) + r" \\")

    # cmidrules underlining each embedding group.
    cmid, start = [], 2
    for _ in embs:
        end = start + nmet - 1
        cmid.append(r"\cmidrule(lr){%d-%d}" % (start, end))
        start = end + 1
    lines.append("".join(cmid))

    # Sub header: the metric names repeated under each group.
    sub = ["Classifier"]
    for _ in embs:
        for mt in metrics:
            sub.append(DISPLAY_METRIC.get(mt, mt))
    lines.append(" & ".join(sub) + r" \\")
    lines.append(r"\midrule")

    # Body rows.
    for fam in order:
        cells = [DISPLAY_FAMILY.get(fam, fam.upper())]
        for e in embs:
            for mt in metrics:
                v = pivots[mt].loc[fam, e]
                s = _fmt_tex(v)
                mx = col_max[(e, mt)]
                # Bold the column-best value (NaN-safe, float-tolerant).
                if (not (isinstance(v, float) and np.isnan(v))
                        and not np.isnan(mx) and np.isclose(v, mx)):
                    s = r"\textbf{" + s + "}"
                cells.append(s)
        lines.append(" & ".join(cells) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    return "\n".join(lines) + "\n"


def parse_args():
    """Parse CLI arguments (inputs, CSV output, and optional LaTeX output)."""
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--predictions-root", required=True,
                    help="Root dir holding per-RUN_TAG prediction subdirs.")
    ap.add_argument("--out-csv", required=True,
                    help="Where to write the tidy metrics table.")
    ap.add_argument("--latex-out", default=None,
                    help="Optional path to also write a LaTeX table.")
    ap.add_argument("--latex-metrics", default="avg_f1,auroc",
                    help="Comma-separated metrics per embedding in the LaTeX "
                         "table (subset of: " + ",".join(ALLOWED_METRICS) + ").")
    ap.add_argument("--latex-caption", default="Detection metrics by classifier and embedding type.",
                    help="Caption text for the LaTeX table.")
    ap.add_argument("--latex-label", default="tab:rq2d_metrics",
                    help="\\label for the LaTeX table.")
    return ap.parse_args()


def main():
    """
    Build the tidy metrics table, write it to --out-csv, optionally write a
    LaTeX table, and print the AUROC-sorted table plus a per-family ranking.
    """
    args = parse_args()

    rows = collect_rows(args.predictions_root)
    if not rows:
        raise SystemExit(
            f"[ERROR] no prediction CSVs found under {args.predictions_root}"
        )

    df = pd.DataFrame(rows)

    # Stable column order for the output file.
    cols = ["run_tag", "family", "dataset", "emb", "n_test",
            "acc", "tpr", "tnr", "human_f1", "ai_f1", "avg_f1",
            "auroc", "score_mode"]
    df = df[cols]

    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    df.to_csv(args.out_csv, index=False)
    print(f"Wrote {len(df)} rows -> {args.out_csv}\n")

    # --- Optional LaTeX table ----------------------------------------------
    if args.latex_out:
        # Validate and order the requested metrics against the allow-list.
        requested = [m.strip() for m in args.latex_metrics.split(",") if m.strip()]
        bad = [m for m in requested if m not in ALLOWED_METRICS]
        if bad:
            raise SystemExit(f"[ERROR] unknown --latex-metrics: {bad}; "
                             f"choose from {ALLOWED_METRICS}")
        tex = build_latex_table(df, requested, args.latex_caption, args.latex_label)
        os.makedirs(os.path.dirname(args.latex_out) or ".", exist_ok=True)
        with open(args.latex_out, "w") as f:
            f.write(tex)
        print(f"Wrote LaTeX table ({','.join(requested)}) -> {args.latex_out}\n")

    # --- View 1: full table, sorted by emb then AUROC (best first) ----------
    print("=" * 78)
    print("Per (family, emb) metrics  [sorted by emb, then AUROC desc]")
    print("=" * 78)
    df["emb"] = pd.Categorical(df["emb"], categories=EMB_ORDER, ordered=True)
    view = df.sort_values(["emb", "auroc"], ascending=[True, False])
    for _, r in view.iterrows():
        print(f"  {str(r['emb']):9s} {r['family']:4s}  "
              f"ACC={r['acc']:.4f}  AvgF1={r['avg_f1']:.4f}  AUROC={r['auroc']:.4f}  "
              f"({r['score_mode']})")

    # --- View 2: per-family mean AUROC across embedding types ---------------
    print()
    print("=" * 78)
    print("Per-family mean AUROC (averaged over embedding types)  [best first]")
    print("=" * 78)
    by_family = (df.groupby("family", observed=True)["auroc"]
                   .agg(lambda s: np.nanmean(s.to_numpy()))
                   .sort_values(ascending=False))
    for fam, val in by_family.items():
        print(f"  {fam:4s}  mean AUROC = {val:.4f}")


if __name__ == "__main__":
    main()