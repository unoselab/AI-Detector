#!/usr/bin/env python3
"""run-x-06: matched 4,500-pair CodeLlama-7B T=0.0 generation and extraction.

Read-only inputs:
    Original 4,500-pair CSV (idx,code,label) and 450-block split manifest.
    Saved run-x-02 prepared/experiment metadata and run-x-04 Standard-EOS
    output (100 pairs) plus run-x-05 extraction summary (verification only).
    Existing code-generation/find_validsyntax_mgc.py (imported validator API).

Outputs within one new run-x-06/<RUN_ID> directory:
    experiment_config.json, full_selection.csv, full_prepared.jsonl,
    gpu0_generation.jsonl, gpu1_generation.jsonl (append-only checkpoints),
    generation_full.jsonl, extracted_functions.jsonl, extraction_qc.csv,
    valid_pairs_full.csv, common_valid_pairs_full.csv, full_summary.json,
    full_findings.txt, runtime_environment.json, generation_reference_qc.csv.

A single worker runs on exactly one visible GPU. Use the independent shell
wrapper to launch two workers concurrently. No original data are overwritten.
"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import os
import platform
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_MODEL = "codellama/CodeLlama-7b-hf"
EXPECTED = 4500
EOS = [2]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["prepare", "worker", "finalize"], required=True)
    parser.add_argument("--original-pairs", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--validator-script", type=Path, required=True)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--ablation-dir", type=Path, required=True)
    parser.add_argument("--extraction-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--model-name", default=EXPECTED_MODEL)
    parser.add_argument("--gpu-index", choices=[0, 1], type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--fixture-mode", action="store_true", help="Offline fixture testing only; NOT production.")
    parser.add_argument("--allow-other-python-offline", action="store_true",
                        help="Offline verification only, not exposed by production wrapper.")
    return parser.parse_args()


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def read_json(path):
    require(path.is_file(), f"Missing input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    require(path.is_file(), f"Missing input: {path}")
    items = []
    with path.open(encoding="utf-8") as stream:
        for lineno, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as error:
                require(False, f"Corrupt JSONL {path}:{lineno}: {error}")
    return items


def atomic_text(path, content):
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def write_json(path, obj):
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path, items):
    atomic_text(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items))


def write_csv(path, items, headers):
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)
    temp.replace(path)


def append_jsonl(path, item):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(item, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_csv(path):
    csv.field_size_limit(sys.maxsize)
    require(path.is_file(), f"Missing CSV: {path}")
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def import_validator(path):
    require(path.is_file(), f"Validator missing: {path}")
    spec = importlib.util.spec_from_file_location("run_x_06_original_validator", str(path))
    require(spec is not None and spec.loader is not None, "Cannot load original validator")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    for name in ("compose_code", "syntax_check", "code_has_required_structure"):
        require(hasattr(mod, name), f"Original validator missing function: {name}")
    return mod


def check_python(fixture, allow_offline):
    is311 = sys.version_info[:2] == (3, 11)
    require(is311 or fixture or allow_offline, "Python 3.11 is required; activate the aidetector environment")
    return {"python": sys.version, "executable": sys.executable,
            "implementation": platform.python_implementation(), "python311": is311,
            "fixture_mode": fixture, "offline_non311": allow_offline}


def load_source_pairs(path):
    rows = read_csv(path)
    require(len(rows) == 2 * EXPECTED, "Expected exactly 9,000 HWC/AGC rows")
    pairs = {}
    for r in rows:
        idx = r["idx"]
        m = re.fullmatch(r"(.+)_(human|lm)", idx)
        require(m is not None, f"Invalid original row ID: {idx}")
        pid, label = m.group(1), m.group(2)
        require(label == r["label"], f"Index/label mismatch: {idx}")
        pair = pairs.setdefault(pid, {})
        require(label not in pair, f"Duplicate {label} record: {pid}")
        pair[label] = r["code"]
    require(len(pairs) == EXPECTED and all(set(v) == {"human", "lm"} for v in pairs.values()),
            "Original dataset must contain exactly 4,500 complete pairs")
    return pairs


def load_manifest(path, all_ids):
    manifest = read_csv(path)
    require(len(manifest) == EXPECTED, "Original split manifest must contain 4,500 rows")
    ids = [r["pair_id"] for r in manifest]
    require(len(set(ids)) == EXPECTED and set(ids) == set(all_ids), "Original/manifest pair IDs disagree")
    blocks = defaultdict(list)
    for row in manifest:
        require(row["split"] in ("train", "dev", "test"), "Invalid split label")
        block = int(row["complexity_block"])
        require(0 <= block < 450, "Complexity block must be in [0,449]")
        blocks[block].append(row)
    require(len(blocks) == 450, "Expected 450 complexity blocks")
    for bid, block_rows in blocks.items():
        require(len(block_rows) == 10 and Counter(r["split"] for r in block_rows)
                == {"train": 8, "dev": 1, "test": 1}, f"Invalid block {bid}")
    return sorted(manifest, key=lambda r: (int(r["complexity_block"]), r["split"], r["pair_id"]))


def recover_prompt(human_code, original_agc, pair_id):
    # Copied and adapted from the previously validated run-x-02 logic.
    human = human_code.replace("\r\n", "\n").replace("\r", "\n")
    agc = original_agc.replace("\r\n", "\n").replace("\r", "\n")
    tree = ast.parse(human)
    require(len(tree.body) == 1 and isinstance(tree.body[0],
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)),
            f"{pair_id}: expected one top-level function/class")
    block = tree.body[0]
    require(bool(block.body) and isinstance(block.body[0], ast.Expr),
            f"{pair_id}: expected a leading docstring")
    stmt = block.body[0]
    require(isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str),
            f"{pair_id}: leading statement is not a docstring")
    lines = human.splitlines(keepends=True)
    end_row, end_byte = stmt.end_lineno - 1, stmt.end_col_offset
    end_col = len(lines[end_row].encode("utf-8")[:end_byte].decode("utf-8"))
    offset = sum(len(x) for x in lines[:end_row]) + end_col
    prompt, solution = human[:offset], human[offset:]
    require(prompt and solution.strip() and agc.startswith(prompt),
            f"{pair_id}: HWC/AGC prompt-prefix mismatch")
    require(prompt.lstrip().startswith(("def ", "async def ", "class ", "@")),
            f"{pair_id}: unexpected prompt start")
    return prompt, solution


def load_pilot_checks(args):
    """Anchor full generation to the exact audited baseline and 100-pair pilot."""
    if args.fixture_mode:
        return {}, {}, {}
    pc = read_json(args.pilot_dir / "experiment_config.json")
    ac = read_json(args.ablation_dir / "experiment_config.json")
    xs = read_json(args.extraction_dir / "extraction_summary.json")
    require(pc["experiment"] == "run-x-02" and pc["mode"] == "T0_GREEDY", "Wrong pilot")
    require(ac["experiment"] == "run-x-04" and ac["ablation_eos_ids"]["standard"] == EOS,
            "Wrong EOS ablation")
    require(xs["experiment"] == "run-x-05" and xs["status"] == "PASS" and
            xs["extracted_standard_valid"] == 93, "Unverified run-x-05 extraction")
    require(pc["model"] == ac["model"] == args.model_name == EXPECTED_MODEL, "Model differs")
    require(pc["original_csv_sha256"] == file_sha(args.original_pairs)
            and pc["split_manifest_sha256"] == file_sha(args.split_manifest)
            and pc["validator_script_sha256"] == file_sha(args.validator_script),
            "Original source SHA-256 differs from run-x-02")
    require(ac["prompt_max_tokens"] == pc["prompt_max_tokens"] == 128 and
            ac["max_new_tokens"] == pc["max_new_tokens"] == 512,
            "Prompt/generation length differs from pilot")
    pilot = read_jsonl(args.pilot_dir / "pilot_prepared.jsonl")
    require(len(pilot) == 100 and len({p["pair_id"] for p in pilot}) == 100,
            "Expected 100 distinct pilot prompts")
    ablations = read_jsonl(args.ablation_dir / "ablation_generation.jsonl")
    standard = {r["pair_id"]: r for r in ablations if r["mode"] == "standard"}
    require(len(standard) == 100 and len(ablations) == 200, "Incomplete run-x-04 reference")
    for r in standard.values():
        require(r["raw_sha256"] == text_sha256(r["raw_output"]), "Corrupt reference generation")
    return {p["pair_id"]: p for p in pilot}, standard, {
        "pilot_prepared": file_sha(args.pilot_dir / "pilot_prepared.jsonl"),
        "pilot_config": file_sha(args.pilot_dir / "experiment_config.json"),
        "ablation_generation": file_sha(args.ablation_dir / "ablation_generation.jsonl"),
        "extraction_summary": file_sha(args.extraction_dir / "extraction_summary.json"),
    }


def build_prepared(args, validator):
    originals = load_source_pairs(args.original_pairs)
    manifest = load_manifest(args.split_manifest, originals)
    pilot, reference, refs = load_pilot_checks(args)
    prepared = []
    for row in manifest:
        pid = row["pair_id"]
        human, agc = originals[pid]["human"], originals[pid]["lm"]
        prompt, solution = recover_prompt(human, agc, pid)
        require(validator.compose_code(prompt, solution) == human,
                f"HWC reconstruction mismatch: {pid}")
        record = {
            "pair_id": pid, "split": row["split"],
            "complexity_score": row.get("complexity_score", ""),
            "complexity_block": int(row["complexity_block"]),
            "assigned_gpu": int(row["complexity_block"]) % 2,
            "prompt": prompt, "solution": solution,
            "prompt_sha256": text_sha256(prompt),
            "human_code": human, "human_sha256": text_sha256(human),
            "original_agc_sha256": text_sha256(agc),
        }
        if pid in pilot:
            previous = pilot[pid]
            for key in ("pair_id", "split", "complexity_block", "prompt", "solution",
                        "prompt_sha256", "human_code", "human_sha256", "original_agc_sha256"):
                require(record[key] == previous[key], f"Pilot prompt reconstruction changed: {pid}/{key}")
        prepared.append(record)
    counts = Counter(r["split"] for r in prepared)
    require(counts == {"train": 3600, "dev": 450, "test": 450}, f"Split counts changed: {counts}")
    worker_counts = {k: Counter(r["split"] for r in prepared if r["assigned_gpu"] == k)
                     for k in (0, 1)}
    for gpu, split in worker_counts.items():
        require(split == {"train": 1800, "dev": 225, "test": 225},
                f"Unbalanced worker {gpu}: {split}")
    require(len([p for p in prepared if p["pair_id"] in reference]) == len(reference),
            "Not all pilot reference IDs are in full dataset")
    return prepared, refs


def make_config(args, prepared, refs):
    return {
        "experiment": "run-x-06", "design": "4500 matched T=0.0 Standard EOS [2] with AST extraction",
        "model": args.model_name, "temperature": 0.0, "do_sample": False,
        "top_p_argument": None, "temperature_argument": None,
        "eos_ids": EOS, "prompt_max_tokens": 128, "max_new_tokens": 512,
        "original_csv": str(args.original_pairs.resolve()),
        "original_csv_sha256": file_sha(args.original_pairs),
        "split_manifest": str(args.split_manifest.resolve()),
        "split_manifest_sha256": file_sha(args.split_manifest),
        "validator_script": str(args.validator_script.resolve()),
        "validator_script_sha256": file_sha(args.validator_script),
        "pilot_reference_sha256": refs,
        "full_prepared_sha256": text_sha256(canonical_json(prepared)),
        "expected": EXPECTED,
        "gpu_assignment": "complexity_block modulo 2 (225 blocks / 2250 procedures per GPU)",
        "fixture_mode": args.fixture_mode,
    }


def prepare(args, env):
    validator = import_validator(args.validator_script)
    prepared, refs = build_prepared(args, validator)
    config = make_config(args, prepared, refs)
    print(f"[INPUT] Original {len(prepared)} pairs verified; splits=3600/450/450", flush=True)
    print("[INPUT] GPU assignments: gpu0=2250 gpu1=2250 (1800/225/225 each)", flush=True)
    print(f"[INPUT] Pilot prompts verified={100 if not args.fixture_mode else 'fixture-disabled'}", flush=True)
    if args.dry_run:
        print("[DRY-RUN] PASS; no model loading or output creation", flush=True)
        return 0
    out = args.out_dir
    if args.resume:
        old_config = read_json(out / "experiment_config.json")
        require(old_config == config, "Resume mismatch: original data, code, or model changed")
        require(file_sha(out / "full_prepared.jsonl") ==
                read_json(out / "input_manifest.json")["prepared_file_sha256"],
                "Resume input preparation file was modified")
        print("[PREPARE] Resume input provenance PASS", flush=True)
    else:
        require(not out.exists() or not any(out.iterdir()), "Output directory is not empty")
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "experiment_config.json", config)
        write_jsonl(out / "full_prepared.jsonl", prepared)
        write_csv(out / "full_selection.csv", [
            {k: r[k] for k in ("pair_id", "split", "complexity_block", "complexity_score",
                                "assigned_gpu", "prompt_sha256", "human_sha256", "original_agc_sha256")}
            for r in prepared],
            ["pair_id", "split", "complexity_block", "complexity_score", "assigned_gpu",
             "prompt_sha256", "human_sha256", "original_agc_sha256"])
        write_json(out / "input_manifest.json", {
            "prepared_file_sha256": file_sha(out / "full_prepared.jsonl"),
            "source_csv_sha256": config["original_csv_sha256"],
            "split_sha256": config["split_manifest_sha256"],
            "validator_sha256": config["validator_script_sha256"],
            "pilot_reference_sha256": refs,
            "python": env,
        })
        print("[PREPARE] Wrote immutable 4500-pair preparation and manifest", flush=True)
    return 0


def verify_prepared(args):
    config = read_json(args.out_dir / "experiment_config.json")
    require(config["experiment"] == "run-x-06" and config["model"] == args.model_name,
            "Wrong run or model")
    require(config["temperature"] == 0.0 and config["do_sample"] is False and
            config["eos_ids"] == EOS and config["expected"] == EXPECTED,
            "Generation configuration changed")
    for key, path in (("original_csv_sha256", args.original_pairs),
                      ("split_manifest_sha256", args.split_manifest),
                      ("validator_script_sha256", args.validator_script)):
        require(file_sha(path) == config[key], f"Source input changed: {path}")
    prepared_file = args.out_dir / "full_prepared.jsonl"
    require(file_sha(prepared_file) == read_json(args.out_dir / "input_manifest.json")["prepared_file_sha256"],
            "Prepared manifest changed")
    prepared = read_jsonl(prepared_file)
    require(len(prepared) == EXPECTED and
            len({r["pair_id"] for r in prepared}) == EXPECTED, "Corrupt prepared data")
    require(text_sha256(canonical_json(prepared)) == config["full_prepared_sha256"],
            "Prepared content SHA-256 mismatch")
    return config, prepared


def checkpoint_map(path, prepared, gpu):
    expected = {p["pair_id"]: p for p in prepared if p["assigned_gpu"] == gpu}
    entries = read_jsonl(path) if path.is_file() else []
    seen = {}
    for r in entries:
        pid = r.get("pair_id")
        require(pid in expected and pid not in seen, f"Duplicate/foreign GPU{gpu} checkpoint: {pid}")
        p = expected[pid]
        require(r.get("gpu_assignment") == gpu and
                r.get("prompt_sha256") == p["prompt_sha256"] and
                r.get("split") == p["split"] and
                r.get("model") == EXPECTED_MODEL and
                r.get("eos_ids") == EOS and r.get("do_sample") is False and
                r.get("temperature") == 0.0 and
                r.get("raw_sha256") == text_sha256(r["raw_output"]) and
                r.get("generated_tokens") == len(r["generated_token_ids"]) and
                r.get("generated_tokens") <= 512 and
                r.get("generated_token_ids_sha256") == text_sha256(canonical_json(r["generated_token_ids"])),
                f"Checkpoint integrity mismatch: {pid}")
        seen[pid] = r
    return seen


def init_model(model_name, local_only):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1,
            "Worker must see exactly one CUDA GPU via CUDA_VISIBLE_DEVICES")
    tok = AutoTokenizer.from_pretrained(model_name, local_files_only=local_only)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    require(tok.eos_token_id == 2 and tok.truncation_side == "right",
            "Tokenizer EOS or truncation differs from audited pilot")
    tok.padding_side = "left"
    print(f"[CUDA] {torch.cuda.get_device_name(0)}; loading CodeLlama-7B float16", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, torch_dtype=torch.float16,
        local_files_only=local_only).to("cuda:0")
    model.eval()
    model_env = {"torch": torch.__version__, "transformers": transformers.__version__,
                 "gpu": torch.cuda.get_device_name(0), "model_revision": getattr(model.config, "_commit_hash", None),
                 "tokenizer": type(tok).__name__, "model_dtype": str(next(model.parameters()).dtype)}
    return model, tok, torch, model_env


def generate_one(model, tok, torch, prompt):
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=128,
                 return_attention_mask=True)
    token_count_full = len(tok(prompt, add_special_tokens=True).input_ids)
    ids = inputs.input_ids.to("cuda:0")
    mask = inputs.attention_mask.to("cuda:0")
    with torch.inference_mode():
        out = model.generate(input_ids=ids, attention_mask=mask, do_sample=False,
                             max_new_tokens=512, pad_token_id=tok.eos_token_id,
                             eos_token_id=EOS, use_cache=True)
    generated = out[0, ids.shape[1]:].tolist()
    raw = tok.decode(generated, skip_special_tokens=False).split("<|endoftext|>", 1)[0]
    last = generated[-1] if generated else None
    termination = "eos_id" if last in EOS else ("length_cap" if len(generated) == 512 else "other")
    return {"raw_output": raw, "generated_token_ids": generated,
            "input_tokens": int(ids.shape[1]), "full_prompt_tokens": token_count_full,
            "prompt_truncated": token_count_full > 128,
            "generated_tokens": len(generated), "last_token_id": last, "termination": termination}


def worker(args, env):
    require(args.gpu_index in (0, 1), "--gpu-index required for worker phase")
    config, prepared = verify_prepared(args)
    rows = [r for r in prepared if r["assigned_gpu"] == args.gpu_index]
    checkpoint_path = args.out_dir / f"gpu{args.gpu_index}_generation.jsonl"
    done = checkpoint_map(checkpoint_path, prepared, args.gpu_index)
    pending = [r for r in rows if r["pair_id"] not in done]
    print(f"[WORKER{args.gpu_index}] completed={len(done)} pending={len(pending)} / {len(rows)}", flush=True)
    if args.dry_run or not pending:
        return 0
    require(not args.fixture_mode, "Fixture mode cannot run GPU inference")
    model, tokenizer, torch, model_env = init_model(args.model_name, args.local_files_only)
    model_env.update(env)
    model_env["assigned_gpu"] = args.gpu_index
    env_path = args.out_dir / f"gpu{args.gpu_index}_environment.json"
    if env_path.exists():
        original_env = read_json(env_path)
        require(original_env["model_revision"] == model_env["model_revision"] and
                original_env["torch"] == model_env["torch"] and
                original_env["transformers"] == model_env["transformers"],
                "Resume runtime versions differ from original worker")
    else:
        write_json(env_path, model_env)
    for number, p in enumerate(pending, 1):
        started = time.perf_counter()
        info = generate_one(model, tokenizer, torch, p["prompt"])
        result = {"pair_id": p["pair_id"], "split": p["split"],
                  "complexity_block": p["complexity_block"], "gpu_assignment": args.gpu_index,
                  "model": args.model_name, "temperature": 0.0, "do_sample": False,
                  "top_p": None, "eos_ids": EOS, "prompt_sha256": p["prompt_sha256"],
                  **info, "raw_sha256": text_sha256(info["raw_output"]),
                  "generated_token_ids_sha256": text_sha256(canonical_json(info["generated_token_ids"])),
                  "seconds": round(time.perf_counter() - started, 4)}
        append_jsonl(checkpoint_path, result)
        completed = len(done) + number
        if number <= 5 or number % 25 == 0 or number == len(pending):
            print(f"[GPU{args.gpu_index}] {completed}/{len(rows)} {p['pair_id']} "
                  f"tokens={result['generated_tokens']} stop={result['termination']} "
                  f"elapsed={result['seconds']:.2f}s", flush=True)
    print(f"[WORKER{args.gpu_index}] PASS: {len(rows)}/{len(rows)} generated", flush=True)
    return 0


# The following AST-boundary extraction helpers are copied from the already
# validated run-x-05 Python implementation. They are embedded here so that
# run-x-06 does not depend on an earlier experiment implementation at runtime.
def indentation(line: str):
    return len(line.expandtabs(8)) - len(line.expandtabs(8).lstrip(" "))


def expected_body_indent(prompt: str) -> int:
    nonblank = [line for line in prompt.replace("\r\n", "\n").splitlines() if line.strip()]
    require(nonblank, "No lines in prompt")
    last = nonblank[-1]
    return indentation(last) + (4 if last.rstrip().endswith(":") else 0)


def original_signature(prompt: str):
    match = re.search(r"(?m)^[ \t]*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", prompt)
    require(match is not None, "Prompt does not contain a function definition")
    return match.group(1)


def candidate_boundaries(raw: str, body_indent: int):
    """Find dedented continuation statements outside the target body.

    The original CodeSearchNet prompt may normalize the signature to column 0
    while retaining an 8-space docstring/body indent from a class method.
    Therefore an upcoming sibling ``    def ...`` must be compared with the
    original *body* indent, not the prompt signature's column 0.
    Each proposed cut is subsequently required to pass complete AST checks.
    """
    limit = max(0, body_indent - 4)
    offset = 0
    results = []
    lines = raw.splitlines(keepends=True)
    for line_no, line in enumerate(lines, 1):
        current = offset
        offset += len(line)
        if line_no == 1 or not line.strip() or line.lstrip().startswith("#"):
            continue
        if indentation(line) <= limit:
            results.append((current, f"dedented_line_{line_no}", line.strip()[:120]))
    results.append((len(raw), "full_continuation", ""))
    return sorted(set(results), key=lambda item: item[0])


def validate_candidate(validator, prompt: str, raw_prefix: str, human_tree: ast.Module):
    code = validator.compose_code(prompt, raw_prefix)
    syntax = validator.syntax_check(code)
    if not syntax.ok:
        return None, "syntax: " + syntax.error
    structure, reason = validator.code_has_required_structure(code)
    if not structure:
        return None, "structure: " + reason
    tree = ast.parse(code)
    functions = (ast.FunctionDef, ast.AsyncFunctionDef)
    if len(tree.body) != 1 or not isinstance(tree.body[0], functions):
        return None, "ambiguous: expected exactly one top-level procedure"
    h = human_tree.body[0]
    n = tree.body[0]
    if n.name != h.name or type(n) is not type(h):
        return None, "mismatch: function name/type"
    if ast.dump(n.args, include_attributes=False) != ast.dump(h.args, include_attributes=False):
        return None, "mismatch: function arguments"
    if (ast.dump(n.returns, include_attributes=False) if n.returns is not None else None) != (ast.dump(h.returns, include_attributes=False) if h.returns is not None else None):
        return None, "mismatch: return annotation"
    if ast.get_docstring(n, clean=False) != ast.get_docstring(h, clean=False):
        return None, "mismatch: preserved prompt docstring"
    return code, "OK"


def extract_one(validator, prepared: dict, standard: dict):
    prompt = prepared["prompt"]
    human = validator.compose_code(prompt, prepared["solution"])
    require(human == prepared["human_code"],
            f"Cannot reproduce original HWC {prepared['pair_id']}")
    htree = ast.parse(human)
    require(len(htree.body) == 1 and isinstance(htree.body[0],
            (ast.FunctionDef, ast.AsyncFunctionDef)),
            f"Unexpected original HWC structure: {prepared['pair_id']}")
    expected_name = original_signature(prompt)
    require(expected_name == htree.body[0].name,
            f"Prompt/HWC function name mismatch: {prepared['pair_id']}")
    raw = standard["raw_output"]
    body_indent = expected_body_indent(prompt)
    last_rejection = "no candidates"
    boundaries = candidate_boundaries(raw, body_indent)
    for offset, boundary, following in boundaries:
        code, reason = validate_candidate(validator, prompt, raw[:offset], htree)
        if code is not None:
            return {"status": "VALID", "extracted_agc_code": code,
                    "extracted_agc_sha256": text_sha256(code),
                    "extracted_continuation": raw[:offset], "boundary": boundary,
                    "next_line_preview": following, "cut_character_offset": offset,
                    "raw_characters": len(raw), "removed_characters": len(raw) - offset,
                    "candidate_count": len(boundaries), "body_indent": body_indent,
                    "error": ""}
        last_rejection = reason
    return {"status": "INVALID", "extracted_agc_code": "",
            "extracted_agc_sha256": "", "extracted_continuation": "",
            "boundary": "none", "next_line_preview": "", "cut_character_offset": "",
            "raw_characters": len(raw), "removed_characters": "",
            "candidate_count": len(boundaries), "body_indent": body_indent,
            "error": last_rejection}




def finalize(args, env):
    config, prepared = verify_prepared(args)
    by_id = {p["pair_id"]: p for p in prepared}
    gpu_rows = []
    for gpu in (0, 1):
        checkpoint = args.out_dir / f"gpu{gpu}_generation.jsonl"
        require(checkpoint.is_file(), f"GPU{gpu} checkpoint missing")
        records = checkpoint_map(checkpoint, prepared, gpu)
        require(len(records) == 2250, f"GPU{gpu} incomplete: {len(records)}/2250")
        require((args.out_dir / f"gpu{gpu}_environment.json").is_file() or args.fixture_mode,
                f"GPU{gpu} runtime metadata missing")
        gpu_rows.extend(records.values())
    generated = {r["pair_id"]: r for r in gpu_rows}
    require(len(generated) == EXPECTED and set(generated) == set(by_id),
            "Merged generation contains missing, extra or duplicate pair IDs")

    # The same 100 prompts were previously generated in run-x-04 using
    # Standard EOS. Keep a matched reproducibility audit before aggregation.
    if not args.fixture_mode:
        standard = {r["pair_id"]: r for r in read_jsonl(args.ablation_dir / "ablation_generation.jsonl")
                    if r["mode"] == "standard"}
        require(len(standard) == 100, "run-x-04 reference lost 100-pair completeness")
    else:
        standard = {}
    reference_qc = [
        {"pair_id": pid, "same_raw_generation": generated[pid]["raw_sha256"] == old["raw_sha256"],
         "previous_raw_sha256": old["raw_sha256"], "new_raw_sha256": generated[pid]["raw_sha256"]}
        for pid, old in sorted(standard.items())
    ]
    reference_mismatch = sum(not r["same_raw_generation"] for r in reference_qc)
    validator = import_validator(args.validator_script)
    paired, common_pairs, extraction, qc, full_generated = [], [], [], [], []
    orig = load_source_pairs(args.original_pairs)
    original_valid_counter = Counter()
    split_count = {x: {"selected": 0, "extracted_valid": 0, "common_valid": 0}
                   for x in ("train", "dev", "test")}
    for n, p in enumerate(prepared, 1):
        pid = p["pair_id"]
        r = generated[pid]
        info = extract_one(validator, p, r)
        original_code = orig[pid]["lm"]
        orig_syn = validator.syntax_check(original_code)
        orig_struct, orig_reason = validator.code_has_required_structure(original_code) if orig_syn.ok else (False, orig_syn.error)
        orig_ok = bool(orig_syn.ok and orig_struct)
        original_valid_counter["valid" if orig_ok else "invalid"] += 1
        split = p["split"]
        split_count[split]["selected"] += 1
        cap_reached = r["termination"] == "length_cap"
        valid = info["status"] == "VALID"
        # This diagnostic flags suspiciously incomplete functions; it is not
        # used to reject AST-valid code or change a saved output.
        missing_return = False
        has_nested = False
        if valid:
            new_tree = ast.parse(info["extracted_agc_code"])
            human_tree = ast.parse(p["human_code"])
            def has_return(node):
                return any(isinstance(child, (ast.Return, ast.Yield, ast.YieldFrom))
                           for child in ast.walk(node))
            missing_return = has_return(human_tree.body[0]) and not has_return(new_tree.body[0])
            has_nested = any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
                             for x in ast.walk(new_tree.body[0]) if x is not new_tree.body[0])
            split_count[split]["extracted_valid"] += 1
            paired.extend([{"idx": f"{pid}_human", "code": p["human_code"], "label": "human"},
                           {"idx": f"{pid}_lm", "code": info["extracted_agc_code"], "label": "lm"}])
            if orig_ok:
                split_count[split]["common_valid"] += 1
                common_pairs.extend([{"idx": f"{pid}_human", "code": p["human_code"], "label": "human"},
                                     {"idx": f"{pid}_lm", "code": info["extracted_agc_code"], "label": "lm"}])
        record = {"pair_id": pid, "split": split, "complexity_block": p["complexity_block"],
                  "original_t02_strict_valid": orig_ok,
                  "original_t02_reason": "" if orig_ok else orig_reason,
                  "prompt_sha256": p["prompt_sha256"],
                  "raw_sha256": r["raw_sha256"], "generated_tokens": r["generated_tokens"],
                  "last_token_id": r["last_token_id"], "termination": r["termination"],
                  "prompt_truncated": r["prompt_truncated"], "input_tokens": r["input_tokens"],
                  "gpu_assignment": r["gpu_assignment"], "extracted_valid": valid,
                  "missing_return_vs_hwc": missing_return,
                  "nested_functions_present": has_nested,
                  "length_cap_and_full_continuation": cap_reached and info["boundary"] == "full_continuation",
                  **info}
        extraction.append(record)
        qc.append({k: v for k, v in record.items() if k not in
                   ("extracted_agc_code", "extracted_continuation")})
        full_generated.append(r)
        if n % 1000 == 0:
            print(f"[FINALIZE] Processed {n}/{EXPECTED} code extractions", flush=True)
    valid_total = sum(q["extracted_valid"] for q in qc)
    incomplete_flags = sum(q["extracted_valid"] and (q["missing_return_vs_hwc"] or
                          q["length_cap_and_full_continuation"]) for q in qc)
    status = "PASS" if reference_mismatch == 0 else "QC_REVIEW"
    summary = {
        "experiment": "run-x-06", "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "generated": EXPECTED, "generation_complete": True,
        "valid_extracted": valid_total, "invalid_extracted": EXPECTED - valid_total,
        "validity_rate": valid_total / EXPECTED,
        "valid_pairs_csv_rows": len(paired),
        "common_valid_pairs": len(common_pairs) // 2,
        "original_t02_direct_valid": original_valid_counter["valid"],
        "split": split_count, "reference_pilot_100_raw_mismatches": reference_mismatch,
        "reference_pilot_checked": len(reference_qc),
        "prompt_truncated": sum(q["prompt_truncated"] for q in qc),
        "generation_length_cap": sum(q["termination"] == "length_cap" for q in qc),
        "incompleteness_review_flags": incomplete_flags,
        "nested_function_cases_valid": sum(q["extracted_valid"] and q["nested_functions_present"] for q in qc),
        "source_data_modified": False, "invalid_backfilled": False,
        "limitations": [
            "AST/structure-validity does not establish functional completeness.",
            "This Standard-EOS extraction pipeline differs from the original T=0.2 generation/filter policy.",
            "The original T=0.2 sample was already validity-filtered; selection must be reported.",
        ],
    }
    out = args.out_dir
    write_jsonl(out / "generation_full.jsonl", full_generated)
    write_jsonl(out / "extracted_functions.jsonl", extraction)
    write_csv(out / "extraction_qc.csv", qc, [k for k in qc[0] if k not in ("extracted_agc_code", "extracted_continuation")])
    write_csv(out / "valid_pairs_full.csv", paired, ["idx", "code", "label"])
    write_csv(out / "common_valid_pairs_full.csv", common_pairs, ["idx", "code", "label"])
    write_csv(out / "generation_reference_qc.csv", reference_qc,
              ["pair_id", "same_raw_generation", "previous_raw_sha256", "new_raw_sha256"])
    write_json(out / "runtime_environment.json", {
        "python": env, "validator_sha256": file_sha(args.validator_script),
        "gpu0": read_json(out / "gpu0_environment.json") if (out / "gpu0_environment.json").exists() else {},
        "gpu1": read_json(out / "gpu1_environment.json") if (out / "gpu1_environment.json").exists() else {},
    })
    write_json(out / "full_summary.json", summary)
    findings = [
        f"Experiment: run-x-06 | Status: {status}",
        "Model: CodeLlama-7B; T=0.0 greedy; Standard EOS [2]; max_new_tokens=512",
        f"Generated: {EXPECTED}/{EXPECTED} (GPU0=2250 GPU1=2250)",
        f"Extracted valid: {valid_total}/{EXPECTED} ({valid_total/EXPECTED:.2%})",
        f"Common-valid with original T=0.2 direct rules: {len(common_pairs)//2}/{EXPECTED}",
        f"Pilot 100 raw-generation mismatches: {reference_mismatch}/{len(reference_qc)}",
        f"Prompt truncated: {summary['prompt_truncated']} | reached length cap: {summary['generation_length_cap']}",
        f"Potential incompleteness review flags: {incomplete_flags}",
        "Original sources unmodified; no invalid example replacements.",
        "NOTE: AST validity is not behavioral completeness; EOS/extraction differs from T=0.2 benchmark.",
    ]
    atomic_text(out / "full_findings.txt", "\n".join(findings) + "\n")
    print("\n".join(findings), flush=True)
    return 0


def main():
    args = parse_args()
    env = check_python(args.fixture_mode, args.allow_other_python_offline)
    require(args.model_name == EXPECTED_MODEL, "This experiment is fixed to original CodeLlama-7B")
    if args.phase == "prepare":
        return prepare(args, env)
    if args.phase == "worker":
        return worker(args, env)
    return finalize(args, env)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, ValueError, OSError, SyntaxError) as error:
        print(f"[ERROR] {error}", file=sys.stderr, flush=True)
        raise SystemExit(2) from error
