#!/usr/bin/env python3
"""run-x-04: independent CodeLlama-7B T=0.0 EOS ablation.

Read-only inputs:
  run-x-02/20261012-140235-6379/experiment_config.json
  run-x-02/20261012-140235-6379/pilot_prepared.jsonl
  run-x-02/20261012-140235-6379/pilot_selection.csv
  run-x-02/20261012-140235-6379/pilot_generation.jsonl
  Original paired CSV and complexity split manifest (integrity checks only)
  Original code-generation/find_validsyntax_mgc.py validator (Python import)
  Hugging Face CodeLlama-7B weights and tokenizer

New outputs, isolated under run-x-04/<RUN_ID>/:
  experiment_config.json, ablation_generation.jsonl (append-only checkpoint)
  ablation_qc.csv, ablation_comparison.csv, last_token_counts.csv
  model_environment.json, ablation_summary.json, ablation_findings.txt

Design:
  A (legacy): [2, 822, 29871], REUSED from run-x-02; no final token ID.
  B (no_boundary): [2, 822], newly generated; final token ID recorded.
  C (standard): [2], newly generated; final token ID recorded.
  All configurations use do_sample=False, matched prompts and the same
  prompt/max-generation token limits. No previous inputs are modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODES = ("no_boundary", "standard")
LEGACY_IDS = (2, 822, 29871)
EOS_BY_MODE = {"no_boundary": (2, 822), "standard": (2,)}


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot-dir", type=Path, required=True)
    ap.add_argument("--validator-script", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--model-name", default="codellama/CodeLlama-7b-hf")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--local-files-only", action="store_true")
    return ap.parse_args()


def fail(msg):
    raise RuntimeError(msg)


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(buf)
    return digest.hexdigest()


def hash_text(s: str):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def read_jsonl(path: Path):
    items = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as exc:
                fail(f"Malformed JSONL {path}:{number}: {exc}")
    return items


def write_json(path: Path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_csv(path: Path, rows, cols):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(handle, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def append_jsonl(path: Path, item):
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def import_validator(path: Path):
    name = "run_x_04_original_validator"
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        fail(f"Cannot import original validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    for func in ("process_obj", "compose_code", "syntax_check", "code_has_required_structure"):
        if not hasattr(module, func):
            fail(f"Validator missing function: {func}")
    return module


def load_inputs(args):
    pilot = args.pilot_dir
    required = ["experiment_config.json", "pilot_prepared.jsonl", "pilot_selection.csv", "pilot_generation.jsonl"]
    for file in required:
        if not (pilot / file).is_file():
            fail(f"Missing run-x-02 input: {pilot / file}")
    original = json.loads((pilot / "experiment_config.json").read_text(encoding="utf-8"))
    expected = {"experiment": "run-x-02", "mode": "T0_GREEDY", "temperature": 0.0,
                "do_sample": False, "top_p": None}
    for name, val in expected.items():
        if original.get(name) != val:
            fail(f"run-x-02 config mismatch on {name}: {original.get(name)}")
    if original.get("model") != args.model_name:
        fail("Model name differs from run-x-02 baseline")
    for key, hash_key in (("original_csv", "original_csv_sha256"),
                          ("split_manifest", "split_manifest_sha256"),
                          ("validator_script", "validator_script_sha256")):
        path = Path(original[key])
        if not path.is_file():
            fail(f"Original source missing: {path}")
        if sha256(path) != original[hash_key]:
            fail(f"Original source hash changed: {path}")
    if args.validator_script.resolve() != Path(original["validator_script"]).resolve():
        fail("Validator argument does not match original run-x-02 validator")

    prepared = read_jsonl(pilot / "pilot_prepared.jsonl")
    legacy = read_jsonl(pilot / "pilot_generation.jsonl")
    total = int(original["pilot_pairs"])
    if total != 100 or len(prepared) != total or len(legacy) != total:
        fail(f"Expected completed 100-pair run-x-02; got prepared={len(prepared)} legacy={len(legacy)}")
    if hash_text(canonical_json(prepared)) != original["selected_pairs_sha256"]:
        fail("Prepared prompt provenance does not match run-x-02 config")
    pair_ids = [r["pair_id"] for r in prepared]
    if len(set(pair_ids)) != total:
        fail("Duplicate prepared pair IDs")
    legacy_map = {}
    for r in legacy:
        pid = r["pair_id"]
        if pid in legacy_map or pid not in pair_ids:
            fail(f"Duplicate/unexpected legacy pair: {pid}")
        legacy_map[pid] = r
    with (pilot / "pilot_selection.csv").open(newline="", encoding="utf-8") as stream:
        selected = list(csv.DictReader(stream))
    if len(selected) != total or set(p["pair_id"] for p in selected) != set(pair_ids):
        fail("run-x-02 pilot_selection.csv disagrees with prepared data")
    for r in prepared:
        prior = legacy_map[r["pair_id"]]
        if (r["prompt_sha256"] != hash_text(r["prompt"])
                or r["human_sha256"] != hash_text(r["human_code"])
                or prior["prompt_sha256"] != r["prompt_sha256"]
                or prior["new_agc_sha256"] != hash_text(prior["new_agc_code"])
                or prior["split"] != r["split"]
                or prior["complexity_block"] != r["complexity_block"]
                or prior["generated_tokens"] > original["max_new_tokens"]):
            fail(f"run-x-02 prompt/result integrity failure: {r['pair_id']}")
    config = {
        "experiment": "run-x-04", "design": "EOS ablation on T=0.0 greedy CodeLlama-7B",
        "model": args.model_name,
        "legacy_eos_ids": list(LEGACY_IDS),
        "ablation_eos_ids": {k: list(v) for k, v in EOS_BY_MODE.items()},
        "do_sample": False, "temperature_argument": None, "top_p_argument": None,
        "prompt_max_tokens": int(original["prompt_max_tokens"]),
        "max_new_tokens": int(original["max_new_tokens"]),
        "pilot_dir": str(pilot.resolve()),
        "pilot_hashes": {n: sha256(pilot / n) for n in required},
        "original_validator_sha256": sha256(args.validator_script),
        "pair_count": total,
        "selection_sha256": original["selected_pairs_sha256"],
    }
    return original, prepared, legacy_map, config


def load_model(model_name, local_files_only):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if not torch.cuda.is_available():
        fail("CUDA GPU required for EOS ablation")
    tok = AutoTokenizer.from_pretrained(model_name, local_files_only=local_files_only)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"
    # Match run-x-02 default truncation (right) without changing decoding.
    if tok.truncation_side != "right":
        fail(f"Unexpected tokenizer truncation side: {tok.truncation_side}")
    def_id = tok("def", add_special_tokens=False).input_ids[0]
    try:
        def_space_id = tok("def", add_prefix_space=True, add_special_tokens=False).input_ids[0]
    except Exception:
        def_space_id = tok(" def", add_special_tokens=False).input_ids[0]
    resolved = tuple(dict.fromkeys((tok.eos_token_id, def_id, def_space_id)))
    if resolved != LEGACY_IDS:
        fail(f"EOS IDs changed from original source logic: resolved={resolved} expected={LEGACY_IDS}")
    print(f"[CUDA] GPU={torch.cuda.get_device_name(0)}, visible GPUs={torch.cuda.device_count()}", flush=True)
    print(f"[TOKENIZER] original EOS IDs={list(resolved)}", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, torch_dtype=torch.float16,
        local_files_only=local_files_only,
    ).to("cuda:0")
    model.eval()
    env = {
        "model_name": model_name,
        "resolved_revision": getattr(model.config, "_commit_hash", None),
        "torch_version": torch.__version__, "transformers_version": transformers.__version__,
        "gpu_name": torch.cuda.get_device_name(0),
        "model_dtype": str(next(model.parameters()).dtype),
        "tokenizer_type": type(tok).__name__,
        "legacy_eos": [{"id": x, "token": tok.convert_ids_to_tokens(x),
                        "decode": tok.decode([x], skip_special_tokens=False)} for x in resolved],
        "truncation_side": tok.truncation_side,
    }
    return model, tok, torch, env


def generate_one(model, tok, torch, prompt, eos_ids, prompt_cap, max_new):
    # Match the original run-x-02 tokenizer/model.generate settings exactly.
    inputs = tok(prompt, return_tensors="pt", truncation=True,
                 max_length=prompt_cap, return_attention_mask=True)
    ids = inputs.input_ids.to("cuda:0")
    mask = inputs.attention_mask.to("cuda:0")
    with torch.inference_mode():
        out = model.generate(
            input_ids=ids, attention_mask=mask, do_sample=False,
            max_new_tokens=max_new, pad_token_id=tok.eos_token_id,
            eos_token_id=list(eos_ids), use_cache=True,
        )
    new_ids = out[0, ids.shape[1]:]
    ids_list = new_ids.tolist()
    last_id = ids_list[-1] if ids_list else None
    if last_id in eos_ids:
        why = "eos_id"
    elif len(ids_list) == max_new:
        why = "length_cap"
    else:
        why = "other"
    raw = tok.decode(new_ids, skip_special_tokens=False).split("<|endoftext|>", 1)[0]
    return raw, int(ids.shape[1]), len(ids_list), last_id, why


def validate_attempt(validator, prepared, mode, raw, input_tokens, n_tokens, final_id, termination, seconds, model_name):
    p = validator.process_obj({
        "prompt": prepared["prompt"], "solution": prepared["solution"], "output": raw,
        "source_line_no": "", "filter_index": "",
    }, line_no=1)
    new_code = p.mgc_code
    syn = validator.syntax_check(new_code)
    if syn.ok:
        structure_ok, reason = validator.code_has_required_structure(new_code)
    else:
        structure_ok, reason = False, syn.error or "syntax invalid"
    human_ok = p.hwc_ok and p.hwc_code == prepared["human_code"]
    status = "VALID" if (p.status in ("raw_valid", "salvaged_valid")
                        and human_ok and syn.ok and structure_ok) else "INVALID"
    return {
        "mode": mode, "pair_id": prepared["pair_id"],
        "split": prepared["split"], "complexity_block": prepared["complexity_block"],
        "model": model_name, "temperature": 0.0, "do_sample": False,
        "top_p": None, "eos_ids": list(EOS_BY_MODE[mode]),
        "prompt_sha256": prepared["prompt_sha256"],
        "raw_output": raw, "raw_sha256": hash_text(raw),
        "clean_output": p.clean_output, "new_agc_code": new_code,
        "new_agc_sha256": hash_text(new_code),
        "status": status, "pipeline_status": p.status,
        "syntax_ok": bool(syn.ok), "syntax_reason": "" if syn.ok else (syn.error or "syntax invalid"),
        "structure_ok": bool(structure_ok), "structure_reason": reason,
        "human_reproduced": bool(human_ok),
        "input_tokens": input_tokens, "generated_tokens": n_tokens,
        "last_token_id": final_id, "termination": termination,
        "seconds": round(seconds, 4),
    }


def validate_checkpoint(records, prepared, model_name, max_new):
    prepared_map = {p["pair_id"]: p for p in prepared}
    by_key = {}
    for r in records:
        key = (r.get("mode"), r.get("pair_id"))
        if (key in by_key or r.get("mode") not in MODES
                or r.get("pair_id") not in prepared_map):
            fail(f"Duplicate/invalid checkpoint record: {key}")
        p = prepared_map[key[1]]
        if (r.get("model") != model_name or r.get("temperature") != 0.0
                or r.get("do_sample") is not False or r.get("top_p") is not None
                or r.get("eos_ids") != list(EOS_BY_MODE[key[0]])
                or r.get("prompt_sha256") != p["prompt_sha256"]
                or r.get("split") != p["split"]
                or r.get("complexity_block") != p["complexity_block"]
                or r.get("new_agc_sha256") != hash_text(r["new_agc_code"])
                or r.get("generated_tokens", max_new + 1) > max_new):
            fail(f"Checkpoint provenance mismatch: {key}")
        by_key[key] = r
    return by_key


def summarize(args, prepared, legacy_map, by_key, config):
    expected = len(prepared) * len(MODES)
    completed = len(by_key)
    counts = {"legacy": Counter(), "no_boundary": Counter(), "standard": Counter()}
    term_counts = Counter()
    per_mode_time = defaultdict(list)
    rows = []
    qc = []
    for p in prepared:
        pid = p["pair_id"]
        a = legacy_map[pid]
        counts["legacy"][a["status"]] += 1
        row = {
            "pair_id": pid, "split": p["split"], "complexity_block": p["complexity_block"],
            "legacy_status": a["status"], "legacy_tokens": a["generated_tokens"],
            "legacy_last_token_id": "UNRECORDED", "legacy_termination": "UNRECORDED",
            "legacy_agc_sha256": a["new_agc_sha256"],
        }
        for mode in MODES:
            r = by_key.get((mode, pid))
            if r is None:
                row[f"{mode}_status"] = "PENDING"
                row[f"{mode}_termination"] = "PENDING"
                continue
            counts[mode][r["status"]] += 1
            term_counts[(mode, r["termination"], r["last_token_id"])] += 1
            per_mode_time[mode].append(r["seconds"])
            row.update({
                f"{mode}_status": r["status"], f"{mode}_tokens": r["generated_tokens"],
                f"{mode}_last_token_id": r["last_token_id"],
                f"{mode}_termination": r["termination"],
                f"{mode}_same_as_legacy": r["new_agc_sha256"] == a["new_agc_sha256"],
                f"{mode}_agc_sha256": r["new_agc_sha256"],
            })
            qc.append({
                "pair_id": pid, "split": p["split"], "complexity_block": p["complexity_block"],
                "mode": mode, "status": r["status"], "pipeline_status": r["pipeline_status"],
                "syntax_ok": r["syntax_ok"], "syntax_reason": r["syntax_reason"],
                "structure_ok": r["structure_ok"], "structure_reason": r["structure_reason"],
                "generated_tokens": r["generated_tokens"], "last_token_id": r["last_token_id"],
                "termination": r["termination"], "seconds": r["seconds"],
            })
        b = by_key.get(("no_boundary", pid))
        c = by_key.get(("standard", pid))
        if b and c:
            row["no_boundary_equals_standard"] = b["new_agc_sha256"] == c["new_agc_sha256"]
            row["all_three_valid"] = all(x["status"] == "VALID" for x in (a, b, c))
        rows.append(row)
    write_csv(args.output_dir / "ablation_comparison.csv", rows, list(dict.fromkeys(k for r in rows for k in r)))
    write_csv(args.output_dir / "ablation_qc.csv", qc, [
        "pair_id", "split", "complexity_block", "mode", "status", "pipeline_status",
        "syntax_ok", "syntax_reason", "structure_ok", "structure_reason",
        "generated_tokens", "last_token_id", "termination", "seconds",
    ])
    term_rows = [{"mode": mode, "termination": term, "last_token_id": tid, "count": count}
                 for (mode, term, tid), count in sorted(term_counts.items(), key=lambda z: str(z[0]))]
    write_csv(args.output_dir / "last_token_counts.csv", term_rows,
              ["mode", "termination", "last_token_id", "count"])

    status = "PASS" if completed == expected else "INCOMPLETE"
    complete_rows = [r for r in rows if r.get("all_three_valid") is not None]
    all_valid = sum(bool(r.get("all_three_valid")) for r in complete_rows)
    med_block = sorted({p["complexity_block"] for p in prepared})
    lower = set(med_block[:len(med_block) // 2])
    complexity_group = {}
    for mode in ("legacy",) + MODES:
        complexity_group[mode] = {}
        for group, blocks in (("lower", lower), ("higher", set(med_block) - lower)):
            grp_ids = {p["pair_id"] for p in prepared if p["complexity_block"] in blocks}
            if mode == "legacy":
                rs = [legacy_map[pid] for pid in grp_ids]
            else:
                rs = [by_key[(mode, pid)] for pid in grp_ids if (mode, pid) in by_key]
            complexity_group[mode][group] = {"valid": sum(r["status"] == "VALID" for r in rs),
                                             "generated": len(rs)}
    summary = {
        "experiment": "run-x-04", "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "original_pilot": str(args.pilot_dir), "legacy_records_reused": len(prepared),
        "expected_new_generations": expected, "completed_new_generations": completed,
        "mode_validity": {k: dict(v) for k, v in counts.items()},
        "common_valid_all_three": all_valid if completed == expected else None,
        "complexity_group_validity": complexity_group,
        "termination_counts": term_rows,
        "mean_seconds": {k: statistics.mean(v) if v else None for k, v in per_mode_time.items()},
        "legacy_stop_token_attribution": "Unavailable: run-x-02 did not save output token IDs",
        "original_data_modified": False,
        "temperature_compared": False,
        "limitations": [
            "This is an EOS ablation at fixed T=0.0, not a temperature effect estimate.",
            "Legacy run-x-02 final token IDs were not recorded; terminal-token attribution is unavailable.",
            "Original T=0.2 benchmark was validity-filtered and cannot be treated as an unfiltered baseline.",
        ],
        "experiment_config_sha256": hash_text(canonical_json(config)),
        "output_dir": str(args.output_dir),
    }
    write_json(args.output_dir / "ablation_summary.json", summary)
    findings = [
        f"Experiment: run-x-04 | EOS ablation | Status: {status}",
        "Temperature: T=0.0 greedy for all conditions (no temperature/top_p passed)",
        f"Legacy [2,822,29871] (reused): valid={counts['legacy']['VALID']}/{len(prepared)}",
        f"No-boundary [2,822] (generated): valid={counts['no_boundary']['VALID']}/{len(prepared)}",
        f"Standard [2] (generated): valid={counts['standard']['VALID']}/{len(prepared)}",
        f"New generations: {completed}/{expected}; three-way common-valid: {all_valid if completed == expected else 'pending'}",
        "Legacy EOS cause: UNRECORDED; do not infer from decoded output.",
        "This ablation isolates EOS policy, not changes to generation temperature.",
        f"Output directory: {args.output_dir}",
    ]
    (args.output_dir / "ablation_findings.txt").write_text("\n".join(findings) + "\n", encoding="utf-8")
    print("\n".join(findings), flush=True)
    return summary


def main():
    args = parse_args()
    args.pilot_dir = args.pilot_dir.expanduser().resolve()
    args.validator_script = args.validator_script.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    if not args.pilot_dir.is_dir() or not args.validator_script.is_file():
        fail("Missing run-x-02 pilot directory or validator")
    _, prepared, legacy_map, config = load_inputs(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config_file = args.output_dir / "experiment_config.json"
    records_file = args.output_dir / "ablation_generation.jsonl"
    if args.resume:
        if not config_file.is_file():
            fail("Cannot resume: experiment_config.json missing")
        if json.loads(config_file.read_text(encoding="utf-8")) != config:
            fail("Cannot resume: source inputs or configuration changed")
    else:
        if config_file.exists() or records_file.exists():
            fail("Output already exists; refusing to overwrite")
        write_json(config_file, config)
    print(f"[INPUT] Verified 100 original T=0.0 prompts; original generations=100", flush=True)
    print("[INPUT] Model, prompt, original dataset, manifest, validator hashes PASS", flush=True)
    print(f"[ABLATION] Legacy EOS={list(LEGACY_IDS)} (reuse); alternatives={EOS_BY_MODE}", flush=True)
    if args.dry_run:
        print("[DRY-RUN] Input integrity PASS; no GPU inference or new code generation.", flush=True)
        return 0
    validator = import_validator(args.validator_script)
    for p in prepared:
        if validator.compose_code(p["prompt"], p["solution"]) != p["human_code"]:
            fail(f"Original human reconstruction mismatch: {p['pair_id']}")
    records = read_jsonl(records_file) if records_file.is_file() else []
    by_key = validate_checkpoint(records, prepared, args.model_name, config["max_new_tokens"])
    pending = [(mode, p) for p in prepared for mode in MODES if (mode, p["pair_id"]) not in by_key]
    print(f"[CHECKPOINT] existing={len(records)}, pending={len(pending)}", flush=True)
    if pending:
        model, tok, torch, env = load_model(args.model_name, args.local_files_only)
        env_file = args.output_dir / "model_environment.json"
        if env_file.exists() and args.resume:
            old_env = json.loads(env_file.read_text(encoding="utf-8"))
            if (old_env.get("resolved_revision") != env.get("resolved_revision")
                    or old_env.get("torch_version") != env.get("torch_version")
                    or old_env.get("transformers_version") != env.get("transformers_version")):
                fail("Cannot resume: model revision or runtime versions changed")
        else:
            write_json(env_file, env)
        for mode, p in pending:
            t0 = time.monotonic()
            raw, in_t, out_t, last_id, why = generate_one(
                model, tok, torch, p["prompt"], EOS_BY_MODE[mode],
                config["prompt_max_tokens"], config["max_new_tokens"],
            )
            sec = time.monotonic() - t0
            legacy_in = legacy_map[p["pair_id"]]["input_tokens"]
            if in_t != legacy_in:
                fail(f"Prompt token count changed from run-x-02 for {p['pair_id']}: {legacy_in} -> {in_t}")
            item = validate_attempt(validator, p, mode, raw, in_t, out_t, last_id,
                                    why, sec, args.model_name)
            append_jsonl(records_file, item)
            by_key[(mode, p["pair_id"])] = item
            print(f"[GEN] {len(by_key)}/200 mode={mode} pair={p['pair_id']} "
                  f"split={p['split']} status={item['status']} tokens={out_t} "
                  f"last_id={last_id} stop={why} elapsed={sec:.2f}s", flush=True)
        del model
        torch.cuda.empty_cache()
    summary = summarize(args, prepared, legacy_map, by_key, config)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise
