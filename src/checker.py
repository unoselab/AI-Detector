import re
import pandas as pd
from pathlib import Path

ROOT = Path("ml_embeddings/data_codesearchnet/splits")

def pair_id(x):
    return re.sub(r"_(human|lm|ai)$", "", str(x))

expected = {
    "codesearchnet_starcoder2-7b_python_merged": {
        "train": (640, {1: 320, 0: 320}),
        "dev":   (80,  {1: 40,  0: 40}),
        "test":  (80,  {1: 40,  0: 40}),
    },
    "codesearchnet_starcoder2-7b_python_merged_2250": {
        "train": (3600, {1: 1800, 0: 1800}),
        "dev":   (450,  {1: 225,  0: 225}),
        "test":  (450,  {1: 225,  0: 225}),
    },
}

for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    print("=" * 100)
    print("DATASET:", d.name)

    split_pairs = {}
    all_rows = 0

    for split in ["train", "dev", "test"]:
        p = d / f"{split}_.csv"
        df = pd.read_csv(p)

        code_cols = [c for c in df.columns if c.startswith("code_")]
        ast_cols = [c for c in df.columns if c.startswith("ast_")]
        combined_cols = [c for c in df.columns if c.startswith("combined_")]

        pairs = set(df["idx"].map(pair_id))
        split_pairs[split] = pairs
        all_rows += len(df)

        bad_pairs = []
        for pid, g in df.groupby(df["idx"].map(pair_id)):
            labels = sorted(g["actual label"].unique().tolist())
            if len(g) != 2 or labels != [0, 1]:
                bad_pairs.append((pid, len(g), labels))

        label_counts = df["actual label"].value_counts().to_dict()

        print(f"{split:5s}", df.shape)
        print("  labels:", label_counts)
        print("  pairs:", len(pairs))
        print("  bad_pairs:", len(bad_pairs))
        print("  emb cols:", len(code_cols), len(ast_cols), len(combined_cols))

        exp_rows, exp_labels = expected[d.name][split]
        assert len(df) == exp_rows, f"{d.name}/{split}: row count mismatch"
        assert label_counts == exp_labels, f"{d.name}/{split}: label count mismatch"
        assert len(bad_pairs) == 0, f"{d.name}/{split}: bad grouped pairs"
        assert len(code_cols) == 256, f"{d.name}/{split}: bad code dim"
        assert len(ast_cols) == 256, f"{d.name}/{split}: bad ast dim"
        assert len(combined_cols) == 256, f"{d.name}/{split}: bad combined dim"

    train_dev = split_pairs["train"] & split_pairs["dev"]
    train_test = split_pairs["train"] & split_pairs["test"]
    dev_test = split_pairs["dev"] & split_pairs["test"]

    print("train/dev overlap:", len(train_dev))
    print("train/test overlap:", len(train_test))
    print("dev/test overlap:", len(dev_test))

    assert len(train_dev) == 0, "train/dev pair leakage"
    assert len(train_test) == 0, "train/test pair leakage"
    assert len(dev_test) == 0, "dev/test pair leakage"

print("\n[OK] grouped split verification passed")