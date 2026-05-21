"""
split_data.py
=============

Train/dev/test splitter for embedding CSVs.

Default behavior:
  Row-level stratified split on `actual label`.

Optional grouped behavior:
  --group-by-pair-id keeps paired rows such as:
      line217_human
      line217_lm
  in the same split by grouping on `line217`.

Output:
  <output-dir>/<dataset_name>/
      train_.csv
      dev_.csv
      test_.csv
"""

import argparse
import os
import re
from glob import glob

import pandas as pd
from sklearn.model_selection import train_test_split


LABEL_COL = "actual label"


def pair_id_from_idx(idx):
    s = str(idx)
    return re.sub(r"_(human|lm|ai)$", "", s)


def split_csv_row_stratified(csv_in, out_root, train_frac, dev_frac, test_frac, seed):
    df = pd.read_csv(csv_in)

    if LABEL_COL not in df.columns:
        raise ValueError(f"missing label column '{LABEL_COL}' in {csv_in}")

    train_df, temp_df = train_test_split(
        df,
        train_size=train_frac,
        random_state=seed,
        stratify=df[LABEL_COL],
    )

    rel_dev = dev_frac / (dev_frac + test_frac)
    dev_df, test_df = train_test_split(
        temp_df,
        train_size=rel_dev,
        random_state=seed,
        stratify=temp_df[LABEL_COL],
    )

    return train_df, dev_df, test_df


def split_csv_grouped_by_pair(csv_in, out_root, train_frac, dev_frac, test_frac, seed):
    df = pd.read_csv(csv_in)

    if "idx" not in df.columns:
        raise ValueError(f"missing idx column required for grouped split in {csv_in}")
    if LABEL_COL not in df.columns:
        raise ValueError(f"missing label column '{LABEL_COL}' in {csv_in}")

    df = df.copy()
    df["_pair_id"] = df["idx"].map(pair_id_from_idx)

    bad_groups = []
    for pair_id, g in df.groupby("_pair_id"):
        labels = sorted(g[LABEL_COL].unique().tolist())
        if len(g) != 2 or labels != [0, 1]:
            bad_groups.append((pair_id, len(g), labels))

    if bad_groups:
        preview = bad_groups[:10]
        raise ValueError(
            f"grouped split requires exactly one human(1) and one AI(0) row per pair. "
            f"Bad groups: {preview}"
        )

    pair_ids = sorted(df["_pair_id"].unique())

    train_ids, temp_ids = train_test_split(
        pair_ids,
        train_size=train_frac,
        random_state=seed,
        shuffle=True,
    )

    rel_dev = dev_frac / (dev_frac + test_frac)
    dev_ids, test_ids = train_test_split(
        temp_ids,
        train_size=rel_dev,
        random_state=seed,
        shuffle=True,
    )

    train_ids = set(train_ids)
    dev_ids = set(dev_ids)
    test_ids = set(test_ids)

    train_df = df[df["_pair_id"].isin(train_ids)].drop(columns=["_pair_id"])
    dev_df = df[df["_pair_id"].isin(dev_ids)].drop(columns=["_pair_id"])
    test_df = df[df["_pair_id"].isin(test_ids)].drop(columns=["_pair_id"])

    return train_df, dev_df, test_df


def write_splits(csv_in, out_root, train_df, dev_df, test_df):
    dataset_name = os.path.splitext(os.path.basename(csv_in))[0]
    out_dir = os.path.join(out_root, dataset_name)
    os.makedirs(out_dir, exist_ok=True)

    train_df.to_csv(os.path.join(out_dir, "train_.csv"), index=False)
    dev_df.to_csv(os.path.join(out_dir, "dev_.csv"), index=False)
    test_df.to_csv(os.path.join(out_dir, "test_.csv"), index=False)


def balance(df):
    vc = df[LABEL_COL].value_counts().to_dict()
    return f"human(1)={vc.get(1, 0)}  ai(0)={vc.get(0, 0)}"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="data_main_with_embeddings")
    ap.add_argument("--output-dir", default="splits")
    ap.add_argument("--train-frac", type=float, default=0.80)
    ap.add_argument("--dev-frac", type=float, default=0.10)
    ap.add_argument("--test-frac", type=float, default=0.10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--group-by-pair-id",
        action="store_true",
        help="Keep paired idx rows such as line217_human and line217_lm in the same split.",
    )
    return ap.parse_args()


def main():
    args = parse_args()

    total = args.train_frac + args.dev_frac + args.test_frac
    if abs(total - 1.0) > 1e-6:
        raise SystemExit(f"split fractions must sum to 1.0, got {total:.4f}")

    csv_files = sorted(glob(os.path.join(args.input_dir, "**", "*.csv"), recursive=True))
    if not csv_files:
        raise SystemExit(f"[ERROR] no CSVs found under {args.input_dir}")

    print(f"Split fractions: train={args.train_frac}  dev={args.dev_frac}  test={args.test_frac}")
    print(f"Seed:            {args.seed}")
    print(f"Grouped pairs:   {args.group_by_pair_id}")
    print(f"Input  : {args.input_dir}")
    print(f"Output : {args.output_dir}")
    print(f"Found {len(csv_files)} CSV(s).\n")

    grand_train = grand_dev = grand_test = 0

    for csv_in in csv_files:
        name = os.path.splitext(os.path.basename(csv_in))[0]
        print(f"=== {name} ===")

        if args.group_by_pair_id:
            train_df, dev_df, test_df = split_csv_grouped_by_pair(
                csv_in, args.output_dir, args.train_frac, args.dev_frac, args.test_frac, args.seed
            )
        else:
            train_df, dev_df, test_df = split_csv_row_stratified(
                csv_in, args.output_dir, args.train_frac, args.dev_frac, args.test_frac, args.seed
            )

        write_splits(csv_in, args.output_dir, train_df, dev_df, test_df)

        print(f"  train={len(train_df):5d}  [{balance(train_df)}]")
        print(f"  dev  ={len(dev_df):5d}  [{balance(dev_df)}]")
        print(f"  test ={len(test_df):5d}  [{balance(test_df)}]")

        grand_train += len(train_df)
        grand_dev += len(dev_df)
        grand_test += len(test_df)

    print("\nGrand totals:")
    print(f"  train={grand_train}")
    print(f"  dev  ={grand_dev}")
    print(f"  test ={grand_test}")


if __name__ == "__main__":
    main()