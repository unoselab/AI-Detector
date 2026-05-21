"""
split_data.py
=============

Stratified 80/10/10 train/dev/test split for the AI-Detector embedding CSVs.

Reference paper
---------------
Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
Source Code: How Far Are We?", ICSE 2025.
Section IV.D ("Within" evaluation): "we split each dataset into 80% training,
10% validation, and 10% testing sets" with stratification on the label.

Input
-----
Embedding-augmented CSVs produced by `generate_embeddings.py` (one per
dataset/LLM/language combo). Each CSV must contain an `actual label`
column with integer values (1 = human, 0 = AI).

Output
------
One directory per input CSV under the chosen output root:

    <output-dir>/<dataset_name>/
        train_.csv
        dev_.csv
        test_.csv

The trailing underscore matches the naming convention used elsewhere in
the project (see `astnn/classification/.../data/train/train_.pkl`).
The downstream `hyperparameter_tuning.py` and `test_embedding.py` scripts
locate files via substring match on `'train'` / `'test'`, so either
`train.csv` or `train_.csv` would work; the underscore form is used here
for consistency with the existing pipeline.

Splits are deterministic given the seed (default 42).
"""

import argparse
import os
from glob import glob

import pandas as pd
from sklearn.model_selection import train_test_split


# -----------------------------------------------------------------------------
# Defaults
# -----------------------------------------------------------------------------
DEFAULT_SEED       = 42
DEFAULT_TRAIN_FRAC = 0.80
DEFAULT_DEV_FRAC   = 0.10
DEFAULT_TEST_FRAC  = 0.10
LABEL_COL          = "actual label"


# -----------------------------------------------------------------------------
# Splitting
# -----------------------------------------------------------------------------
def split_csv(csv_in, out_root, train_frac, dev_frac, test_frac, seed):
    """Split one CSV into train/dev/test, stratified on `actual label`."""
    df = pd.read_csv(csv_in)

    if LABEL_COL not in df.columns:
        raise ValueError(
            f"missing label column '{LABEL_COL}' in {csv_in} "
            f"(found: {list(df.columns)[:8]}...)"
        )

    # First cut: train vs (dev + test).
    train_df, temp_df = train_test_split(
        df,
        train_size=train_frac,
        random_state=seed,
        stratify=df[LABEL_COL],
    )

    # Second cut: split the held-out portion proportionally into dev and test.
    # `rel_dev` is the dev fraction within `temp_df` (e.g., 0.5 for a 10/10 split).
    rel_dev = dev_frac / (dev_frac + test_frac)
    dev_df, test_df = train_test_split(
        temp_df,
        train_size=rel_dev,
        random_state=seed,
        stratify=temp_df[LABEL_COL],
    )

    dataset_name = os.path.splitext(os.path.basename(csv_in))[0]
    out_dir = os.path.join(out_root, dataset_name)
    os.makedirs(out_dir, exist_ok=True)

    train_df.to_csv(os.path.join(out_dir, "train_.csv"), index=False)
    dev_df.to_csv(os.path.join(out_dir,   "dev_.csv"),   index=False)
    test_df.to_csv(os.path.join(out_dir,  "test_.csv"),  index=False)

    return train_df, dev_df, test_df


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--input-dir", default="data_main_with_embeddings",
        help="Directory of embedding-augmented CSVs from generate_embeddings.py.",
    )
    ap.add_argument(
        "--output-dir", default="splits",
        help="Where to write per-dataset train/dev/test subdirectories.",
    )
    ap.add_argument("--train-frac", type=float, default=DEFAULT_TRAIN_FRAC)
    ap.add_argument("--dev-frac",   type=float, default=DEFAULT_DEV_FRAC)
    ap.add_argument("--test-frac",  type=float, default=DEFAULT_TEST_FRAC)
    ap.add_argument("--seed",       type=int,   default=DEFAULT_SEED)
    return ap.parse_args()


def main():
    args = parse_args()

    total = args.train_frac + args.dev_frac + args.test_frac
    if abs(total - 1.0) > 1e-6:
        raise SystemExit(
            f"--train-frac + --dev-frac + --test-frac must sum to 1.0 (got {total:.4f})"
        )

    csv_files = sorted(
        glob(os.path.join(args.input_dir, "**", "*.csv"), recursive=True)
    )
    if not csv_files:
        raise SystemExit(f"[ERROR] no CSVs found under {args.input_dir}")

    print(f"Split fractions: train={args.train_frac}  dev={args.dev_frac}  test={args.test_frac}")
    print(f"Seed:            {args.seed}")
    print(f"Input  : {args.input_dir}")
    print(f"Output : {args.output_dir}")
    print(f"Found {len(csv_files)} CSV(s).\n")

    grand_train = grand_dev = grand_test = 0
    for csv_in in csv_files:
        name = os.path.splitext(os.path.basename(csv_in))[0]
        print(f"=== {name} ===")
        train_df, dev_df, test_df = split_csv(
            csv_in,
            args.output_dir,
            args.train_frac,
            args.dev_frac,
            args.test_frac,
            args.seed,
        )

        # Show class balance per split (sanity check on stratification).
        def balance(d):
            vc = d[LABEL_COL].value_counts().to_dict()
            return f"human(1)={vc.get(1,0)}  ai(0)={vc.get(0,0)}"

        print(f"  train={len(train_df):5d}  [{balance(train_df)}]")
        print(f"  dev  ={len(dev_df):5d}  [{balance(dev_df)}]")
        print(f"  test ={len(test_df):5d}  [{balance(test_df)}]")

        grand_train += len(train_df)
        grand_dev   += len(dev_df)
        grand_test  += len(test_df)

    print(f"\nTotals: train={grand_train}  dev={grand_dev}  test={grand_test}")
    print("Done.")


if __name__ == "__main__":
    main()