#!/usr/bin/env python3
"""
convert_readable_outputs.py
===========================

Convert generated JSONL outputs.txt into a human-readable outputs_v2.txt.

Input JSONL format:
  {"prompt": "...", "output": "...", "solution": "..."}

Example:
  python code-generation/convert_readable_outputs.py \
    --input output/CodeSearchNet/CodeLlama-7b-hf-9000-tp0.2/outputs.txt \
    --output output/CodeSearchNet/CodeLlama-7b-hf-9000-tp0.2/outputs_v2.txt
"""

import argparse
import json
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, help="Input JSONL outputs.txt")
    p.add_argument("--output", default=None, help="Output readable outputs_v2.txt")
    p.add_argument("--limit", type=int, default=None, help="Optional max records to write")
    return p.parse_args()


def main():
    args = parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"[ERROR] input not found: {in_path}")

    out_path = Path(args.output) if args.output else in_path.with_name("outputs_v2.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_read = 0
    n_written = 0
    n_bad = 0

    with in_path.open("r", encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
        for line_no, line in enumerate(fin, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue

            n_read += 1

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                n_bad += 1
                print(f"[WARN] line {line_no}: JSON decode error: {e}")
                continue

            prompt = obj.get("prompt", "")
            output = obj.get("output", "")
            solution = obj.get("solution", "")

            print("-" * 20, file=fout)
            print(f"Index: {n_written}", file=fout)
            print(f"Source line: {line_no}", file=fout)
            print("Prompt:", file=fout)
            print(prompt, file=fout)
            print("-" * 10, file=fout)
            print("Output:", file=fout)
            print(output, file=fout)
            print("-" * 10, file=fout)
            print("Solution:", file=fout)
            print(solution, file=fout)

            n_written += 1

            if args.limit is not None and n_written >= args.limit:
                break

    print("============================================================")
    print("convert_readable_outputs.py")
    print(f"input   : {in_path}")
    print(f"output  : {out_path}")
    print(f"read    : {n_read}")
    print(f"written : {n_written}")
    print(f"bad json: {n_bad}")
    print("============================================================")


if __name__ == "__main__":
    main()
