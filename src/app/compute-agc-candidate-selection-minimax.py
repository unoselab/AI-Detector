#!/usr/bin/env python3
"""
compute-agc-candidate-selection-minimax.py
===========================================

Run the run4d statistical candidate-selection analysis for the five frozen
Table (1) AGC detectors by jointly considering:

  1. Complexity-balanced matched-source AUROC (Table 1), and
  2. Exact-test-support cross-generator transfer AUROC (run4c / Table 2).

Primary decision criterion
--------------------------
The primary point-estimate decision rule is Savage-style minimax regret. For
candidate c and evaluation regime e:

    regret(c, e) = max_j AUROC(j, e) - AUROC(c, e)
    max_regret(c) = max_e regret(c, e)

The candidate with the smallest maximum regret is the minimax-regret choice.
This rule uses difference magnitudes rather than ordinal ranks and does not
require an arbitrary weighted average. Both regimes use AUROC on the same
[0, 1] scale, so regret is measured directly in AUROC points.

Uncertainty model
-----------------
The complexity-balanced split was constructed at the HWC-AGC pair level. Run4d
therefore uses a pair-cluster bootstrap rather than resampling individual rows.
For each target generator and bootstrap replicate:

  * sample the 450 pair_ids with replacement;
  * retain both HWC(label=1) and AGC(label=0) rows for every sampled pair;
  * reuse the same sampled pair multiplicities for all five classifiers on the
    target, preserving paired classifier comparisons.

Bootstrap uncertainty is propagated through matched-source AUROC, transfer
AUROC, rank distributions, Pareto-front membership, pairwise AUROC differences,
and minimax regret.

Important transfer comparison detail
------------------------------------
The paper-facing Transfer metric for candidate c is the mean of its four
off-diagonal target AUROCs. Because candidate-specific off-diagonal sets omit a
different target, pairwise transfer effect-size inference additionally uses a
COMMON-TARGET comparison: for candidates A and B, exclude target A and target B
and compare their mean AUROC over the remaining three target generators. This
keeps the target composition identical in the pairwise comparison.

Inputs
------
Under --run4c-root (default:
src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c):

  matrix_auroc.csv
  diagonal_qc.csv
  predictions/clf-<source>/target-<target>.csv  (25 files)

Each prediction CSV must contain:
  idx, actual label, pred, score, score_mode

Outputs
-------
Under --output-root:

  point_estimates.csv
      Table (1), Transfer, per-regime regret, maximum regret, point ranks, and
      point Pareto status.

  bootstrap_table1_summary.csv
      Bootstrap CI, expected rank, P(best), and P(top-2) for matched-source
      complexity-balanced AUROC.

  bootstrap_transfer_summary.csv
      The same quantities for the paper-facing off-diagonal Transfer metric.

  minimax_regret_summary.csv
      Bootstrap mean/CI for each candidate's maximum regret, expected minimax
      rank, P(minimax winner), and P(top-2 by minimax regret).

  pairwise_table1_differences.csv
      Pairwise Table (1) AUROC differences with bootstrap CIs and superiority
      probabilities. Candidate matched-source supports are source-specific, so
      these comparisons are not treated as paired across generators.

  pairwise_transfer_common_targets.csv
      Pairwise transfer differences over the same three common off-diagonal
      target generators, using the paired cluster bootstrap.

  pareto_summary.csv
      Point Pareto membership and bootstrap probability of being non-dominated
      across the two AUROC evaluation regimes.

  bootstrap_candidate_metrics.csv.gz
      Reproducible bootstrap draw-level candidate metrics.

  candidate_selection_summary.txt
      Compact paper-facing numerical summary.

  methodology.txt
      Exact estimands, bootstrap unit, and decision rule.

  environment.txt
      Runtime versions and analysis parameters.

Hard QC
-------
* run4c diagonal_qc.csv must contain 5/5 pass_4dp=True.
* Exactly 25 prediction cells are required.
* Each target must contain exactly 450 HWC-AGC pairs.
* Every pair must contain one label 0 and one label 1 row.
* For a target, all five classifiers must have identical idx/label support.
* Full-precision AUROCs recomputed from predictions must match matrix_auroc.csv
  within 1e-12 absolute tolerance.
"""

from __future__ import annotations

import argparse
import gzip
import math
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


LABEL_COL = "actual label"
EXPECTED_PAIRS = 450
EXPECTED_ROWS = 900
EXPECTED_CELLS = 25
DEFAULT_SEED = 20260723


@dataclass(frozen=True)
class Candidate:
    paper_label: str
    slug: str
    config: str


CANDIDATES = [
    Candidate("CL-7B", "codellama-7b", "SVM + AST"),
    Candidate("SC2-7B", "starcoder2-7b", "SVM + AST"),
    Candidate("SC2-15B", "starcoder2-15b-instruct-v0.1", "SVM + AST"),
    Candidate("GO-120B", "gpt-oss", "MLP + AST"),
    Candidate("GM4-31B", "gemma", "LR + AST"),
]

LABELS = [c.paper_label for c in CANDIDATES]
LABEL_TO_INDEX = {label: i for i, label in enumerate(LABELS)}
SLUG_TO_INDEX = {c.slug: i for i, c in enumerate(CANDIDATES)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap minimax-regret candidate selection for Table (1) + run4c transfer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--run4c-root",
        type=Path,
        default=Path("src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c"),
        help="Root containing run4c matrix, QC, and 25 prediction CSVs.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("src/ml_embeddings/data_codesearchnet/candidate_selection_run4d"),
        help="Output directory for run4d statistical analysis.",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=20000,
        help="Number of pair-cluster bootstrap replicates.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Deterministic bootstrap random seed.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Bootstrap batch size used to bound memory.",
    )
    parser.add_argument(
        "--ci-level",
        type=float,
        default=0.95,
        help="Two-sided percentile-bootstrap confidence level.",
    )
    return parser.parse_args()


def pair_id_from_idx(value: object) -> str:
    """Match the pair-id convention used by split_complexity_stratified.py."""

    return re.sub(r"_(human|lm|ai)$", "", str(value))


def weighted_auc_batch(
    weights: np.ndarray,
    positive_scores: np.ndarray,
    negative_scores: np.ndarray,
) -> np.ndarray:
    """Compute weighted AUROC for many pair-cluster bootstrap replicates.

    Each pair has the same bootstrap multiplicity for its positive and negative
    row. The AUROC is the weighted Mann-Whitney probability that a positive
    score exceeds a negative score, with half credit for ties.

    Parameters
    ----------
    weights:
        Shape (B, N), where N is the number of HWC-AGC pairs. Each row sums to N.
    positive_scores:
        Shape (N,), label-1 scores indexed by pair.
    negative_scores:
        Shape (N,), label-0 scores indexed by pair.
    """

    if weights.ndim != 2:
        raise ValueError("weights must be two-dimensional")
    n_draws, n_pairs = weights.shape
    if positive_scores.shape != (n_pairs,) or negative_scores.shape != (n_pairs,):
        raise ValueError("score vector length must equal bootstrap pair count")

    neg_order = np.argsort(negative_scores, kind="mergesort")
    sorted_neg = negative_scores[neg_order]

    lower = np.searchsorted(sorted_neg, positive_scores, side="left")
    upper = np.searchsorted(sorted_neg, positive_scores, side="right")

    sorted_weights = weights[:, neg_order]
    prefix = np.empty((n_draws, n_pairs + 1), dtype=np.float64)
    prefix[:, 0] = 0.0
    np.cumsum(sorted_weights, axis=1, dtype=np.float64, out=prefix[:, 1:])

    less_weight = prefix[:, lower]
    leq_weight = prefix[:, upper]
    tie_weight = leq_weight - less_weight
    credit = less_weight + 0.5 * tie_weight

    numerator = np.sum(weights * credit, axis=1, dtype=np.float64)
    totals = np.sum(weights, axis=1, dtype=np.float64)
    denominator = totals * totals
    if np.any(denominator <= 0):
        raise ValueError("bootstrap multiplicities produced an empty class")
    return numerator / denominator


def observed_auc(positive_scores: np.ndarray, negative_scores: np.ndarray) -> float:
    weights = np.ones((1, len(positive_scores)), dtype=np.float64)
    return float(weighted_auc_batch(weights, positive_scores, negative_scores)[0])


def validate_diagonal_qc(run4c_root: Path) -> None:
    path = run4c_root / "diagonal_qc.csv"
    if not path.is_file():
        raise SystemExit(f"[ERROR] Missing run4c diagonal QC: {path}")
    df = pd.read_csv(path)
    if len(df) != len(CANDIDATES):
        raise SystemExit(f"[ERROR] Expected 5 diagonal QC rows, found {len(df)}")
    if "pass_4dp" not in df.columns:
        raise SystemExit(f"[ERROR] {path}: missing pass_4dp column")
    passed = df["pass_4dp"].astype(str).str.lower().isin(["true", "1", "yes"])
    if int(passed.sum()) != len(CANDIDATES):
        raise SystemExit(
            f"[ERROR] run4c diagonal reproduction gate is not 5/5 PASS: {int(passed.sum())}/5"
        )


def prediction_path(run4c_root: Path, source: Candidate, target: Candidate) -> Path:
    return (
        run4c_root
        / "predictions"
        / f"clf-{source.slug}"
        / f"target-{target.slug}.csv"
    )


def prepare_target_scores(
    run4c_root: Path,
    target: Candidate,
) -> tuple[list[str], np.ndarray, np.ndarray, list[dict[str, object]]]:
    """Load one target across all five classifiers and validate shared support."""

    pair_ids_ref: list[str] | None = None
    labels_ref: np.ndarray | None = None
    pos_scores = np.empty((len(CANDIDATES), EXPECTED_PAIRS), dtype=np.float64)
    neg_scores = np.empty((len(CANDIDATES), EXPECTED_PAIRS), dtype=np.float64)
    audit_rows: list[dict[str, object]] = []

    for source_idx, source in enumerate(CANDIDATES):
        path = prediction_path(run4c_root, source, target)
        if not path.is_file():
            raise SystemExit(f"[ERROR] Missing prediction CSV: {path}")

        df = pd.read_csv(path)
        required = {"idx", LABEL_COL, "score"}
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"[ERROR] {path}: missing columns {sorted(missing)}")
        if len(df) != EXPECTED_ROWS:
            raise SystemExit(f"[ERROR] {path}: expected {EXPECTED_ROWS} rows, found {len(df)}")

        work = df[["idx", LABEL_COL, "score"]].copy()
        work["idx"] = work["idx"].astype(str)
        work[LABEL_COL] = pd.to_numeric(work[LABEL_COL], errors="raise").astype(int)
        work["score"] = pd.to_numeric(work["score"], errors="raise").astype(float)
        if not np.isfinite(work["score"].to_numpy()).all():
            raise SystemExit(f"[ERROR] {path}: non-finite score detected")

        work["pair_id"] = work["idx"].map(pair_id_from_idx)
        pair_counts = work.groupby("pair_id", sort=True)[LABEL_COL].agg(["count", "sum"])
        if len(pair_counts) != EXPECTED_PAIRS:
            raise SystemExit(
                f"[ERROR] {path}: expected {EXPECTED_PAIRS} pair_ids, found {len(pair_counts)}"
            )
        bad = pair_counts[(pair_counts["count"] != 2) | (pair_counts["sum"] != 1)]
        if not bad.empty:
            raise SystemExit(
                f"[ERROR] {path}: every pair_id must contain exactly one label 0 and one label 1; "
                f"bad pairs={len(bad)}"
            )

        work = work.sort_values(["pair_id", LABEL_COL, "idx"]).reset_index(drop=True)
        pair_ids = sorted(work["pair_id"].unique().tolist())
        label_sequence = work[["idx", LABEL_COL]].astype(str).agg("|".join, axis=1).to_numpy()

        if pair_ids_ref is None:
            pair_ids_ref = pair_ids
            labels_ref = label_sequence
        else:
            if pair_ids != pair_ids_ref:
                raise SystemExit(
                    f"[ERROR] Target {target.paper_label}: pair_id support differs across classifiers"
                )
            if labels_ref is None or not np.array_equal(label_sequence, labels_ref):
                raise SystemExit(
                    f"[ERROR] Target {target.paper_label}: idx/label support differs across classifiers"
                )

        grouped = work.set_index(["pair_id", LABEL_COL])["score"]
        for pair_idx, pair_id in enumerate(pair_ids):
            try:
                neg_scores[source_idx, pair_idx] = float(grouped.loc[(pair_id, 0)])
                pos_scores[source_idx, pair_idx] = float(grouped.loc[(pair_id, 1)])
            except KeyError as exc:
                raise SystemExit(
                    f"[ERROR] {path}: incomplete label pair for pair_id={pair_id}"
                ) from exc

        audit_rows.append(
            {
                "train_source": source.paper_label,
                "target_source": target.paper_label,
                "prediction_csv": str(path),
                "rows": len(work),
                "pairs": len(pair_ids),
                "hwc_label1": int((work[LABEL_COL] == 1).sum()),
                "agc_label0": int((work[LABEL_COL] == 0).sum()),
                "observed_auroc_recomputed": observed_auc(
                    pos_scores[source_idx], neg_scores[source_idx]
                ),
            }
        )

    assert pair_ids_ref is not None
    return pair_ids_ref, pos_scores, neg_scores, audit_rows


def load_run4c_matrix(run4c_root: Path) -> np.ndarray:
    path = run4c_root / "matrix_auroc.csv"
    if not path.is_file():
        raise SystemExit(f"[ERROR] Missing run4c matrix: {path}")
    df = pd.read_csv(path)
    if "train_source" not in df.columns:
        raise SystemExit(f"[ERROR] {path}: missing train_source column")

    matrix = np.empty((len(CANDIDATES), len(CANDIDATES)), dtype=np.float64)
    for i, source in enumerate(CANDIDATES):
        row = df[df["train_source"] == source.paper_label]
        if len(row) != 1:
            raise SystemExit(
                f"[ERROR] {path}: expected one row for {source.paper_label}, found {len(row)}"
            )
        for j, target in enumerate(CANDIDATES):
            if target.paper_label not in row.columns:
                raise SystemExit(f"[ERROR] {path}: missing target column {target.paper_label}")
            matrix[i, j] = float(row.iloc[0][target.paper_label])
    return matrix


def descending_ranks(values: np.ndarray) -> np.ndarray:
    """Return rank 1 for the largest value; ties share the minimum rank."""

    if values.ndim != 2:
        raise ValueError("values must be shape (B, C)")
    b, c = values.shape
    ranks = np.empty((b, c), dtype=np.int16)
    for j in range(c):
        ranks[:, j] = 1 + np.sum(values > values[:, j : j + 1], axis=1)
    return ranks


def ascending_ranks(values: np.ndarray) -> np.ndarray:
    """Return rank 1 for the smallest value; ties share the minimum rank."""

    if values.ndim != 2:
        raise ValueError("values must be shape (B, C)")
    b, c = values.shape
    ranks = np.empty((b, c), dtype=np.int16)
    for j in range(c):
        ranks[:, j] = 1 + np.sum(values < values[:, j : j + 1], axis=1)
    return ranks


def point_descending_rank(values: np.ndarray) -> np.ndarray:
    return descending_ranks(values.reshape(1, -1))[0]


def point_ascending_rank(values: np.ndarray) -> np.ndarray:
    return ascending_ranks(values.reshape(1, -1))[0]


def ci_bounds(draws: np.ndarray, ci_level: float) -> tuple[float, float]:
    alpha = 1.0 - ci_level
    lower = float(np.quantile(draws, alpha / 2.0))
    upper = float(np.quantile(draws, 1.0 - alpha / 2.0))
    return lower, upper


def pareto_membership(metric1: np.ndarray, metric2: np.ndarray) -> np.ndarray:
    """Return non-dominated membership for each bootstrap draw and candidate."""

    if metric1.shape != metric2.shape or metric1.ndim != 2:
        raise ValueError("Pareto metrics must share shape (B, C)")
    b, c = metric1.shape
    nondominated = np.ones((b, c), dtype=bool)
    for i in range(c):
        for j in range(c):
            if i == j:
                continue
            dominates = (
                (metric1[:, j] >= metric1[:, i])
                & (metric2[:, j] >= metric2[:, i])
                & (
                    (metric1[:, j] > metric1[:, i])
                    | (metric2[:, j] > metric2[:, i])
                )
            )
            nondominated[:, i] &= ~dominates
    return nondominated


def point_pareto(metric1: np.ndarray, metric2: np.ndarray) -> np.ndarray:
    return pareto_membership(metric1.reshape(1, -1), metric2.reshape(1, -1))[0]


def summarize_metric(
    point: np.ndarray,
    draws: np.ndarray,
    ranks: np.ndarray,
    ci_level: float,
    metric_name: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for i, candidate in enumerate(CANDIDATES):
        lo, hi = ci_bounds(draws[:, i], ci_level)
        rows.append(
            {
                "candidate": candidate.paper_label,
                "config": candidate.config,
                "metric": metric_name,
                "point_estimate": float(point[i]),
                "bootstrap_mean": float(np.mean(draws[:, i])),
                "bootstrap_median": float(np.median(draws[:, i])),
                "ci_level": ci_level,
                "ci_lower": lo,
                "ci_upper": hi,
                "point_rank": int(point_descending_rank(point)[i]),
                "expected_rank": float(np.mean(ranks[:, i])),
                "p_best": float(np.mean(ranks[:, i] == 1)),
                "p_top2": float(np.mean(ranks[:, i] <= 2)),
            }
        )
    return pd.DataFrame(rows)


def pairwise_rows(
    point_values: np.ndarray,
    draw_values: np.ndarray,
    ci_level: float,
    comparison_name: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    n = len(CANDIDATES)
    for i in range(n):
        for j in range(i + 1, n):
            diff = draw_values[:, i] - draw_values[:, j]
            lo, hi = ci_bounds(diff, ci_level)
            rows.append(
                {
                    "comparison": comparison_name,
                    "candidate_a": CANDIDATES[i].paper_label,
                    "candidate_b": CANDIDATES[j].paper_label,
                    "point_delta_a_minus_b": float(point_values[i] - point_values[j]),
                    "bootstrap_mean_delta": float(np.mean(diff)),
                    "ci_level": ci_level,
                    "ci_lower": lo,
                    "ci_upper": hi,
                    "p_a_gt_b": float(np.mean(diff > 0.0)),
                    "p_b_gt_a": float(np.mean(diff < 0.0)),
                    "ci_excludes_zero": bool((lo > 0.0) or (hi < 0.0)),
                }
            )
    return rows


def write_environment(path: Path, args: argparse.Namespace) -> None:
    lines = [
        f"python={platform.python_version()}",
        f"python_executable={sys.executable}",
        f"platform={platform.platform()}",
        f"numpy={np.__version__}",
        f"pandas={pd.__version__}",
        f"bootstrap_reps={args.bootstrap_reps}",
        f"bootstrap_seed={args.seed}",
        f"bootstrap_batch_size={args.batch_size}",
        f"ci_level={args.ci_level}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_methodology(path: Path, args: argparse.Namespace) -> None:
    text = f"""run4d statistical candidate-selection methodology
================================================

Evaluation regimes
------------------
E1 = complexity-balanced matched-source AUROC (Table 1), obtained from the five
     diagonal cells of run4c, which exactly reproduce Table (1).
E2 = cross-generator Transfer AUROC (Table 2), defined for candidate c as the
     arithmetic mean of its four off-diagonal target-generator AUROCs.

Primary decision criterion: minimax AUROC regret
------------------------------------------------
For each evaluation regime e and candidate c:

  regret(c,e) = max_j AUROC(j,e) - AUROC(c,e)
  max_regret(c) = max_e regret(c,e)

The primary point-estimate candidate is argmin_c max_regret(c). This is a
Savage-style minimax-regret rule. It uses magnitude in AUROC points rather than
ordinal rank and introduces no evaluation-specific weights. The two objectives
are directly comparable because both are AUROC on the same [0,1] scale.

Bootstrap uncertainty
---------------------
Bootstrap replicates : {args.bootstrap_reps}
Random seed          : {args.seed}
Confidence level     : {args.ci_level:.4f}
Resampling unit      : HWC-AGC pair_id
Pairs per target     : {EXPECTED_PAIRS}
Rows per target      : {EXPECTED_ROWS}

Within each target generator, 450 pair_ids are sampled with replacement. Both
rows of a sampled pair are retained with the same multiplicity. The same pair
multiplicities are reused for all five classifiers on that target. This keeps
the bootstrap aligned with the pair-level complexity-balanced split and
preserves within-target paired classifier comparisons.

Pairwise transfer effect sizes
------------------------------
The paper-facing Transfer mean omits a different own-source target for each
candidate. Therefore pairwise transfer inference additionally uses a common-
target estimand. For candidates A and B, target A and target B are both removed,
and the mean AUROC difference A-B is computed over the remaining three target
generators. The same bootstrap pair multiplicities are used for A and B on each
common target.

Supporting decision diagnostics
-------------------------------
* expected rank and P(top-2) under bootstrap uncertainty;
* pairwise AUROC-difference percentile confidence intervals;
* P(A > B) from bootstrap draws;
* probability of Pareto non-dominance across E1 and E2;
* probability of minimizing maximum regret.

Interpretation constraint
-------------------------
Run4d does not create a weighted composite AUROC and does not use raw rank sum as
the primary selection rule. Candidate selection should be reported using the
observed minimax-regret criterion together with bootstrap uncertainty and
pairwise effect-size evidence.

Method references
-----------------
Savage, L. J. (1951). The Theory of Statistical Decision. Journal of the
American Statistical Association, 46(253), 55-67.

Efron, B., & Tibshirani, R. J. (1993). An Introduction to the Bootstrap.
Chapman & Hall.
"""
    path.write_text(text, encoding="utf-8")


def write_selection_summary(
    path: Path,
    point_df: pd.DataFrame,
    minimax_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    common_transfer_df: pd.DataFrame,
) -> None:
    point_winner = point_df.sort_values(["max_regret", "candidate"]).iloc[0]
    prob_winner = minimax_df.sort_values(["p_minimax_winner", "candidate"], ascending=[False, True]).iloc[0]

    lines = [
        "run4d candidate-selection summary",
        "=================================",
        "",
        "Primary criterion: Savage-style minimax AUROC regret across",
        "(1) complexity-balanced matched-source AUROC and",
        "(2) cross-generator Transfer AUROC.",
        "",
        f"Point-estimate minimax candidate: {point_winner['candidate']}",
        f"Point maximum regret: {float(point_winner['max_regret']):.6f}",
        "",
        "Point estimates:",
    ]
    for _, row in point_df.sort_values("max_regret").iterrows():
        lines.append(
            f"  {row['candidate']:8s} Table1={float(row['table1_auroc']):.4f} "
            f"Transfer={float(row['transfer_auroc']):.4f} "
            f"MaxRegret={float(row['max_regret']):.4f} "
            f"Pareto={'YES' if bool(row['pareto_point']) else 'NO'}"
        )

    lines.extend(
        [
            "",
            "Bootstrap minimax uncertainty:",
        ]
    )
    for _, row in minimax_df.sort_values("expected_max_regret").iterrows():
        lines.append(
            f"  {row['candidate']:8s} expected_max_regret={float(row['expected_max_regret']):.4f} "
            f"CI=[{float(row['ci_lower']):.4f},{float(row['ci_upper']):.4f}] "
            f"P(winner)={float(row['p_minimax_winner']):.3f} "
            f"P(top2)={float(row['p_top2_minimax']):.3f}"
        )

    lines.extend(
        [
            "",
            f"Highest bootstrap P(minimax winner): {prob_winner['candidate']} "
            f"({float(prob_winner['p_minimax_winner']):.3f})",
            "",
            "Pareto non-dominance probabilities:",
        ]
    )
    for _, row in pareto_df.sort_values("p_pareto_nondominated", ascending=False).iterrows():
        lines.append(
            f"  {row['candidate']:8s} point={'YES' if bool(row['pareto_point']) else 'NO'} "
            f"P(nondominated)={float(row['p_pareto_nondominated']):.3f}"
        )

    lines.extend(
        [
            "",
            "Pairwise common-target transfer comparisons use the same three",
            "off-diagonal target generators for each candidate pair.",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.bootstrap_reps < 1000:
        raise SystemExit("[ERROR] --bootstrap-reps must be at least 1000 for paper-facing analysis")
    if args.batch_size <= 0:
        raise SystemExit("[ERROR] --batch-size must be positive")
    if not (0.80 <= args.ci_level < 1.0):
        raise SystemExit("[ERROR] --ci-level must be in [0.80, 1.0)")

    run4c_root = args.run4c_root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    validate_diagonal_qc(run4c_root)
    run4c_matrix = load_run4c_matrix(run4c_root)

    print("=" * 92)
    print(" run4d: Bootstrap Minimax-Regret Candidate Selection")
    print(f" run4c root      : {run4c_root}")
    print(f" output root     : {output_root}")
    print(f" bootstrap reps  : {args.bootstrap_reps}")
    print(f" bootstrap seed  : {args.seed}")
    print(f" CI level        : {args.ci_level:.3f}")
    print(" resampling unit : HWC-AGC pair_id")
    print("=" * 92)

    # cell_draws[replicate, source, target]
    cell_draws = np.empty(
        (args.bootstrap_reps, len(CANDIDATES), len(CANDIDATES)),
        dtype=np.float64,
    )
    observed_matrix = np.empty((len(CANDIDATES), len(CANDIDATES)), dtype=np.float64)
    prediction_audit_rows: list[dict[str, object]] = []

    # Spawn independent deterministic target streams while keeping the same pair
    # multiplicities across all five classifiers inside a target.
    seed_sequence = np.random.SeedSequence(args.seed)
    target_seeds = seed_sequence.spawn(len(CANDIDATES))

    for target_idx, target in enumerate(CANDIDATES):
        pair_ids, pos_scores, neg_scores, audit_rows = prepare_target_scores(run4c_root, target)
        prediction_audit_rows.extend(audit_rows)

        for source_idx in range(len(CANDIDATES)):
            observed_matrix[source_idx, target_idx] = observed_auc(
                pos_scores[source_idx], neg_scores[source_idx]
            )

        max_abs_error = float(
            np.max(np.abs(observed_matrix[:, target_idx] - run4c_matrix[:, target_idx]))
        )
        if max_abs_error > 1e-12:
            raise SystemExit(
                f"[ERROR] Target {target.paper_label}: recomputed prediction AUROCs differ from "
                f"run4c matrix; max_abs_error={max_abs_error:.3e}"
            )

        rng = np.random.default_rng(target_seeds[target_idx])
        probs = np.full(EXPECTED_PAIRS, 1.0 / EXPECTED_PAIRS, dtype=np.float64)

        for start in range(0, args.bootstrap_reps, args.batch_size):
            stop = min(start + args.batch_size, args.bootstrap_reps)
            batch_n = stop - start
            weights = rng.multinomial(EXPECTED_PAIRS, probs, size=batch_n).astype(
                np.float64, copy=False
            )
            for source_idx in range(len(CANDIDATES)):
                cell_draws[start:stop, source_idx, target_idx] = weighted_auc_batch(
                    weights,
                    pos_scores[source_idx],
                    neg_scores[source_idx],
                )

        print(
            f"[TARGET PASS] {target.paper_label:8s} pairs={len(pair_ids)} rows={2 * len(pair_ids)} "
            f"matrix_error={max_abs_error:.2e}"
        )

    if len(prediction_audit_rows) != EXPECTED_CELLS:
        raise SystemExit(
            f"[ERROR] Expected {EXPECTED_CELLS} prediction audit rows, "
            f"found {len(prediction_audit_rows)}"
        )
    pd.DataFrame(prediction_audit_rows).to_csv(
        output_root / "prediction_support_qc.csv", index=False, float_format="%.17g"
    )

    # Table (1) is the diagonal; run4c hard-QC already proves it reproduces the
    # final complexity-balanced Table (1) AUROCs to four decimals.
    table1_point = np.diag(observed_matrix).copy()
    table1_draws = np.empty((args.bootstrap_reps, len(CANDIDATES)), dtype=np.float64)
    for i in range(len(CANDIDATES)):
        table1_draws[:, i] = cell_draws[:, i, i]

    # Paper-facing Table (2) Transfer is the mean of the four off-diagonal target
    # AUROCs for each source candidate.
    transfer_point = np.empty(len(CANDIDATES), dtype=np.float64)
    transfer_draws = np.empty((args.bootstrap_reps, len(CANDIDATES)), dtype=np.float64)
    for i in range(len(CANDIDATES)):
        targets = [j for j in range(len(CANDIDATES)) if j != i]
        transfer_point[i] = float(np.mean(observed_matrix[i, targets]))
        transfer_draws[:, i] = np.mean(cell_draws[:, i, targets], axis=1)

    table1_ranks = descending_ranks(table1_draws)
    transfer_ranks = descending_ranks(transfer_draws)

    table1_summary = summarize_metric(
        table1_point, table1_draws, table1_ranks, args.ci_level, "table1_complexity_balanced_auroc"
    )
    transfer_summary = summarize_metric(
        transfer_point,
        transfer_draws,
        transfer_ranks,
        args.ci_level,
        "table2_cross_generator_transfer_auroc",
    )
    table1_summary.to_csv(
        output_root / "bootstrap_table1_summary.csv", index=False, float_format="%.17g"
    )
    transfer_summary.to_csv(
        output_root / "bootstrap_transfer_summary.csv", index=False, float_format="%.17g"
    )

    # -------------------------------------------------------------------------
    # Minimax regret: magnitude-aware, weight-free decision criterion.
    # -------------------------------------------------------------------------
    best_table1_point = float(np.max(table1_point))
    best_transfer_point = float(np.max(transfer_point))
    regret1_point = best_table1_point - table1_point
    regret2_point = best_transfer_point - transfer_point
    max_regret_point = np.maximum(regret1_point, regret2_point)

    best_table1_draw = np.max(table1_draws, axis=1, keepdims=True)
    best_transfer_draw = np.max(transfer_draws, axis=1, keepdims=True)
    regret1_draws = best_table1_draw - table1_draws
    regret2_draws = best_transfer_draw - transfer_draws
    max_regret_draws = np.maximum(regret1_draws, regret2_draws)
    minimax_ranks = ascending_ranks(max_regret_draws)

    # Point Pareto front and bootstrap non-dominance probability.
    pareto_point = point_pareto(table1_point, transfer_point)
    pareto_draws = pareto_membership(table1_draws, transfer_draws)

    point_rows: list[dict[str, object]] = []
    point_rank_table1 = point_descending_rank(table1_point)
    point_rank_transfer = point_descending_rank(transfer_point)
    point_rank_minimax = point_ascending_rank(max_regret_point)
    for i, candidate in enumerate(CANDIDATES):
        point_rows.append(
            {
                "candidate": candidate.paper_label,
                "config": candidate.config,
                "table1_auroc": float(table1_point[i]),
                "table1_rank": int(point_rank_table1[i]),
                "transfer_auroc": float(transfer_point[i]),
                "transfer_rank": int(point_rank_transfer[i]),
                "regret_table1": float(regret1_point[i]),
                "regret_transfer": float(regret2_point[i]),
                "max_regret": float(max_regret_point[i]),
                "minimax_rank": int(point_rank_minimax[i]),
                "pareto_point": bool(pareto_point[i]),
            }
        )
    point_df = pd.DataFrame(point_rows)
    point_df.to_csv(output_root / "point_estimates.csv", index=False, float_format="%.17g")

    minimax_rows: list[dict[str, object]] = []
    for i, candidate in enumerate(CANDIDATES):
        lo, hi = ci_bounds(max_regret_draws[:, i], args.ci_level)
        minimax_rows.append(
            {
                "candidate": candidate.paper_label,
                "config": candidate.config,
                "point_max_regret": float(max_regret_point[i]),
                "expected_max_regret": float(np.mean(max_regret_draws[:, i])),
                "median_max_regret": float(np.median(max_regret_draws[:, i])),
                "ci_level": args.ci_level,
                "ci_lower": lo,
                "ci_upper": hi,
                "point_minimax_rank": int(point_rank_minimax[i]),
                "expected_minimax_rank": float(np.mean(minimax_ranks[:, i])),
                "p_minimax_winner": float(np.mean(minimax_ranks[:, i] == 1)),
                "p_top2_minimax": float(np.mean(minimax_ranks[:, i] <= 2)),
            }
        )
    minimax_df = pd.DataFrame(minimax_rows)
    minimax_df.to_csv(
        output_root / "minimax_regret_summary.csv", index=False, float_format="%.17g"
    )

    pareto_rows: list[dict[str, object]] = []
    for i, candidate in enumerate(CANDIDATES):
        pareto_rows.append(
            {
                "candidate": candidate.paper_label,
                "config": candidate.config,
                "pareto_point": bool(pareto_point[i]),
                "p_pareto_nondominated": float(np.mean(pareto_draws[:, i])),
            }
        )
    pareto_df = pd.DataFrame(pareto_rows)
    pareto_df.to_csv(output_root / "pareto_summary.csv", index=False, float_format="%.17g")

    # -------------------------------------------------------------------------
    # Pairwise Table (1) differences.
    # These compare source-specific matched test supports and therefore are not
    # described as paired across candidate source generators.
    # -------------------------------------------------------------------------
    pairwise_table1_df = pd.DataFrame(
        pairwise_rows(
            table1_point,
            table1_draws,
            args.ci_level,
            "table1_complexity_balanced",
        )
    )
    pairwise_table1_df.to_csv(
        output_root / "pairwise_table1_differences.csv", index=False, float_format="%.17g"
    )

    # -------------------------------------------------------------------------
    # Pairwise common-target transfer differences.
    # For A versus B, remove target A and target B, leaving exactly three target
    # generators on which both classifiers are off-diagonal. This eliminates the
    # candidate-specific target-composition difference from pairwise inference.
    # -------------------------------------------------------------------------
    common_rows: list[dict[str, object]] = []
    for i in range(len(CANDIDATES)):
        for j in range(i + 1, len(CANDIDATES)):
            common_targets = [k for k in range(len(CANDIDATES)) if k not in (i, j)]
            point_a = float(np.mean(observed_matrix[i, common_targets]))
            point_b = float(np.mean(observed_matrix[j, common_targets]))
            draws_a = np.mean(cell_draws[:, i, common_targets], axis=1)
            draws_b = np.mean(cell_draws[:, j, common_targets], axis=1)
            diff = draws_a - draws_b
            lo, hi = ci_bounds(diff, args.ci_level)
            common_rows.append(
                {
                    "candidate_a": CANDIDATES[i].paper_label,
                    "candidate_b": CANDIDATES[j].paper_label,
                    "common_targets": ";".join(CANDIDATES[k].paper_label for k in common_targets),
                    "n_common_targets": len(common_targets),
                    "point_common_transfer_a": point_a,
                    "point_common_transfer_b": point_b,
                    "point_delta_a_minus_b": point_a - point_b,
                    "bootstrap_mean_delta": float(np.mean(diff)),
                    "ci_level": args.ci_level,
                    "ci_lower": lo,
                    "ci_upper": hi,
                    "p_a_gt_b": float(np.mean(diff > 0.0)),
                    "p_b_gt_a": float(np.mean(diff < 0.0)),
                    "ci_excludes_zero": bool((lo > 0.0) or (hi < 0.0)),
                }
            )
    common_transfer_df = pd.DataFrame(common_rows)
    common_transfer_df.to_csv(
        output_root / "pairwise_transfer_common_targets.csv",
        index=False,
        float_format="%.17g",
    )

    # Persist draw-level candidate metrics for audit and alternative summaries.
    draw_frames: list[pd.DataFrame] = []
    for i, candidate in enumerate(CANDIDATES):
        draw_frames.append(
            pd.DataFrame(
                {
                    "bootstrap_rep": np.arange(args.bootstrap_reps, dtype=np.int64),
                    "candidate": candidate.paper_label,
                    "table1_auroc": table1_draws[:, i],
                    "transfer_auroc": transfer_draws[:, i],
                    "regret_table1": regret1_draws[:, i],
                    "regret_transfer": regret2_draws[:, i],
                    "max_regret": max_regret_draws[:, i],
                    "rank_table1": table1_ranks[:, i],
                    "rank_transfer": transfer_ranks[:, i],
                    "rank_minimax": minimax_ranks[:, i],
                    "pareto_nondominated": pareto_draws[:, i],
                }
            )
        )
    bootstrap_df = pd.concat(draw_frames, ignore_index=True)
    bootstrap_df.to_csv(
        output_root / "bootstrap_candidate_metrics.csv.gz",
        index=False,
        float_format="%.17g",
        compression="gzip",
    )

    write_environment(output_root / "environment.txt", args)
    write_methodology(output_root / "methodology.txt", args)
    write_selection_summary(
        output_root / "candidate_selection_summary.txt",
        point_df,
        minimax_df,
        pareto_df,
        common_transfer_df,
    )

    print("=" * 92)
    print(" Point estimates and minimax regret")
    print("=" * 92)
    display = point_df[
        [
            "candidate",
            "table1_auroc",
            "transfer_auroc",
            "regret_table1",
            "regret_transfer",
            "max_regret",
            "minimax_rank",
            "pareto_point",
        ]
    ].copy()
    for col in [
        "table1_auroc",
        "transfer_auroc",
        "regret_table1",
        "regret_transfer",
        "max_regret",
    ]:
        display[col] = display[col].map(lambda x: f"{float(x):.4f}")
    print(display.sort_values("minimax_rank").to_string(index=False))

    print("\nBootstrap minimax-regret uncertainty")
    display_minimax = minimax_df[
        [
            "candidate",
            "expected_max_regret",
            "ci_lower",
            "ci_upper",
            "expected_minimax_rank",
            "p_minimax_winner",
            "p_top2_minimax",
        ]
    ].copy()
    for col in ["expected_max_regret", "ci_lower", "ci_upper"]:
        display_minimax[col] = display_minimax[col].map(lambda x: f"{float(x):.4f}")
    for col in ["expected_minimax_rank", "p_minimax_winner", "p_top2_minimax"]:
        display_minimax[col] = display_minimax[col].map(lambda x: f"{float(x):.3f}")
    print(display_minimax.sort_values("expected_max_regret").to_string(index=False))

    print("\n[PASS] run4c diagonal QC: 5/5")
    print("[PASS] prediction cells: 25/25")
    print("[PASS] pair-cluster support: 450 pairs per target")
    print("[PASS] full-precision AUROC reproduction against run4c matrix <= 1e-12")
    print(f"[DONE] Results: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
