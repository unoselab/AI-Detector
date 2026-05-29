#!/usr/bin/env python3
"""
generate.py
===========

OpenAI-compatible GPT/MGC generation for the AI-Detector CodeSearchNet path.

This version is safe for long API runs:
  * writes each completed sample immediately to JSONL;
  * resumes from an existing JSONL if a run is interrupted;
  * can retry transient network/API failures indefinitely with backoff;
  * rebuilds the human-readable inspection file from the checkpoint JSONL.

  1. load CodeSearchNet Python prompt/solution pairs;
  2. call an OpenAI-compatible /v1/chat/completions endpoint;
  3. write JSONL records with fields: prompt, output, solution;
  4. write a readable companion file for inspection.

Default endpoint/model are set for the Nautilus OpenAI-compatible service used
in this project. Override them with --api-url, --model-name, and --api-key-env.

Example:
  OPENAI_API_KEY=... python src/code-generate-llm/generate.py \
      --path ../data/CodeSearchNet \
      --model_name gpt-oss \
      --max_num 10 \
      --temperature 0.0 \
      --max_length 512
"""

from __future__ import annotations

import argparse
import ast
import gzip
import json
import os
import re
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from loguru import logger
from tqdm import tqdm

DEFAULT_API_URL = "https://ellm.nrp-nautilus.io/v1/chat/completions"
DEFAULT_MODEL = "gpt-oss"
DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"
CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)


def split_prompt_body(original_string: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (signature/docstring prompt, human body) from a CodeSearchNet row."""
    s = str(original_string or "").replace("'''", '"""')
    parts = s.split('"""')
    if len(parts) < 3:
        return None, None
    prompt = parts[0] + '"""' + parts[1] + '"""'
    body = parts[2]
    return prompt, body


def load_data(path: str = "data/CodeSearchNet", language: str = "python", max_num: int = 10000, seed: int = 42) -> Tuple[List[str], List[str]]:
    all_prompts: List[str] = []
    all_solutions: List[str] = []

    path_lower = path.lower()
    if "humaneval" in path_lower:
        path_to_data = f"{path}/{language}/data/humaneval_{language}.jsonl.gz"
        logger.info(f"Loading data from {path_to_data}")
        with gzip.open(path_to_data, "rb") as f:
            for line in f:
                data = json.loads(line)
                all_prompts.append(data["prompt"])
                all_solutions.append(data["canonical_solution"])

    elif "codesearchnet" in path_lower:
        path_to_data = f"{path}/{language}/train.jsonl"
        logger.info(f"Loading data from {path_to_data}")

        failed = 0
        success = 0
        max_prompt_len = 128
        min_prompt_len = 5
        max_solution_len = 256
        min_solution_len = 5

        with open(path_to_data, "r", encoding="utf-8") as f:
            for line in tqdm(f, desc="reading CodeSearchNet"):
                data = json.loads(line)
                prompt, solution = split_prompt_body(data.get("original_string", ""))
                if prompt is None or solution is None:
                    failed += 1
                    continue
                success += 1

                if len(prompt.split()) > max_prompt_len or len(prompt.split()) < min_prompt_len:
                    continue
                if len(solution.split()) > max_solution_len or len(solution.split()) < min_solution_len:
                    continue

                all_prompts.append(prompt)
                all_solutions.append(solution)

        logger.info(f"Failed: {failed}, Success: {success}")

    elif "thevault" in path_lower:
        path_to_data = f"{path}/{language}/small_train.jsonl"
        logger.info(f"Loading data from {path_to_data}")
        failed = 0
        success = 0
        with open(path_to_data, "r", encoding="utf-8") as f:
            for line in tqdm(f, desc="reading TheVault"):
                data = json.loads(line)
                prompt, solution = split_prompt_body(data.get("original_string", ""))
                if prompt is None or solution is None:
                    failed += 1
                    continue
                success += 1
                all_prompts.append(prompt)
                all_solutions.append(solution)
        logger.info(f"Failed: {failed}, Success: {success}")
    else:
        raise SystemExit(f"[ERROR] unsupported data path: {path}")

    if not all_prompts:
        raise SystemExit("[ERROR] no prompts loaded")

    logger.info(f"Loaded {len(all_prompts)} prompts and {len(all_solutions)} solutions")
    prompt_lengths = [len(p.split()) for p in all_prompts]
    solution_lengths = [len(s.split()) for s in all_solutions]
    logger.info(
        f"Prompt lengths: min={min(prompt_lengths)}, max={max(prompt_lengths)}, "
        f"mean={np.mean(prompt_lengths):.2f}, std={np.std(prompt_lengths):.2f}"
    )
    logger.info(
        f"Solution lengths: min={min(solution_lengths)}, max={max(solution_lengths)}, "
        f"mean={np.mean(solution_lengths):.2f}, std={np.std(solution_lengths):.2f}"
    )

    if len(all_prompts) > max_num:
        rng = np.random.default_rng(seed)
        indices = rng.choice(len(all_prompts), max_num, replace=False)
        all_prompts = [all_prompts[i] for i in indices]
        all_solutions = [all_solutions[i] for i in indices]
        logger.info(f"Sampled {len(all_prompts)} prompts and {len(all_solutions)} solutions with seed={seed}")

    return all_prompts, all_solutions


def strip_code_fences(text: str) -> str:
    m = CODE_FENCE_RE.search(text or "")
    return m.group(1) if m else (text or "")



def body_indent_from_prompt(prompt: str) -> str:
    """Infer the indentation level for code that follows the prompt docstring."""
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
    """
    Gemma sometimes emits:
        import numpy as np

            if ...
    where the import is column-0 but the body is already indented.
    Shift one indentation level left before reindenting the whole body.
    """
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
    """Dedent model output and reindent every non-empty line as function body code."""
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
    """Convert a chat-model response into the continuation body expected downstream."""
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

    # If the model re-emits the full function, drop the def/docstring prefix.
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
        {"role": "user", "content": instruction},
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
            response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
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
            logger.warning(f"request failed on {attempt_label}: {exc}; sleeping {sleep_s:.1f}s")
            time.sleep(sleep_s)

    raise RuntimeError(f"chat completion failed after {retries + 1} attempts: {last_error}")


def extract_content(response_json: Dict[str, Any]) -> str:
    try:
        return response_json["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"unexpected response shape: {exc}; response={json.dumps(response_json)[:1000]}")


def safe_model_label(model_name: str) -> str:
    return model_name.rstrip("/").split("/")[-1].replace(":", "-")


def output_paths(path: str, model_name: str, max_num: int, temperature: float, max_length: int, output_root: str) -> Tuple[Path, Path, Path]:
    dataset_name = Path(path).name
    model_label = safe_model_label(model_name)
    output_dir = Path(output_root) / dataset_name / f"{model_label}-{max_num}-tp{temperature}"
    jsonl_path = output_dir / f"outputs-{max_length}token.txt"
    readable_path = output_dir / f"outputs-{max_length}token_v2.txt"
    return output_dir, jsonl_path, readable_path


def load_existing_records(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load valid checkpoint records. If the final line is corrupt, truncate to valid prefix."""
    if not jsonl_path.exists():
        return []

    records: List[Dict[str, Any]] = []
    bad_line = None
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                bad_line = line_no
                logger.warning(f"Ignoring corrupt checkpoint line {line_no} in {jsonl_path}")
                break

    if bad_line is not None:
        backup = jsonl_path.with_suffix(jsonl_path.suffix + ".corrupt_backup")
        jsonl_path.replace(backup)
        with jsonl_path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        logger.warning(f"Truncated checkpoint to {len(records)} valid records; backup: {backup}")

    return records


def append_record(jsonl_path: Path, record: Dict[str, Any], do_fsync: bool = True) -> None:
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        if do_fsync:
            os.fsync(f.fileno())


def write_readable_from_jsonl(jsonl_path: Path, readable_path: Path) -> None:
    records = load_existing_records(jsonl_path)
    with readable_path.open("w", encoding="utf-8") as f:
        for i, rec in enumerate(records):
            print("-" * 20 + f" Sample {i} " + "-" * 20, file=f)
            print(f"Prompt:\n{rec.get('prompt', '')}", file=f)
            print("-" * 10, file=f)
            print(f"Output:\n{rec.get('output', '')}", file=f)
            print("-" * 10, file=f)
            print(f"Raw response:\n{rec.get('raw_output', '')}", file=f)
            print("-" * 10, file=f)
            print(f"Solution:\n{rec.get('solution', '')}", file=f)


def generate_openai_compat_streaming(
    model_name: str,
    prompts: List[str],
    solutions: List[str],
    api_url: str,
    api_key_env: str,
    temperature: float,
    max_tokens: int,
    top_p: Optional[float],
    timeout: int,
    retries: int,
    retry_sleep: float,
    retry_sleep_max: float,
    retry_forever: bool,
    jsonl_path: Path,
    resume: bool,
    checkpoint_every: int,
) -> int:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise SystemExit(f"[ERROR] missing API key env var: {api_key_env}")

    existing = load_existing_records(jsonl_path) if resume else []
    start_idx = len(existing)
    if start_idx > len(prompts):
        raise SystemExit(f"[ERROR] checkpoint has {start_idx} records but run only has {len(prompts)} prompts")
    if start_idx:
        logger.info(f"Resuming from checkpoint: {jsonl_path} ({start_idx}/{len(prompts)} records already complete)")

    generated_now = 0
    pbar = tqdm(range(start_idx, len(prompts)), desc=f"generating {model_name}", initial=start_idx, total=len(prompts))
    for i in pbar:
        prompt = prompts[i]
        solution = solutions[i]
        response_json = request_chat_completion(
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            timeout=timeout,
            retries=retries,
            retry_sleep=retry_sleep,
            retry_sleep_max=retry_sleep_max,
            retry_forever=retry_forever,
        )
        raw = extract_content(response_json)
        output = extract_body(raw, prompt)
        record = {
            "prompt": prompt,
            "output": output,
            "solution": solution,
            "raw_output": raw,
            "model": model_name,
            "temperature": temperature,
            "sample_index": i,
        }
        generated_now += 1
        append_record(jsonl_path, record, do_fsync=(checkpoint_every <= 1 or generated_now % checkpoint_every == 0))

    total_records = len(load_existing_records(jsonl_path))
    logger.info(f"Generated {generated_now} new samples; checkpoint now has {total_records} records")

    records = load_existing_records(jsonl_path)
    logger.info("Showing first 3 samples from checkpoint")
    for i, rec in enumerate(records[:3]):
        logger.info(f"Example {i}:")
        logger.info(f"Prompt:\n{rec.get('prompt', '')}")
        logger.info(f"Output:\n{rec.get('output', '')}")
        logger.info(f"Solution:\n{rec.get('solution', '')}")
    return total_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--path", type=str, default="data/CodeSearchNet")
    parser.add_argument("--language", type=str, default="python")
    parser.add_argument("--max_num", type=int, default=1000, help="Max samples to generate. Shell wrapper should set this explicitly.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL)
    parser.add_argument("--api-key-env", type=str, default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--max_length", type=int, default=512, help="Max completion tokens.")
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=20, help="Finite retry count when --retry-forever is not set.")
    parser.add_argument("--retry-sleep", type=float, default=5.0)
    parser.add_argument("--retry-sleep-max", type=float, default=120.0)
    parser.add_argument("--retry-forever", action="store_true", help="Keep waiting/retrying through transient network/API outages.")
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument("--resume", dest="resume", action="store_true", default=True, help="Resume from existing JSONL checkpoint. Default: true.")
    resume_group.add_argument("--no-resume", dest="resume", action="store_false", help="Do not resume; append from the beginning only if output file is absent.")
    parser.add_argument("--checkpoint-every", type=int, default=1, help="fsync every N samples. Default 1 is safest for long jobs.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-root", type=str, default="output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger.info(f"args: {args}")

    output_dir, jsonl_path, readable_path = output_paths(
        path=args.path,
        model_name=args.model_name,
        max_num=args.max_num,
        temperature=args.temperature,
        max_length=args.max_length,
        output_root=args.output_root,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Checkpoint JSONL: {jsonl_path}")

    if jsonl_path.exists() and not args.resume:
        raise SystemExit(f"[ERROR] output exists and --no-resume was used: {jsonl_path}")

    prompts, solutions = load_data(
        path=args.path,
        language=args.language,
        max_num=args.max_num,
        seed=args.seed,
    )

    total_records = generate_openai_compat_streaming(
        model_name=args.model_name,
        prompts=prompts,
        solutions=solutions,
        api_url=args.api_url,
        api_key_env=args.api_key_env,
        temperature=args.temperature,
        max_tokens=args.max_length,
        top_p=args.top_p,
        timeout=args.timeout,
        retries=args.retries,
        retry_sleep=args.retry_sleep,
        retry_sleep_max=args.retry_sleep_max,
        retry_forever=args.retry_forever,
        jsonl_path=jsonl_path,
        resume=args.resume,
        checkpoint_every=args.checkpoint_every,
    )

    write_readable_from_jsonl(jsonl_path, readable_path)
    logger.info(f"Finished writing JSONL to {jsonl_path}")
    logger.info(f"Finished writing readable output to {readable_path}")
    print(f"Output directory: {output_dir}")
    print(f"Records complete: {total_records}/{len(prompts)}")


if __name__ == "__main__":
    main()
