#!/usr/bin/env python3
"""CodeLlama-7B T=0.0 pilot on the ORIGINAL 4,500 complexity-balanced pairs.

Inputs (read-only):
    original paired CSV: idx,code,label (4,500 human/lm pairs)
    complexity-stratified split manifest: pair_id,complexity_block,split,...
    existing find_validsyntax_mgc.py: shared syntax, cleaning, and structure rules
    Hugging Face model weights: codellama/CodeLlama-7b-hf

Outputs (new output directory only):
    pilot_selection.csv          Selected pair IDs, original splits/complexity
    pilot_prepared.jsonl         Original prompts and paired HWC/AGC provenance
    pilot_generation.jsonl       Append-only original greedy generations and QC
    pilot_pairs_valid.csv        Only the VALID new paired HWC/T=0.0 AGC rows
    pilot_qc.csv                 One row per attempted pair, including invalids
    pilot_summary.json          QC, runtime and configuration record
    pilot_findings.txt          Human-readable findings
    experiment_config.json      Input hashes and exact generation settings

The original generation algorithm is mirrored from the local-GPU
code-generation/generate.py and code-generation/generate_more.py. Only decoding
changes: do_sample=False and sampling-only temperature/top_p are NOT passed to
model.generate(). This script does not modify old scripts or source datasets.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-pairs", required=True, type=Path)
    parser.add_argument("--split-manifest", required=True, type=Path)
    parser.add_argument("--validator-script", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model-name", default="codellama/CodeLlama-7b-hf")
    parser.add_argument("--pilot-pairs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42, help="Complexity-block selection seed only.")
    parser.add_argument("--prompt-max-tokens", type=int, default=128)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--min-valid-rate", type=float, default=0.70)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    return parser.parse_args()


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_json(path: Path, data: Any) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_rows(path: Path, rows: list[dict], columns: list[str]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def write_jsonl(path: Path, records: list[dict]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    tmp.replace(path)


def append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        import os
        os.fsync(f.fileno())


def load_jsonl(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    fail(f"Malformed checkpoint JSONL at {path}:{n}: {exc}")
    return records


def read_csv(path: Path) -> list[dict]:
    csv.field_size_limit(sys.maxsize)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pair_id_from_idx(idx: str) -> str:
    m = re.fullmatch(r"(.+)_(human|lm)", idx)
    if not m:
        fail(f"Unexpected original paired CSV index: {idx!r}")
    return m.group(1)


def load_original_pairs(path: Path, expected_count: int) -> dict[str, dict]:
    rows = read_csv(path)
    original: dict[str, dict] = {}
    for row in rows:
        idx = row.get("idx", "")
        pair_id = pair_id_from_idx(idx)
        label = row.get("label", "")
        suffix = idx.rsplit("_", 1)[-1]
        if (suffix, label) not in (("human", "human"), ("lm", "lm")):
            fail(f"Index/label mismatch for {idx}: {label}")
        original.setdefault(pair_id, {})[label] = row["code"]
    if len(rows) != 2 * expected_count or len(original) != expected_count:
        fail(f"Original pairs expected {expected_count}, got {len(rows)} rows / {len(original)} pairs")
    if any(set(p) != {"human", "lm"} for p in original.values()):
        fail("Each original pair must contain exactly one human and one lm entry")
    return original


def load_manifest(path: Path, expected_count: int) -> tuple[list[dict], dict[int, list[dict]]]:
    rows = read_csv(path)
    if len(rows) != expected_count:
        fail(f"Split manifest has {len(rows)} rows (expected {expected_count})")
    if len({r["pair_id"] for r in rows}) != expected_count:
        fail("Split manifest contains duplicate pair IDs")
    blocks: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("split") not in ("train", "dev", "test"):
            fail(f"Unknown split: {row}")
        blocks[int(row["complexity_block"])].append(row)
    if len(blocks) * 10 != expected_count:
        fail("Expected full 10-pair complexity blocks")
    for block, items in blocks.items():
        counts = Counter(r["split"] for r in items)
        if len(items) != 10 or counts != {"train": 8, "dev": 1, "test": 1}:
            fail(f"Invalid manifest block={block}: count={dict(counts)}")
    return rows, blocks


def select_pilot_blocks(blocks: dict[int, list[dict]], n_pairs: int, seed: int) -> list[dict]:
    if n_pairs < 10 or n_pairs % 10:
        fail("--pilot-pairs must be a positive multiple of 10")
    n_blocks = n_pairs // 10
    ordered = sorted(blocks)
    if n_blocks > len(ordered):
        fail("Pilot exceeds the number of available complexity blocks")
    # Pick one block from each complexity quantile for the 100-pair pilot.
    # General n: stratify all blocks into n equally-sized ranges, pick one per range.
    rng = random.Random(seed)
    chosen = []
    for i in range(n_blocks):
        begin = i * len(ordered) // n_blocks
        end = (i + 1) * len(ordered) // n_blocks
        chosen.append(rng.choice(ordered[begin:end]))
    selected = []
    for b in chosen:
        selected.extend(sorted(blocks[b], key=lambda r: (r["split"], r["pair_id"])))
    if Counter(x["split"] for x in selected) != {
        "train": n_blocks * 8, "dev": n_blocks, "test": n_blocks
    }:
        fail("Selected pilot did not preserve original split allocation")
    return selected


def extract_prompt(human_code: str, old_agc_code: str, pair_id: str) -> tuple[str, str]:
    """Recover the exact normalized signature/docstring prefix from HWC syntax.

    The source pipeline concatenates prompt + human solution (and independently
    prompt + old machine output). Verify this common-prefix property explicitly;
    never invent a new prompt or silently match a different procedure.
    """
    human = human_code.replace("\r\n", "\n").replace("\r", "\n")
    old_agc = old_agc_code.replace("\r\n", "\n").replace("\r", "\n")
    tree = ast.parse(human)
    blocks = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if len(blocks) != 1 or len(tree.body) != 1:
        fail(f"{pair_id}: expected exactly one top-level function/class")
    block = blocks[0]
    if not block.body or not isinstance(block.body[0], ast.Expr):
        fail(f"{pair_id}: leading docstring AST node missing")
    expr = block.body[0]
    if not (isinstance(expr.value, ast.Constant) and isinstance(expr.value.value, str)):
        fail(f"{pair_id}: first body statement is not a docstring")
    # Python AST col_offset is a BYTE offset; decode UTF-8 before string slicing.
    lines = human.splitlines(keepends=True)
    end_row = expr.end_lineno - 1
    end_byte = expr.end_col_offset
    char_col = len(lines[end_row].encode("utf-8")[:end_byte].decode("utf-8"))
    cut = sum(len(line) for line in lines[:end_row]) + char_col
    prompt = human[:cut]
    solution = human[cut:]
    if not prompt or not solution.strip() or not old_agc.startswith(prompt):
        fail(f"{pair_id}: original HWC and AGC do not share the recovered prompt prefix")
    if not prompt.lstrip().startswith(("def ", "async def ", "class ", "@")):
        fail(f"{pair_id}: unexpected prompt start")
    return prompt, solution


def import_validator(path: Path):
    # Reuse the project's existing Python validation functions, not its wrappers.
    name = "run_x_02_original_validsyntax"
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        fail(f"Cannot import original validator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    for required in ("process_obj", "syntax_check", "code_has_required_structure", "compose_code"):
        if not hasattr(module, required):
            fail(f"Original validator does not provide {required}")
    return module


def load_model(model_name: str, local_files_only: bool):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available():
        fail("CUDA GPU is required for CodeLlama-7B pilot")
    print(f"[CUDA] available GPUs={torch.cuda.device_count()}; visible device=cuda:0", flush=True)
    print(f"[CUDA] GPU name={torch.cuda.get_device_name(0)}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_files_only)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    print(f"[INFO] Loading {model_name} in float16 on cuda:0", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, torch_dtype=torch.float16,
        local_files_only=local_files_only,
    ).to("cuda:0")
    model.eval()
    def_id = tokenizer("def", add_special_tokens=False).input_ids[0]
    try:
        def_space_id = tokenizer("def", add_prefix_space=True, add_special_tokens=False).input_ids[0]
    except Exception:
        def_space_id = tokenizer(" def", add_special_tokens=False).input_ids[0]
    eos_ids = list(dict.fromkeys(x for x in [tokenizer.eos_token_id, def_id, def_space_id] if x is not None))
    print(f"[INFO] Reusing original eos token IDs: {eos_ids}", flush=True)
    return model, tokenizer, eos_ids, torch


def generate_one(model, tokenizer, eos_ids, torch, prompt: str, prompt_cap: int, max_new: int):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True,
                       max_length=prompt_cap, return_attention_mask=True)
    input_ids = inputs.input_ids.to("cuda:0")
    attention_mask = inputs.attention_mask.to("cuda:0")
    with torch.inference_mode():
        result = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            max_new_tokens=max_new,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=eos_ids,
            use_cache=True,
        )
    continuation_tokens = result[0, input_ids.shape[1]:]
    output = tokenizer.decode(continuation_tokens, skip_special_tokens=False)
    # The original generate.py truncate() trims its trailing special EOT marker.
    output = output.split("<|endoftext|>", 1)[0]
    return output, int(input_ids.shape[1]), int(continuation_tokens.shape[0])


def validate_attempt(validator, record: dict, raw_output: str, input_tokens: int, generated_tokens: int,
                     seconds: float, model_name: str) -> dict:
    process = validator.process_obj({
        "prompt": record["prompt"], "output": raw_output, "solution": record["solution"],
        "source_line_no": "", "filter_index": ""
    }, line_no=1)
    new_code = process.mgc_code
    new_syntax = validator.syntax_check(new_code)
    structure_ok = False
    structure_reason = "syntax invalid"
    if new_syntax.ok:
        structure_ok, structure_reason = validator.code_has_required_structure(new_code)
    human_reproduced = process.hwc_code == record["human_code"]
    status = ("VALID" if (process.status in {"raw_valid", "salvaged_valid"}
                          and process.hwc_ok and new_syntax.ok
                          and structure_ok and human_reproduced) else "INVALID")
    return {
        "pair_id": record["pair_id"], "split": record["split"],
        "complexity_block": record["complexity_block"],
        "model": model_name, "temperature": 0.0, "do_sample": False,
        "top_p": None, "prompt_sha256": record["prompt_sha256"],
        "raw_output": raw_output, "clean_output": process.clean_output,
        "new_agc_code": new_code, "new_agc_sha256": hash_text(new_code),
        "status": status, "original_pipeline_status": process.status,
        "raw_mgc_ok": bool(process.raw_mgc_ok),
        "clean_mgc_ok": bool(process.clean_mgc_ok),
        "structure_ok": bool(structure_ok), "structure_reason": structure_reason,
        "human_reproduced": bool(human_reproduced),
        "input_tokens": input_tokens, "generated_tokens": generated_tokens,
        "seconds": round(seconds, 4),
    }


def emit_final(args, prepared: list[dict], completions: list[dict], config: dict) -> dict:
    by_id = {r["pair_id"]: r for r in completions}
    pairs, qc = [], []
    for original in prepared:
        item = by_id.get(original["pair_id"])
        if item is None:
            continue
        qc.append({
            "pair_id": item["pair_id"], "split": original["split"],
            "complexity_block": original["complexity_block"],
            "status": item["status"], "pipeline_status": item["original_pipeline_status"],
            "raw_mgc_ok": item["raw_mgc_ok"], "clean_mgc_ok": item["clean_mgc_ok"],
            "structure_ok": item["structure_ok"], "structure_reason": item["structure_reason"],
            "human_reproduced": item["human_reproduced"],
            "input_tokens": item["input_tokens"], "generated_tokens": item["generated_tokens"],
            "seconds": item["seconds"],
        })
        if item["status"] == "VALID":
            pairs.extend([
                {"idx": original["pair_id"] + "_human", "code": original["human_code"], "label": "human"},
                {"idx": original["pair_id"] + "_lm", "code": item["new_agc_code"], "label": "lm"},
            ])
    write_rows(args.output_dir / "pilot_pairs_valid.csv", pairs, ["idx", "code", "label"])
    write_rows(args.output_dir / "pilot_qc.csv", qc, [
        "pair_id", "split", "complexity_block", "status", "pipeline_status",
        "raw_mgc_ok", "clean_mgc_ok", "structure_ok", "structure_reason",
        "human_reproduced", "input_tokens", "generated_tokens", "seconds"
    ])
    total = len(completions)
    valid = sum(x["status"] == "VALID" for x in completions)
    invalid = total - valid
    times = [float(x["seconds"]) for x in completions]
    is_done = total == len(prepared)
    rate = valid / total if total else None
    if not is_done:
        status = "INCOMPLETE"
    elif rate < args.min_valid_rate:
        status = "QC_REVIEW"
    else:
        status = "PASS"
    summary = {
        "experiment": "run-x-02", "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model_name, "decoding": "greedy", "temperature": 0.0,
        "do_sample": False, "top_p_passed": False,
        "original_pairs": 4500, "pilot_selected": len(prepared),
        "generated": total, "valid": valid, "invalid": invalid,
        "valid_rate": rate, "min_valid_rate_for_pass": args.min_valid_rate,
        "split_selected": dict(Counter(x["split"] for x in prepared)),
        "split_valid": dict(Counter(x["split"] for x in prepared if by_id.get(x["pair_id"], {}).get("status") == "VALID")),
        "mean_seconds_per_generation": statistics.mean(times) if times else None,
        "elapsed_generation_seconds": sum(times),
        "new_pairs_not_backfilled": True, "original_data_modified": False,
        "config_sha256": hash_text(canonical_json(config)),
        "output_dir": str(args.output_dir),
    }
    write_json(args.output_dir / "pilot_summary.json", summary)
    lines = [
        "Experiment: run-x-02", f"Status: {status}",
        "Generator: codellama/CodeLlama-7b-hf (actual: " + args.model_name + ")",
        "Decoding: T=0.0 greedy (do_sample=False; no temperature/top_p arguments)",
        f"Selected: {len(prepared)}, generated: {total}, valid: {valid}, invalid: {invalid}",
        "Valid rate: " + (f"{rate:.3%}" if rate is not None else "n/a"),
        f"Split selection: {summary['split_selected']}",
        f"Split valid: {summary['split_valid']}",
        "Original data: read-only; invalid generations not backfilled.",
        f"Artifacts: {args.output_dir}",
    ]
    (args.output_dir / "pilot_findings.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    return summary


def main() -> int:
    args = parse_args()
    if not (0 <= args.min_valid_rate <= 1):
        fail("min valid rate must lie in [0,1]")
    if args.prompt_max_tokens <= 0 or args.max_new_tokens <= 0:
        fail("token limits must be positive")
    args.original_pairs = args.original_pairs.expanduser().resolve()
    args.split_manifest = args.split_manifest.expanduser().resolve()
    args.validator_script = args.validator_script.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    for path in (args.original_pairs, args.split_manifest, args.validator_script):
        if not path.is_file():
            fail(f"Missing input: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    original = load_original_pairs(args.original_pairs, 4500)
    manifest, blocks = load_manifest(args.split_manifest, 4500)
    if set(original) != {row["pair_id"] for row in manifest}:
        fail("Original HWC/AGC CSV IDs differ from the split manifest")
    selection = select_pilot_blocks(blocks, args.pilot_pairs, args.seed)
    print(f"[INFO] Original 4,500 pairs verified; complexity blocks={len(blocks)}", flush=True)
    print(f"[INFO] Pilot selected {len(selection)} pairs, "
          f"split={dict(Counter(r['split'] for r in selection))}", flush=True)

    prepared = []
    for row in selection:
        pair_id = row["pair_id"]
        human = original[pair_id]["human"]
        old_agc = original[pair_id]["lm"]
        prompt, solution = extract_prompt(human, old_agc, pair_id)
        prepared.append({
            "pair_id": pair_id, "complexity_block": int(row["complexity_block"]),
            "complexity_score": row.get("complexity_score", ""),
            "split": row["split"], "prompt": prompt, "solution": solution,
            "prompt_sha256": hash_text(prompt),
            "human_code": human, "human_sha256": hash_text(human),
            "original_agc_sha256": hash_text(old_agc),
        })

    config = {
        "experiment": "run-x-02", "mode": "T0_GREEDY", "model": args.model_name,
        "temperature": 0.0, "do_sample": False, "top_p": None,
        "prompt_max_tokens": args.prompt_max_tokens,
        "max_new_tokens": args.max_new_tokens, "pilot_pairs": args.pilot_pairs,
        "selection_seed": args.seed,
        "original_csv": str(args.original_pairs),
        "original_csv_sha256": sha256(args.original_pairs),
        "split_manifest": str(args.split_manifest),
        "split_manifest_sha256": sha256(args.split_manifest),
        "validator_script": str(args.validator_script),
        "validator_script_sha256": sha256(args.validator_script),
        "selected_pairs_sha256": hash_text(canonical_json(prepared)),
    }
    config_file = args.output_dir / "experiment_config.json"
    selection_file = args.output_dir / "pilot_selection.csv"
    prepared_file = args.output_dir / "pilot_prepared.jsonl"
    records_file = args.output_dir / "pilot_generation.jsonl"
    if args.resume:
        if not config_file.is_file() or not prepared_file.is_file():
            fail("Cannot resume: experiment_config.json/pilot_prepared.jsonl missing")
        previous = json.loads(config_file.read_text(encoding="utf-8"))
        if previous != config:
            fail("Cannot resume because the inputs, selected prompts, or model settings changed")
    else:
        if any(p.exists() for p in (config_file, selection_file, prepared_file, records_file)):
            fail("Output files already exist; refusing to overwrite original run")
        write_json(config_file, config)
        write_rows(selection_file, prepared, [
            "pair_id", "split", "complexity_block", "complexity_score",
            "prompt_sha256", "human_sha256", "original_agc_sha256"
        ])
        write_jsonl(prepared_file, prepared)
    print("[INFO] Recovered 100% original prompt prefixes and verified HWC/AGC correspondence", flush=True)
    if args.dry_run:
        print("[DRY-RUN] Selection and prompt integrity checks PASS; no GPU/model loaded.", flush=True)
        return 0

    # Load shared validation logic before expensive model initialization.
    validator = import_validator(args.validator_script)
    for row in prepared:
        if validator.compose_code(row["prompt"], row["solution"]) != row["human_code"]:
            fail(f"HWC reconstruction differs from original: {row['pair_id']}")
    print("[INFO] Original validator HWC reconstruction PASS", flush=True)

    records = load_jsonl(records_file)
    prepared_by_id = {r["pair_id"]: r for r in prepared}
    seen = set()
    for record in records:
        pair_id = record.get("pair_id")
        if pair_id not in prepared_by_id or pair_id in seen:
            fail(f"Invalid or repeated checkpoint pair ID: {pair_id}")
        if (record.get("model") != args.model_name
                or record.get("temperature") != 0.0
                or record.get("do_sample") is not False
                or record.get("top_p") is not None
                or record.get("prompt_sha256") != prepared_by_id[pair_id]["prompt_sha256"]
                or record.get("split") != prepared_by_id[pair_id]["split"]):
            fail(f"Checkpoint generation configuration/provenance mismatch: {pair_id}")
        seen.add(pair_id)
    remaining = [r for r in prepared if r["pair_id"] not in seen]
    print(f"[INFO] Checkpoint records={len(records)}, pending={len(remaining)}", flush=True)

    if remaining:
        model, tokenizer, eos_ids, torch = load_model(args.model_name, args.local_files_only)
        for offset, row in enumerate(remaining, start=1):
            t0 = time.monotonic()
            raw, input_tok, new_tok = generate_one(
                model, tokenizer, eos_ids, torch, row["prompt"],
                args.prompt_max_tokens, args.max_new_tokens,
            )
            duration = time.monotonic() - t0
            result = validate_attempt(
                validator, row, raw, input_tok, new_tok, duration, args.model_name
            )
            append_jsonl(records_file, result)
            records.append(result)
            print(f"[GEN] {len(records)}/{len(prepared)} pair={row['pair_id']} "
                  f"split={row['split']} status={result['status']} "
                  f"tokens={new_tok} elapsed={duration:.2f}s", flush=True)
        del model
        torch.cuda.empty_cache()

    summary = emit_final(args, prepared, records, config)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise
