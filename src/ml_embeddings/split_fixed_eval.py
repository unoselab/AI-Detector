#!/usr/bin/env python3
"""
split_fixed_eval.py
===================

Build nested training-size splits with the same fixed dev/test pairs.

Input:
  One full embedding CSV, usually *_merged_2700.csv.

Output:
  <output-dir>/<prefix>_merged_0500/{train_,dev_,test_}.csv
  ...
  <output-dir>/<prefix>_merged_2500/{train_,dev_,test_}.csv

Design:
  2700 total pairs
  = 2500 training-candidate pairs
  + 100 fixed dev pairs
  + 100 fixed test pairs

For order-mode=random:
  training candidates are randomly ordered.

For order-mode=complexity:
  training candidates are sorted by complexity_score from the complexity report.
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


def parse_sizes(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def validate_pairs(df: pd.DataFrame) -> pd.DataFrame:
    if "idx" not in df.columns:
        raise SystemExit("[ERROR] missing idx column")
    if LABEL_COL not in df.columns:
        raise SystemExit(f"[ERROR] missing {LABEL_COL} column")

    df = df.copy()
    df["_pair_id"] = df["idx"].map(pair_id_from_idx)

    bad = []
    for pair_id, g in df.groupby("_pair_id"):
        labels = sorted(g[LABEL_COL].astype(int).unique().tolist())
        if len(g) != 2 or labels != [0, 1]:
            bad.append((pair_id, len(g), labels))

    if bad:
        raise SystemExit(f"[ERROR] bad pair groups, first examples: {bad[:10]}")

    return df


def make_fixed_eval_ids(pair_ids: list[str], dev_pairs: int, test_pairs: int, seed: int):
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(pair_ids), dtype=object)
    rng.shuffle(ids)

    if len(ids) < dev_pairs + test_pairs:
        raise SystemExit("[ERROR] not enough pairs for fixed dev/test")

    dev_ids = ids[:dev_pairs].tolist()
    test_ids = ids[dev_pairs:dev_pairs + test_pairs].tolist()
    train_candidate_ids = ids[dev_pairs + test_pairs:].tolist()

    return dev_ids, test_ids, train_candidate_ids


def order_train_candidates_random(train_candidate_ids: list[str], seed: int) -> list[str]:
    rng = np.random.default_rng(seed + 1000)
    ids = np.array(train_candidate_ids, dtype=object)
    rng.shuffle(ids)
    return ids.tolist()


def order_train_candidates_complexity(
    train_candidate_ids: list[str],
    complexity_report: Path,
) -> list[str]:
    if complexity_report is None or not complexity_report.exists():
        raise SystemExit(f"[ERROR] complexity report not found: {complexity_report}")

    report = pd.read_csv(complexity_report)
    required = {"pair_id", "complexity_score"}
    missing = required - set(report.columns)
    if missing:
        raise SystemExit(f"[ERROR] complexity report missing columns: {sorted(missing)}")

    cand = set(train_candidate_ids)
    report = report[report["pair_id"].isin(cand)].copy()

    missing_ids = cand - set(report["pair_id"])
    if missing_ids:
        raise SystemExit(f"[ERROR] complexity report missing {len(missing_ids)} candidate pair ids")

    report = report.sort_values(
        ["complexity_score", "pair_id"],
        ascending=[True, True],
    )

    return report["pair_id"].tolist()


def select_rows(df: pd.DataFrame, pair_ids: set[str]) -> pd.DataFrame:
    out = df[df["_pair_id"].isin(pair_ids)].copy()
    out = out.sort_values(["_pair_id", LABEL_COL]).drop(columns=["_pair_id"])
    return out.reset_index(drop=True)


def balance(df: pd.DataFrame) -> str:
    vc = df[LABEL_COL].astype(int).value_counts().to_dict()
    return f"human(1)={vc.get(1, 0)} ai(0)={vc.get(0, 0)}"


def write_one_split(
    df: pd.DataFrame,
    output_dir: Path,
    dataset_name: str,
    train_ids: set[str],
    dev_ids: set[str],
    test_ids: set[str],
) -> dict:
    out_dir = output_dir / dataset_name
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df = select_rows(df, train_ids)
    dev_df = select_rows(df, dev_ids)
    test_df = select_rows(df, test_ids)

    train_df.to_csv(out_dir / "train_.csv", index=False)
    dev_df.to_csv(out_dir / "dev_.csv", index=False)
    test_df.to_csv(out_dir / "test_.csv", index=False)

    return {
        "dataset": dataset_name,
        "train_rows": len(train_df),
        "dev_rows": len(dev_df),
        "test_rows": len(test_df),
        "train_balance": balance(train_df),
        "dev_balance": balance(dev_df),
        "test_balance": balance(test_df),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-csv", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--sizes", default="500,1000,1500,2000,2500")
    ap.add_argument("--dev-pairs", type=int, default=100)
    ap.add_argument("--test-pairs", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--order-mode", choices=["random", "complexity"], default="random")
    ap.add_argument("--complexity-report", type=Path, default=None)
    args = ap.parse_args()

    sizes = parse_sizes(args.sizes)

    print("Fixed-evaluation nested split")
    print("=" * 72)
    print(f"input csv        : {args.input_csv}")
    print(f"output dir       : {args.output_dir}")
    print(f"prefix           : {args.prefix}")
    print(f"sizes            : {sizes}")
    print(f"dev pairs        : {args.dev_pairs}")
    print(f"test pairs       : {args.test_pairs}")
    print(f"seed             : {args.seed}")
    print(f"order mode       : {args.order_mode}")
    print(f"complexity report: {args.complexity_report}")
    print()

    df = pd.read_csv(args.input_csv)
    df = validate_pairs(df)

    pair_ids = sorted(df["_pair_id"].unique().tolist())
    dev_ids, test_ids, train_candidate_ids = make_fixed_eval_ids(
        pair_ids=pair_ids,
        dev_pairs=args.dev_pairs,
        test_pairs=args.test_pairs,
        seed=args.seed,
    )

    if len(train_candidate_ids) < max(sizes):
        raise SystemExit(
            f"[ERROR] need {max(sizes)} train pairs, but only "
            f"{len(train_candidate_ids)} remain after fixed dev/test"
        )

    if args.order_mode == "random":
        train_order = order_train_candidates_random(train_candidate_ids, args.seed)
    else:
        train_order = order_train_candidates_complexity(
            train_candidate_ids=train_candidate_ids,
            complexity_report=args.complexity_report,
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    dev_set = set(dev_ids)
    test_set = set(test_ids)

    rows = []
    for n in sizes:
        train_set = set(train_order[:n])

        if train_set & dev_set or train_set & test_set or dev_set & test_set:
            raise SystemExit("[ERROR] train/dev/test overlap detected")

        dataset_name = f"{args.prefix}_merged_{n:04d}"
        summary = write_one_split(
            df=df,
            output_dir=args.output_dir,
            dataset_name=dataset_name,
            train_ids=train_set,
            dev_ids=dev_set,
            test_ids=test_set,
        )

        print(f"=== {dataset_name} ===")
        print(f"  train={summary['train_rows']:5d} [{summary['train_balance']}]")
        print(f"  dev  ={summary['dev_rows']:5d} [{summary['dev_balance']}]")
        print(f"  test ={summary['test_rows']:5d} [{summary['test_balance']}]")

        rows.append(summary)

    manifest = pd.DataFrame(rows)
    manifest_path = args.output_dir / "fixed_eval_split_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    pair_manifest_rows = []
    for pid in train_order:
        pair_manifest_rows.append({"pair_id": pid, "role": "train_candidate"})
    for pid in dev_ids:
        pair_manifest_rows.append({"pair_id": pid, "role": "dev"})
    for pid in test_ids:
        pair_manifest_rows.append({"pair_id": pid, "role": "test"})

    pair_manifest = pd.DataFrame(pair_manifest_rows)
    pair_manifest_path = args.output_dir / "fixed_eval_pair_manifest.csv"
    pair_manifest.to_csv(pair_manifest_path, index=False)

    print()
    print(f"manifest     : {manifest_path}")
    print(f"pair manifest: {pair_manifest_path}")
    print("Done.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
