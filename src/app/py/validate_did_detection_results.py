#!/usr/bin/env python3
"""
Validate final treatment/control outputs produced by analyze_did_python_snapshots.py.

The validator checks final CSV/JSON artifacts without requiring the prediction
cache or commit-level checkpoint directories. Use --require-parts when the
original parts/<source>/.../_SUCCESS tree is available and must be audited.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(
    "../ai_code_complexity_study_python/python_snapshots_detect/"
    "codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict"
)
DEFAULT_EXPERIMENT = "codellama-7b_4500_complexity_stratified_maxlen2048"
DEFAULT_CLASSIFIER = "svm"
DEFAULT_REPRESENTATION = "ast"
DEFAULT_SCORE_MODE = "decision"
DEFAULT_MODEL_KEY = "codesearchnet_codellama-7b_python_merged_4500ast_"
DEFAULT_EXPECTED_COMMITS = {"treatment": 863, "control": 800}
ALLOWED_BLOCK_KINDS = {"function_definition", "class_definition"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate final treatment/control AGC detection outputs."
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--source",
        choices=["treatment", "control", "both"],
        default="both",
    )
    parser.add_argument(
        "--expected-treatment-commits",
        type=int,
        default=DEFAULT_EXPECTED_COMMITS["treatment"],
    )
    parser.add_argument(
        "--expected-control-commits",
        type=int,
        default=DEFAULT_EXPECTED_COMMITS["control"],
    )
    parser.add_argument("--expected-experiment", default=DEFAULT_EXPERIMENT)
    parser.add_argument("--expected-classifier", default=DEFAULT_CLASSIFIER)
    parser.add_argument(
        "--expected-representation",
        default=DEFAULT_REPRESENTATION,
    )
    parser.add_argument("--expected-score-mode", default=DEFAULT_SCORE_MODE)
    parser.add_argument("--expected-model-key", default=DEFAULT_MODEL_KEY)
    parser.add_argument(
        "--require-parts",
        action="store_true",
        help="Require one _SUCCESS marker per expected commit.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Default: <root>/qc/run1c",
    )
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"[ERROR] required file not found: {path}")


def load_json(path: Path) -> Dict[str, Any]:
    require_file(path)
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"[ERROR] expected JSON object: {path}")
    return value


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
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def parse_int(value: Any, label: str, errors: List[str]) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        errors.append(f"invalid integer for {label}: {value!r}")
        return 0


def parse_float(value: Any) -> Optional[float]:
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def close_enough(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def metadata_value(metadata: Dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in metadata:
            return metadata[name]
    return None


def selected_sources(source: str) -> List[str]:
    return ["treatment", "control"] if source == "both" else [source]


def expected_commits(args: argparse.Namespace, source: str) -> int:
    if source == "treatment":
        return args.expected_treatment_commits
    return args.expected_control_commits


def check_equal(actual: Any, expected: Any, label: str, errors: List[str]) -> None:
    if actual != expected:
        errors.append(f"{label}: actual={actual!r} expected={expected!r}")


def validate_snapshot_summary(
    path: Path,
    source: str,
    expected_commit_count: int,
    qc: Dict[str, Any],
    errors: List[str],
) -> Dict[str, Any]:
    require_file(path)
    keys = set()
    totals = Counter()
    row_count = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "dataset_source",
            "repo_name",
            "commit",
            "regular_files_expected",
            "files_analyzed",
            "blocks_scored",
            "human_blocks",
            "agc_blocks",
            "failure_count",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            errors.append(f"snapshot summary missing columns: {missing}")
            return {}

        for row in reader:
            row_count += 1
            check_equal(
                row["dataset_source"],
                source,
                f"snapshot row {row_count} dataset_source",
                errors,
            )
            key = (row["dataset_source"], row["repo_name"], row["commit"])
            if key in keys:
                errors.append(f"duplicate snapshot key: {key}")
            keys.add(key)
            for field in (
                "regular_files_expected",
                "files_analyzed",
                "blocks_scored",
                "human_blocks",
                "agc_blocks",
                "failure_count",
            ):
                totals[field] += parse_int(
                    row[field],
                    f"snapshot row {row_count} {field}",
                    errors,
                )

    check_equal(row_count, expected_commit_count, "snapshot CSV row count", errors)
    check_equal(len(keys), row_count, "unique snapshot key count", errors)
    for field in (
        "regular_files_expected",
        "files_analyzed",
        "blocks_scored",
        "human_blocks",
        "agc_blocks",
        "failure_count",
    ):
        check_equal(
            totals[field],
            parse_int(qc.get(field), f"QC {field}", errors),
            f"snapshot total vs QC {field}",
            errors,
        )

    return {"rows": row_count, **dict(totals)}


def validate_file_summary(
    path: Path,
    source: str,
    qc: Dict[str, Any],
    errors: List[str],
) -> Dict[str, Any]:
    require_file(path)
    row_count = 0
    files_analyzed = 0
    failure_count = 0
    blocks_scored = 0
    statuses = Counter()
    accepted_statuses = {
        "ok",
        "no_top_level_blocks",
        "skipped_symlink",
        "skipped_non_regular",
    }

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"dataset_source", "analysis_status", "blocks_scored"}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            errors.append(f"file summary missing columns: {missing}")
            return {}

        for row in reader:
            row_count += 1
            check_equal(
                row["dataset_source"],
                source,
                f"file row {row_count} dataset_source",
                errors,
            )
            status = row["analysis_status"]
            statuses[status] += 1
            blocks_scored += parse_int(
                row["blocks_scored"],
                f"file row {row_count} blocks_scored",
                errors,
            )
            if status in {"ok", "no_top_level_blocks"}:
                files_analyzed += 1
            if status not in accepted_statuses:
                failure_count += 1

    check_equal(
        files_analyzed,
        parse_int(qc.get("files_analyzed"), "QC files_analyzed", errors),
        "file summary analyzed count vs QC",
        errors,
    )
    check_equal(
        failure_count,
        parse_int(qc.get("failure_count"), "QC failure_count", errors),
        "file summary failure count vs QC",
        errors,
    )
    check_equal(
        blocks_scored,
        parse_int(qc.get("blocks_scored"), "QC blocks_scored", errors),
        "file summary block total vs QC",
        errors,
    )

    return {
        "rows": row_count,
        "files_analyzed": files_analyzed,
        "failure_count": failure_count,
        "blocks_scored": blocks_scored,
        "analysis_status_counts": dict(sorted(statuses.items())),
    }


def validate_block_predictions(
    path: Path,
    source: str,
    expected_score_mode: str,
    expected_model_key: str,
    qc: Dict[str, Any],
    errors: List[str],
) -> Dict[str, Any]:
    require_file(path)
    row_count = 0
    human_blocks = 0
    agc_blocks = 0
    invalid_predictions = 0
    score_modes = set()
    model_keys = set()
    block_kinds = Counter()
    agc_by_kind = Counter()

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "dataset_source",
            "block_kind",
            "predicted_agc",
            "score_mode",
            "model_key",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            errors.append(f"block predictions missing columns: {missing}")
            return {}

        for row in reader:
            row_count += 1
            check_equal(
                row["dataset_source"],
                source,
                f"block row {row_count} dataset_source",
                errors,
            )
            predicted_agc = row["predicted_agc"]
            if predicted_agc not in {"0", "1"}:
                invalid_predictions += 1
                continue

            kind = row["block_kind"]
            block_kinds[kind] += 1
            if kind not in ALLOWED_BLOCK_KINDS:
                errors.append(f"unexpected block_kind at row {row_count}: {kind!r}")

            if predicted_agc == "1":
                agc_blocks += 1
                agc_by_kind[kind] += 1
            else:
                human_blocks += 1
            score_modes.add(row["score_mode"])
            model_keys.add(row["model_key"])

    check_equal(
        row_count,
        parse_int(qc.get("blocks_scored"), "QC blocks_scored", errors),
        "block CSV row count vs QC",
        errors,
    )
    check_equal(
        human_blocks,
        parse_int(qc.get("human_blocks"), "QC human_blocks", errors),
        "block human count vs QC",
        errors,
    )
    check_equal(
        agc_blocks,
        parse_int(qc.get("agc_blocks"), "QC agc_blocks", errors),
        "block AGC count vs QC",
        errors,
    )
    check_equal(invalid_predictions, 0, "invalid predicted_agc rows", errors)
    check_equal(score_modes, {expected_score_mode}, "score modes", errors)
    check_equal(model_keys, {expected_model_key}, "model keys", errors)

    kind_summary: Dict[str, Dict[str, Any]] = {}
    for kind in sorted(block_kinds):
        total = block_kinds[kind]
        agc = agc_by_kind[kind]
        kind_summary[kind] = {
            "blocks": total,
            "agc_blocks": agc,
            "agc_block_ratio": agc / total if total else None,
        }

    return {
        "rows": row_count,
        "human_blocks": human_blocks,
        "agc_blocks": agc_blocks,
        "score_modes": sorted(score_modes),
        "model_keys": sorted(model_keys),
        "block_kind_summary": kind_summary,
    }


def validate_repo_month_panel(
    path: Path,
    source: str,
    qc: Dict[str, Any],
    errors: List[str],
) -> Dict[str, Any]:
    require_file(path)
    row_count = 0
    ok_rows = 0
    keys = set()
    invalid_ratios = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "dataset_source",
            "repo_name",
            "month",
            "analysis_status",
            "blocks_scored",
            "agc_blocks",
            "agc_block_ratio",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            errors.append(f"repo-month panel missing columns: {missing}")
            return {}

        for row in reader:
            row_count += 1
            check_equal(
                row["dataset_source"],
                source,
                f"repo-month row {row_count} dataset_source",
                errors,
            )
            key = (row["dataset_source"], row["repo_name"], row["month"])
            if key in keys:
                errors.append(f"duplicate repo-month key: {key}")
            keys.add(key)
            if row["analysis_status"] == "ok":
                ok_rows += 1

            blocks = parse_int(
                row["blocks_scored"],
                f"repo-month row {row_count} blocks_scored",
                errors,
            )
            agc = parse_int(
                row["agc_blocks"],
                f"repo-month row {row_count} agc_blocks",
                errors,
            )
            ratio = parse_float(row["agc_block_ratio"])
            if blocks > 0:
                expected_ratio = agc / blocks
                if ratio is None or not close_enough(ratio, expected_ratio):
                    invalid_ratios += 1
            elif ratio is not None:
                invalid_ratios += 1

    check_equal(
        row_count,
        parse_int(qc.get("repo_month_rows_total"), "QC repo_month_rows_total", errors),
        "repo-month row count vs QC",
        errors,
    )
    check_equal(
        ok_rows,
        parse_int(qc.get("repo_month_rows_matched"), "QC repo_month_rows_matched", errors),
        "repo-month matched count vs QC",
        errors,
    )
    check_equal(ok_rows, row_count, "non-ok repo-month rows", errors)
    check_equal(len(keys), row_count, "unique repo-month key count", errors)
    check_equal(invalid_ratios, 0, "invalid repo-month AGC ratios", errors)

    return {
        "rows": row_count,
        "matched_rows": ok_rows,
        "invalid_ratio_rows": invalid_ratios,
    }


def validate_run_metadata(
    path: Path,
    source: str,
    expected_commit_count: int,
    args: argparse.Namespace,
    errors: List[str],
) -> Dict[str, Any]:
    metadata = load_json(path)
    check_equal(metadata_value(metadata, "dataset_source"), source, "run metadata source", errors)
    check_equal(metadata_value(metadata, "selected_commits"), expected_commit_count, "run metadata selected_commits", errors)
    check_equal(metadata_value(metadata, "experiment"), args.expected_experiment, "run metadata experiment", errors)
    check_equal(metadata_value(metadata, "classifier"), args.expected_classifier, "run metadata classifier", errors)
    check_equal(metadata_value(metadata, "representation", "embedding"), args.expected_representation, "run metadata representation", errors)
    check_equal(metadata_value(metadata, "expected_score_mode", "score_mode"), args.expected_score_mode, "run metadata score mode", errors)
    check_equal(metadata_value(metadata, "model_key"), args.expected_model_key, "run metadata model key", errors)

    return {
        "experiment": metadata_value(metadata, "experiment"),
        "classifier": metadata_value(metadata, "classifier"),
        "representation": metadata_value(metadata, "representation", "embedding"),
        "model_sha256": metadata_value(metadata, "model_sha256"),
        "model_key": metadata_value(metadata, "model_key"),
        "embedding_model_id": metadata_value(metadata, "embedding_model_id"),
        "max_len": metadata_value(metadata, "max_len"),
        "threshold_effective": metadata_value(metadata, "threshold_effective", "threshold"),
        "score_mode": metadata_value(metadata, "expected_score_mode", "score_mode"),
    }


def validate_parts(
    root: Path,
    source: str,
    expected_commit_count: int,
    require_parts: bool,
    errors: List[str],
    warnings: List[str],
) -> Dict[str, Any]:
    parts_root = root / "parts" / source
    success_count = (
        sum(1 for _ in parts_root.glob("*/*/_SUCCESS"))
        if parts_root.is_dir()
        else 0
    )

    if require_parts:
        check_equal(success_count, expected_commit_count, f"{source} _SUCCESS count", errors)
    elif success_count == 0:
        warnings.append(
            f"{source}: checkpoint parts are absent; final artifacts were validated without checkpoint auditing"
        )
    elif success_count != expected_commit_count:
        warnings.append(
            f"{source}: partial checkpoint tree found ({success_count}/{expected_commit_count})"
        )

    return {
        "parts_directory_exists": parts_root.is_dir(),
        "success_markers": success_count,
        "required": require_parts,
    }


def validate_source(
    root: Path,
    source: str,
    expected_commit_count: int,
    args: argparse.Namespace,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []

    qc = load_json(root / f"qc_summary_{source}.json")
    check_equal(qc.get("dataset_source"), source, "QC dataset_source", errors)
    check_equal(qc.get("experiment"), args.expected_experiment, "QC experiment", errors)
    check_equal(qc.get("classifier"), args.expected_classifier, "QC classifier", errors)
    check_equal(qc.get("representation"), args.expected_representation, "QC representation", errors)
    check_equal(parse_int(qc.get("snapshot_rows"), "QC snapshot_rows", errors), expected_commit_count, "QC snapshot_rows", errors)
    check_equal(parse_int(qc.get("failure_count"), "QC failure_count", errors), 0, "QC failure_count", errors)
    check_equal(
        parse_int(qc.get("files_analyzed"), "QC files_analyzed", errors),
        parse_int(qc.get("regular_files_expected"), "QC regular_files_expected", errors),
        "QC files_analyzed vs regular_files_expected",
        errors,
    )
    check_equal(
        parse_int(qc.get("blocks_scored"), "QC blocks_scored", errors),
        parse_int(qc.get("human_blocks"), "QC human_blocks", errors)
        + parse_int(qc.get("agc_blocks"), "QC agc_blocks", errors),
        "QC block decomposition",
        errors,
    )
    check_equal(
        parse_int(qc.get("repo_month_rows_matched"), "QC repo_month_rows_matched", errors),
        parse_int(qc.get("repo_month_rows_total"), "QC repo_month_rows_total", errors),
        "QC repo-month match coverage",
        errors,
    )

    snapshot_summary = validate_snapshot_summary(
        root / f"snapshot_summary_{source}.csv",
        source,
        expected_commit_count,
        qc,
        errors,
    )
    file_summary = validate_file_summary(
        root / f"file_summary_{source}.csv",
        source,
        qc,
        errors,
    )
    block_summary = validate_block_predictions(
        root / f"block_predictions_{source}.csv",
        source,
        args.expected_score_mode,
        args.expected_model_key,
        qc,
        errors,
    )
    panel_summary = validate_repo_month_panel(
        root / f"repo_month_agc_panel_{source}.csv",
        source,
        qc,
        errors,
    )
    comparable_metadata = validate_run_metadata(
        root / f"run_metadata_{source}.json",
        source,
        expected_commit_count,
        args,
        errors,
    )
    parts_summary = validate_parts(
        root,
        source,
        expected_commit_count,
        args.require_parts,
        errors,
        warnings,
    )

    result = {
        "source": source,
        "status": "PASS" if not errors else "FAIL",
        "expected_commits": expected_commit_count,
        "qc_summary": qc,
        "snapshot_validation": snapshot_summary,
        "file_validation": file_summary,
        "block_validation": block_summary,
        "repo_month_validation": panel_summary,
        "parts_validation": parts_summary,
        "warnings": warnings,
        "errors": errors,
    }
    return result, comparable_metadata


def compare_source_metadata(metadata_by_source: Dict[str, Dict[str, Any]]) -> List[str]:
    if set(metadata_by_source) != {"treatment", "control"}:
        return []
    errors: List[str] = []
    treatment = metadata_by_source["treatment"]
    control = metadata_by_source["control"]
    for field in treatment:
        if treatment[field] != control.get(field):
            errors.append(
                f"treatment/control metadata mismatch for {field}: "
                f"treatment={treatment[field]!r} control={control.get(field)!r}"
            )
    return errors


def print_source_summary(result: Dict[str, Any]) -> None:
    qc = result["qc_summary"]
    block_kinds = result["block_validation"].get("block_kind_summary", {})
    print()
    print("=" * 72)
    print(f"Source: {result['source']}")
    print(f"Status: {result['status']}")
    print(f"Snapshots: {qc.get('snapshot_rows')}")
    print(f"Files analyzed: {qc.get('files_analyzed')}")
    print(f"Blocks scored: {qc.get('blocks_scored')}")
    print(f"Human blocks: {qc.get('human_blocks')}")
    print(f"AGC-like blocks: {qc.get('agc_blocks')}")
    print(f"Repo-month rows: {qc.get('repo_month_rows_total')}")
    print(
        "Checkpoint markers: "
        f"{result['parts_validation']['success_markers']} "
        f"(required={result['parts_validation']['required']})"
    )
    for kind, summary in block_kinds.items():
        ratio = summary["agc_block_ratio"]
        ratio_text = "NA" if ratio is None else f"{ratio:.6f}"
        print(
            f"{kind}: blocks={summary['blocks']} "
            f"agc={summary['agc_blocks']} ratio={ratio_text}"
        )
    for warning in result["warnings"]:
        print(f"WARNING: {warning}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    print("=" * 72)


def main() -> None:
    args = parse_args()
    args.root = args.root.expanduser().resolve()
    if not args.root.is_dir():
        raise SystemExit(f"[ERROR] root directory not found: {args.root}")
    args.output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir is not None
        else args.root / "qc" / "run1c"
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Dict[str, Any]] = {}
    metadata_by_source: Dict[str, Dict[str, Any]] = {}
    for source in selected_sources(args.source):
        result, comparable_metadata = validate_source(
            args.root,
            source,
            expected_commits(args, source),
            args,
        )
        results[source] = result
        metadata_by_source[source] = comparable_metadata
        atomic_write_json(
            args.output_dir / f"source_validation_{source}.json",
            result,
        )
        print_source_summary(result)

    metadata_errors = compare_source_metadata(metadata_by_source)
    combined_errors = [
        error for result in results.values() for error in result["errors"]
    ] + metadata_errors
    combined = {
        "root": str(args.root),
        "requested_source": args.source,
        "status": "PASS" if not combined_errors else "FAIL",
        "source_status": {
            source: result["status"] for source, result in results.items()
        },
        "metadata_comparison_errors": metadata_errors,
        "errors": combined_errors,
    }
    combined_path = args.output_dir / "combined_validation_summary.json"
    atomic_write_json(combined_path, combined)

    print()
    print("=" * 72)
    print(f"Combined status: {combined['status']}")
    print(f"Validation output: {args.output_dir}")
    print(f"Combined summary: {combined_path}")
    for error in metadata_errors:
        print(f"ERROR: {error}")
    print("=" * 72)

    if combined_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
