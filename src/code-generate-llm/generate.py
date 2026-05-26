#!/usr/bin/env python3
"""
generate.py
===========

OpenAI-compatible GPT/MGC generation for the AI-Detector CodeSearchNet path.

This is a drop-in-style replacement for the HF-local `generate.py` workflow:
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
import gzip
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
    """
    Load benchmark prompt/solution pairs using the same shape as the original
    project generate.py: `prompt` is the function signature + docstring, and
    `solution` is the human-written implementation body.
    """
    all_prompts: List[str] = []
    all_solutions: List[str] = []

    if "humaneval" in path.lower():
        path_to_data = f"{path}/{language}/data/humaneval_{language}.jsonl.gz"
        logger.info(f"Loading data from {path_to_data}")
        with gzip.open(path_to_data, "rb") as f:
            for line in f:
                data = json.loads(line)
                all_prompts.append(data["prompt"])
                all_solutions.append(data["canonical_solution"])

    elif "codesearchnet" in path.lower():
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

    elif "thevault" in path.lower():
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


def extract_body(response: str, prompt: str) -> str:
    """
    Convert a chat-model response into the continuation body expected downstream.

    Downstream `find_validsyntax_mgc.py` builds MGC as prompt + output, so this
    function tries to remove re-emitted signatures/docstrings and keep only the
    implementation body.
    """
    text = strip_code_fences(response)
    text = text.split("###", 1)[0]
    text = text.split("<file_sep>", 1)[0]
    text = text.strip("\n")

    # Remove common prose before code.
    first_code = re.search(r"(?m)^(?:from\s+\S+\s+import\s+|import\s+|async\s+def\s+|def\s+|class\s+|\s{4,}\S)", text)
    if first_code:
        text = text[first_code.start():]

    # If the model re-emits the full function, drop the def/docstring prefix.
    if re.match(r"(?s)^\s*(?:async\s+def|def)\s+", text):
        normalized = text.replace("'''", '"""')
        parts = normalized.split('"""')
        if len(parts) >= 3:
            text = '"""'.join(parts[2:])
        else:
            lines = normalized.splitlines()
            for i, line in enumerate(lines):
                if i > 0 and (line.startswith("    ") or line.startswith("\t")):
                    text = "\n".join(lines[i:])
                    break

    # Cut at the next top-level def/class. Mirrors the validated logic in
    # generate_starcoder15b.py: require a blank line before the cut and a
    # real identifier after the keyword, so we don't over-cut nested
    # helpers indented 1-3 spaces.
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
    if not text:
        return "\n"
    if not text.startswith("\n"):
        text = "\n" + text
    return text + "\n"


def build_messages(prompt: str) -> List[Dict[str, str]]:
    instruction = (
        "Implement the following Python function. Match the signature and "
        "docstring exactly. Return only the function body that should appear "
        "after the docstring. Do not include Markdown fences, explanations, "
        "tests, examples, or a repeated function signature.\n\n"
        f"{prompt.rstrip()}"
    )
    return [
        {
            "role": "system",
            "content": "You generate compact, correct Python source code only. Never include prose.",
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

    last_error: Optional[BaseException] = None
    for attempt in range(1, retries + 2):
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # network/API failure; retry a few times for long batch jobs
            last_error = exc
            if attempt > retries:
                break
            logger.warning(f"request failed on attempt {attempt}/{retries + 1}: {exc}; retrying")
            time.sleep(retry_sleep * attempt)

    raise RuntimeError(f"chat completion failed after {retries + 1} attempts: {last_error}")


def extract_content(response_json: Dict[str, Any]) -> str:
    try:
        return response_json["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"unexpected response shape: {exc}; response={json.dumps(response_json)[:1000]}")


def generate_openai_compat(
    model_name: str,
    prompts: List[str],
    solutions: List[str],
    api_url: str,
    api_key_env: str,
    temperature: float = 0.0,
    max_tokens: int = 512,
    top_p: Optional[float] = None,
    timeout: int = 120,
    retries: int = 2,
    retry_sleep: float = 2.0,
) -> Tuple[List[str], List[str], List[str], List[str]]:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise SystemExit(f"[ERROR] missing API key env var: {api_key_env}")

    outputs: List[str] = []
    raw_outputs: List[str] = []

    for prompt in tqdm(prompts, desc=f"generating {model_name}"):
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
        )
        raw = extract_content(response_json)
        raw_outputs.append(raw)
        outputs.append(extract_body(raw, prompt))

    logger.info(f"Generated {len(outputs)} samples")
    logger.info("Showing first 3 samples")
    for i in range(min(3, len(outputs))):
        logger.info(f"Example {i}:")
        logger.info(f"Prompt:\n{prompts[i]}")
        logger.info(f"Output:\n{outputs[i]}")
        logger.info(f"Solution:\n{solutions[i]}")

    return prompts, outputs, solutions, raw_outputs


def safe_model_label(model_name: str) -> str:
    return model_name.rstrip("/").split("/")[-1].replace(":", "-")


def write_outputs(
    path: str,
    model_name: str,
    max_num: int,
    temperature: float,
    max_length: int,
    prompts: List[str],
    outputs: List[str],
    solutions: List[str],
    raw_outputs: List[str],
    output_root: str,
) -> Path:
    dataset_name = Path(path).name
    model_label = safe_model_label(model_name)
    output_dir = Path(output_root) / dataset_name / f"{model_label}-{max_num}-tp{temperature}"
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / f"outputs-{max_length}token.txt"
    readable_path = output_dir / f"outputs-{max_length}token_v2.txt"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for prompt, output, solution, raw in zip(prompts, outputs, solutions, raw_outputs):
            record = {
                "prompt": prompt,
                "output": output,
                "solution": solution,
                "raw_output": raw,
                "model": model_name,
                "temperature": temperature,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with readable_path.open("w", encoding="utf-8") as f:
        for i, (prompt, output, solution, raw) in enumerate(zip(prompts, outputs, solutions, raw_outputs)):
            print("-" * 20 + f" Sample {i} " + "-" * 20, file=f)
            print(f"Prompt:\n{prompt}", file=f)
            print("-" * 10, file=f)
            print(f"Output:\n{output}", file=f)
            print("-" * 10, file=f)
            print(f"Raw response:\n{raw}", file=f)
            print("-" * 10, file=f)
            print(f"Solution:\n{solution}", file=f)

    logger.info(f"Finished writing JSONL to {jsonl_path}")
    logger.info(f"Finished writing readable output to {readable_path}")
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--path", type=str, default="data/CodeSearchNet")
    parser.add_argument("--language", type=str, default="python")
    parser.add_argument(
        "--max_num",
        type=int,
        default=1000,
        help=(
            "Max samples to generate. Default is intentionally small "
            "because each sample is a paid API call; the run0a-*.sh shell "
            "always sets this explicitly."
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL)
    parser.add_argument("--api-key-env", type=str, default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--max_length", type=int, default=512, help="Max completion tokens.")
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-root", type=str, default="output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger.info(f"args: {args}")

    prompts, solutions = load_data(
        path=args.path,
        language=args.language,
        max_num=args.max_num,
        seed=args.seed,
    )

    prompts, outputs, solutions, raw_outputs = generate_openai_compat(
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
    )

    out_dir = write_outputs(
        path=args.path,
        model_name=args.model_name,
        max_num=args.max_num,
        temperature=args.temperature,
        max_length=args.max_length,
        prompts=prompts,
        outputs=outputs,
        solutions=solutions,
        raw_outputs=raw_outputs,
        output_root=args.output_root,
    )
    print(f"Output directory: {out_dir}")


if __name__ == "__main__":
    main()
