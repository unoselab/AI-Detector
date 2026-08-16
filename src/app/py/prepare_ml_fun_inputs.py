#!/usr/bin/env python3
"""
run-x-a02-v3: diagnose and repair Tree-sitter full-function mapping failures.

This revision is a targeted follow-up to run-x-a02-v2. The v2 full run already
verified the frozen A05 file/body identity for the historical FUN universe and
successfully prepared 913,558 of 921,762 function occurrences. The remaining
8,204 rows failed only while mapping the independently verified A05 function
body occurrence to a full Tree-sitter ``function_definition`` in the original
source file.

v3 does not rescore the full corpus. It reads the exact v2 failure set, reconnects
those code-unit IDs to the frozen A05 manifest, and performs a stricter diagnostic
of Tree-sitter candidate structure. A failed v2 occurrence is safe to recover only
when all of the following hold:

1. The historical Git blob SHA-256 still matches the A05 file SHA-256.
2. The exact A05 body slice still matches the A05 body SHA-256 and literal-space
   token count.
3. There is exactly one same-name, module-level Tree-sitter function node whose
   byte span contains the A05 body-start anchor.
4. If that Tree-sitter node extends past the A05 body end, only its START boundary
   is reused. The END boundary is taken from the authoritative A05 body end,
   which was produced by the frozen Python-3.12 AST extractor.
5. The reconstructed standalone function source is accepted by the frozen ML
   detector's Tree-sitter pipeline as exactly one function block with the expected
   name, full-source coverage, and a non-empty AST sequence.

This keeps the equality contract unchanged:

    same repository -> same commit -> same Python file -> same A05 FUN occurrence

The Tree-sitter full-file parse is therefore a locator for the function header,
not the authority for the historical function's terminal boundary. A05 remains
that authority because the A05 body identity was produced from Python-3.12 AST
semantics and is independently cryptographically verified before recovery.

Modes
-----
diagnose
    Re-analyze only the v2 failure rows. Write detailed candidate diagnostics,
    safely recovered occurrence rows, residual failures, and a repair-readiness
    summary. The existing v2 output is not modified.

repair
    Require a completed diagnosis with repair_ready=true, back up the failed v2
    core manifests, merge the v2 successes with the safely recovered rows, copy
    recovered source artifacts into the canonical A02 artifact store, rebuild the
    unique ML-source manifest, and write authoritative v3 PASS metadata/QC.

verify
    Read-only verification of the repaired canonical A02 output.

No CodeT5+ model is loaded, no SVM inference is run, and no SonarQube/DiD outcome
is accessed in any mode.
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


SCRIPT_VERSION = "run-x-a02-v3"
RUN_NAME = "run-x-a02"
EXPECTED_FUN_OCCURRENCES = 921_762
EXPECTED_UNIQUE_FUN_BODY_SHA = 105_635
EXPECTED_V2_FAILURES = 8_204
PRIMARY_UNIT_TYPE = "function_body"
PRIMARY_AGGREGATION_ROLE = "primary"
FULL_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

BASE_OCCURRENCE_COLUMNS = [
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

V3_EXTRA_OCCURRENCE_COLUMNS = [
    "tree_sitter_occurrence_mapping",
    "ml_source_end_strategy",
    "tree_sitter_same_name_candidate_count",
    "tree_sitter_anchor_candidate_count",
    "tree_sitter_primary_anchor_candidate_count",
    "tree_sitter_strict_candidate_count",
    "tree_sitter_candidate_start_byte_utf8",
    "tree_sitter_candidate_end_byte_utf8",
    "tree_sitter_candidate_end_minus_a05_body_end_bytes",
]

OCCURRENCE_COLUMNS = BASE_OCCURRENCE_COLUMNS[:-2] + V3_EXTRA_OCCURRENCE_COLUMNS + BASE_OCCURRENCE_COLUMNS[-2:]

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

DIAGNOSTIC_COLUMNS = [
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "snapshot_commit",
    "relative_path",
    "code_unit_id",
    "qualified_name",
    "function_name",
    "npr_body_sha256",
    "a05_body_start_byte",
    "a05_body_end_byte",
    "full_file_tree_has_error",
    "all_function_candidate_count",
    "same_name_candidate_count",
    "anchor_candidate_count",
    "same_name_anchor_candidate_count",
    "primary_same_name_anchor_candidate_count",
    "strict_same_name_anchor_candidate_count",
    "chosen_candidate_start_byte",
    "chosen_candidate_end_byte",
    "chosen_candidate_end_minus_a05_body_end_bytes",
    "chosen_candidate_primary_module_level",
    "chosen_candidate_includes_decorators",
    "mapping_strategy",
    "ml_source_end_strategy",
    "standalone_tree_has_error",
    "standalone_error_nodes",
    "standalone_missing_nodes",
    "standalone_blocks_found",
    "standalone_block_name",
    "standalone_block_covers_full_source",
    "recovery_status",
    "recovery_error_stage",
    "recovery_error_type",
    "recovery_error_message",
]

CHECK_COLUMNS = ["check_name", "severity", "passed", "observed", "expected", "note"]


class MappingError(RuntimeError):
    """Attach a stable pipeline stage to a mapping failure."""

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
class ResolvedFunction:
    node: Any
    strategy: str
    source_end_strategy: str
    source_end_byte: int
    analysis: CandidateAnalysis


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


def normalize_function_source(raw_source: str, strip_block_markers: Any) -> str:
    text = strip_block_markers(raw_source)
    text = textwrap.dedent(text).strip()
    if not text:
        raise MappingError("ml_source_normalize", "standalone function source is empty")
    return text + "\n"


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
    return utf8_source[int(name_node.start_byte): int(name_node.end_byte)].decode("utf-8", errors="strict")


def full_definition_node(function_node: Any) -> tuple[Any, bool]:
    parent = getattr(function_node, "parent", None)
    if parent is not None and clean(getattr(parent, "type", "")) == "decorated_definition":
        return parent, True
    return function_node, False


def is_primary_module_function(function_node: Any) -> bool:
    """Return whether a Tree-sitter function is a direct module definition.

    A05 primary ``function_body`` excludes nested functions, methods, and named
    definitions inside compound statements. For a decorated module function the
    function's parent is ``decorated_definition`` and that parent's parent is the
    module. For an undecorated module function the direct parent is the module.
    """

    parent = getattr(function_node, "parent", None)
    if parent is None:
        return False
    if clean(getattr(parent, "type", "")) == "decorated_definition":
        parent = getattr(parent, "parent", None)
    return parent is not None and clean(getattr(parent, "type", "")) == "module"


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
            if is_primary_module_function(node):
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


def resolve_function_node(
    root: Any,
    utf8_source: bytes,
    body_start_byte: int,
    body_end_byte: int,
    expected_name: str,
) -> ResolvedFunction:
    analysis = analyze_candidates(root, utf8_source, body_start_byte, body_end_byte, expected_name)

    # Keep the exact v2 rule when it succeeds. This ensures v3 does not alter
    # successful historical mappings merely because a recovery path exists.
    if analysis.strict_same_name_anchor:
        node = choose_smallest_unique(analysis.strict_same_name_anchor, "strict same-name anchor")
        if not is_primary_module_function(node):
            raise MappingError(
                "tree_sitter_occurrence_map",
                "strict Tree-sitter candidate is not a direct module-level function for an A05 primary FUN row",
            )
        full_node, _ = full_definition_node(node)
        return ResolvedFunction(
            node=node,
            strategy="strict_v2_body_start_anchor_with_end_guard",
            source_end_strategy="tree_sitter_full_definition_end",
            source_end_byte=int(full_node.end_byte),
            analysis=analysis,
        )

    # Safe repair path: A05 already proves the function-body identity. We only
    # accept a single same-name module-level Tree-sitter candidate containing
    # the A05 body-start anchor. If its recovery span runs beyond the A05 end,
    # use the Tree-sitter header START but the authoritative A05 function END.
    if len(analysis.primary_same_name_anchor) == 1:
        node = analysis.primary_same_name_anchor[0]
        return ResolvedFunction(
            node=node,
            strategy="unique_primary_body_start_anchor_a05_end_override",
            source_end_strategy="a05_verified_function_body_end",
            source_end_byte=body_end_byte,
            analysis=analysis,
        )

    raise MappingError(
        "tree_sitter_occurrence_map",
        "unsafe Tree-sitter mapping after v2 failure: "
        f"all_functions={len(analysis.all_functions)}; "
        f"same_name={len(analysis.same_name)}; "
        f"anchor={len(analysis.anchor_functions)}; "
        f"same_name_anchor={len(analysis.same_name_anchor)}; "
        f"primary_same_name_anchor={len(analysis.primary_same_name_anchor)}; "
        f"strict_same_name_anchor={len(analysis.strict_same_name_anchor)}",
    )


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
            raise MappingError("artifact_integrity", f"existing artifact hash mismatch: {destination}")
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v or "") for k, v in row.items()} for row in csv.DictReader(handle)]


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"[ERROR] expected JSON object: {path}")
    return payload


def add_check(rows: list[dict[str, Any]], name: str, severity: str, passed: bool, observed: Any, expected: Any, note: str = "") -> None:
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


def diagnostic_base(row: dict[str, str]) -> dict[str, Any]:
    return {
        "snapshot_id": clean(row.get("snapshot_id")),
        "dataset_source": clean(row.get("dataset_source")),
        "repo_name": clean(row.get("repo_name")),
        "snapshot_commit": clean(row.get("snapshot_commit")),
        "relative_path": clean(row.get("relative_path")),
        "code_unit_id": clean(row.get("code_unit_id")),
        "qualified_name": clean(row.get("qualified_name")),
        "function_name": leaf_function_name(clean(row.get("qualified_name"))),
        "npr_body_sha256": clean(row.get("code_unit_sha256")),
    }


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


def best_effort_candidate_diagnostic(
    row: dict[str, str],
    payload: bytes,
    detector: DetectorParser,
) -> dict[str, Any]:
    """Return candidate counts even when safe recovery later fails.

    This helper intentionally performs only read-only parsing and boundary
    accounting. It never writes artifacts and never changes the repair decision.
    It exists so residual failures retain enough evidence to distinguish missing,
    ambiguous, non-primary, and end-overrun Tree-sitter candidate families.
    """

    diagnostic = diagnostic_base(row)
    try:
        decoded_source, _ = decode_python_source(payload)
        utf8_source = decoded_source.encode("utf-8")
        body_start = as_int(row.get("start_char_offset"), "start_char_offset")
        body_end = as_int(row.get("end_char_offset"), "end_char_offset")
        if not (0 <= body_start < body_end <= len(decoded_source)):
            return diagnostic
        body_start_byte = char_offset_to_utf8_byte(decoded_source, body_start)
        body_end_byte = char_offset_to_utf8_byte(decoded_source, body_end)
        expected_name = leaf_function_name(clean(row.get("qualified_name")))
        if not expected_name:
            return diagnostic
        full_tree = detector.parser.parse(utf8_source)
        analysis = analyze_candidates(
            full_tree.root_node,
            utf8_source,
            body_start_byte,
            body_end_byte,
            expected_name,
        )
        diagnostic.update(
            {
                "a05_body_start_byte": body_start_byte,
                "a05_body_end_byte": body_end_byte,
                "full_file_tree_has_error": int(tree_has_error(full_tree.root_node)),
                "all_function_candidate_count": len(analysis.all_functions),
                "same_name_candidate_count": len(analysis.same_name),
                "anchor_candidate_count": len(analysis.anchor_functions),
                "same_name_anchor_candidate_count": len(analysis.same_name_anchor),
                "primary_same_name_anchor_candidate_count": len(analysis.primary_same_name_anchor),
                "strict_same_name_anchor_candidate_count": len(analysis.strict_same_name_anchor),
            }
        )
        if len(analysis.primary_same_name_anchor) == 1:
            node = analysis.primary_same_name_anchor[0]
            full_node, includes_decorators = full_definition_node(node)
            diagnostic.update(
                {
                    "chosen_candidate_start_byte": int(node.start_byte),
                    "chosen_candidate_end_byte": int(node.end_byte),
                    "chosen_candidate_end_minus_a05_body_end_bytes": int(node.end_byte) - body_end_byte,
                    "chosen_candidate_primary_module_level": 1,
                    "chosen_candidate_includes_decorators": int(includes_decorators),
                }
            )
            del full_node
    except Exception:
        # The original failure remains authoritative. Diagnostic enrichment must
        # never mask it or turn an unsafe mapping into a successful one.
        pass
    return diagnostic


def map_failed_occurrence(
    row: dict[str, str],
    payload: bytes,
    git_blob_oid: str,
    detector: DetectorParser,
    artifact_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    relative_path = validate_relative_python_path(clean(row.get("relative_path")))
    expected_file_sha = clean(row.get("file_sha256")).lower()
    if not FULL_SHA256_RE.fullmatch(expected_file_sha):
        raise MappingError("manifest_schema", f"invalid file_sha256: {expected_file_sha!r}")
    actual_file_sha = sha256_bytes(payload)
    if actual_file_sha != expected_file_sha:
        raise MappingError("file_identity", f"historical Git blob SHA mismatch: A05={expected_file_sha} actual={actual_file_sha}")

    decoded_source, _ = decode_python_source(payload)
    utf8_source = decoded_source.encode("utf-8")
    body_start = as_int(row.get("start_char_offset"), "start_char_offset")
    body_end = as_int(row.get("end_char_offset"), "end_char_offset")
    if not (0 <= body_start < body_end <= len(decoded_source)):
        raise MappingError("body_boundary", f"invalid A05 body range [{body_start}, {body_end})")
    body_text = decoded_source[body_start:body_end]
    expected_body_sha = clean(row.get("code_unit_sha256")).lower()
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
        raise MappingError("manifest_schema", "cannot derive function name from qualified_name")

    full_tree = detector.parser.parse(utf8_source)
    analysis = analyze_candidates(full_tree.root_node, utf8_source, body_start_byte, body_end_byte, expected_name)
    diagnostic = diagnostic_base(row)
    diagnostic.update(
        {
            "a05_body_start_byte": body_start_byte,
            "a05_body_end_byte": body_end_byte,
            "full_file_tree_has_error": int(tree_has_error(full_tree.root_node)),
            "all_function_candidate_count": len(analysis.all_functions),
            "same_name_candidate_count": len(analysis.same_name),
            "anchor_candidate_count": len(analysis.anchor_functions),
            "same_name_anchor_candidate_count": len(analysis.same_name_anchor),
            "primary_same_name_anchor_candidate_count": len(analysis.primary_same_name_anchor),
            "strict_same_name_anchor_candidate_count": len(analysis.strict_same_name_anchor),
        }
    )

    resolved = resolve_function_node(full_tree.root_node, utf8_source, body_start_byte, body_end_byte, expected_name)
    function_node = resolved.node
    full_node, includes_decorators = full_definition_node(function_node)
    source_start = int(full_node.start_byte)
    source_end = int(resolved.source_end_byte)
    if not (0 <= source_start < source_end <= len(utf8_source)):
        raise MappingError(
            "ml_source_boundary",
            f"invalid reconstructed function bytes [{source_start}, {source_end}) for source length {len(utf8_source)}",
        )

    raw_full_source = utf8_source[source_start:source_end].decode("utf-8", errors="strict")
    normalized_source = normalize_function_source(raw_full_source, detector.strip_block_markers)
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
    candidate_start = int(function_node.start_byte)
    candidate_end = int(function_node.end_byte)
    warning_parts: list[str] = []
    if tree_has_error(full_tree.root_node):
        warning_parts.append("full_file_tree_sitter_recovery")
    if tree_has_error(standalone_tree.root_node) or error_nodes or missing_nodes:
        warning_parts.append("standalone_tree_sitter_recovery")
    if resolved.source_end_strategy == "a05_verified_function_body_end":
        warning_parts.append("tree_sitter_full_file_end_overridden_by_a05")

    mapped = {
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
        "tree_sitter_function_name": node_name(function_node, utf8_source),
        "tree_sitter_function_name_matches": 1,
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

    diagnostic.update(
        {
            "chosen_candidate_start_byte": candidate_start,
            "chosen_candidate_end_byte": candidate_end,
            "chosen_candidate_end_minus_a05_body_end_bytes": candidate_end - body_end_byte,
            "chosen_candidate_primary_module_level": int(is_primary_module_function(function_node)),
            "chosen_candidate_includes_decorators": int(includes_decorators),
            "mapping_strategy": resolved.strategy,
            "ml_source_end_strategy": resolved.source_end_strategy,
            "standalone_tree_has_error": int(tree_has_error(standalone_tree.root_node)),
            "standalone_error_nodes": error_nodes,
            "standalone_missing_nodes": missing_nodes,
            "standalone_blocks_found": len(blocks),
            "standalone_block_name": block_name,
            "standalone_block_covers_full_source": covers,
            "recovery_status": "PASS",
            "recovery_error_stage": "",
            "recovery_error_type": "",
            "recovery_error_message": "",
        }
    )
    return mapped, diagnostic


def scan_a05_failure_rows(code_manifest_path: Path, failed_ids: set[str]) -> tuple[list[dict[str, str]], set[str], set[str]]:
    selected: list[dict[str, str]] = []
    found: set[str] = set()
    body_sha: set[str] = set()
    with code_manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        required = {
            "snapshot_order", "snapshot_id", "dataset_source", "repo_name", "repo_key",
            "snapshot_time", "snapshot_commit", "relative_path", "file_sha256", "code_unit_id",
            "code_unit_type", "aggregation_role", "qualified_name", "function_kind", "occurrence_index",
            "start_line", "end_line", "start_char_offset", "end_char_offset", "code_unit_sha256",
            "code_unit_relative_path", "character_count", "utf8_byte_count", "physical_line_count",
            "space_by_token_count",
        }
        missing = required - fields
        if missing:
            raise SystemExit(f"[ERROR] A05 code-unit manifest missing columns: {sorted(missing)}")
        for row in reader:
            code_unit_id = clean(row.get("code_unit_id"))
            if code_unit_id not in failed_ids:
                continue
            if clean(row.get("aggregation_role")) != PRIMARY_AGGREGATION_ROLE or clean(row.get("code_unit_type")) != PRIMARY_UNIT_TYPE:
                raise SystemExit(f"[ERROR] v2 failed code_unit_id is not A05 primary FUN: {code_unit_id}")
            if code_unit_id in found:
                raise SystemExit(f"[ERROR] duplicate failed code_unit_id in A05 manifest: {code_unit_id}")
            found.add(code_unit_id)
            body_sha.add(clean(row.get("code_unit_sha256")).lower())
            selected.append(dict(row))
    selected.sort(key=lambda row: (as_int(row.get("snapshot_order"), "snapshot_order"), clean(row.get("relative_path")), clean(row.get("code_unit_id"))))
    return selected, found, body_sha


def run_diagnosis(args: argparse.Namespace) -> int:
    started = time.time()
    repo_root = args.repo_root.resolve()
    a01_root = args.a01_root.resolve()
    a05_root = args.a05_root.resolve()
    base_root = args.base_output_root.resolve()
    output_root = args.diagnostic_output_root.resolve()

    validate_a01_freeze(a01_root)
    base_summary_path = base_root / "summary.json"
    base_occurrence_path = base_root / "python_ml_fun_occurrence_manifest.csv"
    base_failure_path = base_root / "python_ml_fun_mapping_failures.csv"
    for path in [base_summary_path, base_occurrence_path, base_failure_path, a05_root / "snapshot_status.csv", a05_root / "python_code_unit_manifest.csv"]:
        if not path.is_file():
            raise SystemExit(f"[ERROR] required input not found: {path}")

    base_summary = load_json(base_summary_path)
    base_failures = read_csv(base_failure_path)
    failed_ids = {clean(row.get("code_unit_id")) for row in base_failures}
    if "" in failed_ids:
        raise SystemExit("[ERROR] base failure CSV contains blank code_unit_id")
    if len(failed_ids) != len(base_failures):
        raise SystemExit("[ERROR] base failure CSV contains duplicate code_unit_id values")

    if args.expected_v2_failures > 0 and len(base_failures) != args.expected_v2_failures:
        raise SystemExit(f"[ERROR] v2 failure count mismatch: observed={len(base_failures)} expected={args.expected_v2_failures}")
    base_occurrence_count = sum(1 for _ in open(base_occurrence_path, "r", encoding="utf-8")) - 1
    if base_occurrence_count + len(base_failures) != args.expected_occurrences:
        raise SystemExit(
            f"[ERROR] v2 accounting mismatch: mapped={base_occurrence_count} failures={len(base_failures)} expected={args.expected_occurrences}"
        )

    selected_rows, found_ids, failed_body_sha = scan_a05_failure_rows(a05_root / "python_code_unit_manifest.csv", failed_ids)
    missing_ids = failed_ids - found_ids
    if missing_ids:
        raise SystemExit(f"[ERROR] {len(missing_ids)} v2 failed code_unit_ids were not found in A05 manifest")

    statuses = load_snapshot_status(
        a05_root / "snapshot_status.csv",
        args.clone_path_prefix_from,
        args.clone_path_prefix_to,
    )
    detector = load_detector_parser(repo_root, args.tree_sitter_lib.resolve(), args.ast_helper_dir.resolve())

    if output_root.exists() and args.overwrite:
        shutil.rmtree(output_root)
    if output_root.exists() and not args.overwrite:
        raise SystemExit(f"[ERROR] diagnostic output already exists: {output_root}; use --overwrite")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "ml_function_sources").mkdir(parents=True, exist_ok=True)

    mapped_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    residual_failures: list[dict[str, Any]] = []
    failure_stage_counts: Counter[str] = Counter()
    strategy_counts: Counter[str] = Counter()
    full_file_error_recovered = 0
    git_pool = GitBatchLRU(max_open=args.max_open_git_processes)

    current_snapshot = ""
    current_path = ""
    current_payload: bytes | None = None
    current_oid = ""
    processed = 0

    try:
        for row in selected_rows:
            snapshot_id = clean(row.get("snapshot_id"))
            relative_path = validate_relative_python_path(clean(row.get("relative_path")))
            status = statuses.get(snapshot_id)
            if status is None:
                raise SystemExit(f"[ERROR] snapshot_id not found in A05 status: {snapshot_id}")
            if status.status != "success":
                raise SystemExit(f"[ERROR] A05 snapshot status is not success: {snapshot_id} status={status.status}")
            if clean(row.get("repo_name")) != status.repo_name or clean(row.get("snapshot_commit")).lower() != status.commit_sha:
                raise SystemExit(f"[ERROR] A05 manifest/status identity mismatch for {snapshot_id}")
            if not status.clone_path_effective.is_dir():
                raise SystemExit(f"[ERROR] historical clone path not found: {status.clone_path_effective}")

            if snapshot_id != current_snapshot or relative_path != current_path:
                batch = git_pool.get(status.clone_path_effective)
                current_oid, current_payload = batch.read_blob(status.commit_sha, relative_path)
                current_snapshot = snapshot_id
                current_path = relative_path
            assert current_payload is not None

            diagnostic = diagnostic_base(row)
            try:
                mapped, diagnostic = map_failed_occurrence(row, current_payload, current_oid, detector, output_root)
                mapped_rows.append(mapped)
                diagnostic_rows.append(diagnostic)
                strategy_counts[clean(mapped.get("tree_sitter_occurrence_mapping"))] += 1
                if clean(mapped.get("mapping_warning")).find("full_file_tree_sitter_recovery") >= 0:
                    full_file_error_recovered += 1
            except Exception as exc:
                stage = exc.stage if isinstance(exc, MappingError) else "repair_occurrence_map"
                residual_failures.append(failure_row(row, stage, exc))
                failure_stage_counts[stage] += 1
                diagnostic = best_effort_candidate_diagnostic(row, current_payload, detector)
                diagnostic.update(
                    {
                        "recovery_status": "FAIL",
                        "recovery_error_stage": stage,
                        "recovery_error_type": type(exc).__name__,
                        "recovery_error_message": str(exc),
                    }
                )
                diagnostic_rows.append(diagnostic)

            processed += 1
            if args.progress_every > 0 and processed % args.progress_every == 0:
                print(
                    f"[diagnose] {processed}/{len(selected_rows)} recovered={len(mapped_rows)} "
                    f"residual_failures={len(residual_failures)}",
                    flush=True,
                )
    finally:
        git_pool.close()

    atomic_write_csv(output_root / "repair_occurrences.csv", mapped_rows, OCCURRENCE_COLUMNS)
    atomic_write_csv(output_root / "repair_failures.csv", residual_failures, FAILURE_COLUMNS)
    atomic_write_csv(output_root / "tree_sitter_mapping_diagnostics.csv", diagnostic_rows, DIAGNOSTIC_COLUMNS)

    unique_repaired_sources = len({clean(row.get("ml_source_sha256")) for row in mapped_rows if clean(row.get("ml_source_sha256"))})
    recovered_with_override = strategy_counts["unique_primary_body_start_anchor_a05_end_override"]
    repair_ready = len(mapped_rows) == len(selected_rows) and not residual_failures

    full_file_error_targets = sum(as_int(row.get("full_file_tree_has_error") or 0, "full_file_tree_has_error") for row in diagnostic_rows)
    no_same_name_anchor = sum(as_int(row.get("same_name_anchor_candidate_count") or 0, "same_name_anchor_candidate_count") == 0 for row in diagnostic_rows)
    no_primary_anchor = sum(
        as_int(row.get("same_name_anchor_candidate_count") or 0, "same_name_anchor_candidate_count") > 0
        and as_int(row.get("primary_same_name_anchor_candidate_count") or 0, "primary_same_name_anchor_candidate_count") == 0
        for row in diagnostic_rows
    )
    ambiguous_primary_anchor = sum(as_int(row.get("primary_same_name_anchor_candidate_count") or 0, "primary_same_name_anchor_candidate_count") > 1 for row in diagnostic_rows)
    unique_primary_anchor = sum(as_int(row.get("primary_same_name_anchor_candidate_count") or 0, "primary_same_name_anchor_candidate_count") == 1 for row in diagnostic_rows)
    unique_primary_end_overrun = sum(
        as_int(row.get("primary_same_name_anchor_candidate_count") or 0, "primary_same_name_anchor_candidate_count") == 1
        and as_int(row.get("strict_same_name_anchor_candidate_count") or 0, "strict_same_name_anchor_candidate_count") == 0
        for row in diagnostic_rows
    )

    checks: list[dict[str, Any]] = []
    add_check(checks, "base_v2_status_is_fail", "hard", base_summary.get("status") == "FAIL", base_summary.get("status"), "FAIL")
    add_check(checks, "base_v2_failure_count", "hard", len(base_failures) == args.expected_v2_failures, len(base_failures), args.expected_v2_failures)
    add_check(checks, "base_v2_accounting", "hard", base_occurrence_count + len(base_failures) == args.expected_occurrences, base_occurrence_count + len(base_failures), args.expected_occurrences)
    add_check(checks, "failed_code_unit_ids_found_in_a05", "hard", len(found_ids) == len(failed_ids), len(found_ids), len(failed_ids))
    add_check(checks, "diagnostic_rows_complete", "hard", len(diagnostic_rows) == len(selected_rows), len(diagnostic_rows), len(selected_rows))
    add_check(checks, "repair_occurrence_rows", "info", len(mapped_rows) == len(selected_rows), len(mapped_rows), len(selected_rows), "This is a repair-readiness gate, not a diagnostic execution gate.")
    add_check(checks, "residual_repair_failures", "info", len(residual_failures) == 0, len(residual_failures), 0)

    hard_failures = [row for row in checks if row["severity"] == "hard" and int(row["passed"]) == 0]
    status = "PASS" if not hard_failures else "FAIL"
    summary = {
        "run": SCRIPT_VERSION,
        "mode": "diagnose",
        "status": status,
        "failed_hard_checks": len(hard_failures),
        "base_v2_mapped_occurrences": base_occurrence_count,
        "base_v2_mapping_failures": len(base_failures),
        "target_failed_occurrences": len(selected_rows),
        "target_unique_npr_body_sha": len(failed_body_sha),
        "safely_recovered_occurrences": len(mapped_rows),
        "residual_repair_failures": len(residual_failures),
        "repair_ready": bool(repair_ready),
        "unique_repaired_ml_source_sha": unique_repaired_sources,
        "recovered_with_a05_end_override": recovered_with_override,
        "recovered_with_full_file_tree_errors": full_file_error_recovered,
        "target_full_file_tree_error_occurrences": full_file_error_targets,
        "target_no_same_name_anchor_occurrences": no_same_name_anchor,
        "target_same_name_anchor_but_no_primary_occurrences": no_primary_anchor,
        "target_ambiguous_primary_anchor_occurrences": ambiguous_primary_anchor,
        "target_unique_primary_anchor_occurrences": unique_primary_anchor,
        "target_unique_primary_anchor_end_overrun_occurrences": unique_primary_end_overrun,
        "mapping_strategy_counts": dict(sorted(strategy_counts.items())),
        "residual_failure_stage_counts": dict(sorted(failure_stage_counts.items())),
        "elapsed_seconds": round(time.time() - started, 3),
        "created_at_utc": utc_now(),
    }
    metadata = {
        "run": SCRIPT_VERSION,
        "mode": "diagnose",
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "python": sys.version,
        "inputs": {
            "a01_root": str(a01_root),
            "a05_root": str(a05_root),
            "a05_code_unit_manifest_sha256": sha256_file(a05_root / "python_code_unit_manifest.csv"),
            "a05_snapshot_status_sha256": sha256_file(a05_root / "snapshot_status.csv"),
            "base_v2_output_root": str(base_root),
            "base_v2_summary_sha256": sha256_file(base_summary_path),
            "base_v2_occurrence_manifest_sha256": sha256_file(base_occurrence_path),
            "base_v2_failure_manifest_sha256": sha256_file(base_failure_path),
            "tree_sitter_lib_sha256": sha256_file(args.tree_sitter_lib.resolve()),
        },
        "repair_policy": {
            "identity_authority": "A05 exact file/body SHA plus literal-space-token count",
            "tree_sitter_locator": "exactly_one_same_name_primary_module_function_containing_A05_body_start",
            "failed_v2_end_policy": "use_tree_sitter_header_start_and_A05_verified_function_end",
            "standalone_acceptance": "exactly_one_expected_function_block_full_source_coverage_nonempty_AST",
            "outcome_access": False,
            "model_loading": False,
            "svm_inference": False,
        },
        "created_at_utc": utc_now(),
    }
    atomic_write_csv(output_root / "checks.csv", checks, CHECK_COLUMNS)
    atomic_write_json(output_root / "summary.json", summary)
    atomic_write_json(output_root / "metadata.json", metadata)

    print("=" * 80)
    print("run-x-a02-v3 Tree-sitter failure diagnosis")
    print(f"Status:                              {status}")
    print(f"Target v2 mapping failures:          {len(selected_rows)}")
    print(f"Safely recovered occurrences:       {len(mapped_rows)}")
    print(f"Residual repair failures:            {len(residual_failures)}")
    print(f"Repair ready:                        {repair_ready}")
    print(f"Recovered with A05 end override:     {recovered_with_override}")
    print(f"Recovered with full-file TS errors:  {full_file_error_recovered}")
    print(f"Target full-file TS errors:          {full_file_error_targets}")
    print(f"Unique primary anchor targets:       {unique_primary_anchor}")
    print(f"Unique primary end-overrun targets:  {unique_primary_end_overrun}")
    print(f"No same-name anchor targets:         {no_same_name_anchor}")
    print(f"Ambiguous primary anchor targets:    {ambiguous_primary_anchor}")
    print(f"Unique repaired ML source SHA:       {unique_repaired_sources}")
    print(f"Failed hard checks:                  {len(hard_failures)}")
    print(f"Elapsed seconds:                     {time.time() - started:.3f}")
    print(f"Diagnostic output root:              {output_root}")
    print("=" * 80)
    return 0 if not hard_failures else 5


def normalize_base_occurrence_row(row: dict[str, str]) -> dict[str, Any]:
    result = {column: row.get(column, "") for column in OCCURRENCE_COLUMNS}
    if not clean(result.get("tree_sitter_occurrence_mapping")):
        result["tree_sitter_occurrence_mapping"] = "v2_strict_body_start_anchor_with_end_guard"
    if not clean(result.get("ml_source_end_strategy")):
        result["ml_source_end_strategy"] = "tree_sitter_full_definition_end"
    return result


def copy_or_link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != sha256_file(source):
            raise SystemExit(f"[ERROR] destination artifact conflicts with source: {destination}")
        return
    try:
        os.link(source, destination)
    except OSError:
        temp = destination.with_name(destination.name + f".tmp.{os.getpid()}")
        shutil.copy2(source, temp)
        os.replace(temp, destination)


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
    atomic_write_csv(output_path, [summaries[key] for key in sorted(summaries)], UNIQUE_SOURCE_COLUMNS)
    return len(summaries)


def verify_artifacts(occurrence_path: Path, output_root: Path) -> tuple[int, int]:
    checked: set[str] = set()
    failures = 0
    with occurrence_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            source_sha = clean(row.get("ml_source_sha256"))
            if not source_sha or source_sha in checked:
                continue
            checked.add(source_sha)
            path = output_root / clean(row.get("ml_source_relative_path"))
            if not path.is_file() or sha256_file(path) != source_sha:
                failures += 1
    return len(checked), failures


def backup_v2_core(base_root: Path) -> Path:
    backup_root = base_root / "provenance" / "run-x-a02-v2-failed"
    backup_root.mkdir(parents=True, exist_ok=True)
    names = [
        "summary.json",
        "metadata.json",
        "checks.csv",
        "python_ml_fun_occurrence_manifest.csv",
        "python_ml_fun_unique_source_manifest.csv",
        "python_ml_fun_mapping_failures.csv",
    ]
    manifest: dict[str, Any] = {"created_at_utc": utc_now(), "files": {}}
    for name in names:
        source = base_root / name
        if not source.is_file():
            raise SystemExit(f"[ERROR] cannot back up missing v2 file: {source}")
        destination = backup_root / name
        source_sha = sha256_file(source)
        if destination.exists():
            if sha256_file(destination) != source_sha:
                raise SystemExit(f"[ERROR] existing v2 backup conflicts: {destination}")
        else:
            shutil.copy2(source, destination)
        manifest["files"][name] = {"sha256": source_sha, "bytes": source.stat().st_size}
    atomic_write_json(backup_root / "backup_manifest.json", manifest)
    return backup_root


def run_repair(args: argparse.Namespace) -> int:
    started = time.time()
    base_root = args.base_output_root.resolve()
    diag_root = args.diagnostic_output_root.resolve()
    summary_path = diag_root / "summary.json"
    repair_occurrences_path = diag_root / "repair_occurrences.csv"
    repair_failures_path = diag_root / "repair_failures.csv"
    diagnostics_path = diag_root / "tree_sitter_mapping_diagnostics.csv"
    for path in [summary_path, repair_occurrences_path, repair_failures_path, diagnostics_path]:
        if not path.is_file():
            raise SystemExit(f"[ERROR] repair requires completed diagnosis output: {path}")
    diagnosis = load_json(summary_path)
    if diagnosis.get("status") != "PASS" or not bool(diagnosis.get("repair_ready")):
        raise SystemExit(f"[ERROR] diagnosis is not repair-ready: status={diagnosis.get('status')} repair_ready={diagnosis.get('repair_ready')}")

    repair_rows = read_csv(repair_occurrences_path)
    residual = read_csv(repair_failures_path)
    if residual:
        raise SystemExit(f"[ERROR] diagnosis contains {len(residual)} residual failures")
    if len(repair_rows) != args.expected_v2_failures:
        raise SystemExit(f"[ERROR] repair occurrence count mismatch: {len(repair_rows)} != {args.expected_v2_failures}")

    base_occurrence_path = base_root / "python_ml_fun_occurrence_manifest.csv"
    base_failure_path = base_root / "python_ml_fun_mapping_failures.csv"
    if not base_occurrence_path.is_file() or not base_failure_path.is_file():
        raise SystemExit("[ERROR] canonical v2 occurrence/failure manifests are missing")
    base_failures = read_csv(base_failure_path)
    if len(base_failures) != args.expected_v2_failures:
        raise SystemExit(f"[ERROR] canonical base failure count changed since diagnosis: {len(base_failures)}")
    failed_ids = {clean(row.get("code_unit_id")) for row in base_failures}
    repair_ids = {clean(row.get("code_unit_id")) for row in repair_rows}
    if failed_ids != repair_ids:
        raise SystemExit("[ERROR] repair code_unit_id set does not exactly equal the canonical v2 failure set")

    backup_root = backup_v2_core(base_root)

    # Materialize only newly repaired artifacts. Existing v2 artifacts remain in
    # the canonical store and are verified later from the merged occurrence file.
    for row in repair_rows:
        relative = clean(row.get("ml_source_relative_path"))
        source = diag_root / relative
        destination = base_root / relative
        if not source.is_file():
            raise SystemExit(f"[ERROR] repaired source artifact missing from diagnosis root: {source}")
        copy_or_link(source, destination)

    merged_temp = base_root / f"python_ml_fun_occurrence_manifest.csv.tmp.v3.{os.getpid()}"
    seen_ids: set[str] = set()
    unique_body_sha: set[str] = set()
    mapped_count = 0
    warning_occurrences = 0
    strategy_counts: Counter[str] = Counter()
    with merged_temp.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=OCCURRENCE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        with base_occurrence_path.open("r", encoding="utf-8", newline="") as inp:
            for row in csv.DictReader(inp):
                normalized = normalize_base_occurrence_row(row)
                code_unit_id = clean(normalized.get("code_unit_id"))
                if code_unit_id in seen_ids:
                    raise SystemExit(f"[ERROR] duplicate code_unit_id in base v2 successes: {code_unit_id}")
                seen_ids.add(code_unit_id)
                unique_body_sha.add(clean(normalized.get("npr_body_sha256")))
                if clean(normalized.get("mapping_warning")):
                    warning_occurrences += 1
                strategy_counts[clean(normalized.get("tree_sitter_occurrence_mapping"))] += 1
                writer.writerow({column: normalized.get(column, "") for column in OCCURRENCE_COLUMNS})
                mapped_count += 1
        for row in repair_rows:
            code_unit_id = clean(row.get("code_unit_id"))
            if code_unit_id in seen_ids:
                raise SystemExit(f"[ERROR] repaired code_unit_id already exists among v2 successes: {code_unit_id}")
            seen_ids.add(code_unit_id)
            unique_body_sha.add(clean(row.get("npr_body_sha256")))
            if clean(row.get("mapping_warning")):
                warning_occurrences += 1
            strategy_counts[clean(row.get("tree_sitter_occurrence_mapping"))] += 1
            writer.writerow({column: row.get(column, "") for column in OCCURRENCE_COLUMNS})
            mapped_count += 1

    if mapped_count != args.expected_occurrences:
        merged_temp.unlink(missing_ok=True)
        raise SystemExit(f"[ERROR] merged occurrence count mismatch: {mapped_count} != {args.expected_occurrences}")
    if len(seen_ids) != mapped_count:
        merged_temp.unlink(missing_ok=True)
        raise SystemExit("[ERROR] merged code_unit_id uniqueness failed")
    if len(unique_body_sha) != args.expected_unique_body_sha:
        merged_temp.unlink(missing_ok=True)
        raise SystemExit(f"[ERROR] merged unique NPR body SHA mismatch: {len(unique_body_sha)} != {args.expected_unique_body_sha}")

    # Replace the canonical occurrence manifest only after all merge invariants pass.
    os.replace(merged_temp, base_occurrence_path)
    atomic_write_csv(base_failure_path, [], FAILURE_COLUMNS)
    unique_source_count = build_unique_source_manifest(base_occurrence_path, base_root / "python_ml_fun_unique_source_manifest.csv")
    artifact_count, artifact_failures = verify_artifacts(base_occurrence_path, base_root)

    # Preserve the targeted diagnostic evidence beside the final authoritative output.
    shutil.copy2(diagnostics_path, base_root / "tree_sitter_mapping_diagnostics-v3.csv")

    checks: list[dict[str, Any]] = []
    add_check(checks, "full_fun_occurrence_count", "hard", mapped_count == args.expected_occurrences, mapped_count, args.expected_occurrences)
    add_check(checks, "code_unit_ids_unique", "hard", len(seen_ids) == mapped_count, len(seen_ids), mapped_count)
    add_check(checks, "unique_npr_body_sha", "hard", len(unique_body_sha) == args.expected_unique_body_sha, len(unique_body_sha), args.expected_unique_body_sha)
    add_check(checks, "mapping_failures_zero", "hard", len(read_csv(base_failure_path)) == 0, len(read_csv(base_failure_path)), 0)
    add_check(checks, "artifact_integrity_failures", "hard", artifact_failures == 0, artifact_failures, 0)
    add_check(checks, "diagnosis_repair_ready", "hard", bool(diagnosis.get("repair_ready")), diagnosis.get("repair_ready"), True)
    add_check(checks, "tree_sitter_recovery_warnings", "warning", warning_occurrences == 0, warning_occurrences, 0, "Warnings preserve occurrence identity and are retained for robustness auditing.")
    hard_failures = [row for row in checks if row["severity"] == "hard" and int(row["passed"]) == 0]
    warning_failures = [row for row in checks if row["severity"] == "warning" and int(row["passed"]) == 0]
    status = "FAIL" if hard_failures else ("PASS_WITH_WARNINGS" if warning_failures else "PASS")

    summary = {
        "run": SCRIPT_VERSION,
        "mode": "repair",
        "status": status,
        "failed_hard_checks": len(hard_failures),
        "failed_warning_checks": len(warning_failures),
        "selected_occurrences": mapped_count,
        "mapped_occurrences": mapped_count,
        "mapping_failures": 0,
        "unique_npr_body_sha": len(unique_body_sha),
        "unique_ml_source_sha": unique_source_count,
        "artifact_files_verified": artifact_count,
        "artifact_integrity_failures": artifact_failures,
        "warning_occurrences": warning_occurrences,
        "v2_success_occurrences_reused": mapped_count - len(repair_rows),
        "v3_repaired_occurrences": len(repair_rows),
        "mapping_strategy_counts": dict(sorted(strategy_counts.items())),
        "v2_failed_backup_root": str(backup_root),
        "elapsed_seconds": round(time.time() - started, 3),
        "created_at_utc": utc_now(),
    }
    metadata = {
        "run": SCRIPT_VERSION,
        "mode": "repair",
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "python": sys.version,
        "authoritative_output_root": str(base_root),
        "provenance": {
            "v2_failed_backup_root": str(backup_root),
            "diagnostic_root": str(diag_root),
            "diagnostic_summary_sha256": sha256_file(summary_path),
            "diagnostic_mapping_csv_sha256": sha256_file(diagnostics_path),
        },
        "equality_contract": [
            "same_repository",
            "same_historical_commit",
            "same_python_file",
            "same_A05_primary_function_body_occurrence",
        ],
        "mapping_policy": {
            "v2_successes": "unchanged",
            "v3_failed_recovery": "unique_same_name_primary_module_function_containing_A05_body_start",
            "v3_recovered_source_start": "Tree-sitter function/decorated-definition start",
            "v3_recovered_source_end": "A05 verified function body end",
            "standalone_acceptance": "frozen detector Tree-sitter exact one block, expected name, full coverage, nonempty AST",
        },
        "downstream_file_weight": "A05 function_body literal-space-token count",
        "prespecified_file_selection_rule": "file_ml_agc_share_space_by_token_weighted > 0.5",
        "model_loading": False,
        "svm_inference": False,
        "sonarqube_or_did_outcome_access": False,
        "created_at_utc": utc_now(),
    }
    atomic_write_csv(base_root / "checks.csv", checks, CHECK_COLUMNS)
    atomic_write_json(base_root / "summary.json", summary)
    atomic_write_json(base_root / "metadata.json", metadata)

    print("=" * 80)
    print("run-x-a02-v3 canonical repair")
    print(f"Status:                              {status}")
    print(f"V2 success occurrences reused:      {mapped_count - len(repair_rows)}")
    print(f"V3 repaired occurrences:            {len(repair_rows)}")
    print(f"Final mapped occurrences:           {mapped_count}")
    print(f"Final mapping failures:             0")
    print(f"Unique NPR body SHA:                {len(unique_body_sha)}")
    print(f"Unique ML standalone source SHA:    {unique_source_count}")
    print(f"Warning occurrences:                {warning_occurrences}")
    print(f"Artifact integrity failures:        {artifact_failures}")
    print(f"Failed hard checks:                 {len(hard_failures)}")
    print(f"V2 failed backup:                   {backup_root}")
    print(f"Canonical output root:              {base_root}")
    print("=" * 80)
    return 0 if not hard_failures else 5


def verify_repaired_output(base_root: Path, expected_occurrences: int, expected_unique_body_sha: int) -> int:
    required = [
        base_root / "summary.json",
        base_root / "metadata.json",
        base_root / "checks.csv",
        base_root / "python_ml_fun_occurrence_manifest.csv",
        base_root / "python_ml_fun_unique_source_manifest.csv",
        base_root / "python_ml_fun_mapping_failures.csv",
        base_root / "tree_sitter_mapping_diagnostics-v3.csv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        print(f"A02 v3 output verification: FAIL; missing={missing}", file=sys.stderr)
        return 1
    summary = load_json(base_root / "summary.json")
    failures: list[str] = []
    if summary.get("run") != SCRIPT_VERSION:
        failures.append(f"run={summary.get('run')!r}")
    if summary.get("status") not in {"PASS", "PASS_WITH_WARNINGS"}:
        failures.append(f"status={summary.get('status')!r}")
    if int(summary.get("failed_hard_checks", -1)) != 0:
        failures.append("failed_hard_checks != 0")
    if int(summary.get("mapped_occurrences", -1)) != expected_occurrences:
        failures.append("mapped_occurrences mismatch")
    if int(summary.get("mapping_failures", -1)) != 0:
        failures.append("mapping_failures != 0")
    if int(summary.get("unique_npr_body_sha", -1)) != expected_unique_body_sha:
        failures.append("unique_npr_body_sha mismatch")
    occurrence_path = base_root / "python_ml_fun_occurrence_manifest.csv"
    row_count = 0
    ids: set[str] = set()
    body_sha: set[str] = set()
    repaired = 0
    with occurrence_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if not set(OCCURRENCE_COLUMNS).issubset(fields):
            failures.append("occurrence manifest missing v3 columns")
        for row in reader:
            row_count += 1
            ids.add(clean(row.get("code_unit_id")))
            body_sha.add(clean(row.get("npr_body_sha256")))
            repaired += clean(row.get("tree_sitter_occurrence_mapping")) == "unique_primary_body_start_anchor_a05_end_override"
    if row_count != expected_occurrences or len(ids) != row_count:
        failures.append(f"row/id count mismatch rows={row_count} ids={len(ids)}")
    if len(body_sha) != expected_unique_body_sha:
        failures.append(f"body SHA count={len(body_sha)}")
    if read_csv(base_root / "python_ml_fun_mapping_failures.csv"):
        failures.append("failure manifest is not empty")
    _, artifact_failures = verify_artifacts(occurrence_path, base_root)
    if artifact_failures:
        failures.append(f"artifact_integrity_failures={artifact_failures}")
    if failures:
        print("A02 v3 output verification: FAIL", file=sys.stderr)
        for item in failures:
            print(f"[ERROR] {item}", file=sys.stderr)
        return 1
    print("A02 v3 output verification: PASS")
    print(f"Status:                    {summary['status']}")
    print(f"Mapped occurrences:        {row_count}")
    print(f"Unique NPR body SHA:       {len(body_sha)}")
    print(f"Unique ML source SHA:      {summary['unique_ml_source_sha']}")
    print(f"V3 end-override mappings:  {repaired}")
    print(f"Warning occurrences:       {summary['warning_occurrences']}")
    print(f"Mapping failures:          {summary['mapping_failures']}")
    print(f"Failed hard checks:        {summary['failed_hard_checks']}")
    return 0


def run_self_test() -> int:
    class FakeNode:
        def __init__(self, node_type: str, start: int, end: int, name: str = "", children: list[Any] | None = None) -> None:
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

    class FakeNameNode:
        def __init__(self, name: str, start: int) -> None:
            self.start_byte = start
            self.end_byte = start + len(name)
            self.type = "identifier"
            self.children: list[Any] = []
            self.parent = None
            self._name = name

    source = b"def f():\n    x = 1\n\ndef g():\n    return 2\n"
    f_end = source.find(b"\n\ndef g")
    f = FakeNode("function_definition", 0, f_end, "f")
    g_start = source.find(b"def g")
    g = FakeNode("function_definition", g_start, len(source.rstrip(b"\n")), "g")
    root = FakeNode("module", 0, len(source), children=[f, g])
    body_start = source.find(b"    x = 1")
    strict = resolve_function_node(root, source, body_start, f_end + 1, "f")
    if strict.strategy != "strict_v2_body_start_anchor_with_end_guard":
        raise SystemExit("[ERROR] self-test strict mapping failed")

    # Simulate the production failure family: a Tree-sitter recovery node extends
    # beyond the independently verified A05 function end. The unique module-level
    # name+anchor candidate must be recoverable using the A05 end boundary.
    f_recovery = FakeNode("function_definition", 0, len(source.rstrip(b"\n")), "f")
    root_recovery = FakeNode("module", 0, len(source), children=[f_recovery])
    recovered = resolve_function_node(root_recovery, source, body_start, f_end + 1, "f")
    if recovered.strategy != "unique_primary_body_start_anchor_a05_end_override":
        raise SystemExit("[ERROR] self-test A05 end-override mapping failed")
    if recovered.source_end_byte != f_end + 1:
        raise SystemExit("[ERROR] self-test A05 end boundary was not preserved")

    # Ambiguous same-name primary candidates must never be auto-repaired.
    f1 = FakeNode("function_definition", 0, len(source), "f")
    f2 = FakeNode("function_definition", 0, len(source), "f")
    ambiguous_root = FakeNode("module", 0, len(source), children=[f1, f2])
    try:
        resolve_function_node(ambiguous_root, source, body_start, f_end + 1, "f")
    except MappingError:
        pass
    else:
        raise SystemExit("[ERROR] self-test ambiguous recovery was not rejected")

    print("prepare_ml_fun_inputs-v3 self-test: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["diagnose", "repair", "verify"], default="diagnose")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--a01-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a01")
    parser.add_argument("--a05-root", type=Path)
    parser.add_argument("--base-output-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a02")
    parser.add_argument("--diagnostic-output-root", type=Path, default=repo_root / "src/app/data_did_agc_analysis/run-x-a02-v3-diagnose")
    parser.add_argument("--tree-sitter-lib", type=Path, default=repo_root / "src/code-analyzer-tree-sitter/build/my-languages.so")
    parser.add_argument("--ast-helper-dir", type=Path, default=repo_root / "src/code-analyzer-tree-sitter")
    parser.add_argument("--expected-occurrences", type=int, default=EXPECTED_FUN_OCCURRENCES)
    parser.add_argument("--expected-unique-body-sha", type=int, default=EXPECTED_UNIQUE_FUN_BODY_SHA)
    parser.add_argument("--expected-v2-failures", type=int, default=EXPECTED_V2_FAILURES)
    parser.add_argument("--max-open-git-processes", type=int, default=4)
    parser.add_argument("--progress-every", type=int, default=500)
    parser.add_argument("--clone-path-prefix-from", default="")
    parser.add_argument("--clone-path-prefix-to", default="")
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
    if args.mode in {"diagnose", "repair"} and args.a05_root is None:
        parser.error("--a05-root is required for diagnose/repair")
    if args.mode == "diagnose":
        for path, label in [(args.tree_sitter_lib, "tree-sitter library"), (args.ast_helper_dir, "AST helper directory")]:
            if not path.exists():
                parser.error(f"{label} not found: {path}")
        return run_diagnosis(args)
    if args.mode == "repair":
        return run_repair(args)
    return verify_repaired_output(args.base_output_root.resolve(), args.expected_occurrences, args.expected_unique_body_sha)


if __name__ == "__main__":
    raise SystemExit(main())
