#!/usr/bin/env python3
"""Independent Python 3.12 AST audit for A-01-v2 frozen CL-7B generation.

Inputs:
  output/run-x-a-01/v2/run_spec.json, plan.jsonl
  output/run-x-a-01/v2/{smoke,production}/checkpoints/{t02,t04,t06}/*.json
Outputs (new files only):
  output/run-x-a-01/v2/ast_plan_qc_python312.json
  output/run-x-a-01/v2/smoke/ast_smoke_qc_python312.json
  output/run-x-a-01/v2/production/ast_{pilot,full}_qc_python312.json

No PyTorch or GPU is required. This script never modifies the frozen plan,
existing checkpoint files, or the original v2 generation QC files.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import sys
import textwrap
from collections import Counter
from pathlib import Path

TAGS = ("t02", "t04", "t06")
BUCKETS = [(100 if k == 1 else 100 + (k - 1) * 10 + 1, 100 + k * 10) for k in range(1, 11)]
BUCKET_NAMES = tuple(f"type{i:02d}_{hi}" for i, (_, hi) in enumerate(BUCKETS, 1))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(code: str) -> str:
    return textwrap.dedent(str(code or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    try:
        temp.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def structure_ok(code: str) -> bool:
    """Reproduce A-01's one-outer-block/nonempty-body rule under Python 3.12."""
    try:
        body = ast.parse(code).body
    except (SyntaxError, IndentationError, ValueError):
        return False
    blocks = [n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if len(body) != 1 or len(blocks) != 1:
        return False
    stmts = list(blocks[0].body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) and isinstance(stmts[0].value.value, str):
        stmts.pop(0)
    return any(not isinstance(stmt, ast.Pass) for stmt in stmts)


def bucket(text: str) -> str:
    n = len(text.strip("\n").split(" "))
    for i, (lo, hi) in enumerate(BUCKETS, 1):
        if lo <= n <= hi:
            return f"type{i:02d}_{hi}"
    return "out_of_range"


def load_plan(out: Path) -> tuple[dict, list[dict]]:
    spec = load_json(out / "run_spec.json")
    plan_bytes = (out / "plan.jsonl").read_bytes()
    if digest(plan_bytes) != spec.get("plan_sha256"):
        raise ValueError("Frozen plan SHA256 mismatch")
    rows = [json.loads(x) for x in plan_bytes.decode("utf-8").splitlines() if x.strip()]
    if len(rows) != spec.get("max_prompts"):
        raise ValueError("Frozen plan length mismatch")
    if spec.get("experiment") != "run-x-a-01-v2":
        raise ValueError("Unexpected source experiment")
    if len({r["prompt_sha256"] for r in rows}) != len(rows):
        raise ValueError("Duplicated prompt hashes in plan")
    return spec, rows


def metadata(phase: str, spec: dict) -> dict:
    return {
        "status": "PENDING",
        "phase": phase,
        "source_experiment": spec["experiment"],
        "plan_sha256": spec["plan_sha256"],
        "python_ast_binary": sys.executable,
        "python_ast_version": platform.python_version(),
        "python_ast_version_info": list(sys.version_info[:3]),
        "rule": "one outer function/class/async-function with a substantive body",
    }


def audit_plan(out: Path, spec: dict, rows: list[dict]) -> dict:
    report = metadata("plan", spec)
    good = 0
    bad = []
    source_counts = Counter()
    for r in rows:
        human = canonical(r["prompt"] + r["solution"]) + "\n"
        if digest(canonical(r["prompt"]).encode("utf-8")) != r["prompt_sha256"]:
            raise ValueError(f"Plan prompt hash mismatch at {r['line_no']}")
        if digest(canonical(human).encode("utf-8")) != r["human_sha256"]:
            raise ValueError(f"Plan HWC hash mismatch at {r['line_no']}")
        source_counts[r["source_stratum"]] += 1
        if structure_ok(human):
            good += 1
        else:
            bad.append(r["line_no"])
    report.update({
        "checked": len(rows), "human_valid_python312": good,
        "human_invalid_line_numbers": bad,
        "source_strata": dict(sorted(source_counts.items())),
        "status": "PASS" if not bad else "FAIL",
    })
    save_json(out / "ast_plan_qc_python312.json", report)
    print(f"[AST-312] plan checked={len(rows)} valid={good} invalid={len(bad)} status={report['status']}")
    return report


def audit_checkpoints(out: Path, spec: dict, rows: list[dict], phase: str) -> dict:
    base = out / ("smoke" if phase == "smoke" else "production")
    if phase == "smoke":
        required = rows[:1]
    elif phase == "pilot":
        required = rows[:spec["pilot_size"]]
    else:
        required = rows
    report = metadata(phase, spec)
    report["expected_per_temperature"] = len(required)
    report["per_temperature"] = {}
    errors = []
    for tag in TAGS:
        count = Counter()
        valid_buckets = Counter()
        seen_bodies = set()
        invalid_312_but_311_valid = []
        recovered_by_312 = []
        for r in required:
            cp = base / "checkpoints" / tag / f"{r['line_no']:09d}-{r['prompt_sha256'][:12]}.json"
            if not cp.is_file():
                count["missing"] += 1
                continue
            obj = load_json(cp)
            if any([
                obj.get("plan_sha256") != spec["plan_sha256"],
                obj.get("tag") != tag,
                obj.get("line_no") != r["line_no"],
                obj.get("prompt_sha256") != r["prompt_sha256"],
                obj.get("human_sha256") != r["human_sha256"],
                obj.get("body_sha256") != digest(obj["clean_output"].strip("\n").encode("utf-8")),
                obj.get("agc_code") != canonical(r["prompt"] + obj["clean_output"]) + "\n",
            ]):
                raise ValueError(f"Checkpoint provenance/content mismatch: {cp}")
            count["checked"] += 1
            human_code = canonical(r["prompt"] + r["solution"]) + "\n"
            valid_human_312 = structure_ok(human_code)
            valid_agc_312 = structure_ok(obj["agc_code"])
            if valid_human_312 != bool(obj["human_valid"]):
                count["human_parser_disagreement"] += 1
                if not valid_human_312:
                    errors.append(f"3.12 rejected original HWC: {cp.name}")
            if valid_agc_312 != bool(obj["agc_valid"]):
                count["agc_parser_disagreement"] += 1
                if not valid_agc_312:
                    invalid_312_but_311_valid.append(r["line_no"])
                else:
                    recovered_by_312.append(r["line_no"])
            generated_bucket = bucket(obj["clean_output"])
            if generated_bucket != obj.get("bucket"):
                raise ValueError(f"Checkpoint body bucket mismatch: {cp}")
            if obj.get("body_tokens") != len(obj["clean_output"].strip("\n").split(" ")):
                raise ValueError(f"Checkpoint literal-space body token count mismatch: {cp}")
            if not valid_human_312:
                count["invalid_human_312"] += 1
            elif not valid_agc_312:
                count["invalid_agc_312"] += 1
            elif generated_bucket == "out_of_range":
                count["out_of_range"] += 1
            elif obj["body_sha256"] in seen_bodies:
                count["duplicate_body"] += 1
            else:
                count["accepted_312"] += 1
                seen_bodies.add(obj["body_sha256"])
                valid_buckets[generated_bucket] += 1
            # A sample accepted by the original 3.11 gate cannot be excluded by 3.12.
            if obj.get("accepted_for_pool") and not (valid_human_312 and valid_agc_312):
                errors.append(f"Existing accepted sample invalid under Python 3.12: {cp.name}")
        if count["missing"]:
            errors.append(f"{tag}: incomplete checkpoints ({count['checked']}/{len(required)})")
        report["per_temperature"][tag] = {
            "counts": dict(sorted(count.items())),
            "accepted_312_by_generated_bucket": {b: valid_buckets[b] for b in BUCKET_NAMES},
            "buckets_with_any_312": sum(valid_buckets[b] > 0 for b in BUCKET_NAMES),
            "buckets_with_15_312": sum(valid_buckets[b] >= 15 for b in BUCKET_NAMES),
            "ready_for_15_each_312": all(valid_buckets[b] >= 15 for b in BUCKET_NAMES),
            "invalid_312_but_311_valid_lines": invalid_312_but_311_valid,
            "valid_312_but_311_invalid_lines": recovered_by_312,
        }
        print(f"[AST-312] {phase} {tag}: checked={count['checked']}/{len(required)} "
              f"accepted_312={count['accepted_312']} parser_disagreement={count['agc_parser_disagreement']} "
              f"buckets_any={sum(valid_buckets[b]>0 for b in BUCKET_NAMES)}/10")
    report["errors"] = errors[:100]
    report["status"] = "PASS" if not errors else "FAIL"
    output_path = base / f"ast_{phase}_qc_python312.json"
    save_json(output_path, report)
    print(f"[AST-312] report={output_path} status={report['status']}")
    return report


def self_test() -> None:
    assert structure_ok('def f():\n    """D"""\n    return 1\n')
    assert not structure_ok('def f():\n    """D"""\n    pass\n')
    assert not structure_ok('def f():\n    """D"""\n')
    assert not structure_ok('def f():\n    return 1\ndef g():\n    return 2\n')
    print(f"[AST-312] SELF-TEST PASS Python={platform.python_version()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("output/run-x-a-01/v2"))
    parser.add_argument("--phase", choices=("self-test", "plan", "smoke", "pilot", "full"), required=True)
    parser.add_argument("--expect-python", default="3.12.13")
    args = parser.parse_args()
    if args.expect_python != "any" and platform.python_version() != args.expect_python:
        raise RuntimeError(f"Requires Python {args.expect_python}; found {platform.python_version()} at {sys.executable}")
    if args.phase == "self-test":
        self_test()
        return 0
    spec, rows = load_plan(args.out)
    report = (audit_plan(args.out, spec, rows) if args.phase == "plan"
              else audit_checkpoints(args.out, spec, rows, args.phase))
    return 0 if report["status"] == "PASS" else 3


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"[AST-312] ERROR {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
