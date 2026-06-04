#!/usr/bin/env python3
import ast
import argparse
import textwrap
from pathlib import Path
from collections import Counter

import pandas as pd


DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def is_docstring_stmt(stmt):
    """Return True if stmt is a Python docstring expression."""
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def is_docstring_only_def(node):
    """
    Return True if a function/class body contains only a docstring.

    Example counted:
        def f():
            '''docstring'''

    Example not counted:
        def f():
            '''docstring'''
            return x
    """
    if not isinstance(node, DEF_NODES):
        return False

    body = node.body

    if not body:
        return False

    if not is_docstring_stmt(body[0]):
        return False

    return len(body) == 1


def find_docstring_only_defs(code):
    """
    Parse a code snippet and return top-level definitions whose body
    contains only a docstring.
    """
    code = textwrap.dedent(str(code)).strip() + "\n"

    tree = ast.parse(code)

    empty_defs = []

    for node in tree.body:
        if is_docstring_only_def(node):
            empty_defs.append(node)

    return empty_defs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_path",
        help="Path to the merged CSV file",
    )
    parser.add_argument(
        "--show",
        type=int,
        default=20,
        help="Number of matching rows to print",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path, usecols=["idx", "code", "label"])

    results = []
    parse_errors = []

    for row_num, row in df.iterrows():
        idx = row["idx"]
        label = row["label"]
        code = row["code"]

        try:
            empty_defs = find_docstring_only_defs(code)
        except SyntaxError as e:
            parse_errors.append(
                {
                    "row_num": row_num,
                    "idx": idx,
                    "label": label,
                    "error": str(e),
                }
            )
            continue

        if empty_defs:
            for node in empty_defs:
                doc = ast.get_docstring(node) or ""
                results.append(
                    {
                        "row_num": row_num,
                        "idx": idx,
                        "label": label,
                        "def_type": type(node).__name__,
                        "def_name": getattr(node, "name", "<unknown>"),
                        "doc_preview": doc.replace("\n", " ")[:80],
                    }
                )

    result_df = pd.DataFrame(results)

    print("=== Empty-body-with-only-docstring check ===")
    print(f"CSV file: {csv_path}")
    print(f"Total rows: {len(df)}")
    print(f"Rows with docstring-only body: {len(result_df)}")

    if len(result_df) > 0:
        print("\n=== Count by label ===")
        print(result_df["label"].value_counts().to_string())

        print("\n=== Count by idx suffix ===")
        suffix_counts = Counter(
            "human" if str(idx).endswith("_human") else "lm" if str(idx).endswith("_lm") else "unknown"
            for idx in result_df["idx"]
        )
        for suffix, count in suffix_counts.items():
            print(f"{suffix}: {count}")

        print(f"\n=== First {args.show} matching rows ===")
        print(result_df.head(args.show).to_string(index=False))

    if parse_errors:
        print("\n=== Syntax parse errors ===")
        print(f"Parse error rows: {len(parse_errors)}")
        print(pd.DataFrame(parse_errors).head(args.show).to_string(index=False))


if __name__ == "__main__":
    main()