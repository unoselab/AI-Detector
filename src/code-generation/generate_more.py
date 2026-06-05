#!/usr/bin/env python3
"""generate-more-local.py

Local-GPU (transformers) counterpart of generate-more.py, for models that were
generated locally (e.g. StarCoder2-7b) rather than via an OpenAI-compatible API.

It REUSES the project's own logic instead of reimplementing it:
  - code_generation.find_validsyntax_mgc : process_obj, compose_code, syntax_check,
        normalize_newlines, and (crucially) code_has_required_structure  -- the
        empty-body / docstring-only gate that is the whole point of this run.
  - code_generation.generate            : truncate(), and the EXACT StarCoder2
        generation procedure from generate_hf() (starcoder branch), refactored so
        the 7B model/tokenizer is loaded ONCE and reused across all candidates
        (generate_hf reloads the model on every call, which is unusable here).

The only behavioural difference vs generate-more.py is the generation backend:
local-GPU StarCoder2 instead of HTTP. Generation settings mirror the original run
that built *_merged_4500.csv:
    model=bigcode/starcoder2-7b, temperature=0.2, top_p=0.95,
    max_length(prompt cap)=128, max_length_sample=512  (=> eos_id_list branch),
    do_sample=True, batch_size=1 (per-prompt, exactly like generate_hf's starcoder path).

Empty-body / docstring-only functions are excluded on BOTH sides via
code_has_required_structure. Because revalidate_existing_csv_pairs() applies the
same gate, simply targeting the original pair count (e.g. 4500) will drop the
empty-body pairs and regenerate exactly that many replacements.

Example
-------
  cd ~/project-workspace/ai_detector
  CUDA_VISIBLE_DEVICES=0 python src/code-generate-llm/generate_more.py \
      src/code-analyzer-tree-sitter/data_codesearchnet/starcoder2-7b/validsyntax_4500_complexity/codesearchnet_starcoder2-7b_python_merged_4500.csv \
      4500 \
      --codesearchnet-root data/CodeSearchNet \
      --model-name bigcode/starcoder2-7b \
      --temperature 0.2 --top-p 0.95 --max-length 128 --max-length-sample 512
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

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def print(*args, **kwargs):  # noqa: A001 - timestamped, flushed logging
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    kwargs.setdefault("flush", True)
    builtins.print(timestamp, *args, **kwargs)


# ---------------------------------------------------------------------------
# Import shared project modules (same package as generate-more.py reuses).
# ---------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[1]          # .../src
THIS_DIR = THIS_FILE.parent

for p in (str(SRC_DIR), str(THIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Package-qualified imports so we get code_generation/generate.py (local-GPU),
# NOT code-generate-llm/generate.py (HTTP). Both are named `generate`.
from code_generation import find_validsyntax_mgc as validsyntax  # noqa: E402
from code_generation import generate as gen  # noqa: E402

# Heavy deps are imported lazily inside load_local_model() so that --dry-run and
# CSV revalidation work on a box without a GPU / torch.

VALID_STATUSES = {"raw_valid", "salvaged_valid"}


# ---------------------------------------------------------------------------
# Small helpers (reused from generate-more.py)
# ---------------------------------------------------------------------------
def require_validsyntax_helpers() -> None:
    required = ["process_obj", "compose_code", "syntax_check", "code_has_required_structure"]
    missing = [name for name in required if not hasattr(validsyntax, name)]
    if missing:
        raise RuntimeError(
            "find_validsyntax_mgc.py is missing required helpers: " + ", ".join(missing)
            + "\nAdd code_has_required_structure() to find_validsyntax_mgc.py first."
        )


def normalize_code_for_hash(code: Any) -> str:
    return validsyntax.normalize_newlines(code).strip()


def stable_code_hash(code: Any) -> str:
    return hashlib.sha256(normalize_code_for_hash(code).encode("utf-8")).hexdigest()


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
    return idx[:-len(suffix)] if idx.endswith(suffix) else idx


def extract_line_number(pair_id: str) -> Optional[int]:
    m = re.search(r"line(\d+)$", str(pair_id))
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Existing CSV validation / revalidation (reused from generate-more.py)
# ---------------------------------------------------------------------------
def validate_existing_pair_shape(df: pd.DataFrame) -> Tuple[int, int, set]:
    required = {"idx", "code", "label"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {sorted(required)}")
    if len(df) % 2 != 0:
        raise ValueError(f"CSV has odd row count: {len(df)}")

    seen_pair_ids, all_hwc_hashes, max_line_num = set(), set(), 0
    for i in range(0, len(df), 2):
        human, lm = df.iloc[i], df.iloc[i + 1]
        human_idx, lm_idx = str(human["idx"]).strip(), str(lm["idx"]).strip()
        if not human_idx.endswith("_human"):
            raise ValueError(f"Row {i} is not a human row: {human_idx}")
        if not lm_idx.endswith("_lm"):
            raise ValueError(f"Row {i + 1} is not an lm row: {lm_idx}")
        if str(human["label"]).strip() != "human":
            raise ValueError(f"Row {i} label should be human")
        if str(lm["label"]).strip() != "lm":
            raise ValueError(f"Row {i + 1} label should be lm")
        h_base = pair_base_from_idx(human_idx, "_human")
        l_base = pair_base_from_idx(lm_idx, "_lm")
        if h_base != l_base:
            raise ValueError(f"Pair mismatch at rows {i}-{i + 1}: {human_idx}, {lm_idx}")
        if h_base in seen_pair_ids:
            raise ValueError(f"Duplicate pair id: {h_base}")
        seen_pair_ids.add(h_base)
        all_hwc_hashes.add(stable_code_hash(human["code"]))
        ln = extract_line_number(h_base)
        if ln is not None:
            max_line_num = max(max_line_num, ln)
    return len(seen_pair_ids), max_line_num, all_hwc_hashes


def code_is_valid_for_dataset(code: str) -> Tuple[bool, str]:
    res = validsyntax.syntax_check(code)
    if not res.ok:
        return False, res.error
    return validsyntax.code_has_required_structure(code)


def revalidate_existing_csv_pairs(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    valid_rows: List[Dict[str, str]] = []
    invalid_records: List[Dict[str, str]] = []
    for i in range(0, len(df), 2):
        human, lm = df.iloc[i], df.iloc[i + 1]
        human_idx, lm_idx = str(human["idx"]).strip(), str(lm["idx"]).strip()
        human_code, lm_code = str(human["code"]), str(lm["code"])
        human_ok, human_err = code_is_valid_for_dataset(human_code)
        lm_ok, lm_err = code_is_valid_for_dataset(lm_code)
        errors = []
        if not human_ok:
            errors.append(f"HWC: {human_err}")
        if not lm_ok:
            errors.append(f"MGC: {lm_err}")
        if errors:
            invalid_records.append({"human_idx": human_idx, "lm_idx": lm_idx,
                                    "errors": " | ".join(errors),
                                    "human_code": human_code, "lm_code": lm_code})
            continue
        valid_rows.append({"idx": human_idx, "code": human_code, "label": "human"})
        valid_rows.append({"idx": lm_idx, "code": lm_code, "label": "lm"})
    valid_df = pd.DataFrame(valid_rows, columns=["idx", "code", "label"])
    invalid_df = pd.DataFrame(invalid_records,
                              columns=["human_idx", "lm_idx", "errors", "human_code", "lm_code"])
    return valid_df, invalid_df


# ---------------------------------------------------------------------------
# CodeSearchNet candidate scanning
# Replicates generate.load_data()'s prompt/solution split EXACTLY so new pairs
# are constructed identically to the original CSV:
#   original_string.replace("'''", '"""'); prompt = [0]+'"""'+[1]+'"""'; solution=[2]
# with prompt words in [5,128] and solution words in [5,256].
# ---------------------------------------------------------------------------
def iter_codesearchnet_candidates(train_jsonl: Path,
                                  min_prompt_len: int, max_prompt_len: int,
                                  min_solution_len: int, max_solution_len: int) -> Iterable[Dict[str, Any]]:
    with train_jsonl.open("r", encoding="utf-8") as f:
        filter_index = 0
        for source_line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            original = str(data.get("original_string", "")).replace("'''", '"""')
            parts = original.split('"""')
            if len(parts) < 3:
                continue
            prompt = parts[0] + '"""' + parts[1] + '"""'
            solution = parts[2]
            if not (min_prompt_len <= len(prompt.split()) <= max_prompt_len):
                continue
            if not (min_solution_len <= len(solution.split()) <= max_solution_len):
                continue
            yield {
                "prompt": prompt,
                "solution": solution,
                "source_line_no": source_line_no,
                "filter_index": filter_index,
                "repo": data.get("repo", ""),
                "path": data.get("path", ""),
                "func_name": data.get("func_name", ""),
            }
            filter_index += 1


# ---------------------------------------------------------------------------
# Local-GPU generation (load model ONCE; body copied from generate_hf's
# starcoder branch, with gen.truncate reused verbatim).
# ---------------------------------------------------------------------------
def load_local_model(model_name: str):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    device = gen.device  # reuse the same device object generate.py uses

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    # starcoder/llama/wizard branch in generate_hf applies no special pad override.

    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, torch_dtype=torch.float16,
    ).to(device)

    def_id = tokenizer("def", add_special_tokens=False).input_ids[0]
    try:
        def_with_space_id = tokenizer("def", add_prefix_space=True, add_special_tokens=False).input_ids[0]
    except Exception:
        def_with_space_id = tokenizer(" def", add_special_tokens=False).input_ids[0]
    eos_id_list = [tokenizer.eos_token_id, def_id, def_with_space_id]
    print(f"[INFO] eos_id_list: {eos_id_list}")
    return model, tokenizer, eos_id_list, device


def generate_one(prompt: str, model, tokenizer, eos_id_list, device,
                 max_length: int, max_length_sample: int,
                 do_sample: bool, top_p: float, temperature: float) -> str:
    """One prompt -> body (continuation, prompt stripped, truncated). Mirrors generate_hf."""
    enc = tokenizer(prompt, return_tensors="pt", truncation=True,
                    max_length=max_length, return_attention_mask=True)
    input_ids = enc.input_ids.to(device)
    attention_mask = enc.attention_mask.to(device)
    input_ids_len = input_ids.shape[1]

    gen_kwargs = dict(
        attention_mask=attention_mask,
        do_sample=do_sample,
        max_length=max_length_sample + input_ids_len,
        top_p=top_p,
        temperature=temperature,
        pad_token_id=tokenizer.eos_token_id,
        use_cache=True,
    )
    if max_length_sample >= 256:
        gen_kwargs["eos_token_id"] = eos_id_list  # same branch as the original run

    outputs = model.generate(input_ids, **gen_kwargs)
    decoded = tokenizer.decode(outputs[0, input_ids_len:])
    return gen.truncate(decoded)  # reuse the project's <|endoftext|> truncation


def build_generation_record(candidate, raw_output, output, model_name, temperature):
    return {
        "prompt": candidate["prompt"], "output": output, "solution": candidate["solution"],
        "raw_output": raw_output, "model": model_name, "temperature": temperature,
        "source_line_no": candidate.get("source_line_no", ""),
        "filter_index": candidate.get("filter_index", ""),
        "repo": candidate.get("repo", ""), "path": candidate.get("path", ""),
        "func_name": candidate.get("func_name", ""),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate more valid MGC pairs (local-GPU) for an existing CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("existing_csv", type=Path, help="Path to existing paired CSV.")
    p.add_argument("num_datasets", type=int,
                   help="Target final valid-pair count (default mode), or with "
                        "--additional, the number of NEW pairs to add.")
    p.add_argument("--additional", action="store_true",
                   help="Treat num_datasets as additional pairs to add.")
    p.add_argument("--codesearchnet-root", type=Path, default=Path("data/CodeSearchNet"))
    p.add_argument("--language", default="python")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="Output validsyntax dir. Default: existing_csv's parent dir.")
    p.add_argument("--out-csv", type=Path, default=None,
                   help="Explicit output CSV. Default: out-dir / existing_csv.name")
    # local generation settings (match the original StarCoder2 run)
    p.add_argument("--model-name", default="bigcode/starcoder2-7b")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--max-length", type=int, default=128, help="Prompt truncation cap.")
    p.add_argument("--max-length-sample", type=int, default=512, help="Generation budget.")
    p.add_argument("--no-sample", action="store_true", help="Disable sampling (greedy).")
    # candidate filters (match generate.load_data)
    p.add_argument("--min-prompt-len", type=int, default=5)
    p.add_argument("--max-prompt-len", type=int, default=128)
    p.add_argument("--min-solution-len", type=int, default=5)
    p.add_argument("--max-solution-len", type=int, default=256)
    p.add_argument("--max-candidates", type=int, default=0,
                   help="Safety cap on candidates scanned. 0 = unlimited.")
    p.add_argument("--dry-run", action="store_true",
                   help="Revalidate existing CSV + print plan; no model load / no write.")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    require_validsyntax_helpers()
    args = parse_args()

    existing_csv = args.existing_csv.expanduser().resolve()
    out_dir = (args.out_dir.expanduser().resolve() if args.out_dir
               else existing_csv.parent)

    if not existing_csv.exists():
        print(f"[ERROR] existing CSV not found: {existing_csv}", file=sys.stderr)
        return 2

    train_jsonl = (args.codesearchnet_root.expanduser().resolve()
                   / args.language / "train.jsonl")
    if not train_jsonl.exists():
        print(f"[ERROR] CodeSearchNet train.jsonl not found: {train_jsonl}", file=sys.stderr)
        return 2

    print("=" * 72)
    print("generate-more-local.py")
    print("=" * 72)
    print(f"existing_csv : {existing_csv}")
    print(f"train_jsonl  : {train_jsonl}")
    print(f"out_dir      : {out_dir}")
    print(f"model        : {args.model_name}")
    print(f"temperature  : {args.temperature}  top_p: {args.top_p}  "
          f"max_length: {args.max_length}  max_length_sample: {args.max_length_sample}")

    df_original = pd.read_csv(existing_csv, dtype={"idx": "string", "label": "string"})
    original_pairs, max_line_num, original_hwc_hashes = validate_existing_pair_shape(df_original)
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
        print("[DRY-RUN] Stopping before model load / generation / write.")
        return 0

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = make_backup(out_dir, timestamp)
    print(f"[INFO] Backup: {backup_dir}" if backup_dir else f"[INFO] No out_dir to back up: {out_dir}")
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
        print(f"[INFO] Existing invalid pairs -> {invalid_existing_csv}")

    # Load the 7B model ONCE and reuse it for every candidate.
    print("[INFO] Loading local model (once)...")
    model, tokenizer, eos_id_list, device = load_local_model(args.model_name)

    seen_hwc_hashes = set(original_hwc_hashes)  # never reuse an HWC already in the CSV
    new_rows: List[Dict[str, str]] = []
    new_valid_pairs = 0
    candidates_scanned = 0
    skipped_existing_hwc = 0
    skipped_bad_hwc = 0
    generated_invalid = 0
    structure_rejected = 0
    next_line_num = max_line_num + 1

    for candidate in iter_codesearchnet_candidates(
        train_jsonl, args.min_prompt_len, args.max_prompt_len,
        args.min_solution_len, args.max_solution_len,
    ):
        if new_valid_pairs >= needed_pairs:
            break
        candidates_scanned += 1
        if args.max_candidates > 0 and candidates_scanned > args.max_candidates:
            print(f"[WARN] Reached --max-candidates={args.max_candidates}")
            break

        prompt = candidate["prompt"]
        solution = candidate["solution"]
        hwc_code = validsyntax.compose_code(prompt, solution)
        hwc_hash = stable_code_hash(hwc_code)

        if hwc_hash in seen_hwc_hashes:
            skipped_existing_hwc += 1
            continue

        # Pre-gen HWC gate: skip before spending a GPU generation.
        hwc_syntax = validsyntax.syntax_check(hwc_code)
        hwc_struct_ok, _ = (False, "") if not hwc_syntax.ok else validsyntax.code_has_required_structure(hwc_code)
        if not (hwc_syntax.ok and hwc_struct_ok):
            skipped_bad_hwc += 1
            seen_hwc_hashes.add(hwc_hash)
            continue

        print(f"[GEN] src_line={candidate['source_line_no']} "
              f"new_valid={new_valid_pairs}/{needed_pairs} scanned={candidates_scanned}")

        raw_output = generate_one(
            prompt, model, tokenizer, eos_id_list, device,
            max_length=args.max_length, max_length_sample=args.max_length_sample,
            do_sample=(not args.no_sample), top_p=args.top_p, temperature=args.temperature,
        )

        sample = validsyntax.process_obj(
            {
                "prompt": prompt, "output": raw_output, "solution": solution,
                "source_line_no": candidate.get("source_line_no", ""),
                "filter_index": candidate.get("filter_index", ""),
                "repo": candidate.get("repo", ""), "path": candidate.get("path", ""),
                "func_name": candidate.get("func_name", ""),
            },
            line_no=int(candidate["source_line_no"]),
        )

        attempt_record = build_generation_record(candidate, raw_output, sample.clean_output,
                                                  args.model_name, args.temperature)
        append_jsonl(attempts_jsonl, attempt_record)

        # Validity gate 1: syntax/status + HWC parse (same as generate-more.py).
        if not (sample.status in VALID_STATUSES and sample.hwc_ok):
            generated_invalid += 1
            rec = dict(attempt_record)
            rec.update({"status": sample.status, "raw_mgc_ok": sample.raw_mgc_ok,
                        "clean_mgc_ok": sample.clean_mgc_ok, "hwc_ok": sample.hwc_ok,
                        "reject": "invalid_syntax_or_status"})
            append_jsonl(invalid_jsonl, rec)
            seen_hwc_hashes.add(hwc_hash)
            continue

        # Validity gate 2 (the point of this run): exclude empty-body / docstring-only
        # on BOTH the final MGC and HWC code.
        mgc_struct_ok, mgc_reason = validsyntax.code_has_required_structure(sample.mgc_code)
        hwc_struct_ok2, hwc_reason = validsyntax.code_has_required_structure(sample.hwc_code)
        if not (mgc_struct_ok and hwc_struct_ok2):
            structure_rejected += 1
            rec = dict(attempt_record)
            rec.update({"status": sample.status, "reject": "empty_body_or_docstring_only",
                        "mgc_reason": mgc_reason, "hwc_reason": hwc_reason})
            append_jsonl(invalid_jsonl, rec)
            seen_hwc_hashes.add(hwc_hash)
            continue

        pair_id = f"line{next_line_num}"
        next_line_num += 1
        new_rows.append({"idx": f"{pair_id}_human", "code": sample.hwc_code, "label": "human"})
        new_rows.append({"idx": f"{pair_id}_lm", "code": sample.mgc_code, "label": "lm"})

        valid_record = asdict(sample)
        valid_record.update({"new_pair_id": pair_id, "repo": candidate.get("repo", ""),
                             "path": candidate.get("path", ""), "func_name": candidate.get("func_name", "")})
        append_jsonl(valid_jsonl, valid_record)

        seen_hwc_hashes.add(hwc_hash)
        new_valid_pairs += 1
        print(f"[OK] {pair_id}; new_valid={new_valid_pairs}/{needed_pairs}")

    if new_valid_pairs < needed_pairs:
        print(f"[WARN] Only generated {new_valid_pairs}/{needed_pairs} needed pairs.",
              file=sys.stderr)

    df_new = pd.DataFrame(new_rows, columns=["idx", "code", "label"])
    df_out = pd.concat([df_valid_existing[["idx", "code", "label"]], df_new], ignore_index=True)
    final_pairs = len(df_out) // 2

    out_csv = (args.out_csv.expanduser().resolve() if args.out_csv else (out_dir / existing_csv.name))
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp_csv = out_csv.with_suffix(out_csv.suffix + ".tmp")
    df_out.to_csv(tmp_csv, index=False)
    tmp_csv.replace(out_csv)

    summary = {
        "existing_csv": str(existing_csv), "out_csv": str(out_csv), "out_dir": str(out_dir),
        "backup_dir": str(backup_dir) if backup_dir else "", "metadata_dir": str(metadata_dir),
        "model_name": args.model_name, "temperature": args.temperature, "top_p": args.top_p,
        "max_length": args.max_length, "max_length_sample": args.max_length_sample,
        "original_pairs_before_revalidation": original_pairs,
        "valid_existing_pairs": current_valid_pairs,
        "invalid_existing_pairs_removed": invalid_existing_pairs,
        "target_pairs": target_pairs, "needed_pairs": needed_pairs,
        "new_valid_pairs": new_valid_pairs, "final_pairs": final_pairs,
        "candidates_scanned": candidates_scanned,
        "skipped_existing_hwc": skipped_existing_hwc, "skipped_bad_hwc": skipped_bad_hwc,
        "generated_invalid": generated_invalid, "structure_rejected": structure_rejected,
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print("Done")
    print("=" * 72)
    for k, v in summary.items():
        print(f"{k:>34} : {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
