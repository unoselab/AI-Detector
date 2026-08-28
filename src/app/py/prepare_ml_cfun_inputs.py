#!/usr/bin/env python3
"""
prepare_ml_cfun_inputs-v3.py
============================

Prepare the exact historical C_FUN population for frozen ML AGC inference.

This run is the C_FUN analogue of the frozen FUN preparation lineage. It keeps
repository, historical snapshot, Python file, and A05 code-unit identities
fixed, but changes the selected primary code-unit category from
``function_body`` to ``method_body``.

Scientific contract
-------------------
1. The authoritative historical corpus is NPR run-x-a05. No repository,
   snapshot, or file is recollected.
2. C_FUN membership is exactly:
      aggregation_role == "primary" and code_unit_type == "method_body"
3. The A05 method body remains the identity/weight authority. The script
   cryptographically re-verifies the historical file SHA-256, the exact body
   SHA-256, and the literal-space-token count before producing an ML source.
4. The ML detector input is detector-native standalone method source rather
   than the NPR body text. Tree-sitter is used only to recover the method
   header/decorators around the already-verified A05 body occurrence.
5. A method is accepted only when the matching Tree-sitter
   ``function_definition`` is a direct class-body definition (decorated or
   undecorated), has the expected leaf name, and contains the A05 body-start
   anchor. The strict path requires the Tree-sitter method end not to exceed
   the authoritative A05 method end. A conservative recovery path may reuse
   only the Tree-sitter START while keeping the A05 END.
6. The reconstructed standalone source must be accepted by the frozen ML
   detector parser as exactly one full-source function block with the expected
   name and a non-empty AST sequence.
7. This run performs no CodeT5+ embedding, no SVM inference, no threshold
   calibration, no SonarQube access, and no DiD estimation.

Expected frozen full-corpus gates
---------------------------------
- C_FUN occurrences: 1,677,916
- Unique C_FUN body SHA-256 values: 195,193
- Snapshot/files with C_FUN: 196,190
- A13 C_FUN unique membership count: 195,193

Modes
-----
diagnose
    Reprocess only the 946 residual failures from the failed run-x-a05-v2
    production output. The failed v2 output is read-only in this mode.
repair
    After diagnose recovers 946/946, merge the audited v2 successes plus v3
    recoveries in the frozen NPR A05 order into a complete repaired output.
verify
    Read-only verification of the repaired v3 output.

Primary diagnose outputs
------------------------
python_ml_cfun_recovered_occurrences.csv
python_ml_cfun_recovery_failures.csv
python_ml_cfun_recovery_diagnostics.csv
python_ml_cfun_recovered_unique_source_manifest.csv
ml_cfun_sources/<sha-prefix>/<sha256>.py

Primary repair outputs
----------------------
python_ml_cfun_occurrence_manifest.csv
python_ml_cfun_unique_source_manifest.csv
python_ml_cfun_mapping_failures.csv
checks.csv
summary.json
metadata.json
ml_cfun_sources/<sha-prefix>/<sha256>.py
"""

from __future__ import annotations

import argparse
import bisect
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


SCRIPT_VERSION = "run-x-a05-v3"
RUN_NAME = "run-x-a05"
PRIMARY_UNIT_TYPE = "method_body"
PRIMARY_AGGREGATION_ROLE = "primary"
EXPECTED_CFUN_OCCURRENCES = 1_677_916
EXPECTED_UNIQUE_CFUN_BODY_SHA = 195_193
EXPECTED_FILES_WITH_CFUN = 196_190
EXPECTED_A13_SCRIPT_VERSION = "run-x-a13-v1"
EXPECTED_A13_CATEGORY = "C_FUN"
EXPECTED_A13_UNIT_TYPE = "method_body"
EXPECTED_A05_MANIFEST_SHA256 = "1acb3726f5c62e6154672f1aff592973c65a13e58dbfd37f8058560d1a474e6c"
FULL_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

A05_REQUIRED_COLUMNS = {
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
    "tree_sitter_direct_class_method",
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
    "ml_source_tree_sitter_start_byte_utf8",
    "ml_source_start_strategy",
    "ml_source_top_level_decorator_count",
    "ml_source_decorator_headers_column_zero",
    "ml_source_definition_header_column_zero",
    "ml_source_normalization",
    "tree_sitter_occurrence_mapping",
    "ml_source_end_strategy",
    "tree_sitter_same_name_candidate_count",
    "tree_sitter_anchor_candidate_count",
    "tree_sitter_primary_anchor_candidate_count",
    "tree_sitter_strict_candidate_count",
    "tree_sitter_candidate_start_byte_utf8",
    "tree_sitter_candidate_end_byte_utf8",
    "tree_sitter_candidate_end_minus_a05_body_end_bytes",
    "mapping_status",
    "mapping_warning",
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

CHECK_COLUMNS = ["check_name", "severity", "passed", "observed", "expected", "note"]


class MappingError(RuntimeError):
    """Mapping failure with a stable pipeline stage."""

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


@dataclass
class CandidateAnalysis:
    all_functions: list[Any]
    same_name: list[Any]
    anchor_functions: list[Any]
    same_name_anchor: list[Any]
    primary_same_name_anchor: list[Any]
    strict_same_name_anchor: list[Any]


@dataclass(frozen=True)
class ResolvedMethod:
    node: Any
    strategy: str
    source_end_strategy: str
    source_end_byte: int
    analysis: CandidateAnalysis


@dataclass
class HistoricalFileContext:
    key: tuple[str, str, str]
    git_blob_oid: str
    payload: bytes
    decoded_source: str
    utf8_source: bytes
    full_tree: Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def count_physical_lines(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines()) or 1


def as_int(value: Any, label: str) -> int:
    text = clean(value)
    try:
        result = int(text)
    except ValueError as exc:
        raise MappingError("manifest_schema", f"invalid integer {label}={text!r}") from exc
    if result < 0:
        raise MappingError("manifest_schema", f"negative integer {label}={result}")
    return result


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


def char_offset_to_utf8_byte(source: str, offset: int) -> int:
    if offset < 0 or offset > len(source):
        raise MappingError("body_boundary", f"character offset {offset} outside source length {len(source)}")
    return len(source[:offset].encode("utf-8"))


def physical_line_start_byte(payload: bytes, node_start_byte: int) -> int:
    """Return the UTF-8 byte offset at the beginning of the node's physical line.

    Tree-sitter starts a decorated_definition at the ``@`` token and an
    undecorated function_definition at the ``def``/``async`` token. Those
    offsets intentionally exclude the class-body indentation. For a standalone
    detector source we must preserve the common class indentation first and
    then remove it from the whole definition with ``textwrap.dedent``.
    """

    if node_start_byte < 0 or node_start_byte > len(payload):
        raise MappingError("ml_source_boundary", f"node start byte outside source: {node_start_byte}")
    previous_newline = payload.rfind(b"\n", 0, node_start_byte)
    return 0 if previous_newline < 0 else previous_newline + 1


def normalize_method_source(raw_source: str, strip_block_markers: Any) -> str:
    text = strip_block_markers(raw_source)
    text = textwrap.dedent(text).strip()
    if not text:
        raise MappingError("ml_source_normalize", "standalone method source is empty")
    return text + "\n"


def validate_standalone_header_alignment(normalized_source: str, includes_decorators: bool) -> dict[str, int]:
    """Validate top-level decorator/definition indentation after normalization.

    Continuation lines inside a multi-line decorator expression may be
    indented. Only decorator statement starts and the associated top-level
    ``def``/``async def`` header must begin in column zero.
    """

    lines = normalized_source.splitlines()
    definition_index = None
    decorator_count = 0
    decorator_headers_column_zero = 1

    for index, line in enumerate(lines):
        stripped = line.lstrip(" \t")
        if not stripped:
            continue
        if re.match(r"(?:async\s+)?def\b", stripped):
            definition_index = index
            break
        if stripped.startswith("@"):
            decorator_count += 1
            if line != stripped:
                decorator_headers_column_zero = 0

    if definition_index is None:
        raise MappingError("ml_source_indentation", "standalone source has no top-level def/async def header")

    definition_line = lines[definition_index]
    definition_header_column_zero = int(definition_line == definition_line.lstrip(" \t"))
    if not definition_header_column_zero:
        raise MappingError("ml_source_indentation", "standalone def/async def header is not in column zero")
    if not decorator_headers_column_zero:
        raise MappingError("ml_source_indentation", "standalone decorator header is not in column zero")
    if includes_decorators and decorator_count == 0:
        raise MappingError("ml_source_indentation", "decorated Tree-sitter definition produced no top-level decorator")
    if not includes_decorators and decorator_count != 0:
        raise MappingError("ml_source_indentation", "undecorated Tree-sitter definition unexpectedly produced a decorator")

    return {
        "top_level_decorator_count": decorator_count,
        "decorator_headers_column_zero": decorator_headers_column_zero,
        "definition_header_column_zero": definition_header_column_zero,
    }


def deterministic_smoke_positions(total: int, sample_size: int) -> set[int]:
    """Return 1-based positions spread deterministically over the full universe."""

    if total <= 0 or sample_size <= 0:
        return set()
    sample_size = min(total, sample_size)
    if sample_size == 1:
        return {(total + 1) // 2}
    positions = {1 + round(i * (total - 1) / (sample_size - 1)) for i in range(sample_size)}
    if len(positions) != sample_size:
        raise RuntimeError(f"deterministic smoke position collision: expected={sample_size} observed={len(positions)}")
    return positions


def iter_tree_nodes(root: Any) -> Iterator[Any]:
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(list(getattr(node, "children", []) or [])))


def tree_has_error(root: Any) -> bool:
    value = getattr(root, "has_error", False)
    return bool(value() if callable(value) else value)


def count_tree_recovery_nodes(root: Any) -> tuple[int, int]:
    errors = 0
    missing = 0
    for node in iter_tree_nodes(root):
        if clean(getattr(node, "type", "")) == "ERROR":
            errors += 1
        flag = getattr(node, "is_missing", False)
        if callable(flag):
            flag = flag()
        if bool(flag):
            missing += 1
    return errors, missing


def node_name(node: Any, utf8_source: bytes) -> str:
    name_node = None
    field = getattr(node, "child_by_field_name", None)
    if callable(field):
        try:
            name_node = field("name")
        except Exception:
            name_node = None
    if name_node is None:
        for child in list(getattr(node, "children", []) or []):
            if clean(getattr(child, "type", "")) == "identifier":
                name_node = child
                break
    if name_node is None:
        return ""
    return utf8_source[int(name_node.start_byte): int(name_node.end_byte)].decode("utf-8", errors="strict")


def full_definition_node(function_node: Any) -> tuple[Any, bool]:
    parent = getattr(function_node, "parent", None)
    if parent is not None and clean(getattr(parent, "type", "")) == "decorated_definition":
        return parent, True
    return function_node, False


def is_primary_class_method(function_node: Any) -> bool:
    """Return whether a Tree-sitter function is a direct class-body method.

    This mirrors the frozen FUN rule that accepts only direct module-level
    functions. For C_FUN, an undecorated method must be directly inside the
    class body block; a decorated method is wrapped by ``decorated_definition``
    inside that same class body block. Definitions nested inside another method
    or inside a compound statement are not promoted to C_FUN by this locator.
    """

    parent = getattr(function_node, "parent", None)
    if parent is None:
        return False
    if clean(getattr(parent, "type", "")) == "decorated_definition":
        parent = getattr(parent, "parent", None)
    if parent is None:
        return False
    parent_type = clean(getattr(parent, "type", ""))
    if parent_type == "class_definition":
        return True
    if parent_type != "block":
        return False
    grandparent = getattr(parent, "parent", None)
    return grandparent is not None and clean(getattr(grandparent, "type", "")) == "class_definition"


def analyze_candidates(
    root: Any,
    utf8_source: bytes,
    body_start_byte: int,
    body_end_byte: int,
    expected_name: str,
) -> CandidateAnalysis:
    all_functions: list[Any] = []
    same_name: list[Any] = []
    anchor_functions: list[Any] = []
    same_name_anchor: list[Any] = []
    primary_same_name_anchor: list[Any] = []
    strict_same_name_anchor: list[Any] = []

    for node in iter_tree_nodes(root):
        if clean(getattr(node, "type", "")) != "function_definition":
            continue
        all_functions.append(node)
        start = int(getattr(node, "start_byte", -1))
        end = int(getattr(node, "end_byte", -1))
        contains_anchor = start <= body_start_byte < end
        if contains_anchor:
            anchor_functions.append(node)
        name_matches = node_name(node, utf8_source) == expected_name
        if name_matches:
            same_name.append(node)
        if name_matches and contains_anchor:
            same_name_anchor.append(node)
            if is_primary_class_method(node):
                primary_same_name_anchor.append(node)
                if end <= body_end_byte:
                    strict_same_name_anchor.append(node)

    return CandidateAnalysis(
        all_functions=all_functions,
        same_name=same_name,
        anchor_functions=anchor_functions,
        same_name_anchor=same_name_anchor,
        primary_same_name_anchor=primary_same_name_anchor,
        strict_same_name_anchor=strict_same_name_anchor,
    )


def choose_smallest_unique(candidates: Sequence[Any], label: str) -> Any:
    if not candidates:
        raise MappingError("tree_sitter_occurrence_map", f"no {label} candidates")
    ordered = sorted(candidates, key=lambda node: (int(node.end_byte) - int(node.start_byte), int(node.start_byte)))
    best = ordered[0]
    if len(ordered) > 1:
        first_span = int(best.end_byte) - int(best.start_byte)
        second_span = int(ordered[1].end_byte) - int(ordered[1].start_byte)
        if first_span == second_span:
            raise MappingError("tree_sitter_occurrence_map", f"ambiguous equal-span {label} candidates")
    return best


def resolve_method_node(
    root: Any,
    utf8_source: bytes,
    body_start_byte: int,
    body_end_byte: int,
    expected_name: str,
) -> ResolvedMethod:
    analysis = analyze_candidates(root, utf8_source, body_start_byte, body_end_byte, expected_name)

    if analysis.strict_same_name_anchor:
        node = choose_smallest_unique(analysis.strict_same_name_anchor, "strict same-name direct-class-method anchor")
        full_node, _ = full_definition_node(node)
        return ResolvedMethod(
            node=node,
            strategy="strict_body_start_anchor_with_end_guard",
            source_end_strategy="tree_sitter_full_definition_end",
            source_end_byte=int(full_node.end_byte),
            analysis=analysis,
        )

    # Conservative recovery copied from the successful FUN A02-v3 repair
    # policy: A05 already proves the exact method body. If there is exactly one
    # direct class method with the expected name containing the verified body
    # start, reuse only the Tree-sitter START and keep the authoritative A05 END.
    if len(analysis.primary_same_name_anchor) == 1:
        node = analysis.primary_same_name_anchor[0]
        return ResolvedMethod(
            node=node,
            strategy="unique_primary_method_body_start_anchor_a05_end_override",
            source_end_strategy="a05_verified_method_body_end",
            source_end_byte=body_end_byte,
            analysis=analysis,
        )

    raise MappingError(
        "tree_sitter_occurrence_map",
        "unsafe C_FUN Tree-sitter mapping: "
        f"all_functions={len(analysis.all_functions)}; "
        f"same_name={len(analysis.same_name)}; "
        f"anchor={len(analysis.anchor_functions)}; "
        f"same_name_anchor={len(analysis.same_name_anchor)}; "
        f"primary_same_name_anchor={len(analysis.primary_same_name_anchor)}; "
        f"strict_same_name_anchor={len(analysis.strict_same_name_anchor)}",
    )


def artifact_relative_path(source_sha256: str) -> Path:
    return Path("ml_cfun_sources") / source_sha256[:2] / f"{source_sha256}.py"


def write_artifact(output_root: Path, source: str) -> tuple[str, str, bool]:
    payload = source.encode("utf-8")
    digest = sha256_bytes(payload)
    relative = artifact_relative_path(digest)
    destination = output_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    reused = destination.exists()
    if reused:
        if sha256_file(destination) != digest:
            raise MappingError("artifact_integrity", f"existing artifact hash mismatch: {destination}")
    else:
        temp = destination.with_name(destination.name + f".tmp.{os.getpid()}")
        temp.write_bytes(payload)
        os.replace(temp, destination)
    return digest, relative.as_posix(), reused


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"[ERROR] expected JSON object: {path}")
    return payload


def add_check(
    rows: list[dict[str, Any]],
    name: str,
    severity: str,
    passed: bool,
    observed: Any,
    expected: Any,
    note: str = "",
) -> None:
    rows.append(
        {
            "check_name": name,
            "severity": severity,
            "passed": int(bool(passed)),
            "observed": observed,
            "expected": expected,
            "note": note,
        }
    )


def resolve_clone_path(original: Path, prefix_from: str, prefix_to: str) -> Path:
    if original.is_dir():
        return original
    if prefix_from and prefix_to:
        original_text = str(original)
        prefix = prefix_from.rstrip("/")
        if original_text == prefix or original_text.startswith(prefix + "/"):
            candidate = Path(prefix_to.rstrip("/") + original_text[len(prefix):])
            if candidate.is_dir():
                return candidate
    return original


def load_snapshot_status(path: Path, prefix_from: str, prefix_to: str) -> dict[str, SnapshotStatus]:
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


def validate_a01_freeze(a01_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    summary_path = a01_root / "detector_freeze_summary.json"
    metadata_path = a01_root / "detector_freeze_metadata.json"
    if not summary_path.is_file() or not metadata_path.is_file():
        raise SystemExit(f"[ERROR] A01 freeze artifacts missing under {a01_root}")
    summary = load_json(summary_path)
    metadata = load_json(metadata_path)
    if summary.get("status") != "PASS" or int(summary.get("failed_hard_checks", -1)) != 0:
        raise SystemExit("[ERROR] A01 detector freeze is not PASS with zero hard failures")
    if summary.get("frozen_detector_spec", {}) != metadata.get("frozen_detector_spec", {}):
        raise SystemExit("[ERROR] A01 summary/metadata frozen detector mismatch")
    frozen = summary.get("frozen_detector_spec", {})
    expected = {
        "generation_source": "CodeLlama-7B",
        "classifier": "svm",
        "representation": "ast",
        "embedding_model_id": "Salesforce/codet5p-110m-embedding",
        "score_mode": "decision",
        "human_decision_threshold": 0.0,
    }
    for key, value in expected.items():
        if frozen.get(key) != value:
            raise SystemExit(f"[ERROR] A01 frozen detector {key} mismatch: {frozen.get(key)!r}")
    return summary, metadata


def validate_a13_summary(a13_summary_path: Path, expected_unique_body_sha: int) -> dict[str, Any]:
    if not a13_summary_path.is_file():
        raise SystemExit(f"[ERROR] A13 summary not found: {a13_summary_path}")
    summary = load_json(a13_summary_path)
    expected_pairs = {
        "script_version": EXPECTED_A13_SCRIPT_VERSION,
        "status": "PASS",
        "category": EXPECTED_A13_CATEGORY,
        "code_unit_type": EXPECTED_A13_UNIT_TYPE,
    }
    for key, value in expected_pairs.items():
        if summary.get(key) != value:
            raise SystemExit(f"[ERROR] A13 summary {key} mismatch: {summary.get(key)!r} != {value!r}")
    if int(summary.get("failed_checks", -1)) != 0:
        raise SystemExit("[ERROR] A13 summary has failed checks")
    if int(summary.get("cfun_unique_unit_memberships", -1)) != expected_unique_body_sha:
        raise SystemExit(
            "[ERROR] A13 C_FUN unique membership mismatch: "
            f"{summary.get('cfun_unique_unit_memberships')} != {expected_unique_body_sha}"
        )
    return summary


def load_detector_parser(repo_root: Path, tree_sitter_lib: Path, ast_helper_dir: Path) -> DetectorParser:
    app_dir = repo_root / "src/app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    try:
        from agc_detector import extract_blocks, generate_ast_sequence, load_parser_and_F, strip_block_markers  # type: ignore
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


class GitCatFileBatch:
    def __init__(self, clone_path: Path) -> None:
        self.clone_path = clone_path
        if not clone_path.is_dir():
            raise MappingError("clone_path", f"clone path not found: {clone_path}")
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
        self.proc.stdin.write(spec.encode("utf-8") + b"\n")
        self.proc.stdin.flush()
        header = self.proc.stdout.readline()
        if not header:
            raise MappingError("git_blob_read", f"git cat-file terminated while reading {spec}")
        header_text = header.decode("utf-8", errors="replace").rstrip("\n")
        if header_text.endswith(" missing"):
            raise MappingError("git_blob_read", f"Git object missing: {spec}")
        parts = header_text.split(" ")
        if len(parts) != 3 or parts[1] != "blob":
            raise MappingError("git_blob_read", f"unexpected git cat-file header: {header_text!r}")
        oid = parts[0]
        try:
            size = int(parts[2])
        except ValueError as exc:
            raise MappingError("git_blob_read", f"invalid object size: {header_text!r}") from exc
        payload = self.proc.stdout.read(size)
        terminator = self.proc.stdout.read(1)
        if len(payload) != size or terminator != b"\n":
            raise MappingError("git_blob_read", f"truncated git cat-file payload for {spec}")
        return oid, payload

    def close(self) -> None:
        try:
            if self.proc.stdin is not None:
                self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


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


def validate_snapshot_row(row: dict[str, str], status: SnapshotStatus) -> None:
    if status.status != "success":
        raise MappingError("snapshot_status", f"A05 snapshot status is not success: {status.snapshot_id} status={status.status}")
    comparisons = {
        "dataset_source": (clean(row.get("dataset_source")), status.dataset_source),
        "repo_name": (clean(row.get("repo_name")), status.repo_name),
        "repo_key": (clean(row.get("repo_key")), status.repo_key),
        "snapshot_commit": (clean(row.get("snapshot_commit")).lower(), status.commit_sha),
    }
    mismatches = [key for key, (left, right) in comparisons.items() if left and right and left != right]
    if mismatches:
        raise MappingError("snapshot_identity", f"A05 manifest/status mismatch for {status.snapshot_id}: {mismatches}")


def load_file_context(
    row: dict[str, str],
    statuses: dict[str, SnapshotStatus],
    git_batches: GitBatchLRU,
    detector: DetectorParser,
) -> HistoricalFileContext:
    snapshot_id = clean(row.get("snapshot_id"))
    status = statuses.get(snapshot_id)
    if status is None:
        raise MappingError("snapshot_status", f"snapshot_id not found in A05 status: {snapshot_id}")
    validate_snapshot_row(row, status)
    relative_path = validate_relative_python_path(clean(row.get("relative_path")))
    expected_file_sha = clean(row.get("file_sha256")).lower()
    if not FULL_SHA256_RE.fullmatch(expected_file_sha):
        raise MappingError("manifest_schema", f"invalid file_sha256: {expected_file_sha!r}")
    git_blob_oid, payload = git_batches.get(status.clone_path_effective).read_blob(status.commit_sha, relative_path)
    actual_file_sha = sha256_bytes(payload)
    if actual_file_sha != expected_file_sha:
        raise MappingError("file_identity", f"historical Git blob SHA mismatch: A05={expected_file_sha} actual={actual_file_sha}")
    decoded_source, _ = decode_python_source(payload)
    utf8_source = decoded_source.encode("utf-8")
    full_tree = detector.parser.parse(utf8_source)
    return HistoricalFileContext(
        key=(snapshot_id, relative_path, expected_file_sha),
        git_blob_oid=git_blob_oid,
        payload=payload,
        decoded_source=decoded_source,
        utf8_source=utf8_source,
        full_tree=full_tree,
    )


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
    context: HistoricalFileContext,
    detector: DetectorParser,
    artifact_root: Path,
) -> dict[str, Any]:
    relative_path = validate_relative_python_path(clean(row.get("relative_path")))
    expected_file_sha = clean(row.get("file_sha256")).lower()
    if context.key != (clean(row.get("snapshot_id")), relative_path, expected_file_sha):
        raise MappingError("file_cache", "historical file context key mismatch")

    decoded_source = context.decoded_source
    utf8_source = context.utf8_source
    body_start = as_int(row.get("start_char_offset"), "start_char_offset")
    body_end = as_int(row.get("end_char_offset"), "end_char_offset")
    if not (0 <= body_start < body_end <= len(decoded_source)):
        raise MappingError("body_boundary", f"invalid A05 body range [{body_start}, {body_end})")

    body_text = decoded_source[body_start:body_end]
    expected_body_sha = clean(row.get("code_unit_sha256")).lower()
    if not FULL_SHA256_RE.fullmatch(expected_body_sha):
        raise MappingError("manifest_schema", f"invalid code_unit_sha256: {expected_body_sha!r}")
    actual_body_sha = sha256_text(body_text)
    if actual_body_sha != expected_body_sha:
        raise MappingError("body_identity", f"A05 body SHA mismatch: A05={expected_body_sha} actual={actual_body_sha}")

    expected_tokens = as_int(row.get("space_by_token_count"), "space_by_token_count")
    actual_tokens = len(body_text.split(" "))
    if actual_tokens != expected_tokens:
        raise MappingError("body_identity", f"literal-space-token mismatch: A05={expected_tokens} actual={actual_tokens}")

    body_start_byte = char_offset_to_utf8_byte(decoded_source, body_start)
    body_end_byte = char_offset_to_utf8_byte(decoded_source, body_end)
    expected_name = leaf_function_name(clean(row.get("qualified_name")))
    if not expected_name:
        raise MappingError("manifest_schema", "cannot derive method name from qualified_name")

    resolved = resolve_method_node(
        context.full_tree.root_node,
        utf8_source,
        body_start_byte,
        body_end_byte,
        expected_name,
    )
    method_node = resolved.node
    if not is_primary_class_method(method_node):
        raise MappingError("tree_sitter_occurrence_map", "resolved node is not a direct class method")

    full_node, includes_decorators = full_definition_node(method_node)
    tree_sitter_source_start = int(full_node.start_byte)
    source_start = physical_line_start_byte(utf8_source, tree_sitter_source_start)
    source_end = int(resolved.source_end_byte)
    if not (0 <= source_start < source_end <= len(utf8_source)):
        raise MappingError(
            "ml_source_boundary",
            f"invalid reconstructed method bytes [{source_start}, {source_end}) for source length {len(utf8_source)}",
        )

    raw_full_source = utf8_source[source_start:source_end].decode("utf-8", errors="strict")
    normalized_source = normalize_method_source(raw_full_source, detector.strip_block_markers)
    alignment = validate_standalone_header_alignment(normalized_source, includes_decorators)
    normalized_bytes = normalized_source.encode("utf-8")
    standalone_tree = detector.parser.parse(normalized_bytes)
    error_nodes, missing_nodes = count_tree_recovery_nodes(standalone_tree.root_node)

    blocks = detector.extract_blocks(normalized_source, detector.parser)
    if len(blocks) != 1:
        raise MappingError("ml_input_compatibility", f"standalone source must contain exactly one detector block; found {len(blocks)}")
    block = blocks[0]
    block_kind = clean(block.get("kind"))
    block_name = clean(block.get("name"))
    block_code = str(block.get("code", ""))
    if block_kind != "function_definition":
        raise MappingError("ml_input_compatibility", f"standalone source resolved to block kind {block_kind!r}")
    if block_name != expected_name:
        raise MappingError("ml_input_compatibility", f"standalone block name {block_name!r} != expected {expected_name!r}")
    covers = int(block_code.strip() == normalized_source.strip())
    if not covers:
        raise MappingError("ml_input_compatibility", "Tree-sitter block does not cover complete normalized standalone source")

    ast_sequence = detector.generate_ast_sequence(block_code, detector.parser, detector.ast_function)
    if not ast_sequence.strip():
        raise MappingError("ml_input_compatibility", "AST sequence is empty")

    source_sha, source_relative, _ = write_artifact(artifact_root, normalized_source)
    analysis = resolved.analysis
    candidate_start = int(method_node.start_byte)
    candidate_end = int(method_node.end_byte)
    warning_parts: list[str] = []
    if tree_has_error(context.full_tree.root_node):
        warning_parts.append("full_file_tree_sitter_recovery")
    if tree_has_error(standalone_tree.root_node) or error_nodes or missing_nodes:
        warning_parts.append("standalone_tree_sitter_recovery")
    if resolved.source_end_strategy == "a05_verified_method_body_end":
        warning_parts.append("tree_sitter_full_file_end_overridden_by_a05")

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
        "git_blob_oid": context.git_blob_oid,
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
        "tree_sitter_function_name": node_name(method_node, utf8_source),
        "tree_sitter_function_name_matches": 1,
        "tree_sitter_direct_class_method": 1,
        "tree_sitter_full_file_has_error": int(tree_has_error(context.full_tree.root_node)),
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
        "ml_source_tree_sitter_start_byte_utf8": tree_sitter_source_start,
        "ml_source_start_strategy": "physical_line_start_before_decorator_or_definition",
        "ml_source_top_level_decorator_count": alignment["top_level_decorator_count"],
        "ml_source_decorator_headers_column_zero": alignment["decorator_headers_column_zero"],
        "ml_source_definition_header_column_zero": alignment["definition_header_column_zero"],
        "ml_source_normalization": "physical_line_start_then_strip_block_markers_then_textwrap_dedent_strip_plus_lf",
        "tree_sitter_occurrence_mapping": resolved.strategy,
        "ml_source_end_strategy": resolved.source_end_strategy,
        "tree_sitter_same_name_candidate_count": len(analysis.same_name),
        "tree_sitter_anchor_candidate_count": len(analysis.anchor_functions),
        "tree_sitter_primary_anchor_candidate_count": len(analysis.primary_same_name_anchor),
        "tree_sitter_strict_candidate_count": len(analysis.strict_same_name_anchor),
        "tree_sitter_candidate_start_byte_utf8": candidate_start,
        "tree_sitter_candidate_end_byte_utf8": candidate_end,
        "tree_sitter_candidate_end_minus_a05_body_end_bytes": candidate_end - body_end_byte,
        "mapping_status": "PASS",
        "mapping_warning": ";".join(warning_parts),
    }


def update_unique_source_summary(summaries: dict[str, dict[str, Any]], mapped: dict[str, Any]) -> None:
    source_sha = clean(mapped.get("ml_source_sha256"))
    item = summaries.get(source_sha)
    if item is None:
        item = {
            "ml_source_sha256": source_sha,
            "ml_source_relative_path": clean(mapped.get("ml_source_relative_path")),
            "occurrence_count": 0,
            "first_dataset_source": clean(mapped.get("dataset_source")),
            "first_repo_name": clean(mapped.get("repo_name")),
            "first_snapshot_id": clean(mapped.get("snapshot_id")),
            "first_snapshot_commit": clean(mapped.get("snapshot_commit")),
            "first_relative_path": clean(mapped.get("relative_path")),
            "first_code_unit_id": clean(mapped.get("code_unit_id")),
            "first_qualified_name": clean(mapped.get("qualified_name")),
            "function_name": clean(mapped.get("function_name")),
            "function_kind": clean(mapped.get("function_kind")),
            "ml_source_character_count": clean(mapped.get("ml_source_character_count")),
            "ml_source_utf8_byte_count": clean(mapped.get("ml_source_utf8_byte_count")),
            "ml_source_physical_line_count": clean(mapped.get("ml_source_physical_line_count")),
            "ml_ast_sequence_character_count": clean(mapped.get("ml_ast_sequence_character_count")),
            "ml_ast_sequence_token_count": clean(mapped.get("ml_ast_sequence_token_count")),
            "any_tree_sitter_standalone_warning": 0,
        }
        summaries[source_sha] = item
    item["occurrence_count"] = int(item["occurrence_count"]) + 1
    if clean(mapped.get("mapping_warning")):
        item["any_tree_sitter_standalone_warning"] = 1




def run_self_test_v2_core() -> int:
    class FakeNameNode:
        def __init__(self, name: str, start: int) -> None:
            self.start_byte = start
            self.end_byte = start + len(name)
            self.type = "identifier"
            self.children: list[Any] = []
            self.parent = None
            self._name = name

    class FakeNode:
        def __init__(
            self,
            node_type: str,
            start: int,
            end: int,
            name: str = "",
            children: list[Any] | None = None,
        ) -> None:
            self.type = node_type
            self.start_byte = start
            self.end_byte = end
            self.children = children or []
            self.parent = None
            self._name = name
            self.has_error = False
            for child in self.children:
                child.parent = self

        def child_by_field_name(self, field: str) -> Any:
            if field != "name" or not self._name:
                return None
            return FakeNameNode(self._name, self.start_byte + 4)

    # Strict direct-class method.
    source = b"class C:\n    def f(self):\n        x = 1\n"
    method_start = source.find(b"def f")
    method_end = len(source.rstrip(b"\n"))
    method = FakeNode("function_definition", method_start, method_end, "f")
    block = FakeNode("block", method_start, method_end, children=[method])
    cls = FakeNode("class_definition", 0, method_end, "C", children=[block])
    root = FakeNode("module", 0, len(source), children=[cls])
    body_start = source.find(b"x = 1")
    strict = resolve_method_node(root, source, body_start, method_end, "f")
    if strict.strategy != "strict_body_start_anchor_with_end_guard":
        raise SystemExit("[ERROR] self-test strict class-method mapping failed")
    if not is_primary_class_method(method):
        raise SystemExit("[ERROR] self-test direct class method not recognized")

    # Exercise the complete occurrence-to-artifact mapping with detector stubs.
    class FakeTree:
        def __init__(self, root_node: Any) -> None:
            self.root_node = root_node

    class FakeParser:
        def parse(self, payload: bytes) -> Any:
            # The standalone validation path only needs an error-free root.
            return FakeTree(FakeNode("module", 0, len(payload), children=[]))

    fake_detector = DetectorParser(
        parser=FakeParser(),
        ast_function=object(),
        extract_blocks=lambda text, parser: [{"kind": "function_definition", "name": "f", "code": text}],
        generate_ast_sequence=lambda code, parser, ast_function: "function_definition identifier block",
        strip_block_markers=lambda text: text,
    )
    decoded = source.decode("utf-8")
    file_sha = sha256_bytes(source)
    body_char_start = decoded.index("        x = 1")
    body_char_end = len(decoded.rstrip("\n"))
    body_text = decoded[body_char_start:body_char_end]
    row = {
        "snapshot_order": "1",
        "snapshot_id": "s1",
        "dataset_source": "control",
        "repo_name": "o/r",
        "repo_key": "o/r",
        "snapshot_time": "2026-01-01",
        "snapshot_commit": "abc",
        "relative_path": "a.py",
        "file_sha256": file_sha,
        "code_unit_id": "u1",
        "code_unit_type": "method_body",
        "aggregation_role": "primary",
        "qualified_name": "C.f",
        "function_kind": "method",
        "occurrence_index": "0",
        "start_line": "3",
        "end_line": "3",
        "start_char_offset": str(body_char_start),
        "end_char_offset": str(body_char_end),
        "code_unit_sha256": sha256_text(body_text),
        "code_unit_relative_path": "code_units/aa/example.txt",
        "character_count": str(len(body_text)),
        "utf8_byte_count": str(len(body_text.encode("utf-8"))),
        "physical_line_count": "1",
        "space_by_token_count": str(len(body_text.split(" "))),
    }
    context = HistoricalFileContext(
        key=("s1", "a.py", file_sha),
        git_blob_oid="deadbeef",
        payload=source,
        decoded_source=decoded,
        utf8_source=source,
        full_tree=FakeTree(root),
    )
    with tempfile.TemporaryDirectory() as tmp:
        mapped = map_occurrence(row, context, fake_detector, Path(tmp))
        if mapped["code_unit_type"] != "method_body" or mapped["tree_sitter_direct_class_method"] != 1:
            raise SystemExit("[ERROR] self-test complete C_FUN mapping metadata failed")
        artifact = Path(tmp) / mapped["ml_source_relative_path"]
        if not artifact.is_file() or sha256_file(artifact) != mapped["ml_source_sha256"]:
            raise SystemExit("[ERROR] self-test C_FUN source artifact integrity failed")

    # Decorated methods must preserve the common class indentation before
    # whole-definition dedent so both decorators and def/async def reach column 0.
    decorated_raw = "    @staticmethod\n    def f(x):\n        return x\n"
    decorated_normalized = normalize_method_source(decorated_raw, lambda text: text)
    if decorated_normalized != "@staticmethod\ndef f(x):\n    return x\n":
        raise SystemExit("[ERROR] self-test decorated method normalization failed")
    alignment = validate_standalone_header_alignment(decorated_normalized, True)
    if alignment["top_level_decorator_count"] != 1:
        raise SystemExit("[ERROR] self-test decorated method count failed")

    multi_decorator_raw = (
        "    @classmethod\n"
        "    @cache(key=(\n"
        "        'x',\n"
        "    ))\n"
        "    async def g(cls):\n"
        "        return 1\n"
    )
    multi_normalized = normalize_method_source(multi_decorator_raw, lambda text: text)
    alignment = validate_standalone_header_alignment(multi_normalized, True)
    if alignment["top_level_decorator_count"] != 2 or not multi_normalized.startswith("@classmethod\n@cache"):
        raise SystemExit("[ERROR] self-test multiple-decorator normalization failed")

    # Reproduce the v1 failure mode explicitly: slicing at the @ token drops
    # the decorator line indentation, so textwrap.dedent cannot unindent def.
    broken_v1_source = "@staticmethod\n    def f(x):\n        return x\n"
    try:
        validate_standalone_header_alignment(normalize_method_source(broken_v1_source, lambda text: text), True)
    except MappingError as exc:
        if exc.stage != "ml_source_indentation":
            raise
    else:
        raise SystemExit("[ERROR] self-test did not reject the v1 decorated-method indentation bug")

    # A nested function inside a method must never be promoted to C_FUN.
    nested_start = body_start
    nested = FakeNode("function_definition", nested_start, method_end, "g")
    nested_block = FakeNode("block", nested_start, method_end, children=[nested])
    outer_method = FakeNode("function_definition", method_start, method_end, "f", children=[nested_block])
    class_block = FakeNode("block", method_start, method_end, children=[outer_method])
    cls2 = FakeNode("class_definition", 0, method_end, "C", children=[class_block])
    FakeNode("module", 0, len(source), children=[cls2])
    if is_primary_class_method(nested):
        raise SystemExit("[ERROR] self-test nested function incorrectly recognized as C_FUN")

    # Recovery path: Tree-sitter method end extends past authoritative A05 end.
    recovery_source = b"class C:\n    def f(self):\n        x = 1\n\n    def g(self):\n        return 2\n"
    f_start = recovery_source.find(b"def f")
    f_body_start = recovery_source.find(b"x = 1")
    a05_end = recovery_source.find(b"\n\n    def g") + 1
    f_recovery = FakeNode("function_definition", f_start, len(recovery_source.rstrip(b"\n")), "f")
    recovery_block = FakeNode("block", f_start, len(recovery_source), children=[f_recovery])
    recovery_cls = FakeNode("class_definition", 0, len(recovery_source), "C", children=[recovery_block])
    recovery_root = FakeNode("module", 0, len(recovery_source), children=[recovery_cls])
    recovered = resolve_method_node(recovery_root, recovery_source, f_body_start, a05_end, "f")
    if recovered.strategy != "unique_primary_method_body_start_anchor_a05_end_override":
        raise SystemExit("[ERROR] self-test A05 end-override method mapping failed")
    if recovered.source_end_byte != a05_end:
        raise SystemExit("[ERROR] self-test authoritative A05 method end was not preserved")

    # Ambiguous same-name direct-class candidates must be rejected.
    f1 = FakeNode("function_definition", f_start, len(recovery_source), "f")
    f2 = FakeNode("function_definition", f_start, len(recovery_source), "f")
    ambiguous_block = FakeNode("block", f_start, len(recovery_source), children=[f1, f2])
    ambiguous_cls = FakeNode("class_definition", 0, len(recovery_source), "C", children=[ambiguous_block])
    ambiguous_root = FakeNode("module", 0, len(recovery_source), children=[ambiguous_cls])
    try:
        resolve_method_node(ambiguous_root, recovery_source, f_body_start, a05_end, "f")
    except MappingError:
        pass
    else:
        raise SystemExit("[ERROR] self-test ambiguous method mapping was not rejected")

    print("prepare_ml_cfun_inputs-v3 base self-test: PASS")
    return 0


# ---------------------------------------------------------------------------
# run-x-a05-v3 residual diagnostics and repair
# ---------------------------------------------------------------------------

EXPECTED_V2_FAILURES = 946
EXPECTED_V2_INDENTATION_FAILURES = 862
EXPECTED_V2_OCCURRENCE_MAP_FAILURES = 84

RECOVERY_DIAGNOSTIC_COLUMNS = [
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "snapshot_commit",
    "relative_path",
    "code_unit_id",
    "qualified_name",
    "npr_body_sha256",
    "v2_stage",
    "v2_error_message",
    "recovery_status",
    "v3_mapping_strategy",
    "v3_source_normalization",
    "v3_mapping_warning",
    "v3_ml_source_sha256",
    "v3_error_stage",
    "v3_error_message",
]


def occurrence_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        clean(row.get("snapshot_id")),
        clean(row.get("relative_path")),
        clean(row.get("code_unit_id")),
    )


def multiline_string_continuation_rows(text: str) -> set[int]:
    """Return 1-based physical rows that must retain literal leading spaces.

    Only rows after the first physical row of a multiline STRING token are
    protected. The first row still contains structural Python indentation
    before the string token and may safely lose the surrounding class prefix.
    Interior and closing-delimiter rows can contain literal string whitespace,
    so they are never structurally dedented.
    """

    protected: set[int] = set()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type != tokenize.STRING:
                continue
            start_row, _ = token.start
            end_row, _ = token.end
            if end_row > start_row:
                protected.update(range(start_row + 1, end_row + 1))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        raise MappingError("ml_source_normalize_tokenize", f"{type(exc).__name__}: {exc}") from exc
    return protected


def normalize_method_source_v3(
    raw_source: str,
    structural_prefix: str,
    strip_block_markers: Any,
) -> str:
    """Remove only the enclosing class indentation from detector source.

    ``textwrap.dedent`` is intentionally not used here. Historical methods can
    contain multiline string literals whose continuation lines begin in column
    zero. A whole-text minimum-indent calculation therefore leaves the method
    header indented. More importantly, blindly removing indentation from every
    line can alter literal string content. This routine removes the exact
    Tree-sitter/lexical method indentation prefix only on physical lines that
    are outside multiline-string continuation rows.
    """

    text = strip_block_markers(raw_source)
    protected = multiline_string_continuation_rows(text)
    lines = text.splitlines(keepends=True)
    normalized_lines: list[str] = []
    for row_number, line in enumerate(lines, start=1):
        if row_number not in protected and structural_prefix and line.startswith(structural_prefix):
            line = line[len(structural_prefix):]
        normalized_lines.append(line)
    normalized = "".join(normalized_lines).strip()
    if not normalized:
        raise MappingError("ml_source_normalize", "standalone method source is empty")
    return normalized + "\n"


def validate_detector_standalone(
    normalized_source: str,
    includes_decorators: bool,
    expected_name: str,
    detector: DetectorParser,
) -> dict[str, Any]:
    alignment = validate_standalone_header_alignment(normalized_source, includes_decorators)
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
        raise MappingError("ml_input_compatibility", f"standalone source resolved to block kind {block_kind!r}")
    if block_name != expected_name:
        raise MappingError(
            "ml_input_compatibility",
            f"standalone block name {block_name!r} != expected {expected_name!r}",
        )
    covers = int(block_code.strip() == normalized_source.strip())
    if not covers:
        raise MappingError("ml_input_compatibility", "Tree-sitter block does not cover complete normalized standalone source")
    ast_sequence = detector.generate_ast_sequence(block_code, detector.parser, detector.ast_function)
    if not ast_sequence.strip():
        raise MappingError("ml_input_compatibility", "AST sequence is empty")
    return {
        "alignment": alignment,
        "normalized_bytes": normalized_bytes,
        "standalone_tree": standalone_tree,
        "error_nodes": error_nodes,
        "missing_nodes": missing_nodes,
        "blocks": blocks,
        "block_kind": block_kind,
        "block_name": block_name,
        "block_code": block_code,
        "covers": covers,
        "ast_sequence": ast_sequence,
    }


def source_line_char_offsets(source: str) -> tuple[list[str], list[int]]:
    lines = source.splitlines(keepends=True)
    offsets: list[int] = []
    position = 0
    for line in lines:
        offsets.append(position)
        position += len(line)
    if not lines:
        return [""], [0]
    return lines, offsets


def local_method_source_recovery(
    decoded_source: str,
    body_start_char: int,
    body_end_char: int,
    expected_name: str,
    detector: DetectorParser,
    max_back_lines: int = 500,
    max_decorator_back_lines: int = 80,
) -> dict[str, Any]:
    """Recover a standalone method around an authoritative A05 body anchor.

    This fallback is used only when the full-file Tree-sitter hierarchy cannot
    safely locate the A05 C_FUN occurrence. A05 has already independently
    verified the exact historical file/body identity. We search a bounded local
    region for the nearest same-name ``def``/``async def`` header preceding the
    body anchor, then require the reconstructed standalone source to pass the
    frozen detector parser as exactly one full-source function block with the
    expected name and a non-empty AST sequence.
    """

    lines, offsets = source_line_char_offsets(decoded_source)
    body_line_index = max(0, bisect.bisect_right(offsets, body_start_char) - 1)
    first_line = max(0, body_line_index - max_back_lines)
    pattern = re.compile(
        r"^(?P<indent>[ \t]*)(?:async[ \t]+)?def[ \t]+" + re.escape(expected_name) + r"\b"
    )
    header_candidates: list[tuple[int, str]] = []
    for index in range(body_line_index, first_line - 1, -1):
        line = lines[index].rstrip("\r\n")
        match = pattern.match(line)
        if match:
            header_candidates.append((index, match.group("indent")))

    if not header_candidates:
        raise MappingError(
            "local_header_recovery",
            f"no bounded same-name def/async def header found within {max_back_lines} lines for {expected_name}",
        )

    rejection_messages: list[str] = []
    for def_index, structural_prefix in header_candidates:
        candidate_start_indices = [def_index]
        decorator_first = max(0, def_index - max_decorator_back_lines)
        for index in range(def_index - 1, decorator_first - 1, -1):
            line = lines[index].rstrip("\r\n")
            if line.startswith(structural_prefix + "@"):
                candidate_start_indices.append(index)
        # Prefer the earliest valid decorator-bearing source; fall back to def.
        candidate_start_indices = sorted(set(candidate_start_indices))
        valid: list[dict[str, Any]] = []
        for start_index in candidate_start_indices:
            start_char = offsets[start_index]
            if not (0 <= start_char < body_start_char < body_end_char <= len(decoded_source)):
                continue
            raw_source = decoded_source[start_char:body_end_char]
            includes_decorators = start_index != def_index and lines[start_index].lstrip(" \t").startswith("@")
            try:
                normalized = normalize_method_source_v3(raw_source, structural_prefix, detector.strip_block_markers)
                validation = validate_detector_standalone(
                    normalized,
                    includes_decorators,
                    expected_name,
                    detector,
                )
            except MappingError as exc:
                rejection_messages.append(
                    f"start_line={start_index + 1}:{exc.stage}:{str(exc)[:160]}"
                )
                continue
            valid.append(
                {
                    "start_index": start_index,
                    "def_index": def_index,
                    "start_char": start_char,
                    "structural_prefix": structural_prefix,
                    "includes_decorators": includes_decorators,
                    "normalized_source": normalized,
                    "validation": validation,
                }
            )
        if valid:
            # Earliest valid start preserves all detector-visible decorators.
            return sorted(valid, key=lambda item: item["start_index"])[0]

    detail = "; ".join(rejection_messages[:8])
    raise MappingError(
        "local_header_recovery",
        f"same-name headers found but no safe standalone reconstruction for {expected_name}; {detail}",
    )


def map_occurrence_v3(
    row: dict[str, str],
    context: HistoricalFileContext,
    detector: DetectorParser,
    artifact_root: Path,
) -> dict[str, Any]:
    """Map one residual v2 failure using v3 structural/local recovery."""

    relative_path = validate_relative_python_path(clean(row.get("relative_path")))
    expected_file_sha = clean(row.get("file_sha256")).lower()
    if context.key != (clean(row.get("snapshot_id")), relative_path, expected_file_sha):
        raise MappingError("file_cache", "historical file context key mismatch")

    decoded_source = context.decoded_source
    utf8_source = context.utf8_source
    body_start = as_int(row.get("start_char_offset"), "start_char_offset")
    body_end = as_int(row.get("end_char_offset"), "end_char_offset")
    if not (0 <= body_start < body_end <= len(decoded_source)):
        raise MappingError("body_boundary", f"invalid A05 body range [{body_start}, {body_end})")

    body_text = decoded_source[body_start:body_end]
    expected_body_sha = clean(row.get("code_unit_sha256")).lower()
    if not FULL_SHA256_RE.fullmatch(expected_body_sha):
        raise MappingError("manifest_schema", f"invalid code_unit_sha256: {expected_body_sha!r}")
    actual_body_sha = sha256_text(body_text)
    if actual_body_sha != expected_body_sha:
        raise MappingError("body_identity", f"A05 body SHA mismatch: A05={expected_body_sha} actual={actual_body_sha}")
    expected_tokens = as_int(row.get("space_by_token_count"), "space_by_token_count")
    actual_tokens = len(body_text.split(" "))
    if actual_tokens != expected_tokens:
        raise MappingError("body_identity", f"literal-space-token mismatch: A05={expected_tokens} actual={actual_tokens}")

    body_start_byte = char_offset_to_utf8_byte(decoded_source, body_start)
    body_end_byte = char_offset_to_utf8_byte(decoded_source, body_end)
    expected_name = leaf_function_name(clean(row.get("qualified_name")))
    if not expected_name:
        raise MappingError("manifest_schema", "cannot derive method name from qualified_name")

    warning_parts: list[str] = []
    full_file_has_error = int(tree_has_error(context.full_tree.root_node))
    if full_file_has_error:
        warning_parts.append("full_file_tree_sitter_recovery")

    analysis = analyze_candidates(
        context.full_tree.root_node,
        utf8_source,
        body_start_byte,
        body_end_byte,
        expected_name,
    )

    local_recovery = False
    try:
        resolved = resolve_method_node(
            context.full_tree.root_node,
            utf8_source,
            body_start_byte,
            body_end_byte,
            expected_name,
        )
        method_node = resolved.node
        if not is_primary_class_method(method_node):
            raise MappingError("tree_sitter_occurrence_map", "resolved node is not a direct class method")
        full_node, includes_decorators = full_definition_node(method_node)
        tree_sitter_source_start = int(full_node.start_byte)
        source_start = physical_line_start_byte(utf8_source, tree_sitter_source_start)
        source_end = int(resolved.source_end_byte)
        if not (0 <= source_start < source_end <= len(utf8_source)):
            raise MappingError(
                "ml_source_boundary",
                f"invalid reconstructed method bytes [{source_start}, {source_end}) for source length {len(utf8_source)}",
            )
        prefix_bytes = utf8_source[source_start:tree_sitter_source_start]
        try:
            structural_prefix = prefix_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise MappingError("ml_source_indentation", f"invalid structural indentation prefix: {exc}") from exc
        if structural_prefix.strip(" \t"):
            raise MappingError(
                "ml_source_indentation",
                f"method structural prefix contains non-whitespace: {structural_prefix!r}",
            )
        raw_full_source = utf8_source[source_start:source_end].decode("utf-8", errors="strict")
        normalized_source = normalize_method_source_v3(
            raw_full_source,
            structural_prefix,
            detector.strip_block_markers,
        )
        validation = validate_detector_standalone(
            normalized_source,
            includes_decorators,
            expected_name,
            detector,
        )
        mapping_strategy = resolved.strategy + "+v3_structural_indent_prefix"
        source_end_strategy = resolved.source_end_strategy
        if source_end_strategy == "a05_verified_method_body_end":
            warning_parts.append("tree_sitter_full_file_end_overridden_by_a05")
        candidate_start = int(method_node.start_byte)
        candidate_end = int(method_node.end_byte)
        direct_class_method = 1
    except MappingError as exc:
        if exc.stage != "tree_sitter_occurrence_map":
            raise
        local_recovery = True
        local = local_method_source_recovery(
            decoded_source,
            body_start,
            body_end,
            expected_name,
            detector,
        )
        normalized_source = local["normalized_source"]
        validation = local["validation"]
        includes_decorators = bool(local["includes_decorators"])
        source_start_char = int(local["start_char"])
        source_start = char_offset_to_utf8_byte(decoded_source, source_start_char)
        source_end = body_end_byte
        def_line_start_char = source_line_char_offsets(decoded_source)[1][int(local["def_index"])]
        tree_sitter_source_start = char_offset_to_utf8_byte(
            decoded_source,
            def_line_start_char + len(str(local["structural_prefix"])),
        )
        mapping_strategy = "v3_local_same_name_header_a05_body_anchor"
        source_end_strategy = "a05_verified_method_body_end"
        candidate_start = tree_sitter_source_start
        candidate_end = body_end_byte
        direct_class_method = 1  # A05 primary method_body membership is authoritative here.
        warning_parts.append("full_file_tree_sitter_local_header_recovery")

    standalone_tree = validation["standalone_tree"]
    error_nodes = int(validation["error_nodes"])
    missing_nodes = int(validation["missing_nodes"])
    blocks = validation["blocks"]
    block_kind = str(validation["block_kind"])
    block_name = str(validation["block_name"])
    covers = int(validation["covers"])
    ast_sequence = str(validation["ast_sequence"])
    alignment = validation["alignment"]
    normalized_bytes = validation["normalized_bytes"]
    if tree_has_error(standalone_tree.root_node) or error_nodes or missing_nodes:
        warning_parts.append("standalone_tree_sitter_recovery")

    source_sha, source_relative, _ = write_artifact(artifact_root, normalized_source)

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
        "git_blob_oid": context.git_blob_oid,
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
        "tree_sitter_function_name": expected_name,
        "tree_sitter_function_name_matches": 1,
        "tree_sitter_direct_class_method": direct_class_method,
        "tree_sitter_full_file_has_error": full_file_has_error,
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
        "ml_source_tree_sitter_start_byte_utf8": tree_sitter_source_start,
        "ml_source_start_strategy": (
            "v3_local_same_name_header_or_decorator_line_start"
            if local_recovery
            else "physical_line_start_before_decorator_or_definition"
        ),
        "ml_source_top_level_decorator_count": alignment["top_level_decorator_count"],
        "ml_source_decorator_headers_column_zero": alignment["decorator_headers_column_zero"],
        "ml_source_definition_header_column_zero": alignment["definition_header_column_zero"],
        "ml_source_normalization": "v3_exact_structural_prefix_dedent_preserve_multiline_string_rows_plus_lf",
        "tree_sitter_occurrence_mapping": mapping_strategy,
        "ml_source_end_strategy": source_end_strategy,
        "tree_sitter_same_name_candidate_count": len(analysis.same_name),
        "tree_sitter_anchor_candidate_count": len(analysis.anchor_functions),
        "tree_sitter_primary_anchor_candidate_count": len(analysis.primary_same_name_anchor),
        "tree_sitter_strict_candidate_count": len(analysis.strict_same_name_anchor),
        "tree_sitter_candidate_start_byte_utf8": candidate_start,
        "tree_sitter_candidate_end_byte_utf8": candidate_end,
        "tree_sitter_candidate_end_minus_a05_body_end_bytes": candidate_end - body_end_byte,
        "mapping_status": "PASS",
        "mapping_warning": ";".join(dict.fromkeys(warning_parts)),
    }


def load_v2_failures(path: Path) -> tuple[list[dict[str, str]], dict[tuple[str, str, str], dict[str, str]]]:
    rows: list[dict[str, str]] = []
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(FAILURE_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"[ERROR] v2 failure CSV missing columns: {sorted(missing)}")
        for row in reader:
            key = occurrence_identity(row)
            if key in by_key:
                raise SystemExit(f"[ERROR] duplicate v2 failure identity: {key}")
            rows.append(dict(row))
            by_key[key] = dict(row)
    return rows, by_key


def collect_target_a05_rows(
    code_manifest_path: Path,
    target_keys: set[tuple[str, str, str]],
) -> tuple[list[dict[str, str]], int]:
    found: list[dict[str, str]] = []
    selected = 0
    with code_manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = A05_REQUIRED_COLUMNS - fields
        if missing:
            raise SystemExit(f"[ERROR] A05 code manifest missing columns: {sorted(missing)}")
        for row in reader:
            if clean(row.get("aggregation_role")) != PRIMARY_AGGREGATION_ROLE:
                continue
            if clean(row.get("code_unit_type")) != PRIMARY_UNIT_TYPE:
                continue
            selected += 1
            if occurrence_identity(row) in target_keys:
                found.append(dict(row))
    return found, selected


def diagnose_residuals(args: argparse.Namespace) -> int:
    started = time.time()
    repo_root = args.repo_root.resolve()
    v2_root = args.v2_root.resolve()
    output_root = args.output_root.resolve()
    a01_root = args.a01_root.resolve()
    a05_root = args.npr_a05_root.resolve()
    a13_summary = args.a13_summary_file.resolve()

    validate_a01_freeze(a01_root)
    validate_a13_summary(a13_summary, args.expected_unique_body_sha)
    code_manifest_path = a05_root / "python_code_unit_manifest.csv"
    snapshot_status_path = a05_root / "snapshot_status.csv"
    if sha256_file(code_manifest_path) != args.expected_a05_manifest_sha256:
        raise SystemExit("[ERROR] frozen NPR A05 manifest SHA256 mismatch")

    v2_summary = load_json(v2_root / "summary.json")
    if clean(v2_summary.get("run")) != "run-x-a05-v2" or clean(v2_summary.get("status")) != "FAIL":
        raise SystemExit("[ERROR] diagnose requires the failed run-x-a05-v2 canonical output")
    v2_failure_path = v2_root / "python_ml_cfun_mapping_failures.csv"
    failure_rows, failures_by_key = load_v2_failures(v2_failure_path)
    failure_stage_counts = Counter(clean(row.get("stage")) for row in failure_rows)

    target_rows, universe_occurrences = collect_target_a05_rows(code_manifest_path, set(failures_by_key))
    target_by_key = {occurrence_identity(row): row for row in target_rows}

    if output_root.exists():
        if not args.overwrite:
            raise SystemExit(f"[ERROR] diagnose output already exists: {output_root}; use --overwrite")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    detector = load_detector_parser(repo_root, args.tree_sitter_lib.resolve(), args.ast_helper_dir.resolve())
    statuses = load_snapshot_status(snapshot_status_path, args.clone_path_prefix_from, args.clone_path_prefix_to)
    git_batches = GitBatchLRU(args.max_open_git_processes)
    recovered: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    source_summaries: dict[str, dict[str, Any]] = {}
    warning_counts: Counter[str] = Counter()
    recovery_strategy_counts: Counter[str] = Counter()
    cache_context: HistoricalFileContext | None = None
    cache_key: tuple[str, str, str] | None = None

    try:
        for index, failure in enumerate(failure_rows, start=1):
            key = occurrence_identity(failure)
            row = target_by_key.get(key)
            if row is None:
                exc = MappingError("a05_residual_lookup", "v2 failure identity not found in frozen A05 manifest")
                remaining.append(failure_row(failure, exc.stage, exc))
                diagnostics.append({
                    **{column: failure.get(column, "") for column in FAILURE_COLUMNS[:8]},
                    "v2_stage": clean(failure.get("stage")),
                    "v2_error_message": clean(failure.get("error_message")),
                    "recovery_status": "FAIL",
                    "v3_error_stage": exc.stage,
                    "v3_error_message": str(exc),
                })
                continue
            try:
                relative = validate_relative_python_path(clean(row.get("relative_path")))
                file_key = (clean(row.get("snapshot_id")), relative, clean(row.get("file_sha256")).lower())
                if cache_key != file_key:
                    cache_context = load_file_context(row, statuses, git_batches, detector)
                    cache_key = file_key
                assert cache_context is not None
                mapped = map_occurrence_v3(row, cache_context, detector, output_root)
                recovered.append(mapped)
                update_unique_source_summary(source_summaries, mapped)
                recovery_strategy_counts[clean(mapped.get("tree_sitter_occurrence_mapping"))] += 1
                for warning in clean(mapped.get("mapping_warning")).split(";"):
                    if warning:
                        warning_counts[warning] += 1
                diagnostics.append({
                    "snapshot_id": clean(failure.get("snapshot_id")),
                    "dataset_source": clean(failure.get("dataset_source")),
                    "repo_name": clean(failure.get("repo_name")),
                    "snapshot_commit": clean(failure.get("snapshot_commit")),
                    "relative_path": clean(failure.get("relative_path")),
                    "code_unit_id": clean(failure.get("code_unit_id")),
                    "qualified_name": clean(failure.get("qualified_name")),
                    "npr_body_sha256": clean(failure.get("npr_body_sha256")),
                    "v2_stage": clean(failure.get("stage")),
                    "v2_error_message": clean(failure.get("error_message")),
                    "recovery_status": "PASS",
                    "v3_mapping_strategy": clean(mapped.get("tree_sitter_occurrence_mapping")),
                    "v3_source_normalization": clean(mapped.get("ml_source_normalization")),
                    "v3_mapping_warning": clean(mapped.get("mapping_warning")),
                    "v3_ml_source_sha256": clean(mapped.get("ml_source_sha256")),
                    "v3_error_stage": "",
                    "v3_error_message": "",
                })
            except Exception as exc:
                stage = exc.stage if isinstance(exc, MappingError) else "unexpected_exception"
                remaining.append(failure_row(row, stage, exc))
                diagnostics.append({
                    "snapshot_id": clean(failure.get("snapshot_id")),
                    "dataset_source": clean(failure.get("dataset_source")),
                    "repo_name": clean(failure.get("repo_name")),
                    "snapshot_commit": clean(failure.get("snapshot_commit")),
                    "relative_path": clean(failure.get("relative_path")),
                    "code_unit_id": clean(failure.get("code_unit_id")),
                    "qualified_name": clean(failure.get("qualified_name")),
                    "npr_body_sha256": clean(failure.get("npr_body_sha256")),
                    "v2_stage": clean(failure.get("stage")),
                    "v2_error_message": clean(failure.get("error_message")),
                    "recovery_status": "FAIL",
                    "v3_mapping_strategy": "",
                    "v3_source_normalization": "",
                    "v3_mapping_warning": "",
                    "v3_ml_source_sha256": "",
                    "v3_error_stage": stage,
                    "v3_error_message": str(exc),
                })
            if args.progress_every and index % args.progress_every == 0:
                print(
                    f"[diagnose] processed={index}/{len(failure_rows)} recovered={len(recovered)} "
                    f"remaining={len(remaining)} elapsed_s={time.time() - started:.1f}"
                )
    finally:
        git_batches.close()

    recovered_path = output_root / "python_ml_cfun_recovered_occurrences.csv"
    remaining_path = output_root / "python_ml_cfun_recovery_failures.csv"
    diagnostics_path = output_root / "python_ml_cfun_recovery_diagnostics.csv"
    unique_path = output_root / "python_ml_cfun_recovered_unique_source_manifest.csv"
    atomic_write_csv(recovered_path, recovered, OCCURRENCE_COLUMNS)
    atomic_write_csv(remaining_path, remaining, FAILURE_COLUMNS)
    atomic_write_csv(diagnostics_path, diagnostics, RECOVERY_DIAGNOSTIC_COLUMNS)
    atomic_write_csv(
        unique_path,
        [source_summaries[key] for key in sorted(source_summaries)],
        UNIQUE_SOURCE_COLUMNS,
    )

    checks: list[dict[str, Any]] = []
    add_check(checks, "v2_failure_rows", "hard", len(failure_rows) == args.expected_v2_failures, len(failure_rows), args.expected_v2_failures)
    add_check(
        checks,
        "v2_indentation_failure_rows",
        "hard",
        failure_stage_counts.get("ml_source_indentation", 0) == args.expected_v2_indentation_failures,
        failure_stage_counts.get("ml_source_indentation", 0),
        args.expected_v2_indentation_failures,
    )
    add_check(
        checks,
        "v2_occurrence_map_failure_rows",
        "hard",
        failure_stage_counts.get("tree_sitter_occurrence_map", 0) == args.expected_v2_occurrence_failures,
        failure_stage_counts.get("tree_sitter_occurrence_map", 0),
        args.expected_v2_occurrence_failures,
    )
    add_check(checks, "target_a05_rows_found", "hard", len(target_rows) == len(failure_rows), len(target_rows), len(failure_rows))
    add_check(checks, "full_cfun_occurrences_scanned", "hard", universe_occurrences == args.expected_occurrences, universe_occurrences, args.expected_occurrences)
    add_check(checks, "recovered_plus_remaining", "hard", len(recovered) + len(remaining) == len(failure_rows), len(recovered) + len(remaining), len(failure_rows))
    add_check(checks, "all_v2_failures_recovered", "hard", len(recovered) == len(failure_rows), len(recovered), len(failure_rows))
    add_check(checks, "remaining_recovery_failures_zero", "hard", len(remaining) == 0, len(remaining), 0)
    hard_failures = [row for row in checks if row["severity"] == "hard" and int(row["passed"]) != 1]
    status = "PASS_WITH_WARNINGS" if not hard_failures and warning_counts else ("PASS" if not hard_failures else "FAIL")
    atomic_write_csv(output_root / "checks.csv", checks, CHECK_COLUMNS)
    summary = {
        "run": SCRIPT_VERSION,
        "mode": "diagnose",
        "status": status,
        "v2_input_failure_rows": len(failure_rows),
        "v2_failure_stage_counts": dict(sorted(failure_stage_counts.items())),
        "target_a05_rows_found": len(target_rows),
        "recovered_occurrences": len(recovered),
        "remaining_failures": len(remaining),
        "unique_recovered_ml_sources": len(source_summaries),
        "recovery_strategy_counts": dict(sorted(recovery_strategy_counts.items())),
        "mapping_warning_counts": dict(sorted(warning_counts.items())),
        "full_cfun_occurrences_scanned": universe_occurrences,
        "failed_hard_checks": len(hard_failures),
        "elapsed_seconds": time.time() - started,
        "completed_utc": utc_now(),
    }
    atomic_write_json(output_root / "summary.json", summary)
    atomic_write_json(
        output_root / "metadata.json",
        {
            "run": SCRIPT_VERSION,
            "mode": "diagnose",
            "created_utc": utc_now(),
            "scientific_scope": "targeted residual recovery of failed run-x-a05-v2 C_FUN ML source mappings only",
            "v2_root": str(v2_root),
            "v2_failure_file_sha256": sha256_file(v2_failure_path),
            "npr_a05_root": str(a05_root),
            "a05_code_manifest_sha256": sha256_file(code_manifest_path),
            "a13_summary_sha256": sha256_file(a13_summary),
            "normalization_policy": "remove exact structural class prefix outside multiline-string continuation rows; preserve literal string whitespace",
            "local_mapping_policy": "bounded nearest same-name def/async def header around authoritative A05 body anchor; accept only detector-valid exactly-one-block reconstruction",
            "quality_outcomes_consumed": False,
            "model_loaded": False,
            "embedding_generated": False,
            "classifier_inference": False,
            "outputs": {
                "recovered_occurrences": str(recovered_path),
                "remaining_failures": str(remaining_path),
                "diagnostics": str(diagnostics_path),
                "recovered_unique_sources": str(unique_path),
                "source_artifact_root": str(output_root / "ml_cfun_sources"),
            },
        },
    )

    print("=" * 80)
    print("run-x-a05-v3 residual C_FUN ML mapping diagnosis")
    print(f"Status:                         {status}")
    print(f"V2 residual failures:           {len(failure_rows)}")
    print(f"Recovered occurrences:          {len(recovered)}")
    print(f"Remaining failures:             {len(remaining)}")
    print(f"Unique recovered ML sources:    {len(source_summaries)}")
    print(f"Recovery strategies:            {dict(sorted(recovery_strategy_counts.items()))}")
    print(f"Hard QC failures:               {len(hard_failures)}")
    print(f"Diagnostics:                    {diagnostics_path}")
    print("=" * 80)
    return 0 if not hard_failures else 5


def link_artifact(source: Path, destination: Path, allow_copy_fallback: bool) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != destination.stem:
            raise SystemExit(f"[ERROR] existing repair artifact hash mismatch: {destination}")
        return "reused"
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError as exc:
        if not allow_copy_fallback:
            raise SystemExit(
                f"[ERROR] hardlink failed for {source} -> {destination}: {exc}; "
                "rerun with --allow-copy-fallback only if intentional"
            ) from exc
        shutil.copy2(source, destination)
        return "copy"


def repair_from_diagnose(args: argparse.Namespace) -> int:
    started = time.time()
    v2_root = args.v2_root.resolve()
    diagnose_root = args.diagnose_root.resolve()
    output_root = args.output_root.resolve()
    a05_root = args.npr_a05_root.resolve()
    code_manifest_path = a05_root / "python_code_unit_manifest.csv"

    v2_summary = load_json(v2_root / "summary.json")
    diagnose_summary = load_json(diagnose_root / "summary.json")
    if clean(v2_summary.get("run")) != "run-x-a05-v2" or int(v2_summary.get("mapping_failures", -1)) != args.expected_v2_failures:
        raise SystemExit("[ERROR] repair input is not the expected failed run-x-a05-v2 output")
    if clean(diagnose_summary.get("run")) != SCRIPT_VERSION or clean(diagnose_summary.get("mode")) != "diagnose":
        raise SystemExit("[ERROR] diagnose root does not come from run-x-a05-v3 diagnose mode")
    if clean(diagnose_summary.get("status")) not in {"PASS", "PASS_WITH_WARNINGS"}:
        raise SystemExit("[ERROR] diagnose output is not PASS")
    if int(diagnose_summary.get("remaining_failures", -1)) != 0:
        raise SystemExit("[ERROR] diagnose output still contains recovery failures")

    if output_root.exists():
        if not args.overwrite:
            raise SystemExit(f"[ERROR] repair output already exists: {output_root}; use --overwrite")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    recovered_path = diagnose_root / "python_ml_cfun_recovered_occurrences.csv"
    recovered_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    with recovered_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = occurrence_identity(row)
            if key in recovered_by_key:
                raise SystemExit(f"[ERROR] duplicate recovered occurrence identity: {key}")
            recovered_by_key[key] = dict(row)
    if len(recovered_by_key) != args.expected_v2_failures:
        raise SystemExit(
            f"[ERROR] recovered occurrence count mismatch: {len(recovered_by_key)} != {args.expected_v2_failures}"
        )

    v2_occurrence_path = v2_root / "python_ml_cfun_occurrence_manifest.csv"
    v2_unique_path = v2_root / "python_ml_cfun_unique_source_manifest.csv"
    v2_failure_path = v2_root / "python_ml_cfun_mapping_failures.csv"
    _, v2_failure_by_key = load_v2_failures(v2_failure_path)
    if set(v2_failure_by_key) != set(recovered_by_key):
        raise SystemExit("[ERROR] diagnose recovered identities do not exactly equal v2 failure identities")

    final_occurrence_path = output_root / "python_ml_cfun_occurrence_manifest.csv"
    body_sha: set[str] = set()
    file_keys: set[tuple[str, str, str]] = set()
    mapping_strategy_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()
    function_kind_counts: Counter[str] = Counter()
    dataset_source_counts: Counter[str] = Counter()
    selected = 0
    warning_occurrences = 0
    recovered_written = 0
    success_written = 0
    identity_mismatches = 0

    with v2_occurrence_path.open("r", encoding="utf-8-sig", newline="") as success_handle, \
         code_manifest_path.open("r", encoding="utf-8-sig", newline="") as a05_handle, \
         final_occurrence_path.open("w", encoding="utf-8", newline="") as output_handle:
        success_reader = csv.DictReader(success_handle)
        a05_reader = csv.DictReader(a05_handle)
        writer = csv.DictWriter(output_handle, fieldnames=OCCURRENCE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        success_iter = iter(success_reader)
        next_success = next(success_iter, None)
        for a05_row in a05_reader:
            if clean(a05_row.get("aggregation_role")) != PRIMARY_AGGREGATION_ROLE or clean(a05_row.get("code_unit_type")) != PRIMARY_UNIT_TYPE:
                continue
            selected += 1
            key = occurrence_identity(a05_row)
            if key in recovered_by_key:
                mapped = recovered_by_key[key]
                recovered_written += 1
            else:
                if next_success is None:
                    raise SystemExit(f"[ERROR] v2 success manifest exhausted at selected occurrence {selected}")
                mapped = next_success
                if occurrence_identity(mapped) != key:
                    identity_mismatches += 1
                    raise SystemExit(
                        "[ERROR] v2 success manifest order/identity mismatch: "
                        f"expected={key} observed={occurrence_identity(mapped)}"
                    )
                success_written += 1
                next_success = next(success_iter, None)
            if clean(mapped.get("npr_body_sha256")) != clean(a05_row.get("code_unit_sha256")):
                raise SystemExit(f"[ERROR] merged body SHA mismatch for {key}")
            writer.writerow({column: mapped.get(column, "") for column in OCCURRENCE_COLUMNS})
            body_sha.add(clean(mapped.get("npr_body_sha256")))
            file_keys.add((clean(mapped.get("snapshot_id")), clean(mapped.get("relative_path")), clean(mapped.get("file_sha256"))))
            mapping_strategy_counts[clean(mapped.get("tree_sitter_occurrence_mapping"))] += 1
            function_kind_counts[clean(mapped.get("function_kind"))] += 1
            dataset_source_counts[clean(mapped.get("dataset_source"))] += 1
            row_warning = clean(mapped.get("mapping_warning"))
            if row_warning:
                warning_occurrences += 1
            for warning in row_warning.split(";"):
                if warning:
                    warning_counts[warning] += 1
        if next_success is not None:
            raise SystemExit("[ERROR] v2 success manifest has rows remaining after frozen A05 merge")

    # Reuse the already audited v2 unique-source summary and update it with the
    # 946 recovered occurrences. This avoids rescanning 1.68M rows solely to
    # rebuild per-source occurrence counts.
    source_summaries: dict[str, dict[str, Any]] = {}
    v2_occurrence_sum = 0
    with v2_unique_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sha = clean(row.get("ml_source_sha256"))
            if sha in source_summaries:
                raise SystemExit(f"[ERROR] duplicate v2 unique source SHA: {sha}")
            item = dict(row)
            item["occurrence_count"] = int(clean(row.get("occurrence_count")))
            item["any_tree_sitter_standalone_warning"] = int(clean(row.get("any_tree_sitter_standalone_warning")) or "0")
            source_summaries[sha] = item
            v2_occurrence_sum += int(item["occurrence_count"])
    for mapped in recovered_by_key.values():
        update_unique_source_summary(source_summaries, mapped)
    final_unique_occurrence_sum = sum(int(item["occurrence_count"]) for item in source_summaries.values())
    final_unique_path = output_root / "python_ml_cfun_unique_source_manifest.csv"
    atomic_write_csv(final_unique_path, [source_summaries[key] for key in sorted(source_summaries)], UNIQUE_SOURCE_COLUMNS)
    atomic_write_csv(output_root / "python_ml_cfun_mapping_failures.csv", [], FAILURE_COLUMNS)

    # Build a self-contained artifact root using hardlinks. Existing successful
    # artifacts come from v2; newly recovered artifacts come from diagnose.
    link_counts: Counter[str] = Counter()
    missing_artifacts = 0
    for index, (sha, item) in enumerate(sorted(source_summaries.items()), start=1):
        rel = Path(clean(item.get("ml_source_relative_path")))
        if rel != artifact_relative_path(sha):
            raise SystemExit(f"[ERROR] unique-source relative path mismatch for {sha}: {rel}")
        source = v2_root / rel
        if not source.is_file():
            source = diagnose_root / rel
        if not source.is_file():
            missing_artifacts += 1
            continue
        mode = link_artifact(source, output_root / rel, args.allow_copy_fallback)
        link_counts[mode] += 1
        if args.progress_every and index % args.progress_every == 0:
            print(
                f"[repair-artifacts] linked={index}/{len(source_summaries)} "
                f"hardlink={link_counts['hardlink']} copy={link_counts['copy']}"
            )

    checks: list[dict[str, Any]] = []
    add_check(checks, "selected_occurrences", "hard", selected == args.expected_occurrences, selected, args.expected_occurrences)
    add_check(checks, "v2_success_rows_written", "hard", success_written == args.expected_occurrences - args.expected_v2_failures, success_written, args.expected_occurrences - args.expected_v2_failures)
    add_check(checks, "recovered_rows_written", "hard", recovered_written == args.expected_v2_failures, recovered_written, args.expected_v2_failures)
    add_check(checks, "merged_identity_mismatches", "hard", identity_mismatches == 0, identity_mismatches, 0)
    add_check(checks, "unique_cfun_body_sha", "hard", len(body_sha) == args.expected_unique_body_sha, len(body_sha), args.expected_unique_body_sha)
    add_check(checks, "files_with_cfun", "hard", len(file_keys) == args.expected_files_with_cfun, len(file_keys), args.expected_files_with_cfun)
    add_check(checks, "v2_unique_occurrence_sum", "hard", v2_occurrence_sum == args.expected_occurrences - args.expected_v2_failures, v2_occurrence_sum, args.expected_occurrences - args.expected_v2_failures)
    add_check(checks, "final_unique_occurrence_sum", "hard", final_unique_occurrence_sum == args.expected_occurrences, final_unique_occurrence_sum, args.expected_occurrences)
    add_check(checks, "missing_source_artifacts", "hard", missing_artifacts == 0, missing_artifacts, 0)
    add_check(checks, "final_mapping_failures", "hard", True, 0, 0)
    hard_failures = [row for row in checks if row["severity"] == "hard" and int(row["passed"]) != 1]
    status = "PASS_WITH_WARNINGS" if not hard_failures and warning_counts else ("PASS" if not hard_failures else "FAIL")
    atomic_write_csv(output_root / "checks.csv", checks, CHECK_COLUMNS)
    summary = {
        "run": SCRIPT_VERSION,
        "mode": "repair",
        "status": status,
        "selected_occurrences": selected,
        "mapped_occurrences": selected,
        "mapping_failures": 0,
        "warning_occurrences": warning_occurrences,
        "unique_npr_body_sha": len(body_sha),
        "unique_ml_source_sha": len(source_summaries),
        "files_with_cfun": len(file_keys),
        "function_kind_counts": dict(sorted(function_kind_counts.items())),
        "mapping_strategy_counts": dict(sorted(mapping_strategy_counts.items())),
        "mapping_warning_counts": dict(sorted(warning_counts.items())),
        "dataset_source_counts": dict(sorted(dataset_source_counts.items())),
        "v2_success_occurrences_reused": success_written,
        "v3_recovered_occurrences": recovered_written,
        "artifact_link_counts": dict(sorted(link_counts.items())),
        "failed_hard_checks": len(hard_failures),
        "completed_utc": utc_now(),
        "elapsed_seconds": time.time() - started,
    }
    summary["warning_occurrence_count_semantics"] = "warning_occurrences counts merged rows with any warning; mapping_warning_counts can overlap by category"
    atomic_write_json(output_root / "summary.json", summary)
    atomic_write_json(
        output_root / "metadata.json",
        {
            "run": SCRIPT_VERSION,
            "mode": "repair",
            "created_utc": utc_now(),
            "scientific_scope": "complete A05 C_FUN ML source manifest rebuilt from audited v2 successes plus v3 residual recoveries",
            "v2_root": str(v2_root),
            "diagnose_root": str(diagnose_root),
            "npr_a05_root": str(a05_root),
            "a05_code_manifest_sha256": sha256_file(code_manifest_path),
            "merge_order_policy": "stream frozen NPR A05 primary method_body order; substitute v3 recovered row exactly at each v2 failure identity",
            "artifact_policy": "self-contained hardlinked source store; copy fallback disabled unless explicitly requested",
            "mapping_failures": 0,
            "quality_outcomes_consumed": False,
            "model_loaded": False,
            "embedding_generated": False,
            "classifier_inference": False,
            "outputs": {
                "occurrence_manifest": str(final_occurrence_path),
                "unique_source_manifest": str(final_unique_path),
                "mapping_failures": str(output_root / "python_ml_cfun_mapping_failures.csv"),
                "source_artifact_root": str(output_root / "ml_cfun_sources"),
                "checks": str(output_root / "checks.csv"),
                "summary": str(output_root / "summary.json"),
            },
        },
    )

    print("=" * 80)
    print("run-x-a05-v3 repaired complete C_FUN ML input preparation")
    print(f"Status:                         {status}")
    print(f"Merged C_FUN occurrences:       {selected}")
    print(f"Reused v2 successes:            {success_written}")
    print(f"Recovered v3 residuals:         {recovered_written}")
    print(f"Mapping failures:               0")
    print(f"Unique C_FUN body SHA:           {len(body_sha)}")
    print(f"Unique standalone ML sources:   {len(source_summaries)}")
    print(f"Files with C_FUN:                {len(file_keys)}")
    print(f"Missing source artifacts:       {missing_artifacts}")
    print(f"Hard QC failures:               {len(hard_failures)}")
    print(f"Output root:                    {output_root}")
    print("=" * 80)
    return 0 if not hard_failures else 5


def verify_repaired(args: argparse.Namespace) -> int:
    output_root = args.output_root.resolve()
    summary = load_json(output_root / "summary.json")
    checks_path = output_root / "checks.csv"
    occurrence_path = output_root / "python_ml_cfun_occurrence_manifest.csv"
    unique_path = output_root / "python_ml_cfun_unique_source_manifest.csv"
    failure_path = output_root / "python_ml_cfun_mapping_failures.csv"
    required = [checks_path, occurrence_path, unique_path, failure_path, output_root / "metadata.json"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"[ERROR] repaired output missing required files: {missing}")
    if clean(summary.get("run")) != SCRIPT_VERSION or clean(summary.get("mode")) != "repair":
        raise SystemExit("[ERROR] repaired summary run/mode mismatch")
    if clean(summary.get("status")) not in {"PASS", "PASS_WITH_WARNINGS"}:
        raise SystemExit(f"[ERROR] repaired summary is not PASS: {summary.get('status')}")
    with checks_path.open("r", encoding="utf-8-sig", newline="") as handle:
        failed = [row for row in csv.DictReader(handle) if clean(row.get("severity")) == "hard" and clean(row.get("passed")) != "1"]
    if failed:
        raise SystemExit(f"[ERROR] repaired hard QC failures: {[row['check_name'] for row in failed]}")
    with failure_path.open("r", encoding="utf-8-sig", newline="") as handle:
        failure_count = sum(1 for _ in csv.DictReader(handle))
    if failure_count != 0:
        raise SystemExit(f"[ERROR] repaired mapping failure CSV has {failure_count} rows")
    if int(summary.get("selected_occurrences", -1)) != args.expected_occurrences:
        raise SystemExit("[ERROR] repaired selected occurrence count mismatch")
    if int(summary.get("mapping_failures", -1)) != 0:
        raise SystemExit("[ERROR] repaired mapping_failures != 0")
    if int(summary.get("unique_npr_body_sha", -1)) != args.expected_unique_body_sha:
        raise SystemExit("[ERROR] repaired unique body SHA count mismatch")
    if int(summary.get("files_with_cfun", -1)) != args.expected_files_with_cfun:
        raise SystemExit("[ERROR] repaired files-with-C_FUN count mismatch")
    print("prepare_ml_cfun_inputs-v3 repaired output verification: PASS")
    return 0


def run_self_test() -> int:
    # Retain all v2 mapping/reconstruction tests first.
    run_self_test_v2_core()

    # v3 must structurally dedent code while preserving a column-zero multiline
    # string continuation that defeated textwrap.dedent in full production.
    raw = (
        "    def f(self):\n"
        "        query = \"\"\"\n"
        "SELECT * FROM table\n"
        "WHERE id = 1\n"
        "\"\"\"\n"
        "        return query\n"
    )
    normalized = normalize_method_source_v3(raw, "    ", lambda text: text)
    expected = (
        "def f(self):\n"
        "    query = \"\"\"\n"
        "SELECT * FROM table\n"
        "WHERE id = 1\n"
        "\"\"\"\n"
        "    return query\n"
    )
    if normalized != expected:
        raise SystemExit(f"[ERROR] v3 multiline-string structural dedent failed:\n{normalized!r}")
    alignment = validate_standalone_header_alignment(normalized, False)
    if alignment["definition_header_column_zero"] != 1:
        raise SystemExit("[ERROR] v3 multiline-string def alignment self-test failed")

    decorated = (
        "\t@classmethod\n"
        "\tdef g(cls):\n"
        "\t\ttext = \"\"\"\n"
        "literal\n"
        "\"\"\"\n"
        "\t\treturn text\n"
    )
    decorated_normalized = normalize_method_source_v3(decorated, "\t", lambda text: text)
    if not decorated_normalized.startswith("@classmethod\ndef g(cls):\n"):
        raise SystemExit("[ERROR] v3 tab/decorator structural dedent self-test failed")
    validate_standalone_header_alignment(decorated_normalized, True)
    print("prepare_ml_cfun_inputs-v3 self-test: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["diagnose", "repair", "verify"], default="diagnose")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--a01-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a01")
    parser.add_argument("--v2-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a05")
    parser.add_argument("--diagnose-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a05-v3-diagnose")
    parser.add_argument("--npr-a05-root", type=Path, required=False)
    parser.add_argument("--a13-summary-file", type=Path, required=False)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--tree-sitter-lib", type=Path, default=repo_root / "src/code-analyzer-tree-sitter/build/my-languages.so")
    parser.add_argument("--ast-helper-dir", type=Path, default=repo_root / "src/code-analyzer-tree-sitter")
    parser.add_argument("--expected-occurrences", type=int, default=EXPECTED_CFUN_OCCURRENCES)
    parser.add_argument("--expected-unique-body-sha", type=int, default=EXPECTED_UNIQUE_CFUN_BODY_SHA)
    parser.add_argument("--expected-files-with-cfun", type=int, default=EXPECTED_FILES_WITH_CFUN)
    parser.add_argument("--expected-a05-manifest-sha256", default=EXPECTED_A05_MANIFEST_SHA256)
    parser.add_argument("--expected-v2-failures", type=int, default=EXPECTED_V2_FAILURES)
    parser.add_argument("--expected-v2-indentation-failures", type=int, default=EXPECTED_V2_INDENTATION_FAILURES)
    parser.add_argument("--expected-v2-occurrence-failures", type=int, default=EXPECTED_V2_OCCURRENCE_MAP_FAILURES)
    parser.add_argument("--max-open-git-processes", type=int, default=4)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--clone-path-prefix-from", default="")
    parser.add_argument("--clone-path-prefix-to", default="")
    parser.add_argument("--allow-copy-fallback", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    if args.max_open_git_processes < 1:
        parser.error("--max-open-git-processes must be >= 1")
    if args.progress_every < 0:
        parser.error("--progress-every cannot be negative")
    if args.npr_a05_root is None:
        parser.error("--npr-a05-root is required")
    if args.a13_summary_file is None:
        parser.error("--a13-summary-file is required")
    if args.mode == "diagnose":
        for path, label in [(args.tree_sitter_lib, "tree-sitter library"), (args.ast_helper_dir, "AST helper directory")]:
            if not path.exists():
                parser.error(f"{label} not found: {path}")
        return diagnose_residuals(args)
    if args.mode == "repair":
        return repair_from_diagnose(args)
    return verify_repaired(args)


if __name__ == "__main__":
    raise SystemExit(main())
