#!/usr/bin/env python3
"""
select_quality400_pairs.py
==========================

Build a quality-controlled 400-pair CodeSearchNet dataset from a larger
cleaned AST CSV, without using classifier predictions or model performance.

Purpose
-------
This script selects pairs by structural/data-quality criteria only:
  * exactly one human row and one LM row per pair;
  * both rows parse as Python;
  * both rows contain exactly one top-level function/class;
  * AST token lengths fit within a chosen embedding max length;
  * rows are not extremely tiny or extremely long;
  * human/LM pair lengths are not wildly imbalanced;
  * final sampling is length-stratified so the 400-pair subset is not only
    short/easy examples.

Input
-----
An AST CSV from ast-generator.py, usually:
  src/code-analyzer-tree-sitter/data_codesearchnet/<MODEL>/ast/
    codesearchnet_<MODEL>_python_merged_2700.csv

Required columns:
  idx, code, ast, label

Output
------
1. AST CSV with selected rows, preserving original columns:
   <out-ast-dir>/<prefix>_merged_quality400.csv

2. Validsyntax-style CSV with only idx,code,label:
   <out-validsyntax-dir>/<prefix>_merged_quality400.csv

3. Manifest with selection metadata per pair:
   <out-ast-dir>/<prefix>_merged_quality400_manifest.csv

Example
-------
From repo src/:

  python ml_embeddings/select_quality400_pairs.py \
    --input-csv code-analyzer-tree-sitter/data_codesearchnet/starcoder2-15b-instruct-v0.1/ast/codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_2700.csv \
    --out-ast-dir code-analyzer-tree-sitter/data_codesearchnet/starcoder2-15b-instruct-v0.1/ast_quality400 \
    --out-validsyntax-dir code-analyzer-tree-sitter/data_codesearchnet/starcoder2-15b-instruct-v0.1/validsyntax_quality400 \
    --prefix codesearchnet_starcoder2-15b-instruct-v0.1_python \
    --n-pairs 400 \
    --max-ast-tokens 2048 \
    --seed 42
"""

from __future__ import annotations

import argparse
import ast as py_ast
import re
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
from transformers import AutoTokenizer


DEFAULT_TOKENIZER = "Salesforce/codet5p-110m-embedding"
LABEL_HUMAN = "human"
LABEL_LM = "lm"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def pair_id_from_idx(idx: object) -> str:
    """Remove the final _human/_lm/_ai label suffix from an idx."""
    return re.sub(r"_(human|lm|ai)$", "", str(idx))


def top_level_block_names(code: str) -> List[str]:
    """Return top-level function/class names in a Python module."""
    tree = py_ast.parse(str(code))
    return [
        node.name
        for node in tree.body
        if isinstance(node, (py_ast.FunctionDef, py_ast.AsyncFunctionDef, py_ast.ClassDef))
    ]


def count_lines(code: str) -> int:
    return len(str(code).splitlines())


def quality_score(row: pd.Series) -> float:
    """
    Lower is better. Used for deterministic ranking inside length strata.

    The score intentionally does NOT use classifier predictions or labels beyond
    pair structure. It favors moderate length, balanced human/LM AST lengths,
    and concise code.
    """
    # Prefer examples near the middle of the allowed AST range, not just the
    # shortest examples. The exact center is empirical and can be overridden by
    # changing filters/strata rather than by model performance.
    target_ast = row.get("target_ast_tokens", 650)
    max_ast = float(row["max_ast_tokens"])
    ratio = float(row["ast_token_ratio"])
    max_lines = float(row["max_code_lines"])

    return (
        abs(max_ast - target_ast) / max(target_ast, 1)
        + 0.50 * abs(ratio - 1.0)
        + 0.01 * max_lines
    )


# -----------------------------------------------------------------------------
# Main selection logic
# -----------------------------------------------------------------------------
def build_pair_table(
    df: pd.DataFrame,
    tokenizer_name: str,
    min_ast_tokens: int,
    max_ast_tokens: int,
    max_code_lines: int,
    max_pair_token_ratio: float,
    require_one_top_level: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (annotated_df, candidate_pairs_df)."""
    required = {"idx", "code", "ast", "label"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] input CSV missing required columns: {sorted(missing)}")

    df = df.copy()
    df["idx"] = df["idx"].astype(str)
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    df["_pair_id"] = df["idx"].map(pair_id_from_idx)

    print(f"Loading tokenizer: {tokenizer_name}")
    tok = AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)

    print("Computing AST token lengths...")
    df["_ast_tokens"] = [
        len(tok(str(x), truncation=False)["input_ids"])
        for x in df["ast"].astype(str)
    ]
    df["_code_lines"] = df["code"].astype(str).map(count_lines)

    print("Checking Python parse + top-level block counts...")
    parse_ok = []
    block_counts = []
    block_names = []
    for code in df["code"].astype(str):
        try:
            names = top_level_block_names(code)
            parse_ok.append(True)
            block_counts.append(len(names))
            block_names.append(";".join(names))
        except Exception:
            parse_ok.append(False)
            block_counts.append(-1)
            block_names.append("")

    df["_parse_ok"] = parse_ok
    df["_top_level_count"] = block_counts
    df["_top_level_names"] = block_names

    rows = []
    for pair_id, g in df.groupby("_pair_id", sort=True):
        labels = sorted(g["label"].unique().tolist())
        if len(g) != 2 or labels != [LABEL_HUMAN, LABEL_LM]:
            continue

        reasons = []
        if not bool(g["_parse_ok"].all()):
            reasons.append("parse_fail")
        if require_one_top_level and not bool((g["_top_level_count"] == 1).all()):
            reasons.append("top_level_count")

        min_tokens = int(g["_ast_tokens"].min())
        max_tokens = int(g["_ast_tokens"].max())
        ratio = max_tokens / max(min_tokens, 1)
        max_lines = int(g["_code_lines"].max())

        if min_tokens < min_ast_tokens:
            reasons.append("too_short_ast")
        if max_tokens > max_ast_tokens:
            reasons.append("too_long_ast")
        if max_lines > max_code_lines:
            reasons.append("too_many_code_lines")
        if ratio > max_pair_token_ratio:
            reasons.append("pair_ast_imbalance")

        human = g[g["label"] == LABEL_HUMAN].iloc[0]
        lm = g[g["label"] == LABEL_LM].iloc[0]

        rows.append(
            {
                "pair_id": pair_id,
                "human_idx": human["idx"],
                "lm_idx": lm["idx"],
                "human_ast_tokens": int(human["_ast_tokens"]),
                "lm_ast_tokens": int(lm["_ast_tokens"]),
                "min_ast_tokens": min_tokens,
                "max_ast_tokens": max_tokens,
                "ast_token_ratio": ratio,
                "human_code_lines": int(human["_code_lines"]),
                "lm_code_lines": int(lm["_code_lines"]),
                "max_code_lines": max_lines,
                "human_top_level_names": human["_top_level_names"],
                "lm_top_level_names": lm["_top_level_names"],
                "eligible": len(reasons) == 0,
                "reject_reasons": ";".join(reasons),
            }
        )

    pairs = pd.DataFrame(rows)
    if pairs.empty:
        raise SystemExit("[ERROR] no pair records found")

    pairs["target_ast_tokens"] = min(650, max_ast_tokens)
    pairs["quality_score"] = pairs.apply(quality_score, axis=1)
    return df, pairs


def stratified_select_pairs(
    candidates: pd.DataFrame,
    n_pairs: int,
    n_bins: int,
    seed: int,
) -> pd.DataFrame:
    """Select n_pairs from candidates, stratified by max_ast_tokens."""
    if len(candidates) < n_pairs:
        raise SystemExit(
            f"[ERROR] only {len(candidates)} eligible pairs, need {n_pairs}. "
            "Relax filters or lower --n-pairs."
        )

    cand = candidates.copy()
    # Sort before qcut for deterministic behavior when ties occur.
    cand = cand.sort_values(["max_ast_tokens", "quality_score", "pair_id"]).reset_index(drop=True)

    # qcut can collapse bins when many examples share the same token length.
    cand["length_bin"] = pd.qcut(
        cand["max_ast_tokens"],
        q=n_bins,
        labels=False,
        duplicates="drop",
    )

    bins = sorted(cand["length_bin"].dropna().unique().tolist())
    rng = np.random.default_rng(seed)

    base = n_pairs // len(bins)
    remainder = n_pairs - base * len(bins)

    chosen_ids: List[str] = []
    for i, b in enumerate(bins):
        sub = cand[cand["length_bin"] == b].copy()
        # Pick best-quality examples inside each length stratum. To avoid a
        # perfectly deterministic top-only sample, shuffle within close score
        # ranks by selecting from the best 2x needed when possible.
        take = base + (1 if i < remainder else 0)
        pool_size = min(len(sub), max(take * 2, take))
        pool = sub.sort_values(["quality_score", "pair_id"]).head(pool_size)
        chosen = rng.choice(pool["pair_id"].to_numpy(), size=take, replace=False)
        chosen_ids.extend(chosen.tolist())

    if len(chosen_ids) < n_pairs:
        remaining = cand[~cand["pair_id"].isin(chosen_ids)].copy()
        top_up = rng.choice(
            remaining["pair_id"].to_numpy(),
            size=n_pairs - len(chosen_ids),
            replace=False,
        )
        chosen_ids.extend(top_up.tolist())

    selected = cand[cand["pair_id"].isin(chosen_ids)].copy()
    selected = selected.sort_values(["length_bin", "quality_score", "pair_id"]).reset_index(drop=True)

    if selected["pair_id"].nunique() != n_pairs:
        raise SystemExit(
            f"[ERROR] selected {selected['pair_id'].nunique()} unique pairs; expected {n_pairs}"
        )

    return selected


def write_outputs(
    annotated_df: pd.DataFrame,
    selected_pairs: pd.DataFrame,
    out_ast_dir: Path,
    out_validsyntax_dir: Path,
    prefix: str,
    dataset_tag: str,
) -> None:
    out_ast_dir.mkdir(parents=True, exist_ok=True)
    out_validsyntax_dir.mkdir(parents=True, exist_ok=True)

    out_ast = out_ast_dir / f"{prefix}_merged_{dataset_tag}.csv"
    out_valid = out_validsyntax_dir / f"{prefix}_merged_{dataset_tag}.csv"
    out_manifest = out_ast_dir / f"{prefix}_merged_{dataset_tag}_manifest.csv"

    selected_ids = set(selected_pairs["pair_id"])
    out_df = annotated_df[annotated_df["_pair_id"].isin(selected_ids)].copy()
    out_df = out_df.sort_values(["_pair_id", "label"]).reset_index(drop=True)

    # Final sanity checks.
    if len(out_df) != 2 * len(selected_ids):
        raise SystemExit("[ERROR] selected row count does not equal 2 * selected pair count")
    if out_df["label"].value_counts().to_dict() != {LABEL_HUMAN: len(selected_ids), LABEL_LM: len(selected_ids)}:
        raise SystemExit("[ERROR] selected labels are not balanced")

    ast_cols = [c for c in out_df.columns if not c.startswith("_")]
    out_df[ast_cols].to_csv(out_ast, index=False)
    out_df[["idx", "code", "label"]].to_csv(out_valid, index=False)
    selected_pairs.to_csv(out_manifest, index=False)

    print("\nSelected dataset summary")
    print("=" * 72)
    print(f"pairs:            {len(selected_ids)}")
    print(f"rows:             {len(out_df)}")
    print(f"labels:           {out_df['label'].value_counts().to_dict()}")
    print(f"max AST tokens:   {int(out_df['_ast_tokens'].max())}")
    print(f"over 512:         {int((out_df['_ast_tokens'] > 512).sum())} / {len(out_df)}")
    print(f"over 1024:        {int((out_df['_ast_tokens'] > 1024).sum())} / {len(out_df)}")
    print(f"over 2048:        {int((out_df['_ast_tokens'] > 2048).sum())} / {len(out_df)}")

    print("\nWrote")
    print("=" * 72)
    print(f"AST CSV:          {out_ast}")
    print(f"validsyntax CSV:  {out_valid}")
    print(f"manifest:         {out_manifest}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Select a quality-controlled 400-pair dataset from cleaned AST CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input-csv", required=True, type=Path)
    p.add_argument("--out-ast-dir", required=True, type=Path)
    p.add_argument("--out-validsyntax-dir", required=True, type=Path)
    p.add_argument("--prefix", required=True)
    p.add_argument("--n-pairs", type=int, default=400)
    p.add_argument(
        "--dataset-tag",
        default=None,
        help="Output dataset suffix after '_merged_'. Defaults to quality<N>, e.g. quality400.",
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--tokenizer", default=DEFAULT_TOKENIZER)
    p.add_argument("--min-ast-tokens", type=int, default=80)
    p.add_argument("--max-ast-tokens", type=int, default=2048)
    p.add_argument("--max-code-lines", type=int, default=120)
    p.add_argument("--max-pair-token-ratio", type=float, default=2.5)
    p.add_argument("--length-bins", type=int, default=4)
    p.add_argument(
        "--allow-multiple-top-level",
        action="store_true",
        help="Disable the exactly-one-top-level-block requirement. Not recommended.",
    )
    p.add_argument(
        "--write-candidate-report",
        action="store_true",
        help="Also write eligible/rejected pair report next to the manifest.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input_csv.exists():
        raise SystemExit(f"[ERROR] input not found: {args.input_csv}")

    print("Quality-controlled pair selection")
    print("=" * 72)
    print(f"input:                 {args.input_csv}")
    print(f"n_pairs:               {args.n_pairs}")
    print(f"seed:                  {args.seed}")
    print(f"max_ast_tokens:        {args.max_ast_tokens}")
    print(f"min_ast_tokens:        {args.min_ast_tokens}")
    print(f"max_code_lines:        {args.max_code_lines}")
    print(f"max_pair_token_ratio:  {args.max_pair_token_ratio}")
    print(f"require_one_top_level: {not args.allow_multiple_top_level}")
    print()

    df = pd.read_csv(args.input_csv)
    annotated_df, pairs = build_pair_table(
        df=df,
        tokenizer_name=args.tokenizer,
        min_ast_tokens=args.min_ast_tokens,
        max_ast_tokens=args.max_ast_tokens,
        max_code_lines=args.max_code_lines,
        max_pair_token_ratio=args.max_pair_token_ratio,
        require_one_top_level=not args.allow_multiple_top_level,
    )

    eligible = pairs[pairs["eligible"]].copy()
    rejected = pairs[~pairs["eligible"]].copy()

    print("\nCandidate summary")
    print("=" * 72)
    print(f"all pairs:       {len(pairs)}")
    print(f"eligible pairs:  {len(eligible)}")
    print(f"rejected pairs:  {len(rejected)}")
    if len(rejected):
        print("\nTop rejection reasons:")
        print(rejected["reject_reasons"].value_counts().head(20).to_string())

    selected = stratified_select_pairs(
        candidates=eligible,
        n_pairs=args.n_pairs,
        n_bins=args.length_bins,
        seed=args.seed,
    )
    dataset_tag = args.dataset_tag or f"quality{args.n_pairs}"
    
    write_outputs(
        annotated_df=annotated_df,
        selected_pairs=selected,
        out_ast_dir=args.out_ast_dir,
        out_validsyntax_dir=args.out_validsyntax_dir,
        prefix=args.prefix,
        dataset_tag=dataset_tag,
    )

    if args.write_candidate_report:
        report = args.out_ast_dir / f"{args.prefix}_merged_{dataset_tag}_candidate_report.csv"
        pairs.to_csv(report, index=False)
        print(f"candidate report: {report}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
