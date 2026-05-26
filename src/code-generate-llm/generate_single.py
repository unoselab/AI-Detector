#!/usr/bin/env python3
"""
generate_one_mgc_openai_compat.py
=================================

Generate one machine-generated code (MGC) sample with an OpenAI-compatible
chat-completions endpoint, using the AI-Detector/ICSE-2025-style data shape.

Outputs:
  1. JSONL record with fields: prompt, output, solution, raw_response
  2. CSV rows in AI-Detector raw format: idx,code,label
     - <sample_id>_lm is always written
     - <sample_id>_human is written only when --human-solution is provided

Example:
  OPENAI_API_KEY=... python generate_one_mgc_openai_compat.py \
    --spec "How do I check if a Python object is an instance of a class?" \
    --signature "def is_instance_of_class(obj, cls):" \
    --sample-id isinstance_demo \
    --temperature 0
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests

DEFAULT_API_URL = "https://ellm.nrp-nautilus.io/v1/chat/completions"
DEFAULT_MODEL = "gpt-oss"

CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)


def strip_code_fences(text: str) -> str:
    match = CODE_FENCE_RE.search(text or "")
    return match.group(1) if match else (text or "")


def trim_overgeneration(code: str) -> str:
    """Keep one Python snippet and remove common chat-model tails."""
    code = strip_code_fences(code)
    code = code.split("###", 1)[0]
    code = code.split("<file_sep>", 1)[0]
    code = code.strip()

    # If the model adds prose before the function/class, start at the first code block.
    first_code = re.search(r"(?m)^(?:from\s+\S+\s+import\s+|import\s+|async\s+def\s+|def\s+|class\s+)", code)
    if first_code:
        code = code[first_code.start():]

    # Stop before a second top-level function/class if the answer over-generates.
    starts = list(re.finditer(r"(?m)^(?:async\s+def\s+|def\s+|class\s+)", code))
    if len(starts) > 1:
        code = code[:starts[1].start()].rstrip()

    return code.rstrip() + "\n"


def syntax_error(code: str) -> Optional[str]:
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return f"{exc.msg} at line {exc.lineno}, column {exc.offset}"


def build_prompt(spec: str, signature: Optional[str]) -> str:
    if signature:
        return (
            f"{signature}\n"
            f"    \"\"\"{spec.strip()}\"\"\"\n"
        )
    return spec.strip()


def build_messages(spec: str, signature: Optional[str]) -> list[Dict[str, str]]:
    if signature:
        user_content = (
            "Implement the following Python function. Match the signature and "
            "docstring exactly. Return only Python source code; do not include "
            "Markdown fences, explanations, tests, or examples.\n\n"
            f"{build_prompt(spec, signature)}"
        )
    else:
        user_content = (
            "Write a Python function for the following programming task. Return only "
            "Python source code; do not include Markdown fences, explanations, tests, "
            "or examples.\n\n"
            f"Task: {spec.strip()}"
        )

    return [
        {
            "role": "system",
            "content": (
                "You generate compact, correct Python source code only. "
                "Never answer in a persona and never include prose."
            ),
        },
        {"role": "user", "content": user_content},
    ]


def request_completion(args: argparse.Namespace) -> Dict[str, Any]:
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"[ERROR] missing API key env var: {args.api_key_env}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/7.81.0",
    }
    payload = {
        "model": args.model,
        "messages": build_messages(args.spec, args.signature),
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.top_p is not None:
        payload["top_p"] = args.top_p

    response = requests.post(args.api_url, json=payload, headers=headers, timeout=args.timeout)
    response.raise_for_status()
    return response.json()


def extract_content(response_json: Dict[str, Any]) -> str:
    try:
        return response_json["choices"][0]["message"]["content"]
    except Exception as exc:
        raise SystemExit(f"[ERROR] unexpected response shape: {exc}\n{json.dumps(response_json, indent=2)}")


def write_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, sample_id: str, prompt: str, mgc_code: str, human_solution: Optional[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["idx", "code", "label"])
        writer.writeheader()
        if human_solution:
            writer.writerow({
                "idx": f"{sample_id}_human",
                "code": prompt + human_solution.rstrip() + "\n" if prompt.lstrip().startswith(("def ", "async def ")) else human_solution.rstrip() + "\n",
                "label": "human",
            })
        writer.writerow({"idx": f"{sample_id}_lm", "code": mgc_code, "label": "lm"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", required=True, help="Natural-language programming specification.")
    parser.add_argument("--signature", default="def is_instance_of_class(obj, cls):",
                        help="Optional Python function signature to preserve.")
    parser.add_argument("--human-solution", default=None,
                        help="Optional human-written body/code, for paired HWC/MGC CSV output.")
    parser.add_argument("--sample-id", default="single_mgc_001")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Use 0.0 for deterministic ICSE-style temperature=0 generation; also run default-temperature variants separately if needed.")
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--out-jsonl", default="single_mgc_outputs.jsonl")
    parser.add_argument("--out-csv", default="single_mgc_merged.csv")
    parser.add_argument("--allow-syntax-error", action="store_true",
                        help="Write outputs even if Python syntax validation fails.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompt = build_prompt(args.spec, args.signature)

    print(f"Sending one MGC request to {args.api_url} with model={args.model} ...", file=sys.stderr)
    response_json = request_completion(args)
    raw_content = extract_content(response_json)
    mgc_code = trim_overgeneration(raw_content)

    err = syntax_error(mgc_code)
    if err and not args.allow_syntax_error:
        raise SystemExit(
            "[ERROR] generated MGC has invalid Python syntax; not writing reportable outputs.\n"
            f"Reason: {err}\n"
            "Re-run with --allow-syntax-error only for debugging.\n\n"
            f"Generated code:\n{mgc_code}"
        )

    record = {
        "sample_id": args.sample_id,
        "prompt": prompt,
        "output": mgc_code if args.signature else mgc_code,
        "solution": args.human_solution or "",
        "raw_response": raw_content,
        "syntax_ok": err is None,
        "syntax_error": err or "",
        "model": args.model,
        "temperature": args.temperature,
    }

    write_jsonl(Path(args.out_jsonl), record)
    write_csv(Path(args.out_csv), args.sample_id, prompt, mgc_code, args.human_solution)

    print(f"Wrote JSONL: {args.out_jsonl}")
    print(f"Wrote CSV:   {args.out_csv}")
    print("\nGenerated MGC:\n")
    print(mgc_code)


if __name__ == "__main__":
    main()
