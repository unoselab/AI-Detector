#!/usr/bin/env python3
"""
generate-more.py
================

Generate additional valid MGC samples for an existing AI-Detector CSV.

This script reuses:
  - src/code_generation/find_validsyntax_mgc.py for syntax/salvage/body validation
  - src/code-generate-llm/generate.py for OpenAI-compatible generation helpers

Input:
  1. existing CSV path
  2. target number of valid pairs by default

Output:
  - backup of the current validsyntax directory
  - repaired/expanded CSV in the validsyntax directory
  - metadata JSONL/CSV files under generate_more_metadata_TIMESTAMP

Example:
  cd ~/project-workspace/ai_detector

  OPENAI_API_KEY=... python src/code-generate-llm/generate-more.py \
    src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax/codesearchnet_gpt-oss_python_merged_4500.csv \
    4500 \
    --codesearchnet-root data/CodeSearchNet \
    --model-name gpt-oss \
    --retry-forever
"""

from __future__ import annotations

import argparse
import builtins
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


def print(*args, **kwargs):
    """Timestamped, always-flushed print for long-running tmux/log jobs."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    kwargs.setdefault("flush", True)
    builtins.print(timestamp, *args, **kwargs)



# ---------------------------------------------------------------------------
# Import shared modules
# ---------------------------------------------------------------------------

THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[1]
THIS_DIR = THIS_FILE.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from code_generation import find_validsyntax_mgc as validsyntax  # noqa: E402
import generate as basegen  # noqa: E402


DEFAULT_OUT_DIR = Path(
    "src/code-analyzer-tree-sitter/data_codesearchnet/gpt-oss/validsyntax"
)

VALID_STATUSES = {"raw_valid", "salvaged_valid"}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def require_validsyntax_helpers() -> None:
    required = [
        "process_obj",
        "compose_code",
        "syntax_check",
        "code_has_required_structure",
    ]

    missing = [name for name in required if not hasattr(validsyntax, name)]

    if missing:
        raise RuntimeError(
            "find_validsyntax_mgc.py is missing required helpers: "
            + ", ".join(missing)
            + "\nPlease add code_has_required_structure() to find_validsyntax_mgc.py first."
        )


def normalize_code_for_hash(code: Any) -> str:
    return validsyntax.normalize_newlines(code).strip()


def stable_code_hash(code: Any) -> str:
    normalized = normalize_code_for_hash(code)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def make_backup(out_dir: Path, timestamp: str) -> Optional[Path]:
    if not out_dir.exists():
        return None

    backup_dir = out_dir.with_name(f"{out_dir.name}-bak-{timestamp}")

    if backup_dir.exists():
        raise FileExistsError(f"Backup directory already exists: {backup_dir}")

    shutil.copytree(out_dir, backup_dir)
    return backup_dir


def pair_base_from_idx(idx: str, suffix: str) -> str:
    idx = str(idx).strip()
    if idx.endswith(suffix):
        return idx[:-len(suffix)]
    return idx


def extract_line_number(pair_id: str) -> Optional[int]:
    m = re.search(r"line(\d+)$", str(pair_id))
    if not m:
        return None
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Existing CSV validation
# ---------------------------------------------------------------------------

def validate_existing_pair_shape(df: pd.DataFrame) -> Tuple[int, int, set[str]]:
    required = {"idx", "code", "label"}

    if not required.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {sorted(required)}")

    if len(df) % 2 != 0:
        raise ValueError(f"CSV has odd row count: {len(df)}")

    seen_pair_ids = set()
    all_hwc_hashes = set()
    max_line_num = 0

    for i in range(0, len(df), 2):
        human = df.iloc[i]
        lm = df.iloc[i + 1]

        human_idx = str(human["idx"]).strip()
        lm_idx = str(lm["idx"]).strip()
        human_label = str(human["label"]).strip()
        lm_label = str(lm["label"]).strip()

        if not human_idx.endswith("_human"):
            raise ValueError(f"Row {i} is not a human row: {human_idx}")

        if not lm_idx.endswith("_lm"):
            raise ValueError(f"Row {i + 1} is not an lm row: {lm_idx}")

        if human_label != "human":
            raise ValueError(f"Row {i} label should be human, got: {human_label}")

        if lm_label != "lm":
            raise ValueError(f"Row {i + 1} label should be lm, got: {lm_label}")

        human_base = pair_base_from_idx(human_idx, "_human")
        lm_base = pair_base_from_idx(lm_idx, "_lm")

        if human_base != lm_base:
            raise ValueError(
                f"Pair mismatch at rows {i}-{i + 1}: {human_idx}, {lm_idx}"
            )

        if human_base in seen_pair_ids:
            raise ValueError(f"Duplicate pair id: {human_base}")

        seen_pair_ids.add(human_base)
        all_hwc_hashes.add(stable_code_hash(human["code"]))

        line_no = extract_line_number(human_base)
        if line_no is not None:
            max_line_num = max(max_line_num, line_no)

    return len(seen_pair_ids), max_line_num, all_hwc_hashes


def code_is_valid_for_dataset(code: str) -> Tuple[bool, str]:
    syntax_res = validsyntax.syntax_check(code)

    if not syntax_res.ok:
        return False, syntax_res.error

    return validsyntax.code_has_required_structure(code)


def revalidate_existing_csv_pairs(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    valid_rows: List[Dict[str, str]] = []
    invalid_records: List[Dict[str, str]] = []

    for i in range(0, len(df), 2):
        human = df.iloc[i]
        lm = df.iloc[i + 1]

        human_idx = str(human["idx"]).strip()
        lm_idx = str(lm["idx"]).strip()

        human_code = str(human["code"])
        lm_code = str(lm["code"])

        human_ok, human_err = code_is_valid_for_dataset(human_code)
        lm_ok, lm_err = code_is_valid_for_dataset(lm_code)

        errors = []

        if not human_ok:
            errors.append(f"HWC: {human_err}")

        if not lm_ok:
            errors.append(f"MGC: {lm_err}")

        if errors:
            invalid_records.append(
                {
                    "human_idx": human_idx,
                    "lm_idx": lm_idx,
                    "errors": " | ".join(errors),
                    "human_code": human_code,
                    "lm_code": lm_code,
                }
            )
            continue

        valid_rows.append(
            {
                "idx": human_idx,
                "code": human_code,
                "label": "human",
            }
        )
        valid_rows.append(
            {
                "idx": lm_idx,
                "code": lm_code,
                "label": "lm",
            }
        )

    valid_df = pd.DataFrame(valid_rows, columns=["idx", "code", "label"])
    invalid_df = pd.DataFrame(
        invalid_records,
        columns=["human_idx", "lm_idx", "errors", "human_code", "lm_code"],
    )

    return valid_df, invalid_df


# ---------------------------------------------------------------------------
# CodeSearchNet scanning
# ---------------------------------------------------------------------------

def iter_codesearchnet_candidates(
    train_jsonl: Path,
    min_prompt_len: int,
    max_prompt_len: int,
    min_solution_len: int,
    max_solution_len: int,
) -> Iterable[Dict[str, Any]]:
    with train_jsonl.open("r", encoding="utf-8") as f:
        filter_index = 0

        for source_line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue

            obj = json.loads(line)
            prompt, solution = basegen.split_prompt_body(obj.get("original_string", ""))

            if prompt is None or solution is None:
                continue

            if len(prompt.split()) < min_prompt_len:
                continue

            if len(prompt.split()) > max_prompt_len:
                continue

            if len(solution.split()) < min_solution_len:
                continue

            if len(solution.split()) > max_solution_len:
                continue

            yield {
                "prompt": prompt,
                "solution": solution,
                "source_line_no": source_line_no,
                "filter_index": filter_index,
                "repo": obj.get("repo", ""),
                "path": obj.get("path", ""),
                "func_name": obj.get("func_name", ""),
            }

            filter_index += 1


def build_generation_record(
    candidate: Dict[str, Any],
    raw_output: str,
    output: str,
    model_name: str,
    temperature: float,
) -> Dict[str, Any]:
    return {
        "prompt": candidate["prompt"],
        "output": output,
        "solution": candidate["solution"],
        "raw_output": raw_output,
        "model": model_name,
        "temperature": temperature,
        "source_line_no": candidate.get("source_line_no", ""),
        "filter_index": candidate.get("filter_index", ""),
        "repo": candidate.get("repo", ""),
        "path": candidate.get("path", ""),
        "func_name": candidate.get("func_name", ""),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate more valid MGC pairs for an existing AI-Detector CSV.",
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
        help=(
            "Target final number of valid pairs by default. "
            "With --additional, this is the number of new valid pairs to add."
        ),
    )

    parser.add_argument(
        "--additional",
        action="store_true",
        help="Treat num_datasets as additional valid pairs to add.",
    )

    parser.add_argument(
        "--codesearchnet-root",
        type=Path,
        default=Path("data/CodeSearchNet"),
        help="Path to CodeSearchNet root directory.",
    )
    parser.add_argument("--language", default="python")

    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output validsyntax directory.",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=None,
        help="Optional explicit output CSV path. Default: out-dir / existing_csv.name",
    )

    parser.add_argument("--model-name", default=basegen.DEFAULT_MODEL)
    parser.add_argument("--api-url", default=basegen.DEFAULT_API_URL)
    parser.add_argument("--api-key-env", default=basegen.DEFAULT_API_KEY_ENV)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--top-p", type=float, default=None)

    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=20)
    parser.add_argument("--retry-sleep", type=float, default=5.0)
    parser.add_argument("--retry-sleep-max", type=float, default=120.0)
    parser.add_argument("--retry-forever", action="store_true")

    parser.add_argument("--min-prompt-len", type=int, default=5)
    parser.add_argument("--max-prompt-len", type=int, default=128)
    parser.add_argument("--min-solution-len", type=int, default=5)
    parser.add_argument("--max-solution-len", type=int, default=256)

    parser.add_argument(
        "--max-api-calls",
        type=int,
        default=0,
        help="Safety limit for API calls. 0 means unlimited.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Revalidate existing CSV and print plan, but do not call API or write outputs.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    require_validsyntax_helpers()

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

    df_original = pd.read_csv(
        existing_csv,
        dtype={"idx": "string", "label": "string"},
    )

    original_pairs, max_line_num, original_hwc_hashes = validate_existing_pair_shape(
        df_original
    )

    df_valid_existing, df_invalid_existing = revalidate_existing_csv_pairs(df_original)

    current_valid_pairs = len(df_valid_existing) // 2
    invalid_existing_pairs = len(df_invalid_existing)

    if args.additional:
        target_pairs = current_valid_pairs + args.num_datasets
        needed_pairs = args.num_datasets
    else:
        target_pairs = args.num_datasets
        needed_pairs = target_pairs - current_valid_pairs

    print(f"original pairs before revalidation: {original_pairs}")
    print(f"valid existing pairs              : {current_valid_pairs}")
    print(f"invalid existing pairs removed    : {invalid_existing_pairs}")
    print(f"target pairs                      : {target_pairs}")
    print(f"needed new valid pairs            : {needed_pairs}")

    if needed_pairs <= 0:
        print("[INFO] No generation needed.")
        return 0

    if args.dry_run:
        print("[DRY-RUN] Stopping before backup/API/write.")
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
        print(f"[INFO] No existing out_dir to back up: {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    metadata_dir = out_dir / f"generate_more_metadata_{timestamp}"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    attempts_jsonl = metadata_dir / "generated_attempts.jsonl"
    valid_jsonl = metadata_dir / "generated_valid.jsonl"
    invalid_jsonl = metadata_dir / "generated_invalid.jsonl"
    invalid_existing_csv = metadata_dir / "existing_invalid_pairs.csv"
    summary_json = metadata_dir / "summary.json"

    if not df_invalid_existing.empty:
        df_invalid_existing.to_csv(invalid_existing_csv, index=False)
        print(f"[INFO] Existing invalid pairs written to: {invalid_existing_csv}")

    # Important: skip all HWC from the original CSV, not just valid existing rows.
    # This prevents generating a different MGC for an HWC already used before.
    seen_hwc_hashes = set(original_hwc_hashes)

    new_rows: List[Dict[str, str]] = []
    new_valid_pairs = 0
    api_calls = 0
    skipped_existing_hwc = 0
    skipped_bad_hwc = 0
    generated_invalid = 0

    next_line_num = max_line_num + 1

    for candidate in iter_codesearchnet_candidates(
        train_jsonl=train_jsonl,
        min_prompt_len=args.min_prompt_len,
        max_prompt_len=args.max_prompt_len,
        min_solution_len=args.min_solution_len,
        max_solution_len=args.max_solution_len,
    ):
        if new_valid_pairs >= needed_pairs:
            break

        if args.max_api_calls > 0 and api_calls >= args.max_api_calls:
            print(f"[WARN] Reached --max-api-calls={args.max_api_calls}")
            break

        prompt = candidate["prompt"]
        solution = candidate["solution"]
        hwc_code = validsyntax.compose_code(prompt, solution)
        hwc_hash = stable_code_hash(hwc_code)

        if hwc_hash in seen_hwc_hashes:
            skipped_existing_hwc += 1
            continue

        hwc_syntax = validsyntax.syntax_check(hwc_code)
        if not hwc_syntax.ok:
            skipped_bad_hwc += 1
            seen_hwc_hashes.add(hwc_hash)
            continue

        hwc_structure_ok, _ = validsyntax.code_has_required_structure(hwc_code)
        if not hwc_structure_ok:
            skipped_bad_hwc += 1
            seen_hwc_hashes.add(hwc_hash)
            continue

        print(
            f"[GEN] source_line_no={candidate['source_line_no']} "
            f"new_valid={new_valid_pairs}/{needed_pairs} "
            f"api_calls={api_calls}"
        )

        response_json = basegen.request_chat_completion(
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

        raw_output = basegen.extract_content(response_json)
        output = basegen.extract_body(raw_output, prompt)

        attempt_record = build_generation_record(
            candidate=candidate,
            raw_output=raw_output,
            output=output,
            model_name=args.model_name,
            temperature=args.temperature,
        )
        append_jsonl(attempts_jsonl, attempt_record)

        sample = validsyntax.process_obj(
            {
                "prompt": prompt,
                "output": output,
                "solution": solution,
                "source_line_no": candidate.get("source_line_no", ""),
                "filter_index": candidate.get("filter_index", ""),
                "repo": candidate.get("repo", ""),
                "path": candidate.get("path", ""),
                "func_name": candidate.get("func_name", ""),
            },
            line_no=int(candidate["source_line_no"]),
        )

        if not (sample.status in VALID_STATUSES and sample.hwc_ok):
            generated_invalid += 1

            invalid_record = dict(attempt_record)
            invalid_record.update(
                {
                    "status": sample.status,
                    "raw_mgc_ok": sample.raw_mgc_ok,
                    "clean_mgc_ok": sample.clean_mgc_ok,
                    "hwc_ok": sample.hwc_ok,
                    "raw_mgc_error": sample.raw_mgc_error,
                    "clean_mgc_error": sample.clean_mgc_error,
                    "hwc_error": sample.hwc_error,
                }
            )
            append_jsonl(invalid_jsonl, invalid_record)

            seen_hwc_hashes.add(hwc_hash)
            continue

        pair_id = f"line{next_line_num}"
        next_line_num += 1

        new_rows.append(
            {
                "idx": f"{pair_id}_human",
                "code": sample.hwc_code,
                "label": "human",
            }
        )
        new_rows.append(
            {
                "idx": f"{pair_id}_lm",
                "code": sample.mgc_code,
                "label": "lm",
            }
        )

        valid_record = asdict(sample)
        valid_record.update(
            {
                "new_pair_id": pair_id,
                "repo": candidate.get("repo", ""),
                "path": candidate.get("path", ""),
                "func_name": candidate.get("func_name", ""),
            }
        )
        append_jsonl(valid_jsonl, valid_record)

        seen_hwc_hashes.add(hwc_hash)
        new_valid_pairs += 1

        print(f"[OK] Added {pair_id}; new_valid={new_valid_pairs}/{needed_pairs}")

    if new_valid_pairs < needed_pairs:
        print(
            f"[WARN] Only generated {new_valid_pairs}/{needed_pairs} needed valid pairs.",
            file=sys.stderr,
        )

    df_new = pd.DataFrame(new_rows, columns=["idx", "code", "label"])
    df_out = pd.concat(
        [df_valid_existing[["idx", "code", "label"]], df_new],
        ignore_index=True,
    )

    final_pairs = len(df_out) // 2

    out_csv = args.out_csv.expanduser().resolve() if args.out_csv else (out_dir / existing_csv.name)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    tmp_csv = out_csv.with_suffix(out_csv.suffix + ".tmp")
    df_out.to_csv(tmp_csv, index=False)
    tmp_csv.replace(out_csv)

    summary = {
        "existing_csv": str(existing_csv),
        "out_csv": str(out_csv),
        "out_dir": str(out_dir),
        "backup_dir": str(backup_dir) if backup_dir else "",
        "metadata_dir": str(metadata_dir),
        "original_pairs_before_revalidation": original_pairs,
        "valid_existing_pairs": current_valid_pairs,
        "invalid_existing_pairs_removed": invalid_existing_pairs,
        "target_pairs": target_pairs,
        "needed_pairs": needed_pairs,
        "new_valid_pairs": new_valid_pairs,
        "final_pairs": final_pairs,
        "api_calls": api_calls,
        "skipped_existing_hwc": skipped_existing_hwc,
        "skipped_bad_hwc": skipped_bad_hwc,
        "generated_invalid": generated_invalid,
        "attempts_jsonl": str(attempts_jsonl),
        "valid_jsonl": str(valid_jsonl),
        "invalid_jsonl": str(invalid_jsonl),
        "invalid_existing_csv": str(invalid_existing_csv),
    }

    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print("Done")
    print("=" * 72)
    print(f"backup_dir                  : {backup_dir}")
    print(f"output_csv                  : {out_csv}")
    print(f"metadata_dir                : {metadata_dir}")
    print(f"original_pairs              : {original_pairs}")
    print(f"valid_existing_pairs        : {current_valid_pairs}")
    print(f"invalid_existing_pairs      : {invalid_existing_pairs}")
    print(f"new_valid_pairs             : {new_valid_pairs}")
    print(f"final_pairs                 : {final_pairs}")
    print(f"api_calls                   : {api_calls}")
    print(f"skipped_existing_hwc        : {skipped_existing_hwc}")
    print(f"skipped_bad_hwc             : {skipped_bad_hwc}")
    print(f"generated_invalid           : {generated_invalid}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
