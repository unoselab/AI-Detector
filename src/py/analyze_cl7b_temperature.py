#!/usr/bin/env python3
"""A-01 revision v4: matched-prompt CL-7B temperature dataset construction.

Inputs (read only):
    <source-out>/run_spec.json, plan.jsonl,
    <source-out>/production/checkpoints/{t02,t04,t06}/*.json,
    <source-out>/production/model_metadata/{t02,t04,t06}.json
Outputs (new; <source-out>/analysis-v4 only):
    pilot_review.json or full_review.json, coverage_by_source_stratum.csv,
    matched_prompt_metadata.csv, matched_{tag}_pairs.csv (full only),
    secondary_{tag}_metadata.csv, and optional secondary_balanced_{tag}_pairs.csv.

This script is pure standard-library Python for the separate AST Python 3.12.13.
It never regenerates code or modifies v2 frozen plans, checkpoints, or QC.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import platform
import statistics
import sys
import tempfile
import textwrap
import warnings
from collections import Counter, defaultdict
from pathlib import Path

TAGS = ("t02", "t04", "t06")
TEMPERATURES = {"t02": 0.2, "t04": 0.4, "t06": 0.6}
BINS = tuple(f"type{i:02d}_{100 + 10*i}" for i in range(1, 11))
VERSION = "run-x-a-01-protocol-v4"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text(s: str) -> str:
    return sha(s.encode("utf-8"))


def canonical(value: str) -> str:
    return textwrap.dedent(str(value or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp-" + str(os.getpid()))
    try:
        temp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def atomic_csv(path: Path, header: list[str], data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp-" + str(os.getpid()))
    try:
        with temp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def structure_ok(source: str) -> bool:
    # Suppress non-fatal invalid-escape SyntaxWarning while parsing historical code.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            block = ast.parse(source).body
        except (SyntaxError, IndentationError, ValueError):
            return False
    if len(block) != 1 or not isinstance(block[0], (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    body = list(block[0].body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body.pop(0)
    return any(not isinstance(statement, ast.Pass) for statement in body)


def body_bin(count: int) -> str:
    if 100 <= count <= 200:
        j = 1 if count <= 110 else (count - 101) // 10 + 1
        return BINS[j - 1]
    return "under_100" if count < 100 else "over_200"


def load_source(out: Path) -> tuple[dict, list[dict]]:
    spec = read_json(out / "run_spec.json")
    plan = (out / "plan.jsonl").read_bytes()
    if spec.get("experiment") != "run-x-a-01-v2" or sha(plan) != spec.get("plan_sha256"):
        raise RuntimeError("Frozen v2 plan/spec mismatch")
    rows = [json.loads(line) for line in plan.decode("utf-8").splitlines() if line.strip()]
    if len(rows) != spec["max_prompts"] or len({r["prompt_sha256"] for r in rows}) != len(rows):
        raise RuntimeError("Frozen v2 plan size/uniqueness mismatch")
    for r in rows:
        if hash_text(canonical(r["prompt"])) != r["prompt_sha256"]:
            raise RuntimeError(f"Prompt hash mismatch at {r['line_no']}")
        if hash_text(canonical(r["prompt"] + r["solution"])) != r["human_sha256"]:
            raise RuntimeError(f"HWC code hash mismatch at {r['line_no']}")
        if body_bin(r["human_body_tokens"]) != r["source_stratum"]:
            raise RuntimeError(f"Source stratum mismatch at {r['line_no']}")
    return spec, rows


def read_checkpoint(out: Path, spec: dict, row: dict, tag: str) -> dict | None:
    path = out / "production" / "checkpoints" / tag / f"{row['line_no']:09d}-{row['prompt_sha256'][:12]}.json"
    if not path.exists():
        return None
    obj = read_json(path)
    if (obj.get("tag") != tag or obj.get("temperature") != TEMPERATURES[tag]
            or obj.get("line_no") != row["line_no"]
            or obj.get("experiment") != spec["experiment"]
            or obj.get("plan_sha256") != spec["plan_sha256"]
            or obj.get("prompt_sha256") != row["prompt_sha256"]
            or obj.get("human_sha256") != row["human_sha256"]
            or obj.get("human_body_tokens") != row["human_body_tokens"]
            or obj.get("source_stratum") != row["source_stratum"]
            or obj.get("body_sha256") != hash_text(obj["clean_output"].strip("\n"))
            or obj.get("agc_code") != canonical(row["prompt"] + obj["clean_output"]) + "\n"
            or obj.get("body_tokens") != len(obj["clean_output"].strip("\n").split(" "))
            or obj.get("bucket") != (body_bin(obj["body_tokens"]) if 100 <= obj["body_tokens"] <= 200 else "out_of_range")
            or obj.get("accepted_for_pool") != bool(obj.get("human_valid") and obj.get("agc_valid") and 100 <= obj["body_tokens"] <= 200)):
        raise RuntimeError(f"Checkpoint provenance/integrity mismatch: {path}")
    return obj


def model_provenance(out: Path, spec: dict, require: bool) -> dict:
    meta = {}
    for tag in TAGS:
        file = out / "production" / "model_metadata" / f"{tag}.json"
        if not file.is_file():
            if require:
                raise RuntimeError(f"Missing GPU model metadata: {file}")
            continue
        m = read_json(file)
        if m.get("model") != spec["model"] or m.get("dtype") != "torch.float16":
            raise RuntimeError(f"Unexpected model/dtype metadata: {file}")
        meta[tag] = m
    if require and len({m.get("model_commit") for m in meta.values()}) != 1:
        raise RuntimeError("Model revision mismatch across temperature GPUs")
    return meta


def export_pairs(path: Path, selected: list[tuple[dict, dict]]) -> None:
    rows = []
    for original, result in selected:
        sid = f"line{original['line_no']}"
        rows.append({"idx": sid + "_human", "code": canonical(original["prompt"] + original["solution"]) + "\n", "label": "human"})
        rows.append({"idx": sid + "_lm", "code": result["agc_code"], "label": "lm"})
    atomic_csv(path, ["idx", "code", "label"], rows)


def analyze(args: argparse.Namespace) -> dict:
    source = Path(args.out)
    spec, all_rows = load_source(source)
    selection = all_rows[:spec["pilot_size"]] if args.phase == "pilot" else all_rows
    report_out = source / "analysis-v4"
    metadata = model_provenance(source, spec, require=(args.phase != "check"))
    counts = {t: Counter() for t in TAGS}
    bin_valid = {t: Counter() for t in TAGS}
    by_source = defaultdict(lambda: Counter())
    primary = {t: [] for t in TAGS}
    secondary = {t: [] for t in TAGS}
    matched = []
    complete = 0
    common_valid = 0
    common_length = 0
    reason_counter = Counter()
    secondary_seen = {t: set() for t in TAGS}
    for r in selection:
        objects = {t: read_checkpoint(source, spec, r, t) for t in TAGS}
        if all(v is not None for v in objects.values()):
            complete += 1
        else:
            if args.phase in ("pilot", "full"):
                missing = [t for t in TAGS if objects[t] is None]
                raise RuntimeError(f"Missing {missing} at line={r['line_no']} for phase={args.phase}")
        hcode = canonical(r["prompt"] + r["solution"]) + "\n"
        human_ok = structure_ok(hcode)
        if not human_ok:
            raise RuntimeError(f"Python 3.12 invalid HWC: {r['line_no']}")
        flags = {}
        for tag, obj in objects.items():
            if obj is None:
                counts[tag]["missing"] += 1
                continue
            counts[tag]["checkpoints"] += 1
            agc_ok = structure_ok(obj["agc_code"])
            flags[tag] = agc_ok
            if agc_ok != bool(obj["agc_valid"]):
                counts[tag]["python_311_vs_312_disagreement"] += 1
                # Fail if v2 believed code to be valid and 3.12 rejects it.
                if bool(obj["agc_valid"]) and not agc_ok:
                    raise RuntimeError(f"Python 3.12 rejected 3.11-valid AGC: {tag} line={r['line_no']}")
            if agc_ok:
                counts[tag]["ast_valid"] += 1
                category = body_bin(obj["body_tokens"])
                if category in BINS:
                    counts[tag]["ast_valid_length_100_200"] += 1
                    if obj["body_sha256"] not in secondary_seen[tag]:
                        secondary_seen[tag].add(obj["body_sha256"])
                        secondary[tag].append((r, obj))
                        bin_valid[tag][category] += 1
                else:
                    counts[tag][category] += 1
            else:
                counts[tag]["invalid_agc"] += 1
        if len(flags) == 3:
            if all(flags.values()):
                common_valid += 1
                lengths = [objects[t]["body_tokens"] for t in TAGS]
                if all(100 <= n <= 200 for n in lengths):
                    common_length += 1
                by_source[r["source_stratum"]]["common_ast_valid"] += 1
                matched.append({"line_no": r["line_no"], "prompt_sha256": r["prompt_sha256"],
                                "human_sha256": r["human_sha256"], "source_stratum": r["source_stratum"],
                                "human_body_tokens": r["human_body_tokens"],
                                **{f"{t}_body_tokens": objects[t]["body_tokens"] for t in TAGS},
                                **{f"{t}_body_sha256": objects[t]["body_sha256"] for t in TAGS}})
                for tag in TAGS:
                    primary[tag].append((r, objects[tag]))
            else:
                reason_counter["common_invalid_one_or_more"] += 1
        by_source[r["source_stratum"]]["total"] += 1
    review = {
        "protocol": VERSION, "phase": args.phase, "source_experiment": spec["experiment"],
        "plan_sha256": spec["plan_sha256"], "source_out": str(source.resolve()),
        "python_ast_binary": sys.executable, "python_ast_version": platform.python_version(),
        "selection_size": len(selection), "complete_triplets": complete,
        "common_ast_valid_triplets": common_valid, "common_ast_valid_rate": round(common_valid / max(1, complete), 6),
        "common_ast_and_100_200_triplets": common_length,
        "temperature": {t: {**dict(counts[t]),
                            "length_100_200_unique_body": len(secondary[t]),
                            "length_100_200_by_generated_bucket": {b: bin_valid[t][b] for b in BINS}} for t in TAGS},
        "model_metadata": metadata,
        "primary_protocol": "All three temperature outputs must be Python-3.12-AST-valid for the SAME prompt. No AGC length restriction. HWC original body selection 100-200 is retained and disclosed.",
        "secondary_protocol": "Within each temperature, AST-valid generated-body length 100-200, unique continuation per tag. Cross-temperature prompt sets may differ; cannot be interpreted as paired.",
        "primary_machine_learning_metrics_computed": False,
        "secondary_ready_for_15_per_bucket": {t: all(bin_valid[t][b] >= 15 for b in BINS) for t in TAGS},
    }
    if args.phase == "pilot":
        review["min_common_ast_valid_rate"] = args.min_pilot_common_rate
        review["min_source_stratum_common_n"] = args.min_source_common_n
        review["common_by_source_stratum"] = {b: by_source[b]["common_ast_valid"] for b in BINS}
        review["recommend_full"] = (
            complete == len(selection)
            and review["common_ast_valid_rate"] >= args.min_pilot_common_rate
            and all(by_source[b]["common_ast_valid"] >= args.min_source_common_n for b in BINS))
    if args.phase in ("pilot", "full"):
        report_out.mkdir(parents=True, exist_ok=True)
        atomic_json(report_out / f"{args.phase}_review.json", review)
        rows = [{"source_stratum": b, "total": by_source[b]["total"], "common_ast_valid": by_source[b]["common_ast_valid"],
                 "common_rate": round(by_source[b]["common_ast_valid"] / max(1, by_source[b]["total"]), 6)} for b in BINS]
        atomic_csv(report_out / f"{args.phase}_by_source_stratum.csv", ["source_stratum", "total", "common_ast_valid", "common_rate"], rows)
        if args.phase == "full":
            # All three CSV files have exactly the same sorted prompt IDs / HWC code.
            atomic_csv(report_out / "matched_prompt_metadata.csv", list(matched[0].keys()) if matched else
                       ["line_no", "prompt_sha256", "human_sha256", "source_stratum", "human_body_tokens"] +
                       [f"{t}_body_tokens" for t in TAGS] + [f"{t}_body_sha256" for t in TAGS], matched)
            for tag in TAGS:
                export_pairs(report_out / f"matched_{tag}_pairs.csv", primary[tag])
                secondary_meta = [{"line_no": r["line_no"], "prompt_sha256": r["prompt_sha256"],
                                   "source_stratum": r["source_stratum"], "body_tokens": obj["body_tokens"],
                                   "generated_bucket": body_bin(obj["body_tokens"]), "body_sha256": obj["body_sha256"]}
                                  for r, obj in secondary[tag]]
                atomic_csv(report_out / f"secondary_{tag}_metadata.csv",
                           ["line_no", "prompt_sha256", "source_stratum", "body_tokens", "generated_bucket", "body_sha256"], secondary_meta)
                # Do not claim a balanced benchmark unless every generated-length bucket is large enough.
                if review["secondary_ready_for_15_per_bucket"][tag]:
                    chosen = []
                    for b in BINS:
                        candidates = [(r, o) for r, o in secondary[tag] if body_bin(o["body_tokens"]) == b]
                        candidates.sort(key=lambda pair: (hash_text(f"{spec['seed']}|{tag}|{pair[0]['prompt_sha256']}"), pair[0]["line_no"]))
                        chosen.extend(candidates[:15])
                    chosen.sort(key=lambda pair: pair[0]["line_no"])
                    export_pairs(report_out / f"secondary_balanced_{tag}_pairs.csv", chosen)
        print(f"[REVIEW-v4] phase={args.phase} matched_ast={common_valid}/{complete} rate={review['common_ast_valid_rate']:.3f} "
              f"matched_length_100_200={common_length}")
        if args.phase == "pilot":
            print(f"[REVIEW-v4] recommend_full={review['recommend_full']} "
                  f"common_by_source_stratum={review['common_by_source_stratum']}")
        else:
            print(f"[EXPORT-v4] matched primary: {common_valid} prompts; {2*common_valid} CSV rows per temperature")
            print(f"[EXPORT-v4] secondary readiness={review['secondary_ready_for_15_per_bucket']}")
        print(f"[REVIEW-v4] report={report_out / f'{args.phase}_review.json'}")
    else:
        print(f"[CHECK-v4] completed triplets={complete}/{len(selection)}, matched_AST={common_valid}, "
              f"matched_AST_and_length={common_length}")
    return review


def self_test() -> None:
    assert structure_ok('def f():\n    """Example"""\n    return 1\n')
    assert not structure_ok('def f():\n    """Example"""\n    pass\n')
    assert body_bin(100) == 'type01_110'
    assert body_bin(110) == 'type01_110'
    assert body_bin(111) == 'type02_120'
    assert body_bin(200) == 'type10_200'
    assert body_bin(201) == 'over_200'
    print(f"[SELF-TEST-v4] PASS Python={platform.python_version()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("pilot", "full", "check", "self-test"), required=True)
    parser.add_argument("--out", type=Path, default=Path("output/run-x-a-01/v2"))
    parser.add_argument("--min-pilot-common-rate", type=float, default=0.30,
                        help="Minimum fraction of pilot prompts valid under all 3 temperatures")
    parser.add_argument("--min-source-common-n", type=int, default=4,
                        help="Minimum common-AST-valid pilot prompts in each original-HWC length stratum")
    parser.add_argument("--expect-python", default="3.12.13")
    args = parser.parse_args()
    if args.expect_python != "any" and platform.python_version() != args.expect_python:
        raise RuntimeError(f"Expected Python {args.expect_python}, got {platform.python_version()}")
    if args.phase == "self-test":
        self_test()
        return 0
    if not 0 <= args.min_pilot_common_rate <= 1 or args.min_source_common_n < 0:
        raise ValueError("Invalid pilot threshold")
    review = analyze(args)
    return 0 if (args.phase != "pilot" or review["recommend_full"]) else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR-v4] {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
