#!/usr/bin/env python3
"""run-x-10: CodeLlama-7B T=0.4/0.6 sampling, original 450 TEST IDs.

Independent implementation ADAPTED FROM A COPY of run-x-08-v1.
The original run-x-08 T=0.2 sample (seed 20260723) is READ ONLY and
reused as a reference. Reuse run-x-06 prompts/splits, AST-boundary function
extraction and validator, but do not import old experiment Python scripts.

Prepare / worker / finalize are separate phases, with append-only checkpoints,
strict input hashes and a three-temperature common-valid matched test set.
This stage does not calculate classifier AUROC or modify original data.
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
TEMPERATURES = {"t04": 0.4, "t06": 0.6}
TOP_P = 0.95
TOP_K = 50
EOS = [2]
N_TEST = 450
REFERENCE_SEED = 20260723


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
    spec = importlib.util.spec_from_file_location("run_x_10_original_validator", str(path))
    require(spec is not None and spec.loader is not None, "Cannot import validator")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    for fn in ("compose_code", "syntax_check", "code_has_required_structure"):
        require(hasattr(mod, fn), f"Validator API missing: {fn}")
    return mod


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", choices=("prepare", "worker", "finalize"), required=True)
    p.add_argument("--run06-dir", required=True, type=Path)
    p.add_argument("--run08-dir", required=True, type=Path)
    p.add_argument("--validator-script", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--seed", type=int, default=REFERENCE_SEED)
    p.add_argument("--gpu-index", type=int, choices=(0, 1))
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--offline-allow-non311", action="store_true",
                   help="Offline preflight only, never allowed for model inference")
    return p.parse_args()


def pair_seed(seed, pair_id, temperature_tag):
    """Per-(pair,seed,temperature) RNG, invariant to order/GPU/resumption."""
    digest = hashlib.sha256(
        f"run-x-10:{seed}:{temperature_tag}:{pair_id}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63 - 1)


def pair_seed_run08(seed, pair_id):
    """Verify the independent run-x-08 RNG algorithm on saved raw outputs."""
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


def load_run08_reference(args, tests, run06_hashes):
    """Independently verify run-x-08 T=0.2 provenance and all 450 saved results."""
    base = args.run08_dir
    cfg = read_json(base / "experiment_config.json")
    summary = read_json(base / f"seed{args.seed}_summary.json")
    manifest = read_json(base / "input_manifest.json")
    require(cfg.get("experiment") == "run-x-08" and cfg.get("version") == "v1" and
            cfg.get("model") == MODEL_NAME and cfg.get("temperature") == 0.2 and
            cfg.get("do_sample") is True and cfg.get("top_p") == TOP_P and
            cfg.get("top_k") == TOP_K and cfg.get("eos_ids") == EOS and
            cfg.get("prompt_max_tokens") == 128 and cfg.get("max_new_tokens") == 512 and
            args.seed in cfg.get("seeds", []), "run-x-08 temperature/seed configuration mismatch")
    require(cfg.get("input_hashes") == run06_hashes and
            cfg.get("original_run06") == str(args.run06_dir.resolve()),
            "run-x-08 does not point to exactly the verified run-x-06 source")
    require(summary.get("status") == "PASS" and summary.get("seed") == args.seed and
            summary.get("generated") == 450 and summary.get("t02_controlled_valid") == 404 and
            summary.get("common_valid") == 382,
            "run-x-08 must be the completed audited T=0.2 run")
    source_test = base / "test_prepared.jsonl"
    require(file_sha(source_test) == manifest["test_prepared_file_sha256"],
            "run-x-08 prepared test bytes changed")
    ref_test = read_jsonl(source_test)
    require(ref_test == tests and text_sha256(canonical_json(ref_test)) == cfg["test_prepared_sha256"],
            "run-x-08 test prompts/splits disagree with run-x-06")
    id_map = {p["pair_id"]: p for p in tests}
    gen_file = base / f"seed{args.seed}_generation.jsonl"
    ext_file = base / f"seed{args.seed}_extracted_functions.jsonl"
    comp_file = base / f"seed{args.seed}_comparison.csv"
    pairs_file = base / f"seed{args.seed}_t02_valid_pairs.csv"
    raw = read_jsonl(gen_file)
    ext = read_jsonl(ext_file)
    comp = read_csv(comp_file)
    rows = read_csv(pairs_file)
    require(len(raw) == len(ext) == len(comp) == N_TEST,
            "run-x-08 must contain exactly 450 generation/extraction/comparison records")
    require(len(rows) == 808, "run-x-08 must contain exactly 404 matched HWC/AGC pairs")
    require(len({r["pair_id"] for r in raw}) == N_TEST and
            len({r["pair_id"] for r in ext}) == N_TEST and
            len({r["pair_id"] for r in comp}) == N_TEST,
            "run-x-08 duplicate/missing test pair IDs")
    gen_by_id = {r["pair_id"]: r for r in raw}
    ext_by_id = {r["pair_id"]: r for r in ext}
    comp_by_id = {r["pair_id"]: r for r in comp}
    for pid, p in id_map.items():
        gen = gen_by_id[pid]
        e = ext_by_id[pid]
        c = comp_by_id[pid]
        require(gen["prompt_sha256"] == p["prompt_sha256"] and
                gen["raw_sha256"] == text_sha256(gen["raw_output"]) and
                gen["seed"] == args.seed and gen["sample_seed"] == pair_seed_run08(args.seed, pid) and
                gen["temperature"] == 0.2 and gen["do_sample"] is True and
                gen["top_p"] == TOP_P and gen["top_k"] == TOP_K and gen["eos_ids"] == EOS and
                len(gen["generated_token_ids"]) == gen["generated_tokens"] and
                gen["generated_token_ids_sha256"] == text_sha256(canonical_json(gen["generated_token_ids"])) and
                e["prompt_sha256"] == p["prompt_sha256"] and
                e["raw_sha256"] == gen["raw_sha256"] and
                e["status"] in {"VALID", "INVALID"},
                f"run-x-08 generation/extraction integrity mismatch: {pid}")
        valid = e["status"] == "VALID"
        require(str(c["t02_controlled_valid"]).lower() == str(valid).lower() and
                (not valid or (e["extracted_agc_sha256"] == text_sha256(e["extracted_agc_code"]) ==
                               c["t02_agc_sha256"])),
                f"run-x-08 validity/code hash mismatch: {pid}")
    require(sum(e["status"] == "VALID" for e in ext) == 404, "run-x-08 validity drift")
    pair_by_idx = {r["idx"]: r for r in rows}
    require(len(pair_by_idx) == 808, "run-x-08 final paired rows contain duplicate IDs")
    for pid, p in id_map.items():
        e = ext_by_id[pid]
        if e["status"] == "VALID":
            h = pair_by_idx[pid + "_human"]
            a = pair_by_idx[pid + "_lm"]
            require(h["code"] == p["human_code"] and h["label"] == "human" and
                    a["code"] == e["extracted_agc_code"] and a["label"] == "lm",
                    f"run-x-08 final HWC/AGC CSV mismatch: {pid}")
    source_paths = [base / "experiment_config.json", base / "input_manifest.json",
                    base / f"seed{args.seed}_summary.json", source_test,
                    gen_file, ext_file, comp_file, pairs_file]
    hashes = {path.name: file_sha(path) for path in source_paths}
    return ext_by_id, comp_by_id, hashes


def experiment_config(args, tests, run06_hashes, run08_hashes):
    return {
        "experiment": "run-x-10", "version": "v1",
        "design": "T=0.4/T=0.6 CodeLlama sampling on 450 held test IDs; reuse run-x-08 T=0.2",
        "model": MODEL_NAME, "temperatures": TEMPERATURES,
        "do_sample": True, "top_p": TOP_P, "top_k": TOP_K, "eos_ids": EOS,
        "prompt_max_tokens": 128, "max_new_tokens": 512,
        "seed": args.seed, "rng_policy": "SHA256(run-x-10:seed:temperature_tag:pair_id), torch.manual_seed per sample",
        "run06_dir": str(args.run06_dir.resolve()), "run08_dir": str(args.run08_dir.resolve()),
        "run06_source_hashes": run06_hashes, "run08_source_hashes": run08_hashes,
        "test_prepared_sha256": text_sha256(canonical_json(tests)),
        "expected_test": N_TEST, "gpu_assignment": "reuse run-x-06 complexity blocks modulo 2",
        "read_only_inputs": True, "invalid_backfill": False,
        "sampling_temperature_not_tuned_from_detector_scores": True,
    }


def verify_prepared(args):
    cfg = read_json(args.out_dir / "experiment_config.json")
    tests, _, hashes = load_provenance(args)
    t02, comparison, run08_hashes = load_run08_reference(args, tests, hashes)
    expected = experiment_config(args, tests, hashes, run08_hashes)
    require(cfg == expected, "run-x-10 configuration/input source hashes changed since preparation")
    test_path = args.out_dir / "test_prepared.jsonl"
    require(file_sha(test_path) == read_json(args.out_dir / "input_manifest.json")["test_prepared_file_sha256"],
            "Prepared test file bytes changed")
    local_tests = read_jsonl(test_path)
    require(local_tests == tests and text_sha256(canonical_json(local_tests)) == cfg["test_prepared_sha256"],
            "run-x-10 prepared procedures changed")
    return cfg, tests, t02, comparison


def prepare(args, env):
    tests, _, hashes = load_provenance(args)
    t02, comparison, run08_hashes = load_run08_reference(args, tests, hashes)
    cfg = experiment_config(args, tests, hashes, run08_hashes)
    require(len(t02) == len(comparison) == N_TEST, "Reference source missing procedures")
    print(f"[INPUT] run-x-06 + run-x-08 provenance PASS; test=450; "
          f"T02_valid=404; new_temps=[0.4,0.6]; seed={args.seed}; "
          "GPU0=225 GPU1=225", flush=True)
    if args.dry_run:
        print("[DRY-RUN] PASS; no GPU model loading or output directory creation", flush=True)
        return 0
    if args.resume:
        require(read_json(args.out_dir / "experiment_config.json") == cfg,
                "RESUME configuration or source input hashes differ")
        verify_prepared(args)
        print("[PREPARE] Existing input snapshot verified for resume", flush=True)
    else:
        require(not args.out_dir.exists() or not any(args.out_dir.iterdir()),
                "Refusing to overwrite an existing nonempty output directory")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.out_dir / "experiment_config.json", cfg)
        write_jsonl(args.out_dir / "test_prepared.jsonl", tests)
        write_csv(args.out_dir / "test_selection.csv", [
            {k: p[k] for k in ("pair_id", "complexity_score", "complexity_block", "assigned_gpu", "prompt_sha256")}
            for p in tests], ["pair_id", "complexity_score", "complexity_block", "assigned_gpu", "prompt_sha256"])
        write_json(args.out_dir / "input_manifest.json", {
            "test_prepared_file_sha256": file_sha(args.out_dir / "test_prepared.jsonl"),
            "run06_source_hashes": hashes, "run08_source_hashes": run08_hashes,
            "python": env, "seed": args.seed, "temperature_tags": list(TEMPERATURES)})
        print("[PREPARE] Snapshot of 450 original test inputs saved; old runs untouched", flush=True)
    return 0
def checkpoint_map(path, prepared, seed, gpu, tag):
    expected = {p["pair_id"]: p for p in prepared if p["assigned_gpu"] == gpu}
    done = {}
    for r in (read_jsonl(path) if path.exists() else []):
        pid = r.get("pair_id")
        require(pid in expected and pid not in done, f"Duplicate/foreign checkpoint on GPU{gpu}: {pid}")
        p = expected[pid]
        require(r.get("seed") == seed and r.get("sample_seed") == pair_seed(seed, pid, tag) and
                r.get("temperature_tag") == tag and r.get("temperature") == TEMPERATURES[tag] and
                r.get("gpu_assignment") == gpu and r.get("split") == "test" and
                r.get("model") == MODEL_NAME and r.get("do_sample") is True and
                r.get("top_p") == TOP_P and r.get("top_k") == TOP_K and
                r.get("eos_ids") == EOS and r.get("prompt_sha256") == p["prompt_sha256"] and
                r.get("raw_sha256") == text_sha256(r["raw_output"]) and
                0 < r["generated_tokens"] <= 512 and
                r["generated_tokens"] == len(r["generated_token_ids"]) and
                r.get("last_token_id") == r["generated_token_ids"][-1] and
                r.get("generated_token_ids_sha256") == text_sha256(canonical_json(r["generated_token_ids"])),
                f"Checkpoint integrity failure for {pid} at {tag}")
        done[pid] = r
    return done


def generate_one(model, tokenizer, torch, prompt, sample_seed, temp):
    """Same run-x-08 tokenizer/decoding, except the controlled temperature."""
    enc = tokenizer(prompt, return_tensors="pt", truncation=True,
                    max_length=128, return_attention_mask=True)
    full_count = len(tokenizer(prompt, add_special_tokens=True).input_ids)
    ids = enc.input_ids.to("cuda:0")
    mask = enc.attention_mask.to("cuda:0")
    # Reset RNG for each sample; unaffected by GPU assignment, order or restart.
    torch.manual_seed(sample_seed)
    torch.cuda.manual_seed_all(sample_seed)
    with torch.inference_mode():
        generated_full = model.generate(input_ids=ids, attention_mask=mask,
                do_sample=True, temperature=temp, top_p=TOP_P, top_k=TOP_K,
                max_new_tokens=512, eos_token_id=EOS,
                pad_token_id=tokenizer.eos_token_id, use_cache=True)
    tokens = generated_full[0, ids.shape[1]:].tolist()
    require(tokens, "Model returned an empty generation")
    raw = tokenizer.decode(tokens, skip_special_tokens=False).split("<|endoftext|>", 1)[0]
    last = tokens[-1]
    term = "eos_id" if last in EOS else ("length_cap" if len(tokens) == 512 else "other")
    return {"raw_output": raw, "generated_token_ids": tokens,
            "generated_tokens": len(tokens), "last_token_id": last, "termination": term,
            "input_tokens": int(ids.shape[1]), "full_prompt_tokens": full_count,
            "prompt_truncated": full_count > 128}


def worker(args):
    require(args.gpu_index in (0, 1), "GPU worker needs --gpu-index 0 or 1")
    cfg, prepared, _, _ = verify_prepared(args)
    expected = [p for p in prepared if p["assigned_gpu"] == args.gpu_index]
    require(len(expected) == 225, "Wrong GPU partition")
    pending_total = 0
    for tag in TEMPERATURES:
        ck = args.out_dir / f"seed{args.seed}_{tag}_gpu{args.gpu_index}_generation.jsonl"
        already = checkpoint_map(ck, prepared, args.seed, args.gpu_index, tag)
        pending_total += len(expected) - len(already)
        print(f"[GPU{args.gpu_index} {tag}] completed={len(already)} pending={len(expected)-len(already)}", flush=True)
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
        require(read_json(env_path) == runtime, "Resume GPU environment differs")
    else:
        write_json(env_path, runtime)
    for tag, temp in TEMPERATURES.items():
        ck = args.out_dir / f"seed{args.seed}_{tag}_gpu{args.gpu_index}_generation.jsonl"
        already = checkpoint_map(ck, prepared, args.seed, args.gpu_index, tag)
        pending = [p for p in expected if p["pair_id"] not in already]
        for number, p in enumerate(pending, 1):
            start = time.perf_counter()
            sseed = pair_seed(args.seed, p["pair_id"], tag)
            generated = generate_one(model, tokenizer, torch, p["prompt"], sseed, temp)
            rec = {"pair_id": p["pair_id"], "split": "test",
                   "complexity_block": p["complexity_block"], "gpu_assignment": args.gpu_index,
                   "model": MODEL_NAME, "seed": args.seed, "sample_seed": sseed,
                   "temperature_tag": tag, "temperature": temp,
                   "do_sample": True, "top_p": TOP_P, "top_k": TOP_K,
                   "eos_ids": EOS, "prompt_sha256": p["prompt_sha256"],
                   **generated, "raw_sha256": text_sha256(generated["raw_output"]),
                   "generated_token_ids_sha256": text_sha256(canonical_json(generated["generated_token_ids"])),
                   "seconds": round(time.perf_counter() - start, 4)}
            append_jsonl(ck, rec)
            completed = len(already) + number
            if number <= 3 or completed % 25 == 0 or number == len(pending):
                print(f"[GPU{args.gpu_index} {tag}] {completed}/225 {p['pair_id']} "
                      f"tokens={rec['generated_tokens']} stop={rec['termination']} "
                      f"time={rec['seconds']:.2f}s", flush=True)
        print(f"[GPU{args.gpu_index} {tag}] COMPLETE 225/225", flush=True)
    return 0


# AST extraction helpers below are copied VERBATIM from run-x-08-v1.
# Keeping a local copy avoids a runtime dependency on earlier Python scripts.
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


def has_true(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def finalize(args, env):
    cfg, prepared, t02_ext, t02_comp = verify_prepared(args)
    r06_qc = {r["pair_id"]: r for r in read_csv(args.run06_dir / "extraction_qc.csv")
              if r.get("split") == "test"}
    require(len(r06_qc) == N_TEST, "run-x-06 TEST QC must have 450 IDs")
    validator = import_validator(args.validator_script)
    per_tag = {}
    per_tag_summaries = {}
    temp_valid_pairs = {}
    for tag, temp in TEMPERATURES.items():
        raw_by_id = {}
        for gpu in (0, 1):
            ck = args.out_dir / f"seed{args.seed}_{tag}_gpu{gpu}_generation.jsonl"
            require(ck.is_file(), f"Missing {tag} GPU{gpu} checkpoint")
            checked = checkpoint_map(ck, prepared, args.seed, gpu, tag)
            require(len(checked) == 225, f"Incomplete {tag} GPU{gpu}: {len(checked)}/225")
            for pid, r in checked.items():
                require(pid not in raw_by_id, f"Duplicated GPU record for {pid} {tag}")
                raw_by_id[pid] = r
        require(len(raw_by_id) == N_TEST, f"Missing raw generations for {tag}")
        extracted, qc, rows, valid_ids = [], [], [], {}
        for p in prepared:
            pid = p["pair_id"]
            r = raw_by_id[pid]
            r06 = r06_qc[pid]
            require(str(r["input_tokens"]) == str(r06["input_tokens"]) and
                    str(r["prompt_truncated"]).lower() == str(r06["prompt_truncated"]).lower(),
                    f"Prompt tokenization differs from T=0.0: {pid}")
            info = extract_one(validator, p, r)
            valid = info["status"] == "VALID"
            missing_return = False
            nested = False
            if valid:
                htree = ast.parse(p["human_code"])
                ntree = ast.parse(info["extracted_agc_code"])
                missing_return = (has_return_or_yield(htree.body[0]) and
                                  not has_return_or_yield(ntree.body[0]))
                nested = any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
                             for x in ast.walk(ntree.body[0]) if x is not ntree.body[0])
                valid_ids[pid] = info
                rows.extend([
                    {"idx": f"{pid}_human", "code": p["human_code"], "label": "human"},
                    {"idx": f"{pid}_lm", "code": info["extracted_agc_code"], "label": "lm"},
                ])
            incomplete = bool(valid and (missing_return or
                              (r["termination"] == "length_cap" and info["boundary"] == "full_continuation")))
            e = {"seed": args.seed, "pair_id": pid, "split": "test",
                 "temperature_tag": tag, "temperature": temp,
                 "prompt_sha256": p["prompt_sha256"],
                 "raw_sha256": r["raw_sha256"], "generated_tokens": r["generated_tokens"],
                 "termination": r["termination"], "prompt_truncated": r["prompt_truncated"],
                 "input_tokens": r["input_tokens"], "gpu_assignment": r["gpu_assignment"],
                 "missing_return_vs_hwc": missing_return, "nested_functions_present": nested,
                 "length_cap_and_full_continuation": bool(valid and r["termination"] == "length_cap"
                                                         and info["boundary"] == "full_continuation"),
                 "incompleteness_warning": incomplete, **info}
            extracted.append(e)
            qc.append({k: v for k, v in e.items()
                       if k not in ("extracted_agc_code", "extracted_continuation")})
        valid_count = len(valid_ids)
        require(len(rows) == 2 * valid_count and
                len({r["idx"] for r in rows}) == len(rows), f"{tag} paired CSV integrity failure")
        prefix = f"seed{args.seed}_{tag}"
        write_jsonl(args.out_dir / f"{prefix}_generation.jsonl", [raw_by_id[p["pair_id"]] for p in prepared])
        write_jsonl(args.out_dir / f"{prefix}_extracted_functions.jsonl", extracted)
        write_csv(args.out_dir / f"{prefix}_extraction_qc.csv", qc, list(qc[0]))
        write_csv(args.out_dir / f"{prefix}_valid_pairs.csv", rows, ["idx", "code", "label"])
        summary = {"experiment": "run-x-10", "version": "v1", "status": "PASS",
                   "seed": args.seed, "temperature": temp, "temperature_tag": tag,
                   "generated": N_TEST, "gpu0": 225, "gpu1": 225,
                   "valid": valid_count, "invalid": N_TEST - valid_count,
                   "valid_rate": valid_count / N_TEST,
                   "prompt_truncated": sum(r["prompt_truncated"] for r in raw_by_id.values()),
                   "reached_length_cap": sum(r["termination"] == "length_cap" for r in raw_by_id.values()),
                   "incompleteness_warning": sum(r["incompleteness_warning"] for r in extracted),
                   "valid_pairs_rows": len(rows), "backfilled": False}
        write_json(args.out_dir / f"{prefix}_summary.json", summary)
        per_tag[tag] = {e["pair_id"]: e for e in extracted}
        per_tag_summaries[tag] = summary
        temp_valid_pairs[tag] = valid_ids
        print(f"[FINALIZE {tag}] generated=450 valid={valid_count} "
              f"invalid={450 - valid_count} warning={summary['incompleteness_warning']}", flush=True)

    comparisons, common_rows = [], {"t02": [], "t04": [], "t06": []}
    common_ids = []
    for p in prepared:
        pid = p["pair_id"]
        ref = t02_ext[pid]
        a = per_tag["t04"][pid]
        b = per_tag["t06"][pid]
        v02 = ref["status"] == "VALID"
        v04 = a["status"] == "VALID"
        v06 = b["status"] == "VALID"
        triple = v02 and v04 and v06
        hash02 = ref["extracted_agc_sha256"] if v02 else ""
        hash04 = a["extracted_agc_sha256"] if v04 else ""
        hash06 = b["extracted_agc_sha256"] if v06 else ""
        t02_warning = has_true(t02_comp[pid]["t02_incompleteness_warning"]) if v02 else False
        t04_warning = bool(a["incompleteness_warning"]) if v04 else False
        t06_warning = bool(b["incompleteness_warning"]) if v06 else False
        comparisons.append({"seed": args.seed, "pair_id": pid, "split": "test",
                            "complexity_score": p["complexity_score"],
                            "complexity_block": p["complexity_block"],
                            "human_sha256": p["human_sha256"],
                            "t02_valid": v02, "t04_valid": v04, "t06_valid": v06,
                            "common_valid_all3": triple,
                            "t02_agc_sha256": hash02, "t04_agc_sha256": hash04, "t06_agc_sha256": hash06,
                            "t02_warning": t02_warning, "t04_warning": t04_warning,
                            "t06_warning": t06_warning,
                            "common_warning_free_all3": triple and not (
                                t02_warning or t04_warning or t06_warning),
                            "identical_t02_t04": triple and hash02 == hash04,
                            "identical_t02_t06": triple and hash02 == hash06,
                            "identical_t04_t06": triple and hash04 == hash06,
                            "identical_all3": triple and hash02 == hash04 == hash06})
        if triple:
            common_ids.append(pid)
            for tag, code in (("t02", ref["extracted_agc_code"]),
                              ("t04", a["extracted_agc_code"]),
                              ("t06", b["extracted_agc_code"])):
                common_rows[tag].extend([
                    {"idx": pid + "_human", "code": p["human_code"], "label": "human"},
                    {"idx": pid + "_lm", "code": code, "label": "lm"},
                ])
    require(len(comparisons) == N_TEST and len({r["pair_id"] for r in comparisons}) == N_TEST,
            "Comparison must cover 450 unique test IDs")
    require(sum(e["t02_valid"] for e in comparisons) == 404,
            "Audited T=0.2 source validity changed")
    common_count = len(common_ids)
    require(all(len(rows) == 2 * common_count for rows in common_rows.values()),
            "Three-temperature common-valid paired rows differ")
    indexes = [[r["idx"] for r in common_rows[tag]] for tag in ("t02", "t04", "t06")]
    require(indexes[0] == indexes[1] == indexes[2] and
            len(set(indexes[0])) == len(indexes[0]),
            "Three-temperature common-valid pair ID alignment failed")
    for tag in ("t02", "t04", "t06"):
        write_csv(args.out_dir / f"seed{args.seed}_common_{tag}_pairs.csv",
                  common_rows[tag], ["idx", "code", "label"])
    write_csv(args.out_dir / f"seed{args.seed}_comparison.csv", comparisons, list(comparisons[0]))
    write_csv(args.out_dir / f"seed{args.seed}_common_ids.csv",
              [{"pair_id": pid} for pid in common_ids], ["pair_id"])

    final = {"experiment": "run-x-10", "status": "PASS", "version": "v1",
             "timestamp_utc": datetime.now(timezone.utc).isoformat(),
             "seed": args.seed, "n_original_test": N_TEST,
             "temperatures": {"t02": 0.2, **TEMPERATURES},
             "generated_new": 900, "reused_t02": 450,
             "valid_by_temperature": {"t02": 404,
                                       "t04": per_tag_summaries["t04"]["valid"],
                                       "t06": per_tag_summaries["t06"]["valid"]},
             "common_valid_all3": common_count,
             "common_pairs_rows_per_temperature": common_count * 2,
             "common_warning_free_all3": sum(r["common_warning_free_all3"] for r in comparisons),
             "identical_all3": sum(r["identical_all3"] for r in comparisons),
             "common_identical_t02_t04": sum(r["identical_t02_t04"] for r in comparisons),
             "common_identical_t02_t06": sum(r["identical_t02_t06"] for r in comparisons),
             "common_identical_t04_t06": sum(r["identical_t04_t06"] for r in comparisons),
             "input_hashes": cfg["run06_source_hashes"],
             "t02_reference_hashes": cfg["run08_source_hashes"],
             "source_data_modified": False, "invalid_backfilled": False,
             "limitations": ["AST validity is not behavioral completeness.",
                             "Only one sampling seed is evaluated.",
                             "Common-valid inclusion can change complexity distribution."]}
    write_json(args.out_dir / "multitemp_summary.json", final)
    write_json(args.out_dir / "runtime_environment.json", {
        "python": env, "input_hashes": cfg["run06_source_hashes"],
        "t02_reference_hashes": cfg["run08_source_hashes"],
        "gpu0": read_json(args.out_dir / "gpu0_environment.json"),
        "gpu1": read_json(args.out_dir / "gpu1_environment.json")})
    lines = ["run-x-10 | Controlled CodeLlama-7B T=0.4,0.6 generation | PASS",
             f"Seed={args.seed} new_generations=900 reused_T02=450",
             "All temperatures: top_p=0.95 top_k=50 EOS=[2] max_new_tokens=512",
             f"VALID: T02=404, T04={per_tag_summaries['t04']['valid']}, T06={per_tag_summaries['t06']['valid']}",
             f"Common-valid(all 3)={common_count}; warning-free={final['common_warning_free_all3']}",
             f"Common paired CSV rows per temperature={common_count * 2}",
             "NOTE: No AUROC calculated; use same common_valid IDs for all temperatures in run-x-11.",
             "NOTE: Seed is fixed; additional seeds would require matching T02 source data.",
             "Original source data and run-x-08 T02 outputs were not modified; no invalid backfill."]
    atomic_text(args.out_dir / "multitemp_findings.txt", "\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


def main():
    args = parse_args()
    env = check_python(args)
    require(args.seed == REFERENCE_SEED,
            "This v1 run intentionally uses the audited T=0.2 reference seed 20260723")
    if args.phase == "prepare":
        return prepare(args, env)
    if args.phase == "worker":
        return worker(args)
    return finalize(args, env)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, OSError, SyntaxError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr, flush=True)
        raise SystemExit(2) from exc
