#!/usr/bin/env python3
"""Independent, resumable CodeLlama-7B temperature generation (run-x-a-01-v1).

Inputs: CodeSearchNet python/train.jsonl and a historical CL-7B paired CSV.
Outputs: frozen plan, per-prompt JSON checkpoints, and length-bin QC reports.
This script never trains a detector, chooses a classification threshold, or
uses ML predictions to select code. Each temperature shares the same prompts.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import heapq
import json
import os
import re
import sys
import tempfile
import textwrap
from collections import Counter
from pathlib import Path

TEMPERATURES = {"t02": 0.2, "t04": 0.4, "t06": 0.6}
BUCKETS = [(100 if k == 1 else 100 + (k - 1) * 10 + 1, 100 + k * 10) for k in range(1, 11)]
EXPERIMENT = "run-x-a-01-v1"


def canonical(text):
    return textwrap.dedent(str(text or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_jsonl(path, obj):
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def split_prompt_body(source):
    """Preserve the project's original triple-quote prompt/solution split."""
    s = str(source or "").replace("'''", '"""')
    chunks = s.split('"""')
    if len(chunks) < 3:
        return None, None
    return chunks[0] + '"""' + chunks[1] + '"""', chunks[2]


def filter_source(source):
    prompt, solution = split_prompt_body(source)
    if prompt is None:
        return None
    nprompt, nsolution = len(prompt.split()), len(solution.split())
    if not (5 <= nprompt <= 128 and 5 <= nsolution <= 256):
        return None
    human_code = canonical(prompt + solution)
    if not python_structure_ok(human_code):
        return None
    return prompt, solution, human_code


def python_structure_ok(code):
    try:
        body = ast.parse(code).body
    except (ValueError, SyntaxError, IndentationError):
        return False
    blocks = [x for x in body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if len(blocks) != 1 or len(body) != 1:
        return False
    stmts = list(blocks[0].body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) and isinstance(stmts[0].value.value, str):
        stmts.pop(0)
    return any(not isinstance(s, ast.Pass) for s in stmts)


def legacy_prompt_from_code(code):
    """Recover the signature/docstring prompt from a stored HWC code sample."""
    chunks = str(code or "").replace("'''", '"""').split('"""')
    if len(chunks) < 3:
        return None
    return chunks[0] + '"""' + chunks[1] + '"""'


def exclusion_set(paths):
    """Ban historical CL-7B HWC/AGC prompts, code hashes, and legacy line IDs.

    Exclusion CSV must be a previously built paired dataset, not model scores.
    Never proceed without at least one usable historical exclusion.
    """
    excluded_prompts, excluded_human_codes, excluded_lines = set(), set(), set()
    sizes = []
    for path in paths:
        path = Path(path)
        if not path.is_file():
            raise RuntimeError(f"[EXCLUSION] Required historical CSV is missing: {path}")
        count, hwc_count = 0, 0
        with path.open("r", encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            if not {"idx", "code", "label"}.issubset(set(rd.fieldnames or [])):
                raise RuntimeError(f"[EXCLUSION] Missing idx/code/label columns: {path}")
            for row in rd:
                count += 1
                label = str(row["label"]).strip().lower()
                if label not in {"human", "hwc", "0"}:
                    continue
                hwc_count += 1
                excluded_human_codes.add(sha(canonical(row["code"])))
                p = legacy_prompt_from_code(row["code"])
                if p is not None:
                    excluded_prompts.add(sha(canonical(p)))
                m = re.match(r"^line(\d+)(?:_|$)", str(row["idx"]).strip())
                if m:
                    excluded_lines.add(int(m.group(1)))
        if hwc_count < 100:
            raise RuntimeError(f"[EXCLUSION] Suspiciously small HWC population ({hwc_count}): {path}")
        sizes.append({"path": str(path), "rows": count, "hwc_rows": hwc_count, "sha256": file_sha(path)})
    if not excluded_prompts and not excluded_human_codes:
        raise RuntimeError("[EXCLUSION] No usable prior HWC examples")
    return excluded_prompts, excluded_human_codes, excluded_lines, sizes


def build_candidates(args):
    train = Path(args.train)
    if not train.is_file():
        raise RuntimeError(f"CodeSearchNet input missing: {train}")
    ep, eh, el, exclusion_files = exclusion_set(args.exclude_csv)
    counters = Counter()
    top = []  # Max-size stable-priority reservoir with reproducible hash ranking.
    seen_prompts = set()
    with train.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            counters["source_lines"] += 1
            if not line.strip():
                continue
            try:
                source = json.loads(line).get("original_string", "")
            except json.JSONDecodeError:
                counters["bad_json"] += 1
                continue
            parsed = filter_source(source)
            if parsed is None:
                counters["source_filtered"] += 1
                continue
            prompt, solution, hwc_code = parsed
            psha, hsha = sha(canonical(prompt)), sha(canonical(hwc_code))
            if psha in ep or hsha in eh or lineno in el:
                counters["historical_excluded"] += 1
                continue
            if psha in seen_prompts:
                counters["duplicate_prompt_excluded"] += 1
                continue
            seen_prompts.add(psha)
            counters["eligible"] += 1
            rank = int(sha(f"{args.seed}|{lineno}|{psha}")[:16], 16)
            # Store the lowest hash ranks, regardless of CodeSearchNet ordering.
            item = (-rank, -lineno, {"line_no": lineno, "prompt": prompt,
                    "solution": solution, "prompt_sha256": psha, "human_sha256": hsha,
                    "prompt_words": len(prompt.split()), "solution_words": len(solution.split())})
            if len(top) < args.max_prompts:
                heapq.heappush(top, item)
            elif item[:2] > top[0][:2]:
                heapq.heapreplace(top, item)
    selected = sorted((item[2] for item in top), key=lambda x: x["line_no"])
    if len(selected) < args.max_prompts:
        raise RuntimeError(f"Only {len(selected)} independent prompts; requested {args.max_prompts}")
    spec = {"experiment": EXPERIMENT, "train_path": str(train.resolve()),
            "train_sha256": file_sha(train), "exclusions": exclusion_files,
            "seed": args.seed, "max_prompts": args.max_prompts,
            "generator_script_sha256": file_sha(Path(__file__)),
            "model": args.model, "top_p": args.top_p, "max_input_tokens": 128,
            "max_new_tokens": 512, "temperatures": TEMPERATURES,
            "selection": "lowest_seeded_hash_ranks_after_historical_exclusion",
            "filter": "CodeSearchNet 5..128 prompt words, 5..256 solution words, valid HWC AST",
            "benchmark_length": "literal_space_split_100_to_200_in_ten_buckets"}
    stats = dict(counters)
    stats["selected"] = len(selected)
    stats["excluded_hwc_hashes"] = len(eh)
    stats["excluded_prompt_hashes"] = len(ep)
    stats["excluded_legacy_lines"] = len(el)
    return selected, spec, stats


def prepare(args):
    out = Path(args.out)
    selected, spec, stats = build_candidates(args)
    plan = out / "plan.jsonl"
    run_spec = out / "run_spec.json"
    plan_data = "".join(json.dumps(p, sort_keys=True, ensure_ascii=False) + "\n" for p in selected)
    spec["plan_sha256"] = sha(plan_data)
    if run_spec.exists() or plan.exists():
        if not (run_spec.is_file() and plan.is_file()):
            raise RuntimeError("Partial preflight artifacts; inspect before proceeding")
        if load_json(run_spec) != spec or file_sha(plan) != spec["plan_sha256"]:
            raise RuntimeError("Frozen plan/spec differs; use a new experiment output path")
        print(f"[PREFLIGHT] PASS existing immutable plan: {len(selected)} prompts")
    else:
        out.mkdir(parents=True, exist_ok=True)
        tmp = plan.with_suffix(".jsonl.tmp")
        tmp.write_text(plan_data, encoding="utf-8")
        os.replace(tmp, plan)
        save_json(run_spec, spec)
        print(f"[PREFLIGHT] PASS created frozen plan: {len(selected)} prompts")
    save_json(out / "preflight_qc.json", {"status": "PASS", **stats})
    print(f"[EXCLUSION] HWC={stats['excluded_hwc_hashes']} prompt={stats['excluded_prompt_hashes']} legacy_lines={stats['excluded_legacy_lines']} skipped={stats.get('historical_excluded', 0)}")
    print(f"[SPEC] plan_sha256={spec['plan_sha256']}")


def load_plan(out):
    out = Path(out)
    spec = load_json(out / "run_spec.json")
    if spec["experiment"] != EXPERIMENT or file_sha(out / "plan.jsonl") != spec["plan_sha256"]:
        raise RuntimeError("Frozen plan SHA256 mismatch")
    if spec.get("generator_script_sha256") != file_sha(Path(__file__)):
        raise RuntimeError("Python implementation changed after preflight; use a new output/version")
    rows = [json.loads(line) for line in (out / "plan.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != spec["max_prompts"] or len({r["prompt_sha256"] for r in rows}) != len(rows):
        raise RuntimeError("Plan count or prompt uniqueness failure")
    for r in rows:
        if sha(canonical(r["prompt"])) != r["prompt_sha256"] or sha(canonical(r["prompt"] + r["solution"])) != r["human_sha256"]:
            # Canonicalization should preserve semantics but concatenation requires matching first.
            if sha(canonical(r["prompt"] + r["solution"])) != r["human_sha256"]:
                raise RuntimeError(f"Plan human body mismatch at line {r['line_no']}")
    return spec, rows


def expected_indent(prompt):
    lines = [x for x in prompt.splitlines() if x.strip()]
    if not lines:
        return 4
    last = lines[-1]
    w = len(last.expandtabs(4)) - len(last.expandtabs(4).lstrip(" "))
    return w + 4 if last.rstrip().endswith(":") else w


def clean_generation(prompt, output):
    """Copy the project's conservative continuation cleanup, independently."""
    s = str(output).replace("\r\n", "\n").replace("\r", "\n")
    for stop in ("<|endoftext|>", "<file_sep>", "```"):
        s = s.split(stop, 1)[0]
    patterns = [r"\n\n(?=def\s+\w+\s*\()", r"\n\n(?=async\s+def\s+\w+\s*\()",
                r"\n\n(?=class\s+\w+)", r"\n\s{4}def\s*$", r"\n\s*def\s*$",
                r"\n\s*async\s+def\s*$", r"\n\s*class\s*$"]
    cut = min([m.start() for pat in patterns for m in re.finditer(pat, s)] or [len(s)])
    s = s[:cut].rstrip("\n ")
    # A continuation occasionally starts with the same outer function signature.
    name = re.search(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", prompt, re.M)
    ls = s.splitlines()
    while ls and not ls[0].strip():
        ls.pop(0)
    if name and ls and re.match(rf"^\s*def\s+{re.escape(name.group(1))}\s*\(.*\)\s*:\s*$", ls[0]):
        ls.pop(0)
    if not ls:
        return "\n"
    nonempty = [x for x in ls if x.strip()]
    if not nonempty:
        return "\n"
    leading = min(len(x.expandtabs(4)) - len(x.expandtabs(4).lstrip(" ")) for x in nonempty)
    shift = max(0, expected_indent(prompt) - leading)
    s = "\n".join((" " * shift + x.expandtabs(4) if x.strip() else x) for x in ls).rstrip()
    return "\n" + s + "\n"


def body_bucket(text):
    """Match the D10 literal-space body token convention, not LM BPE tokens."""
    n = len(text.strip("\n").split(" "))
    for i, (lo, hi) in enumerate(BUCKETS, 1):
        if lo <= n <= hi:
            return n, f"type{i:02d}_{hi}"
    return n, "out_of_range"


def validate_result(prompt, solution, continuation):
    clean = clean_generation(prompt, continuation)
    mgc = canonical(prompt + clean) + "\n"
    human = canonical(prompt + solution) + "\n"
    valid_human = python_structure_ok(human)
    valid_agc = python_structure_ok(mgc)
    n, bucket = body_bucket(clean)
    return clean, mgc, valid_human, valid_agc, n, bucket


def load_model(model_id):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available; GPU inference is mandatory")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, trust_remote_code=True)
    model = model.cuda().eval()
    def_id = tokenizer("def", add_special_tokens=False).input_ids[0]
    try:
        spaced_id = tokenizer("def", add_prefix_space=True, add_special_tokens=False).input_ids[0]
    except (TypeError, ValueError):
        spaced_id = tokenizer(" def", add_special_tokens=False).input_ids[0]
    stops = list(dict.fromkeys(i for i in [tokenizer.eos_token_id, def_id, spaced_id] if i is not None))
    meta = {"model": model_id, "model_commit": getattr(model.config, "_commit_hash", None),
            "device": torch.cuda.get_device_name(0), "torch": torch.__version__,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
            "eos_token_ids": stops, "dtype": "torch.float16"}
    print(f"[MODEL] {json.dumps(meta, sort_keys=True)}", flush=True)
    return torch, tokenizer, model, stops, meta


def generate(prompt, seed, temperature, torch, tokenizer, model, stops, spec):
    import torch as torch_module
    torch_module.manual_seed(seed)
    torch_module.cuda.manual_seed_all(seed)
    encoded = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=spec["max_input_tokens"], return_attention_mask=True)
    ids = encoded.input_ids.cuda()
    mask = encoded.attention_mask.cuda()
    with torch.inference_mode():
        out = model.generate(ids, attention_mask=mask, do_sample=True,
                             max_new_tokens=spec["max_new_tokens"],
                             top_p=spec["top_p"], temperature=temperature,
                             pad_token_id=tokenizer.eos_token_id, eos_token_id=stops,
                             use_cache=True)
    text = tokenizer.decode(out[0, ids.shape[1]:], skip_special_tokens=False)
    return text


def worker(args):
    spec, rows = load_plan(args.out)
    tag = args.tag
    if tag not in TEMPERATURES or spec["model"] != args.model:
        raise RuntimeError("Worker tag or model does not match the frozen plan")
    if args.smoke:
        rows = rows[:1]
        base = Path(args.out) / "smoke"
    else:
        base = Path(args.out) / "production"
    checkpoint_dir = base / "checkpoints" / tag
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    # Do not load expensive model when all assigned checkpoints are completed.
    pending = [r for r in rows if not (checkpoint_dir / f"{r['line_no']:09d}-{r['prompt_sha256'][:12]}.json").exists()]
    print(f"[WORKER] tag={tag} temp={TEMPERATURES[tag]} pending={len(pending)} total={len(rows)}", flush=True)
    if not pending:
        return
    torch, tok, model, stops, meta = load_model(args.model)
    save_json(base / "model_metadata" / f"{tag}.json", meta)
    for i, r in enumerate(pending, 1):
        model_seed = int(sha(f"{spec['seed']}|{tag}|{r['prompt_sha256']}")[:8], 16)
        raw = generate(r["prompt"], model_seed, TEMPERATURES[tag], torch, tok, model, stops, spec)
        clean, agc_code, human_ok, agc_ok, word_count, bucket = validate_result(r["prompt"], r["solution"], raw)
        record = {"experiment": EXPERIMENT, "tag": tag, "temperature": TEMPERATURES[tag],
                  "line_no": r["line_no"], "prompt_sha256": r["prompt_sha256"],
                  "human_sha256": r["human_sha256"], "body_sha256": sha(clean.strip("\n")),
                  "raw_output": raw, "clean_output": clean, "agc_code": agc_code,
                  "human_valid": human_ok, "agc_valid": agc_ok,
                  "body_tokens": word_count, "bucket": bucket,
                  "accepted_for_pool": bool(human_ok and agc_ok and bucket != "out_of_range"),
                  "sampling_seed": model_seed, "plan_sha256": spec["plan_sha256"]}
        save_json(checkpoint_dir / f"{r['line_no']:09d}-{r['prompt_sha256'][:12]}.json", record)
        if i % 10 == 0 or i == len(pending):
            print(f"[GENERATE] {tag} {i}/{len(pending)} line={r['line_no']} valid={agc_ok} bucket={bucket}", flush=True)
    print(f"[WORKER] {tag} PASS processed={len(pending)}", flush=True)


def aggregate(args, strict):
    spec, rows = load_plan(args.out)
    base = Path(args.out) / ("smoke" if args.smoke else "production")
    summary = {"experiment": EXPERIMENT, "plan_sha256": spec["plan_sha256"],
               "n_selected_prompts": len(rows), "per_temperature": {}, "mode": "smoke" if args.smoke else "production"}
    all_accepted = []
    required = rows[:1] if args.smoke else rows
    for tag in TEMPERATURES:
        found = 0
        bucket_hist = Counter()
        state_hist = Counter()
        seen_body_hash = set()
        for r in required:
            path = base / "checkpoints" / tag / f"{r['line_no']:09d}-{r['prompt_sha256'][:12]}.json"
            if not path.is_file():
                continue
            obj = load_json(path)
            if (obj["plan_sha256"] != spec["plan_sha256"] or obj["tag"] != tag or
                obj["prompt_sha256"] != r["prompt_sha256"] or obj["human_sha256"] != r["human_sha256"] or
                obj["body_sha256"] != sha(obj["clean_output"].strip("\n"))):
                raise RuntimeError(f"Checkpoint provenance/hash mismatch: {path}")
            clean, code, human_ok, agc_ok, n, bucket = validate_result(r["prompt"], r["solution"], obj["raw_output"])
            if any([obj["clean_output"] != clean, obj["agc_code"] != code, obj["human_valid"] != human_ok,
                    obj["agc_valid"] != agc_ok, obj["body_tokens"] != n, obj["bucket"] != bucket]):
                raise RuntimeError(f"Checkpoint revalidation mismatch: {path}")
            found += 1
            duplicate = obj["accepted_for_pool"] and obj["body_sha256"] in seen_body_hash
            status = "duplicate_body" if duplicate else ("accepted" if obj["accepted_for_pool"] else "filtered")
            state_hist[status] += 1
            if obj["accepted_for_pool"] and not duplicate:
                seen_body_hash.add(obj["body_sha256"])
                bucket_hist[bucket] += 1
                all_accepted.append({"temperature_tag": tag, "temperature": TEMPERATURES[tag],
                                     "line_no": r["line_no"], "prompt_sha256": r["prompt_sha256"],
                                     "human_sha256": r["human_sha256"], "body_sha256": obj["body_sha256"],
                                     "bucket": bucket, "body_tokens": n,
                                     "checkpoint": str(path.relative_to(base))})
        if strict and found != len(required):
            raise RuntimeError(f"Incomplete {tag}: {found}/{len(required)}")
        quota = {f"type{i:02d}_{hi}": bucket_hist.get(f"type{i:02d}_{hi}", 0) for i, (_, hi) in enumerate(BUCKETS, 1)}
        summary["per_temperature"][tag] = {"checkpoints": found, "expected": len(required),
                                              "state_counts": dict(state_hist), "bucket_valid": quota,
                                              "buckets_with_15": sum(v >= 15 for v in quota.values()),
                                              "ready_for_15_each": all(v >= 15 for v in quota.values())}
        print(f"[QC] {tag}: checkpoints={found}/{len(required)} accepted={sum(quota.values())} buckets_with_15={sum(v>=15 for v in quota.values())}/10")
    if strict:
        # All GPU workers must have written consistent model identity/provenance.
        model_metadata = []
        for tag in TEMPERATURES:
            metadata_path = base / "model_metadata" / f"{tag}.json"
            if not metadata_path.is_file():
                raise RuntimeError(f"Missing GPU model metadata: {metadata_path}")
            metadata = load_json(metadata_path)
            if metadata.get("model") != spec["model"] or metadata.get("dtype") != "torch.float16":
                raise RuntimeError(f"Unexpected model/dtype in: {metadata_path}")
            model_metadata.append(metadata)
        commits = {m.get("model_commit") for m in model_metadata}
        if len(commits) != 1:
            raise RuntimeError("Different CL-7B model revisions across temperature workers")
        summary["model_metadata"] = model_metadata
        summary["status"] = "PASS"
        base.mkdir(parents=True, exist_ok=True)
        out_csv = base / "accepted_pool.csv"
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["temperature_tag", "temperature", "line_no", "prompt_sha256", "human_sha256", "body_sha256", "bucket", "body_tokens", "checkpoint"])
            writer.writeheader()
            writer.writerows(sorted(all_accepted, key=lambda r: (r["temperature_tag"], r["line_no"])))
        save_json(base / "generation_qc.json", summary)
        summary["output_sha256"] = {"accepted_pool.csv": file_sha(out_csv)}
        save_json(base / "generation_qc.json", summary)
        print("[VERIFY] PASS all generation checkpoints and outputs")
    else:
        print("[CHECK] Partial checkpoint coverage (no final QC written)")
    return summary


def self_test():
    assert split_prompt_body('def f():\n    """X"""\n    return 1')[0] == 'def f():\n    """X"""'
    assert body_bucket("a " * 99 + "b")[1] == "type01_110"
    assert body_bucket("a " * 110 + "b")[1] == "type02_120"
    assert body_bucket("a " * 199 + "b")[1] == "type10_200"
    assert body_bucket("a " * 200 + "b")[1] == "out_of_range"
    prompt = 'def f():\n    """Demo."""'
    cont = "\n    return 1\n"
    assert validate_result(prompt, cont, cont)[3]
    assert not validate_result(prompt, cont, "\n  invalid syntax !\n")[3]
    assert sha(canonical(prompt)) == sha(canonical(prompt))
    print("[SELF-TEST] PASS prompt extraction, bucket boundaries, AST validation, hashing")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["self-test", "preflight", "worker", "check", "verify"], required=True)
    p.add_argument("--train", default="data/CodeSearchNet/python/train.jsonl")
    p.add_argument("--exclude-csv", action="append", default=[])
    p.add_argument("--out", default="output/run-x-a-01/v1")
    p.add_argument("--model", default="codellama/CodeLlama-7b-hf")
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--seed", type=int, default=20260723)
    p.add_argument("--max-prompts", type=int, default=1500)
    p.add_argument("--tag", default="")
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    try:
        if args.mode == "self-test":
            self_test()
        elif args.mode == "preflight":
            if not args.exclude_csv:
                raise RuntimeError("Preflight requires --exclude-csv with historical CL-7B HWC/AGC pairs")
            if args.max_prompts <= 0 or not (0 < args.top_p <= 1):
                raise RuntimeError("Invalid max-prompts or top-p")
            prepare(args)
        elif args.mode == "worker":
            worker(args)
        elif args.mode == "check":
            aggregate(args, strict=False)
        elif args.mode == "verify":
            aggregate(args, strict=True)
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
