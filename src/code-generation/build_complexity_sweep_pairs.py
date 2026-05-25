#!/usr/bin/env python3
"""
build_complexity_sweep_pairs.py
===============================

Build cumulative complexity-ordered CodeSearchNet pair datasets.

Input:
  AST CSV produced by run1-ast-generator.sh:
    idx, code, ast, label

Output:
  For each requested pair count N:
    ast_complexity_sweep/<prefix>_merged_NNNN.csv
    validsyntax_complexity_sweep/<prefix>_merged_NNNN.csv

The subsets are cumulative and sorted by pair-level complexity:
  500  = lowest-complexity 500 pairs
  1000 = lowest-complexity 1000 pairs
  ...
  2500 = lowest-complexity 2500 pairs

Complexity score:
  average percentile rank of:
    - max AST token count across the HWC/AGC pair
    - max code-line count across the HWC/AGC pair
    - max Tree-sitter McCabe-style cyclomatic complexity across the pair
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from tree_sitter import Language, Parser


LABEL_HUMAN = "human"
LABEL_LM = "lm"

DECISION_NODE_TYPES = {
    "if_statement",
    "for_statement",
    "while_statement",
    "except_clause",
    "conditional_expression",
    "boolean_operator",
    "match_statement",
    "case_clause",
}


def pair_id_from_idx(idx: object) -> str:
    return re.sub(r"_(human|lm|ai)$", "", str(idx))


def count_code_lines(code: str) -> int:
    return len(str(code).splitlines())


def ast_token_count(ast_text: str) -> int:
    return len(str(ast_text).split())


def load_python_parser(tree_sitter_lib: Path) -> Parser:
    if not tree_sitter_lib.exists():
        raise SystemExit(
            f"[ERROR] tree-sitter library not found: {tree_sitter_lib}\n"
            "Run the tree-sitter build step first."
        )

    lang = Language(str(tree_sitter_lib), "python")
    parser = Parser()
    parser.set_language(lang)
    return parser


def tree_sitter_cyclomatic_complexity(code: str, parser: Parser) -> int:
    """
    McCabe-style complexity from Tree-sitter nodes.

    Starts at 1 and increments for decision/control-flow nodes.
    This is intentionally transparent and language-specific for Python.
    """
    tree = parser.parse(bytes(str(code), "utf8"))
    root = tree.root_node

    complexity = 1
    stack = [root]

    while stack:
        node = stack.pop()

        if node.type in DECISION_NODE_TYPES:
            complexity += 1

        stack.extend(node.children)

    return complexity


def percentile_rank(s: pd.Series) -> pd.Series:
    return s.rank(method="average", pct=True)


def parse_sizes(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def build_pair_table(df: pd.DataFrame, parser: Parser) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"idx", "code", "ast", "label"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] input missing columns: {sorted(missing)}")

    df = df.copy()
    df["idx"] = df["idx"].astype(str)
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    df["_pair_id"] = df["idx"].map(pair_id_from_idx)

    print("Computing row-level complexity metrics...")
    df["_ast_tokens"] = df["ast"].astype(str).map(ast_token_count)
    df["_code_lines"] = df["code"].astype(str).map(count_code_lines)

    cc_values = []
    parse_ok = []
    for code in df["code"].astype(str):
        try:
            cc_values.append(tree_sitter_cyclomatic_complexity(code, parser))
            parse_ok.append(True)
        except Exception:
            cc_values.append(np.nan)
            parse_ok.append(False)

    df["_cc"] = cc_values
    df["_parse_ok"] = parse_ok

    rows = []
    for pair_id, g in df.groupby("_pair_id", sort=True):
        labels = sorted(g["label"].unique().tolist())

        if len(g) != 2 or labels != [LABEL_HUMAN, LABEL_LM]:
            continue

        if not bool(g["_parse_ok"].all()):
            continue

        human = g[g["label"] == LABEL_HUMAN].iloc[0]
        lm = g[g["label"] == LABEL_LM].iloc[0]

        rows.append({
            "pair_id": pair_id,
            "human_idx": human["idx"],
            "lm_idx": lm["idx"],
            "human_ast_tokens": int(human["_ast_tokens"]),
            "lm_ast_tokens": int(lm["_ast_tokens"]),
            "max_ast_tokens": int(g["_ast_tokens"].max()),
            "human_code_lines": int(human["_code_lines"]),
            "lm_code_lines": int(lm["_code_lines"]),
            "max_code_lines": int(g["_code_lines"].max()),
            "human_cc": int(human["_cc"]),
            "lm_cc": int(lm["_cc"]),
            "max_cc": int(g["_cc"].max()),
        })

    pairs = pd.DataFrame(rows)
    if pairs.empty:
        raise SystemExit("[ERROR] no valid pairs found")

    pairs["ast_pct"] = percentile_rank(pairs["max_ast_tokens"])
    pairs["line_pct"] = percentile_rank(pairs["max_code_lines"])
    pairs["cc_pct"] = percentile_rank(pairs["max_cc"])

    pairs["complexity_score"] = (
        pairs["ast_pct"] + pairs["line_pct"] + pairs["cc_pct"]
    ) / 3.0

    pairs = pairs.sort_values(
        ["complexity_score", "max_cc", "max_ast_tokens", "max_code_lines", "pair_id"]
    ).reset_index(drop=True)

    pairs["complexity_rank"] = np.arange(1, len(pairs) + 1)

    return df, pairs


def write_outputs(
    annotated_df: pd.DataFrame,
    pairs: pd.DataFrame,
    sizes: list[int],
    out_ast_dir: Path,
    out_validsyntax_dir: Path,
    prefix: str,
) -> None:
    out_ast_dir.mkdir(parents=True, exist_ok=True)
    out_validsyntax_dir.mkdir(parents=True, exist_ok=True)

    max_size = max(sizes)
    if len(pairs) < max_size:
        raise SystemExit(f"[ERROR] need {max_size} pairs, but only found {len(pairs)}")

    manifest_rows = []

    for n in sizes:
        chosen_ids = set(pairs.head(n)["pair_id"])

        out_df = annotated_df[annotated_df["_pair_id"].isin(chosen_ids)].copy()
        out_df = out_df.sort_values(["_pair_id", "label"]).reset_index(drop=True)

        counts = out_df["label"].value_counts().to_dict()
        expected = {LABEL_HUMAN: n, LABEL_LM: n}
        if counts != expected:
            raise SystemExit(f"[ERROR] label imbalance for {n}: {counts}")

        out_ast = out_ast_dir / f"{prefix}_merged_{n:04d}.csv"
        out_valid = out_validsyntax_dir / f"{prefix}_merged_{n:04d}.csv"

        ast_cols = [c for c in out_df.columns if not c.startswith("_")]
        out_df[ast_cols].to_csv(out_ast, index=False)
        out_df[["idx", "code", "label"]].to_csv(out_valid, index=False)

        sub_pairs = pairs.head(n)
        manifest_rows.append({
            "pair_count": n,
            "rows": len(out_df),
            "mean_complexity_score": sub_pairs["complexity_score"].mean(),
            "max_complexity_score": sub_pairs["complexity_score"].max(),
            "mean_max_ast_tokens": sub_pairs["max_ast_tokens"].mean(),
            "mean_max_code_lines": sub_pairs["max_code_lines"].mean(),
            "mean_max_cc": sub_pairs["max_cc"].mean(),
            "max_ast_tokens": sub_pairs["max_ast_tokens"].max(),
            "max_code_lines": sub_pairs["max_code_lines"].max(),
            "max_cc": sub_pairs["max_cc"].max(),
            "ast_csv": str(out_ast),
            "validsyntax_csv": str(out_valid),
        })

        print(
            f"wrote {n:4d} pairs -> rows={len(out_df):5d} "
            f"max_cc={int(sub_pairs['max_cc'].max()):3d} "
            f"max_ast={int(sub_pairs['max_ast_tokens'].max()):5d} "
            f"max_lines={int(sub_pairs['max_code_lines'].max()):4d}"
        )

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = out_ast_dir / f"{prefix}_complexity_sweep_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    pair_report = out_ast_dir / f"{prefix}_complexity_pair_report.csv"
    pairs.to_csv(pair_report, index=False)

    print()
    print(f"manifest:    {manifest_path}")
    print(f"pair report: {pair_report}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-csv", required=True, type=Path)
    ap.add_argument("--out-ast-dir", required=True, type=Path)
    ap.add_argument("--out-validsyntax-dir", required=True, type=Path)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--sizes", default="500,1000,1500,2000,2500")
    ap.add_argument(
        "--tree-sitter-lib",
        default=Path("code-analyzer-tree-sitter/build/my-languages.so"),
        type=Path,
    )
    args = ap.parse_args()

    sizes = parse_sizes(args.sizes)

    print("Complexity-ordered cumulative pair construction")
    print("=" * 72)
    print(f"input csv       : {args.input_csv}")
    print(f"sizes           : {sizes}")
    print(f"tree-sitter lib : {args.tree_sitter_lib}")
    print(f"out AST dir     : {args.out_ast_dir}")
    print(f"out valid dir   : {args.out_validsyntax_dir}")
    print()

    parser = load_python_parser(args.tree_sitter_lib)

    df = pd.read_csv(args.input_csv)
    annotated_df, pairs = build_pair_table(df, parser)

    print()
    print("Pair complexity summary")
    print("=" * 72)
    print(pairs[["max_ast_tokens", "max_code_lines", "max_cc", "complexity_score"]]
          .describe(percentiles=[.5, .75, .9, .95])
          .to_string())
    print()

    write_outputs(
        annotated_df=annotated_df,
        pairs=pairs,
        sizes=sizes,
        out_ast_dir=args.out_ast_dir,
        out_validsyntax_dir=args.out_validsyntax_dir,
        prefix=args.prefix,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
