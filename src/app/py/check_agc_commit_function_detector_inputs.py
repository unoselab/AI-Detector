#!/usr/bin/env python3
"""
Check commit-function artifacts before fresh AGC detector inference.

This preflight validates the Python 3.12 extraction manifest and every referenced
function artifact without loading the embedding model or classifier. It is
intended to run in the existing ai_detector environment, where the validated
AGC detector and tree-sitter parser are already installed.

The runtime Python AST result is diagnostic only. Python 3.12-generated
artifacts may be valid detector inputs even when an older runtime Python cannot
parse newer syntax. Tree-sitter compatibility, source hashes, one-function
boundaries, and function-name agreement are the required inference gates.

Command: 
  python src/app/py/check_agc_commit_function_detector_inputs.py
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import textwrap
import tokenize
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Optional, Sequence

SCRIPT_PATH = Path(__file__).resolve()
APP_DIR = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
WORKSPACE_ROOT = REPO_ROOT.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agc_detector import extract_blocks, load_parser_and_F, strip_block_markers  # type: ignore

DEFAULT_MANIFEST = (
    WORKSPACE_ROOT
    / "ai_code_complexity_study_python/ai-code-complexity-study"
    / "repo_python/run-py-5a-py312/strict/commit_function_detection_manifest.csv"
)
DEFAULT_SOURCE_ROOT = (
    WORKSPACE_ROOT
    / "ai_code_complexity_study_python/ai-code-complexity-study"
    / "repo_python/run-py-5a-py312/strict/commit_function_sources"
)
DEFAULT_OUTPUT_ROOT = (
    WORKSPACE_ROOT
    / "ai_code_complexity_study_python/python_commit_function_detect"
    / "input_compatibility/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast"
    / "strict/py312"
)
DEFAULT_TREE_SITTER_LIB = (
    REPO_ROOT / "src/code-analyzer-tree-sitter/build/my-languages.so"
)
DEFAULT_AST_HELPER_DIR = REPO_ROOT / "src/code-analyzer-tree-sitter"
DEFAULT_EXPECTED_ROWS = 450_548

FAILURE_FIELDS = [
    "manifest_row_number",
    "function_event_id",
    "dataset_source",
    "repo_name",
    "time",
    "commit",
    "relative_path",
    "qualified_function_name",
    "function_name",
    "function_source_path",
    "stage",
    "error_type",
    "error_message",
]

RUNTIME_AST_FIELDS = FAILURE_FIELDS + ["runtime_python"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--function-event-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )
    parser.add_argument(
        "--function-source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument(
        "--tree-sitter-lib",
        type=Path,
        default=DEFAULT_TREE_SITTER_LIB,
    )
    parser.add_argument(
        "--ast-helper-dir",
        type=Path,
        default=DEFAULT_AST_HELPER_DIR,
    )
    parser.add_argument(
        "--expected-manifest-rows",
        type=int,
        default=DEFAULT_EXPECTED_ROWS,
        help="Use 0 to disable the exact row-count check.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Process the first N sorted manifest rows; use 0 for all rows.",
    )
    parser.add_argument("--progress-every", type=int, default=10_000)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def require_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise SystemExit(f"[ERROR] {label} not found: {resolved}")
    return resolved


def require_dir(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"[ERROR] {label} not found: {resolved}")
    return resolved


def first_field(
    fieldnames: Sequence[str],
    candidates: Sequence[str],
    label: str,
    required: bool = True,
) -> Optional[str]:
    available = set(fieldnames)
    for candidate in candidates:
        if candidate in available:
            return candidate
    if required:
        raise SystemExit(
            f"[ERROR] manifest is missing {label}; accepted columns: "
            + ", ".join(candidates)
        )
    return None


def field_value(row: Dict[str, str], field: Optional[str]) -> str:
    if field is None:
        return ""
    return str(row.get(field, "")).strip()


def validate_relative_python_path(text: str, label: str) -> str:
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts:
        raise ValueError(f"invalid {label}: {text!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe {label}: {text!r}")
    if path.suffix.lower() != ".py":
        raise ValueError(f"{label} is not a .py file: {text!r}")
    return path.as_posix()


def resolve_source_path(root: Path, relative_path: str) -> Path:
    safe_path = validate_relative_python_path(
        relative_path,
        "function source path",
    )
    candidate = root.joinpath(*PurePosixPath(safe_path).parts)
    if not candidate.exists() and not candidate.is_symlink():
        raise FileNotFoundError(f"function source artifact not found: {candidate}")

    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve(strict=True)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"function source artifact escapes source root: {candidate}"
        ) from exc
    if not resolved_candidate.is_file():
        raise ValueError(
            f"function source artifact is not a regular file: {candidate}"
        )
    return resolved_candidate


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_python_source(path: Path) -> str:
    with tokenize.open(path) as handle:
        return handle.read()


def normalize_function_source(source: str) -> str:
    text = strip_block_markers(source)
    text = textwrap.dedent(text).strip()
    if not text:
        raise ValueError("function source artifact is empty")
    return text + "\n"


def leaf_function_name(qualified_name: str) -> str:
    normalized = qualified_name.strip().replace("::", ".")
    return normalized.rsplit(".", 1)[-1] if normalized else ""


def tree_has_error(root: Any) -> bool:
    value = getattr(root, "has_error", False)
    return bool(value() if callable(value) else value)


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_write_csv(
    path: Path,
    rows: Iterable[Dict[str, Any]],
    fieldnames: Sequence[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def failure_row(
    row_number: int,
    row: Dict[str, str],
    schema: Dict[str, Optional[str]],
    stage: str,
    exc: BaseException,
) -> Dict[str, Any]:
    qualified_name = field_value(row, schema["qualified_function_name"])
    function_name = field_value(row, schema["function_name"])
    return {
        "manifest_row_number": row_number,
        "function_event_id": field_value(row, schema["function_event_id"]),
        "dataset_source": field_value(row, schema["dataset_source"]),
        "repo_name": field_value(row, schema["repo_name"]),
        "time": field_value(row, schema["time"]),
        "commit": field_value(row, schema["commit"]),
        "relative_path": field_value(row, schema["relative_path"]),
        "qualified_function_name": qualified_name,
        "function_name": function_name or leaf_function_name(qualified_name),
        "function_source_path": field_value(row, schema["function_source_path"]),
        "stage": stage,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }


def run_self_test(tree_sitter_lib: Path, ast_helper_dir: Path) -> None:
    parser, _ = load_parser_and_F(str(tree_sitter_lib), str(ast_helper_dir))
    source = "@staticmethod\ndef sample(value: int) -> int:\n    return value + 1\n"
    tree = parser.parse(source.encode("utf-8"))
    if tree_has_error(tree.root_node):
        raise SystemExit("Self-test: FAIL (tree-sitter parse error)")
    blocks = extract_blocks(source, parser)
    if len(blocks) != 1 or blocks[0].get("name") != "sample":
        raise SystemExit("Self-test: FAIL (unexpected top-level block result)")
    print("Self-test: PASS")


def main() -> None:
    args = parse_args()
    if args.expected_manifest_rows < 0:
        raise SystemExit("[ERROR] --expected-manifest-rows cannot be negative")
    if args.max_events < 0:
        raise SystemExit("[ERROR] --max-events cannot be negative")
    if args.progress_every <= 0:
        raise SystemExit("[ERROR] --progress-every must be positive")

    manifest_path = require_file(
        args.function_event_manifest,
        "function-event manifest",
    )
    source_root = require_dir(
        args.function_source_root,
        "function source root",
    )
    tree_sitter_lib = require_file(args.tree_sitter_lib, "tree-sitter library")
    ast_helper_dir = require_dir(args.ast_helper_dir, "AST helper directory")
    output_root = args.output_root.expanduser().resolve()

    if args.self_test:
        run_self_test(tree_sitter_lib, ast_helper_dir)
        return

    parser, _ = load_parser_and_F(str(tree_sitter_lib), str(ast_helper_dir))

    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            raise SystemExit(f"[ERROR] manifest has no header: {manifest_path}")

        schema: Dict[str, Optional[str]] = {
            "function_event_id": first_field(
                fieldnames,
                ["function_event_id", "event_id"],
                "function event id",
            ),
            "dataset_source": first_field(
                fieldnames,
                ["dataset_source"],
                "dataset source",
            ),
            "repo_name": first_field(fieldnames, ["repo_name"], "repository name"),
            "time": first_field(fieldnames, ["time", "month"], "repo-month"),
            "commit": first_field(
                fieldnames,
                ["commit", "scan_current_commit"],
                "current commit",
            ),
            "relative_path": first_field(
                fieldnames,
                ["relative_path"],
                "repository file path",
            ),
            "qualified_function_name": first_field(
                fieldnames,
                ["qualified_function_name", "qualified_name"],
                "qualified function name",
            ),
            "function_name": first_field(
                fieldnames,
                ["function_name"],
                "function name",
                required=False,
            ),
            "function_source_path": first_field(
                fieldnames,
                [
                    "function_source_path",
                    "function_source_relative_path",
                    "source_relative_path",
                ],
                "function source path",
            ),
            "content_sha256": first_field(
                fieldnames,
                ["content_sha256", "function_content_sha256"],
                "function source SHA-256",
            ),
        }
        rows = list(reader)

    rows.sort(
        key=lambda row: (
            field_value(row, schema["dataset_source"]),
            field_value(row, schema["repo_name"]),
            field_value(row, schema["time"]),
            field_value(row, schema["commit"]),
            field_value(row, schema["relative_path"]),
            field_value(row, schema["qualified_function_name"]),
            field_value(row, schema["function_event_id"]),
        )
    )

    manifest_rows = len(rows)
    selected_rows = rows[: args.max_events] if args.max_events else rows

    print("=" * 76)
    print("Check AGC commit-function detector inputs")
    print(f"Runtime Python:        {sys.version.split()[0]}")
    print(f"Manifest:              {manifest_path}")
    print(f"Function source root:  {source_root}")
    print(f"Manifest rows:         {manifest_rows}")
    print(f"Selected rows:         {len(selected_rows)}")
    print(f"Expected rows:         {args.expected_manifest_rows or '<disabled>'}")
    print(f"Tree-sitter library:   {tree_sitter_lib}")
    print(f"Output root:           {output_root}")
    print("=" * 76)

    failures: list[Dict[str, Any]] = []
    runtime_ast_failures: list[Dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    runtime_ast_error_types: Counter[str] = Counter()
    dataset_counts: Counter[str] = Counter()
    duplicate_event_ids = 0
    seen_event_ids: set[str] = set()
    hash_verified = 0
    tree_sitter_valid = 0

    for index, row in enumerate(selected_rows, start=1):
        row_number = index + 1
        event_id = field_value(row, schema["function_event_id"])
        dataset_source = field_value(row, schema["dataset_source"]).lower()
        dataset_counts[dataset_source] += 1

        if event_id in seen_event_ids:
            duplicate_event_ids += 1
            exc = ValueError(f"duplicate function_event_id: {event_id}")
            record = failure_row(
                row_number,
                row,
                schema,
                "duplicate_event_id",
                exc,
            )
            failures.append(record)
            stage_counts[record["stage"]] += 1
            continue
        seen_event_ids.add(event_id)

        try:
            if dataset_source not in {"treatment", "control"}:
                raise ValueError(
                    f"unsupported dataset_source {dataset_source!r}"
                )
            source_relative = field_value(row, schema["function_source_path"])
            source_path = resolve_source_path(source_root, source_relative)
        except Exception as exc:
            record = failure_row(
                row_number,
                row,
                schema,
                "source_resolution",
                exc,
            )
            failures.append(record)
            stage_counts[record["stage"]] += 1
            continue

        try:
            expected_hash = field_value(row, schema["content_sha256"]).lower()
            if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                raise ValueError(f"invalid manifest SHA-256: {expected_hash!r}")
            actual_hash = sha256_file(source_path)
            if actual_hash != expected_hash:
                raise ValueError(
                    "function source SHA-256 mismatch: "
                    f"manifest={expected_hash} actual={actual_hash}"
                )
            hash_verified += 1
        except Exception as exc:
            record = failure_row(
                row_number,
                row,
                schema,
                "source_hash",
                exc,
            )
            failures.append(record)
            stage_counts[record["stage"]] += 1
            continue

        try:
            normalized_source = normalize_function_source(
                read_python_source(source_path)
            )
        except Exception as exc:
            record = failure_row(
                row_number,
                row,
                schema,
                "source_read_normalize",
                exc,
            )
            failures.append(record)
            stage_counts[record["stage"]] += 1
            continue

        qualified_name = field_value(row, schema["qualified_function_name"])
        expected_name = (
            field_value(row, schema["function_name"])
            or leaf_function_name(qualified_name)
        )

        try:
            module = ast.parse(normalized_source)
            functions = [
                node
                for node in module.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if len(functions) != 1:
                raise ValueError(
                    "runtime AST expected exactly one top-level function; "
                    f"found {len(functions)}"
                )
            if functions[0].name != expected_name:
                raise ValueError(
                    "runtime AST function name mismatch: "
                    f"manifest={expected_name!r} source={functions[0].name!r}"
                )
        except Exception as exc:
            record = failure_row(
                row_number,
                row,
                schema,
                "runtime_python_ast",
                exc,
            )
            record["runtime_python"] = sys.version
            runtime_ast_failures.append(record)
            runtime_ast_error_types[type(exc).__name__] += 1

        try:
            source_bytes = normalized_source.encode("utf-8")
            tree = parser.parse(source_bytes)
            if tree_has_error(tree.root_node):
                raise SyntaxError("tree-sitter parse tree contains ERROR nodes")
            blocks = extract_blocks(normalized_source, parser)
            if len(blocks) != 1:
                raise ValueError(
                    "tree-sitter expected exactly one top-level block; "
                    f"found {len(blocks)}"
                )
            block = blocks[0]
            if str(block.get("kind", "")) != "function_definition":
                raise ValueError(
                    "tree-sitter resolved a non-function block: "
                    f"{block.get('kind')!r}"
                )
            actual_name = str(block.get("name", ""))
            if actual_name != expected_name:
                raise ValueError(
                    "tree-sitter function name mismatch: "
                    f"manifest={expected_name!r} source={actual_name!r}"
                )
            tree_sitter_valid += 1
        except Exception as exc:
            record = failure_row(
                row_number,
                row,
                schema,
                "tree_sitter_validation",
                exc,
            )
            failures.append(record)
            stage_counts[record["stage"]] += 1

        if index % args.progress_every == 0 or index == len(selected_rows):
            print(
                "Detector-input preflight: "
                f"{index}/{len(selected_rows)}; "
                f"required_failures={len(failures)}; "
                f"runtime_ast_failures={len(runtime_ast_failures)}"
            )

    full_run = args.max_events == 0
    expected_rows_pass = (
        args.expected_manifest_rows == 0
        or manifest_rows == args.expected_manifest_rows
    )
    required_failures = len(failures)
    runtime_ast_failure_count = len(runtime_ast_failures)

    checks = [
        {
            "check": "manifest_row_count_expected",
            "passed": int(expected_rows_pass),
            "observed": manifest_rows,
            "expected": args.expected_manifest_rows or "disabled",
        },
        {
            "check": "selected_rows_positive",
            "passed": int(len(selected_rows) > 0),
            "observed": len(selected_rows),
            "expected": ">0",
        },
        {
            "check": "duplicate_event_ids_zero",
            "passed": int(duplicate_event_ids == 0),
            "observed": duplicate_event_ids,
            "expected": 0,
        },
        {
            "check": "required_detector_input_failures_zero",
            "passed": int(required_failures == 0),
            "observed": required_failures,
            "expected": 0,
        },
        {
            "check": "hash_verified_for_all_selected_rows",
            "passed": int(hash_verified == len(selected_rows)),
            "observed": hash_verified,
            "expected": len(selected_rows),
        },
        {
            "check": "tree_sitter_valid_for_all_selected_rows",
            "passed": int(tree_sitter_valid == len(selected_rows)),
            "observed": tree_sitter_valid,
            "expected": len(selected_rows),
        },
        {
            "check": "dataset_sources_supported",
            "passed": int(set(dataset_counts) <= {"treatment", "control"}),
            "observed": ";".join(
                f"{key}:{value}" for key, value in sorted(dataset_counts.items())
            ),
            "expected": "treatment/control",
        },
        {
            "check": "full_run_completed",
            "passed": int(full_run),
            "observed": int(full_run),
            "expected": 1,
        },
    ]

    checks_passed = sum(int(row["passed"]) for row in checks)
    checks_failed = len(checks) - checks_passed
    required_ready = checks_failed == 0

    if not required_ready:
        status = "FAIL"
        recommendation = "FIX_INPUT_OR_TREE_SITTER_BEFORE_FRESH_INFERENCE"
    elif runtime_ast_failure_count:
        status = "PASS_WITH_RUNTIME_AST_INCOMPATIBILITY"
        recommendation = (
            "UPDATE_ANALYZER_TO_REMOVE_OLD_RUNTIME_AST_GATE_"
            "OR_RUN_WITH_A_PYTHON_3_12_DETECTOR_ENVIRONMENT"
        )
    else:
        status = "PASS"
        recommendation = "READY_FOR_FRESH_AGC_INFERENCE"

    output_root.mkdir(parents=True, exist_ok=True)
    failure_path = output_root / "detector_input_compatibility_failures.csv"
    runtime_ast_path = output_root / "detector_input_runtime_ast_failures.csv"
    checks_path = output_root / "detector_input_compatibility_checks.csv"
    summary_path = output_root / "detector_input_compatibility_summary.json"

    atomic_write_csv(failure_path, failures, FAILURE_FIELDS)
    atomic_write_csv(runtime_ast_path, runtime_ast_failures, RUNTIME_AST_FIELDS)
    atomic_write_csv(
        checks_path,
        checks,
        ["check", "passed", "observed", "expected"],
    )

    summary = {
        "status": status,
        "recommendation": recommendation,
        "completed_at_utc": utc_now(),
        "runtime_python": sys.version,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "function_source_root": str(source_root),
        "tree_sitter_library": str(tree_sitter_lib),
        "expected_manifest_rows": args.expected_manifest_rows,
        "manifest_rows": manifest_rows,
        "selected_rows": len(selected_rows),
        "full_run": full_run,
        "dataset_source_counts": dict(sorted(dataset_counts.items())),
        "duplicate_event_ids": duplicate_event_ids,
        "source_hashes_verified": hash_verified,
        "tree_sitter_valid_events": tree_sitter_valid,
        "required_detector_input_failures": required_failures,
        "required_failure_stage_counts": dict(sorted(stage_counts.items())),
        "runtime_python_ast_failures": runtime_ast_failure_count,
        "runtime_python_ast_error_types": dict(
            sorted(runtime_ast_error_types.items())
        ),
        "analyzer_v1_runtime_ast_compatible": runtime_ast_failure_count == 0,
        "checks_total": len(checks),
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "outputs": {
            "required_failures": str(failure_path),
            "runtime_ast_failures": str(runtime_ast_path),
            "checks": str(checks_path),
            "summary": str(summary_path),
        },
    }
    atomic_write_json(summary_path, summary)

    print("=" * 76)
    print("AGC commit-function detector-input compatibility")
    print(f"Status:                         {status}")
    print(f"Recommendation:                 {recommendation}")
    print(f"Checks passed:                  {checks_passed}/{len(checks)}")
    print(f"Manifest rows:                  {manifest_rows}")
    print(f"Selected rows:                  {len(selected_rows)}")
    print(f"Source hashes verified:         {hash_verified}")
    print(f"Tree-sitter valid events:       {tree_sitter_valid}")
    print(f"Required detector failures:     {required_failures}")
    print(f"Runtime Python AST failures:    {runtime_ast_failure_count}")
    print(f"Summary:                        {summary_path}")
    print("=" * 76)

    if not required_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
