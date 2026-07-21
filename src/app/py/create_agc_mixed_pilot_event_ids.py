#!/usr/bin/env python3
"""
Create a deterministic mixed AGC detector pilot event list.

The mixed pilot contains:

- all runtime-CPython-AST compatibility edge events;
- all tree-sitter recovery-node edge events;
- a deterministic sample of normal control events; and
- a deterministic sample of normal treatment events.

Normal events exclude both edge groups. Selection uses a stable SHA-256 rank
computed from a user-visible seed and function_event_id, so the same inputs and
seed always produce the same pilot.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


DEFAULT_SEED = "py312-mixed-pilot-v1"


@dataclass(frozen=True)
class ManifestEvent:
    manifest_row_number: int
    function_event_id: str
    dataset_source: str
    repo_name: str
    time: str
    commit: str
    relative_path: str
    qualified_function_name: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--runtime-ast-edge-csv", type=Path)
    parser.add_argument("--tree-sitter-edge-csv", type=Path)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-summary", type=Path)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--normal-control-events", type=int, default=50)
    parser.add_argument("--normal-treatment-events", type=int, default=50)
    parser.add_argument("--expected-manifest-rows", type=int, default=None)
    parser.add_argument("--expected-runtime-ast-edge-events", type=int, default=None)
    parser.add_argument("--expected-tree-sitter-edge-events", type=int, default=None)
    parser.add_argument("--expected-edge-overlap", type=int, default=0)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def require_file(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise SystemExit(f"[ERROR] required file not found: {resolved}")
    return resolved


def validate_positive(value: int, label: str) -> None:
    if value <= 0:
        raise SystemExit(f"[ERROR] {label} must be positive")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


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
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def read_event_ids(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if "function_event_id" not in fieldnames:
            raise SystemExit(
                f"[ERROR] edge CSV lacks function_event_id: {path}"
            )
        event_ids = [
            str(row.get("function_event_id", "")).strip()
            for row in reader
            if str(row.get("function_event_id", "")).strip()
        ]
    if not event_ids:
        raise SystemExit(f"[ERROR] edge CSV has no event ids: {path}")
    if len(event_ids) != len(set(event_ids)):
        raise SystemExit(f"[ERROR] duplicate event ids in edge CSV: {path}")
    return event_ids


def first_present(fieldnames: Iterable[str], candidates: Sequence[str]) -> str:
    available = set(fieldnames)
    for candidate in candidates:
        if candidate in available:
            return candidate
    return ""


def read_manifest(path: Path) -> Tuple[List[ManifestEvent], List[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        required = {"function_event_id", "dataset_source", "repo_name"}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise SystemExit(
                "[ERROR] manifest lacks required columns: " + ", ".join(missing)
            )

        time_field = first_present(fieldnames, ["time", "month"])
        commit_field = first_present(
            fieldnames, ["commit", "scan_current_commit"]
        )
        qualified_field = first_present(
            fieldnames, ["qualified_function_name", "qualified_name"]
        )
        if not time_field or not commit_field or not qualified_field:
            raise SystemExit(
                "[ERROR] manifest lacks time/month, commit, or qualified-name column"
            )
        if "relative_path" not in fieldnames:
            raise SystemExit("[ERROR] manifest lacks relative_path")

        events: List[ManifestEvent] = []
        seen_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            event_id = str(row.get("function_event_id", "")).strip()
            dataset_source = str(row.get("dataset_source", "")).strip().lower()
            if not event_id:
                raise SystemExit(
                    f"[ERROR] empty function_event_id at manifest row {row_number}"
                )
            if event_id in seen_ids:
                raise SystemExit(
                    f"[ERROR] duplicate function_event_id in manifest: {event_id}"
                )
            if dataset_source not in {"control", "treatment"}:
                raise SystemExit(
                    f"[ERROR] invalid dataset_source at row {row_number}: "
                    f"{dataset_source!r}"
                )
            seen_ids.add(event_id)
            events.append(
                ManifestEvent(
                    manifest_row_number=row_number,
                    function_event_id=event_id,
                    dataset_source=dataset_source,
                    repo_name=str(row.get("repo_name", "")).strip(),
                    time=str(row.get(time_field, "")).strip(),
                    commit=str(row.get(commit_field, "")).strip(),
                    relative_path=str(row.get("relative_path", "")).strip(),
                    qualified_function_name=str(
                        row.get(qualified_field, "")
                    ).strip(),
                )
            )
    if not events:
        raise SystemExit(f"[ERROR] manifest has no data rows: {path}")
    return events, fieldnames


def stable_rank_key(seed: str, event_id: str) -> str:
    payload = f"{seed}\0{event_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def select_normal_events(
    events: Sequence[ManifestEvent],
    excluded_ids: set[str],
    dataset_source: str,
    count: int,
    seed: str,
) -> List[Tuple[str, ManifestEvent]]:
    candidates = [
        event
        for event in events
        if event.dataset_source == dataset_source
        and event.function_event_id not in excluded_ids
    ]
    ranked = sorted(
        (
            stable_rank_key(seed, event.function_event_id),
            event,
        )
        for event in candidates
    )
    if len(ranked) < count:
        raise SystemExit(
            f"[ERROR] not enough normal {dataset_source} events: "
            f"requested={count} available={len(ranked)}"
        )
    return ranked[:count]


def event_to_output_row(
    event: ManifestEvent,
    selection_group: str,
    selection_rank: int,
    rank_key: str,
) -> Dict[str, Any]:
    return {
        "function_event_id": event.function_event_id,
        "selection_group": selection_group,
        "selection_rank": selection_rank,
        "deterministic_rank_key": rank_key,
        "manifest_row_number": event.manifest_row_number,
        "dataset_source": event.dataset_source,
        "repo_name": event.repo_name,
        "time": event.time,
        "commit": event.commit,
        "relative_path": event.relative_path,
        "qualified_function_name": event.qualified_function_name,
    }


def build_selection(
    events: Sequence[ManifestEvent],
    runtime_ids: Sequence[str],
    tree_sitter_ids: Sequence[str],
    normal_control_events: int,
    normal_treatment_events: int,
    seed: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    by_id = {event.function_event_id: event for event in events}
    runtime_set = set(runtime_ids)
    tree_sitter_set = set(tree_sitter_ids)
    overlap = runtime_set & tree_sitter_set
    edge_ids = runtime_set | tree_sitter_set

    missing_edges = sorted(edge_ids - set(by_id))
    if missing_edges:
        raise SystemExit(
            f"[ERROR] {len(missing_edges)} edge ids are absent from manifest; "
            f"first={missing_edges[:10]}"
        )

    rows: List[Dict[str, Any]] = []
    for rank, event_id in enumerate(sorted(runtime_set), start=1):
        rows.append(
            event_to_output_row(
                by_id[event_id],
                "runtime_ast_edge",
                rank,
                "",
            )
        )
    for rank, event_id in enumerate(sorted(tree_sitter_set), start=1):
        rows.append(
            event_to_output_row(
                by_id[event_id],
                "tree_sitter_edge",
                rank,
                "",
            )
        )

    normal_control = select_normal_events(
        events,
        edge_ids,
        "control",
        normal_control_events,
        seed,
    )
    normal_treatment = select_normal_events(
        events,
        edge_ids,
        "treatment",
        normal_treatment_events,
        seed,
    )

    for rank, (rank_key, event) in enumerate(normal_control, start=1):
        rows.append(
            event_to_output_row(
                event,
                "normal_control",
                rank,
                rank_key,
            )
        )
    for rank, (rank_key, event) in enumerate(normal_treatment, start=1):
        rows.append(
            event_to_output_row(
                event,
                "normal_treatment",
                rank,
                rank_key,
            )
        )

    selected_ids = [str(row["function_event_id"]) for row in rows]
    if len(selected_ids) != len(set(selected_ids)):
        raise SystemExit("[ERROR] duplicate event ids in final mixed pilot")

    group_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    for row in rows:
        group = str(row["selection_group"])
        source = str(row["dataset_source"])
        group_counts[group] = group_counts.get(group, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1

    summary = {
        "seed": seed,
        "manifest_rows": len(events),
        "runtime_ast_edge_events": len(runtime_set),
        "tree_sitter_edge_events": len(tree_sitter_set),
        "edge_overlap_events": len(overlap),
        "unique_edge_events": len(edge_ids),
        "normal_control_events": len(normal_control),
        "normal_treatment_events": len(normal_treatment),
        "selected_events": len(rows),
        "selection_group_counts": dict(sorted(group_counts.items())),
        "dataset_source_counts": dict(sorted(source_counts.items())),
        "duplicate_selected_event_ids": len(selected_ids) - len(set(selected_ids)),
    }
    return rows, summary


def run_self_test() -> None:
    events = [
        ManifestEvent(2, "r1", "control", "c/r", "2025-01", "a1", "a.py", "f"),
        ManifestEvent(3, "r2", "treatment", "t/r", "2025-01", "a2", "b.py", "g"),
        ManifestEvent(4, "t1", "control", "c/r", "2025-02", "a3", "c.py", "h"),
        ManifestEvent(5, "c1", "control", "c/r", "2025-03", "a4", "d.py", "i"),
        ManifestEvent(6, "c2", "control", "c/r", "2025-04", "a5", "e.py", "j"),
        ManifestEvent(7, "c3", "control", "c/r", "2025-05", "a6", "f.py", "k"),
        ManifestEvent(8, "x1", "treatment", "t/r", "2025-02", "a7", "g.py", "l"),
        ManifestEvent(9, "x2", "treatment", "t/r", "2025-03", "a8", "h.py", "m"),
        ManifestEvent(10, "x3", "treatment", "t/r", "2025-04", "a9", "i.py", "n"),
    ]
    rows, summary = build_selection(
        events=events,
        runtime_ids=["r1", "r2"],
        tree_sitter_ids=["t1"],
        normal_control_events=2,
        normal_treatment_events=2,
        seed="test-seed",
    )
    assert len(rows) == 7
    assert summary["unique_edge_events"] == 3
    assert summary["selected_events"] == 7
    assert summary["duplicate_selected_event_ids"] == 0
    assert summary["selection_group_counts"] == {
        "normal_control": 2,
        "normal_treatment": 2,
        "runtime_ast_edge": 2,
        "tree_sitter_edge": 1,
    }
    rows_again, summary_again = build_selection(
        events=events,
        runtime_ids=["r1", "r2"],
        tree_sitter_ids=["t1"],
        normal_control_events=2,
        normal_treatment_events=2,
        seed="test-seed",
    )
    assert rows == rows_again
    assert summary == summary_again
    print("Self-test: PASS")


def main() -> None:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return

    required_options = {
        "--manifest": args.manifest,
        "--runtime-ast-edge-csv": args.runtime_ast_edge_csv,
        "--tree-sitter-edge-csv": args.tree_sitter_edge_csv,
        "--output-csv": args.output_csv,
        "--output-summary": args.output_summary,
    }
    missing_options = [name for name, value in required_options.items() if value is None]
    if missing_options:
        raise SystemExit(
            "[ERROR] missing required options: " + ", ".join(missing_options)
        )

    validate_positive(args.normal_control_events, "--normal-control-events")
    validate_positive(args.normal_treatment_events, "--normal-treatment-events")
    if not str(args.seed).strip():
        raise SystemExit("[ERROR] --seed cannot be empty")

    manifest = require_file(args.manifest)
    runtime_csv = require_file(args.runtime_ast_edge_csv)
    tree_sitter_csv = require_file(args.tree_sitter_edge_csv)
    output_csv = args.output_csv.expanduser().resolve()
    output_summary = args.output_summary.expanduser().resolve()

    events, _ = read_manifest(manifest)
    runtime_ids = read_event_ids(runtime_csv)
    tree_sitter_ids = read_event_ids(tree_sitter_csv)

    if (
        args.expected_manifest_rows is not None
        and len(events) != args.expected_manifest_rows
    ):
        raise SystemExit(
            "[ERROR] manifest row count mismatch: "
            f"expected={args.expected_manifest_rows} actual={len(events)}"
        )
    if (
        args.expected_runtime_ast_edge_events is not None
        and len(runtime_ids) != args.expected_runtime_ast_edge_events
    ):
        raise SystemExit(
            "[ERROR] runtime AST edge count mismatch: "
            f"expected={args.expected_runtime_ast_edge_events} "
            f"actual={len(runtime_ids)}"
        )
    if (
        args.expected_tree_sitter_edge_events is not None
        and len(tree_sitter_ids) != args.expected_tree_sitter_edge_events
    ):
        raise SystemExit(
            "[ERROR] tree-sitter edge count mismatch: "
            f"expected={args.expected_tree_sitter_edge_events} "
            f"actual={len(tree_sitter_ids)}"
        )

    rows, summary = build_selection(
        events=events,
        runtime_ids=runtime_ids,
        tree_sitter_ids=tree_sitter_ids,
        normal_control_events=args.normal_control_events,
        normal_treatment_events=args.normal_treatment_events,
        seed=str(args.seed).strip(),
    )
    if summary["edge_overlap_events"] != args.expected_edge_overlap:
        raise SystemExit(
            "[ERROR] edge overlap mismatch: "
            f"expected={args.expected_edge_overlap} "
            f"actual={summary['edge_overlap_events']}"
        )

    summary.update(
        {
            "manifest": str(manifest),
            "manifest_sha256": sha256_file(manifest),
            "runtime_ast_edge_csv": str(runtime_csv),
            "runtime_ast_edge_csv_sha256": sha256_file(runtime_csv),
            "tree_sitter_edge_csv": str(tree_sitter_csv),
            "tree_sitter_edge_csv_sha256": sha256_file(tree_sitter_csv),
            "output_csv": str(output_csv),
            "output_summary": str(output_summary),
        }
    )

    fieldnames = [
        "function_event_id",
        "selection_group",
        "selection_rank",
        "deterministic_rank_key",
        "manifest_row_number",
        "dataset_source",
        "repo_name",
        "time",
        "commit",
        "relative_path",
        "qualified_function_name",
    ]
    atomic_write_csv(output_csv, rows, fieldnames)
    summary["output_csv_sha256"] = sha256_file(output_csv)
    atomic_write_json(output_summary, summary)

    print("=" * 76)
    print("Create AGC mixed pilot event IDs")
    print(f"Manifest rows:               {summary['manifest_rows']}")
    print(f"Runtime AST edge events:     {summary['runtime_ast_edge_events']}")
    print(f"Tree-sitter edge events:     {summary['tree_sitter_edge_events']}")
    print(f"Edge overlap events:         {summary['edge_overlap_events']}")
    print(f"Normal control events:       {summary['normal_control_events']}")
    print(f"Normal treatment events:     {summary['normal_treatment_events']}")
    print(f"Selected events:             {summary['selected_events']}")
    print(f"Output CSV:                  {output_csv}")
    print(f"Output summary:              {output_summary}")
    print("=" * 76)


if __name__ == "__main__":
    main()
