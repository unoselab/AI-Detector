"""
build_mixed_samples.py
======================

Construct synthetic "mixed-authorship" Python files for testing the
block-level AGC detector (app/agc_detector.py).

Concept
-------
Each sample file is a concatenation of K top-level functions drawn from a
single source CSV that already has per-row labels (human vs lm). The
sample mixes some human blocks and some AI blocks, so the detector under
test can be evaluated per block (HWC vs AGC).

Per the task setup:
  * Block unit             : top-level function/class (one row = one block).
  * Mixing strategy        : concatenation (not mutation).
  * Source pool            : a single ast CSV (default 15B-Instruct).

Output (per sample)
-------------------
For each sample, two files are produced under --out-dir:

    mixed_sample<N>.py            mixed source code, one function per block,
                                  separated by a `# === BLOCK ... ===` marker.
    mixed_sample<N>.labels.tsv    ground truth: block_idx, function_name,
                                  start_line, end_line, label (human|lm),
                                  source_idx (idx in the original CSV).

A combined `manifest.csv` summarises all samples in the run.

Determinism
-----------
The whole procedure is seeded (default 42). Re-running with the same seed
on the same input CSV reproduces identical sample files.

Source split safety
-------------------
By default the script only samples from CSV rows that are in the existing
TEST split for this dataset (so that re-running the detector on these
samples does not leak training data into the test). The split dir is
auto-located via --splits-dir; pass --no-split-filter to disable this and
draw from all rows.
"""

import argparse
import csv
import os
import random
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


# -----------------------------------------------------------------------------
# Defaults (matched to the agreed task setup)
# -----------------------------------------------------------------------------
DEFAULT_SRC_CSV = (
    "src/code-analyzer-tree-sitter/data_codesearchnet/"
    "starcoder2-15b-instruct-v0.1/ast/"
    "codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_2250.csv"
)
DEFAULT_SPLITS_DIR = (
    "src/ml_embeddings/data_codesearchnet/splits/"
    "starcoder2-15b-instruct-v0.1/"
    "codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_2250"
)
DEFAULT_OUT_DIR = "src/app/mixed_samples"

# Block-count distribution per sample. 10 samples × varying K covers
# the "mostly human", "balanced", and "mostly AI" regions, including
# two corner cases (all-human and all-lm).
SAMPLE_SPECS: List[Dict] = [
    {"name": "mixed_sample_001", "n_human": 3, "n_lm": 1},   # 4 blocks
    {"name": "mixed_sample_002", "n_human": 1, "n_lm": 3},   # 4 blocks (inverse)
    {"name": "mixed_sample_003", "n_human": 2, "n_lm": 2},   # 4 blocks balanced
    {"name": "mixed_sample_004", "n_human": 4, "n_lm": 1},   # 5 blocks mostly human
    {"name": "mixed_sample_005", "n_human": 1, "n_lm": 4},   # 5 blocks mostly lm
    {"name": "mixed_sample_006", "n_human": 3, "n_lm": 3},   # 6 blocks balanced
    {"name": "mixed_sample_007", "n_human": 5, "n_lm": 1},   # 6 blocks lopsided
    {"name": "mixed_sample_008", "n_human": 1, "n_lm": 5},   # 6 blocks lopsided inverse
    {"name": "mixed_sample_009", "n_human": 0, "n_lm": 4},   # 4 blocks all-lm (corner)
    {"name": "mixed_sample_010", "n_human": 4, "n_lm": 0},   # 4 blocks all-human (corner)
]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
FUNC_DEF_RE  = re.compile(r"^\s*(async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
CLASS_DEF_RE = re.compile(r"^\s*class\s+(\w+)\s*[:(]", re.MULTILINE)


def extract_function_name(code: str) -> str:
    m = FUNC_DEF_RE.search(code)
    if m:
        return m.group(2)
    m = CLASS_DEF_RE.search(code)
    if m:
        return m.group(1)
    return "<anon>"


def normalize_block(code: str) -> str:
    code = (code or "").rstrip() + "\n"
    if code.strip() == "":
        return "def _empty_block(): pass\n"
    return code


def load_test_idx_set(splits_dir: str) -> Optional[set]:
    test_path = os.path.join(splits_dir, "test_.csv")
    if not os.path.exists(test_path):
        return None
    df = pd.read_csv(test_path, usecols=["idx"])
    return set(df["idx"].tolist())


def sample_rows(
    df: pd.DataFrame,
    n_human: int,
    n_lm: int,
    used: set,
    rng: random.Random,
) -> Tuple[List[pd.Series], List[pd.Series]]:
    pool_human = df[(df["label"] == "human") & (~df["idx"].isin(used))]
    pool_lm    = df[(df["label"] == "lm")    & (~df["idx"].isin(used))]

    if len(pool_human) < n_human:
        raise ValueError(f"need {n_human} human rows, only {len(pool_human)} remain")
    if len(pool_lm) < n_lm:
        raise ValueError(f"need {n_lm} lm rows, only {len(pool_lm)} remain")

    h_idx = rng.sample(pool_human.index.tolist(), n_human)
    l_idx = rng.sample(pool_lm.index.tolist(),    n_lm)
    return [df.loc[i] for i in h_idx], [df.loc[i] for i in l_idx]


def render_sample(rows: List[Tuple[pd.Series, str]]) -> Tuple[str, List[Dict]]:
    lines_out: List[str] = []
    truth: List[Dict] = []

    lines_out.append("# Auto-generated mixed-authorship test sample.")
    lines_out.append("# Block boundaries are marked with a `# === BLOCK ... ===` comment.")
    lines_out.append("# Markers include the ground-truth label; agc_detector strips them at scan time.")
    lines_out.append("")

    for i, (row, label) in enumerate(rows, start=1):
        body = normalize_block(str(row["code"]))
        fname = extract_function_name(body)
        marker = (
            f"# === BLOCK {i} (label={label}, "
            f"source_idx={row['idx']}, name={fname}) ==="
        )

        start_line = len(lines_out) + 1
        lines_out.append(marker)
        for line in body.splitlines():
            lines_out.append(line)
        lines_out.append("")
        end_line = len(lines_out) - 1

        truth.append({
            "block_idx":     i,
            "function_name": fname,
            "start_line":    start_line,
            "end_line":      end_line,
            "label":         label,
            "source_idx":    int(row["idx"]),
        })

    text = "\n".join(lines_out).rstrip() + "\n"
    return text, truth


def write_sample(out_dir: str, name: str, text: str, truth: List[Dict]) -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    py_path  = os.path.join(out_dir, f"{name}.py")
    tsv_path = os.path.join(out_dir, f"{name}.labels.tsv")

    with open(py_path, "w") as f:
        f.write(text)

    fieldnames = ["block_idx", "function_name", "start_line", "end_line",
                  "label", "source_idx"]
    with open(tsv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for r in truth:
            w.writerow(r)

    return py_path, tsv_path


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--src-csv",    default=DEFAULT_SRC_CSV,
                    help="Per-row ast CSV with columns idx, code, ast, label.")
    ap.add_argument("--splits-dir", default=DEFAULT_SPLITS_DIR,
                    help="Per-dataset splits dir; restricts the pool to test rows.")
    ap.add_argument("--out-dir",    default=DEFAULT_OUT_DIR,
                    help="Where to write the .py and .labels.tsv files.")
    ap.add_argument("--seed",       type=int, default=42)
    ap.add_argument("--no-split-filter", action="store_true",
                    help="Draw from all rows in --src-csv, not just test split.")
    return ap.parse_args()


def main():
    args = parse_args()
    rng = random.Random(args.seed)

    if not os.path.exists(args.src_csv):
        raise SystemExit(f"[ERROR] source CSV not found: {args.src_csv}")

    df = pd.read_csv(args.src_csv)
    needed = {"idx", "code", "label"}
    missing = needed - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] source CSV missing columns: {missing}")

    test_idx = None
    if not args.no_split_filter:
        test_idx = load_test_idx_set(args.splits_dir)
        if test_idx is None:
            print(f"[WARN] no test_.csv in {args.splits_dir}; using all rows.")
        else:
            before = len(df)
            df = df[df["idx"].isin(test_idx)].copy()
            print(f"Restricted pool to test split: {len(df)} / {before} rows.")

    df["label"] = df["label"].astype(str).str.strip().str.lower()
    label_counts = df["label"].value_counts().to_dict()
    print(f"Pool label counts: {label_counts}")

    n_human_total = sum(s["n_human"] for s in SAMPLE_SPECS)
    n_lm_total    = sum(s["n_lm"]    for s in SAMPLE_SPECS)
    if label_counts.get("human", 0) < n_human_total:
        raise SystemExit(f"[ERROR] need {n_human_total} human rows total, "
                         f"pool has only {label_counts.get('human', 0)}")
    if label_counts.get("lm", 0) < n_lm_total:
        raise SystemExit(f"[ERROR] need {n_lm_total} lm rows total, "
                         f"pool has only {label_counts.get('lm', 0)}")

    os.makedirs(args.out_dir, exist_ok=True)

    manifest_rows = []
    used: set = set()

    for spec in SAMPLE_SPECS:
        name = spec["name"]
        h_rows, l_rows = sample_rows(df, spec["n_human"], spec["n_lm"], used, rng)
        used.update(r["idx"] for r in h_rows)
        used.update(r["idx"] for r in l_rows)

        labeled = (
            [(r, "human") for r in h_rows] +
            [(r, "lm")    for r in l_rows]
        )
        rng.shuffle(labeled)

        text, truth = render_sample(labeled)
        py_path, tsv_path = write_sample(args.out_dir, name, text, truth)

        h_pos = [t["block_idx"] for t in truth if t["label"] == "human"]
        l_pos = [t["block_idx"] for t in truth if t["label"] == "lm"]
        print(f"  {name}: {len(truth)} blocks "
              f"(human at {h_pos}, lm at {l_pos}) -> {py_path}")

        manifest_rows.append({
            "name":         name,
            "n_blocks":     len(truth),
            "n_human":      len(h_pos),
            "n_lm":         len(l_pos),
            "py_path":      py_path,
            "labels_path":  tsv_path,
        })

    manifest_path = os.path.join(args.out_dir, "manifest.csv")
    pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False)
    print(f"\nManifest -> {manifest_path}")
    print(f"Total samples: {len(manifest_rows)}")
    print(f"Total blocks : {sum(r['n_blocks'] for r in manifest_rows)}  "
          f"(human={sum(r['n_human'] for r in manifest_rows)}, "
          f"lm={sum(r['n_lm'] for r in manifest_rows)})")
    print(f"Unique source idxs used: {len(used)}")


if __name__ == "__main__":
    main()