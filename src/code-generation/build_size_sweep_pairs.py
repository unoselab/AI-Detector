#!/usr/bin/env python3
"""
Build nested dataset-size sweep CSVs from a cleaned paired validsyntax CSV.

Input:
  idx, code, label

Output:
  One balanced CSV per requested pair count:
    <prefix>_merged_0500.csv
    <prefix>_merged_1000.csv
    ...
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


def pair_id_from_idx(idx: object) -> str:
    return re.sub(r"_(human|lm|ai)$", "", str(idx))


def parse_sizes(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-csv", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--sizes", default="500,1000,1500,2000,2500")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    sizes = parse_sizes(args.sizes)
    max_size = max(sizes)

    df = pd.read_csv(args.input_csv)
    required = {"idx", "code", "label"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] missing columns: {sorted(missing)}")

    df = df.copy()
    df["idx"] = df["idx"].astype(str)
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    df["_pair_id"] = df["idx"].map(pair_id_from_idx)

    pair_ids = []
    bad_pairs = []

    for pid, g in df.groupby("_pair_id", sort=True):
        labels = sorted(g["label"].unique().tolist())
        if len(g) == 2 and labels == ["human", "lm"]:
            pair_ids.append(pid)
        else:
            bad_pairs.append(pid)

    print(f"valid pairs: {len(pair_ids)}")
    print(f"bad pairs skipped: {len(bad_pairs)}")

    if len(pair_ids) < max_size:
        raise SystemExit(f"[ERROR] need {max_size} pairs, found {len(pair_ids)}")

    rng = np.random.default_rng(args.seed)
    ordered = rng.permutation(np.array(pair_ids)).tolist()
    selected_max = ordered[:max_size]

    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    for n in sizes:
        chosen = set(selected_max[:n])
        out = df[df["_pair_id"].isin(chosen)].copy()
        out = out.sort_values(["_pair_id", "label"]).reset_index(drop=True)

        counts = out["label"].value_counts().to_dict()
        expected = {"human": n, "lm": n}
        if counts != expected:
            raise SystemExit(f"[ERROR] unbalanced output for n={n}: {counts}")

        out_path = args.output_dir / f"{args.prefix}_merged_{n:04d}.csv"
        out[["idx", "code", "label"]].to_csv(out_path, index=False)

        print(f"wrote {out_path} rows={len(out)} labels={counts}")
        manifest_rows.append({
            "pair_count": n,
            "rows": len(out),
            "path": str(out_path),
        })

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = args.output_dir / f"{args.prefix}_size_sweep_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    print(f"manifest: {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())