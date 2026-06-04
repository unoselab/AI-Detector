#!/usr/bin/env python3
"""
generate-more.py
================

Generate additional valid MGC samples for an existing AI-Detector CSV.

Main behavior:
  1. Read an existing CSV with rows:
       idx,code,label
       lineX_human,<human code>,human
       lineX_lm,<model code>,lm

  2. Count existing pairs.

  3. Scan CodeSearchNet train.jsonl in continuous order.

  4. Skip any HWC code already present in the existing CSV, so we do not
     generate another MGC for the same human-written code.

  5. Generate MGC using an OpenAI-compatible /v1/chat/completions endpoint.

  6. Keep only pairs where:
       - HWC parses as valid Python,
       - MGC parses as valid Python,
       - both have exactly one top-level function/class block,
       - body is not empty/docstring-only.

  7. Backup the existing validsyntax directory:
       validsyntax-bak-TIMESTAMP

  8. Write the expanded CSV into:
       src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax

Example:
  cd ~/project-workspace/ai_detector

  OPENAI_API_KEY=... python src/code-generate-llm/generate-more.py \\
    src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax/codesearchnet_gpt-oss_python_merged_4500.csv \\
    4500 \\
    --codesearchnet-root data/CodeSearchNet \\
    --model-name gpt-oss \\
    --retry-forever
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import sys
import textwrap
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests


DEFAULT_API_URL = "https://ellm.nrp-nautilus.io/v1/chat/completions"
DEFAULT_MODEL = "gpt-oss"
DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"

DEFAULT_OUT_DIR = Path(
    "src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax"
)

CODE_FENCE_RE = re.compile(
    r"```(?:python|py)?\s*\n?(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class SyntaxResult:
    ok: bool
    error: str = ""


@dataclass
class CandidateResult:
    ok: bool
    error: str
    status: str
    hwc_code: str
    mgc_code: str
    selected_output: str


def normalize_newlines(s: Any) -> str:
    return str(s or "").replace("\r\n", "\n").replace("\r", "\n")


def stable_hash(text: str) -> str:
    normalized = normalize_newlines(text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def split_prompt_body(original_string: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (signature/docstring prompt, human body) from a CodeSearchNet row.

    This follows the same basic format as the previous generator:
      prompt   = function signature + docstring
      solution = body after the docstring
    """
    s = str(original_string or "").replace("'''", '"""')
    parts = s.split('"""')

    if len(parts) < 3:
        return None, None

    prompt = parts[0] + '"""' + parts[1] + '"""'
    body = '"""'.join(parts[2:])
    return prompt, body


def compose_code(prompt: str, continuation: str) -> str:
    return textwrap.dedent(
        normalize_newlines(prompt) + normalize_newlines(continuation)
    ).strip() + "\n"


def syntax_check(code: str) -> SyntaxResult:
    try:
        ast.parse(code)
        return SyntaxResult(True, "")
    except SyntaxError as e:
        return SyntaxResult(False, f"{e.msg} at line {e.lineno}")
    except Exception as e:
        return SyntaxResult(False, f"{type(e).__name__}: {e}")


def top_level_blocks(code: str) -> List[ast.AST]:
    tree = ast.parse(code)
    return [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def has_exactly_one_top_level_block(code: str) -> bool:
    return len(top_level_blocks(code)) == 1


def is_docstring_stmt(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def has_non_empty_body_after_docstring(code: str, allow_pass: bool = False) -> bool:
    """
    Return True only if the single top-level function/class has real body
    statements after removing the leading docstring.

    If allow_pass=False, a body containing only `pass` is treated as empty.
    """
    blocks = top_level_blocks(code)

    if len(blocks) != 1:
        return False

    body = list(getattr(blocks[0], "body", []))

    if body and is_docstring_stmt(body[0]):
        body = body[1:]

    if not allow_pass:
        body = [stmt for stmt in body if not isinstance(stmt, ast.Pass)]

    return len(body) > 0


def _indent_width(line: str) -> int:
    line = line.expandtabs(4)
    return len(line) - len(line.lstrip(" "))


def _expected_body_indent(prompt: str) -> int:
    lines = normalize_newlines(prompt).splitlines()
    nonempty = [line for line in lines if line.strip()]

    if not nonempty:
        return 4

    last = nonempty[-1]
    last_indent = _indent_width(last)

    if last.rstrip().endswith(":"):
        return last_indent + 4

    return last_indent


def prompt_function_name(prompt: str) -> Optional[str]:
    code = textwrap.dedent(normalize_newlines(prompt))

    m = re.search(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", code, re.MULTILINE)
    if m:
        return m.group(1)

    m = re.search(r"^\s*class\s+([A-Za-z_]\w*)\s*[:(]", code, re.MULTILINE)
    if m:
        return m.group(1)

    return None


def strip_repeated_outer_signature(prompt: str, output: str) -> str:
    expected_name = prompt_function_name(prompt)

    if not expected_name:
        return output

    lines = normalize_newlines(output).splitlines()
    first = next((i for i, line in enumerate(lines) if line.strip()), None)

    if first is None:
        return "\n"

    first_text = lines[first].strip()

    repeated_def = re.match(
        rf"^(?:async\s+)?def\s+{re.escape(expected_name)}\s*\(.*\)\s*(?:->\s*[^:]+)?\s*:\s*$",
        first_text,
    )
    repeated_class = re.match(
        rf"^class\s+{re.escape(expected_name)}\s*[:(]",
        first_text,
    )

    if repeated_def or repeated_class:
        rest = "\n".join(lines[first + 1:]).lstrip("\n")
        return "\n" + rest if rest.strip() else "\n"

    return output


def _strip_repeated_signature_tail(output: str) -> str:
    lines = normalize_newlines(output).splitlines()

    first = None
    for i, line in enumerate(lines):
        if line.strip():
            first = i
            break

    if first is None:
        return "\n"

    first_text = lines[first].strip()

    signature_like = (
        first_text.endswith(",")
        or first_text.startswith(")")
        or "->" in first_text
    )

    if not signature_like:
        return output

    limit = min(len(lines), first + 30)

    for j in range(first, limit):
        text = lines[j].strip()
        if text.endswith(":") and (text.startswith(")") or "->" in text or j > first):
            rest = "\n".join(lines[j + 1:]).lstrip("\n")
            return "\n" + rest if rest else "\n"

    return output


def _normalize_continuation_indent(prompt: str, output: str) -> str:
    expected = _expected_body_indent(prompt)
    lines = normalize_newlines(output).splitlines()

    nonempty_indices = [i for i, line in enumerate(lines) if line.strip()]
    if not nonempty_indices:
        return "\n"

    current_min = min(_indent_width(lines[i]) for i in nonempty_indices)

    if expected > current_min:
        delta = expected - current_min
        lines = [
            (" " * delta + line if line.strip() else line)
            for line in lines
        ]

    result = "\n".join(lines).rstrip()

    if result and not result.startswith("\n"):
        result = "\n" + result

    return result + "\n"


def clean_output(prompt: str, output: str) -> str:
    s = normalize_newlines(output)

    s = s.split("<file_sep>", 1)[0]
    s = s.split("```", 1)[0]

    patterns = [
        r"\n\n(?=def\s+\w+\s*\()",
        r"\n\n(?=async\s+def\s+\w+\s*\()",
        r"\n\n(?=class\s+\w+)",
        r"\n\s{4}def\s*$",
        r"\n\s{4}async\s+def\s*$",
        r"\n\s{4}class\s*$",
        r"\n\s*def\s*$",
        r"\n\s*async\s+def\s*$",
        r"\n\s*class\s*$",
    ]

    cut = len(s)
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            cut = min(cut, m.start())

    s = s[:cut].rstrip() + "\n"
    s = strip_repeated_outer_signature(prompt, s)
    s = _strip_repeated_signature_tail(s)
    s = _normalize_continuation_indent(prompt, s)
    return s


def strip_code_fences(text: str) -> str:
    m = CODE_FENCE_RE.search(text or "")
    return m.group(1) if m else (text or "")


def body_indent_from_prompt(prompt: str) -> str:
    triple_double = chr(34) * 3
    triple_single = chr(39) * 3

    lines = [ln for ln in prompt.splitlines() if ln.strip()]

    for ln in reversed(lines):
        if triple_double in ln or triple_single in ln:
            indent = re.match(r"^(\s*)", ln).group(1)
            return indent if indent else "    "

    return "    "


def as_current_continuation(text: str) -> str:
    text = text.rstrip()

    if not text:
        return "\n"

    if not text.startswith("\n"):
        text = "\n" + text

    return text + "\n"


def shift_spurious_mixed_indent(text: str) -> str:
    lines = text.strip("\n").splitlines()
    indents = []

    for ln in lines:
        if not ln.strip():
            continue
        stripped = ln.lstrip(" \t")
        indents.append(len(ln) - len(stripped))

    if 0 in indents and any(i >= 4 for i in indents):
        fixed = []
        for ln in lines:
            if ln.startswith("    "):
                fixed.append(ln[4:])
            elif ln.startswith("\t"):
                fixed.append(ln[1:])
            else:
                fixed.append(ln)
        return "\n".join(fixed)

    return text


def reindent_as_function_body(text: str, prompt: str) -> str:
    indent = body_indent_from_prompt(prompt)
    logical = textwrap.dedent(text.strip("\n"))
    lines = logical.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)

    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return "\n"

    out = []
    for ln in lines:
        out.append(indent + ln.rstrip() if ln.strip() else "")

    return "\n" + "\n".join(out).rstrip() + "\n"


def combined_is_valid(prompt: str, body: str) -> bool:
    try:
        ast.parse(prompt.rstrip() + body)
        return True
    except SyntaxError:
        return False


def choose_best_body(text: str, prompt: str) -> str:
    bases = [
        text,
        textwrap.dedent(text),
        shift_spurious_mixed_indent(text),
        textwrap.dedent(shift_spurious_mixed_indent(text)),
    ]

    candidates = [as_current_continuation(text)]

    for base in bases:
        candidates.append(reindent_as_function_body(base, prompt))

    seen = set()
    unique = []

    for cand in candidates:
        if cand not in seen:
            unique.append(cand)
            seen.add(cand)

    for cand in unique:
        if combined_is_valid(prompt, cand):
            return cand

    return unique[-1] if unique else "\n"


def extract_body(response: str, prompt: str) -> str:
    text = strip_code_fences(response)
    text = text.split("###", 1)[0]
    text = text.split("<file_sep>", 1)[0]
    text = text.strip("\n")

    first_code = re.search(
        r"(?m)^(?:from\s+\S+\s+import\s+|import\s+|async\s+def\s+|def\s+|class\s+|\s{4,}\S)",
        text,
    )

    if first_code:
        text = text[first_code.start():]

    if re.match(r"(?s)^\s*(?:async\s+def|def)\s+", text):
        normalized = text.replace(chr(39) * 3, chr(34) * 3)
        parts = normalized.split(chr(34) * 3)

        if len(parts) >= 3:
            text = (chr(34) * 3).join(parts[2:])
        else:
            lines = normalized.splitlines()
            for i, line in enumerate(lines):
                if i > 0 and (line.startswith("    ") or line.startswith("\t")):
                    text = "\n".join(lines[i:])
                    break

    cut = len(text)

    for pat in (
        r"\n\n(?=def\s+\w+\s*\()",
        r"\n\n(?=async\s+def\s+\w+\s*\()",
        r"\n\n(?=class\s+\w+)",
    ):
        m = re.search(pat, text)
        if m:
            cut = min(cut, m.start())

    text = text[:cut].rstrip()
    return choose_best_body(text, prompt)


def build_messages(prompt: str) -> List[Dict[str, str]]:
    instruction = (
        "Implement the following Python function. Match the signature and "
        "docstring exactly. Return only the function body that should appear "
        "after the docstring. Do not include Markdown fences, explanations, "
        "tests, examples, or a repeated function signature. Make sure the "
        "returned body is syntactically complete Python. Every non-empty line "
        "in your answer must be valid Python code inside the function body; "
        "do not put imports or statements at column 0.\n\n"
        f"{prompt.rstrip()}"
    )

    return [
        {
            "role": "system",
            "content": "You generate compact, complete, correct Python source code only. Never include prose.",
        },
        {
            "role": "user",
            "content": instruction,
        },
    ]


def request_chat_completion(
    api_url: str,
    api_key: str,
    model_name: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: Optional[float],
    timeout: int,
    retries: int,
    retry_sleep: float,
    retry_sleep_max: float,
    retry_forever: bool,
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/7.81.0",
    }

    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": build_messages(prompt),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if top_p is not None:
        payload["top_p"] = top_p

    attempt = 0
    last_error: Optional[BaseException] = None

    while True:
        attempt += 1

        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        except Exception as exc:
            last_error = exc

            if not retry_forever and attempt > retries:
                break

            if retry_forever:
                attempt_label = f"attempt {attempt}; retrying indefinitely"
            else:
                attempt_label = f"attempt {attempt}/{retries + 1}"

            sleep_s = min(retry_sleep * max(attempt, 1), retry_sleep_max)
            print(
                f"[WARN] request failed on {attempt_label}: {exc}; "
                f"sleeping {sleep_s:.1f}s",
                file=sys.stderr,
            )
            time.sleep(sleep_s)

    raise RuntimeError(f"chat completion failed after {retries + 1} attempts: {last_error}")


def extract_content(response_json: Dict[str, Any]) -> str:
    try:
        return response_json["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(
            f"unexpected response shape: {exc}; "
            f"response={json.dumps(response_json)[:1000]}"
        )


def validate_candidate(prompt: str, solution: str, output: str) -> CandidateResult:
    hwc_code = compose_code(prompt, solution)
    raw_mgc_code = compose_code(prompt, output)

    clean = clean_output(prompt, output)
    clean_mgc_code = compose_code(prompt, clean)

    hwc_res = syntax_check(hwc_code)
    if not hwc_res.ok:
        return CandidateResult(False, f"HWC syntax error: {hwc_res.error}", "invalid", hwc_code, clean_mgc_code, clean)

    if not has_exactly_one_top_level_block(hwc_code):
        return CandidateResult(False, "HWC wrong top-level block count", "invalid", hwc_code, clean_mgc_code, clean)

    if not has_non_empty_body_after_docstring(hwc_code):
        return CandidateResult(False, "HWC empty or docstring-only body", "invalid", hwc_code, clean_mgc_code, clean)

    clean_res = syntax_check(clean_mgc_code)
    raw_res = syntax_check(raw_mgc_code)

    clean_ok = (
        clean_res.ok
        and has_exactly_one_top_level_block(clean_mgc_code)
        and has_non_empty_body_after_docstring(clean_mgc_code)
    )

    raw_ok = (
        raw_res.ok
        and has_exactly_one_top_level_block(raw_mgc_code)
        and has_non_empty_body_after_docstring(raw_mgc_code)
    )

    if clean_ok:
        return CandidateResult(True, "", "clean_valid", hwc_code, clean_mgc_code, clean)

    if raw_ok:
        return CandidateResult(True, "", "raw_valid", hwc_code, raw_mgc_code, output)

    error = clean_res.error if clean_res.error else "MGC failed structural/body validation"
    return CandidateResult(False, error, "invalid", hwc_code, clean_mgc_code, clean)


def validate_existing_pairs(df: pd.DataFrame) -> Tuple[int, int]:
    required = {"idx", "code", "label"}

    if not required.issubset(df.columns):
        raise ValueError(f"CSV must contain columns {sorted(required)}")

    if len(df) % 2 != 0:
        raise ValueError(f"CSV has odd row count: {len(df)}")

    seen_pairs = set()
    max_line_num = 0

    for i in range(0, len(df), 2):
        human_idx = str(df.iloc[i]["idx"]).strip()
        lm_idx = str(df.iloc[i + 1]["idx"]).strip()
        human_label = str(df.iloc[i]["label"]).strip()
        lm_label = str(df.iloc[i + 1]["label"]).strip()

        if not human_idx.endswith("_human"):
            raise ValueError(f"Row {i} is not a human row: {human_idx}")

        if not lm_idx.endswith("_lm"):
            raise ValueError(f"Row {i + 1} is not an lm row: {lm_idx}")

        if human_label != "human":
            raise ValueError(f"Row {i} label should be human: {human_label}")

        if lm_label != "lm":
            raise ValueError(f"Row {i + 1} label should be lm: {lm_label}")

        human_base = human_idx[:-len("_human")]
        lm_base = lm_idx[:-len("_lm")]

        if human_base != lm_base:
            raise ValueError(f"Pair mismatch at rows {i}-{i + 1}: {human_idx}, {lm_idx}")

        if human_base in seen_pairs:
            raise ValueError(f"Duplicate pair id found: {human_base}")

        seen_pairs.add(human_base)

        m = re.search(r"line(\d+)$", human_base)
        if m:
            max_line_num = max(max_line_num, int(m.group(1)))

    return len(seen_pairs), max_line_num


def make_backup(out_dir: Path, timestamp: str) -> Optional[Path]:
    if not out_dir.exists():
        return None

    backup_dir = out_dir.with_name(f"{out_dir.name}-bak-{timestamp}")

    if backup_dir.exists():
        raise FileExistsError(f"backup already exists: {backup_dir}")

    shutil.copytree(out_dir, backup_dir)
    return backup_dir


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def iter_codesearchnet_train(train_jsonl: Path):
    with train_jsonl.open("r", encoding="utf-8") as f:
        for source_line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            yield source_line_no, json.loads(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate more valid MGC samples and append to an existing AI-Detector CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "existing_csv",
        type=Path,
        help="Path to existing paired CSV.",
    )
    parser.add_argument(
        "num_datasets",
        type=int,
        help="Target final number of valid pairs by default. Use --additional to treat this as additional pair count.",
    )

    parser.add_argument(
        "--additional",
        action="store_true",
        help="Treat num_datasets as the number of new pairs to add, not the final target size.",
    )
    parser.add_argument(
        "--codesearchnet-root",
        type=Path,
        default=Path("data/CodeSearchNet"),
        help="Path to CodeSearchNet root directory.",
    )
    parser.add_argument("--language", default="python")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--out-csv", type=Path, default=None)

    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--top-p", type=float, default=None)

    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=20)
    parser.add_argument("--retry-sleep", type=float, default=5.0)
    parser.add_argument("--retry-sleep-max", type=float, default=120.0)
    parser.add_argument("--retry-forever", action="store_true")

    parser.add_argument(
        "--max-api-calls",
        type=int,
        default=0,
        help="Safety limit for API calls. 0 means no limit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do all checks but do not call API and do not write output.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    existing_csv = args.existing_csv.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()

    if not existing_csv.exists():
        print(f"[ERROR] existing CSV not found: {existing_csv}", file=sys.stderr)
        return 2

    train_jsonl = (
        args.codesearchnet_root.expanduser().resolve()
        / args.language
        / "train.jsonl"
    )

    if not train_jsonl.exists():
        print(f"[ERROR] CodeSearchNet train.jsonl not found: {train_jsonl}", file=sys.stderr)
        return 2

    print("=" * 72)
    print("generate-more.py")
    print("=" * 72)
    print(f"existing_csv : {existing_csv}")
    print(f"train_jsonl  : {train_jsonl}")
    print(f"out_dir      : {out_dir}")
    print(f"model        : {args.model_name}")
    print(f"temperature  : {args.temperature}")
    print(f"max_tokens   : {args.max_tokens}")

    df_existing = pd.read_csv(existing_csv, dtype={"idx": "string", "label": "string"})
    current_pairs, max_line_num = validate_existing_pairs(df_existing)

    if args.additional:
        target_pairs = current_pairs + args.num_datasets
        needed_pairs = args.num_datasets
    else:
        target_pairs = args.num_datasets
        needed_pairs = target_pairs - current_pairs

    print(f"current pairs: {current_pairs}")
    print(f"target pairs : {target_pairs}")
    print(f"needed pairs : {needed_pairs}")

    if needed_pairs <= 0:
        print("[INFO] No generation needed. Existing CSV already satisfies target.")
        return 0

    existing_hwc_hashes = set()
    for i in range(0, len(df_existing), 2):
        hwc_code = str(df_existing.iloc[i]["code"])
        existing_hwc_hashes.add(stable_hash(hwc_code))

    if args.dry_run:
        print("[DRY-RUN] Would scan CodeSearchNet and generate new samples.")
        return 0

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"[ERROR] missing API key env var: {args.api_key_env}", file=sys.stderr)
        return 2

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    backup_dir = make_backup(out_dir, timestamp)
    if backup_dir:
        print(f"[INFO] Backup created: {backup_dir}")
    else:
        print(f"[INFO] Output directory does not exist yet. No backup needed: {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    metadata_dir = out_dir / f"generate_more_metadata_{timestamp}"
    attempts_jsonl = metadata_dir / "generated_attempts.jsonl"
    valid_jsonl = metadata_dir / "generated_valid.jsonl"
    invalid_jsonl = metadata_dir / "generated_invalid.jsonl"
    summary_json = metadata_dir / "summary.json"

    new_rows: List[Dict[str, str]] = []
    new_valid_pairs = 0
    api_calls = 0
    skipped_existing_hwc = 0
    skipped_bad_prompt = 0
    skipped_bad_hwc = 0
    generated_invalid = 0

    next_line_num = max_line_num + 1

    for source_line_no, obj in iter_codesearchnet_train(train_jsonl):
        if new_valid_pairs >= needed_pairs:
            break

        if args.max_api_calls > 0 and api_calls >= args.max_api_calls:
            print(f"[WARN] Reached --max-api-calls={args.max_api_calls}")
            break

        prompt, solution = split_prompt_body(obj.get("original_string", ""))

        if prompt is None or solution is None:
            skipped_bad_prompt += 1
            continue

        hwc_code = compose_code(prompt, solution)
        hwc_hash = stable_hash(hwc_code)

        if hwc_hash in existing_hwc_hashes:
            skipped_existing_hwc += 1
            continue

        # Avoid spending API calls on HWC that cannot enter paired-valid output.
        hwc_res = syntax_check(hwc_code)
        if (
            not hwc_res.ok
            or not has_exactly_one_top_level_block(hwc_code)
            or not has_non_empty_body_after_docstring(hwc_code)
        ):
            skipped_bad_hwc += 1
            existing_hwc_hashes.add(hwc_hash)
            continue

        print(
            f"[GEN] source_line_no={source_line_no}, "
            f"new_valid={new_valid_pairs}/{needed_pairs}, "
            f"api_calls={api_calls}"
        )

        response_json = request_chat_completion(
            api_url=args.api_url,
            api_key=api_key,
            model_name=args.model_name,
            prompt=prompt,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            top_p=args.top_p,
            timeout=args.timeout,
            retries=args.retries,
            retry_sleep=args.retry_sleep,
            retry_sleep_max=args.retry_sleep_max,
            retry_forever=args.retry_forever,
        )

        api_calls += 1

        raw_output = extract_content(response_json)
        output = extract_body(raw_output, prompt)

        attempt_record = {
            "prompt": prompt,
            "output": output,
            "solution": solution,
            "raw_output": raw_output,
            "model": args.model_name,
            "temperature": args.temperature,
            "source_line_no": source_line_no,
            "repo": obj.get("repo", ""),
            "path": obj.get("path", ""),
            "func_name": obj.get("func_name", ""),
        }
        append_jsonl(attempts_jsonl, attempt_record)

        result = validate_candidate(prompt, solution, output)

        if not result.ok:
            generated_invalid += 1
            invalid_record = dict(attempt_record)
            invalid_record["error"] = result.error
            invalid_record["status"] = result.status
            append_jsonl(invalid_jsonl, invalid_record)
            existing_hwc_hashes.add(hwc_hash)
            continue

        pair_id = f"line{next_line_num}"
        next_line_num += 1

        human_idx = f"{pair_id}_human"
        lm_idx = f"{pair_id}_lm"

        new_rows.append(
            {
                "idx": human_idx,
                "code": result.hwc_code,
                "label": "human",
            }
        )
        new_rows.append(
            {
                "idx": lm_idx,
                "code": result.mgc_code,
                "label": "lm",
            }
        )

        valid_record = dict(attempt_record)
        valid_record["status"] = result.status
        valid_record["pair_id"] = pair_id
        valid_record["hwc_code"] = result.hwc_code
        valid_record["mgc_code"] = result.mgc_code
        valid_record["selected_output"] = result.selected_output
        append_jsonl(valid_jsonl, valid_record)

        existing_hwc_hashes.add(hwc_hash)
        new_valid_pairs += 1

        print(f"[OK] Added {pair_id}; total new valid={new_valid_pairs}/{needed_pairs}")

    if new_valid_pairs < needed_pairs:
        print(
            f"[WARN] Only generated {new_valid_pairs}/{needed_pairs} needed valid pairs.",
            file=sys.stderr,
        )

    df_new = pd.DataFrame(new_rows, columns=["idx", "code", "label"])
    df_out = pd.concat([df_existing[["idx", "code", "label"]], df_new], ignore_index=True)

    final_pairs = len(df_out) // 2

    out_csv = args.out_csv.expanduser().resolve() if args.out_csv else (out_dir / existing_csv.name)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_csv, index=False)

    summary = {
        "existing_csv": str(existing_csv),
        "out_csv": str(out_csv),
        "out_dir": str(out_dir),
        "backup_dir": str(backup_dir) if backup_dir else "",
        "metadata_dir": str(metadata_dir),
        "current_pairs": current_pairs,
        "target_pairs": target_pairs,
        "needed_pairs": needed_pairs,
        "new_valid_pairs": new_valid_pairs,
        "final_pairs": final_pairs,
        "api_calls": api_calls,
        "skipped_existing_hwc": skipped_existing_hwc,
        "skipped_bad_prompt": skipped_bad_prompt,
        "skipped_bad_hwc": skipped_bad_hwc,
        "generated_invalid": generated_invalid,
        "attempts_jsonl": str(attempts_jsonl),
        "valid_jsonl": str(valid_jsonl),
        "invalid_jsonl": str(invalid_jsonl),
    }

    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print("Done")
    print("=" * 72)
    print(f"backup_dir          : {backup_dir}")
    print(f"output_csv          : {out_csv}")
    print(f"metadata_dir        : {metadata_dir}")
    print(f"current_pairs       : {current_pairs}")
    print(f"new_valid_pairs     : {new_valid_pairs}")
    print(f"final_pairs         : {final_pairs}")
    print(f"api_calls           : {api_calls}")
    print(f"skipped_existing_hwc: {skipped_existing_hwc}")
    print(f"skipped_bad_prompt  : {skipped_bad_prompt}")
    print(f"skipped_bad_hwc     : {skipped_bad_hwc}")
    print(f"generated_invalid   : {generated_invalid}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())