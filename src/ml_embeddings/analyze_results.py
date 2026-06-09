"""
analyze_results.py
==================

Aggregate the per-sample prediction CSVs written by test_embedding.py (via
run5b) into ONE tidy metrics table across all classifier families.

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
* --out-csv : tidy long table, one row per (family, dataset, emb):
      run_tag, family, dataset, emb, n_test,
      acc, tpr, tnr, human_f1, ai_f1, avg_f1, auroc, score_mode
* Stdout    : the table sorted by AUROC, plus a per-family mean-AUROC ranking.

Convention: label 1 == human (positive class), label 0 == AI -- identical to
test_embedding.py, so these numbers match the logged ones.

Usage
-----
  python analyze_results.py \
      --predictions-root data_codesearchnet/predictions/<MODEL_NAME> \
      --out-csv          data_codesearchnet/analysis/<MODEL_NAME>/metrics.csv
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

# Canonical emb display order for the printed summary.
EMB_ORDER = ["ast", "combined", "code"]


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
    score_mode}. score_mode is taken from the first row (it is constant within
    a file) for transparency about how AUROC was scored.
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


def parse_args():
    """Parse CLI arguments (predictions root + output CSV path)."""
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--predictions-root", required=True,
                    help="Root dir holding per-RUN_TAG prediction subdirs.")
    ap.add_argument("--out-csv", required=True,
                    help="Where to write the tidy metrics table.")
    return ap.parse_args()


def main():
    """
    Build the tidy metrics table, write it to --out-csv, and print two views:
    the full table sorted by AUROC, and a per-family mean-AUROC ranking.
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

    # --- View 1: full table, sorted by emb then AUROC (best first) ----------
    print("=" * 78)
    print("Per (family, emb) metrics  [sorted by emb, then AUROC desc]")
    print("=" * 78)
    # Categorical emb order so ast/combined/code print in a sensible order.
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
    # nanmean so a family with one undefined fold is not dropped entirely.
    by_family = (df.groupby("family")["auroc"]
                   .agg(lambda s: np.nanmean(s.to_numpy()))
                   .sort_values(ascending=False))
    for fam, val in by_family.items():
        print(f"  {fam:4s}  mean AUROC = {val:.4f}")


if __name__ == "__main__":
    main()