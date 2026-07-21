#!/usr/bin/env python3
"""
Diagnose and score commit-function events whose tree-sitter trees contain errors.

This targeted diagnostic reads the events flagged by the detector-input preflight
because the current tree-sitter grammar produced ERROR or MISSING nodes. It then
runs the existing validated detector pipeline through feature construction and
classifier prediction without treating tree-sitter recovery nodes as an automatic
fatal condition.

The script does not retrain the model, reuse prediction or embedding caches, or
resume from previous inference checkpoints. The existing trained classifier,
tree-sitter library, AST helper, and CodeT5+ embedder are loaded once and reused
for all selected events.

Primary decision rule
---------------------
A tree-sitter ERROR node is recorded as a diagnostic warning. An event is accepted
only when all required detector operations succeed:

1. The manifest row and source artifact are found.
2. The artifact SHA-256 matches the manifest.
3. tree-sitter extracts exactly one function block.
4. The extracted function name matches the manifest.
5. The extracted block covers the complete normalized artifact.
6. The AST sequence is nonempty.
7. The feature vector is nonempty and finite.
8. The classifier returns the expected score mode and a valid prediction.

Expected use
------------
Run this script in the aidetector Conda environment from the ai_detector root.
The default input is the 42 tree-sitter preflight failures produced for the
Python 3.12 commit-function extraction.

Usage
-----
  python src/app/py/diagnose_agc_tree_sitter_error_events.py --self-test
  python src/app/py/diagnose_agc_tree_sitter_error_events.py
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
import platform
import re
import sys
import tempfile
import textwrap
import time
import tokenize
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

SCRIPT_PATH = Path(__file__).resolve()
APP_DIR = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
WORKSPACE_ROOT = REPO_ROOT.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import agc_detector as agc_detector_module  # type: ignore

from agc_detector import (  # type: ignore
    build_feature_vector,
    extract_blocks,
    generate_ast_sequence,
    load_embedder,
    load_parser_and_F,
    pick_classifier_from_pickle,
    predict_one,
    strip_block_markers,
)

DEFAULT_EXPERIMENT = "codellama-7b_4500_complexity_stratified_maxlen2048"
DEFAULT_REPRESENTATION = "ast"
DEFAULT_MAX_LEN = 2048
DEFAULT_EXPECTED_MODEL_KEY = "codesearchnet_codellama-7b_python_merged_4500ast_"
DEFAULT_EXPECTED_SCORE_MODE = "decision"
DEFAULT_EXPECTED_EVENTS = 42
DEFAULT_EXPECTED_MANIFEST_ROWS = 450_548

DEFAULT_MODEL_PICKLE = (
    REPO_ROOT
    / "src/ml_embeddings/data_codesearchnet/models"
    / DEFAULT_EXPERIMENT
    / (
        "tuned_models_codesearchnet_codellama-7b_"
        "4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"
    )
)
DEFAULT_TREE_SITTER_LIB = (
    REPO_ROOT / "src/code-analyzer-tree-sitter/build/my-languages.so"
)
DEFAULT_AST_HELPER_DIR = REPO_ROOT / "src/code-analyzer-tree-sitter"
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
DEFAULT_PREFLIGHT_FAILURES = (
    WORKSPACE_ROOT
    / "ai_code_complexity_study_python/python_commit_function_detect"
    / "input_compatibility"
    / "codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast"
    / "strict/py312/detector_input_compatibility_failures.csv"
)
DEFAULT_OUTPUT_ROOT = (
    WORKSPACE_ROOT
    / "ai_code_complexity_study_python/python_commit_function_detect"
    / "tree_sitter_error_event_diagnostic"
    / "codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast"
    / "strict/py312"
)

DIAGNOSTIC_FIELDS = [
    "manifest_row_number",
    "function_event_id",
    "dataset_source",
    "repo_name",
    "time",
    "commit",
    "parent_commit",
    "relative_path",
    "qualified_function_name",
    "function_name",
    "function_kind",
    "change_type",
    "function_source_path",
    "content_sha256",
    "source_hash_verified",
    "normalized_content_sha256",
    "runtime_python",
    "runtime_ast_compatible",
    "runtime_ast_error_type",
    "runtime_ast_error_message",
    "tree_sitter_has_error",
    "tree_sitter_error_node_count",
    "tree_sitter_missing_node_count",
    "tree_sitter_blocks_found",
    "tree_sitter_block_kind",
    "tree_sitter_block_name",
    "tree_sitter_name_matches_manifest",
    "tree_sitter_block_covers_full_source",
    "tree_sitter_block_start_line",
    "tree_sitter_block_end_line",
    "ast_sequence_character_count",
    "ast_sequence_token_count",
    "feature_shape",
    "feature_size",
    "feature_all_finite",
    "analysis_status",
    "pred_int",
    "pred_label",
    "predicted_agc",
    "predicted_hwc",
    "human_score",
    "agc_score",
    "score_mode",
    "model_key",
    "inference_seconds",
    "failure_stage",
    "error_type",
    "error_message",
]

NODE_DETAIL_FIELDS = [
    "function_event_id",
    "dataset_source",
    "repo_name",
    "time",
    "relative_path",
    "qualified_function_name",
    "node_category",
    "node_type",
    "start_line",
    "start_column",
    "end_line",
    "end_column",
    "start_byte",
    "end_byte",
    "text_excerpt",
]

PREDICTION_FIELDS = [
    "function_event_id",
    "dataset_source",
    "repo_name",
    "time",
    "commit",
    "relative_path",
    "qualified_function_name",
    "change_type",
    "tree_sitter_has_error",
    "tree_sitter_error_node_count",
    "tree_sitter_missing_node_count",
    "runtime_ast_compatible",
    "pred_int",
    "pred_label",
    "predicted_agc",
    "predicted_hwc",
    "human_score",
    "agc_score",
    "score_mode",
    "model_key",
    "inference_seconds",
]

FAILURE_FIELDS = [
    "function_event_id",
    "dataset_source",
    "repo_name",
    "time",
    "commit",
    "relative_path",
    "qualified_function_name",
    "function_source_path",
    "failure_stage",
    "error_type",
    "error_message",
]

CHECK_FIELDS = ["check", "required", "passed", "observed", "expected", "note"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--preflight-failures",
        type=Path,
        default=DEFAULT_PREFLIGHT_FAILURES,
    )
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
    parser.add_argument("--model-pickle", type=Path, default=DEFAULT_MODEL_PICKLE)
    parser.add_argument(
        "--expected-model-key",
        default=DEFAULT_EXPECTED_MODEL_KEY,
    )
    parser.add_argument(
        "--expected-score-mode",
        choices=["decision", "proba"],
        default=DEFAULT_EXPECTED_SCORE_MODE,
    )
    parser.add_argument(
        "--representation",
        choices=["ast", "code", "combined"],
        default=DEFAULT_REPRESENTATION,
    )
    parser.add_argument("--max-len", type=int, default=DEFAULT_MAX_LEN)
    parser.add_argument("--threshold", type=float, default=None)
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
    parser.add_argument("--device", default=None)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--expected-events",
        type=int,
        default=DEFAULT_EXPECTED_EVENTS,
        help="Use 0 to disable the exact target-event count check.",
    )
    parser.add_argument(
        "--expected-manifest-rows",
        type=int,
        default=DEFAULT_EXPECTED_MANIFEST_ROWS,
        help="Use 0 to disable the exact manifest row-count check.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Process the first N target events; use 0 for all target events.",
    )
    parser.add_argument("--progress-every", type=int, default=1)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument(
        "--allow-scoring-failures",
        action="store_true",
        help="Write outputs and exit 0 even when actual detector scoring fails.",
    )
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
            f"[ERROR] missing {label}; accepted columns: " + ", ".join(candidates)
        )
    return None


def value(row: Dict[str, str], field: Optional[str]) -> str:
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
    safe_path = validate_relative_python_path(relative_path, "function source path")
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
        raise ValueError(f"function source artifact is not a regular file: {candidate}")
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


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def tree_flag(node: Any, attribute: str) -> bool:
    raw = getattr(node, attribute, False)
    return bool(raw() if callable(raw) else raw)


def point_value(point: Any, index: int) -> int:
    try:
        return int(point[index])
    except Exception:
        return -1


def node_excerpt(node: Any, source_bytes: bytes, limit: int = 500) -> str:
    start_byte = int(getattr(node, "start_byte", 0))
    end_byte = int(getattr(node, "end_byte", start_byte))
    if end_byte > start_byte:
        raw = source_bytes[start_byte:end_byte]
    else:
        left = max(0, start_byte - 100)
        right = min(len(source_bytes), start_byte + 300)
        raw = source_bytes[left:right]
    text = raw.decode("utf-8", errors="replace")
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    return text[:limit]


def collect_error_nodes(
    root: Any,
    source_bytes: bytes,
    event: Dict[str, str],
) -> Tuple[List[Dict[str, Any]], int, int]:
    details: List[Dict[str, Any]] = []
    error_count = 0
    missing_count = 0
    stack = [root]

    while stack:
        node = stack.pop()
        node_type = str(getattr(node, "type", ""))
        is_missing = tree_flag(node, "is_missing")
        is_error = node_type == "ERROR"

        if is_error or is_missing:
            if is_error:
                error_count += 1
            if is_missing:
                missing_count += 1
            start_point = getattr(node, "start_point", (-1, -1))
            end_point = getattr(node, "end_point", (-1, -1))
            details.append(
                {
                    "function_event_id": event["function_event_id"],
                    "dataset_source": event["dataset_source"],
                    "repo_name": event["repo_name"],
                    "time": event["time"],
                    "relative_path": event["relative_path"],
                    "qualified_function_name": event["qualified_function_name"],
                    "node_category": (
                        "ERROR+MISSING"
                        if is_error and is_missing
                        else "ERROR" if is_error else "MISSING"
                    ),
                    "node_type": node_type,
                    "start_line": point_value(start_point, 0) + 1,
                    "start_column": point_value(start_point, 1),
                    "end_line": point_value(end_point, 0) + 1,
                    "end_column": point_value(end_point, 1),
                    "start_byte": int(getattr(node, "start_byte", -1)),
                    "end_byte": int(getattr(node, "end_byte", -1)),
                    "text_excerpt": node_excerpt(node, source_bytes),
                }
            )

        children = list(getattr(node, "children", []) or [])
        stack.extend(reversed(children))

    return details, error_count, missing_count


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


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise SystemExit(f"[ERROR] CSV has no header: {path}")
        rows = list(reader)
    return fieldnames, rows


def resolve_manifest_schema(fieldnames: Sequence[str]) -> Dict[str, Optional[str]]:
    return {
        "function_event_id": first_field(
            fieldnames, ["function_event_id", "event_id"], "function event id"
        ),
        "dataset_source": first_field(
            fieldnames, ["dataset_source"], "dataset source"
        ),
        "repo_name": first_field(fieldnames, ["repo_name"], "repository name"),
        "time": first_field(fieldnames, ["time", "month"], "repo-month"),
        "commit": first_field(
            fieldnames, ["commit", "scan_current_commit"], "current commit"
        ),
        "parent_commit": first_field(
            fieldnames,
            ["parent_commit", "scan_parent_commit"],
            "parent commit",
        ),
        "relative_path": first_field(
            fieldnames, ["relative_path"], "repository file path"
        ),
        "qualified_function_name": first_field(
            fieldnames,
            ["qualified_function_name", "qualified_name"],
            "qualified function name",
        ),
        "function_name": first_field(
            fieldnames, ["function_name"], "function name", required=False
        ),
        "function_kind": first_field(
            fieldnames, ["function_kind"], "function kind", required=False
        ),
        "change_type": first_field(fieldnames, ["change_type"], "change type"),
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


def canonical_manifest_event(
    row: Dict[str, str],
    schema: Dict[str, Optional[str]],
) -> Dict[str, str]:
    qualified_name = value(row, schema["qualified_function_name"])
    function_name = value(row, schema["function_name"]) or leaf_function_name(
        qualified_name
    )
    return {
        "manifest_row_number": value(row, "manifest_row_number") or "",
        "function_event_id": value(row, schema["function_event_id"]),
        "dataset_source": value(row, schema["dataset_source"]).lower(),
        "repo_name": value(row, schema["repo_name"]),
        "time": value(row, schema["time"]),
        "commit": value(row, schema["commit"]).lower(),
        "parent_commit": value(row, schema["parent_commit"]).lower(),
        "relative_path": value(row, schema["relative_path"]),
        "qualified_function_name": qualified_name,
        "function_name": function_name,
        "function_kind": value(row, schema["function_kind"]),
        "change_type": value(row, schema["change_type"]).lower(),
        "function_source_path": value(row, schema["function_source_path"]),
        "content_sha256": value(row, schema["content_sha256"]).lower(),
    }


def failure_payload(
    event: Dict[str, str],
    stage: str,
    exc: BaseException,
) -> Dict[str, Any]:
    return {
        "function_event_id": event.get("function_event_id", ""),
        "dataset_source": event.get("dataset_source", ""),
        "repo_name": event.get("repo_name", ""),
        "time": event.get("time", ""),
        "commit": event.get("commit", ""),
        "relative_path": event.get("relative_path", ""),
        "qualified_function_name": event.get("qualified_function_name", ""),
        "function_source_path": event.get("function_source_path", ""),
        "failure_stage": stage,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }


def empty_diagnostic(event: Dict[str, str]) -> Dict[str, Any]:
    row: Dict[str, Any] = {field: "" for field in DIAGNOSTIC_FIELDS}
    row.update(event)
    row.update(
        {
            "source_hash_verified": 0,
            "runtime_python": platform.python_version(),
            "runtime_ast_compatible": 0,
            "tree_sitter_has_error": 0,
            "tree_sitter_error_node_count": 0,
            "tree_sitter_missing_node_count": 0,
            "tree_sitter_blocks_found": 0,
            "tree_sitter_name_matches_manifest": 0,
            "tree_sitter_block_covers_full_source": 0,
            "feature_all_finite": 0,
            "predicted_agc": "",
            "predicted_hwc": "",
            "analysis_status": "pending",
        }
    )
    return row


def human_score_to_agc_score(human_score: float, score_mode: str) -> float:
    if score_mode == "decision":
        return -human_score
    if score_mode == "proba":
        return 1.0 - human_score
    raise ValueError(f"unsupported score mode: {score_mode!r}")


def model_sha256(path: Path) -> str:
    return sha256_file(path)


def build_summary(
    args: argparse.Namespace,
    paths: Dict[str, Path],
    target_rows: int,
    manifest_rows: int,
    diagnostics: Sequence[Dict[str, Any]],
    node_details: Sequence[Dict[str, Any]],
    model_key: str,
    model_hash: str,
    device: str,
    completed: bool,
) -> Dict[str, Any]:
    scored = [row for row in diagnostics if row.get("analysis_status") == "ok"]
    failed = [row for row in diagnostics if row.get("analysis_status") == "failed"]
    agc = sum(int(row["predicted_agc"]) for row in scored)
    hwc = sum(int(row["predicted_hwc"]) for row in scored)
    runtime_ast_failures = sum(
        int(row.get("runtime_ast_compatible", 0)) == 0 for row in diagnostics
    )
    root_error_events = sum(
        int(row.get("tree_sitter_has_error", 0)) == 1 for row in diagnostics
    )
    error_nodes = sum(int(row.get("tree_sitter_error_node_count", 0)) for row in diagnostics)
    missing_nodes = sum(
        int(row.get("tree_sitter_missing_node_count", 0)) for row in diagnostics
    )
    feature_shapes = sorted(
        {
            str(row.get("feature_shape", ""))
            for row in scored
            if str(row.get("feature_shape", ""))
        }
    )
    score_modes = sorted(
        {
            str(row.get("score_mode", ""))
            for row in scored
            if str(row.get("score_mode", ""))
        }
    )
    status = "PASS" if completed and not failed and len(scored) == target_rows else "FAIL"
    recommendation = (
        "PROCEED_TO_ANALYZER_V2_AND_166_EVENT_EDGE_PILOT"
        if status == "PASS"
        else "REVIEW_ACTUAL_DETECTOR_FAILURES_BEFORE_EDGE_PILOT"
    )

    return {
        "status": status,
        "recommendation": recommendation,
        "completed": completed,
        "started_or_updated_at_utc": utc_now(),
        "runtime_python": sys.version,
        "platform": platform.platform(),
        "experiment": DEFAULT_EXPERIMENT,
        "representation": args.representation,
        "max_len": args.max_len,
        "threshold": args.threshold,
        "device": device,
        "model_pickle": str(args.model_pickle),
        "model_sha256": model_hash,
        "model_key": model_key,
        "expected_model_key": args.expected_model_key,
        "expected_score_mode": args.expected_score_mode,
        "manifest_rows": manifest_rows,
        "target_events": target_rows,
        "events_processed": len(diagnostics),
        "events_scored": len(scored),
        "events_failed": len(failed),
        "runtime_ast_failures": runtime_ast_failures,
        "tree_sitter_root_error_events": root_error_events,
        "tree_sitter_error_nodes": error_nodes,
        "tree_sitter_missing_nodes": missing_nodes,
        "node_detail_rows": len(node_details),
        "feature_shapes": feature_shapes,
        "score_modes": score_modes,
        "agc_events": agc,
        "hwc_events": hwc,
        "prediction_arithmetic_pass": len(scored) == agc + hwc,
        "dataset_source_counts": dict(
            sorted(Counter(str(row.get("dataset_source", "")) for row in diagnostics).items())
        ),
        "repository_counts": dict(
            Counter(str(row.get("repo_name", "")) for row in diagnostics).most_common()
        ),
        "failure_stage_counts": dict(
            sorted(
                Counter(
                    str(row.get("failure_stage", ""))
                    for row in failed
                    if str(row.get("failure_stage", ""))
                ).items()
            )
        ),
        "inference_policy": {
            "fresh_inference": True,
            "prediction_cache_used": False,
            "embedding_cache_used": False,
            "checkpoint_resume_used": False,
            "model_retrained": False,
            "tree_sitter_error_is_automatic_failure": False,
        },
        "outputs": {key: str(path) for key, path in paths.items()},
    }


def build_checks(
    args: argparse.Namespace,
    target_rows: int,
    manifest_rows: int,
    diagnostics: Sequence[Dict[str, Any]],
    model_key: str,
) -> List[Dict[str, Any]]:
    scored = [row for row in diagnostics if row.get("analysis_status") == "ok"]
    failed = [row for row in diagnostics if row.get("analysis_status") == "failed"]
    agc = sum(int(row["predicted_agc"]) for row in scored)
    hwc = sum(int(row["predicted_hwc"]) for row in scored)
    feature_shapes = {
        str(row.get("feature_shape", ""))
        for row in scored
        if str(row.get("feature_shape", ""))
    }

    def check(
        name: str,
        required: bool,
        passed: bool,
        observed: Any,
        expected: Any,
        note: str = "",
    ) -> Dict[str, Any]:
        return {
            "check": name,
            "required": int(required),
            "passed": int(bool(passed)),
            "observed": observed,
            "expected": expected,
            "note": note,
        }

    expected_target_pass = args.expected_events == 0 or target_rows == args.expected_events
    expected_manifest_pass = (
        args.expected_manifest_rows == 0
        or manifest_rows == args.expected_manifest_rows
    )

    return [
        check(
            "target_event_count_expected",
            True,
            expected_target_pass,
            target_rows,
            args.expected_events or "disabled",
        ),
        check(
            "manifest_row_count_expected",
            True,
            expected_manifest_pass,
            manifest_rows,
            args.expected_manifest_rows or "disabled",
        ),
        check(
            "all_events_processed",
            True,
            len(diagnostics) == target_rows,
            len(diagnostics),
            target_rows,
        ),
        check(
            "source_hashes_verified",
            True,
            all(int(row.get("source_hash_verified", 0)) == 1 for row in diagnostics),
            sum(int(row.get("source_hash_verified", 0)) for row in diagnostics),
            target_rows,
        ),
        check(
            "runtime_ast_failures_zero",
            False,
            all(int(row.get("runtime_ast_compatible", 0)) == 1 for row in diagnostics),
            sum(int(row.get("runtime_ast_compatible", 0)) == 0 for row in diagnostics),
            0,
            "Diagnostic only; runtime AST is not an inference gate.",
        ),
        check(
            "tree_sitter_root_errors_reproduced",
            True,
            all(int(row.get("tree_sitter_has_error", 0)) == 1 for row in diagnostics),
            sum(int(row.get("tree_sitter_has_error", 0)) for row in diagnostics),
            target_rows,
        ),
        check(
            "single_function_block_all_events",
            True,
            all(int(row.get("tree_sitter_blocks_found", 0)) == 1 for row in diagnostics),
            sum(int(row.get("tree_sitter_blocks_found", 0)) == 1 for row in diagnostics),
            target_rows,
        ),
        check(
            "function_names_match_all_events",
            True,
            all(
                int(row.get("tree_sitter_name_matches_manifest", 0)) == 1
                for row in diagnostics
            ),
            sum(
                int(row.get("tree_sitter_name_matches_manifest", 0))
                for row in diagnostics
            ),
            target_rows,
        ),
        check(
            "blocks_cover_full_source_all_events",
            True,
            all(
                int(row.get("tree_sitter_block_covers_full_source", 0)) == 1
                for row in diagnostics
            ),
            sum(
                int(row.get("tree_sitter_block_covers_full_source", 0))
                for row in diagnostics
            ),
            target_rows,
        ),
        check(
            "feature_vectors_finite_all_scored",
            True,
            all(int(row.get("feature_all_finite", 0)) == 1 for row in scored),
            sum(int(row.get("feature_all_finite", 0)) for row in scored),
            len(scored),
        ),
        check(
            "feature_dimensions_consistent",
            True,
            len(feature_shapes) == 1 and len(scored) > 0,
            ";".join(sorted(feature_shapes)),
            "one nonempty shape",
        ),
        check(
            "model_key_expected",
            True,
            model_key == args.expected_model_key,
            model_key,
            args.expected_model_key,
        ),
        check(
            "score_mode_expected_all_scored",
            True,
            all(row.get("score_mode") == args.expected_score_mode for row in scored),
            ";".join(sorted({str(row.get("score_mode", "")) for row in scored})),
            args.expected_score_mode,
        ),
        check(
            "actual_scoring_failures_zero",
            True,
            len(failed) == 0,
            len(failed),
            0,
        ),
        check(
            "prediction_arithmetic",
            True,
            len(scored) == agc + hwc,
            f"scored={len(scored)} agc={agc} hwc={hwc}",
            "scored=agc+hwc",
        ),
    ]


def write_outputs(
    paths: Dict[str, Path],
    diagnostics: Sequence[Dict[str, Any]],
    node_details: Sequence[Dict[str, Any]],
    summary: Dict[str, Any],
    checks: Sequence[Dict[str, Any]],
) -> None:
    predictions = [row for row in diagnostics if row.get("analysis_status") == "ok"]
    failures = [row for row in diagnostics if row.get("analysis_status") == "failed"]

    atomic_write_csv(paths["diagnostic"], diagnostics, DIAGNOSTIC_FIELDS)
    atomic_write_csv(paths["node_details"], node_details, NODE_DETAIL_FIELDS)
    atomic_write_csv(paths["predictions"], predictions, PREDICTION_FIELDS)
    atomic_write_csv(paths["failures"], failures, FAILURE_FIELDS)
    atomic_write_json(paths["summary"], summary)
    atomic_write_csv(paths["checks"], checks, CHECK_FIELDS)


def run_self_test(tree_sitter_lib: Path, ast_helper_dir: Path) -> None:
    parser, _ = load_parser_and_F(str(tree_sitter_lib), str(ast_helper_dir))

    valid = "@staticmethod\ndef sample(value: int) -> int:\n    return value + 1\n"
    valid_tree = parser.parse(valid.encode("utf-8"))
    if tree_flag(valid_tree.root_node, "has_error"):
        raise SystemExit("Self-test: FAIL (valid source has tree-sitter error)")
    blocks = extract_blocks(valid, parser)
    if len(blocks) != 1 or blocks[0].get("name") != "sample":
        raise SystemExit("Self-test: FAIL (valid block extraction)")

    invalid = "def broken(value:\n    return value\n"
    invalid_bytes = invalid.encode("utf-8")
    invalid_tree = parser.parse(invalid_bytes)
    if not tree_flag(invalid_tree.root_node, "has_error"):
        raise SystemExit("Self-test: FAIL (invalid source lacks recovery error)")
    event = {
        "function_event_id": "self-test",
        "dataset_source": "control",
        "repo_name": "example/repo",
        "time": "2025-01",
        "relative_path": "sample.py",
        "qualified_function_name": "broken",
    }
    details, error_count, missing_count = collect_error_nodes(
        invalid_tree.root_node,
        invalid_bytes,
        event,
    )
    if not details or error_count + missing_count <= 0:
        raise SystemExit("Self-test: FAIL (error-node collection)")

    print("Self-test: PASS")


def main() -> None:
    args = parse_args()
    if args.max_len <= 0:
        raise SystemExit("[ERROR] --max-len must be positive")
    if args.expected_events < 0:
        raise SystemExit("[ERROR] --expected-events cannot be negative")
    if args.expected_manifest_rows < 0:
        raise SystemExit("[ERROR] --expected-manifest-rows cannot be negative")
    if args.max_events < 0:
        raise SystemExit("[ERROR] --max-events cannot be negative")
    if args.progress_every <= 0:
        raise SystemExit("[ERROR] --progress-every must be positive")
    if args.checkpoint_every <= 0:
        raise SystemExit("[ERROR] --checkpoint-every must be positive")

    tree_sitter_lib = require_file(args.tree_sitter_lib, "tree-sitter library")
    ast_helper_dir = require_dir(args.ast_helper_dir, "AST helper directory")

    if args.self_test:
        run_self_test(tree_sitter_lib, ast_helper_dir)
        return

    preflight_failures = require_file(
        args.preflight_failures,
        "preflight failure CSV",
    )
    manifest_path = require_file(
        args.function_event_manifest,
        "function-event manifest",
    )
    source_root = require_dir(args.function_source_root, "function source root")
    model_pickle = require_file(args.model_pickle, "classifier pickle")
    output_root = args.output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    args.preflight_failures = preflight_failures
    args.function_event_manifest = manifest_path
    args.function_source_root = source_root
    args.model_pickle = model_pickle
    args.tree_sitter_lib = tree_sitter_lib
    args.ast_helper_dir = ast_helper_dir
    args.output_root = output_root

    paths = {
        "diagnostic": output_root / "tree_sitter_error_event_diagnostic.csv",
        "node_details": output_root / "tree_sitter_error_node_details.csv",
        "predictions": output_root / "tree_sitter_error_event_predictions.csv",
        "failures": output_root / "tree_sitter_error_event_failures.csv",
        "summary": output_root / "tree_sitter_error_event_summary.json",
        "checks": output_root / "tree_sitter_error_event_checks.csv",
    }

    failure_fields, preflight_rows = read_csv(preflight_failures)
    required_preflight_fields = {
        "function_event_id",
        "stage",
        "error_message",
    }
    missing_preflight_fields = sorted(required_preflight_fields - set(failure_fields))
    if missing_preflight_fields:
        raise SystemExit(
            "[ERROR] preflight failure CSV is missing columns: "
            + ", ".join(missing_preflight_fields)
        )

    target_rows = [
        row
        for row in preflight_rows
        if str(row.get("stage", "")).strip() == "tree_sitter_validation"
    ]
    if len(target_rows) != len(preflight_rows):
        other_stages = Counter(str(row.get("stage", "")) for row in preflight_rows)
        raise SystemExit(
            "[ERROR] preflight failure CSV contains non-tree-sitter stages: "
            + json.dumps(dict(other_stages), sort_keys=True)
        )

    target_ids = [str(row.get("function_event_id", "")).strip() for row in target_rows]
    if any(not event_id for event_id in target_ids):
        raise SystemExit("[ERROR] preflight failure row has empty function_event_id")
    if len(set(target_ids)) != len(target_ids):
        duplicates = [
            event_id
            for event_id, count in Counter(target_ids).items()
            if count > 1
        ]
        raise SystemExit(
            "[ERROR] duplicate target function_event_id values: "
            + ", ".join(sorted(duplicates))
        )

    manifest_fields, manifest_rows_raw = read_csv(manifest_path)
    manifest_schema = resolve_manifest_schema(manifest_fields)
    manifest_rows = len(manifest_rows_raw)
    manifest_by_id: Dict[str, Dict[str, str]] = {}
    for row in manifest_rows_raw:
        event = canonical_manifest_event(row, manifest_schema)
        event_id = event["function_event_id"]
        if event_id in manifest_by_id:
            raise SystemExit(f"[ERROR] duplicate manifest function_event_id: {event_id}")
        manifest_by_id[event_id] = event

    missing_target_ids = [event_id for event_id in target_ids if event_id not in manifest_by_id]
    if missing_target_ids:
        raise SystemExit(
            f"[ERROR] {len(missing_target_ids)} target events are missing from manifest; "
            f"first={missing_target_ids[0]}"
        )

    selected_ids = target_ids[: args.max_events] if args.max_events else target_ids
    events = [manifest_by_id[event_id] for event_id in selected_ids]

    print("=" * 76)
    print("Diagnose AGC tree-sitter ERROR-node events")
    print(f"Runtime Python:        {platform.python_version()}")
    print(f"Preflight failures:    {preflight_failures}")
    print(f"Manifest:              {manifest_path}")
    print(f"Manifest rows:         {manifest_rows}")
    print(f"Target events:         {len(target_rows)}")
    print(f"Selected events:       {len(events)}")
    print(f"Function source root:  {source_root}")
    print(f"Tree-sitter library:   {tree_sitter_lib}")
    print(f"Model pickle:          {model_pickle}")
    print(f"Expected model key:    {args.expected_model_key}")
    print(f"Expected score mode:   {args.expected_score_mode}")
    print(f"Representation:        {args.representation}")
    print(f"Max length:            {args.max_len}")
    print(f"Device:                {args.device or '<auto>'}")
    print(f"Output root:           {output_root}")
    print("=" * 76)

    agc_detector_module.MAX_LEN = args.max_len

    import torch

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    parser, ast_function = load_parser_and_F(
        str(tree_sitter_lib),
        str(ast_helper_dir),
    )
    tokenizer, embedding_model = load_embedder(device)
    classifier, selected_model_key = pick_classifier_from_pickle(
        str(model_pickle),
        f"{args.representation}_",
    )
    selected_model_hash = model_sha256(model_pickle)

    if selected_model_key != args.expected_model_key:
        raise SystemExit(
            "[ERROR] unexpected classifier key\n"
            f"        selected: {selected_model_key}\n"
            f"        expected: {args.expected_model_key}"
        )

    diagnostics: List[Dict[str, Any]] = []
    node_details: List[Dict[str, Any]] = []

    for index, event in enumerate(events, start=1):
        result = empty_diagnostic(event)
        started = time.perf_counter()
        failure_stage = ""

        try:
            failure_stage = "source_resolution"
            source_path = resolve_source_path(
                source_root,
                event["function_source_path"],
            )

            failure_stage = "source_hash"
            expected_hash = event["content_sha256"]
            if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                raise ValueError(f"invalid manifest SHA-256: {expected_hash!r}")
            actual_hash = sha256_file(source_path)
            if actual_hash != expected_hash:
                raise ValueError(
                    "function source SHA-256 mismatch: "
                    f"manifest={expected_hash} actual={actual_hash}"
                )
            result["source_hash_verified"] = 1

            failure_stage = "source_read_normalize"
            normalized_source = normalize_function_source(
                read_python_source(source_path)
            )
            normalized_bytes = normalized_source.encode("utf-8")
            result["normalized_content_sha256"] = sha256_bytes(normalized_bytes)

            try:
                module = ast.parse(normalized_source)
                function_nodes = [
                    node
                    for node in module.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                if len(function_nodes) != 1:
                    raise ValueError(
                        "runtime AST expected exactly one top-level function; "
                        f"found {len(function_nodes)}"
                    )
                if function_nodes[0].name != event["function_name"]:
                    raise ValueError(
                        "runtime AST function name mismatch: "
                        f"manifest={event['function_name']!r} "
                        f"source={function_nodes[0].name!r}"
                    )
                result["runtime_ast_compatible"] = 1
            except Exception as runtime_exc:
                result["runtime_ast_compatible"] = 0
                result["runtime_ast_error_type"] = type(runtime_exc).__name__
                result["runtime_ast_error_message"] = str(runtime_exc)

            failure_stage = "tree_sitter_parse"
            tree = parser.parse(normalized_bytes)
            root = tree.root_node
            result["tree_sitter_has_error"] = int(tree_flag(root, "has_error"))
            event_node_details, error_count, missing_count = collect_error_nodes(
                root,
                normalized_bytes,
                event,
            )
            node_details.extend(event_node_details)
            result["tree_sitter_error_node_count"] = error_count
            result["tree_sitter_missing_node_count"] = missing_count

            if not result["tree_sitter_has_error"]:
                raise ValueError(
                    "preflight inconsistency: tree-sitter no longer reports ERROR nodes"
                )

            failure_stage = "tree_sitter_block_extraction"
            blocks = extract_blocks(normalized_source, parser)
            result["tree_sitter_blocks_found"] = len(blocks)
            if len(blocks) != 1:
                raise ValueError(
                    "tree-sitter detector input must contain exactly one block; "
                    f"found {len(blocks)}"
                )
            block = blocks[0]
            result["tree_sitter_block_kind"] = str(block.get("kind", ""))
            result["tree_sitter_block_name"] = str(block.get("name", ""))
            result["tree_sitter_block_start_line"] = block.get("start_line", "")
            result["tree_sitter_block_end_line"] = block.get("end_line", "")

            if result["tree_sitter_block_kind"] != "function_definition":
                raise ValueError(
                    "tree-sitter resolved a non-function block: "
                    f"{result['tree_sitter_block_kind']!r}"
                )

            name_match = int(
                result["tree_sitter_block_name"] == event["function_name"]
            )
            result["tree_sitter_name_matches_manifest"] = name_match
            if not name_match:
                raise ValueError(
                    "tree-sitter function name mismatch: "
                    f"manifest={event['function_name']!r} "
                    f"source={result['tree_sitter_block_name']!r}"
                )

            block_code = str(block.get("code", ""))
            full_source_match = int(
                block_code.strip() == normalized_source.strip()
            )
            result["tree_sitter_block_covers_full_source"] = full_source_match
            if not full_source_match:
                raise ValueError(
                    "tree-sitter extracted block does not cover the complete artifact"
                )

            failure_stage = "ast_sequence_generation"
            ast_sequence = generate_ast_sequence(
                block_code,
                parser,
                ast_function,
            )
            result["ast_sequence_character_count"] = len(ast_sequence)
            result["ast_sequence_token_count"] = len(ast_sequence.split())
            if not ast_sequence.strip():
                raise ValueError("AST sequence is empty")

            failure_stage = "feature_vector_generation"
            vector = build_feature_vector(
                block_code,
                args.representation,
                parser,
                ast_function,
                tokenizer,
                embedding_model,
                device,
            )
            array = np.asarray(vector)
            result["feature_shape"] = "x".join(str(part) for part in array.shape)
            result["feature_size"] = int(array.size)
            result["feature_all_finite"] = int(
                array.size > 0 and bool(np.isfinite(array).all())
            )
            if array.size == 0:
                raise ValueError("feature vector is empty")
            if not bool(np.isfinite(array).all()):
                raise ValueError("feature vector contains NaN or infinite values")

            failure_stage = "classifier_prediction"
            pred_int, score, score_mode = predict_one(
                classifier,
                array,
                args.threshold,
            )
            if score_mode != args.expected_score_mode:
                raise ValueError(
                    f"unexpected score mode {score_mode!r}; "
                    f"expected {args.expected_score_mode!r}"
                )
            if int(pred_int) not in {0, 1}:
                raise ValueError(f"unexpected predicted class: {pred_int!r}")
            human_score = float(score)
            if not math.isfinite(human_score):
                raise ValueError(f"prediction score is not finite: {human_score!r}")

            predicted_agc = 1 if int(pred_int) == 0 else 0
            predicted_hwc = 1 - predicted_agc
            result.update(
                {
                    "analysis_status": "ok",
                    "pred_int": int(pred_int),
                    "pred_label": "agc" if predicted_agc else "human",
                    "predicted_agc": predicted_agc,
                    "predicted_hwc": predicted_hwc,
                    "human_score": human_score,
                    "agc_score": human_score_to_agc_score(
                        human_score,
                        score_mode,
                    ),
                    "score_mode": score_mode,
                    "model_key": selected_model_key,
                    "failure_stage": "",
                    "error_type": "",
                    "error_message": "",
                }
            )
        except Exception as exc:
            result.update(
                {
                    "analysis_status": "failed",
                    "failure_stage": failure_stage,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )

        result["inference_seconds"] = time.perf_counter() - started
        diagnostics.append(result)

        if index % args.progress_every == 0 or index == len(events):
            scored_so_far = sum(
                row.get("analysis_status") == "ok" for row in diagnostics
            )
            failed_so_far = len(diagnostics) - scored_so_far
            print(
                "Tree-sitter ERROR-event diagnostic: "
                f"{index}/{len(events)}; scored={scored_so_far}; "
                f"failed={failed_so_far}; "
                f"event={event['function_event_id']}"
            )

        if index % args.checkpoint_every == 0 and index < len(events):
            partial_summary = build_summary(
                args=args,
                paths=paths,
                target_rows=len(events),
                manifest_rows=manifest_rows,
                diagnostics=diagnostics,
                node_details=node_details,
                model_key=selected_model_key,
                model_hash=selected_model_hash,
                device=device,
                completed=False,
            )
            partial_checks = build_checks(
                args=args,
                target_rows=len(events),
                manifest_rows=manifest_rows,
                diagnostics=diagnostics,
                model_key=selected_model_key,
            )
            write_outputs(
                paths,
                diagnostics,
                node_details,
                partial_summary,
                partial_checks,
            )

    summary = build_summary(
        args=args,
        paths=paths,
        target_rows=len(events),
        manifest_rows=manifest_rows,
        diagnostics=diagnostics,
        node_details=node_details,
        model_key=selected_model_key,
        model_hash=selected_model_hash,
        device=device,
        completed=True,
    )
    checks = build_checks(
        args=args,
        target_rows=len(events),
        manifest_rows=manifest_rows,
        diagnostics=diagnostics,
        model_key=selected_model_key,
    )
    write_outputs(paths, diagnostics, node_details, summary, checks)

    required_checks = [row for row in checks if int(row["required"]) == 1]
    required_passed = sum(int(row["passed"]) for row in required_checks)
    actual_failures = sum(
        row.get("analysis_status") == "failed" for row in diagnostics
    )

    print("=" * 76)
    print("AGC tree-sitter ERROR-node event diagnostic")
    print(f"Status:                         {summary['status']}")
    print(f"Recommendation:                 {summary['recommendation']}")
    print(
        "Required checks passed:         "
        f"{required_passed}/{len(required_checks)}"
    )
    print(f"Target events:                  {len(events)}")
    print(f"Events scored:                  {summary['events_scored']}")
    print(f"Actual scoring failures:        {summary['events_failed']}")
    print(f"Runtime AST failures:           {summary['runtime_ast_failures']}")
    print(
        "Tree-sitter root-error events:  "
        f"{summary['tree_sitter_root_error_events']}"
    )
    print(f"AGC predictions:                {summary['agc_events']}")
    print(f"HWC predictions:                {summary['hwc_events']}")
    print(f"Model key:                      {selected_model_key}")
    print(f"Score modes:                    {','.join(summary['score_modes'])}")
    print(f"Summary:                        {paths['summary']}")
    print("=" * 76)

    if actual_failures and not args.allow_scoring_failures:
        raise SystemExit(1)
    if any(int(row["passed"]) == 0 for row in required_checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
