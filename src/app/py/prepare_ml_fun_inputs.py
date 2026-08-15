#!/usr/bin/env python3
"""
run-x-a02: prepare ML detector inputs for the exact NPR FUN occurrence universe.

Purpose
-------
This stage creates the bridge between the frozen perturbation-based NPR input
universe and the frozen CodeLlama-7B + SVM + AST detector from run-x-a01.
It does not load CodeT5+, does not run SVM inference, and does not inspect any
SonarQube/DiD quality outcome.

The primary equality contract is:

    same repository
      -> same historical commit
      -> same Python file
      -> same A05 primary function_body occurrence

For every selected A05 primary ``function_body`` occurrence, A02:

1. Reads the exact historical Python blob from the original Git clone.
2. Verifies the raw file SHA-256 against the frozen A05 manifest.
3. Slices the exact NPR implementation body by A05 character offsets and
   verifies its SHA-256 and literal-space-token count.
4. Uses the ML detector's tree-sitter parser to locate the corresponding full
   function definition in the same historical source file.
5. Normalizes that function as a standalone source artifact using the same
   dedent/strip convention used by the existing function-level ML analyzer.
6. Verifies that the standalone source resolves to exactly one function block,
   preserves the expected function name, and produces a nonempty AST sequence.
7. Stores the normalized standalone function source content-addressed by SHA-256.

The current run-x-a02 wrapper intentionally pins the scope to primary
``function_body`` occurrences so that the first ML-based quality DiD is directly
comparable with the already-frozen FUN NPR quality analysis. The Python program
supports another unit type for a later prespecified extension, but run-x-a02-v1
must use ``function_body``.

Inputs
------
A01 freeze artifacts:
    detector_freeze_summary.json
    detector_freeze_metadata.json

A05 NPR preparation artifacts:
    snapshot_status.csv
    python_code_unit_manifest.csv

Outputs
-------
    python_ml_fun_occurrence_manifest.csv
    python_ml_fun_unique_source_manifest.csv
    python_ml_fun_mapping_failures.csv
    checks.csv
    summary.json
    metadata.json
    ml_function_sources/<sha-prefix>/<sha256>.py
    snapshot_chunks/<snapshot_id>/...

The per-snapshot chunks make a long CPU preparation resumable. Existing chunks
are reused only when their selected A05 occurrence fingerprint and the frozen
A01/A05 provenance match exactly.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import tokenize
from collections import Counter, OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Sequence


SCRIPT_VERSION = "run-x-a02-v2"
RUN_NAME = "run-x-a02"
PRIMARY_UNIT_TYPE = "function_body"
PRIMARY_AGGREGATION_ROLE = "primary"
EXPECTED_FUN_OCCURRENCES = 921_762
EXPECTED_UNIQUE_FUN_BODY_SHA = 105_635
EXPECTED_SNAPSHOTS = 1_496

FULL_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{7,64}$")

OCCURRENCE_COLUMNS = [
    "snapshot_order",
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "repo_key",
    "snapshot_time",
    "snapshot_commit",
    "relative_path",
    "file_sha256",
    "git_blob_oid",
    "code_unit_id",
    "code_unit_type",
    "aggregation_role",
    "qualified_name",
    "function_name",
    "function_kind",
    "occurrence_index",
    "npr_body_sha256",
    "npr_body_relative_path",
    "npr_body_start_line",
    "npr_body_end_line",
    "npr_body_start_char_offset",
    "npr_body_end_char_offset",
    "npr_body_character_count",
    "npr_body_utf8_byte_count",
    "npr_body_physical_line_count",
    "npr_body_space_by_token_count",
    "file_sha256_verified",
    "npr_body_sha256_verified",
    "npr_body_space_by_token_count_verified",
    "tree_sitter_function_name",
    "tree_sitter_function_name_matches",
    "tree_sitter_full_file_has_error",
    "tree_sitter_standalone_has_error",
    "tree_sitter_standalone_error_nodes",
    "tree_sitter_standalone_missing_nodes",
    "tree_sitter_blocks_found",
    "tree_sitter_block_kind",
    "tree_sitter_block_name",
    "tree_sitter_block_covers_full_source",
    "ml_ast_sequence_character_count",
    "ml_ast_sequence_token_count",
    "ml_source_sha256",
    "ml_source_relative_path",
    "ml_source_character_count",
    "ml_source_utf8_byte_count",
    "ml_source_physical_line_count",
    "ml_source_start_byte_utf8",
    "ml_source_end_byte_utf8",
    "ml_source_includes_decorators",
    "ml_source_normalization",
    "mapping_status",
    "mapping_warning",
]

FAILURE_COLUMNS = [
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "snapshot_commit",
    "relative_path",
    "code_unit_id",
    "qualified_name",
    "npr_body_sha256",
    "stage",
    "error_type",
    "error_message",
]

UNIQUE_SOURCE_COLUMNS = [
    "ml_source_sha256",
    "ml_source_relative_path",
    "occurrence_count",
    "first_dataset_source",
    "first_repo_name",
    "first_snapshot_id",
    "first_snapshot_commit",
    "first_relative_path",
    "first_code_unit_id",
    "first_qualified_name",
    "function_name",
    "function_kind",
    "ml_source_character_count",
    "ml_source_utf8_byte_count",
    "ml_source_physical_line_count",
    "ml_ast_sequence_character_count",
    "ml_ast_sequence_token_count",
    "any_tree_sitter_standalone_warning",
]

CHECK_COLUMNS = ["check_name", "severity", "passed", "observed", "expected", "note"]


class MappingError(RuntimeError):
    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


@dataclass(frozen=True)
class SnapshotStatus:
    snapshot_id: str
    dataset_source: str
    repo_name: str
    repo_key: str
    commit_sha: str
    clone_path_original: Path
    clone_path_effective: Path
    status: str


@dataclass
class DetectorParser:
    parser: Any
    ast_function: Any
    extract_blocks: Any
    generate_ast_sequence: Any
    strip_block_markers: Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def count_physical_lines(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines()) or 1


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def as_int(value: Any, label: str) -> int:
    text = clean(value)
    try:
        result = int(text)
    except ValueError as exc:
        raise MappingError("manifest_schema", f"invalid integer {label}={text!r}") from exc
    if result < 0:
        raise MappingError("manifest_schema", f"negative integer {label}={result}")
    return result


def parse_bool(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def validate_relative_python_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts:
        raise MappingError("manifest_schema", f"invalid relative path: {value!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise MappingError("manifest_schema", f"unsafe relative path: {value!r}")
    if path.suffix.lower() != ".py":
        raise MappingError("manifest_schema", f"not a Python path: {value!r}")
    return path.as_posix()


def leaf_function_name(qualified_name: str) -> str:
    normalized = qualified_name.replace("::", ".").strip(".")
    return normalized.rsplit(".", 1)[-1] if normalized else ""


def decode_python_source(payload: bytes) -> tuple[str, str]:
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(payload).readline)
        return payload.decode(encoding), encoding
    except Exception as exc:
        raise MappingError("source_decode", f"{type(exc).__name__}: {exc}") from exc


def normalize_function_source(raw_source: str, strip_block_markers: Any) -> str:
    text = strip_block_markers(raw_source)
    text = textwrap.dedent(text).strip()
    if not text:
        raise MappingError("ml_source_normalize", "standalone function source is empty")
    return text + "\n"


def count_tree_recovery_nodes(root: Any) -> tuple[int, int]:
    error_count = 0
    missing_count = 0
    stack = [root]
    while stack:
        node = stack.pop()
        if clean(getattr(node, "type", "")) == "ERROR":
            error_count += 1
        is_missing = getattr(node, "is_missing", False)
        if callable(is_missing):
            is_missing = is_missing()
        if bool(is_missing):
            missing_count += 1
        children = list(getattr(node, "children", []) or [])
        stack.extend(reversed(children))
    return error_count, missing_count


def tree_has_error(root: Any) -> bool:
    value = getattr(root, "has_error", False)
    return bool(value() if callable(value) else value)


def iter_tree_nodes(root: Any) -> Iterator[Any]:
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(list(getattr(node, "children", []) or [])))


def node_name(node: Any, utf8_source: bytes) -> str:
    name_node = None
    child_by_field_name = getattr(node, "child_by_field_name", None)
    if callable(child_by_field_name):
        try:
            name_node = child_by_field_name("name")
        except Exception:
            name_node = None
    if name_node is None:
        for child in list(getattr(node, "children", []) or []):
            if clean(getattr(child, "type", "")) == "identifier":
                name_node = child
                break
    if name_node is None:
        return ""
    return utf8_source[int(name_node.start_byte) : int(name_node.end_byte)].decode(
        "utf-8", errors="strict"
    )


def char_offset_to_utf8_byte(source: str, offset: int) -> int:
    if offset < 0 or offset > len(source):
        raise MappingError(
            "body_boundary",
            f"character offset {offset} outside decoded source length {len(source)}",
        )
    return len(source[:offset].encode("utf-8"))


def enclosing_function_node(
    root: Any,
    utf8_source: bytes,
    body_start_byte: int,
    body_end_byte: int,
    expected_name: str,
) -> Any:
    """Map an A05 body slice to the matching tree-sitter function node.

    A05 intentionally defines the function-body end at the end of the final
    physical source line so comments and the line terminator are preserved.
    Tree-sitter, however, normally ends ``function_definition`` at the final
    syntactic token and may exclude the trailing newline/trivia. Requiring the
    entire A05 body interval to be contained by the tree-sitter node therefore
    rejects valid functions.

    The A05 body start is a stable interior anchor: it is either the suite start
    or the first non-docstring statement. We identify a same-name function node
    that contains this anchor and whose syntactic end does not extend beyond the
    independently verified A05 body envelope. The file SHA and exact A05 body
    SHA are verified before this function is called, so this relaxed trailing
    boundary rule does not weaken occurrence identity.
    """
    candidates: list[Any] = []
    for node in iter_tree_nodes(root):
        if clean(getattr(node, "type", "")) != "function_definition":
            continue
        start = int(getattr(node, "start_byte", -1))
        end = int(getattr(node, "end_byte", -1))
        if start <= body_start_byte < end and end <= body_end_byte:
            if node_name(node, utf8_source) == expected_name:
                candidates.append(node)
    if not candidates:
        raise MappingError(
            "tree_sitter_occurrence_map",
            f"no function_definition for {expected_name!r} containing A05 body-start anchor "
            f"{body_start_byte} with syntactic end <= A05 body end {body_end_byte}",
        )
    candidates.sort(key=lambda node: int(node.end_byte) - int(node.start_byte))
    best = candidates[0]
    if len(candidates) > 1:
        first_span = int(best.end_byte) - int(best.start_byte)
        second_span = int(candidates[1].end_byte) - int(candidates[1].start_byte)
        if first_span == second_span:
            raise MappingError(
                "tree_sitter_occurrence_map",
                f"ambiguous equal-span function nodes for {expected_name!r}",
            )
    return best


def full_definition_node(function_node: Any) -> tuple[Any, bool]:
    parent = getattr(function_node, "parent", None)
    if parent is not None and clean(getattr(parent, "type", "")) == "decorated_definition":
        return parent, True
    return function_node, False


def artifact_relative_path(source_sha256: str) -> Path:
    return Path("ml_function_sources") / source_sha256[:2] / f"{source_sha256}.py"


def write_artifact(output_root: Path, source: str) -> tuple[str, str, bool]:
    payload = source.encode("utf-8")
    digest = sha256_bytes(payload)
    relative = artifact_relative_path(digest)
    destination = output_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    reused = destination.exists()
    if reused:
        if sha256_file(destination) != digest:
            raise MappingError(
                "artifact_integrity",
                f"existing artifact hash mismatch: {destination}",
            )
    else:
        temp = destination.with_name(destination.name + f".tmp.{os.getpid()}")
        temp.write_bytes(payload)
        if sha256_file(temp) != digest:
            temp.unlink(missing_ok=True)
            raise MappingError("artifact_integrity", f"new artifact hash mismatch: {temp}")
        os.replace(temp, destination)
    return digest, relative.as_posix(), reused


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def atomic_write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})
    os.replace(temp, path)


def add_check(
    checks: list[dict[str, Any]],
    name: str,
    severity: str,
    passed: bool,
    observed: Any,
    expected: Any,
    note: str = "",
) -> None:
    checks.append(
        {
            "check_name": name,
            "severity": severity,
            "passed": 1 if passed else 0,
            "observed": observed,
            "expected": expected,
            "note": note,
        }
    )


class GitCatFileBatch:
    """Read Git objects through one long-lived ``git cat-file --batch`` process."""

    def __init__(self, clone_path: Path) -> None:
        self.clone_path = clone_path
        self.proc = subprocess.Popen(
            ["git", "-C", str(clone_path), "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if self.proc.stdin is None or self.proc.stdout is None:
            raise MappingError("git_batch", f"failed to open git cat-file pipes: {clone_path}")

    def read_blob(self, commit: str, relative_path: str) -> tuple[str, bytes]:
        spec = f"{commit}:{relative_path}"
        assert self.proc.stdin is not None
        assert self.proc.stdout is not None
        self.proc.stdin.write((spec + "\n").encode("utf-8"))
        self.proc.stdin.flush()
        header = self.proc.stdout.readline()
        if not header:
            raise MappingError("git_blob_read", f"git cat-file terminated while reading {spec}")
        header_text = header.decode("utf-8", errors="replace").rstrip("\n")
        if header_text.endswith(" missing"):
            raise MappingError("git_blob_read", f"Git object missing: {spec}")
        parts = header_text.split()
        if len(parts) != 3:
            raise MappingError("git_blob_read", f"unexpected git cat-file header: {header_text!r}")
        oid, object_type, size_text = parts
        if object_type != "blob":
            raise MappingError(
                "git_blob_read",
                f"expected blob for {spec}, got {object_type!r}",
            )
        try:
            size = int(size_text)
        except ValueError as exc:
            raise MappingError("git_blob_read", f"invalid object size: {header_text!r}") from exc
        payload = self.proc.stdout.read(size)
        delimiter = self.proc.stdout.read(1)
        if len(payload) != size or delimiter != b"\n":
            raise MappingError("git_blob_read", f"truncated git cat-file payload for {spec}")
        return oid, payload

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                if self.proc.stdin is not None:
                    self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                self.proc.kill()


class GitBatchLRU:
    def __init__(self, max_open: int = 4) -> None:
        self.max_open = max_open
        self.items: "OrderedDict[str, GitCatFileBatch]" = OrderedDict()

    def get(self, clone_path: Path) -> GitCatFileBatch:
        key = str(clone_path)
        if key in self.items:
            batch = self.items.pop(key)
            self.items[key] = batch
            return batch
        batch = GitCatFileBatch(clone_path)
        self.items[key] = batch
        while len(self.items) > self.max_open:
            _, old = self.items.popitem(last=False)
            old.close()
        return batch

    def close(self) -> None:
        for batch in self.items.values():
            batch.close()
        self.items.clear()


def resolve_clone_path(
    original: Path,
    prefix_from: str,
    prefix_to: str,
) -> Path:
    if original.is_dir():
        return original
    if prefix_from and prefix_to:
        original_text = str(original)
        if original_text == prefix_from or original_text.startswith(prefix_from.rstrip("/") + "/"):
            candidate = Path(prefix_to + original_text[len(prefix_from) :])
            if candidate.is_dir():
                return candidate
    return original


def load_snapshot_status(
    path: Path,
    prefix_from: str,
    prefix_to: str,
) -> dict[str, SnapshotStatus]:
    result: dict[str, SnapshotStatus] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        required = {"snapshot_key", "dataset_source", "repo_name", "commit_sha", "clone_path", "status"}
        missing = required - fields
        if missing:
            raise SystemExit(f"[ERROR] snapshot_status.csv missing columns: {sorted(missing)}")
        for row in reader:
            snapshot_id = clean(row.get("snapshot_key"))
            if not snapshot_id:
                raise SystemExit("[ERROR] snapshot_status.csv contains blank snapshot_key")
            if snapshot_id in result:
                raise SystemExit(f"[ERROR] duplicate snapshot_key in snapshot_status.csv: {snapshot_id}")
            original = Path(clean(row.get("clone_path"))).expanduser()
            effective = resolve_clone_path(original, prefix_from, prefix_to)
            result[snapshot_id] = SnapshotStatus(
                snapshot_id=snapshot_id,
                dataset_source=clean(row.get("dataset_source")),
                repo_name=clean(row.get("repo_name")),
                repo_key=clean(row.get("repo_key")),
                commit_sha=clean(row.get("commit_sha")).lower(),
                clone_path_original=original,
                clone_path_effective=effective,
                status=clean(row.get("status")),
            )
    return result


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"[ERROR] expected JSON object: {path}")
    return payload


def validate_a01_freeze(a01_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    summary_path = a01_root / "detector_freeze_summary.json"
    metadata_path = a01_root / "detector_freeze_metadata.json"
    if not summary_path.is_file() or not metadata_path.is_file():
        raise SystemExit(f"[ERROR] A01 freeze artifacts missing under {a01_root}")
    summary = load_json(summary_path)
    metadata = load_json(metadata_path)
    failures: list[str] = []
    if summary.get("status") != "PASS":
        failures.append(f"A01 status={summary.get('status')!r}, expected PASS")
    if int(summary.get("failed_hard_checks", -1)) != 0:
        failures.append("A01 failed_hard_checks is not zero")
    frozen = summary.get("frozen_detector_spec", {})
    if frozen != metadata.get("frozen_detector_spec", {}):
        failures.append("A01 summary/metadata frozen_detector_spec mismatch")
    expected = {
        "generation_source": "CodeLlama-7B",
        "classifier": "svm",
        "representation": "ast",
        "embedding_model_id": "Salesforce/codet5p-110m-embedding",
        "score_mode": "decision",
        "human_decision_threshold": 0.0,
        "agc_score_transform": "agc_score=-human_decision_score",
        "function_prediction_rule": "agc if human_decision_score < 0 else human",
    }
    for key, value in expected.items():
        if frozen.get(key) != value:
            failures.append(f"A01 frozen {key}={frozen.get(key)!r}, expected {value!r}")
    input_contract = frozen.get("downstream_function_input_contract", {})
    if input_contract.get("npr") != "function_body":
        failures.append("A01 NPR downstream input contract is not function_body")
    if input_contract.get("ml") != "full_standalone_function_source_to_ast_to_codet5plus_to_svm":
        failures.append("A01 ML downstream input contract mismatch")
    aggregation = frozen.get("prespecified_file_aggregation", {})
    expected_aggregation = {
        "weight": "function_body_literal_space_token_count",
        "metric": "file_ml_agc_share_space_by_token_weighted",
        "selection_rule": "file_ml_agc_share_space_by_token_weighted > 0.5",
        "unscored_function_policy": "exclude_from_denominator",
        "no_scored_function_file_policy": "NA_no_ml_fun_not_HWC",
    }
    for key, value in expected_aggregation.items():
        if aggregation.get(key) != value:
            failures.append(f"A01 file aggregation {key} mismatch")
    return summary, metadata, failures


def load_detector_parser(repo_root: Path, tree_sitter_lib: Path, ast_helper_dir: Path) -> DetectorParser:
    app_dir = repo_root / "src/app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    try:
        from agc_detector import (  # type: ignore
            extract_blocks,
            generate_ast_sequence,
            load_parser_and_F,
            strip_block_markers,
        )
    except Exception as exc:
        raise SystemExit(f"[ERROR] failed to import agc_detector parser helpers: {exc}") from exc
    parser, ast_function = load_parser_and_F(str(tree_sitter_lib), str(ast_helper_dir))
    return DetectorParser(
        parser=parser,
        ast_function=ast_function,
        extract_blocks=extract_blocks,
        generate_ast_sequence=generate_ast_sequence,
        strip_block_markers=strip_block_markers,
    )


def selected_row_fingerprint(rows: Sequence[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        payload = "\x1f".join(
            [
                clean(row.get("code_unit_id")),
                clean(row.get("file_sha256")),
                clean(row.get("code_unit_sha256")),
                clean(row.get("start_char_offset")),
                clean(row.get("end_char_offset")),
                clean(row.get("space_by_token_count")),
            ]
        )
        digest.update(payload.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def failure_row(row: dict[str, str], stage: str, exc: BaseException) -> dict[str, Any]:
    return {
        "snapshot_id": clean(row.get("snapshot_id")),
        "dataset_source": clean(row.get("dataset_source")),
        "repo_name": clean(row.get("repo_name")),
        "snapshot_commit": clean(row.get("snapshot_commit")),
        "relative_path": clean(row.get("relative_path")),
        "code_unit_id": clean(row.get("code_unit_id")),
        "qualified_name": clean(row.get("qualified_name")),
        "npr_body_sha256": clean(row.get("code_unit_sha256")),
        "stage": stage,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }


def map_occurrence(
    row: dict[str, str],
    payload: bytes,
    git_blob_oid: str,
    decoded_source: str,
    utf8_source: bytes,
    full_tree: Any,
    detector: DetectorParser,
    output_root: Path,
) -> dict[str, Any]:
    relative_path = validate_relative_python_path(clean(row.get("relative_path")))
    expected_file_sha = clean(row.get("file_sha256")).lower()
    if not FULL_SHA256_RE.fullmatch(expected_file_sha):
        raise MappingError("manifest_schema", f"invalid file_sha256: {expected_file_sha!r}")
    actual_file_sha = sha256_bytes(payload)
    if actual_file_sha != expected_file_sha:
        raise MappingError(
            "file_identity",
            f"historical Git blob file SHA mismatch: A05={expected_file_sha} actual={actual_file_sha}",
        )

    body_start = as_int(row.get("start_char_offset"), "start_char_offset")
    body_end = as_int(row.get("end_char_offset"), "end_char_offset")
    if not (0 <= body_start < body_end <= len(decoded_source)):
        raise MappingError(
            "body_boundary",
            f"invalid A05 body character range [{body_start}, {body_end}) for source length {len(decoded_source)}",
        )
    body_text = decoded_source[body_start:body_end]
    body_sha = sha256_text(body_text)
    expected_body_sha = clean(row.get("code_unit_sha256")).lower()
    if body_sha != expected_body_sha:
        raise MappingError(
            "body_identity",
            f"A05 body SHA mismatch after exact historical reconstruction: A05={expected_body_sha} actual={body_sha}",
        )
    expected_tokens = as_int(row.get("space_by_token_count"), "space_by_token_count")
    actual_tokens = len(body_text.split(" "))
    if actual_tokens != expected_tokens:
        raise MappingError(
            "body_identity",
            f"literal-space-token mismatch: A05={expected_tokens} reconstructed={actual_tokens}",
        )

    body_start_byte = char_offset_to_utf8_byte(decoded_source, body_start)
    body_end_byte = char_offset_to_utf8_byte(decoded_source, body_end)
    expected_name = leaf_function_name(clean(row.get("qualified_name")))
    if not expected_name:
        raise MappingError("manifest_schema", "cannot derive function name from qualified_name")

    function_node = enclosing_function_node(
        full_tree.root_node,
        utf8_source,
        body_start_byte,
        body_end_byte,
        expected_name,
    )
    actual_name = node_name(function_node, utf8_source)
    full_node, includes_decorators = full_definition_node(function_node)
    source_start = int(full_node.start_byte)
    source_end = int(full_node.end_byte)
    if not (0 <= source_start < source_end <= len(utf8_source)):
        raise MappingError("ml_source_boundary", "invalid tree-sitter full function byte range")
    raw_full_source = utf8_source[source_start:source_end].decode("utf-8", errors="strict")
    normalized_source = normalize_function_source(raw_full_source, detector.strip_block_markers)
    normalized_bytes = normalized_source.encode("utf-8")

    standalone_tree = detector.parser.parse(normalized_bytes)
    error_nodes, missing_nodes = count_tree_recovery_nodes(standalone_tree.root_node)
    blocks = detector.extract_blocks(normalized_source, detector.parser)
    if len(blocks) != 1:
        raise MappingError(
            "ml_input_compatibility",
            f"standalone source must contain exactly one detector block; found {len(blocks)}",
        )
    block = blocks[0]
    block_kind = clean(block.get("kind"))
    block_name = clean(block.get("name"))
    block_code = str(block.get("code", ""))
    if block_kind != "function_definition":
        raise MappingError(
            "ml_input_compatibility",
            f"standalone source resolved to block kind {block_kind!r}",
        )
    if block_name != expected_name:
        raise MappingError(
            "ml_input_compatibility",
            f"standalone block name {block_name!r} != expected {expected_name!r}",
        )
    covers = int(block_code.strip() == normalized_source.strip())
    if not covers:
        raise MappingError(
            "ml_input_compatibility",
            "tree-sitter block does not cover complete normalized standalone source",
        )
    ast_sequence = detector.generate_ast_sequence(
        block_code,
        detector.parser,
        detector.ast_function,
    )
    if not ast_sequence.strip():
        raise MappingError("ml_input_compatibility", "AST sequence is empty")

    source_sha, source_relative, _ = write_artifact(output_root, normalized_source)
    warning_parts: list[str] = []
    if tree_has_error(full_tree.root_node):
        warning_parts.append("full_file_tree_sitter_recovery")
    if tree_has_error(standalone_tree.root_node) or error_nodes or missing_nodes:
        warning_parts.append("standalone_tree_sitter_recovery")

    return {
        "snapshot_order": clean(row.get("snapshot_order")),
        "snapshot_id": clean(row.get("snapshot_id")),
        "dataset_source": clean(row.get("dataset_source")),
        "repo_name": clean(row.get("repo_name")),
        "repo_key": clean(row.get("repo_key")),
        "snapshot_time": clean(row.get("snapshot_time")),
        "snapshot_commit": clean(row.get("snapshot_commit")),
        "relative_path": relative_path,
        "file_sha256": expected_file_sha,
        "git_blob_oid": git_blob_oid,
        "code_unit_id": clean(row.get("code_unit_id")),
        "code_unit_type": clean(row.get("code_unit_type")),
        "aggregation_role": clean(row.get("aggregation_role")),
        "qualified_name": clean(row.get("qualified_name")),
        "function_name": expected_name,
        "function_kind": clean(row.get("function_kind")),
        "occurrence_index": clean(row.get("occurrence_index")),
        "npr_body_sha256": expected_body_sha,
        "npr_body_relative_path": clean(row.get("code_unit_relative_path")),
        "npr_body_start_line": clean(row.get("start_line")),
        "npr_body_end_line": clean(row.get("end_line")),
        "npr_body_start_char_offset": body_start,
        "npr_body_end_char_offset": body_end,
        "npr_body_character_count": clean(row.get("character_count")),
        "npr_body_utf8_byte_count": clean(row.get("utf8_byte_count")),
        "npr_body_physical_line_count": clean(row.get("physical_line_count")),
        "npr_body_space_by_token_count": expected_tokens,
        "file_sha256_verified": 1,
        "npr_body_sha256_verified": 1,
        "npr_body_space_by_token_count_verified": 1,
        "tree_sitter_function_name": actual_name,
        "tree_sitter_function_name_matches": int(actual_name == expected_name),
        "tree_sitter_full_file_has_error": int(tree_has_error(full_tree.root_node)),
        "tree_sitter_standalone_has_error": int(tree_has_error(standalone_tree.root_node)),
        "tree_sitter_standalone_error_nodes": error_nodes,
        "tree_sitter_standalone_missing_nodes": missing_nodes,
        "tree_sitter_blocks_found": len(blocks),
        "tree_sitter_block_kind": block_kind,
        "tree_sitter_block_name": block_name,
        "tree_sitter_block_covers_full_source": covers,
        "ml_ast_sequence_character_count": len(ast_sequence),
        "ml_ast_sequence_token_count": len(ast_sequence.split()),
        "ml_source_sha256": source_sha,
        "ml_source_relative_path": source_relative,
        "ml_source_character_count": len(normalized_source),
        "ml_source_utf8_byte_count": len(normalized_bytes),
        "ml_source_physical_line_count": count_physical_lines(normalized_source),
        "ml_source_start_byte_utf8": source_start,
        "ml_source_end_byte_utf8": source_end,
        "ml_source_includes_decorators": int(includes_decorators),
        "ml_source_normalization": "strip_block_markers_then_textwrap_dedent_strip_plus_lf",
        "tree_sitter_occurrence_mapping": "verified_A05_body_start_anchor_with_trailing_trivia_tolerant_end",
        "mapping_status": "PASS",
        "mapping_warning": ";".join(warning_parts),
    }


def group_rows_by_file(rows: Sequence[dict[str, str]]) -> Iterator[tuple[str, list[dict[str, str]]]]:
    current_path: str | None = None
    current_rows: list[dict[str, str]] = []
    for row in rows:
        path = clean(row.get("relative_path"))
        if current_path is None:
            current_path = path
        if path != current_path:
            yield current_path, current_rows
            current_path = path
            current_rows = []
        current_rows.append(row)
    if current_path is not None:
        yield current_path, current_rows


def chunk_is_reusable(
    chunk_dir: Path,
    input_fingerprint: str,
    a01_metadata_sha: str,
    a05_manifest_sha: str,
) -> bool:
    summary_path = chunk_dir / "summary.json"
    occurrences_path = chunk_dir / "occurrences.csv"
    failures_path = chunk_dir / "failures.csv"
    if not (summary_path.is_file() and occurrences_path.is_file() and failures_path.is_file()):
        return False
    try:
        summary = load_json(summary_path)
    except Exception:
        return False
    return bool(
        summary.get("status") in {"PASS", "PASS_WITH_WARNINGS"}
        and summary.get("script_version") == SCRIPT_VERSION
        and summary.get("selected_input_fingerprint") == input_fingerprint
        and summary.get("a01_metadata_sha256") == a01_metadata_sha
        and summary.get("a05_code_unit_manifest_sha256") == a05_manifest_sha
        and int(summary.get("failed_occurrences", -1)) == 0
    )


def process_snapshot(
    rows: Sequence[dict[str, str]],
    snapshot_status: SnapshotStatus,
    detector: DetectorParser,
    output_root: Path,
    git_pool: GitBatchLRU,
    a01_metadata_sha: str,
    a05_manifest_sha: str,
    resume: bool,
) -> dict[str, Any]:
    snapshot_id = snapshot_status.snapshot_id
    chunk_dir = output_root / "snapshot_chunks" / snapshot_id
    fingerprint = selected_row_fingerprint(rows)
    if resume and chunk_is_reusable(
        chunk_dir,
        fingerprint,
        a01_metadata_sha,
        a05_manifest_sha,
    ):
        summary = load_json(chunk_dir / "summary.json")
        summary["reused"] = True
        return summary

    if chunk_dir.exists():
        shutil.rmtree(chunk_dir)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    occurrence_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    warnings = 0
    files_processed = 0
    unique_sources: set[str] = set()

    if snapshot_status.status != "success":
        raise MappingError(
            "snapshot_status",
            f"A05 snapshot status is {snapshot_status.status!r}, expected success",
        )
    if not snapshot_status.clone_path_effective.is_dir():
        raise MappingError(
            "clone_path",
            "A05 clone path is not accessible. Original="
            f"{snapshot_status.clone_path_original} effective={snapshot_status.clone_path_effective}. "
            "Use --clone-path-prefix-from/--clone-path-prefix-to when the clone tree was mirrored.",
        )

    batch = git_pool.get(snapshot_status.clone_path_effective)
    for relative_path, file_rows in group_rows_by_file(rows):
        files_processed += 1
        try:
            commit = clean(file_rows[0].get("snapshot_commit")).lower()
            if commit != snapshot_status.commit_sha:
                raise MappingError(
                    "snapshot_identity",
                    f"code-unit commit {commit} != snapshot_status commit {snapshot_status.commit_sha}",
                )
            if clean(file_rows[0].get("repo_name")) != snapshot_status.repo_name:
                raise MappingError("snapshot_identity", "repository identity mismatch")
            git_blob_oid, payload = batch.read_blob(commit, relative_path)
            decoded_source, _ = decode_python_source(payload)
            utf8_source = decoded_source.encode("utf-8")
            full_tree = detector.parser.parse(utf8_source)
            for row in file_rows:
                try:
                    mapped = map_occurrence(
                        row,
                        payload,
                        git_blob_oid,
                        decoded_source,
                        utf8_source,
                        full_tree,
                        detector,
                        output_root,
                    )
                    occurrence_rows.append(mapped)
                    unique_sources.add(str(mapped["ml_source_sha256"]))
                    if mapped.get("mapping_warning"):
                        warnings += 1
                except Exception as exc:
                    stage = exc.stage if isinstance(exc, MappingError) else "occurrence_map"
                    failures.append(failure_row(row, stage, exc))
        except Exception as exc:
            stage = exc.stage if isinstance(exc, MappingError) else "file_prepare"
            for row in file_rows:
                failures.append(failure_row(row, stage, exc))

    occurrence_path = chunk_dir / "occurrences.csv"
    failures_path = chunk_dir / "failures.csv"
    atomic_write_csv(occurrence_path, occurrence_rows, OCCURRENCE_COLUMNS)
    atomic_write_csv(failures_path, failures, FAILURE_COLUMNS)
    status = "FAIL" if failures else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    summary = {
        "script_version": SCRIPT_VERSION,
        "status": status,
        "snapshot_id": snapshot_id,
        "dataset_source": snapshot_status.dataset_source,
        "repo_name": snapshot_status.repo_name,
        "snapshot_commit": snapshot_status.commit_sha,
        "selected_occurrences": len(rows),
        "mapped_occurrences": len(occurrence_rows),
        "failed_occurrences": len(failures),
        "warning_occurrences": warnings,
        "files_processed": files_processed,
        "unique_ml_sources": len(unique_sources),
        "selected_input_fingerprint": fingerprint,
        "a01_metadata_sha256": a01_metadata_sha,
        "a05_code_unit_manifest_sha256": a05_manifest_sha,
        "clone_path_original": str(snapshot_status.clone_path_original),
        "clone_path_effective": str(snapshot_status.clone_path_effective),
        "created_at_utc": utc_now(),
        "reused": False,
    }
    atomic_write_json(chunk_dir / "summary.json", summary)
    return summary


def concatenate_chunks(
    selected_snapshot_ids: Sequence[str],
    output_root: Path,
    relative_name: str,
    output_path: Path,
    columns: Sequence[str],
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp = output_path.with_name(output_path.name + f".tmp.{os.getpid()}")
    count = 0
    with temp.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for snapshot_id in selected_snapshot_ids:
            source = output_root / "snapshot_chunks" / snapshot_id / relative_name
            if not source.is_file():
                continue
            with source.open("r", encoding="utf-8", newline="") as inp:
                reader = csv.DictReader(inp)
                for row in reader:
                    writer.writerow({key: row.get(key, "") for key in columns})
                    count += 1
    os.replace(temp, output_path)
    return count


def build_unique_source_manifest(occurrence_path: Path, output_path: Path) -> int:
    summaries: dict[str, dict[str, Any]] = {}
    with occurrence_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_sha = clean(row.get("ml_source_sha256"))
            if not source_sha:
                continue
            item = summaries.get(source_sha)
            if item is None:
                item = {
                    "ml_source_sha256": source_sha,
                    "ml_source_relative_path": clean(row.get("ml_source_relative_path")),
                    "occurrence_count": 0,
                    "first_dataset_source": clean(row.get("dataset_source")),
                    "first_repo_name": clean(row.get("repo_name")),
                    "first_snapshot_id": clean(row.get("snapshot_id")),
                    "first_snapshot_commit": clean(row.get("snapshot_commit")),
                    "first_relative_path": clean(row.get("relative_path")),
                    "first_code_unit_id": clean(row.get("code_unit_id")),
                    "first_qualified_name": clean(row.get("qualified_name")),
                    "function_name": clean(row.get("function_name")),
                    "function_kind": clean(row.get("function_kind")),
                    "ml_source_character_count": clean(row.get("ml_source_character_count")),
                    "ml_source_utf8_byte_count": clean(row.get("ml_source_utf8_byte_count")),
                    "ml_source_physical_line_count": clean(row.get("ml_source_physical_line_count")),
                    "ml_ast_sequence_character_count": clean(row.get("ml_ast_sequence_character_count")),
                    "ml_ast_sequence_token_count": clean(row.get("ml_ast_sequence_token_count")),
                    "any_tree_sitter_standalone_warning": 0,
                }
                summaries[source_sha] = item
            item["occurrence_count"] = int(item["occurrence_count"]) + 1
            if clean(row.get("mapping_warning")):
                item["any_tree_sitter_standalone_warning"] = 1
    ordered = [summaries[key] for key in sorted(summaries)]
    atomic_write_csv(output_path, ordered, UNIQUE_SOURCE_COLUMNS)
    return len(ordered)


def verify_artifacts(occurrence_path: Path, output_root: Path) -> int:
    checked: set[str] = set()
    failures = 0
    with occurrence_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_sha = clean(row.get("ml_source_sha256"))
            if not source_sha or source_sha in checked:
                continue
            checked.add(source_sha)
            path = output_root / clean(row.get("ml_source_relative_path"))
            if not path.is_file() or sha256_file(path) != source_sha:
                failures += 1
    return failures


def verify_existing_output(output_root: Path, expected_occurrences: int, expected_unique_body_sha: int) -> int:
    summary_path = output_root / "summary.json"
    checks_path = output_root / "checks.csv"
    occurrences_path = output_root / "python_ml_fun_occurrence_manifest.csv"
    unique_path = output_root / "python_ml_fun_unique_source_manifest.csv"
    failures_path = output_root / "python_ml_fun_mapping_failures.csv"
    required = [summary_path, checks_path, occurrences_path, unique_path, failures_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        print("A02 output verification: FAIL", file=sys.stderr)
        print(f"[ERROR] missing outputs: {missing}", file=sys.stderr)
        return 1
    summary = load_json(summary_path)
    failures: list[str] = []
    if summary.get("status") not in {"PASS", "PASS_WITH_WARNINGS"}:
        failures.append(f"status={summary.get('status')!r}")
    if int(summary.get("failed_hard_checks", -1)) != 0:
        failures.append("failed_hard_checks != 0")
    if expected_occurrences > 0 and int(summary.get("selected_occurrences", -1)) != expected_occurrences:
        failures.append("selected_occurrences mismatch")
    if expected_unique_body_sha > 0 and int(summary.get("unique_npr_body_sha", -1)) != expected_unique_body_sha:
        failures.append("unique_npr_body_sha mismatch")
    if int(summary.get("mapping_failures", -1)) != 0:
        failures.append("mapping_failures != 0")
    if int(summary.get("selected_occurrences", -1)) != int(summary.get("mapped_occurrences", -2)):
        failures.append("selected/mapped occurrence mismatch")
    with checks_path.open("r", encoding="utf-8", newline="") as handle:
        checks = list(csv.DictReader(handle))
    bad = [row for row in checks if clean(row.get("severity")) == "hard" and clean(row.get("passed")) != "1"]
    if bad:
        failures.append(f"{len(bad)} hard checks failed")
    if failures:
        print("A02 output verification: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"[ERROR] {failure}", file=sys.stderr)
        return 1
    print("A02 output verification: PASS")
    print(f"Status:                    {summary['status']}")
    print(f"Selected occurrences:      {summary['selected_occurrences']}")
    print(f"Mapped occurrences:        {summary['mapped_occurrences']}")
    print(f"Unique NPR body SHA:       {summary['unique_npr_body_sha']}")
    print(f"Unique ML source SHA:      {summary['unique_ml_source_sha']}")
    print(f"Warning occurrences:       {summary['warning_occurrences']}")
    print(f"Mapping failures:          {summary['mapping_failures']}")
    print(f"Failed hard checks:        {summary['failed_hard_checks']}")
    return 0


def run_pipeline(args: argparse.Namespace) -> int:
    started = time.time()
    repo_root = args.repo_root.resolve()
    a01_root = args.a01_root.resolve()
    a05_root = args.a05_root.resolve()
    output_root = args.output_root.resolve()

    a01_summary, a01_metadata, a01_failures = validate_a01_freeze(a01_root)
    if a01_failures:
        raise SystemExit("[ERROR] A01 freeze validation failed:\n  - " + "\n  - ".join(a01_failures))

    snapshot_status_path = a05_root / "snapshot_status.csv"
    code_manifest_path = a05_root / "python_code_unit_manifest.csv"
    for path in [snapshot_status_path, code_manifest_path]:
        if not path.is_file():
            raise SystemExit(f"[ERROR] required A05 input not found: {path}")

    a01_summary_sha = sha256_file(a01_root / "detector_freeze_summary.json")
    a01_metadata_sha = sha256_file(a01_root / "detector_freeze_metadata.json")
    a05_status_sha = sha256_file(snapshot_status_path)
    a05_manifest_sha = sha256_file(code_manifest_path)

    statuses = load_snapshot_status(
        snapshot_status_path,
        args.clone_path_prefix_from,
        args.clone_path_prefix_to,
    )
    detector = load_detector_parser(repo_root, args.tree_sitter_lib, args.ast_helper_dir)

    if output_root.exists() and args.overwrite:
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "snapshot_chunks").mkdir(parents=True, exist_ok=True)
    (output_root / "ml_function_sources").mkdir(parents=True, exist_ok=True)

    selected_occurrences = 0
    unique_body_sha: set[str] = set()
    selected_snapshot_ids: list[str] = []
    selected_snapshot_set: set[str] = set()
    current_snapshot: str | None = None
    current_rows: list[dict[str, str]] = []
    snapshot_summaries: list[dict[str, Any]] = []
    git_pool = GitBatchLRU(max_open=args.max_open_git_processes)

    def flush_snapshot() -> None:
        nonlocal current_snapshot, current_rows
        if current_snapshot is None or not current_rows:
            current_rows = []
            return
        status = statuses.get(current_snapshot)
        if status is None:
            raise SystemExit(f"[ERROR] selected A05 snapshot_id missing from snapshot_status.csv: {current_snapshot}")
        summary = process_snapshot(
            current_rows,
            status,
            detector,
            output_root,
            git_pool,
            a01_metadata_sha,
            a05_manifest_sha,
            args.resume,
        )
        snapshot_summaries.append(summary)
        print(
            f"[snapshot] {len(snapshot_summaries)} id={current_snapshot[:12]} "
            f"repo={status.repo_name} selected={summary['selected_occurrences']} "
            f"mapped={summary['mapped_occurrences']} failures={summary['failed_occurrences']} "
            f"warnings={summary['warning_occurrences']} reused={summary.get('reused', False)}",
            flush=True,
        )
        current_rows = []

    try:
        with code_manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            required = {
                "snapshot_order",
                "snapshot_id",
                "dataset_source",
                "repo_name",
                "repo_key",
                "snapshot_time",
                "snapshot_commit",
                "relative_path",
                "file_sha256",
                "code_unit_id",
                "code_unit_type",
                "aggregation_role",
                "qualified_name",
                "function_kind",
                "occurrence_index",
                "start_line",
                "end_line",
                "start_char_offset",
                "end_char_offset",
                "code_unit_sha256",
                "code_unit_relative_path",
                "character_count",
                "utf8_byte_count",
                "physical_line_count",
                "space_by_token_count",
            }
            missing = required - fields
            if missing:
                raise SystemExit(f"[ERROR] A05 code-unit manifest missing columns: {sorted(missing)}")

            for row in reader:
                if clean(row.get("aggregation_role")) != args.aggregation_role:
                    continue
                if clean(row.get("code_unit_type")) != args.unit_type:
                    continue
                if args.unit_type == PRIMARY_UNIT_TYPE and "method" in clean(row.get("function_kind")):
                    raise SystemExit(
                        "[ERROR] primary function_body row unexpectedly has method-like function_kind: "
                        f"{row.get('code_unit_id')} {row.get('function_kind')}"
                    )
                selected_occurrences += 1
                body_sha = clean(row.get("code_unit_sha256")).lower()
                if not FULL_SHA256_RE.fullmatch(body_sha):
                    raise SystemExit(f"[ERROR] invalid code_unit_sha256 at selected row {selected_occurrences}")
                unique_body_sha.add(body_sha)
                snapshot_id = clean(row.get("snapshot_id"))
                if current_snapshot is None:
                    current_snapshot = snapshot_id
                if snapshot_id != current_snapshot:
                    flush_snapshot()
                    current_snapshot = snapshot_id
                if snapshot_id not in selected_snapshot_set:
                    selected_snapshot_set.add(snapshot_id)
                    selected_snapshot_ids.append(snapshot_id)
                current_rows.append(dict(row))
                if args.max_occurrences > 0 and selected_occurrences >= args.max_occurrences:
                    break
            flush_snapshot()
    finally:
        git_pool.close()

    occurrence_path = output_root / "python_ml_fun_occurrence_manifest.csv"
    failure_path = output_root / "python_ml_fun_mapping_failures.csv"
    unique_path = output_root / "python_ml_fun_unique_source_manifest.csv"
    mapped_occurrences = concatenate_chunks(
        selected_snapshot_ids,
        output_root,
        "occurrences.csv",
        occurrence_path,
        OCCURRENCE_COLUMNS,
    )
    mapping_failures = concatenate_chunks(
        selected_snapshot_ids,
        output_root,
        "failures.csv",
        failure_path,
        FAILURE_COLUMNS,
    )
    unique_ml_sources = build_unique_source_manifest(occurrence_path, unique_path)
    artifact_integrity_failures = verify_artifacts(occurrence_path, output_root)

    warning_occurrences = sum(int(item.get("warning_occurrences", 0)) for item in snapshot_summaries)
    reused_snapshots = sum(bool(item.get("reused")) for item in snapshot_summaries)
    files_processed = sum(int(item.get("files_processed", 0)) for item in snapshot_summaries)
    mapped_from_summaries = sum(int(item.get("mapped_occurrences", 0)) for item in snapshot_summaries)
    failed_from_summaries = sum(int(item.get("failed_occurrences", 0)) for item in snapshot_summaries)

    full_run = args.max_occurrences <= 0
    checks: list[dict[str, Any]] = []
    add_check(checks, "a01_freeze_status", "hard", a01_summary.get("status") == "PASS", a01_summary.get("status"), "PASS")
    add_check(checks, "a01_freeze_failed_hard_checks", "hard", int(a01_summary.get("failed_hard_checks", -1)) == 0, a01_summary.get("failed_hard_checks"), 0)
    add_check(checks, "a05_snapshot_status_rows", "hard", len(statuses) == EXPECTED_SNAPSHOTS if full_run else len(statuses) >= 1, len(statuses), EXPECTED_SNAPSHOTS if full_run else ">=1")
    add_check(checks, "selected_unit_type", "hard", args.unit_type == PRIMARY_UNIT_TYPE, args.unit_type, PRIMARY_UNIT_TYPE, "run-x-a02-v2 is pinned to FUN for direct NPR/ML comparison")
    add_check(checks, "selected_aggregation_role", "hard", args.aggregation_role == PRIMARY_AGGREGATION_ROLE, args.aggregation_role, PRIMARY_AGGREGATION_ROLE)
    add_check(checks, "selected_occurrence_count", "hard", selected_occurrences == args.expected_occurrences if full_run else selected_occurrences > 0, selected_occurrences, args.expected_occurrences if full_run else ">0")
    add_check(checks, "unique_npr_body_sha", "hard", len(unique_body_sha) == args.expected_unique_body_sha if full_run else len(unique_body_sha) > 0, len(unique_body_sha), args.expected_unique_body_sha if full_run else ">0")
    add_check(checks, "mapped_occurrences_match_selected", "hard", mapped_occurrences == selected_occurrences, mapped_occurrences, selected_occurrences)
    add_check(checks, "mapping_failures_zero", "hard", mapping_failures == 0, mapping_failures, 0)
    add_check(checks, "chunk_mapping_reconciliation", "hard", mapped_from_summaries == mapped_occurrences and failed_from_summaries == mapping_failures, f"mapped={mapped_from_summaries};failed={failed_from_summaries}", f"mapped={mapped_occurrences};failed={mapping_failures}")
    add_check(checks, "artifact_integrity_failures", "hard", artifact_integrity_failures == 0, artifact_integrity_failures, 0)
    add_check(checks, "unique_ml_sources_positive", "hard", unique_ml_sources > 0, unique_ml_sources, ">0")
    add_check(checks, "tree_sitter_recovery_warnings", "warning", warning_occurrences == 0, warning_occurrences, 0, "Recovery nodes are diagnostic if occurrence identity and standalone AST generation succeeded.")

    failed_hard = [row for row in checks if row["severity"] == "hard" and int(row["passed"]) == 0]
    failed_warning = [row for row in checks if row["severity"] == "warning" and int(row["passed"]) == 0]
    status = "FAIL" if failed_hard else ("PASS_WITH_WARNINGS" if failed_warning else "PASS")
    elapsed = time.time() - started

    summary = {
        "run": SCRIPT_VERSION,
        "status": status,
        "failed_hard_checks": len(failed_hard),
        "failed_warning_checks": len(failed_warning),
        "full_run": full_run,
        "max_occurrences": args.max_occurrences,
        "unit_type": args.unit_type,
        "aggregation_role": args.aggregation_role,
        "selected_occurrences": selected_occurrences,
        "mapped_occurrences": mapped_occurrences,
        "mapping_failures": mapping_failures,
        "unique_npr_body_sha": len(unique_body_sha),
        "unique_ml_source_sha": unique_ml_sources,
        "selected_snapshots": len(selected_snapshot_ids),
        "files_processed": files_processed,
        "warning_occurrences": warning_occurrences,
        "artifact_integrity_failures": artifact_integrity_failures,
        "reused_snapshot_chunks": reused_snapshots,
        "expected_full_fun_occurrences": args.expected_occurrences,
        "expected_full_unique_fun_body_sha": args.expected_unique_body_sha,
        "elapsed_seconds": elapsed,
        "output_root": str(output_root),
        "created_at_utc": utc_now(),
    }
    metadata = {
        "run": SCRIPT_VERSION,
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "python": sys.version,
        "inputs": {
            "a01_root": str(a01_root),
            "a01_summary_sha256": a01_summary_sha,
            "a01_metadata_sha256": a01_metadata_sha,
            "a01_model_pickle_sha256": clean(a01_metadata.get("inputs", {}).get("model_pickle_sha256")),
            "a01_analyzer_script_sha256": clean(a01_metadata.get("inputs", {}).get("analyzer_script_sha256")),
            "a05_root": str(a05_root),
            "a05_snapshot_status_sha256": a05_status_sha,
            "a05_code_unit_manifest_sha256": a05_manifest_sha,
            "tree_sitter_lib": str(args.tree_sitter_lib.resolve()),
            "tree_sitter_lib_sha256": sha256_file(args.tree_sitter_lib),
        },
        "equality_contract": [
            "same_repository",
            "same_historical_commit",
            "same_python_file",
            "same_a05_primary_function_body_occurrence",
        ],
        "npr_input": "exact_A05_function_body_source_slice",
        "ml_input": "normalized_full_standalone_function_source_to_AST",
        "ml_source_normalization": "strip_block_markers_then_textwrap_dedent_strip_plus_lf",
        "tree_sitter_occurrence_mapping": "verified_A05_body_start_anchor_with_trailing_trivia_tolerant_end",
        "file_aggregation_weight_for_downstream": "A05 function_body space_by_token_count",
        "prespecified_file_selection_rule": "file_ml_agc_share_space_by_token_weighted > 0.5",
        "scope_note": "run-x-a02-v2 uses primary function_body only to match the current FUN NPR quality DiD; C_FUN is a later prespecified extension",
        "clone_path_prefix_from": args.clone_path_prefix_from,
        "clone_path_prefix_to": args.clone_path_prefix_to,
        "created_at_utc": utc_now(),
    }

    atomic_write_csv(output_root / "checks.csv", checks, CHECK_COLUMNS)
    atomic_write_json(output_root / "summary.json", summary)
    atomic_write_json(output_root / "metadata.json", metadata)

    print("=" * 80)
    print("run-x-a02 ML FUN input preparation")
    print(f"Status:                              {status}")
    print(f"Selected A05 FUN occurrences:       {selected_occurrences}")
    print(f"Mapped ML function occurrences:     {mapped_occurrences}")
    print(f"Mapping failures:                   {mapping_failures}")
    print(f"Unique NPR body SHA:                {len(unique_body_sha)}")
    print(f"Unique ML standalone source SHA:    {unique_ml_sources}")
    print(f"Selected snapshots:                 {len(selected_snapshot_ids)}")
    print(f"Historical Python files processed:  {files_processed}")
    print(f"Tree-sitter warning occurrences:    {warning_occurrences}")
    print(f"Reused snapshot chunks:             {reused_snapshots}")
    print(f"Failed hard checks:                 {len(failed_hard)}")
    print(f"Elapsed seconds:                    {elapsed:.3f}")
    print(f"Output root:                        {output_root}")
    print("=" * 80)
    return 0 if not failed_hard else 5


def run_self_test() -> int:
    # This structural self-test intentionally uses only the Python standard
    # library. Production tree-sitter compatibility is exercised by smoke/full
    # mode against the actual frozen detector parser.
    source = (
        "@decorator\n"
        "def f(x):\n"
        "    \"\"\"Doc.\"\"\"\n"
        "\n"
        "    # keep comment\n"
        "    y = x + 1\n"
        "    return y\n"
    )
    tree = ast.parse(source)
    node = tree.body[0]
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise SystemExit("[ERROR] self-test did not parse function")
    raw = source
    normalized = textwrap.dedent(raw).strip() + "\n"
    if not normalized.startswith("@decorator\ndef f(x):"):
        raise SystemExit("[ERROR] self-test standalone normalization failed")
    if leaf_function_name("f") != "f" or leaf_function_name("A.f") != "f":
        raise SystemExit("[ERROR] self-test leaf function name failed")
    body_text = "\n    # keep comment\n    y = x + 1\n    return y\n"
    if len(body_text.split(" ")) <= 0 or not FULL_SHA256_RE.fullmatch(sha256_text(body_text)):
        raise SystemExit("[ERROR] self-test body hash/token helpers failed")
    class FakeNode:
        def __init__(self, node_type: str, start: int, end: int, name: str = "", children: list[Any] | None = None) -> None:
            self.type = node_type
            self.start_byte = start
            self.end_byte = end
            self.children = children or []
            self.parent = None
            self._name = name
            for child in self.children:
                child.parent = self

        def child_by_field_name(self, field: str) -> Any:
            if field != "name" or not self._name:
                return None
            name_start = source.encode("utf-8").find(self._name.encode("utf-8"), self.start_byte)
            return FakeNode("identifier", name_start, name_start + len(self._name.encode("utf-8")))

    source_utf8 = source.encode("utf-8")
    function_start = source_utf8.find(b"def f")
    # Regression for production smoke failure: A05 body_end includes the final
    # physical line terminator, while tree-sitter's syntactic function node can
    # end immediately before that newline. Mapping must still succeed.
    function_syntax_end = len(source_utf8.rstrip(b"\n"))
    function_node = FakeNode("function_definition", function_start, function_syntax_end, "f")
    decorated_node = FakeNode("decorated_definition", 0, function_syntax_end, children=[function_node])
    root_node = FakeNode("module", 0, len(source_utf8), children=[decorated_node])
    body_start_byte = source_utf8.find(b"    # keep comment")
    mapped = enclosing_function_node(root_node, source_utf8, body_start_byte, len(source_utf8), "f")
    if mapped is not function_node:
        raise SystemExit("[ERROR] self-test tree occurrence mapping failed")
    full_node, includes_decorators = full_definition_node(mapped)
    if full_node is not decorated_node or not includes_decorators:
        raise SystemExit("[ERROR] self-test decorated definition expansion failed")

    with tempfile.TemporaryDirectory(prefix="run-x-a02-selftest-") as tmp:
        root = Path(tmp)
        digest, relative, reused = write_artifact(root, normalized)
        if reused:
            raise SystemExit("[ERROR] self-test first artifact write unexpectedly reused")
        if sha256_file(root / relative) != digest:
            raise SystemExit("[ERROR] self-test artifact integrity failed")
        digest2, relative2, reused2 = write_artifact(root, normalized)
        if digest2 != digest or relative2 != relative or not reused2:
            raise SystemExit("[ERROR] self-test artifact reuse failed")

        git_root = root / "git-repo"
        git_root.mkdir()
        subprocess.run(["git", "init", "-q", str(git_root)], check=True)
        subprocess.run(["git", "-C", str(git_root), "config", "user.email", "selftest@example.com"], check=True)
        subprocess.run(["git", "-C", str(git_root), "config", "user.name", "A02 Self Test"], check=True)
        (git_root / "a.py").write_text(source, encoding="utf-8")
        subprocess.run(["git", "-C", str(git_root), "add", "a.py"], check=True)
        subprocess.run(["git", "-C", str(git_root), "commit", "-q", "-m", "selftest"], check=True)
        commit = subprocess.check_output(["git", "-C", str(git_root), "rev-parse", "HEAD"], text=True).strip()
        batch = GitCatFileBatch(git_root)
        try:
            oid, payload = batch.read_blob(commit, "a.py")
        finally:
            batch.close()
        if not oid or payload != source.encode("utf-8"):
            raise SystemExit("[ERROR] self-test git cat-file batch failed")
    print("prepare_ml_fun_inputs self-test: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--a01-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a01")
    parser.add_argument("--a05-root", type=Path)
    parser.add_argument("--output-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a02")
    parser.add_argument("--tree-sitter-lib", type=Path, default=repo_root / "src/code-analyzer-tree-sitter/build/my-languages.so")
    parser.add_argument("--ast-helper-dir", type=Path, default=repo_root / "src/code-analyzer-tree-sitter")
    parser.add_argument("--unit-type", default=PRIMARY_UNIT_TYPE)
    parser.add_argument("--aggregation-role", default=PRIMARY_AGGREGATION_ROLE)
    parser.add_argument("--expected-occurrences", type=int, default=EXPECTED_FUN_OCCURRENCES)
    parser.add_argument("--expected-unique-body-sha", type=int, default=EXPECTED_UNIQUE_FUN_BODY_SHA)
    parser.add_argument("--max-occurrences", type=int, default=0)
    parser.add_argument("--max-open-git-processes", type=int, default=4)
    parser.add_argument("--clone-path-prefix-from", default="")
    parser.add_argument("--clone-path-prefix-to", default="")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-output", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    if args.verify_output:
        return verify_existing_output(
            args.output_root.resolve(),
            args.expected_occurrences if args.max_occurrences <= 0 else 0,
            args.expected_unique_body_sha if args.max_occurrences <= 0 else 0,
        )
    if args.a05_root is None:
        parser.error("--a05-root is required for preparation")
    if args.max_occurrences < 0:
        parser.error("--max-occurrences cannot be negative")
    if args.max_open_git_processes < 1:
        parser.error("--max-open-git-processes must be >= 1")
    for path, label in [
        (args.tree_sitter_lib, "tree-sitter language library"),
        (args.ast_helper_dir, "AST helper directory"),
    ]:
        if not path.exists():
            parser.error(f"{label} not found: {path}")
    return run_pipeline(args)


if __name__ == "__main__":
    raise SystemExit(main())
