#!/usr/bin/env python3
"""run-x-08 controlled T=0.2 sampling on the original 450 CodeLlama test IDs.

Inputs are READ ONLY: audited run-x-06 prepared data, extracted T=0.0 data,
its manifests and Python validator, plus the original benchmark CSV and split.
Outputs per seed: two independent checkpoint files, raw generations, extracted
functions, validation QC, paired test CSVs, and comparisons to matched T=0.0.
No classifier training, no modification to previous experiment files, no
replacement of invalid procedures.
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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MODEL_NAME = "codellama/CodeLlama-7b-hf"
TEMPERATURE = 0.2
TOP_P = 0.95
TOP_K = 50
EOS = [2]
N_TEST = 450


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json(path):
    require(path.is_file(), f"Missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    require(path.is_file(), f"Missing JSONL: {path}")
    out = []
    with path.open(encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Corrupt JSONL {path}:{number}: {e}") from e
    return out


def read_csv(path):
    csv.field_size_limit(sys.maxsize)
    require(path.is_file(), f"Missing CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def atomic_text(path, contents):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(contents, encoding="utf-8")
    tmp.replace(path)


def write_json(path, data):
    atomic_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path, rows):
    atomic_text(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def write_csv(path, rows, columns):
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    tmp.replace(path)


def append_jsonl(path, record):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def check_python(args):
    is311 = sys.version_info[:2] == (3, 11)
    require(is311 or (args.dry_run and args.offline_allow_non311),
            "Python 3.11 required (activate aidetector Conda environment)")
    return {"version": sys.version, "executable": sys.executable,
            "implementation": platform.python_implementation(), "python311": is311}


def import_validator(path):
    require(path.is_file(), f"Missing original validator: {path}")
    spec = importlib.util.spec_from_file_location("run_x_08_original_validator", str(path))
    require(spec is not None and spec.loader is not None, "Cannot import validator")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    for fn in ("compose_code", "syntax_check", "code_has_required_structure"):
        require(hasattr(mod, fn), f"Validator API missing: {fn}")
    return mod


def parse_seeds(s):
    parts = [x.strip() for x in s.replace(" ", ",").split(",") if x.strip()]
    seeds = [int(x) for x in parts]
    require(seeds and len(set(seeds)) == len(seeds) and
            all(1 <= x < 2**31 for x in seeds), "Seeds must be unique positive integers")
    return sorted(seeds)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", required=True, choices=["prepare", "worker", "finalize"])
    p.add_argument("--run06-dir", type=Path, required=True)
    p.add_argument("--validator-script", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--seeds", default="20260723")
    p.add_argument("--gpu-index", type=int, choices=[0, 1])
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--offline-allow-non311", action="store_true",
                   help="Offline preflight testing only, not for GPU inference")
    return p.parse_args()


def pair_seed(seed, pair_id):
    """Stable local RNG seed independent of GPU, order and checkpoint resume."""
    digest = hashlib.sha256(f"run-x-08:{seed}:{pair_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2**63 - 1)


def load_provenance(args):
    """Verify complete run-x-06 inputs without regenerating any T=0.0 code."""
    base = args.run06_dir
    bc = read_json(base / "experiment_config.json")
    bs = read_json(base / "full_summary.json")
    bm = read_json(base / "input_manifest.json")
    require(bc["experiment"] == "run-x-06" and bc["model"] == MODEL_NAME and
            bc["temperature"] == 0.0 and bc["eos_ids"] == EOS and
            bc["max_new_tokens"] == 512 and bc["prompt_max_tokens"] == 128,
            "Incorrect run-x-06 reference configuration")
    require(bs["experiment"] == "run-x-06" and bs["status"] == "PASS" and
            bs["generated"] == 4500 and bs["split"]["test"]["selected"] == N_TEST,
            "run-x-06 must be fully PASS with 450 test IDs")
    require(file_sha(args.validator_script) == bc["validator_script_sha256"] == bm["validator_sha256"],
            "Original validator hash disagrees with run-x-06")
    original = Path(bc["original_csv"])
    manifest = Path(bc["split_manifest"])
    require(file_sha(original) == bc["original_csv_sha256"] == bm["source_csv_sha256"],
            "Original benchmark was modified")
    require(file_sha(manifest) == bc["split_manifest_sha256"] == bm["split_sha256"],
            "Original complexity split was modified")
    prepared_path = base / "full_prepared.jsonl"
    require(file_sha(prepared_path) == bm["prepared_file_sha256"],
            "run-x-06 prepared file hash changed")
    prepared = read_jsonl(prepared_path)
    require(len(prepared) == 4500 and len({r["pair_id"] for r in prepared}) == 4500 and
            text_sha256(canonical_json(prepared)) == bc["full_prepared_sha256"],
            "run-x-06 prepared contents changed")
    tests = [r for r in prepared if r["split"] == "test"]
    require(len(tests) == N_TEST and len({r["pair_id"] for r in tests}) == N_TEST and
            Counter(r["assigned_gpu"] for r in tests) == {0: 225, 1: 225},
            "Expected 450 test IDs with 225 assigned to each GPU")
    ext = read_jsonl(base / "extracted_functions.jsonl")
    require(len(ext) == 4500 and len({r["pair_id"] for r in ext}) == 4500,
            "Invalid run-x-06 extracted functions")
    test_by_id = {r["pair_id"]: r for r in tests}
    ext_test = {r["pair_id"]: r for r in ext if r["pair_id"] in test_by_id}
    require(len(ext_test) == N_TEST, "Missing run-x-06 T=0.0 extracted test IDs")
    for pid, r in ext_test.items():
        p = test_by_id[pid]
        require(r["split"] == "test" and r["prompt_sha256"] == p["prompt_sha256"] and
                r["status"] in {"VALID", "INVALID"} and
                (r["status"] != "VALID" or
                 r["extracted_agc_sha256"] == text_sha256(r["extracted_agc_code"])),
                f"Reference T=0.0 extracted mismatch: {pid}")
    require(sum(r["status"] == "VALID" for r in ext_test.values()) == bs["split"]["test"]["extracted_valid"],
            "T=0.0 test valid-count mismatch")
    return tests, ext_test, {
        "run06_config_sha256": file_sha(base / "experiment_config.json"),
        "run06_prepared_sha256": file_sha(prepared_path),
        "run06_extracted_sha256": file_sha(base / "extracted_functions.jsonl"),
        "run06_summary_sha256": file_sha(base / "full_summary.json"),
        "original_csv_sha256": file_sha(original),
        "split_manifest_sha256": file_sha(manifest),
        "validator_sha256": file_sha(args.validator_script),
    }


def experiment_config(args, tests, hashes, seeds):
    return {"experiment": "run-x-08", "version": "v1", "design": "test 450 controlled T=0.2 sampling vs run-x-06 T=0.0",
            "model": MODEL_NAME, "temperature": TEMPERATURE, "do_sample": True,
            "top_p": TOP_P, "top_k": TOP_K, "eos_ids": EOS,
            "prompt_max_tokens": 128, "max_new_tokens": 512, "seeds": seeds,
            "rng_policy": "per-sample torch.manual_seed and torch.cuda.manual_seed_all using SHA256(run-x-08,seed,pair_id)",
            "original_run06": str(args.run06_dir.resolve()), "input_hashes": hashes,
            "test_prepared_sha256": text_sha256(canonical_json(tests)),
            "expected_test": N_TEST, "gpu_assignment": "reuse run-x-06 complexity_block modulo 2; 225 per GPU",
            "source_inputs_read_only": True, "invalid_backfill": False}


def verify_prepared(args):
    cfg = read_json(args.out_dir / "experiment_config.json")
    require(cfg["experiment"] == "run-x-08" and cfg["model"] == MODEL_NAME and
            cfg["seeds"] == parse_seeds(args.seeds) and cfg["eos_ids"] == EOS and
            cfg["temperature"] == TEMPERATURE and cfg["do_sample"] is True and
            cfg["top_p"] == TOP_P and cfg["top_k"] == TOP_K,
            "run-x-08 config mismatch")
    # Recheck all previous-run hashes before each phase.
    _, _, hashes = load_provenance(args)
    require(cfg["input_hashes"] == hashes, "A reference input changed since prepare")
    path = args.out_dir / "test_prepared.jsonl"
    require(file_sha(path) == read_json(args.out_dir / "input_manifest.json")["test_prepared_file_sha256"],
            "Prepared test file bytes changed")
    rows = read_jsonl(path)
    require(len(rows) == N_TEST and
            text_sha256(canonical_json(rows)) == cfg["test_prepared_sha256"],
            "Prepared test content changed")
    return cfg, rows


def prepare(args, env):
    tests, _, hashes = load_provenance(args)
    cfg = experiment_config(args, tests, hashes, parse_seeds(args.seeds))
    print(f"[INPUT] run-x-06 provenance PASS; test=450; GPU0=225 GPU1=225; seeds={cfg['seeds']}", flush=True)
    if args.dry_run:
        print("[DRY-RUN] PASS; no model load or output creation", flush=True)
        return 0
    if args.resume:
        existing = read_json(args.out_dir / "experiment_config.json")
        require(existing == cfg, "RESUME configuration differs from previous run")
        verify_prepared(args)
        print("[PREPARE] Existing inputs verified for resume", flush=True)
    else:
        require(not args.out_dir.exists() or not any(args.out_dir.iterdir()),
                "Refusing to overwrite nonempty run output")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.out_dir / "experiment_config.json", cfg)
        write_jsonl(args.out_dir / "test_prepared.jsonl", tests)
        write_csv(args.out_dir / "test_selection.csv", [
            {k: p[k] for k in ("pair_id", "complexity_score", "complexity_block", "assigned_gpu", "prompt_sha256")}
            for p in tests], ["pair_id", "complexity_score", "complexity_block", "assigned_gpu", "prompt_sha256"])
        write_json(args.out_dir / "input_manifest.json", {
            "test_prepared_file_sha256": file_sha(args.out_dir / "test_prepared.jsonl"),
            "source_hashes": hashes, "environment": env, "seeds": cfg["seeds"]})
        print("[PREPARE] 450 read-only test inputs prepared", flush=True)
    return 0


def checkpoint_map(path, prepared, seed, gpu):
    expected = {p["pair_id"]: p for p in prepared if p["assigned_gpu"] == gpu}
    records = read_jsonl(path) if path.exists() else []
    done = {}
    for r in records:
        pid = r.get("pair_id")
        require(pid in expected and pid not in done, f"Duplicate/foreign checkpoint for GPU{gpu}: {pid}")
        p = expected[pid]
        require(r.get("seed") == seed and r.get("sample_seed") == pair_seed(seed, pid) and
                r.get("gpu_assignment") == gpu and r.get("split") == "test" and
                r.get("model") == MODEL_NAME and r.get("temperature") == TEMPERATURE and
                r.get("do_sample") is True and r.get("top_p") == TOP_P and
                r.get("top_k") == TOP_K and r.get("eos_ids") == EOS and
                r.get("prompt_sha256") == p["prompt_sha256"] and
                r.get("raw_sha256") == text_sha256(r["raw_output"]) and
                r.get("generated_tokens") == len(r["generated_token_ids"]) and
                0 < r["generated_tokens"] <= 512 and
                r.get("generated_token_ids_sha256") == text_sha256(canonical_json(r["generated_token_ids"])),
                f"Checkpoint integrity failure {pid}")
        done[pid] = r
    return done


def load_model(local_only):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1,
            "Each worker must see exactly one GPU (CUDA_VISIBLE_DEVICES)")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=local_only)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    require(tokenizer.eos_token_id == 2 and tokenizer.truncation_side == "right", "Unexpected tokenizer")
    tokenizer.padding_side = "left"
    print(f"[CUDA] {torch.cuda.get_device_name(0)}; CodeLlama-7B FP16", flush=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, trust_remote_code=True,
            torch_dtype=torch.float16, local_files_only=local_only).to("cuda:0").eval()
    runtime = {"torch": torch.__version__, "transformers": transformers.__version__,
               "gpu": torch.cuda.get_device_name(0),
               "model_revision": getattr(model.config, "_commit_hash", None),
               "tokenizer": type(tokenizer).__name__,
               "model_dtype": str(next(model.parameters()).dtype)}
    return model, tokenizer, torch, runtime


def generate_one(model, tokenizer, torch, prompt, sample_seed):
    enc = tokenizer(prompt, return_tensors="pt", truncation=True,
                    max_length=128, return_attention_mask=True)
    full_count = len(tokenizer(prompt, add_special_tokens=True).input_ids)
    ids = enc.input_ids.to("cuda:0")
    mask = enc.attention_mask.to("cuda:0")
    # Reset the RNG for EACH procedure so sample order and resume do not matter.
    # Transformers 4.36 generate() does not accept a generator= model kwarg.
    torch.manual_seed(sample_seed)
    torch.cuda.manual_seed_all(sample_seed)
    with torch.inference_mode():
        generated_full = model.generate(input_ids=ids, attention_mask=mask,
                do_sample=True, temperature=TEMPERATURE, top_p=TOP_P, top_k=TOP_K,
                max_new_tokens=512, eos_token_id=EOS,
                pad_token_id=tokenizer.eos_token_id, use_cache=True)
    tokens = generated_full[0, ids.shape[1]:].tolist()
    require(tokens, "Empty model generation")
    raw = tokenizer.decode(tokens, skip_special_tokens=False).split("<|endoftext|>", 1)[0]
    last = tokens[-1]
    term = "eos_id" if last in EOS else ("length_cap" if len(tokens) == 512 else "other")
    return {"raw_output": raw, "generated_token_ids": tokens,
            "generated_tokens": len(tokens), "last_token_id": last, "termination": term,
            "input_tokens": int(ids.shape[1]), "full_prompt_tokens": full_count,
            "prompt_truncated": full_count > 128}


def worker(args):
    require(args.gpu_index in (0, 1), "GPU worker needs --gpu-index 0 or 1")
    cfg, prepared = verify_prepared(args)
    expected = [p for p in prepared if p["assigned_gpu"] == args.gpu_index]
    seeds = cfg["seeds"]
    pending_total = 0
    for seed in seeds:
        ck = args.out_dir / f"seed{seed}_gpu{args.gpu_index}_generation.jsonl"
        completed = checkpoint_map(ck, prepared, seed, args.gpu_index)
        pending_total += len(expected) - len(completed)
        print(f"[GPU{args.gpu_index} SEED{seed}] complete={len(completed)} pending={len(expected)-len(completed)}", flush=True)
    if pending_total == 0:
        return 0
    model, tokenizer, torch, runtime = load_model(args.local_files_only)
    reference = read_json(args.run06_dir / f"gpu{args.gpu_index}_environment.json")
    for key in ("model_revision", "torch", "transformers", "tokenizer", "model_dtype"):
        require(runtime[key] == reference[key], f"GPU runtime differs from run-x-06: {key}")
    runtime.update({"python": sys.version, "executable": sys.executable,
                    "physical_gpu": os.environ.get("CUDA_VISIBLE_DEVICES"),
                    "gpu_assignment": args.gpu_index})
    env_path = args.out_dir / f"gpu{args.gpu_index}_environment.json"
    if env_path.exists():
        require(read_json(env_path) == runtime, "Resume environment mismatch")
    else:
        write_json(env_path, runtime)
    for seed in seeds:
        ck = args.out_dir / f"seed{seed}_gpu{args.gpu_index}_generation.jsonl"
        already = checkpoint_map(ck, prepared, seed, args.gpu_index)
        pending = [p for p in expected if p["pair_id"] not in already]
        for number, p in enumerate(pending, 1):
            start = time.perf_counter()
            sseed = pair_seed(seed, p["pair_id"])
            generated = generate_one(model, tokenizer, torch, p["prompt"], sseed)
            rec = {"pair_id": p["pair_id"], "split": p["split"],
                   "complexity_block": p["complexity_block"], "gpu_assignment": args.gpu_index,
                   "model": MODEL_NAME, "seed": seed, "sample_seed": sseed,
                   "temperature": TEMPERATURE, "do_sample": True, "top_p": TOP_P,
                   "top_k": TOP_K, "eos_ids": EOS, "prompt_sha256": p["prompt_sha256"],
                   **generated, "raw_sha256": text_sha256(generated["raw_output"]),
                   "generated_token_ids_sha256": text_sha256(canonical_json(generated["generated_token_ids"])),
                   "seconds": round(time.perf_counter() - start, 4)}
            append_jsonl(ck, rec)
            completed = len(already) + number
            if number <= 3 or completed % 25 == 0 or number == len(pending):
                print(f"[GPU{args.gpu_index} S{seed}] {completed}/225 {p['pair_id']} "
                      f"tokens={rec['generated_tokens']} stop={rec['termination']} "
                      f"time={rec['seconds']:.2f}s", flush=True)
        print(f"[GPU{args.gpu_index} S{seed}] COMPLETE 225/225", flush=True)
    return 0


# The AST-boundary extraction methods below are COPIED from the vetted
# run-x-06 implementation (itself based on run-x-05), to avoid a dependency
# on any previous experiment Python implementation at runtime.
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



def has_return_or_yield(root):
    return any(isinstance(n, (ast.Return, ast.Yield, ast.YieldFrom)) for n in ast.walk(root))


def finalize_seed(args, prepared, old_by_id, old_qc, seed):
    raw_by_id = {}
    for gpu in (0, 1):
        path = args.out_dir / f"seed{seed}_gpu{gpu}_generation.jsonl"
        require(path.is_file(), f"Missing checkpoint for seed {seed} GPU {gpu}")
        checked = checkpoint_map(path, prepared, seed, gpu)
        require(len(checked) == 225, f"Incomplete seed {seed} GPU {gpu}: {len(checked)}/225")
        for pid, rec in checked.items():
            require(pid not in raw_by_id, f"Double GPU assignment: {pid}")
            raw_by_id[pid] = rec
    require(len(raw_by_id) == N_TEST, f"Missing seed {seed} test generations")
    validator = import_validator(args.validator_script)
    common_t02, common_t00, t02_valid_pairs = [], [], []
    qc, extracted, combined = [], [], []
    for p in prepared:
        pid = p["pair_id"]
        r = raw_by_id[pid]
        old = old_by_id[pid]
        ref_qc = old_qc[pid]
        require(str(r["input_tokens"]) == str(ref_qc["input_tokens"]) and
                str(r["prompt_truncated"]).lower() == str(ref_qc["prompt_truncated"]).lower(),
                f"T=0.2 input tokens differ from T=0.0: {pid}")
        info = extract_one(validator, p, r)
        valid = info["status"] == "VALID"
        old_valid = old["status"] == "VALID"
        original_direct_valid = bool(old["original_t02_strict_valid"])
        incomplete = False
        nested = False
        missing_return = False
        if valid:
            htree = ast.parse(p["human_code"])
            ntree = ast.parse(info["extracted_agc_code"])
            missing_return = (has_return_or_yield(htree.body[0]) and
                              not has_return_or_yield(ntree.body[0]))
            nested = any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
                         for x in ast.walk(ntree.body[0]) if x is not ntree.body[0])
            incomplete = bool(missing_return or
                              (r["termination"] == "length_cap" and info["boundary"] == "full_continuation"))
            t02_valid_pairs.extend([
                {"idx": f"{pid}_human", "code": p["human_code"], "label": "human"},
                {"idx": f"{pid}_lm", "code": info["extracted_agc_code"], "label": "lm"},
            ])
            if old_valid:
                common_t02.extend([
                    {"idx": f"{pid}_human", "code": p["human_code"], "label": "human"},
                    {"idx": f"{pid}_lm", "code": info["extracted_agc_code"], "label": "lm"},
                ])
                common_t00.extend([
                    {"idx": f"{pid}_human", "code": p["human_code"], "label": "human"},
                    {"idx": f"{pid}_lm", "code": old["extracted_agc_code"], "label": "lm"},
                ])
        comparison = {
            "seed": seed, "pair_id": pid, "split": "test",
            "complexity_score": p["complexity_score"], "complexity_block": p["complexity_block"],
            "original_t02_direct_valid": original_direct_valid,
            "t00_valid": old_valid, "t02_controlled_valid": valid,
            "common_valid": valid and old_valid,
            "same_code_if_common": (valid and old_valid and
                                   info["extracted_agc_sha256"] == old["extracted_agc_sha256"]),
            "t00_agc_sha256": old["extracted_agc_sha256"] if old_valid else "",
            "t02_agc_sha256": info["extracted_agc_sha256"] if valid else "",
            "t02_incompleteness_warning": incomplete,
            "t00_incompleteness_warning": bool(old["missing_return_vs_hwc"] or
                                              old["length_cap_and_full_continuation"]) if old_valid else False,
        }
        combined.append(comparison)
        extracted.append({"seed": seed, "pair_id": pid, "split": "test",
                          "original_t02_direct_valid": original_direct_valid,
                          "t00_valid": old_valid,
                          "prompt_sha256": p["prompt_sha256"],
                          "raw_sha256": r["raw_sha256"], "generated_tokens": r["generated_tokens"],
                          "termination": r["termination"], "prompt_truncated": r["prompt_truncated"],
                          "input_tokens": r["input_tokens"], "gpu_assignment": r["gpu_assignment"],
                          "missing_return_vs_hwc": missing_return,
                          "nested_functions_present": nested,
                          "length_cap_and_full_continuation": r["termination"] == "length_cap" and info["boundary"] == "full_continuation",
                          "incompleteness_warning": incomplete, **info})
        qc.append({k: v for k, v in extracted[-1].items()
                   if k not in ("extracted_agc_code", "extracted_continuation")})
    valid_count = sum(r["t02_controlled_valid"] for r in combined)
    common = sum(r["common_valid"] for r in combined)
    common_same = sum(r["same_code_if_common"] for r in combined)
    require(sum(r["t00_valid"] for r in combined) == 400,
            "run-x-06 T=0.0 valid-test reference changed; expected 400")
    require(len(t02_valid_pairs) == valid_count * 2 and
            len(common_t02) == len(common_t00) == common * 2,
            "Mismatched paired data output")
    summary = {
        "experiment": "run-x-08", "version": "v1", "seed": seed, "status": "PASS",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "generated": N_TEST, "gpu0": 225, "gpu1": 225,
        "temperature": TEMPERATURE, "do_sample": True, "top_p": TOP_P, "top_k": TOP_K,
        "eos_ids": EOS, "max_new_tokens": 512,
        "t02_controlled_valid": valid_count, "t02_controlled_invalid": N_TEST - valid_count,
        "t00_reference_valid": 400, "common_valid": common,
        "common_identical_agc": common_same,
        "original_t02_direct_valid": sum(r["original_t02_direct_valid"] for r in combined),
        "prompt_truncated": sum(r["prompt_truncated"] for r in raw_by_id.values()),
        "reached_length_cap": sum(r["termination"] == "length_cap" for r in raw_by_id.values()),
        "t02_incompleteness_review_flags": sum(r["t02_incompleteness_warning"] for r in combined),
        "common_warning_free": sum(r["common_valid"] and not r["t02_incompleteness_warning"] and
                                   not r["t00_incompleteness_warning"] for r in combined),
        "new_valid_pairs_rows": len(t02_valid_pairs),
        "matched_pairs_rows_per_condition": len(common_t02),
        "limitations": ["AST validity is not behavioral completeness.",
                        "T=0.2 stochastic sampling vs T=0.0 greedy decoding is a decoding-regime comparison.",
                        "Common-valid inclusion may select easier procedures."]
    }
    prefix = f"seed{seed}"
    write_jsonl(args.out_dir / f"{prefix}_generation.jsonl", [raw_by_id[p["pair_id"]] for p in prepared])
    write_jsonl(args.out_dir / f"{prefix}_extracted_functions.jsonl", extracted)
    write_csv(args.out_dir / f"{prefix}_extraction_qc.csv", qc, list(qc[0]))
    write_csv(args.out_dir / f"{prefix}_comparison.csv", combined, list(combined[0]))
    columns = ["idx", "code", "label"]
    write_csv(args.out_dir / f"{prefix}_t02_valid_pairs.csv", t02_valid_pairs, columns)
    write_csv(args.out_dir / f"{prefix}_common_t02_pairs.csv", common_t02, columns)
    write_csv(args.out_dir / f"{prefix}_common_t00_pairs.csv", common_t00, columns)
    write_json(args.out_dir / f"{prefix}_summary.json", summary)
    print(f"[SEED {seed}] generated=450 valid={valid_count} common={common} "
          f"identical={common_same} warning_flags={summary['t02_incompleteness_review_flags']}", flush=True)
    return summary, combined


def finalize(args, env):
    cfg, prepared = verify_prepared(args)
    _, ext_test, _ = load_provenance(args)
    run06_qc = {r["pair_id"]: r for r in read_csv(args.run06_dir / "extraction_qc.csv") if r["split"] == "test"}
    require(len(run06_qc) == N_TEST, "run-x-06 QC missing test records")
    reports = []
    by_seed = {}
    for seed in cfg["seeds"]:
        report, comparisons = finalize_seed(args, prepared, ext_test, run06_qc, seed)
        reports.append(report)
        by_seed[seed] = {r["pair_id"]: r for r in comparisons}
    multi = []
    for p in prepared:
        pid = p["pair_id"]
        multi.append({"pair_id": pid,
                      "complexity_score": p["complexity_score"],
                      "valid_seed_count": sum(by_seed[s][pid]["t02_controlled_valid"] for s in cfg["seeds"]),
                      "common_seed_count": sum(by_seed[s][pid]["common_valid"] for s in cfg["seeds"]),
                      "unique_valid_agc_codes": len({by_seed[s][pid]["t02_agc_sha256"]
                          for s in cfg["seeds"] if by_seed[s][pid]["t02_controlled_valid"]})})
    write_csv(args.out_dir / "cross_seed_pair_qc.csv", multi, list(multi[0]))
    final = {"experiment": "run-x-08", "status": "PASS", "version": "v1",
             "seeds": cfg["seeds"], "n_test_per_seed": N_TEST,
             "total_generations": len(cfg["seeds"]) * N_TEST,
             "per_seed": reports,
             "all_seeds_valid_test": sum(r["valid_seed_count"] == len(cfg["seeds"]) for r in multi),
             "all_seeds_common_valid_test": sum(r["common_seed_count"] == len(cfg["seeds"]) for r in multi),
             "source_inputs_unmodified": True, "backfill": False,
             "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    write_json(args.out_dir / "controlled_summary.json", final)
    write_json(args.out_dir / "runtime_environment.json", {
        "python": env, "input_hashes": cfg["input_hashes"],
        "gpu0": read_json(args.out_dir / "gpu0_environment.json"),
        "gpu1": read_json(args.out_dir / "gpu1_environment.json")})
    lines = ["run-x-08 | Controlled CodeLlama-7B T=0.2 test generation | PASS",
             f"Seeds={cfg['seeds']} | Generated={final['total_generations']}",
             "T=0.2 sampling top_p=.95 top_k=50 EOS=[2] max_new_tokens=512",
             "T=0.0 outputs reused read-only from run-x-06; AST extraction copied exactly."]
    for r in reports:
        lines.append(f"Seed={r['seed']} valid={r['t02_controlled_valid']}/450 "
                     f"common={r['common_valid']} identical={r['common_identical_agc']} "
                     f"warning-free={r['common_warning_free']}")
    lines.extend(["NOTE: No SVM AUROC is calculated in this generation stage.",
                  "NOTE: T=0.2 sampled vs T=0.0 greedy; no assertion of pure temperature effect.",
                  "Source inputs are read-only, and invalid procedures were not backfilled."])
    atomic_text(args.out_dir / "controlled_findings.txt", "\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


def main():
    args = parse_args()
    env = check_python(args)
    if args.phase == "prepare":
        return prepare(args, env)
    if args.phase == "worker":
        return worker(args)
    return finalize(args, env)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, OSError, SyntaxError) as e:
        print(f"[ERROR] {e}", file=sys.stderr, flush=True)
        raise SystemExit(2) from e
