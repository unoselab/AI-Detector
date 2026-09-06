#!/usr/bin/env python3
"""
compute_agc_transfer_same_test.py
=================================

Run the run4c 5x5 cross-generator transfer experiment on the exact held-out
Table (1) test splits.

Design
------
Table (1) evaluates one validation-selected classifier/representation per AGC
generation source on that source's complexity-balanced held-out test split.
Run4c reuses those exact five held-out test CSVs as the target supports. For
each source-trained frozen classifier, run4c scores all five target test sets
without retraining. Therefore, the only factor that changes across a row is the
target generator.

This design intentionally separates cross-generator robustness from the
mixed-authorship integration check used in run4b. The diagonal cells must
reproduce the published Table (1) AST AUROCs to four decimal places.

Inputs
------
Under --ml-root (default: src/ml_embeddings/data_codesearchnet):

  splits/<experiment>/<dataset>/test_.csv
  models/<experiment>/<selected-model-pickle>.pkl

The five selected Table (1) configurations are frozen below:

  CL-7B    : SVM + AST, expected diagonal AUROC 0.7950
  SC2-7B   : SVM + AST, expected diagonal AUROC 0.7689
  SC2-15B  : SVM + AST, expected diagonal AUROC 0.7666
  GO-120B  : MLP + AST, expected diagonal AUROC 0.8837
  GM4-31B  : LR  + AST, expected diagonal AUROC 0.7767

Outputs
-------
Under --output-root:

  cell_metrics.csv
      One row per source-target cell with AUROC and threshold-dependent metrics.

  matrix_auroc.csv
      The 5x5 AUROC matrix plus the four-target off-diagonal mean (Transfer).

  diagonal_qc.csv
      Expected Table (1) diagonal AUROC versus run4c observed AUROC.

  source_config_manifest.csv
      Frozen classifier configuration and model SHA256 for each source.

  target_test_manifest.csv
      Exact held-out target test path, SHA256, row counts, and AST dimension.

  predictions/clf-<source>/target-<target>.csv
      Row-level labels, predictions, and full-precision continuous scores.

  table2_rows.tex
      Convenience LaTeX rows for the cross-generator AUROC table.

  environment.txt
      Runtime Python/package versions used for the experiment.

Methodological invariants
-------------------------
* No classifier is refit in run4c.
* Only AST embeddings are used, matching Table (1)'s selected representation.
* Every target test set must contain exactly 900 rows: 450 HWC and 450 AGC.
* Human is label 1; AGC is label 0, matching test_embedding.py.
* AUROC uses the same score logic as test_embedding.py:
    predict_proba(class=1) -> decision_function -> fail.
* All 25 source-target cells are required.
* Each diagonal AUROC must round to the exact Table (1) value at four decimals.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pickle
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score


LABEL_COL = "actual label"
AST_PREFIX = "ast_"
EXPECTED_TEST_ROWS = 900
EXPECTED_PER_CLASS = 450
EXPECTED_MATRIX_CELLS = 25


@dataclass(frozen=True)
class SourceConfig:
    paper_label: str
    slug: str
    experiment: str
    dataset: str
    algorithm: str
    embedding: str
    model_relpath: str
    expected_diagonal_auroc: float


# These paths and expected diagonal values are taken from the final run5b
# Table (1) test-only runs. Do not replace them with older run3/run4 choices.
SOURCES = [
    SourceConfig(
        paper_label="CL-7B",
        slug="codellama-7b",
        experiment="codellama-7b_4500_complexity_stratified_maxlen2048",
        dataset="codesearchnet_codellama-7b_python_merged_4500",
        algorithm="svm",
        embedding="ast",
        model_relpath=(
            "models/codellama-7b_4500_complexity_stratified_maxlen2048/"
            "tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_"
            "maxlen2048_svm_20260530_202138.pkl"
        ),
        expected_diagonal_auroc=0.7950,
    ),
    SourceConfig(
        paper_label="SC2-7B",
        slug="starcoder2-7b",
        experiment="starcoder2-7b_4500_complexity_stratified_maxlen2048",
        dataset="codesearchnet_starcoder2-7b_python_merged_4500",
        algorithm="svm",
        embedding="ast",
        model_relpath=(
            "models/starcoder2-7b_4500_complexity_stratified_maxlen2048/"
            "tuned_models_codesearchnet_starcoder2-7b_4500_complexity_stratified_"
            "maxlen2048_svm_20260528_142045.pkl"
        ),
        expected_diagonal_auroc=0.7689,
    ),
    SourceConfig(
        paper_label="SC2-15B",
        slug="starcoder2-15b-instruct-v0.1",
        experiment="starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048",
        dataset="codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_4500",
        algorithm="svm",
        embedding="ast",
        model_relpath=(
            "models/starcoder2-15b-instruct-v0.1_4500_complexity_stratified_maxlen2048/"
            "tuned_models_codesearchnet_starcoder2-15b-instruct-v0.1_4500_"
            "complexity_stratified_maxlen2048_svm_20260526_033005.pkl"
        ),
        expected_diagonal_auroc=0.7666,
    ),
    SourceConfig(
        paper_label="GO-120B",
        slug="gpt-oss",
        experiment="gpt-oss_4500_complexity_stratified_maxlen2048",
        dataset="codesearchnet_gpt-oss_python_merged_4500",
        algorithm="mlp",
        embedding="ast",
        model_relpath=(
            "models/gpt-oss_4500_complexity_stratified_maxlen2048/"
            "tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_"
            "maxlen2048_mlp_20260527_192034.pkl"
        ),
        expected_diagonal_auroc=0.8837,
    ),
    SourceConfig(
        paper_label="GM4-31B",
        slug="gemma",
        experiment="gemma_4500_complexity_stratified_maxlen2048",
        dataset="codesearchnet_gemma_python_merged_4500",
        algorithm="lr",
        embedding="ast",
        model_relpath=(
            "models/gemma_4500_complexity_stratified_maxlen2048/"
            "tuned_models_codesearchnet_gemma_4500_complexity_stratified_"
            "maxlen2048_lr_20260529_163559.pkl"
        ),
        expected_diagonal_auroc=0.7767,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run run4c cross-generator transfer on exact Table (1) test splits.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ml-root",
        type=Path,
        default=Path("src/ml_embeddings/data_codesearchnet"),
        help="Root containing Table (1) splits/ and models/ directories.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c"),
        help="Run4c output root.",
    )
    parser.add_argument(
        "--expected-sklearn-version",
        default="1.4.2",
        help="Required sklearn version used to load the frozen run5b pickles.",
    )
    parser.add_argument(
        "--allow-sklearn-version-mismatch",
        action="store_true",
        help="Explicitly permit a sklearn version mismatch. Not recommended for paper results.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_csv_path(ml_root: Path, cfg: SourceConfig) -> Path:
    return ml_root / "splits" / cfg.experiment / cfg.dataset / "test_.csv"


def validate_runtime(expected_version: str, allow_mismatch: bool) -> None:
    actual = sklearn.__version__
    if expected_version and actual != expected_version:
        msg = (
            f"[ERROR] scikit-learn version mismatch: runtime={actual}, "
            f"expected={expected_version}. The frozen Table (1) estimators were "
            "serialized with the expected version."
        )
        if allow_mismatch:
            print(msg.replace("[ERROR]", "[WARN]"), file=sys.stderr)
        else:
            raise SystemExit(msg)


def validate_test_frame(df: pd.DataFrame, path: Path) -> list[str]:
    required = {"idx", LABEL_COL}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] {path}: missing required columns {sorted(missing)}")

    if len(df) != EXPECTED_TEST_ROWS:
        raise SystemExit(
            f"[ERROR] {path}: expected {EXPECTED_TEST_ROWS} held-out rows, found {len(df)}"
        )

    labels = pd.to_numeric(df[LABEL_COL], errors="raise").astype(int)
    unique = sorted(labels.unique().tolist())
    if unique != [0, 1]:
        raise SystemExit(f"[ERROR] {path}: expected binary labels [0, 1], found {unique}")

    counts = labels.value_counts().to_dict()
    if counts.get(0, 0) != EXPECTED_PER_CLASS or counts.get(1, 0) != EXPECTED_PER_CLASS:
        raise SystemExit(
            f"[ERROR] {path}: expected {EXPECTED_PER_CLASS} AGC(0) and "
            f"{EXPECTED_PER_CLASS} HWC(1), found {counts}"
        )

    ast_cols = [col for col in df.columns if col.startswith(AST_PREFIX)]
    if not ast_cols:
        raise SystemExit(f"[ERROR] {path}: no AST embedding columns with prefix '{AST_PREFIX}'")

    ast_frame = df[ast_cols]
    if ast_frame.isnull().any().any():
        raise SystemExit(f"[ERROR] {path}: NaN found in AST embedding columns")

    return ast_cols


def extract_estimator(model_pickle: Path, source_dataset: str) -> tuple[Any, str, int]:
    with model_pickle.open("rb") as handle:
        tuned_models = pickle.load(handle)

    if not isinstance(tuned_models, dict):
        raise SystemExit(f"[ERROR] {model_pickle}: expected dict-like tuned model pickle")

    model_key = source_dataset + AST_PREFIX
    if model_key not in tuned_models:
        available = sorted(str(k) for k in tuned_models.keys())
        raise SystemExit(
            f"[ERROR] {model_pickle}: expected AST model key '{model_key}' not found. "
            f"Available keys: {available}"
        )

    payload = tuned_models[model_key]
    if isinstance(payload, (tuple, list)):
        if not payload:
            raise SystemExit(f"[ERROR] {model_pickle}: empty payload for key {model_key}")
        estimator = payload[0]
    else:
        estimator = payload

    return estimator, model_key, len(tuned_models)


def predict_scores(clf: Any, x: np.ndarray) -> tuple[np.ndarray, str]:
    """Match test_embedding.py's AUROC score selection logic."""

    try:
        proba = clf.predict_proba(x)
        classes = list(clf.classes_)
        idx = classes.index(1) if 1 in classes else proba.shape[1] - 1
        return np.asarray(proba[:, idx], dtype=float), "proba"
    except Exception:
        pass

    try:
        return np.ravel(np.asarray(clf.decision_function(x), dtype=float)), "decision"
    except Exception as exc:
        raise SystemExit(
            f"[ERROR] Estimator provides neither usable predict_proba nor "
            f"decision_function for AUROC: {type(clf).__name__}: {exc}"
        ) from exc


def calculate_metrics(y_true: np.ndarray, pred: np.ndarray, score: np.ndarray) -> dict[str, float]:
    acc = accuracy_score(y_true, pred)
    human_f1 = f1_score(y_true, pred, pos_label=1, zero_division=0)
    agc_f1 = f1_score(y_true, pred, pos_label=0, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    tpr = tp / max(tp + fn, 1)
    tnr = tn / max(tn + fp, 1)
    auroc = roc_auc_score(y_true, score)
    return {
        "acc": float(acc),
        "tpr": float(tpr),
        "tnr": float(tnr),
        "human_f1": float(human_f1),
        "agc_f1": float(agc_f1),
        "avg_f1": float((human_f1 + agc_f1) / 2.0),
        "auroc": float(auroc),
    }


def write_environment(path: Path, args: argparse.Namespace) -> None:
    lines = [
        f"python={platform.python_version()}",
        f"python_executable={sys.executable}",
        f"platform={platform.platform()}",
        f"numpy={np.__version__}",
        f"pandas={pd.__version__}",
        f"scikit_learn={sklearn.__version__}",
        f"expected_scikit_learn={args.expected_sklearn_version}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex_rows(matrix: pd.DataFrame, output_path: Path) -> None:
    config_map = {cfg.paper_label: f"{cfg.algorithm.upper()} + AST" for cfg in SOURCES}
    target_labels = [cfg.paper_label for cfg in SOURCES]
    lines: list[str] = []
    for _, row in matrix.iterrows():
        label = str(row["train_source"])
        values = " & ".join(f"{float(row[target]):.4f}" for target in target_labels)
        lines.append(
            f"{label} & {config_map[label]} & {values} & {float(row['Transfer']):.4f} \\\\"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    validate_runtime(args.expected_sklearn_version, args.allow_sklearn_version_mismatch)

    ml_root = args.ml_root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    predictions_root = output_root / "predictions"
    predictions_root.mkdir(parents=True, exist_ok=True)

    write_environment(output_root / "environment.txt", args)

    print("=" * 88)
    print(" run4c: Table (1) Exact-Test-Support Cross-Generator Transfer")
    print(f" ML root      : {ml_root}")
    print(f" Output root  : {output_root}")
    print(f" sklearn      : {sklearn.__version__}")
    print(" Representation: AST only")
    print(" Refit         : NO")
    print(" Expected cells: 25")
    print("=" * 88)

    # Load and validate every exact Table (1) target test set once.
    target_frames: dict[str, pd.DataFrame] = {}
    target_ast_cols: dict[str, list[str]] = {}
    target_test_paths: dict[str, Path] = {}
    target_manifest_rows: list[dict[str, object]] = []

    reference_ast_cols: list[str] | None = None
    for target in SOURCES:
        path = test_csv_path(ml_root, target)
        if not path.is_file():
            raise SystemExit(f"[ERROR] Missing Table (1) held-out test CSV: {path}")

        frame = pd.read_csv(path)
        ast_cols = validate_test_frame(frame, path)

        if reference_ast_cols is None:
            reference_ast_cols = ast_cols
        elif ast_cols != reference_ast_cols:
            raise SystemExit(
                f"[ERROR] AST feature schema differs for target {target.paper_label}. "
                "All run4c targets must use the same CodeT5+ AST embedding schema."
            )

        target_frames[target.paper_label] = frame
        target_ast_cols[target.paper_label] = ast_cols
        target_test_paths[target.paper_label] = path

        label_counts = frame[LABEL_COL].astype(int).value_counts().to_dict()
        target_manifest_rows.append(
            {
                "target_source": target.paper_label,
                "target_slug": target.slug,
                "experiment": target.experiment,
                "dataset": target.dataset,
                "test_csv": str(path),
                "test_sha256": sha256_file(path),
                "rows": len(frame),
                "hwc_label1": int(label_counts.get(1, 0)),
                "agc_label0": int(label_counts.get(0, 0)),
                "ast_features": len(ast_cols),
            }
        )

        print(
            f"[TARGET PASS] {target.paper_label:8s} rows={len(frame)} "
            f"HWC={label_counts.get(1, 0)} AGC={label_counts.get(0, 0)} "
            f"AST={len(ast_cols)}"
        )

    pd.DataFrame(target_manifest_rows).to_csv(
        output_root / "target_test_manifest.csv", index=False
    )

    cell_rows: list[dict[str, object]] = []
    source_manifest_rows: list[dict[str, object]] = []

    # Load each frozen Table (1) source classifier once, then score all five
    # exact held-out target test sets without retraining.
    for source in SOURCES:
        model_path = ml_root / source.model_relpath
        if not model_path.is_file():
            raise SystemExit(f"[ERROR] Missing frozen Table (1) model pickle: {model_path}")

        clf, model_key, pickle_entries = extract_estimator(model_path, source.dataset)
        model_sha256 = sha256_file(model_path)
        n_features = getattr(clf, "n_features_in_", None)
        expected_features = len(reference_ast_cols or [])
        if n_features is not None and int(n_features) != expected_features:
            raise SystemExit(
                f"[ERROR] {source.paper_label}: estimator n_features_in_={n_features}, "
                f"target AST feature count={expected_features}"
            )

        source_manifest_rows.append(
            {
                "train_source": source.paper_label,
                "source_slug": source.slug,
                "algorithm": source.algorithm,
                "embedding": source.embedding,
                "source_experiment": source.experiment,
                "source_dataset": source.dataset,
                "model_key": model_key,
                "model_pickle": str(model_path),
                "model_sha256": model_sha256,
                "pickle_entries": pickle_entries,
                "estimator_class": type(clf).__name__,
                "n_features_in": n_features,
                "expected_diagonal_auroc": source.expected_diagonal_auroc,
            }
        )

        print("-" * 88)
        print(
            f"[SOURCE] {source.paper_label} | {source.algorithm.upper()} + AST | "
            f"{type(clf).__name__} | key={model_key}"
        )

        source_pred_dir = predictions_root / f"clf-{source.slug}"
        source_pred_dir.mkdir(parents=True, exist_ok=True)

        for target in SOURCES:
            frame = target_frames[target.paper_label]
            ast_cols = target_ast_cols[target.paper_label]
            x_test = frame[ast_cols].to_numpy()
            y_true = frame[LABEL_COL].astype(int).to_numpy()

            pred = np.asarray(clf.predict(x_test), dtype=int)
            score, score_mode = predict_scores(clf, x_test)
            metrics = calculate_metrics(y_true, pred, score)

            pred_path = source_pred_dir / f"target-{target.slug}.csv"
            pred_df = pd.DataFrame(
                {
                    "idx": frame["idx"].astype(str),
                    LABEL_COL: y_true,
                    "pred": pred,
                    "score": score,
                    "score_mode": score_mode,
                }
            )
            pred_df.to_csv(pred_path, index=False, float_format="%.17g")

            row = {
                "train_source": source.paper_label,
                "train_slug": source.slug,
                "algorithm": source.algorithm,
                "embedding": source.embedding,
                "target_source": target.paper_label,
                "target_slug": target.slug,
                "n_rows": len(frame),
                "hwc_label1": int(np.sum(y_true == 1)),
                "agc_label0": int(np.sum(y_true == 0)),
                "score_mode": score_mode,
                "acc": metrics["acc"],
                "tpr": metrics["tpr"],
                "tnr": metrics["tnr"],
                "human_f1": metrics["human_f1"],
                "agc_f1": metrics["agc_f1"],
                "avg_f1": metrics["avg_f1"],
                "auroc": metrics["auroc"],
                "model_sha256": model_sha256,
                "target_test_sha256": sha256_file(target_test_paths[target.paper_label]),
                "predictions_csv": str(pred_path),
            }
            cell_rows.append(row)

            print(
                f"  {source.paper_label:8s} -> {target.paper_label:8s} "
                f"AUROC={metrics['auroc']:.6f} AvgF1={metrics['avg_f1']:.6f} "
                f"score={score_mode}"
            )

    if len(cell_rows) != EXPECTED_MATRIX_CELLS:
        raise SystemExit(
            f"[ERROR] Expected {EXPECTED_MATRIX_CELLS} matrix cells, found {len(cell_rows)}"
        )

    cell_df = pd.DataFrame(cell_rows)
    cell_df.to_csv(output_root / "cell_metrics.csv", index=False, float_format="%.17g")
    pd.DataFrame(source_manifest_rows).to_csv(
        output_root / "source_config_manifest.csv", index=False
    )

    # Build the paper-facing 5x5 matrix in the same source order as Table (1).
    labels = [cfg.paper_label for cfg in SOURCES]
    matrix_rows: list[dict[str, object]] = []
    for source in SOURCES:
        row: dict[str, object] = {
            "train_source": source.paper_label,
            "config": f"{source.algorithm.upper()} + AST",
        }
        off_diag: list[float] = []
        for target in SOURCES:
            selected = cell_df[
                (cell_df["train_source"] == source.paper_label)
                & (cell_df["target_source"] == target.paper_label)
            ]
            if len(selected) != 1:
                raise SystemExit(
                    f"[ERROR] Expected one cell for {source.paper_label}->{target.paper_label}, "
                    f"found {len(selected)}"
                )
            auroc = float(selected.iloc[0]["auroc"])
            row[target.paper_label] = auroc
            if target.paper_label != source.paper_label:
                off_diag.append(auroc)
        row["Transfer"] = float(np.mean(off_diag))
        matrix_rows.append(row)

    matrix_df = pd.DataFrame(matrix_rows, columns=["train_source", "config", *labels, "Transfer"])
    matrix_df.to_csv(output_root / "matrix_auroc.csv", index=False, float_format="%.17g")
    write_latex_rows(matrix_df, output_root / "table2_rows.tex")

    # Strong QC: because run4c uses the exact Table (1) test support and frozen
    # selected classifier, every diagonal must reproduce Table (1) to 4 decimals.
    diagonal_rows: list[dict[str, object]] = []
    diagonal_failures: list[str] = []
    for source in SOURCES:
        observed = float(
            matrix_df.loc[matrix_df["train_source"] == source.paper_label, source.paper_label].iloc[0]
        )
        expected = source.expected_diagonal_auroc
        observed_4 = f"{observed:.4f}"
        expected_4 = f"{expected:.4f}"
        passed = observed_4 == expected_4
        diagonal_rows.append(
            {
                "source": source.paper_label,
                "expected_table1_auroc": expected,
                "observed_run4c_auroc": observed,
                "absolute_difference": abs(observed - expected),
                "expected_4dp": expected_4,
                "observed_4dp": observed_4,
                "pass_4dp": passed,
            }
        )
        if not passed:
            diagonal_failures.append(
                f"{source.paper_label}: expected {expected_4}, observed {observed_4}"
            )

    diagonal_df = pd.DataFrame(diagonal_rows)
    diagonal_df.to_csv(output_root / "diagonal_qc.csv", index=False, float_format="%.17g")

    print("=" * 88)
    print(" AUROC matrix")
    print("=" * 88)
    display_df = matrix_df.copy()
    for col in [*labels, "Transfer"]:
        display_df[col] = display_df[col].map(lambda x: f"{float(x):.4f}")
    print(display_df.to_string(index=False))
    print()
    print("Diagonal reproduction QC")
    for row in diagonal_rows:
        status = "PASS" if row["pass_4dp"] else "FAIL"
        print(
            f"  {row['source']:8s}: expected={row['expected_4dp']} "
            f"observed={row['observed_4dp']} {status}"
        )

    if diagonal_failures:
        raise SystemExit(
            "[ERROR] Diagonal reproduction failed. Run4c must match Table (1) on the "
            "same held-out test support:\n  " + "\n  ".join(diagonal_failures)
        )

    print()
    print("[PASS] Matrix cells: 25/25")
    print("[PASS] Exact target support: 900 rows per source, 450 HWC + 450 AGC")
    print("[PASS] Table (1) diagonal AUROC reproduction: 5/5 at four decimals")
    print(f"[DONE] Results: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
