#!/usr/bin/env python3
"""
prepare_ml_cfun_inputs-v2.py
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
smoke
    Deterministically sample N C_FUN occurrences spread across the complete
    frozen C_FUN occurrence order. The smoke scan also reconciles the complete
    frozen C_FUN occurrence/body/file universe before mapping the sampled rows.
    This mode is for representation/mapping validation only and never modifies
    the full output root.
full
    Prepare all frozen A05 primary method_body occurrences.
verify
    Read-only verification of the completed full output.

Primary outputs
---------------
python_ml_cfun_occurrence_manifest.csv
    One row per successfully mapped A05 C_FUN occurrence.
python_ml_cfun_unique_source_manifest.csv
    One row per unique detector-native standalone method source SHA-256.
python_ml_cfun_mapping_failures.csv
    Explicit mapping failures. Full production is PASS only when this is empty.
checks.csv
summary.json
metadata.json
ml_cfun_sources/<sha-prefix>/<sha256>.py
    Deduplicated standalone method-source artifacts for downstream A06 scoring.
"""

from __future__ import annotations

import argparse
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


SCRIPT_VERSION = "run-x-a05-v2"
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


def prepare(args: argparse.Namespace) -> int:
    started = time.time()
    repo_root = args.repo_root.resolve()
    a01_root = args.a01_root.resolve()
    a05_root = args.npr_a05_root.resolve()
    a13_summary_path = args.a13_summary_file.resolve()
    output_root = args.output_root.resolve()

    validate_a01_freeze(a01_root)
    validate_a13_summary(a13_summary_path, args.expected_unique_body_sha)

    snapshot_status_path = a05_root / "snapshot_status.csv"
    code_manifest_path = a05_root / "python_code_unit_manifest.csv"
    for path in [snapshot_status_path, code_manifest_path]:
        if not path.is_file():
            raise SystemExit(f"[ERROR] required NPR A05 input not found: {path}")

    observed_a05_sha = sha256_file(code_manifest_path)
    if args.expected_a05_manifest_sha256 and observed_a05_sha != args.expected_a05_manifest_sha256:
        raise SystemExit(
            "[ERROR] frozen A05 code manifest SHA256 mismatch: "
            f"observed={observed_a05_sha} expected={args.expected_a05_manifest_sha256}"
        )

    statuses = load_snapshot_status(
        snapshot_status_path,
        args.clone_path_prefix_from,
        args.clone_path_prefix_to,
    )
    detector = load_detector_parser(repo_root, args.tree_sitter_lib.resolve(), args.ast_helper_dir.resolve())

    if output_root.exists():
        if not args.overwrite:
            raise SystemExit(f"[ERROR] output root already exists: {output_root}; use --overwrite for a clean rerun")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "ml_cfun_sources").mkdir(parents=True, exist_ok=True)

    occurrence_path = output_root / "python_ml_cfun_occurrence_manifest.csv"
    failure_path = output_root / "python_ml_cfun_mapping_failures.csv"
    unique_source_path = output_root / "python_ml_cfun_unique_source_manifest.csv"

    selected_occurrences = 0
    mapped_occurrences = 0
    warning_occurrences = 0
    unique_body_sha: set[str] = set()
    unique_file_keys: set[tuple[str, str, str]] = set()
    unique_source_summaries: dict[str, dict[str, Any]] = {}
    function_kind_counts: Counter[str] = Counter()
    mapping_strategy_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()
    failure_stage_counts: Counter[str] = Counter()
    full_file_parse_error_occurrences = 0
    standalone_parse_warning_occurrences = 0
    end_override_occurrences = 0
    decorated_method_occurrences = 0
    decorator_alignment_failures = 0
    definition_alignment_failures = 0
    sample_dataset_source_counts: Counter[str] = Counter()
    sample_repo_names: set[str] = set()
    universe_occurrences = 0
    universe_body_sha: set[str] = set()
    universe_file_keys: set[tuple[str, str, str]] = set()
    files_loaded = 0
    cache_hits = 0

    git_batches = GitBatchLRU(args.max_open_git_processes)
    current_context: HistoricalFileContext | None = None

    occurrence_temp = occurrence_path.with_name(occurrence_path.name + f".tmp.{os.getpid()}")
    failure_temp = failure_path.with_name(failure_path.name + f".tmp.{os.getpid()}")

    try:
        with code_manifest_path.open("r", encoding="utf-8-sig", newline="") as manifest_handle, \
                occurrence_temp.open("w", encoding="utf-8", newline="") as occurrence_handle, \
                failure_temp.open("w", encoding="utf-8", newline="") as failure_handle:
            reader = csv.DictReader(manifest_handle)
            fields = set(reader.fieldnames or [])
            missing = A05_REQUIRED_COLUMNS - fields
            if missing:
                raise SystemExit(f"[ERROR] A05 code-unit manifest missing columns: {sorted(missing)}")

            occurrence_writer = csv.DictWriter(occurrence_handle, fieldnames=OCCURRENCE_COLUMNS, extrasaction="ignore")
            failure_writer = csv.DictWriter(failure_handle, fieldnames=FAILURE_COLUMNS, extrasaction="ignore")
            occurrence_writer.writeheader()
            failure_writer.writeheader()

            smoke_positions = (
                deterministic_smoke_positions(args.expected_occurrences, args.max_occurrences)
                if args.mode == "smoke" and args.max_occurrences > 0
                else set()
            )

            for row in reader:
                if clean(row.get("aggregation_role")) != PRIMARY_AGGREGATION_ROLE:
                    continue
                if clean(row.get("code_unit_type")) != PRIMARY_UNIT_TYPE:
                    continue

                universe_occurrences += 1
                universe_body_sha.add(clean(row.get("code_unit_sha256")).lower())
                universe_file_key = (
                    clean(row.get("snapshot_id")),
                    clean(row.get("relative_path")),
                    clean(row.get("file_sha256")).lower(),
                )
                universe_file_keys.add(universe_file_key)

                if args.mode == "smoke" and smoke_positions and universe_occurrences not in smoke_positions:
                    continue

                selected_occurrences += 1
                body_sha = clean(row.get("code_unit_sha256")).lower()
                unique_body_sha.add(body_sha)
                file_key = universe_file_key
                unique_file_keys.add(file_key)
                function_kind_counts[clean(row.get("function_kind"))] += 1
                sample_dataset_source_counts[clean(row.get("dataset_source"))] += 1
                sample_repo_names.add(clean(row.get("repo_name")))

                try:
                    if current_context is None or current_context.key != file_key:
                        current_context = load_file_context(row, statuses, git_batches, detector)
                        files_loaded += 1
                    else:
                        cache_hits += 1
                    mapped = map_occurrence(row, current_context, detector, output_root)
                    occurrence_writer.writerow({column: mapped.get(column, "") for column in OCCURRENCE_COLUMNS})
                    mapped_occurrences += 1
                    update_unique_source_summary(unique_source_summaries, mapped)
                    mapping_strategy_counts[clean(mapped.get("tree_sitter_occurrence_mapping"))] += 1
                    warning_text = clean(mapped.get("mapping_warning"))
                    if warning_text:
                        warning_occurrences += 1
                        for warning in warning_text.split(";"):
                            if warning:
                                warning_counts[warning] += 1
                    if int(mapped.get("tree_sitter_full_file_has_error", 0)):
                        full_file_parse_error_occurrences += 1
                    if int(mapped.get("tree_sitter_standalone_has_error", 0)) or int(mapped.get("tree_sitter_standalone_error_nodes", 0)) or int(mapped.get("tree_sitter_standalone_missing_nodes", 0)):
                        standalone_parse_warning_occurrences += 1
                    if clean(mapped.get("ml_source_end_strategy")) == "a05_verified_method_body_end":
                        end_override_occurrences += 1
                    if int(mapped.get("ml_source_includes_decorators", 0)):
                        decorated_method_occurrences += 1
                    if int(mapped.get("ml_source_decorator_headers_column_zero", 0)) != 1:
                        decorator_alignment_failures += 1
                    if int(mapped.get("ml_source_definition_header_column_zero", 0)) != 1:
                        definition_alignment_failures += 1
                except Exception as exc:
                    stage = exc.stage if isinstance(exc, MappingError) else "unexpected_exception"
                    failure_stage_counts[stage] += 1
                    failure_writer.writerow(failure_row(row, stage, exc))
                    # File-context failures may poison repeated rows from the same
                    # file. Drop the cache so the next occurrence revalidates it.
                    if stage in {"clone_path", "git_batch", "git_blob_read", "file_identity", "source_decode", "snapshot_status", "snapshot_identity"}:
                        current_context = None

                if args.progress_every > 0 and selected_occurrences % args.progress_every == 0:
                    elapsed = time.time() - started
                    print(
                        f"[prepare] selected={selected_occurrences} mapped={mapped_occurrences} "
                        f"failures={sum(failure_stage_counts.values())} unique_body_sha={len(unique_body_sha)} "
                        f"unique_ml_source_sha={len(unique_source_summaries)} files_loaded={files_loaded} "
                        f"elapsed_s={elapsed:.1f}",
                        flush=True,
                    )
    finally:
        git_batches.close()

    os.replace(occurrence_temp, occurrence_path)
    os.replace(failure_temp, failure_path)

    unique_source_rows = [unique_source_summaries[key] for key in sorted(unique_source_summaries)]
    atomic_write_csv(unique_source_path, unique_source_rows, UNIQUE_SOURCE_COLUMNS)

    failures = sum(failure_stage_counts.values())
    unique_ml_source_sha = len(unique_source_summaries)
    full_mode = args.mode == "full"

    checks: list[dict[str, Any]] = []
    add_check(checks, "a05_manifest_sha256", "hard", observed_a05_sha == args.expected_a05_manifest_sha256, observed_a05_sha, args.expected_a05_manifest_sha256)
    add_check(checks, "a13_unique_cfun_memberships", "hard", args.expected_unique_body_sha == int(load_json(a13_summary_path).get("cfun_unique_unit_memberships", -1)), int(load_json(a13_summary_path).get("cfun_unique_unit_memberships", -1)), args.expected_unique_body_sha)
    add_check(checks, "mapped_plus_failures_equals_selected", "hard", mapped_occurrences + failures == selected_occurrences, mapped_occurrences + failures, selected_occurrences)
    add_check(checks, "mapping_failures_zero", "hard", failures == 0, failures, 0)
    add_check(checks, "unique_ml_sources_positive", "hard", unique_ml_source_sha > 0, unique_ml_source_sha, ">0")
    add_check(checks, "decorator_alignment_failures_zero", "hard", decorator_alignment_failures == 0, decorator_alignment_failures, 0)
    add_check(checks, "definition_alignment_failures_zero", "hard", definition_alignment_failures == 0, definition_alignment_failures, 0)
    add_check(checks, "ml_source_indentation_failures_zero", "hard", failure_stage_counts.get("ml_source_indentation", 0) == 0, failure_stage_counts.get("ml_source_indentation", 0), 0)

    if full_mode and args.strict_expected_counts:
        add_check(checks, "full_cfun_occurrences", "hard", selected_occurrences == args.expected_occurrences, selected_occurrences, args.expected_occurrences)
        add_check(checks, "full_unique_cfun_body_sha", "hard", len(unique_body_sha) == args.expected_unique_body_sha, len(unique_body_sha), args.expected_unique_body_sha)
        add_check(checks, "full_files_with_cfun", "hard", len(unique_file_keys) == args.expected_files_with_cfun, len(unique_file_keys), args.expected_files_with_cfun)
    else:
        add_check(checks, "smoke_or_non_strict_selected_positive", "hard", selected_occurrences > 0, selected_occurrences, ">0")
        if args.mode == "smoke":
            expected_sample = min(args.max_occurrences, args.expected_occurrences)
            add_check(checks, "smoke_sample_size", "hard", selected_occurrences == expected_sample, selected_occurrences, expected_sample)
            add_check(checks, "smoke_full_universe_occurrences", "hard", universe_occurrences == args.expected_occurrences, universe_occurrences, args.expected_occurrences)
            add_check(checks, "smoke_full_universe_unique_body_sha", "hard", len(universe_body_sha) == args.expected_unique_body_sha, len(universe_body_sha), args.expected_unique_body_sha)
            add_check(checks, "smoke_full_universe_files_with_cfun", "hard", len(universe_file_keys) == args.expected_files_with_cfun, len(universe_file_keys), args.expected_files_with_cfun)
            add_check(checks, "smoke_control_and_treatment_present", "hard", sample_dataset_source_counts.get("control", 0) > 0 and sample_dataset_source_counts.get("treatment", 0) > 0, dict(sorted(sample_dataset_source_counts.items())), "control>0 and treatment>0")

    hard_failures = [row for row in checks if row["severity"] == "hard" and int(row["passed"]) != 1]
    status = "PASS_WITH_WARNINGS" if not hard_failures and warning_occurrences else ("PASS" if not hard_failures else "FAIL")

    atomic_write_csv(output_root / "checks.csv", checks, CHECK_COLUMNS)
    summary = {
        "run": SCRIPT_VERSION,
        "status": status,
        "mode": args.mode,
        "category": "C_FUN",
        "code_unit_type": PRIMARY_UNIT_TYPE,
        "aggregation_role": PRIMARY_AGGREGATION_ROLE,
        "selected_occurrences": selected_occurrences,
        "mapped_occurrences": mapped_occurrences,
        "mapping_failures": failures,
        "warning_occurrences": warning_occurrences,
        "unique_npr_body_sha": len(unique_body_sha),
        "unique_ml_source_sha": unique_ml_source_sha,
        "files_with_cfun": len(unique_file_keys),
        "function_kind_counts": dict(sorted(function_kind_counts.items())),
        "mapping_strategy_counts": dict(sorted(mapping_strategy_counts.items())),
        "mapping_warning_counts": dict(sorted(warning_counts.items())),
        "failure_stage_counts": dict(sorted(failure_stage_counts.items())),
        "full_file_tree_error_occurrences": full_file_parse_error_occurrences,
        "standalone_tree_warning_occurrences": standalone_parse_warning_occurrences,
        "a05_end_override_occurrences": end_override_occurrences,
        "decorated_method_occurrences": decorated_method_occurrences,
        "decorator_alignment_failures": decorator_alignment_failures,
        "definition_alignment_failures": definition_alignment_failures,
        "sample_dataset_source_counts": dict(sorted(sample_dataset_source_counts.items())),
        "sample_repositories": len(sample_repo_names),
        "universe_cfun_occurrences_scanned": universe_occurrences,
        "universe_unique_npr_body_sha": len(universe_body_sha),
        "universe_files_with_cfun": len(universe_file_keys),
        "historical_files_loaded": files_loaded,
        "consecutive_file_cache_hits": cache_hits,
        "failed_hard_checks": len(hard_failures),
        "completed_utc": utc_now(),
        "elapsed_seconds": time.time() - started,
    }
    atomic_write_json(output_root / "summary.json", summary)

    metadata = {
        "run": SCRIPT_VERSION,
        "created_utc": utc_now(),
        "scientific_scope": "frozen ML detector input preparation for A05 primary C_FUN/method_body historical occurrences",
        "identity_contract": "same repository -> same historical commit -> same Python file -> same A05 primary method_body occurrence",
        "representation_contract": "detector-native standalone method source reconstructed around the independently verified A05 method body",
        "primary_cfun_filter": {"aggregation_role": PRIMARY_AGGREGATION_ROLE, "code_unit_type": PRIMARY_UNIT_TYPE},
        "method_locator": "same-name direct-class-method Tree-sitter node containing verified A05 body-start anchor",
        "strict_end_policy": "Tree-sitter method end must not exceed A05 body end",
        "recovery_end_policy": "for a unique direct-class-method anchor, reuse Tree-sitter start and authoritative A05 method end",
        "ml_source_start_policy": "move Tree-sitter decorated/function start to the beginning of its physical source line before dedent",
        "ml_source_normalization": "physical_line_start_then_strip_block_markers_then_textwrap_dedent_strip_plus_lf",
        "standalone_header_alignment_policy": "top-level decorators and def/async def header must begin in column zero after normalization",
        "smoke_selection_policy": "deterministic evenly spaced positions over the complete frozen C_FUN occurrence order",
        "quality_outcomes_consumed": False,
        "model_loaded": False,
        "embedding_generated": False,
        "classifier_inference": False,
        "threshold_calibrated": False,
        "a01_root": str(a01_root),
        "npr_a05_root": str(a05_root),
        "a13_summary_file": str(a13_summary_path),
        "a05_code_manifest_sha256": observed_a05_sha,
        "a05_snapshot_status_sha256": sha256_file(snapshot_status_path),
        "a13_summary_sha256": sha256_file(a13_summary_path),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "tree_sitter_lib": str(args.tree_sitter_lib.resolve()),
        "tree_sitter_lib_sha256": sha256_file(args.tree_sitter_lib.resolve()),
        "ast_helper_dir": str(args.ast_helper_dir.resolve()),
        "expected_full_counts": {
            "cfun_occurrences": args.expected_occurrences,
            "unique_cfun_body_sha": args.expected_unique_body_sha,
            "files_with_cfun": args.expected_files_with_cfun,
        },
        "outputs": {
            "occurrence_manifest": str(occurrence_path),
            "unique_source_manifest": str(unique_source_path),
            "mapping_failures": str(failure_path),
            "source_artifact_root": str(output_root / "ml_cfun_sources"),
            "checks": str(output_root / "checks.csv"),
            "summary": str(output_root / "summary.json"),
        },
    }
    atomic_write_json(output_root / "metadata.json", metadata)

    print("=" * 80)
    print("run-x-a05 C_FUN ML input preparation")
    print(f"Status:                         {status}")
    print(f"Mode:                           {args.mode}")
    print(f"Selected C_FUN occurrences:     {selected_occurrences}")
    print(f"Mapped occurrences:             {mapped_occurrences}")
    print(f"Mapping failures:               {failures}")
    print(f"Warning occurrences:            {warning_occurrences}")
    print(f"Unique C_FUN body SHA:           {len(unique_body_sha)}")
    print(f"Unique standalone ML sources:   {unique_ml_source_sha}")
    print(f"Files with C_FUN:                {len(unique_file_keys)}")
    print(f"A05-end override occurrences:   {end_override_occurrences}")
    print(f"Decorated method occurrences:   {decorated_method_occurrences}")
    print(f"Decorator alignment failures:   {decorator_alignment_failures}")
    print(f"Definition alignment failures:  {definition_alignment_failures}")
    if args.mode == "smoke":
        print(f"Smoke dataset-source counts:    {dict(sorted(sample_dataset_source_counts.items()))}")
        print(f"Smoke repositories represented: {len(sample_repo_names)}")
        print(f"Full C_FUN universe scanned:     {universe_occurrences}")
    print(f"Hard QC failures:               {len(hard_failures)}")
    print(f"Occurrence manifest:            {occurrence_path}")
    print(f"Unique source manifest:         {unique_source_path}")
    print(f"Mapping failures:               {failure_path}")
    print("=" * 80)
    return 0 if not hard_failures else 5


def verify_output(args: argparse.Namespace) -> int:
    output_root = args.output_root.resolve()
    required = [
        output_root / "summary.json",
        output_root / "metadata.json",
        output_root / "checks.csv",
        output_root / "python_ml_cfun_occurrence_manifest.csv",
        output_root / "python_ml_cfun_unique_source_manifest.csv",
        output_root / "python_ml_cfun_mapping_failures.csv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        print(f"A05 output verification: FAIL; missing={missing}", file=sys.stderr)
        return 1

    summary = load_json(output_root / "summary.json")
    failures: list[str] = []
    if summary.get("run") != SCRIPT_VERSION:
        failures.append(f"run={summary.get('run')!r}")
    if summary.get("status") not in {"PASS", "PASS_WITH_WARNINGS"}:
        failures.append(f"status={summary.get('status')!r}")
    if int(summary.get("failed_hard_checks", -1)) != 0:
        failures.append("failed_hard_checks != 0")
    if int(summary.get("selected_occurrences", -1)) != args.expected_occurrences:
        failures.append("selected_occurrences mismatch")
    if int(summary.get("mapped_occurrences", -1)) != args.expected_occurrences:
        failures.append("mapped_occurrences mismatch")
    if int(summary.get("mapping_failures", -1)) != 0:
        failures.append("mapping_failures != 0")
    if int(summary.get("unique_npr_body_sha", -1)) != args.expected_unique_body_sha:
        failures.append("unique_npr_body_sha mismatch")
    if int(summary.get("files_with_cfun", -1)) != args.expected_files_with_cfun:
        failures.append("files_with_cfun mismatch")

    occurrence_path = output_root / "python_ml_cfun_occurrence_manifest.csv"
    row_count = 0
    code_unit_ids: set[str] = set()
    body_sha: set[str] = set()
    file_keys: set[tuple[str, str, str]] = set()
    source_sha: set[str] = set()
    with occurrence_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing_columns = set(OCCURRENCE_COLUMNS) - fields
        if missing_columns:
            failures.append(f"occurrence manifest missing columns={sorted(missing_columns)}")
        for row in reader:
            row_count += 1
            code_unit_id = clean(row.get("code_unit_id"))
            if code_unit_id in code_unit_ids:
                failures.append(f"duplicate code_unit_id={code_unit_id}")
                break
            code_unit_ids.add(code_unit_id)
            body_sha.add(clean(row.get("npr_body_sha256")))
            file_keys.add((clean(row.get("snapshot_id")), clean(row.get("relative_path")), clean(row.get("file_sha256"))))
            source_sha.add(clean(row.get("ml_source_sha256")))
            if clean(row.get("code_unit_type")) != PRIMARY_UNIT_TYPE or clean(row.get("aggregation_role")) != PRIMARY_AGGREGATION_ROLE:
                failures.append("non-C_FUN row found in occurrence manifest")
                break
            if int(clean(row.get("ml_source_decorator_headers_column_zero")) or "0") != 1:
                failures.append("decorator header alignment failure in occurrence manifest")
                break
            if int(clean(row.get("ml_source_definition_header_column_zero")) or "0") != 1:
                failures.append("definition header alignment failure in occurrence manifest")
                break

    if row_count != args.expected_occurrences:
        failures.append(f"row_count={row_count}")
    if len(body_sha) != args.expected_unique_body_sha:
        failures.append(f"body_sha_count={len(body_sha)}")
    if len(file_keys) != args.expected_files_with_cfun:
        failures.append(f"file_key_count={len(file_keys)}")

    failure_path = output_root / "python_ml_cfun_mapping_failures.csv"
    with failure_path.open("r", encoding="utf-8", newline="") as handle:
        failure_count = sum(1 for _ in csv.DictReader(handle))
    if failure_count:
        failures.append(f"mapping_failure_rows={failure_count}")

    unique_source_path = output_root / "python_ml_cfun_unique_source_manifest.csv"
    unique_rows = 0
    unique_manifest_sha: set[str] = set()
    artifact_failures = 0
    with unique_source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            unique_rows += 1
            digest = clean(row.get("ml_source_sha256"))
            if digest in unique_manifest_sha:
                failures.append(f"duplicate unique-source SHA={digest}")
                break
            unique_manifest_sha.add(digest)
            relative = clean(row.get("ml_source_relative_path"))
            artifact = output_root / relative
            if not artifact.is_file() or sha256_file(artifact) != digest:
                artifact_failures += 1
            else:
                try:
                    artifact_text = artifact.read_text(encoding="utf-8")
                    # Whether a source is decorated can be inferred safely from
                    # its first non-empty top-level line for read-only verify.
                    first_nonempty = next((line.lstrip(" \t") for line in artifact_text.splitlines() if line.strip()), "")
                    validate_standalone_header_alignment(artifact_text, first_nonempty.startswith("@"))
                except Exception:
                    artifact_failures += 1
    if unique_manifest_sha != source_sha:
        failures.append(
            f"unique-source set mismatch occurrence={len(source_sha)} unique_manifest={len(unique_manifest_sha)}"
        )
    if unique_rows != int(summary.get("unique_ml_source_sha", -1)):
        failures.append("unique source row count mismatch with summary")
    if artifact_failures:
        failures.append(f"artifact_integrity_failures={artifact_failures}")

    if failures:
        print("A05 output verification: FAIL", file=sys.stderr)
        for item in failures[:20]:
            print(f"[ERROR] {item}", file=sys.stderr)
        if len(failures) > 20:
            print(f"[ERROR] ... {len(failures) - 20} additional verification errors", file=sys.stderr)
        return 1

    print("A05 output verification: PASS")
    print(f"Status:                       {summary['status']}")
    print(f"Mapped C_FUN occurrences:     {row_count}")
    print(f"Unique C_FUN body SHA:         {len(body_sha)}")
    print(f"Unique standalone ML sources: {len(source_sha)}")
    print(f"Files with C_FUN:              {len(file_keys)}")
    print("Mapping failures:             0")
    return 0


def run_self_test() -> int:
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

    print("prepare_ml_cfun_inputs-v2 self-test: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["smoke", "full", "verify"], default="smoke")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--a01-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a01")
    parser.add_argument("--npr-a05-root", type=Path, required=False)
    parser.add_argument("--a13-summary-file", type=Path, required=False)
    parser.add_argument("--output-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a05-smoke")
    parser.add_argument("--tree-sitter-lib", type=Path, default=repo_root / "src/code-analyzer-tree-sitter/build/my-languages.so")
    parser.add_argument("--ast-helper-dir", type=Path, default=repo_root / "src/code-analyzer-tree-sitter")
    parser.add_argument("--expected-occurrences", type=int, default=EXPECTED_CFUN_OCCURRENCES)
    parser.add_argument("--expected-unique-body-sha", type=int, default=EXPECTED_UNIQUE_CFUN_BODY_SHA)
    parser.add_argument("--expected-files-with-cfun", type=int, default=EXPECTED_FILES_WITH_CFUN)
    parser.add_argument("--expected-a05-manifest-sha256", default=EXPECTED_A05_MANIFEST_SHA256)
    parser.add_argument("--max-occurrences", type=int, default=1000)
    parser.add_argument("--max-open-git-processes", type=int, default=4)
    parser.add_argument("--progress-every", type=int, default=10_000)
    parser.add_argument("--clone-path-prefix-from", default="")
    parser.add_argument("--clone-path-prefix-to", default="")
    parser.add_argument("--strict-expected-counts", action="store_true")
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
    if args.max_occurrences < 0:
        parser.error("--max-occurrences cannot be negative")
    if args.npr_a05_root is None:
        parser.error("--npr-a05-root is required")
    if args.a13_summary_file is None:
        parser.error("--a13-summary-file is required")
    if args.mode == "full" and args.max_occurrences != 0:
        parser.error("--mode full requires --max-occurrences 0")
    if args.mode == "verify":
        return verify_output(args)
    for path, label in [(args.tree_sitter_lib, "tree-sitter library"), (args.ast_helper_dir, "AST helper directory")]:
        if not path.exists():
            parser.error(f"{label} not found: {path}")
    return prepare(args)


if __name__ == "__main__":
    raise SystemExit(main())
