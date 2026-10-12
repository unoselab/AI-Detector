#!/usr/bin/env python3
"""run-x-05: recover the target CodeLlama-7B procedure from saved T=0.0 output.

Read-only inputs:
  run-x-02 pilot_prepared.jsonl, pilot_generation.jsonl, experiment_config.json,
  pilot_selection.csv; run-x-04 experiment_config.json, ablation_generation.jsonl,
  ablation_summary.json; original 4,500-pair CSV and split manifest; original
  code-generation/find_validsyntax_mgc.py.

Outputs (only under the new run-x-05 output directory):
  extraction_qc.csv, extraction_comparison.csv, extracted_valid_pairs.csv,
  extraction_summary.json, extraction_findings.txt, extracted_functions.jsonl,
  runtime_environment.json, input_manifest.json.

Extraction policy:
  - Keep the original prompt unchanged; never invent or regenerate code.
  - Derive the continuation indentation from the function's existing prompt.
  - Find the first AST-valid complete target procedure before a dedented
    sibling/top-level statement, preserving more deeply indented nested defs.
  - If no safe boundary is found, test the complete continuation.
  - Validate using the exact existing Python validator plus stricter checks
    for a single top-level target definition, name, signature and docstring.
  - Record failures; do not substitute another procedure or pad the sample.

Use Python 3.11 for server results. Use --allow-other-python only for explicit
local software tests, never for the final comparison.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import platform
import re
import sys
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPERIMENT = "run-x-05"
EXPECTED_MODEL = "codellama/CodeLlama-7b-hf"
CONDITIONS = ("legacy", "no_boundary", "standard")


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot-dir", type=Path, required=True)
    ap.add_argument("--ablation-dir", type=Path, required=True)
    ap.add_argument("--validator-script", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-other-python", action="store_true")
    ap.add_argument("--allow-unmounted-sources", action="store_true",
                    help="Offline fixture testing only; never for server results")
    return ap.parse_args()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def file_sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    require(path.is_file(), f"Required input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    require(path.is_file(), f"Required input missing: {path}")
    result = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if line.strip():
                try:
                    result.append(json.loads(line))
                except ValueError as error:
                    raise RuntimeError(f"Invalid JSONL record {path}:{line_no}: {error}") from error
    return result


def atomic_text(path: Path, text: str):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_json(path: Path, obj: Any):
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, records: list[dict]):
    atomic_text(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


def write_csv(path: Path, records: list[dict], headers: list[str]):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    temporary.replace(path)


def import_validator(path: Path):
    require(path.is_file(), f"Validator missing: {path}")
    spec = importlib.util.spec_from_file_location("agc_old_validator_runx05", str(path))
    require(spec is not None and spec.loader is not None, "Cannot import original validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for function in ("compose_code", "syntax_check", "code_has_required_structure"):
        require(hasattr(module, function), f"Original validator missing {function}")
    return module


def check_python(allow_other: bool):
    current = (sys.version_info.major, sys.version_info.minor)
    require(current == (3, 11) or allow_other,
            f"Python 3.11 is required for reproducible filtering, got {sys.version}. "
            "Use the aidetector conda environment.")
    return {"python_version": sys.version, "python_executable": sys.executable,
            "python_implementation": platform.python_implementation(),
            "python311": current == (3, 11),
            "allow_other_python": allow_other}


def source_integrity(config: dict, allow_missing: bool):
    checks = []
    for key, digest_key in (("original_csv", "original_csv_sha256"),
                            ("split_manifest", "split_manifest_sha256"),
                            ("validator_script", "validator_script_sha256")):
        path = Path(config[key])
        exists = path.is_file()
        if not exists and not allow_missing:
            require(False, f"Original benchmark input is missing: {path}")
        if exists:
            actual = file_sha256(path)
            require(actual == config[digest_key], f"Original source changed: {path}")
            status = "PASS"
        else:
            status = "NOT_MOUNTED_OFFLINE_ONLY"
        checks.append({"key": key, "path": str(path),
                       "expected_sha256": config[digest_key], "status": status})
    return checks


def load_and_verify(args):
    pilot = args.pilot_dir.resolve()
    ablation = args.ablation_dir.resolve()
    require(pilot != ablation, "Pilot and ablation directories must be distinct")
    pfiles = ("experiment_config.json", "pilot_prepared.jsonl", "pilot_selection.csv",
              "pilot_generation.jsonl")
    afiles = ("experiment_config.json", "ablation_generation.jsonl", "ablation_summary.json")
    pc = read_json(pilot / "experiment_config.json")
    ac = read_json(ablation / "experiment_config.json")
    summary = read_json(ablation / "ablation_summary.json")
    require(pc.get("experiment") == "run-x-02" and pc.get("mode") == "T0_GREEDY",
            "Input does not match run-x-02 T=0.0 baseline")
    require(pc.get("model") == EXPECTED_MODEL and pc.get("temperature") == 0.0,
            "Model or temperature does not match baseline")
    require(pc.get("do_sample") is False and pc.get("top_p") is None,
            "Sampling settings do not match baseline")
    require(int(pc.get("pilot_pairs", -1)) == 100, "Expected 100-pair pilot")
    require(ac.get("experiment") == "run-x-04" and ac.get("pair_count") == 100,
            "Input is not the completed run-x-04 ablation")
    require(ac.get("model") == EXPECTED_MODEL and ac.get("ablation_eos_ids", {}).get("standard") == [2],
            "Standard-EOS condition does not match expected design")
    require(ac.get("do_sample") is False and ac.get("temperature_argument") is None,
            "Ablation must use greedy decoding")
    require(summary.get("status") == "PASS" and summary.get("completed_new_generations") == 200,
            "Ablation has not completed all 200 new generations")
    require(int(ac.get("prompt_max_tokens")) == int(pc["prompt_max_tokens"])
            and int(ac["max_new_tokens"]) == int(pc["max_new_tokens"]),
            "Tokenization settings differ across experiments")
    if not args.allow_unmounted_sources:
        require(Path(ac["pilot_dir"]).resolve() == pilot, "Ablation references a different pilot directory")
    for name, expected_digest in ac["pilot_hashes"].items():
        require(name in pfiles and file_sha256(pilot / name) == expected_digest,
                f"Ablation input provenance mismatch: {name}")
    require(file_sha256(args.validator_script) == pc["validator_script_sha256"]
            == ac["original_validator_sha256"], "Validator has changed")
    if not args.allow_unmounted_sources:
        require(args.validator_script.resolve() == Path(pc["validator_script"]).resolve(),
                "Validator file path differs from baseline")
    sources = source_integrity(pc, args.allow_unmounted_sources)

    prepared = read_jsonl(pilot / "pilot_prepared.jsonl")
    old = read_jsonl(pilot / "pilot_generation.jsonl")
    generated = read_jsonl(ablation / "ablation_generation.jsonl")
    require(len(prepared) == len(old) == 100 and len(generated) == 200,
            "Input must contain 100 prepared, 100 legacy, 200 new generations")
    require(len({p["pair_id"] for p in prepared}) == 100, "Duplicate pilot pair IDs")
    old_map = {r["pair_id"]: r for r in old}
    require(len(old_map) == 100, "Duplicate legacy predictions")
    indexed = {(r["mode"], r["pair_id"]): r for r in generated}
    require(len(indexed) == 200, "Duplicate ablation generations")
    with (pilot / "pilot_selection.csv").open(newline="", encoding="utf-8") as stream:
        selected = list(csv.DictReader(stream))
    require(len(selected) == 100 and {p["pair_id"] for p in selected} ==
            {p["pair_id"] for p in prepared}, "Pilot selection changed")
    for p in prepared:
        pid = p["pair_id"]
        require(text_sha256(p["prompt"]) == p["prompt_sha256"] and
                text_sha256(p["human_code"]) == p["human_sha256"],
                f"Corrupt prepared prompt/HWC: {pid}")
        require(old_map[pid]["prompt_sha256"] == p["prompt_sha256"] and
                text_sha256(old_map[pid]["new_agc_code"]) == old_map[pid]["new_agc_sha256"],
                f"Corrupt legacy record: {pid}")
        for mode, eos in (("standard", [2]), ("no_boundary", [2, 822])):
            row = indexed.get((mode, pid))
            require(row is not None and row.get("eos_ids") == eos and
                    row.get("prompt_sha256") == p["prompt_sha256"] and
                    row.get("split") == p["split"] and
                    row.get("complexity_block") == p["complexity_block"] and
                    row.get("temperature") == 0.0 and row.get("do_sample") is False and
                    text_sha256(row["raw_output"]) == row["raw_sha256"] and
                    text_sha256(row["new_agc_code"]) == row["new_agc_sha256"],
                    f"Aborted due to mismatched ablation record: {mode}/{pid}")
    checks = {"run_x_02": {name: file_sha256(pilot / name) for name in pfiles},
              "run_x_04": {name: file_sha256(ablation / name) for name in afiles},
              "original_source_checks": sources, "validator_sha256": file_sha256(args.validator_script)}
    return prepared, old_map, indexed, summary, checks


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


def main():
    args = parse_args()
    environment = check_python(args.allow_other_python)
    require(args.output_dir.resolve() not in (args.pilot_dir.resolve(), args.ablation_dir.resolve()),
            "Output directory cannot be an existing experiment directory")
    if args.output_dir.exists():
        require(not any(args.output_dir.iterdir()),
                "Output directory is not empty: use a fresh RUN_ID")
    print(f"[INPUT] Python={sys.version.split()[0]} executable={sys.executable}", flush=True)
    prepared, old, generated, previous_summary, checks = load_and_verify(args)
    validator = import_validator(args.validator_script)
    print("[INPUT] 100 prepared pairs, 100 legacy, 200 ablation generation records verified", flush=True)
    if args.dry_run:
        print("[DRY-RUN] PASS: integrity verified, no output written", flush=True)
        return 0
    results, qc, paired, compared = [], [], [], []
    for p in prepared:
        pid = p["pair_id"]
        row = generated[("standard", pid)]
        b = generated[("no_boundary", pid)]
        a = old[pid]
        extraction = extract_one(validator, p, row)
        new = {"pair_id": pid, "split": p["split"],
               "complexity_block": p["complexity_block"],
               "complexity_score": p.get("complexity_score", ""),
               "prompt_sha256": p["prompt_sha256"],
               "human_sha256": p["human_sha256"],
               "standard_raw_sha256": row["raw_sha256"],
               "standard_generated_tokens": row["generated_tokens"],
               "original_standard_status": row["status"],
               **extraction}
        results.append(new)
        qc.append({k: v for k, v in new.items() if k not in
                   ("extracted_agc_code", "extracted_continuation")})
        compared.append({"pair_id": pid, "split": p["split"],
                         "complexity_block": p["complexity_block"],
                         "original_standard_valid": row["status"] == "VALID",
                         "extracted_standard_valid": extraction["status"] == "VALID",
                         "legacy_valid": a["status"] == "VALID",
                         "no_boundary_valid": b["status"] == "VALID",
                         "standard_generated_tokens": row["generated_tokens"],
                         "extracted_boundary": extraction["boundary"],
                         "extracted_standard_sha256": extraction["extracted_agc_sha256"],
                         "no_boundary_sha256": b["new_agc_sha256"],
                         "legacy_sha256": a["new_agc_sha256"],
                         "identical_to_no_boundary": extraction["status"] == "VALID"
                         and extraction["extracted_agc_sha256"] == b["new_agc_sha256"],
                         "identical_to_legacy": extraction["status"] == "VALID"
                         and extraction["extracted_agc_sha256"] == a["new_agc_sha256"],
                         "reason": extraction["error"]})
        if extraction["status"] == "VALID":
            paired.append({"idx": f"{pid}_human", "code": p["human_code"], "label": "human"})
            paired.append({"idx": f"{pid}_lm", "code": extraction["extracted_agc_code"],
                           "label": "lm"})
    counts = Counter(r["status"] for r in results)
    old_valid = sum(r["status"] == "VALID" for r in (generated[("standard", p["pair_id"])] for p in prepared))
    split_count = {split: {"selected": sum(p["split"] == split for p in prepared),
                           "extracted_valid": sum(p["split"] == split and r["status"] == "VALID"
                                                  for p, r in zip(prepared, results))}
                   for split in ("train", "dev", "test")}
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "extracted_functions.jsonl", results)
    write_csv(output / "extraction_qc.csv", qc, list(qc[0]))
    write_csv(output / "extraction_comparison.csv", compared, list(compared[0]))
    write_csv(output / "extracted_valid_pairs.csv", paired, ["idx", "code", "label"])
    environment.update({"validator_path": str(args.validator_script.resolve()),
                        "validator_sha256": checks["validator_sha256"]})
    write_json(output / "runtime_environment.json", environment)
    write_json(output / "input_manifest.json", checks)
    summary = {"experiment": EXPERIMENT, "status": "PASS",
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "pilot_pairs": len(prepared),
               "original_standard_valid": old_valid,
               "extracted_standard_valid": counts["VALID"],
               "extracted_standard_invalid": counts["INVALID"],
               "additional_valid_vs_original_standard": counts["VALID"] - old_valid,
               "valid_paired_csv_rows": len(paired), "split": split_count,
               "boundary_counts": dict(Counter(r["boundary"].split("_")[0] for r in results)),
               "matched_no_boundary_code": sum(r["identical_to_no_boundary"] for r in compared),
               "matched_legacy_code": sum(r["identical_to_legacy"] for r in compared),
               "no_boundary_valid": previous_summary["mode_validity"]["no_boundary"]["VALID"],
               "previous_legacy_valid": previous_summary["mode_validity"]["legacy"]["VALID"],
               "python311": environment["python311"],
               "source_integrity": "PASS" if all(c["status"] == "PASS" for c in checks["original_source_checks"])
                                  else "OFFLINE_FIXTURE_ONLY"}
    write_json(output / "extraction_summary.json", summary)
    findings = [f"Experiment: {EXPERIMENT} | Function extraction from T=0.0 Standard EOS",
                f"Status: {summary['status']}",
                f"Original standard validator: {old_valid}/100",
                f"AST-boundary extracted valid: {counts['VALID']}/100",
                f"Additional valid functions: {summary['additional_valid_vs_original_standard']}",
                f"Paired CSV rows (HWC + AGC): {len(paired)}",
                f"Split: {split_count}",
                f"Matched no-boundary AGC code: {summary['matched_no_boundary_code']}",
                f"Python 3.11: {summary['python311']}",
                f"Source integrity: {summary['source_integrity']}",
                "LIMITATION: AST/structure valid does not prove behavioral completeness.",
                "LIMITATION: Standard EOS still has a 512-token generation cap.",
                "NOTE: No GPU generation. No originals modified. No invalid-pair backfill."]
    atomic_text(output / "extraction_findings.txt", "\n".join(findings) + "\n")
    for entry in findings:
        print(entry, flush=True)
    print(f"Outputs saved in: {output}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, SyntaxError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
