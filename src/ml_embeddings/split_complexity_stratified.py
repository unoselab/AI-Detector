#!/usr/bin/env python3
"""
split_complexity_stratified.py
==============================

Build one train/dev/test split from a full embedding CSV while preserving
the pair structure and distributing code complexity evenly across splits.

Design for the 4,500-pair StarCoder2-15B experiment:
  total pairs = 4,500
  train       = 3,600 pairs
  dev         =   450 pairs
  test        =   450 pairs

Method:
  1. Load pair-level complexity scores.
  2. Sort pairs by complexity_score.
  3. Process sorted pairs in local blocks of 10.
  4. Randomly assign 8 pairs to train, 1 to dev, and 1 to test from each block.

This gives all splits examples from the full complexity range.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


LABEL_COL = "actual label"


def pair_id_from_idx(idx: object) -> str:
    return re.sub(r"_(human|lm|ai)$", "", str(idx))


def validate_embedding_pairs(df: pd.DataFrame) -> pd.DataFrame:
    required = {"idx", LABEL_COL}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] embedding CSV missing columns: {sorted(missing)}")

    df = df.copy()
    df["idx"] = df["idx"].astype(str)
    df[LABEL_COL] = df[LABEL_COL].astype(int)
    df["_pair_id"] = df["idx"].map(pair_id_from_idx)

    bad = []
    for pair_id, g in df.groupby("_pair_id", sort=True):
        labels = sorted(g[LABEL_COL].unique().tolist())
        if len(g) != 2 or labels != [0, 1]:
            bad.append((pair_id, len(g), labels))

    if bad:
        raise SystemExit(f"[ERROR] bad pair groups, first examples: {bad[:10]}")

    return df


def load_complexity_report(path: Path, pair_ids: set[str]) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"[ERROR] complexity report not found: {path}")

    report = pd.read_csv(path)

    required = {"pair_id", "complexity_score"}
    missing = required - set(report.columns)
    if missing:
        raise SystemExit(f"[ERROR] complexity report missing columns: {sorted(missing)}")

    report = report.copy()
    report["pair_id"] = report["pair_id"].astype(str)

    if "eligible" in report.columns:
        report = report[report["eligible"].astype(bool)].copy()

    report = report[report["pair_id"].isin(pair_ids)].copy()

    missing_ids = pair_ids - set(report["pair_id"])
    if missing_ids:
        sample = sorted(missing_ids)[:10]
        raise SystemExit(
            f"[ERROR] complexity report missing {len(missing_ids)} pair ids. "
            f"Examples: {sample}"
        )

    report = report.sort_values(["complexity_score", "pair_id"]).reset_index(drop=True)
    return report


def assign_complexity_balanced_splits(
    report: pd.DataFrame,
    block_size: int,
    train_per_block: int,
    dev_per_block: int,
    seed: int,
) -> pd.DataFrame:
    test_per_block = block_size - train_per_block - dev_per_block

    if test_per_block <= 0:
        raise SystemExit("[ERROR] block allocation must leave at least one test pair")
    if len(report) % block_size != 0:
        raise SystemExit(
            f"[ERROR] number of pairs ({len(report)}) is not divisible by block_size={block_size}. "
            "Use a different block size or add fallback logic."
        )

    rng = np.random.default_rng(seed)

    rows = []
    sorted_pairs = report[["pair_id", "complexity_score"]].reset_index(drop=True)

    for block_id, start in enumerate(range(0, len(sorted_pairs), block_size)):
        block = sorted_pairs.iloc[start:start + block_size].copy()
        ids = block["pair_id"].to_numpy(dtype=object)
        rng.shuffle(ids)

        train_ids = set(ids[:train_per_block])
        dev_ids = set(ids[train_per_block:train_per_block + dev_per_block])
        test_ids = set(ids[train_per_block + dev_per_block:])

        for _, row in block.iterrows():
            pair_id = row["pair_id"]
            if pair_id in train_ids:
                split = "train"
            elif pair_id in dev_ids:
                split = "dev"
            elif pair_id in test_ids:
                split = "test"
            else:
                raise RuntimeError("unassigned pair")

            rows.append(
                {
                    "pair_id": pair_id,
                    "complexity_score": float(row["complexity_score"]),
                    "complexity_block": block_id,
                    "split": split,
                }
            )

    assignment = pd.DataFrame(rows)

    # Sanity checks.
    counts = assignment["split"].value_counts().to_dict()
    expected = {
        "train": (len(report) // block_size) * train_per_block,
        "dev": (len(report) // block_size) * dev_per_block,
        "test": (len(report) // block_size) * test_per_block,
    }
    if counts != expected:
        raise SystemExit(f"[ERROR] split counts mismatch: got={counts}, expected={expected}")

    return assignment


def select_rows(df: pd.DataFrame, pair_ids: set[str]) -> pd.DataFrame:
    out = df[df["_pair_id"].isin(pair_ids)].copy()
    out = out.sort_values(["_pair_id", LABEL_COL]).drop(columns=["_pair_id"])
    return out.reset_index(drop=True)


def balance_text(df: pd.DataFrame) -> str:
    vc = df[LABEL_COL].astype(int).value_counts().to_dict()
    return f"human(1)={vc.get(1, 0)} ai(0)={vc.get(0, 0)}"


def complexity_summary(assignment: pd.DataFrame) -> pd.DataFrame:
    return (
        assignment
        .groupby("split")["complexity_score"]
        .describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        .reset_index()
    )


def main() -> int:
    p = argparse.ArgumentParser(
        description="Create complexity-balanced train/dev/test split from embedding CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input-csv", required=True, type=Path)
    p.add_argument("--complexity-report", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--dataset-name", required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--block-size", type=int, default=10)
    p.add_argument("--train-per-block", type=int, default=8)
    p.add_argument("--dev-per-block", type=int, default=1)
    args = p.parse_args()

    if not args.input_csv.exists():
        raise SystemExit(f"[ERROR] input CSV not found: {args.input_csv}")

    print("Complexity-balanced split")
    print("=" * 72)
    print(f"input csv        : {args.input_csv}")
    print(f"complexity report: {args.complexity_report}")
    print(f"output dir       : {args.output_dir}")
    print(f"dataset name     : {args.dataset_name}")
    print(f"seed             : {args.seed}")
    print(f"block size       : {args.block_size}")
    print(f"allocation       : train={args.train_per_block}, dev={args.dev_per_block}, test={args.block_size - args.train_per_block - args.dev_per_block}")
    print()

    df = pd.read_csv(args.input_csv)
    df = validate_embedding_pairs(df)

    pair_ids = set(df["_pair_id"])
    report = load_complexity_report(args.complexity_report, pair_ids)

    assignment = assign_complexity_balanced_splits(
        report=report,
        block_size=args.block_size,
        train_per_block=args.train_per_block,
        dev_per_block=args.dev_per_block,
        seed=args.seed,
    )

    train_ids = set(assignment[assignment["split"] == "train"]["pair_id"])
    dev_ids = set(assignment[assignment["split"] == "dev"]["pair_id"])
    test_ids = set(assignment[assignment["split"] == "test"]["pair_id"])

    if train_ids & dev_ids or train_ids & test_ids or dev_ids & test_ids:
        raise SystemExit("[ERROR] split overlap detected")

    out_dataset_dir = args.output_dir / args.dataset_name
    out_dataset_dir.mkdir(parents=True, exist_ok=True)

    train_df = select_rows(df, train_ids)
    dev_df = select_rows(df, dev_ids)
    test_df = select_rows(df, test_ids)

    train_df.to_csv(out_dataset_dir / "train_.csv", index=False)
    dev_df.to_csv(out_dataset_dir / "dev_.csv", index=False)
    test_df.to_csv(out_dataset_dir / "test_.csv", index=False)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    assignment.to_csv(args.output_dir / "complexity_stratified_pair_manifest.csv", index=False)

    summary = complexity_summary(assignment)
    summary.to_csv(args.output_dir / "complexity_stratified_summary.csv", index=False)

    print("Wrote split")
    print("=" * 72)
    print(f"dataset dir: {out_dataset_dir}")
    print(f"train: rows={len(train_df):5d} pairs={len(train_ids):4d} [{balance_text(train_df)}]")
    print(f"dev  : rows={len(dev_df):5d} pairs={len(dev_ids):4d} [{balance_text(dev_df)}]")
    print(f"test : rows={len(test_df):5d} pairs={len(test_ids):4d} [{balance_text(test_df)}]")
    print()
    print("Overlap checks")
    print("=" * 72)
    print(f"train ∩ dev : {len(train_ids & dev_ids)}")
    print(f"train ∩ test: {len(train_ids & test_ids)}")
    print(f"dev ∩ test  : {len(dev_ids & test_ids)}")
    print()
    print("Complexity summary")
    print("=" * 72)
    print(summary.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
