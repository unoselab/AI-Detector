#!/usr/bin/env python3
"""
analyze_did_python_commit_functions.py
=======================================

Run fresh AGC inference for commit-function change events produced by the
DiD commit-history pipeline.

Analysis unit
-------------
One manifest row represents one named Python function that was structurally
added or modified in one commit. Repeated edits to the same function in
separate commits are intentionally retained as separate events.

Supported function types include:

- module-level functions
- methods defined inside classes
- nested functions
- async variants of all function types above

Class definitions are not analyzed as a single unit. The extraction pipeline
must write each function event as one standalone, dedented Python source
artifact. This analyzer validates that every artifact contains exactly one
function definition and then runs the validated AGC detector on that function.

Fresh inference mode
--------------------
This script intentionally does not implement prediction, embedding, or content
cache reuse. It also does not resume from prior detector checkpoints. Every
selected manifest row is read, hash-verified, normalized, embedded, and scored
again with the existing trained classifier model.

The existing trained model is reused; the model is not retrained.

Required manifest fields
------------------------
The script accepts a small set of aliases so the commit-history extractor can
use the naming conventions already present in the DiD workspace.

Canonical field                    Accepted aliases
---------------                    ----------------
dataset_source                     dataset_source
repo_name                          repo_name
repo-month                         time, month
current commit                     commit, scan_current_commit
parent commit                      parent_commit, scan_parent_commit
repository file path               relative_path
qualified function name            qualified_function_name, qualified_name
change type                        change_type
function source artifact           function_source_path,
                                    function_source_relative_path,
                                    source_relative_path
function source SHA-256             content_sha256,
                                    function_content_sha256

Optional fields such as event_id, commit_order, function_kind, start_line, and
end_line are preserved in the event-level output when present.

Primary repository-month arithmetic
-----------------------------------
function_change_events
    = agc_function_change_events + hwc_function_change_events

agc_function_change_event_ratio
    = agc_function_change_events / function_change_events

Only successfully scored events enter the AGC/HWC denominator. The output also
records expected, scored, and failed event counts. Repository-month rows with
failed detector events should not be used in the primary DiD analysis.

Expected outputs
----------------
- function_event_predictions_<source>.csv
- failed_function_events_<source>.csv
- commit_function_event_summary_<source>.csv
- repo_month_function_event_summary_<source>.csv
- run_metadata_<source>.json
- qc_summary_<source>.json

Example
-------
python src/app/py/analyze_did_python_commit_functions.py \
  --function-event-manifest /path/to/commit_function_detection_manifest.csv \
  --function-source-root /path/to/commit_function_sources \
  --model-pickle /path/to/model.pkl \
  --expected-model-key codesearchnet_codellama-7b_python_merged_4500ast_ \
  --no-cache \
  --no-resume \
  --verify-hashes
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
import textwrap
import time
import tokenize
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# This script lives in src/app/py, while agc_detector.py remains in src/app.
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
APP_DIR = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import agc_detector as agc_detector_module  # type: ignore

from agc_detector import (  # type: ignore
    EMBEDDING_MODEL_ID,
    build_feature_vector,
    extract_blocks,
    load_embedder,
    load_parser_and_F,
    pick_classifier_from_pickle,
    predict_one,
    strip_block_markers,
)

DEFAULT_EXPERIMENT = "codellama-7b_4500_complexity_stratified_maxlen2048"
DEFAULT_CLASSIFIER = "svm"
DEFAULT_REPRESENTATION = "ast"
DEFAULT_MAX_LEN = 2048
DEFAULT_EXPECTED_SCORE_MODE = "decision"
DEFAULT_MODEL_PICKLE = (
    REPO_ROOT
    / "src/ml_embeddings/data_codesearchnet/models"
    / DEFAULT_EXPERIMENT
    / (
        "tuned_models_codesearchnet_codellama-7b_"
        "4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"
    )
)
DEFAULT_MODEL_KEY = "codesearchnet_codellama-7b_python_merged_4500ast_"
DEFAULT_TREE_SITTER_LIB = (
    REPO_ROOT / "src/code-analyzer-tree-sitter/build/my-languages.so"
)
DEFAULT_AST_HELPER_DIR = REPO_ROOT / "src/code-analyzer-tree-sitter"

CANONICAL_EVENT_FIELDS = [
    "manifest_row_number",
    "function_event_id",
    "dataset_source",
    "repo_name",
    "time",
    "commit",
    "parent_commit",
    "commit_order",
    "relative_path",
    "qualified_function_name",
    "function_name",
    "function_kind",
    "occurrence_index",
    "change_type",
    "start_line",
    "end_line",
    "function_source_path",
    "content_sha256",
]

PREDICTION_FIELDS = [
    "normalized_content_sha256",
    "source_hash_verified",
    "function_name_matches_manifest",
    "tree_sitter_blocks_found",
    "analysis_status",
    "pred_label",
    "predicted_agc",
    "predicted_hwc",
    "human_score",
    "human_decision_score",
    "agc_score",
    "score_mode",
    "model_key",
    "inference_mode",
    "prediction_cache_used",
    "embedding_cache_used",
    "checkpoint_resume_used",
    "model_retrained",
    "inference_seconds",
    "error_message",
]

COMMIT_SUMMARY_FIELDS = [
    "dataset_source",
    "repo_name",
    "time",
    "commit",
    "parent_commit",
    "function_change_events_manifest",
    "function_change_events_scored",
    "function_change_events_failed",
    "agc_function_change_events",
    "hwc_function_change_events",
    "agc_function_change_event_ratio",
    "added_function_events",
    "modified_function_events",
    "added_agc_function_events",
    "added_hwc_function_events",
    "modified_agc_function_events",
    "modified_hwc_function_events",
    "unique_changed_functions_scored",
    "detection_complete",
]

REPO_MONTH_SUMMARY_FIELDS = [
    "dataset_source",
    "repo_name",
    "time",
    "commits_with_function_events_manifest",
    "commits_with_function_events_scored",
    "function_change_events_manifest",
    "function_change_events_scored",
    "function_change_events_failed",
    "agc_function_change_events",
    "hwc_function_change_events",
    "agc_function_change_event_ratio",
    "added_function_events",
    "modified_function_events",
    "added_agc_function_events",
    "added_hwc_function_events",
    "modified_agc_function_events",
    "modified_hwc_function_events",
    "unique_changed_functions_scored",
    "detection_complete",
]


@dataclass
class DetectorContext:
    parser: Any
    ast_function: Any
    tokenizer: Any
    embedding_model: Any
    device: str
    classifier: Any
    model_key: str
    model_sha256: str
    model_pickle: Path
    experiment: str
    classifier_family: str
    representation: str
    expected_score_mode: str
    max_len: int
    threshold: Optional[float]


@dataclass(frozen=True)
class ManifestSchema:
    dataset_source: str
    repo_name: str
    repo_month: str
    commit: str
    parent_commit: str
    relative_path: str
    qualified_function_name: str
    change_type: str
    function_source_path: str
    content_sha256: str
    function_event_id: Optional[str]
    commit_order: Optional[str]
    function_name: Optional[str]
    function_kind: Optional[str]
    occurrence_index: Optional[str]
    start_line: Optional[str]
    end_line: Optional[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    parser.add_argument("--classifier", default=DEFAULT_CLASSIFIER)
    parser.add_argument(
        "--representation",
        choices=["ast", "code", "combined"],
        default=DEFAULT_REPRESENTATION,
    )
    parser.add_argument("--max-len", type=int, default=DEFAULT_MAX_LEN)
    parser.add_argument(
        "--expected-score-mode",
        choices=["decision", "proba"],
        default=DEFAULT_EXPECTED_SCORE_MODE,
    )
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument(
        "--model-pickle",
        type=Path,
        default=DEFAULT_MODEL_PICKLE,
    )
    parser.add_argument(
        "--expected-model-key",
        default=DEFAULT_MODEL_KEY,
    )
    parser.add_argument(
        "--function-event-manifest",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--function-source-root",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--dataset-source",
        choices=["treatment", "control", "all"],
        default="treatment",
    )
    parser.add_argument(
        "--max-function-events",
        type=int,
        default=50,
        help="Deterministic pilot limit; use 0 or -1 for all events.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
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
    parser.add_argument("--device", default=None)
    parser.add_argument(
        "--verify-hashes",
        action="store_true",
        help="Required safe-mode flag. Verify each function artifact SHA-256.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Required safe-mode flag. Cache reuse is not implemented.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Required safe-mode flag. Prior checkpoints are not reused.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=100,
        help=(
            "Atomically refresh partial event outputs after this many processed "
            "events. Partial outputs are for failure recovery inspection only; "
            "they are never used to resume inference."
        ),
    )
    parser.add_argument(
        "--allow-event-errors",
        action="store_true",
        help=(
            "Write results and exit successfully even when one or more events "
            "fail validation or inference. The default strict mode exits 1."
        ),
    )
    return parser.parse_args()


def require_path(path: Path, kind: str) -> None:
    if kind == "file" and not path.is_file():
        raise SystemExit(f"[ERROR] required file not found: {path}")
    if kind == "dir" and not path.is_dir():
        raise SystemExit(f"[ERROR] required directory not found: {path}")


def validate_identifier(value: str, option_name: str) -> str:
    text = str(value).strip()
    if not text or not re.fullmatch(r"[A-Za-z0-9_.-]+", text):
        raise SystemExit(
            f"[ERROR] {option_name} must contain only letters, digits, '.', "
            f"'_', or '-': {value!r}"
        )
    return text


def validate_args(args: argparse.Namespace) -> None:
    args.experiment = validate_identifier(args.experiment, "--experiment")
    args.classifier = validate_identifier(args.classifier.lower(), "--classifier")
    args.expected_model_key = str(args.expected_model_key).strip()
    if not args.expected_model_key:
        raise SystemExit("[ERROR] --expected-model-key cannot be empty")
    if args.max_len <= 0:
        raise SystemExit("[ERROR] --max-len must be positive")
    if args.checkpoint_every <= 0:
        raise SystemExit("[ERROR] --checkpoint-every must be positive")

    if args.max_function_events in {0, -1}:
        args.max_function_events = None
    elif args.max_function_events is not None and args.max_function_events < -1:
        raise SystemExit(
            "[ERROR] --max-function-events must be positive, 0, or -1"
        )

    args.model_pickle = args.model_pickle.expanduser().resolve()
    args.function_event_manifest = (
        args.function_event_manifest.expanduser().resolve()
    )
    args.function_source_root = args.function_source_root.expanduser().resolve()
    args.output_root = args.output_root.expanduser().resolve()
    args.tree_sitter_lib = args.tree_sitter_lib.expanduser().resolve()
    args.ast_helper_dir = args.ast_helper_dir.expanduser().resolve()

    require_path(args.model_pickle, "file")
    require_path(args.function_event_manifest, "file")
    require_path(args.function_source_root, "dir")
    require_path(args.tree_sitter_lib, "file")
    require_path(args.ast_helper_dir, "dir")

    # This analyzer is intentionally limited to the agreed fresh safe mode.
    missing_safe_flags = []
    if not args.verify_hashes:
        missing_safe_flags.append("--verify-hashes")
    if not args.no_cache:
        missing_safe_flags.append("--no-cache")
    if not args.no_resume:
        missing_safe_flags.append("--no-resume")
    if missing_safe_flags:
        raise SystemExit(
            "[ERROR] fresh safe mode requires: " + ", ".join(missing_safe_flags)
        )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


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
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def atomic_write_csv(
    path: Path,
    rows: Sequence[Dict[str, Any]],
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
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def first_existing_field(
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


def resolve_manifest_schema(fieldnames: Sequence[str]) -> ManifestSchema:
    return ManifestSchema(
        dataset_source=first_existing_field(
            fieldnames, ["dataset_source"], "dataset source"
        ),
        repo_name=first_existing_field(fieldnames, ["repo_name"], "repo name"),
        repo_month=first_existing_field(
            fieldnames, ["time", "month"], "repo-month"
        ),
        commit=first_existing_field(
            fieldnames, ["commit", "scan_current_commit"], "current commit"
        ),
        parent_commit=first_existing_field(
            fieldnames, ["parent_commit", "scan_parent_commit"], "parent commit"
        ),
        relative_path=first_existing_field(
            fieldnames, ["relative_path"], "repository file path"
        ),
        qualified_function_name=first_existing_field(
            fieldnames,
            ["qualified_function_name", "qualified_name"],
            "qualified function name",
        ),
        change_type=first_existing_field(
            fieldnames, ["change_type"], "change type"
        ),
        function_source_path=first_existing_field(
            fieldnames,
            [
                "function_source_path",
                "function_source_relative_path",
                "source_relative_path",
            ],
            "function source artifact path",
        ),
        content_sha256=first_existing_field(
            fieldnames,
            ["content_sha256", "function_content_sha256"],
            "function source SHA-256",
        ),
        function_event_id=first_existing_field(
            fieldnames,
            ["function_event_id", "event_id"],
            "function event id",
            required=False,
        ),
        commit_order=first_existing_field(
            fieldnames, ["commit_order"], "commit order", required=False
        ),
        function_name=first_existing_field(
            fieldnames, ["function_name"], "function name", required=False
        ),
        function_kind=first_existing_field(
            fieldnames, ["function_kind"], "function kind", required=False
        ),
        occurrence_index=first_existing_field(
            fieldnames,
            ["occurrence_index", "function_occurrence_index"],
            "function occurrence index",
            required=False,
        ),
        start_line=first_existing_field(
            fieldnames, ["start_line"], "start line", required=False
        ),
        end_line=first_existing_field(
            fieldnames, ["end_line"], "end line", required=False
        ),
    )


def read_manifest(
    path: Path,
) -> Tuple[List[str], ManifestSchema, List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            raise SystemExit(f"[ERROR] manifest has no header: {path}")
        schema = resolve_manifest_schema(fieldnames)
        rows = list(reader)
    if not rows:
        raise SystemExit(f"[ERROR] manifest has no data rows: {path}")
    return list(fieldnames), schema, rows


def value(row: Dict[str, str], field: Optional[str]) -> str:
    if field is None:
        return ""
    return str(row.get(field, "")).strip()


def normalize_change_type(raw: str) -> str:
    text = raw.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "add": "added",
        "new": "added",
        "added": "added",
        "modify": "modified",
        "modified": "modified",
        "change": "modified",
        "changed": "modified",
    }
    normalized = aliases.get(text)
    if normalized is None:
        raise ValueError(
            f"unsupported change_type {raw!r}; expected added or modified"
        )
    return normalized


def validate_repo_month(text: str) -> str:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", text):
        raise ValueError(f"invalid repo-month {text!r}; expected YYYY-MM")
    return text


def validate_git_commit(text: str, label: str) -> str:
    value_text = text.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{7,64}", value_text):
        raise ValueError(f"invalid {label}: {text!r}")
    return value_text


def validate_repository_relative_path(text: str) -> str:
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts:
        raise ValueError(f"invalid relative_path: {text!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe relative_path: {text!r}")
    if path.suffix.lower() != ".py":
        raise ValueError(f"relative_path is not a Python file: {text!r}")
    return path.as_posix()


def validate_source_relative_path(text: str) -> str:
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts:
        raise ValueError(f"invalid function source path: {text!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe function source path: {text!r}")
    if path.suffix.lower() != ".py":
        raise ValueError(f"function source artifact is not .py: {text!r}")
    return path.as_posix()


def validate_sha256(text: str) -> str:
    lowered = text.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", lowered):
        raise ValueError(f"invalid SHA-256 value: {text!r}")
    return lowered


def optional_int(text: str, label: str) -> Any:
    if text == "":
        return ""
    try:
        result = int(text)
    except ValueError as exc:
        raise ValueError(f"invalid integer for {label}: {text!r}") from exc
    if result < 0:
        raise ValueError(f"{label} cannot be negative: {text!r}")
    return result


def leaf_function_name(qualified_name: str) -> str:
    text = qualified_name.strip()
    if not text:
        return ""
    normalized = text.replace("::", ".")
    return normalized.rsplit(".", 1)[-1]


def build_event_id(canonical: Dict[str, Any]) -> str:
    payload = {
        key: canonical[key]
        for key in [
            "dataset_source",
            "repo_name",
            "time",
            "commit",
            "parent_commit",
            "relative_path",
            "qualified_function_name",
            "occurrence_index",
            "change_type",
            "function_source_path",
        ]
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_manifest_row(
    row: Dict[str, str],
    row_number: int,
    schema: ManifestSchema,
) -> Dict[str, Any]:
    dataset_source = value(row, schema.dataset_source).lower()
    if dataset_source not in {"treatment", "control"}:
        raise ValueError(
            f"unsupported dataset_source {dataset_source!r}; expected treatment or control"
        )

    repo_name = value(row, schema.repo_name)
    if not repo_name or "/" not in repo_name:
        raise ValueError(f"invalid repo_name: {repo_name!r}")

    repo_month = validate_repo_month(value(row, schema.repo_month))
    commit = validate_git_commit(value(row, schema.commit), "commit")
    parent_commit = validate_git_commit(
        value(row, schema.parent_commit), "parent_commit"
    )
    relative_path = validate_repository_relative_path(
        value(row, schema.relative_path)
    )
    qualified_name = value(row, schema.qualified_function_name)
    if not qualified_name:
        raise ValueError("qualified function name cannot be empty")
    change_type = normalize_change_type(value(row, schema.change_type))
    source_path = validate_source_relative_path(
        value(row, schema.function_source_path)
    )
    content_sha256 = validate_sha256(value(row, schema.content_sha256))

    manifest_function_name = value(row, schema.function_name)
    function_name = manifest_function_name or leaf_function_name(qualified_name)
    if not function_name:
        raise ValueError("function name cannot be derived")

    canonical: Dict[str, Any] = {
        **row,
        "manifest_row_number": row_number,
        "dataset_source": dataset_source,
        "repo_name": repo_name,
        "time": repo_month,
        "commit": commit,
        "parent_commit": parent_commit,
        "commit_order": optional_int(
            value(row, schema.commit_order), "commit_order"
        ),
        "relative_path": relative_path,
        "qualified_function_name": qualified_name,
        "function_name": function_name,
        "function_kind": value(row, schema.function_kind),
        "occurrence_index": optional_int(
            value(row, schema.occurrence_index), "occurrence_index"
        ),
        "change_type": change_type,
        "start_line": optional_int(value(row, schema.start_line), "start_line"),
        "end_line": optional_int(value(row, schema.end_line), "end_line"),
        "function_source_path": source_path,
        "content_sha256": content_sha256,
    }

    supplied_event_id = value(row, schema.function_event_id)
    canonical["function_event_id"] = supplied_event_id or build_event_id(canonical)
    event_id_text = str(canonical["function_event_id"])
    if (
        not event_id_text
        or len(event_id_text) > 512
        or any(ord(char) < 32 or ord(char) == 127 for char in event_id_text)
    ):
        raise ValueError(
            "function_event_id must be nonempty, at most 512 characters, "
            "and contain no control characters"
        )
    return canonical


def canonical_event_key(row: Dict[str, Any]) -> Tuple[str, ...]:
    return (
        str(row["dataset_source"]),
        str(row["repo_name"]),
        str(row["time"]),
        str(row["commit"]),
        str(row["relative_path"]),
        str(row["qualified_function_name"]),
        str(row.get("occurrence_index", "")),
        str(row.get("start_line", "")),
        str(row.get("end_line", "")),
    )


def commit_order_sort_value(value_any: Any) -> int:
    if value_any in {"", None}:
        return 10**12
    try:
        return int(value_any)
    except (TypeError, ValueError):
        return 10**12


def event_sort_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        str(row["dataset_source"]),
        str(row["repo_name"]),
        str(row["time"]),
        commit_order_sort_value(row.get("commit_order")),
        str(row["commit"]),
        str(row["relative_path"]),
        str(row["qualified_function_name"]),
        str(row["function_event_id"]),
    )


def selected_sources(dataset_source: str) -> set[str]:
    if dataset_source == "all":
        return {"treatment", "control"}
    return {dataset_source}


def normalize_and_select_events(
    raw_rows: Sequence[Dict[str, str]],
    schema: ManifestSchema,
    dataset_source: str,
    max_events: Optional[int],
) -> Tuple[List[Dict[str, Any]], int]:
    normalized: List[Dict[str, Any]] = []
    sources = selected_sources(dataset_source)

    for row_number, row in enumerate(raw_rows, start=2):
        try:
            canonical = normalize_manifest_row(row, row_number, schema)
        except Exception as exc:
            raise SystemExit(
                f"[ERROR] invalid manifest row {row_number}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        if canonical["dataset_source"] in sources:
            normalized.append(canonical)

    discovered_selected_source = len(normalized)
    if not normalized:
        raise SystemExit(
            f"[ERROR] no manifest events match dataset source {dataset_source!r}"
        )

    seen_ids: set[str] = set()
    seen_keys: set[Tuple[str, ...]] = set()
    for row in normalized:
        event_id = str(row["function_event_id"])
        event_key = canonical_event_key(row)
        if event_id in seen_ids:
            raise SystemExit(f"[ERROR] duplicate function_event_id: {event_id}")
        if event_key in seen_keys:
            raise SystemExit(
                "[ERROR] duplicate commit-function event: "
                + " | ".join(event_key)
            )
        seen_ids.add(event_id)
        seen_keys.add(event_key)

    normalized.sort(key=event_sort_key)
    if max_events is not None:
        normalized = normalized[:max_events]
    return normalized, discovered_selected_source


def resolve_function_source(root: Path, relative_path: str) -> Path:
    rel = validate_source_relative_path(relative_path)
    candidate = root.joinpath(*PurePosixPath(rel).parts)
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


def read_python_source(path: Path) -> str:
    # tokenize.open honors PEP 263 encoding declarations when they are present.
    with tokenize.open(path) as handle:
        return handle.read()


def normalize_function_source(source: str) -> str:
    text = strip_block_markers(source)
    text = textwrap.dedent(text).strip()
    if not text:
        raise ValueError("function source artifact is empty")
    return text + "\n"


def validate_single_function_source(
    source: str,
    expected_function_name: str,
) -> Tuple[str, int]:
    module = ast.parse(source)
    function_nodes = [
        node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    class_nodes = [node for node in module.body if isinstance(node, ast.ClassDef)]
    other_nodes = [
        node
        for node in module.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    if class_nodes:
        raise ValueError(
            "function artifact contains a top-level class; classes must not be "
            "analyzed as one detector unit"
        )
    if len(function_nodes) != 1:
        raise ValueError(
            "function artifact must contain exactly one top-level function; "
            f"found {len(function_nodes)}"
        )
    if other_nodes:
        node_types = sorted({type(node).__name__ for node in other_nodes})
        raise ValueError(
            "function artifact contains additional top-level statements: "
            + ", ".join(node_types)
        )

    actual_name = str(function_nodes[0].name)
    name_matches = int(actual_name == expected_function_name)
    return actual_name, name_matches


def default_threshold_for_mode(score_mode: str) -> float:
    if score_mode == "proba":
        return 0.5
    if score_mode == "decision":
        return 0.0
    raise ValueError(f"unsupported score mode: {score_mode}")


def effective_threshold(context: DetectorContext) -> float:
    if context.threshold is not None:
        return float(context.threshold)
    return default_threshold_for_mode(context.expected_score_mode)


def human_score_to_agc_score(human_score: float, score_mode: str) -> float:
    if score_mode == "decision":
        return -human_score
    if score_mode == "proba":
        return 1.0 - human_score
    raise RuntimeError(f"unsupported score mode: {score_mode!r}")


def ratio(numerator: int, denominator: int) -> Any:
    return numerator / denominator if denominator else ""


def initialize_detector(args: argparse.Namespace) -> DetectorContext:
    # build_feature_vector() reads MAX_LEN from agc_detector.py module globals.
    agc_detector_module.MAX_LEN = args.max_len

    import torch

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    parser, ast_function = load_parser_and_F(
        str(args.tree_sitter_lib),
        str(args.ast_helper_dir),
    )
    tokenizer, embedding_model = load_embedder(device)
    classifier, model_key = pick_classifier_from_pickle(
        str(args.model_pickle),
        f"{args.representation}_",
    )
    if model_key != args.expected_model_key:
        raise SystemExit(
            "[ERROR] unexpected classifier key\n"
            f"        selected: {model_key}\n"
            f"        expected: {args.expected_model_key}"
        )

    return DetectorContext(
        parser=parser,
        ast_function=ast_function,
        tokenizer=tokenizer,
        embedding_model=embedding_model,
        device=device,
        classifier=classifier,
        model_key=model_key,
        model_sha256=sha256_file(args.model_pickle),
        model_pickle=args.model_pickle,
        experiment=args.experiment,
        classifier_family=args.classifier,
        representation=args.representation,
        expected_score_mode=args.expected_score_mode,
        max_len=args.max_len,
        threshold=args.threshold,
    )


def empty_prediction_fields() -> Dict[str, Any]:
    return {
        "normalized_content_sha256": "",
        "source_hash_verified": 0,
        "function_name_matches_manifest": "",
        "tree_sitter_blocks_found": "",
        "analysis_status": "",
        "pred_label": "",
        "predicted_agc": "",
        "predicted_hwc": "",
        "human_score": "",
        "human_decision_score": "",
        "agc_score": "",
        "score_mode": "",
        "model_key": "",
        "inference_mode": "fresh",
        "prediction_cache_used": 0,
        "embedding_cache_used": 0,
        "checkpoint_resume_used": 0,
        "model_retrained": 0,
        "inference_seconds": "",
        "error_message": "",
    }


def analyze_function_event(
    event: Dict[str, Any],
    args: argparse.Namespace,
    context: DetectorContext,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        **event,
        **empty_prediction_fields(),
    }
    started = time.perf_counter()

    try:
        source_path = resolve_function_source(
            args.function_source_root,
            str(event["function_source_path"]),
        )
        actual_sha256 = sha256_file(source_path)
        expected_sha256 = str(event["content_sha256"])
        if actual_sha256 != expected_sha256:
            raise ValueError(
                "function source SHA-256 mismatch: "
                f"manifest={expected_sha256} actual={actual_sha256}"
            )
        result["source_hash_verified"] = 1

        raw_source = read_python_source(source_path)
        normalized_source = normalize_function_source(raw_source)
        result["normalized_content_sha256"] = sha256_bytes(
            normalized_source.encode("utf-8")
        )

        actual_function_name, name_matches = validate_single_function_source(
            normalized_source,
            str(event["function_name"]),
        )
        result["function_name_matches_manifest"] = name_matches
        if not name_matches:
            raise ValueError(
                "function name mismatch: "
                f"manifest={event['function_name']!r} "
                f"source={actual_function_name!r}"
            )

        blocks = extract_blocks(normalized_source, context.parser)
        result["tree_sitter_blocks_found"] = len(blocks)
        if len(blocks) != 1:
            raise ValueError(
                "tree-sitter detector input must contain exactly one block; "
                f"found {len(blocks)}"
            )
        block = blocks[0]
        if str(block.get("kind", "")) != "function_definition":
            raise ValueError(
                "detector input resolved to a non-function block: "
                f"{block.get('kind')!r}"
            )
        if str(block.get("name", "")) != actual_function_name:
            raise ValueError(
                "tree-sitter function name mismatch: "
                f"python_ast={actual_function_name!r} "
                f"tree_sitter={block.get('name')!r}"
            )

        vector = build_feature_vector(
            block["code"],
            context.representation,
            context.parser,
            context.ast_function,
            context.tokenizer,
            context.embedding_model,
            context.device,
        )
        pred_int, score, score_mode = predict_one(
            context.classifier,
            vector,
            context.threshold,
        )
        if score_mode != context.expected_score_mode:
            raise RuntimeError(
                f"unexpected score mode {score_mode!r}; "
                f"expected {context.expected_score_mode!r}"
            )

        human_score = float(score)
        agc_score = human_score_to_agc_score(human_score, score_mode)
        predicted_agc = 1 if int(pred_int) == 0 else 0
        predicted_hwc = 1 - predicted_agc

        result.update(
            {
                "analysis_status": "ok",
                "pred_label": "agc" if predicted_agc else "human",
                "predicted_agc": predicted_agc,
                "predicted_hwc": predicted_hwc,
                "human_score": human_score,
                "human_decision_score": (
                    human_score if score_mode == "decision" else ""
                ),
                "agc_score": agc_score,
                "score_mode": score_mode,
                "model_key": context.model_key,
            }
        )
    except FileNotFoundError as exc:
        result["analysis_status"] = "missing_source"
        result["error_message"] = str(exc)
    except (UnicodeDecodeError, SyntaxError) as exc:
        result["analysis_status"] = "source_parse_error"
        result["error_message"] = f"{type(exc).__name__}: {exc}"
    except ValueError as exc:
        result["analysis_status"] = "validation_error"
        result["error_message"] = str(exc)
    except Exception as exc:
        result["analysis_status"] = "inference_error"
        result["error_message"] = f"{type(exc).__name__}: {exc}"

    result["inference_seconds"] = time.perf_counter() - started
    return result


def unique_fieldnames(
    manifest_fields: Sequence[str],
    added_fields: Sequence[str],
) -> List[str]:
    result: List[str] = []
    for field in list(manifest_fields) + list(added_fields):
        if field not in result:
            result.append(field)
    return result


def is_scored(row: Dict[str, Any]) -> bool:
    return str(row.get("analysis_status", "")) == "ok"


def summarize_group(
    rows: Sequence[Dict[str, Any]],
    group_fields: Sequence[str],
) -> Dict[str, Any]:
    first = rows[0]
    scored = [row for row in rows if is_scored(row)]
    failed = [row for row in rows if not is_scored(row)]

    agc = sum(int(row["predicted_agc"]) for row in scored)
    hwc = sum(int(row["predicted_hwc"]) for row in scored)
    if len(scored) != agc + hwc:
        raise RuntimeError(
            "scored event arithmetic failed: "
            f"scored={len(scored)} agc={agc} hwc={hwc}"
        )

    added = [row for row in scored if row["change_type"] == "added"]
    modified = [row for row in scored if row["change_type"] == "modified"]

    unique_functions = {
        (str(row["relative_path"]), str(row["qualified_function_name"]))
        for row in scored
    }

    summary: Dict[str, Any] = {field: first[field] for field in group_fields}
    summary.update(
        {
            "function_change_events_manifest": len(rows),
            "function_change_events_scored": len(scored),
            "function_change_events_failed": len(failed),
            "agc_function_change_events": agc,
            "hwc_function_change_events": hwc,
            "agc_function_change_event_ratio": ratio(agc, len(scored)),
            "added_function_events": len(added),
            "modified_function_events": len(modified),
            "added_agc_function_events": sum(
                int(row["predicted_agc"]) for row in added
            ),
            "added_hwc_function_events": sum(
                int(row["predicted_hwc"]) for row in added
            ),
            "modified_agc_function_events": sum(
                int(row["predicted_agc"]) for row in modified
            ),
            "modified_hwc_function_events": sum(
                int(row["predicted_hwc"]) for row in modified
            ),
            "unique_changed_functions_scored": len(unique_functions),
            "detection_complete": int(len(failed) == 0),
        }
    )

    if summary["function_change_events_scored"] != (
        summary["agc_function_change_events"]
        + summary["hwc_function_change_events"]
    ):
        raise RuntimeError("AGC/HWC event arithmetic failed")
    if summary["function_change_events_scored"] != (
        summary["added_function_events"] + summary["modified_function_events"]
    ):
        raise RuntimeError("added/modified event arithmetic failed")
    return summary


def build_commit_summaries(
    rows: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["dataset_source"]),
            str(row["repo_name"]),
            str(row["time"]),
            str(row["commit"]),
            str(row["parent_commit"]),
        )
        groups[key].append(row)

    summaries = [
        summarize_group(
            group_rows,
            ["dataset_source", "repo_name", "time", "commit", "parent_commit"],
        )
        for _, group_rows in sorted(groups.items())
    ]
    return summaries


def build_repo_month_summaries(
    rows: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["dataset_source"]),
            str(row["repo_name"]),
            str(row["time"]),
        )
        groups[key].append(row)

    summaries: List[Dict[str, Any]] = []
    for _, group_rows in sorted(groups.items()):
        summary = summarize_group(
            group_rows,
            ["dataset_source", "repo_name", "time"],
        )
        summary["commits_with_function_events_manifest"] = len(
            {str(row["commit"]) for row in group_rows}
        )
        summary["commits_with_function_events_scored"] = len(
            {str(row["commit"]) for row in group_rows if is_scored(row)}
        )
        summaries.append(summary)
    return summaries


def write_partial_outputs(
    output_root: Path,
    suffix: str,
    rows: Sequence[Dict[str, Any]],
    event_fields: Sequence[str],
) -> None:
    atomic_write_csv(
        output_root / f"function_event_predictions_{suffix}.partial.csv",
        rows,
        event_fields,
    )
    failures = [row for row in rows if not is_scored(row)]
    atomic_write_csv(
        output_root / f"failed_function_events_{suffix}.partial.csv",
        failures,
        event_fields,
    )


def write_final_outputs(
    output_root: Path,
    suffix: str,
    event_rows: Sequence[Dict[str, Any]],
    event_fields: Sequence[str],
) -> Dict[str, Path]:
    prediction_path = output_root / f"function_event_predictions_{suffix}.csv"
    failure_path = output_root / f"failed_function_events_{suffix}.csv"
    commit_path = output_root / f"commit_function_event_summary_{suffix}.csv"
    repo_month_path = output_root / f"repo_month_function_event_summary_{suffix}.csv"

    failures = [row for row in event_rows if not is_scored(row)]
    commit_rows = build_commit_summaries(event_rows)
    repo_month_rows = build_repo_month_summaries(event_rows)

    atomic_write_csv(prediction_path, event_rows, event_fields)
    atomic_write_csv(failure_path, failures, event_fields)
    atomic_write_csv(commit_path, commit_rows, COMMIT_SUMMARY_FIELDS)
    atomic_write_csv(repo_month_path, repo_month_rows, REPO_MONTH_SUMMARY_FIELDS)

    for partial in [
        output_root / f"function_event_predictions_{suffix}.partial.csv",
        output_root / f"failed_function_events_{suffix}.partial.csv",
    ]:
        if partial.exists():
            partial.unlink()

    return {
        "prediction": prediction_path,
        "failure": failure_path,
        "commit": commit_path,
        "repo_month": repo_month_path,
    }


def write_run_metadata(
    args: argparse.Namespace,
    context: DetectorContext,
    manifest_fields: Sequence[str],
    discovered_manifest_rows: int,
    discovered_selected_source: int,
    selected_events: int,
) -> Path:
    suffix = args.dataset_source
    path = args.output_root / f"run_metadata_{suffix}.json"
    atomic_write_json(
        path,
        {
            "script": str(SCRIPT_PATH),
            "script_sha256": sha256_file(SCRIPT_PATH),
            "started_at_utc": utc_now(),
            "repo_root": str(REPO_ROOT),
            "function_event_manifest": str(args.function_event_manifest),
            "function_event_manifest_sha256": sha256_file(
                args.function_event_manifest
            ),
            "function_source_root": str(args.function_source_root),
            "output_root": str(args.output_root),
            "manifest_fields": list(manifest_fields),
            "dataset_source": args.dataset_source,
            "experiment": args.experiment,
            "classifier": args.classifier,
            "representation": args.representation,
            "model_pickle": str(context.model_pickle),
            "model_sha256": context.model_sha256,
            "model_key": context.model_key,
            "embedding_model_id": EMBEDDING_MODEL_ID,
            "max_len": args.max_len,
            "threshold_requested": args.threshold,
            "threshold_effective": effective_threshold(context),
            "expected_score_mode": args.expected_score_mode,
            "device": context.device,
            "inference_mode": "fresh",
            "prediction_cache_used": False,
            "embedding_cache_used": False,
            "checkpoint_resume_used": False,
            "model_retrained": False,
            "verify_hashes": True,
            "max_function_events": args.max_function_events,
            "checkpoint_every": args.checkpoint_every,
            "discovered_manifest_rows": discovered_manifest_rows,
            "discovered_selected_source": discovered_selected_source,
            "selected_events": selected_events,
            "python": sys.version,
            "platform": platform.platform(),
        },
    )
    return path


def write_qc_summary(
    args: argparse.Namespace,
    event_rows: Sequence[Dict[str, Any]],
) -> Path:
    scored = [row for row in event_rows if is_scored(row)]
    failed = [row for row in event_rows if not is_scored(row)]
    agc = sum(int(row["predicted_agc"]) for row in scored)
    hwc = sum(int(row["predicted_hwc"]) for row in scored)
    source_hash_failures = sum(
        int(row.get("source_hash_verified", 0)) == 0 for row in event_rows
    )
    status_counts: Dict[str, int] = defaultdict(int)
    for row in event_rows:
        status_counts[str(row.get("analysis_status", ""))] += 1

    payload = {
        "experiment": args.experiment,
        "classifier": args.classifier,
        "representation": args.representation,
        "dataset_source": args.dataset_source,
        "function_change_events_manifest": len(event_rows),
        "function_change_events_scored": len(scored),
        "function_change_events_failed": len(failed),
        "agc_function_change_events": agc,
        "hwc_function_change_events": hwc,
        "agc_function_change_event_ratio": ratio(agc, len(scored)),
        "event_arithmetic_pass": len(scored) == agc + hwc,
        "source_hash_failures": source_hash_failures,
        "status_counts": dict(sorted(status_counts.items())),
        "inference_mode": "fresh",
        "prediction_cache_used": False,
        "embedding_cache_used": False,
        "checkpoint_resume_used": False,
        "model_retrained": False,
        "completed_at_utc": utc_now(),
    }
    path = args.output_root / f"qc_summary_{args.dataset_source}.json"
    atomic_write_json(path, payload)
    return path


def print_configuration(args: argparse.Namespace) -> None:
    print("=" * 76)
    print("analyze_did_python_commit_functions.py")
    print("  analysis unit        : commit-function change event")
    print("  function scope       : module, class method, nested, async")
    print("  inference mode       : fresh; no cache; no resume")
    print(f"  experiment           : {args.experiment}")
    print(f"  classifier           : {args.classifier}")
    print(f"  representation       : {args.representation}")
    print(f"  model pickle         : {args.model_pickle}")
    print(f"  expected model key   : {args.expected_model_key}")
    print(f"  expected score mode  : {args.expected_score_mode}")
    print(f"  max len              : {args.max_len}")
    print(f"  dataset source       : {args.dataset_source}")
    print(f"  event manifest       : {args.function_event_manifest}")
    print(f"  function source root : {args.function_source_root}")
    print(f"  max function events  : {args.max_function_events}")
    print(f"  output root          : {args.output_root}")
    print(f"  device               : {args.device or '<auto>'}")
    print("=" * 76)


def main() -> None:
    args = parse_args()
    validate_args(args)
    args.output_root.mkdir(parents=True, exist_ok=True)
    print_configuration(args)

    manifest_fields, schema, raw_rows = read_manifest(
        args.function_event_manifest
    )
    events, discovered_selected_source = normalize_and_select_events(
        raw_rows=raw_rows,
        schema=schema,
        dataset_source=args.dataset_source,
        max_events=args.max_function_events,
    )

    print(f"  manifest rows        : {len(raw_rows)}")
    print(f"  source-matched rows  : {discovered_selected_source}")
    print(f"  selected events      : {len(events)}")

    context = initialize_detector(args)
    event_fields = unique_fieldnames(
        manifest_fields,
        CANONICAL_EVENT_FIELDS + PREDICTION_FIELDS,
    )
    metadata_path = write_run_metadata(
        args=args,
        context=context,
        manifest_fields=manifest_fields,
        discovered_manifest_rows=len(raw_rows),
        discovered_selected_source=discovered_selected_source,
        selected_events=len(events),
    )

    results: List[Dict[str, Any]] = []
    total = len(events)
    for event_index, event in enumerate(events, start=1):
        print(
            f"[{event_index}/{total}] "
            f"{event['dataset_source']} {event['repo_name']} {event['time']} "
            f"{event['commit'][:12]} {event['relative_path']} "
            f"{event['qualified_function_name']}"
        )
        result = analyze_function_event(event, args, context)
        results.append(result)
        print(
            f"  status={result['analysis_status']} "
            f"label={result['pred_label'] or '<none>'} "
            f"seconds={float(result['inference_seconds']):.3f}"
        )
        if result["error_message"]:
            print(f"  error={result['error_message']}")

        if event_index % args.checkpoint_every == 0:
            write_partial_outputs(
                args.output_root,
                args.dataset_source,
                results,
                event_fields,
            )
            print(f"  [partial save] processed={event_index}")

    output_paths = write_final_outputs(
        output_root=args.output_root,
        suffix=args.dataset_source,
        event_rows=results,
        event_fields=event_fields,
    )
    qc_path = write_qc_summary(args, results)

    failures = [row for row in results if not is_scored(row)]
    scored = len(results) - len(failures)
    agc = sum(int(row["predicted_agc"]) for row in results if is_scored(row))
    hwc = sum(int(row["predicted_hwc"]) for row in results if is_scored(row))

    print()
    print("=" * 76)
    print("Completed")
    print(f"  selected events      : {len(results)}")
    print(f"  scored events        : {scored}")
    print(f"  failed events        : {len(failures)}")
    print(f"  AGC events           : {agc}")
    print(f"  HWC events           : {hwc}")
    print(f"  AGC event ratio      : {ratio(agc, scored)}")
    print(f"  event predictions    : {output_paths['prediction']}")
    print(f"  failed events        : {output_paths['failure']}")
    print(f"  commit summary       : {output_paths['commit']}")
    print(f"  repo-month summary   : {output_paths['repo_month']}")
    print(f"  run metadata         : {metadata_path}")
    print(f"  QC summary           : {qc_path}")
    print("=" * 76)

    if failures and not args.allow_event_errors:
        raise SystemExit(
            f"[ERROR] {len(failures)} function events failed; "
            "see failed_function_events output"
        )


if __name__ == "__main__":
    main()
