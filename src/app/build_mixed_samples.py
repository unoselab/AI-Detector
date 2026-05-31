"""
build_mixed_samples.py
======================

Construct synthetic "mixed-authorship" Python files for testing the
block-level AGC detector (app/agc_detector.py).

Each sample file is a concatenation of top-level functions/classes drawn
from a SINGLE source CSV. The author of each row (human vs lm) is taken
from the row's `idx` suffix (`..._human` / `..._lm`); a string `label`
column or an integer `actual label` column are also accepted as fallbacks.

Single-input model:
Point --input-csv at the split's `test_.csv`. Because every row in that file
is already test data, no separate split-filter step is needed - test-only
sampling is guaranteed structurally by which CSV you pass in. Only the `idx`
and `code` columns are loaded, so heavy embedding columns are skipped.
"""

import argparse
import csv
import os
import random
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


# -----------------------------------------------------------------------------
# Defaults
# -----------------------------------------------------------------------------
# Single input: the split's test_.csv. Every row here is test data, so the
# old src-csv + splits-dir pair collapses to this one file.
DEFAULT_INPUT_CSV = (
    "src/ml_embeddings/data_codesearchnet/splits/"
    "starcoder2-15b-instruct-v0.1/"
    "codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_2700/test_.csv"
)
DEFAULT_OUT_DIR = "src/app/mixed_samples"


# Legacy default: 10 small samples.
SAMPLE_SPECS: List[Dict] = [
    {"name": "mixed_sample_001", "n_human": 3, "n_lm": 1},
    {"name": "mixed_sample_002", "n_human": 1, "n_lm": 3},
    {"name": "mixed_sample_003", "n_human": 2, "n_lm": 2},
    {"name": "mixed_sample_004", "n_human": 4, "n_lm": 1},
    {"name": "mixed_sample_005", "n_human": 1, "n_lm": 4},
    {"name": "mixed_sample_006", "n_human": 3, "n_lm": 3},
    {"name": "mixed_sample_007", "n_human": 5, "n_lm": 1},
    {"name": "mixed_sample_008", "n_human": 1, "n_lm": 5},
    {"name": "mixed_sample_009", "n_human": 0, "n_lm": 4},
    {"name": "mixed_sample_010", "n_human": 4, "n_lm": 0},
]


# -----------------------------------------------------------------------------
# Spec builder
# -----------------------------------------------------------------------------
def build_sample_specs(
    num_samples: Optional[int],
    blocks_per_sample: Optional[int],
    lm_ratio: float,
    include_corners: bool,
) -> List[Dict]:
    """
    If num_samples and blocks_per_sample are omitted, use legacy SAMPLE_SPECS.

    Otherwise generate:
      mixed_sample_001 ... mixed_sample_N

    Example:
      --num-samples 50 --blocks-per-sample 6 --lm-ratio 0.5
      -> 50 files, each with 3 human + 3 lm blocks.

    If --include-corners is set:
      sample 001 = all human
      sample 002 = all lm
    """
    if num_samples is None and blocks_per_sample is None:
        return SAMPLE_SPECS

    n = num_samples if num_samples is not None else len(SAMPLE_SPECS)
    k = blocks_per_sample if blocks_per_sample is not None else 6

    if n <= 0:
        raise SystemExit("[ERROR] --num-samples must be > 0")
    if k <= 0:
        raise SystemExit("[ERROR] --blocks-per-sample must be > 0")
    if not (0.0 <= lm_ratio <= 1.0):
        raise SystemExit("[ERROR] --lm-ratio must be between 0.0 and 1.0")

    n_lm = int(round(k * lm_ratio))
    n_lm = max(0, min(k, n_lm))
    n_human = k - n_lm

    specs: List[Dict] = []
    for i in range(1, n + 1):
        specs.append({
            "name": f"mixed_sample_{i:03d}",
            "n_human": n_human,
            "n_lm": n_lm,
        })

    if include_corners and n >= 2:
        specs[0]["n_human"], specs[0]["n_lm"] = k, 0
        specs[1]["n_human"], specs[1]["n_lm"] = 0, k

    return specs


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
FUNC_DEF_RE = re.compile(r"^\s*(async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
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


# Columns we actually need from the input CSV. Everything else (e.g. the
# 256-dim code/ast/combined embedding columns in an embedding CSV) is skipped
# at read time so loading test_.csv stays cheap.
WANTED_INPUT_COLS = {"idx", "code", "label", "actual label"}

LABEL_SUFFIX_RE = re.compile(r"_(human|lm)$", re.IGNORECASE)

# Fallback only: integer label convention from the embedding pipeline
# (human=1, lm=0). Used solely when neither a `label` column nor an idx
# suffix is available.
INT_LABEL_MAP = {1: "human", 0: "lm"}


def label_from_idx(idx: object) -> Optional[str]:
    m = LABEL_SUFFIX_RE.search(str(idx))
    return m.group(1).lower() if m else None


def resolve_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach a normalized string `label` column (values: human / lm).

    Resolution order:
      1. explicit `label` column (legacy AST CSV),
      2. `idx` suffix `_human` / `_lm` (the test_.csv case),
      3. integer `actual label` column (last-resort fallback).
    """
    df = df.copy()

    if "label" in df.columns:
        df["label"] = df["label"].astype(str).str.strip().str.lower()
        return df

    suffix = df["idx"].map(label_from_idx)
    if suffix.notna().all():
        df["label"] = suffix.str.lower()
        return df

    if "actual label" in df.columns:
        print("[WARN] no `label` column or idx suffix found; deriving label from")
        print("       integer `actual label` (human=1, lm=0). Verify this matches")
        print("       your pipeline before reporting results.")
        df["label"] = df["actual label"].astype(int).map(INT_LABEL_MAP)
        if df["label"].isna().any():
            raise SystemExit("[ERROR] could not map `actual label` to human/lm")
        return df

    raise SystemExit(
        "[ERROR] cannot determine author labels. The input CSV needs one of:\n"
        "        - a string `label` column (human/lm), or\n"
        "        - an idx suffix like `..._human` / `..._lm`, or\n"
        "        - an integer `actual label` column."
    )


def sample_rows(
    df: pd.DataFrame,
    n_human: int,
    n_lm: int,
    used: set,
    rng: random.Random,
) -> Tuple[List[pd.Series], List[pd.Series]]:
    pool_human = df[(df["label"] == "human") & (~df["idx"].isin(used))]
    pool_lm = df[(df["label"] == "lm") & (~df["idx"].isin(used))]

    if len(pool_human) < n_human:
        raise ValueError(f"need {n_human} human rows, only {len(pool_human)} remain")
    if len(pool_lm) < n_lm:
        raise ValueError(f"need {n_lm} lm rows, only {len(pool_lm)} remain")

    h_idx = rng.sample(pool_human.index.tolist(), n_human)
    l_idx = rng.sample(pool_lm.index.tolist(), n_lm)

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
            "block_idx": i,
            "function_name": fname,
            "start_line": start_line,
            "end_line": end_line,
            "label": label,
            "source_idx": str(row["idx"]),
        })

    text = "\n".join(lines_out).rstrip() + "\n"
    return text, truth


def write_sample(out_dir: str, name: str, text: str, truth: List[Dict]) -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    py_path = os.path.join(out_dir, f"{name}.py")
    tsv_path = os.path.join(out_dir, f"{name}.labels.tsv")

    with open(py_path, "w") as f:
        f.write(text)

    fieldnames = [
        "block_idx",
        "function_name",
        "start_line",
        "end_line",
        "label",
        "source_idx",
    ]

    with open(tsv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for r in truth:
            w.writerow(r)

    return py_path, tsv_path


def parse_grid_configs(text: str) -> List[Tuple[int, int]]:
    """
    Parse grid config string.

    Format:
      "2:240,4:120,6:80,8:60,10:48"

    Meaning:
      blocks_per_sample:num_samples
    """
    configs: List[Tuple[int, int]] = []

    for item in text.split(","):
        item = item.strip()
        if not item:
            continue

        if ":" not in item:
            raise SystemExit(
                f"[ERROR] bad --grid-configs item: {item}\n"
                "        Expected format like 2:240,4:120,6:80"
            )

        k_s, n_s = item.split(":", 1)
        k = int(k_s)
        n = int(n_s)

        if k <= 0:
            raise SystemExit(f"[ERROR] blocks_per_sample must be > 0: {k}")
        if n <= 0:
            raise SystemExit(f"[ERROR] num_samples must be > 0: {n}")

        configs.append((k, n))

    if not configs:
        raise SystemExit("[ERROR] --grid-configs produced no configs")

    return configs


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    ap.add_argument("--input-csv", "--src-csv", dest="input_csv",
                    default=DEFAULT_INPUT_CSV,
                    help="Single input CSV (e.g. the split's test_.csv). "
                         "Only `idx` and `code` are loaded; the author label is "
                         "taken from the idx suffix `_human`/`_lm`. "
                         "(`--src-csv` is a deprecated alias.)")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                    help="Where to write generated .py and .labels.tsv files.")
    ap.add_argument("--seed", type=int, default=42)

    ap.add_argument("--num-samples", type=int, default=None,
                    help="Number of mixed .py files to generate.")
    ap.add_argument("--blocks-per-sample", type=int, default=None,
                    help="Number of top-level blocks per generated mixed file.")
    ap.add_argument("--lm-ratio", type=float, default=0.5,
                    help="Fraction of blocks sampled from lm/AGC rows.")
    ap.add_argument("--include-corners", action="store_true",
                    help="Make sample 001 all-human and sample 002 all-lm.")
    ap.add_argument("--allow-reuse", action="store_true",
                    help="Allow the same source row to appear in multiple samples.")

    # Deprecated: kept so older driver scripts (e.g. the grid runner) that still
    # pass these flags do not crash. They are ignored; the input CSV is used
    # directly, so point --input-csv at test_.csv for test-only sampling.
    ap.add_argument("--splits-dir", default=None,
                    help="[DEPRECATED] ignored; the input CSV is used directly.")
    ap.add_argument("--no-split-filter", action="store_true",
                    help="[DEPRECATED] ignored; the input CSV is used directly.")

    ap.add_argument("--grid-out-root", default=None,
                    help="If set, build multiple grid directories under this root.")
    ap.add_argument("--grid-configs", default="2:240,4:120,6:80,8:60,10:48",
                    help="Grid configs as blocks_per_sample:num_samples pairs.")
    ap.add_argument("--validate-python", action="store_true",
                    help="After writing samples, verify generated .py files parse.")    

    return ap.parse_args()


def build_one_output_dir(
    args,
    out_dir: str,
    sample_specs: List[Dict],
    rng: random.Random,
) -> Dict:
    if not os.path.exists(args.input_csv):
        raise SystemExit(f"[ERROR] input CSV not found: {args.input_csv}")

    # Load only the columns we use; this skips the heavy embedding columns
    # (code_0.., ast_0.., combined_0..) present in an embedding/test CSV.
    df = pd.read_csv(args.input_csv, usecols=lambda c: c in WANTED_INPUT_COLS)

    needed = {"idx", "code"}
    missing = needed - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] input CSV missing columns: {missing}")

    df["idx"] = df["idx"].astype(str)

    if args.splits_dir or args.no_split_filter:
        print("[WARN] --splits-dir / --no-split-filter are deprecated and ignored.")
        print("       The input CSV is now used directly. To keep test-only")
        print("       sampling, point --input-csv at the split's test_.csv.")

    df = resolve_labels(df)
    label_counts = df["label"].value_counts().to_dict()
    print(f"Input rows: {len(df)} from {args.input_csv}")
    print(f"Pool label counts: {label_counts}")

    n_human_total = sum(spec["n_human"] for spec in sample_specs)
    n_lm_total = sum(spec["n_lm"] for spec in sample_specs)

    if not args.allow_reuse:
        if label_counts.get("human", 0) < n_human_total:
            raise SystemExit(
                f"[ERROR] need {n_human_total} human rows total, "
                f"pool has only {label_counts.get('human', 0)}"
            )
        if label_counts.get("lm", 0) < n_lm_total:
            raise SystemExit(
                f"[ERROR] need {n_lm_total} lm rows total, "
                f"pool has only {label_counts.get('lm', 0)}"
            )

    os.makedirs(out_dir, exist_ok=True)

    manifest_rows = []
    used: set = set()

    for spec in sample_specs:
        name = spec["name"]

        used_for_sampling = set() if args.allow_reuse else used
        h_rows, l_rows = sample_rows(
            df,
            spec["n_human"],
            spec["n_lm"],
            used_for_sampling,
            rng,
        )

        if not args.allow_reuse:
            used.update(r["idx"] for r in h_rows)
            used.update(r["idx"] for r in l_rows)

        labeled = (
            [(r, "human") for r in h_rows] +
            [(r, "lm") for r in l_rows]
        )
        rng.shuffle(labeled)

        text, truth = render_sample(labeled)
        py_path, tsv_path = write_sample(out_dir, name, text, truth)

        h_pos = [t["block_idx"] for t in truth if t["label"] == "human"]
        l_pos = [t["block_idx"] for t in truth if t["label"] == "lm"]

        print(
            f"  {name}: {len(truth)} blocks "
            f"(human at {h_pos}, lm at {l_pos}) -> {py_path}"
        )

        manifest_rows.append({
            "name": name,
            "n_blocks": len(truth),
            "n_human": len(h_pos),
            "n_lm": len(l_pos),
            "py_path": py_path,
            "labels_path": tsv_path,
        })

    manifest_path = os.path.join(out_dir, "manifest.csv")
    pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False)

    total_samples = len(manifest_rows)
    total_blocks = sum(r["n_blocks"] for r in manifest_rows)
    total_human = sum(r["n_human"] for r in manifest_rows)
    total_lm = sum(r["n_lm"] for r in manifest_rows)

    print(f"\nManifest -> {manifest_path}")
    print(f"Total samples: {total_samples}")
    print(f"Total blocks : {total_blocks}  (human={total_human}, lm={total_lm})")
    print(f"Unique source idxs used: {len(used)}")

    if args.validate_python:
        bad = 0
        for row in manifest_rows:
            py_path = row["py_path"]
            try:
                import ast
                with open(py_path, "r", encoding="utf8") as f:
                    ast.parse(f.read())
            except Exception:
                print(f"BAD: {py_path}")
                bad += 1

        if bad:
            raise SystemExit(f"[ERROR] {bad} generated file(s) failed Python parsing")
        print("Parse check: OK")

    return {
        "out_dir": out_dir,
        "total_samples": total_samples,
        "total_blocks": total_blocks,
        "total_human": total_human,
        "total_lm": total_lm,
        "unique_source_idxs": len(used),
    }
    
    
# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    args = parse_args()

    if args.grid_out_root:
        configs = parse_grid_configs(args.grid_configs)
        grid_rows = []

        print("============================================================")
        print("Building mixed-sample grid")
        print("============================================================")
        print(f"grid out root : {args.grid_out_root}")
        print(f"grid configs  : {args.grid_configs}")
        print(f"input csv     : {args.input_csv}")
        print()

        for blocks_per_sample, num_samples in configs:
            out_dir = os.path.join(
                args.grid_out_root,
                f"blocks_{blocks_per_sample:02d}",
            )

            print()
            print("------------------------------------------------------------")
            print(f"Grid setting: blocks_per_sample={blocks_per_sample}, num_samples={num_samples}")
            print(f"Output dir  : {out_dir}")
            print("------------------------------------------------------------")

            sample_specs = build_sample_specs(
                num_samples,
                blocks_per_sample,
                args.lm_ratio,
                args.include_corners,
            )

            rng = random.Random(args.seed + blocks_per_sample)
            row = build_one_output_dir(args, out_dir, sample_specs, rng)
            row["blocks_per_sample"] = blocks_per_sample
            row["num_samples"] = num_samples
            grid_rows.append(row)

        summary_path = os.path.join(args.grid_out_root, "grid_manifest.csv")
        os.makedirs(args.grid_out_root, exist_ok=True)
        pd.DataFrame(grid_rows).to_csv(summary_path, index=False)

        print()
        print("============================================================")
        print("Grid build complete")
        print("============================================================")
        print(f"Grid manifest -> {summary_path}")
        return

    rng = random.Random(args.seed)
    sample_specs = build_sample_specs(
        args.num_samples,
        args.blocks_per_sample,
        args.lm_ratio,
        args.include_corners,
    )
    build_one_output_dir(args, args.out_dir, sample_specs, rng)


if __name__ == "__main__":
    main()