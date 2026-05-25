#!/usr/bin/env python3
"""
build_complexity_sweep_pairs.py
===============================

Build cumulative complexity-ordered CodeSearchNet pair datasets from the
cleaned validsyntax CSV.

Input:
  validsyntax CSV produced by run0b-find-validsyntax-mgc.sh:
    idx, code, label

Output:
  validsyntax_complexity_sweep/<prefix>_merged_0500.csv
  validsyntax_complexity_sweep/<prefix>_merged_1000.csv
  ...
  validsyntax_complexity_sweep/<prefix>_complexity_sweep_manifest.csv
  validsyntax_complexity_sweep/<prefix>_complexity_sweep_candidate_report.csv

The subsets are cumulative and sorted by pair-level complexity:
  500  = lowest-complexity 500 pairs
  1000 = lowest-complexity 1000 pairs
  ...
  2500 = lowest-complexity 2500 pairs

Complexity score:
  average percentile rank of:
    - max Tree-sitter AST sequence token count across the HWC/AGC pair
    - max code-line count across the HWC/AGC pair
    - max McCabe-style cyclomatic complexity across the pair
"""

from __future__ import annotations

import argparse
import os
import re
import sys
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


def parse_sizes(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def percentile_rank(s: pd.Series) -> pd.Series:
    return s.rank(method="average", pct=True)


def load_parser_and_ast_fn(tree_sitter_lib: Path, ast_helper_dir: Path):
    if not tree_sitter_lib.exists():
        raise SystemExit(
            f"[ERROR] tree-sitter library not found: {tree_sitter_lib}\n"
            "Run the tree-sitter build step first."
        )

    lang = Language(str(tree_sitter_lib), "python")
    parser = Parser()
    parser.set_language(lang)

    helper_dir_abs = os.path.abspath(ast_helper_dir)
    if helper_dir_abs not in sys.path:
        sys.path.insert(0, helper_dir_abs)

    from tree_sitter_ast_python import F  # noqa: E402

    return parser, F


def tree_sitter_ast_token_count(code: str, parser: Parser, ast_fn) -> int:
    code_bytes = bytes(str(code), "utf8")
    tree = parser.parse(code_bytes)
    return len(ast_fn(tree.root_node, code_bytes))


def tree_sitter_cyclomatic_complexity(code: str, parser: Parser) -> int:
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


def build_pair_table(df: pd.DataFrame, parser: Parser, ast_fn) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"idx", "code", "label"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"[ERROR] input missing columns: {sorted(missing)}")

    df = df.copy()
    df["idx"] = df["idx"].astype(str)
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    df["_pair_id"] = df["idx"].map(pair_id_from_idx)

    print("Computing row-level complexity metrics...")
    ast_tokens = []
    code_lines = []
    cc_values = []
    parse_ok = []

    for code in df["code"].astype(str):
        try:
            ast_tokens.append(tree_sitter_ast_token_count(code, parser, ast_fn))
            code_lines.append(count_code_lines(code))
            cc_values.append(tree_sitter_cyclomatic_complexity(code, parser))
            parse_ok.append(True)
        except Exception:
            ast_tokens.append(np.nan)
            code_lines.append(count_code_lines(code))
            cc_values.append(np.nan)
            parse_ok.append(False)

    df["_ast_tokens"] = ast_tokens
    df["_code_lines"] = code_lines
    df["_cc"] = cc_values
    df["_parse_ok"] = parse_ok

    rows = []
    for pair_id, g in df.groupby("_pair_id", sort=True):
        labels = sorted(g["label"].unique().tolist())

        reasons = []
        if len(g) != 2 or labels != [LABEL_HUMAN, LABEL_LM]:
            reasons.append("invalid_pair_structure")
        if len(g) == 2 and not bool(g["_parse_ok"].all()):
            reasons.append("tree_sitter_parse_fail")

        row = {
            "pair_id": pair_id,
            "eligible": len(reasons) == 0,
            "reject_reasons": ";".join(reasons),
        }

        if len(g) == 2 and labels == [LABEL_HUMAN, LABEL_LM]:
            human = g[g["label"] == LABEL_HUMAN].iloc[0]
            lm = g[g["label"] == LABEL_LM].iloc[0]

            row.update({
                "human_idx": human["idx"],
                "lm_idx": lm["idx"],
                "human_ast_tokens": human["_ast_tokens"],
                "lm_ast_tokens": lm["_ast_tokens"],
                "max_ast_tokens": g["_ast_tokens"].max(),
                "human_code_lines": human["_code_lines"],
                "lm_code_lines": lm["_code_lines"],
                "max_code_lines": g["_code_lines"].max(),
                "human_cc": human["_cc"],
                "lm_cc": lm["_cc"],
                "max_cc": g["_cc"].max(),
            })
        else:
            row.update({
                "human_idx": "",
                "lm_idx": "",
                "human_ast_tokens": np.nan,
                "lm_ast_tokens": np.nan,
                "max_ast_tokens": np.nan,
                "human_code_lines": np.nan,
                "lm_code_lines": np.nan,
                "max_code_lines": np.nan,
                "human_cc": np.nan,
                "lm_cc": np.nan,
                "max_cc": np.nan,
            })

        rows.append(row)

    pairs = pd.DataFrame(rows)
    if pairs.empty:
        raise SystemExit("[ERROR] no pair records found")

    eligible = pairs[pairs["eligible"]].copy()
    if eligible.empty:
        raise SystemExit("[ERROR] no eligible pairs found")

    eligible["ast_pct"] = percentile_rank(eligible["max_ast_tokens"])
    eligible["line_pct"] = percentile_rank(eligible["max_code_lines"])
    eligible["cc_pct"] = percentile_rank(eligible["max_cc"])

    eligible["complexity_score"] = (
        eligible["ast_pct"] + eligible["line_pct"] + eligible["cc_pct"]
    ) / 3.0

    pairs = pairs.merge(
        eligible[["pair_id", "ast_pct", "line_pct", "cc_pct", "complexity_score"]],
        on="pair_id",
        how="left",
    )

    eligible = eligible.sort_values(
        ["complexity_score", "max_cc", "max_ast_tokens", "max_code_lines", "pair_id"]
    ).reset_index(drop=True)

    eligible["complexity_rank"] = np.arange(1, len(eligible) + 1)

    pairs = pairs.merge(
        eligible[["pair_id", "complexity_rank"]],
        on="pair_id",
        how="left",
    )

    return df, pairs


def write_outputs(
    annotated_df: pd.DataFrame,
    pairs: pd.DataFrame,
    sizes: list[int],
    out_dir: Path,
    prefix: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    eligible = pairs[pairs["eligible"]].copy()
    eligible = eligible.sort_values(
        ["complexity_score", "max_cc", "max_ast_tokens", "max_code_lines", "pair_id"]
    ).reset_index(drop=True)

    max_size = max(sizes)
    if len(eligible) < max_size:
        raise SystemExit(f"[ERROR] need {max_size} eligible pairs, found {len(eligible)}")

    manifest_rows = []

    for n in sizes:
        chosen_ids = set(eligible.head(n)["pair_id"])

        out_df = annotated_df[annotated_df["_pair_id"].isin(chosen_ids)].copy()
        out_df = out_df.sort_values(["_pair_id", "label"]).reset_index(drop=True)

        counts = out_df["label"].value_counts().to_dict()
        expected = {LABEL_HUMAN: n, LABEL_LM: n}
        if counts != expected:
            raise SystemExit(f"[ERROR] label imbalance for {n}: {counts}")

        out_csv = out_dir / f"{prefix}_merged_{n:04d}.csv"
        out_df[["idx", "code", "label"]].to_csv(out_csv, index=False)

        sub_pairs = eligible.head(n)
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
            "validsyntax_csv": str(out_csv),
        })

        print(
            f"wrote {n:4d} pairs -> rows={len(out_df):5d} "
            f"mean_score={sub_pairs['complexity_score'].mean():.4f} "
            f"max_score={sub_pairs['complexity_score'].max():.4f} "
            f"max_cc={int(sub_pairs['max_cc'].max()):3d} "
            f"max_ast={int(sub_pairs['max_ast_tokens'].max()):5d} "
            f"max_lines={int(sub_pairs['max_code_lines'].max()):4d}"
        )

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = out_dir / f"{prefix}_complexity_sweep_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    report_path = out_dir / f"{prefix}_complexity_sweep_candidate_report.csv"
    pairs.to_csv(report_path, index=False)

    print()
    print(f"manifest:        {manifest_path}")
    print(f"candidate report:{report_path}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build cumulative complexity-ordered validsyntax pair datasets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--input-csv", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--sizes", default="500,1000,1500,2000,2500")
    ap.add_argument("--tree-sitter-lib", default=Path("code-analyzer-tree-sitter/build/my-languages.so"), type=Path)
    ap.add_argument("--ast-helper-dir", default=Path("code-analyzer-tree-sitter"), type=Path)
    args = ap.parse_args()

    sizes = parse_sizes(args.sizes)

    print("Complexity-ordered cumulative pair construction")
    print("=" * 72)
    print(f"input csv       : {args.input_csv}")
    print(f"sizes           : {sizes}")
    print(f"tree-sitter lib : {args.tree_sitter_lib}")
    print(f"ast helper dir  : {args.ast_helper_dir}")
    print(f"out dir         : {args.out_dir}")
    print()

    parser, ast_fn = load_parser_and_ast_fn(args.tree_sitter_lib, args.ast_helper_dir)

    df = pd.read_csv(args.input_csv)
    annotated_df, pairs = build_pair_table(df, parser, ast_fn)

    eligible = pairs[pairs["eligible"]].copy()
    rejected = pairs[~pairs["eligible"]].copy()

    print()
    print("Candidate summary")
    print("=" * 72)
    print(f"all pairs:       {len(pairs)}")
    print(f"eligible pairs:  {len(eligible)}")
    print(f"rejected pairs:  {len(rejected)}")
    if len(rejected):
        print()
        print("Top rejection reasons:")
        print(rejected["reject_reasons"].value_counts().head(20).to_string())

    print()
    print("Eligible pair complexity summary")
    print("=" * 72)
    print(
        eligible[["max_ast_tokens", "max_code_lines", "max_cc", "complexity_score"]]
        .describe(percentiles=[.5, .75, .9, .95])
        .to_string()
    )
    print()

    write_outputs(
        annotated_df=annotated_df,
        pairs=pairs,
        sizes=sizes,
        out_dir=args.out_dir,
        prefix=args.prefix,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
