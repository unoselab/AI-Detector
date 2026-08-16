#!/usr/bin/env python3
"""
aggregate_ml_fun_files-v1.py
============================

Aggregate frozen run-x-a03 ML function predictions to historical Python files.

Scientific scope
----------------
A04 consumes the exact function-occurrence predictions produced by A03 and
aggregates them to the same historical snapshot/file universe preserved by A05.
It does not retrain the classifier, change the SVM function boundary, access
SonarQube outcomes, or estimate a DiD model.

Primary file-level rule
-----------------------
For every prepared Python file with at least one scored primary FUN occurrence:

    file_ml_agc_share_space_by_token_weighted
        = sum(body_space_tokens * I[predicted_agc]) / sum(body_space_tokens)

The primary AGC-like file indicator is frozen before quality outcomes:

    file_ml_agc_like_primary = 1 iff weighted AGC share > 0.50

Files with no primary FUN occurrence are not classified as HWC. They retain a
blank primary indicator and status ``no_ml_fun``. Files that were not prepared
by A05 also retain a blank primary indicator and status ``file_not_prepared``.

A04 also preserves count-based share and weighted continuous SVM scores for
robustness/descriptive use, but those quantities do not replace the frozen
primary weighted-share rule.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

SCRIPT_VERSION = "run-x-a04-v1"
EXPECTED_A03_RUN = "run-x-a03-v1"
EXPECTED_A03_STATUS = "PASS"
EXPECTED_OCCURRENCES = 921_762
EXPECTED_PYTHON_FILES = 494_592
EXPECTED_PREPARED_FILES = 494_332
EXPECTED_NOT_PREPARED_FILES = 260
EXPECTED_FILES_WITH_FUN = 196_644
EXPECTED_NO_FUN_FILES = 297_688
EXPECTED_AGC_OCCURRENCES = 290_926
EXPECTED_HWC_OCCURRENCES = 630_836
EXPECTED_TOTAL_SPACE_TOKENS = 152_001_674
EXPECTED_AGC_SPACE_TOKENS = 13_202_081
PRIMARY_THRESHOLD = 0.50
SUPPORT_THRESHOLDS = (0.00, 0.25, 0.50, 0.75)

A03_OCCURRENCE_REQUIRED = {
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "repo_key",
    "snapshot_time",
    "snapshot_commit",
    "relative_path",
    "file_sha256",
    "code_unit_id",
    "npr_body_space_by_token_count",
    "ml_source_sha256",
    "a02_mapping_warning",
    "predicted_agc",
    "human_decision_score",
    "ml_agc_score",
    "score_mode",
    "model_key",
}

A05_FILE_REQUIRED = {
    "snapshot_order",
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "repo_key",
    "snapshot_time",
    "snapshot_commit",
    "relative_path",
    "file_sha256",
    "physical_line_count",
    "parse_status",
}

FILE_OUTPUT_COLUMNS = [
    "snapshot_order",
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "repo_key",
    "snapshot_time",
    "snapshot_commit",
    "relative_path",
    "file_sha256",
    "python_lines",
    "parse_status",
    "ml_fun_occurrences_total",
    "ml_fun_agc_occurrences",
    "ml_fun_hwc_occurrences",
    "ml_fun_space_by_tokens_total",
    "ml_fun_agc_space_by_tokens",
    "ml_fun_hwc_space_by_tokens",
    "file_ml_agc_share_by_count",
    "file_ml_agc_share_space_by_token_weighted",
    "file_ml_human_decision_score_space_by_token_weighted",
    "file_ml_agc_score_space_by_token_weighted",
    "ml_fun_mapping_warning_occurrences",
    "ml_fun_mapping_warning_present",
    "file_ml_agc_like_primary",
    "file_ml_agc_primary_threshold",
    "file_ml_agc_primary_operator",
    "file_ml_agc_status",
]

SELECTED_OUTPUT_COLUMNS = [
    "snapshot_id",
    "dataset_source",
    "repo_name",
    "repo_key",
    "snapshot_time",
    "snapshot_commit",
    "relative_path",
    "file_sha256",
    "python_lines",
    "ml_fun_occurrences_total",
    "ml_fun_agc_occurrences",
    "ml_fun_space_by_tokens_total",
    "ml_fun_agc_space_by_tokens",
    "file_ml_agc_share_by_count",
    "file_ml_agc_share_space_by_token_weighted",
    "file_ml_human_decision_score_space_by_token_weighted",
    "file_ml_agc_score_space_by_token_weighted",
    "ml_fun_mapping_warning_present",
    "file_ml_agc_like_primary",
]

SUPPORT_COLUMNS = [
    "dataset_source",
    "threshold",
    "operator",
    "python_file_rows",
    "prepared_file_rows",
    "files_with_fun",
    "selected_files",
    "selected_share_of_fun_files",
    "selected_share_of_python_files",
    "ties_at_threshold",
]

CHECK_COLUMNS = ["check", "severity", "passed", "observed", "expected", "detail"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def parse_int(value: Any, label: str) -> int:
    text = clean(value)
    if not text:
        raise ValueError(f"missing integer field {label}")
    result = int(text)
    if result < 0:
        raise ValueError(f"negative integer field {label}: {result}")
    return result


def parse_float(value: Any, label: str) -> float:
    result = float(clean(value))
    if not math.isfinite(result):
        raise ValueError(f"non-finite float field {label}: {value!r}")
    return result


def parse_boolish(value: Any) -> bool:
    text = clean(value).casefold()
    if text in {"1", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "false", "f", "no", "n", ""}:
        return False
    raise ValueError(f"unsupported boolean value: {value!r}")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
        tmp = Path(handle.name)
    os.replace(tmp, path)


def atomic_write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        tmp = Path(handle.name)
    os.replace(tmp, path)


def iter_csv(path: Path) -> Iterator[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"missing CSV header: {path}")
        for row in reader:
            yield row


def require_columns(path: Path, required: set[str], label: str) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
    if not header:
        raise ValueError(f"missing CSV header for {label}: {path}")
    missing = sorted(required - set(header))
    if missing:
        raise ValueError(f"{label} missing required columns {missing}: {path}")
    return header


def file_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        clean(row.get("snapshot_id")),
        clean(row.get("relative_path")),
        clean(row.get("file_sha256")).casefold(),
    )


def add_check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    observed: Any,
    expected: Any,
    detail: str,
    severity: str = "hard",
) -> None:
    checks.append(
        {
            "check": name,
            "severity": severity,
            "passed": 1 if passed else 0,
            "observed": observed,
            "expected": expected,
            "detail": detail,
        }
    )


@dataclass
class FileAccumulator:
    occurrences_total: int = 0
    agc_occurrences: int = 0
    hwc_occurrences: int = 0
    tokens_total: int = 0
    agc_tokens: int = 0
    hwc_tokens: int = 0
    weighted_human_score_sum: float = 0.0
    weighted_agc_score_sum: float = 0.0
    mapping_warning_occurrences: int = 0

    def add(
        self,
        *,
        predicted_agc: int,
        tokens: int,
        human_score: float,
        agc_score: float,
        mapping_warning: bool,
    ) -> None:
        self.occurrences_total += 1
        self.tokens_total += tokens
        self.weighted_human_score_sum += tokens * human_score
        self.weighted_agc_score_sum += tokens * agc_score
        if predicted_agc == 1:
            self.agc_occurrences += 1
            self.agc_tokens += tokens
        elif predicted_agc == 0:
            self.hwc_occurrences += 1
            self.hwc_tokens += tokens
        else:
            raise ValueError(f"predicted_agc must be 0/1, found {predicted_agc}")
        if mapping_warning:
            self.mapping_warning_occurrences += 1

    def metrics(self, parse_status: str, threshold: float) -> dict[str, Any]:
        prepared = clean(parse_status).casefold() == "prepared"
        if not prepared:
            status = "file_not_prepared"
        elif self.occurrences_total == 0:
            status = "no_ml_fun"
        else:
            status = "scored"

        if self.occurrences_total > 0:
            count_share = self.agc_occurrences / self.occurrences_total
        else:
            count_share = math.nan

        if self.tokens_total > 0:
            weighted_share = self.agc_tokens / self.tokens_total
            weighted_human = self.weighted_human_score_sum / self.tokens_total
            weighted_agc = self.weighted_agc_score_sum / self.tokens_total
        else:
            weighted_share = math.nan
            weighted_human = math.nan
            weighted_agc = math.nan

        def finite_or_blank(value: float) -> Any:
            return value if math.isfinite(value) else ""

        if status == "scored":
            selected: Any = 1 if weighted_share > threshold else 0
            threshold_value: Any = threshold
            operator: Any = ">"
        else:
            selected = ""
            threshold_value = ""
            operator = ""

        return {
            "ml_fun_occurrences_total": self.occurrences_total,
            "ml_fun_agc_occurrences": self.agc_occurrences,
            "ml_fun_hwc_occurrences": self.hwc_occurrences,
            "ml_fun_space_by_tokens_total": self.tokens_total,
            "ml_fun_agc_space_by_tokens": self.agc_tokens,
            "ml_fun_hwc_space_by_tokens": self.hwc_tokens,
            "file_ml_agc_share_by_count": finite_or_blank(count_share),
            "file_ml_agc_share_space_by_token_weighted": finite_or_blank(weighted_share),
            "file_ml_human_decision_score_space_by_token_weighted": finite_or_blank(weighted_human),
            "file_ml_agc_score_space_by_token_weighted": finite_or_blank(weighted_agc),
            "ml_fun_mapping_warning_occurrences": self.mapping_warning_occurrences,
            "ml_fun_mapping_warning_present": 1 if self.mapping_warning_occurrences > 0 else 0,
            "file_ml_agc_like_primary": selected,
            "file_ml_agc_primary_threshold": threshold_value,
            "file_ml_agc_primary_operator": operator,
            "file_ml_agc_status": status,
        }


def load_a03_contract(a03_root: Path, checks: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    summary_path = a03_root / "summary.json"
    metadata_path = a03_root / "metadata.json"
    failures_path = a03_root / "scoring_failures.csv"
    occurrence_path = a03_root / "ml_fun_occurrence_predictions.csv"

    for path in (summary_path, metadata_path, failures_path, occurrence_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    summary = read_json(summary_path)
    metadata = read_json(metadata_path)

    add_check(checks, "a03_run", clean(summary.get("run")) == EXPECTED_A03_RUN, summary.get("run"), EXPECTED_A03_RUN, "A04 must consume run-x-a03-v1 full output.")
    add_check(checks, "a03_mode", clean(summary.get("mode")) == "full", summary.get("mode"), "full", "A04 may not consume the smoke output.")
    add_check(checks, "a03_status", clean(summary.get("status")) == EXPECTED_A03_STATUS, summary.get("status"), EXPECTED_A03_STATUS, "A03 must have clean PASS status.")
    add_check(checks, "a03_failed_hard_checks", int(summary.get("failed_hard_checks", -1)) == 0, summary.get("failed_hard_checks"), 0, "A03 hard QC must be clean.")
    add_check(checks, "a03_scoring_failures", int(summary.get("scoring_failures", -1)) == 0, summary.get("scoring_failures"), 0, "A03 may not have source-scoring failures.")
    add_check(checks, "a03_join_missing", int(summary.get("occurrence_join_missing_predictions", -1)) == 0, summary.get("occurrence_join_missing_predictions"), 0, "A03 occurrence expansion must be complete.")

    failure_rows = sum(1 for _ in iter_csv(failures_path))
    add_check(checks, "a03_failure_file_empty", failure_rows == 0, failure_rows, 0, "A03 scoring_failures.csv must contain no data rows.")

    return summary, metadata


def load_file_manifest_info(
    file_manifest: Path,
    max_files: int,
    checks: list[dict[str, Any]],
) -> tuple[list[dict[str, str]] | None, set[tuple[str, str, str]] | None, dict[str, Any]]:
    require_columns(file_manifest, A05_FILE_REQUIRED, "A05 Python file manifest")
    selected_rows: list[dict[str, str]] | None = [] if max_files > 0 else None
    selected_keys: set[tuple[str, str, str]] | None = set() if max_files > 0 else None
    seen_keys: set[tuple[str, str, str]] = set()
    rows = 0
    prepared = 0
    not_prepared = 0
    duplicate_keys = 0

    for row in iter_csv(file_manifest):
        rows += 1
        key = file_key(row)
        if key in seen_keys:
            duplicate_keys += 1
        else:
            seen_keys.add(key)
        if clean(row.get("parse_status")).casefold() == "prepared":
            prepared += 1
        else:
            not_prepared += 1
        if max_files > 0 and len(selected_rows or []) < max_files:
            assert selected_rows is not None and selected_keys is not None
            selected_rows.append(row)
            selected_keys.add(key)

    add_check(checks, "a05_python_file_rows", rows == EXPECTED_PYTHON_FILES, rows, EXPECTED_PYTHON_FILES, "A04 must use the complete A05 Python file universe.")
    add_check(checks, "a05_prepared_files", prepared == EXPECTED_PREPARED_FILES, prepared, EXPECTED_PREPARED_FILES, "Prepared Python file count must match frozen A05 production.")
    add_check(checks, "a05_not_prepared_files", not_prepared == EXPECTED_NOT_PREPARED_FILES, not_prepared, EXPECTED_NOT_PREPARED_FILES, "Explicitly excluded/not-prepared file count must remain 260.")
    add_check(checks, "a05_file_duplicate_keys", duplicate_keys == 0, duplicate_keys, 0, "Snapshot/path/file-SHA keys must be unique in the A05 file manifest.")

    return selected_rows, selected_keys, {
        "rows": rows,
        "prepared": prepared,
        "not_prepared": not_prepared,
        "unique_keys": len(seen_keys),
    }


def stream_occurrences(
    occurrence_path: Path,
    selected_keys: set[tuple[str, str, str]] | None,
    checks: list[dict[str, Any]],
    expected_occurrences: int,
    expected_agc_occurrences: int,
    expected_hwc_occurrences: int,
    expected_total_tokens: int,
    expected_agc_tokens: int,
    progress_every: int,
) -> tuple[dict[tuple[str, str, str], FileAccumulator], dict[str, Any]]:
    require_columns(occurrence_path, A03_OCCURRENCE_REQUIRED, "A03 occurrence predictions")
    accumulators: dict[tuple[str, str, str], FileAccumulator] = {}
    code_unit_ids: set[str] = set()
    rows = 0
    duplicate_code_units = 0
    agc_occurrences = 0
    hwc_occurrences = 0
    total_tokens = 0
    agc_tokens = 0
    warning_occurrences = 0
    score_rule_errors = 0
    score_transform_errors = 0
    invalid_score_mode = 0

    for row in iter_csv(occurrence_path):
        rows += 1
        code_unit_id = clean(row.get("code_unit_id"))
        if code_unit_id in code_unit_ids:
            duplicate_code_units += 1
        else:
            code_unit_ids.add(code_unit_id)

        predicted_agc = parse_int(row.get("predicted_agc"), f"row {rows}.predicted_agc")
        if predicted_agc not in {0, 1}:
            raise ValueError(f"invalid predicted_agc at row {rows}: {predicted_agc}")
        tokens = parse_int(row.get("npr_body_space_by_token_count"), f"row {rows}.npr_body_space_by_token_count")
        human_score = parse_float(row.get("human_decision_score"), f"row {rows}.human_decision_score")
        ml_agc_score = parse_float(row.get("ml_agc_score"), f"row {rows}.ml_agc_score")
        if clean(row.get("score_mode")) != "decision":
            invalid_score_mode += 1
        expected_agc = 1 if human_score < 0.0 else 0
        if predicted_agc != expected_agc:
            score_rule_errors += 1
        if not math.isclose(ml_agc_score, -human_score, rel_tol=0.0, abs_tol=1e-12):
            score_transform_errors += 1

        warning = bool(clean(row.get("a02_mapping_warning")))
        if warning:
            warning_occurrences += 1
        total_tokens += tokens
        if predicted_agc:
            agc_occurrences += 1
            agc_tokens += tokens
        else:
            hwc_occurrences += 1

        key = file_key(row)
        if selected_keys is None or key in selected_keys:
            accumulator = accumulators.get(key)
            if accumulator is None:
                accumulator = FileAccumulator()
                accumulators[key] = accumulator
            accumulator.add(
                predicted_agc=predicted_agc,
                tokens=tokens,
                human_score=human_score,
                agc_score=ml_agc_score,
                mapping_warning=warning,
            )

        if progress_every > 0 and rows % progress_every == 0:
            print(f"[occurrence] {rows}/{expected_occurrences} rows scanned file_accumulators={len(accumulators)}")

    add_check(checks, "a03_occurrence_rows", rows == expected_occurrences, rows, expected_occurrences, "A04 must scan every A03 FUN occurrence prediction.")
    add_check(checks, "a03_occurrence_unique_code_units", len(code_unit_ids) == expected_occurrences, len(code_unit_ids), expected_occurrences, "Every A03 occurrence must have a unique code_unit_id.")
    add_check(checks, "a03_occurrence_duplicate_code_units", duplicate_code_units == 0, duplicate_code_units, 0, "A03 occurrence predictions must not duplicate function occurrence identity.")
    add_check(checks, "a03_agc_occurrence_count", agc_occurrences == expected_agc_occurrences, agc_occurrences, expected_agc_occurrences, "AGC occurrence count must reproduce A03 summary.")
    add_check(checks, "a03_hwc_occurrence_count", hwc_occurrences == expected_hwc_occurrences, hwc_occurrences, expected_hwc_occurrences, "HWC occurrence count must reproduce A03 summary.")
    add_check(checks, "a03_total_body_space_tokens", total_tokens == expected_total_tokens, total_tokens, expected_total_tokens, "Body-size denominator must reproduce A03 summary.")
    add_check(checks, "a03_agc_body_space_tokens", agc_tokens == expected_agc_tokens, agc_tokens, expected_agc_tokens, "AGC body-size numerator must reproduce A03 summary.")
    add_check(checks, "a03_score_rule_consistency", score_rule_errors == 0, score_rule_errors, 0, "predicted_agc must equal I[human_decision_score < 0].")
    add_check(checks, "a03_score_transform_consistency", score_transform_errors == 0, score_transform_errors, 0, "ml_agc_score must equal -human_decision_score.")
    add_check(checks, "a03_score_mode_decision", invalid_score_mode == 0, invalid_score_mode, 0, "All A03 rows must use decision score mode.")

    return accumulators, {
        "rows": rows,
        "unique_code_unit_ids": len(code_unit_ids),
        "agc_occurrences": agc_occurrences,
        "hwc_occurrences": hwc_occurrences,
        "body_space_tokens_total": total_tokens,
        "body_space_tokens_agc": agc_tokens,
        "mapping_warning_occurrences": warning_occurrences,
        "file_accumulators": len(accumulators),
    }


def support_bucket() -> dict[str, int]:
    return {
        "python_file_rows": 0,
        "prepared_file_rows": 0,
        "files_with_fun": 0,
        "selected_files": 0,
        "ties_at_threshold": 0,
    }


def write_file_outputs(
    file_manifest: Path,
    selected_rows: list[dict[str, str]] | None,
    accumulators: dict[tuple[str, str, str], FileAccumulator],
    output_root: Path,
    primary_threshold: float,
    support_thresholds: tuple[float, ...],
    max_files: int,
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    file_output_path = output_root / "python_ml_fun_file_scores.csv"
    selected_output_path = output_root / "python_ml_fun_selected_files_primary.csv"
    support_output_path = output_root / "python_ml_fun_threshold_support.csv"

    if selected_rows is not None:
        row_source: Iterable[dict[str, str]] = selected_rows
    else:
        row_source = iter_csv(file_manifest)

    support: dict[tuple[str, float], dict[str, int]] = defaultdict(support_bucket)
    status_counts: Counter[str] = Counter()
    output_rows = 0
    selected_primary = 0
    files_with_fun = 0
    no_fun_files = 0
    not_prepared_files = 0
    warning_files = 0
    not_prepared_with_fun = 0
    sum_file_occurrences = 0
    sum_file_agc_occurrences = 0
    sum_file_tokens = 0
    sum_file_agc_tokens = 0
    orphan_accumulators = set(accumulators)
    selected_rows_buffer: list[dict[str, Any]] = []

    file_output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=file_output_path.parent,
        prefix=f".{file_output_path.name}.", delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FILE_OUTPUT_COLUMNS)
        writer.writeheader()
        for row in row_source:
            output_rows += 1
            key = file_key(row)
            orphan_accumulators.discard(key)
            accumulator = accumulators.get(key, FileAccumulator())
            metrics = accumulator.metrics(clean(row.get("parse_status")), primary_threshold)
            status = clean(metrics["file_ml_agc_status"])
            status_counts[status] += 1
            if status == "scored":
                files_with_fun += 1
                if int(metrics["file_ml_agc_like_primary"]) == 1:
                    selected_primary += 1
            elif status == "no_ml_fun":
                no_fun_files += 1
            elif status == "file_not_prepared":
                not_prepared_files += 1
            if int(metrics["ml_fun_mapping_warning_present"]) == 1:
                warning_files += 1
            if status == "file_not_prepared" and accumulator.occurrences_total > 0:
                not_prepared_with_fun += 1
            sum_file_occurrences += accumulator.occurrences_total
            sum_file_agc_occurrences += accumulator.agc_occurrences
            sum_file_tokens += accumulator.tokens_total
            sum_file_agc_tokens += accumulator.agc_tokens

            output = {
                "snapshot_order": row.get("snapshot_order", ""),
                "snapshot_id": row.get("snapshot_id", ""),
                "dataset_source": row.get("dataset_source", ""),
                "repo_name": row.get("repo_name", ""),
                "repo_key": row.get("repo_key", ""),
                "snapshot_time": row.get("snapshot_time", ""),
                "snapshot_commit": row.get("snapshot_commit", ""),
                "relative_path": row.get("relative_path", ""),
                "file_sha256": row.get("file_sha256", ""),
                "python_lines": row.get("physical_line_count", ""),
                "parse_status": row.get("parse_status", ""),
                **metrics,
            }
            writer.writerow(output)
            if clean(metrics["file_ml_agc_like_primary"]) == "1":
                selected_rows_buffer.append(output)

            source = clean(row.get("dataset_source")).casefold() or "unknown"
            for group in ("all", source):
                for threshold in support_thresholds:
                    bucket = support[(group, threshold)]
                    bucket["python_file_rows"] += 1
                    if clean(row.get("parse_status")).casefold() == "prepared":
                        bucket["prepared_file_rows"] += 1
                    if status == "scored":
                        bucket["files_with_fun"] += 1
                        share = float(metrics["file_ml_agc_share_space_by_token_weighted"])
                        if share > threshold:
                            bucket["selected_files"] += 1
                        if math.isclose(share, threshold, rel_tol=0.0, abs_tol=1e-15):
                            bucket["ties_at_threshold"] += 1
        tmp = Path(handle.name)
    os.replace(tmp, file_output_path)

    atomic_write_csv(selected_output_path, selected_rows_buffer, SELECTED_OUTPUT_COLUMNS)

    support_rows: list[dict[str, Any]] = []
    for (group, threshold), bucket in sorted(support.items(), key=lambda item: (item[0][0], item[0][1])):
        files_fun = bucket["files_with_fun"]
        files_all = bucket["python_file_rows"]
        selected = bucket["selected_files"]
        support_rows.append(
            {
                "dataset_source": group,
                "threshold": threshold,
                "operator": ">",
                **bucket,
                "selected_share_of_fun_files": selected / files_fun if files_fun else "",
                "selected_share_of_python_files": selected / files_all if files_all else "",
            }
        )
    atomic_write_csv(support_output_path, support_rows, SUPPORT_COLUMNS)

    if max_files == 0:
        add_check(checks, "a04_output_file_rows", output_rows == EXPECTED_PYTHON_FILES, output_rows, EXPECTED_PYTHON_FILES, "A04 full output must contain one row for every A05 Python file row.")
        add_check(checks, "a04_files_with_fun", files_with_fun == EXPECTED_FILES_WITH_FUN, files_with_fun, EXPECTED_FILES_WITH_FUN, "Files with primary FUN must match the frozen A05/A12 universe.")
        add_check(checks, "a04_no_fun_files", no_fun_files == EXPECTED_NO_FUN_FILES, no_fun_files, EXPECTED_NO_FUN_FILES, "Prepared files with no primary FUN must remain unclassified.")
        add_check(checks, "a04_not_prepared_files", not_prepared_files == EXPECTED_NOT_PREPARED_FILES, not_prepared_files, EXPECTED_NOT_PREPARED_FILES, "A05 explicit file exclusions must stay outside ML file classification.")
        add_check(checks, "a04_file_occurrence_conservation", sum_file_occurrences == EXPECTED_OCCURRENCES, sum_file_occurrences, EXPECTED_OCCURRENCES, "File aggregation must conserve all A03 FUN occurrences.")
        add_check(checks, "a04_file_agc_occurrence_conservation", sum_file_agc_occurrences == EXPECTED_AGC_OCCURRENCES, sum_file_agc_occurrences, EXPECTED_AGC_OCCURRENCES, "File aggregation must conserve all A03 AGC occurrence labels.")
        add_check(checks, "a04_file_token_conservation", sum_file_tokens == EXPECTED_TOTAL_SPACE_TOKENS, sum_file_tokens, EXPECTED_TOTAL_SPACE_TOKENS, "File aggregation must conserve the A03 body-size denominator.")
        add_check(checks, "a04_file_agc_token_conservation", sum_file_agc_tokens == EXPECTED_AGC_SPACE_TOKENS, sum_file_agc_tokens, EXPECTED_AGC_SPACE_TOKENS, "File aggregation must conserve the A03 AGC body-size numerator.")
        add_check(checks, "a04_not_prepared_with_fun", not_prepared_with_fun == 0, not_prepared_with_fun, 0, "A05 not-prepared file rows must not receive primary FUN predictions.")
    else:
        add_check(checks, "a04_smoke_output_file_rows", output_rows == max_files, output_rows, max_files, "Smoke output must contain exactly the requested A05 file prefix.")
    add_check(checks, "a04_orphan_occurrence_file_keys", len(orphan_accumulators) == 0, len(orphan_accumulators), 0, "Every accumulated A03 occurrence file key must resolve to an emitted A05 file row.")

    return {
        "file_rows": output_rows,
        "files_with_fun": files_with_fun,
        "files_no_ml_fun": no_fun_files,
        "files_not_prepared": not_prepared_files,
        "selected_primary_files": selected_primary,
        "mapping_warning_files": warning_files,
        "not_prepared_with_fun": not_prepared_with_fun,
        "sum_file_occurrences": sum_file_occurrences,
        "sum_file_agc_occurrences": sum_file_agc_occurrences,
        "sum_file_space_by_tokens": sum_file_tokens,
        "sum_file_agc_space_by_tokens": sum_file_agc_tokens,
        "status_counts": dict(sorted(status_counts.items())),
        "orphan_occurrence_file_keys": len(orphan_accumulators),
        "outputs": {
            "file_scores": str(file_output_path),
            "selected_primary_files": str(selected_output_path),
            "threshold_support": str(support_output_path),
        },
        "support_rows": support_rows,
    }


def verify_output(output_root: Path, expected_file_rows: int | None = None) -> None:
    summary_path = output_root / "summary.json"
    checks_path = output_root / "checks.csv"
    file_scores_path = output_root / "python_ml_fun_file_scores.csv"
    selected_path = output_root / "python_ml_fun_selected_files_primary.csv"
    support_path = output_root / "python_ml_fun_threshold_support.csv"
    metadata_path = output_root / "metadata.json"
    for path in (summary_path, checks_path, file_scores_path, selected_path, support_path, metadata_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    summary = read_json(summary_path)
    if clean(summary.get("status")) not in {"PASS", "PASS_WITH_WARNINGS"}:
        raise ValueError(f"A04 summary status is not acceptable: {summary.get('status')}")
    if int(summary.get("failed_hard_checks", -1)) != 0:
        raise ValueError("A04 summary has failed hard checks")

    failed_checks = [row for row in iter_csv(checks_path) if clean(row.get("severity")) == "hard" and clean(row.get("passed")) != "1"]
    if failed_checks:
        raise ValueError(f"A04 checks.csv contains failed hard checks: {failed_checks[:5]}")

    rows = 0
    selected = 0
    scored = 0
    no_fun = 0
    not_prepared = 0
    rule_errors = 0
    for row in iter_csv(file_scores_path):
        rows += 1
        status = clean(row.get("file_ml_agc_status"))
        flag = clean(row.get("file_ml_agc_like_primary"))
        if status == "scored":
            scored += 1
            share = parse_float(row.get("file_ml_agc_share_space_by_token_weighted"), f"verify row {rows}.weighted_share")
            expected_flag = "1" if share > PRIMARY_THRESHOLD else "0"
            if flag != expected_flag:
                rule_errors += 1
            if flag == "1":
                selected += 1
        elif status == "no_ml_fun":
            no_fun += 1
            if flag != "":
                rule_errors += 1
        elif status == "file_not_prepared":
            not_prepared += 1
            if flag != "":
                rule_errors += 1
        else:
            rule_errors += 1

    if expected_file_rows is not None and rows != expected_file_rows:
        raise ValueError(f"A04 file row count mismatch: observed={rows} expected={expected_file_rows}")
    if rule_errors:
        raise ValueError(f"A04 primary file rule verification failures: {rule_errors}")
    if selected != int(summary["files"]["selected_primary_files"]):
        raise ValueError("A04 selected primary file count does not match summary")
    selected_file_rows = sum(1 for _ in iter_csv(selected_path))
    if selected_file_rows != selected:
        raise ValueError(f"A04 selected-file output count mismatch: {selected_file_rows} != {selected}")
    primary_support = [
        row for row in iter_csv(support_path)
        if clean(row.get("dataset_source")) == "all"
        and math.isclose(parse_float(row.get("threshold"), "support.threshold"), PRIMARY_THRESHOLD, rel_tol=0.0, abs_tol=1e-15)
    ]
    if len(primary_support) != 1 or parse_int(primary_support[0].get("selected_files"), "support.selected_files") != selected:
        raise ValueError("A04 threshold-support primary selected-file count does not match file output")

    print("A04 output verification: PASS")
    print(f"Status:                    {summary['status']}")
    print(f"File rows:                 {rows}")
    print(f"Files with FUN:            {scored}")
    print(f"Primary AGC-like files:    {selected}")
    print(f"Files with no ML FUN:      {no_fun}")
    print(f"Files not prepared:        {not_prepared}")
    print(f"Failed hard checks:        {summary['failed_hard_checks']}")


def run_self_test() -> None:
    acc = FileAccumulator()
    for predicted_agc, tokens, human_score in [
        (1, 100, -1.0),
        (1, 220, -2.0),
        (0, 10, 1.0),
        (0, 12, 2.0),
        (0, 20, 3.0),
    ]:
        acc.add(
            predicted_agc=predicted_agc,
            tokens=tokens,
            human_score=human_score,
            agc_score=-human_score,
            mapping_warning=False,
        )
    metrics = acc.metrics("prepared", 0.50)
    assert metrics["ml_fun_occurrences_total"] == 5
    assert metrics["ml_fun_agc_occurrences"] == 2
    assert math.isclose(float(metrics["file_ml_agc_share_by_count"]), 0.4, abs_tol=1e-15)
    assert math.isclose(float(metrics["file_ml_agc_share_space_by_token_weighted"]), 320 / 362, abs_tol=1e-15)
    assert metrics["file_ml_agc_like_primary"] == 1
    assert metrics["file_ml_agc_status"] == "scored"

    no_fun = FileAccumulator().metrics("prepared", 0.50)
    assert no_fun["file_ml_agc_status"] == "no_ml_fun"
    assert no_fun["file_ml_agc_like_primary"] == ""
    excluded = FileAccumulator().metrics("excluded_symlink", 0.50)
    assert excluded["file_ml_agc_status"] == "file_not_prepared"
    assert excluded["file_ml_agc_like_primary"] == ""

    tie = FileAccumulator()
    tie.add(predicted_agc=1, tokens=50, human_score=-1.0, agc_score=1.0, mapping_warning=False)
    tie.add(predicted_agc=0, tokens=50, human_score=1.0, agc_score=-1.0, mapping_warning=False)
    tie_metrics = tie.metrics("prepared", 0.50)
    assert math.isclose(float(tie_metrics["file_ml_agc_share_space_by_token_weighted"]), 0.5, abs_tol=1e-15)
    assert tie_metrics["file_ml_agc_like_primary"] == 0
    print("aggregate_ml_fun_files self-test: PASS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate A03 ML FUN predictions to A05 historical Python files.")
    parser.add_argument("--a03-root", type=Path, default=Path("src/app/data_did_agc_analysis/run-x-a03"))
    parser.add_argument("--a05-root", type=Path, required=False, default=Path("../detect_code_gpt/output/snapshot_npr/run-x-a05"))
    parser.add_argument("--output-root", type=Path, default=Path("src/app/data_did_agc_analysis/run-x-a04"))
    parser.add_argument("--max-files", type=int, default=0, help="0 means full A05 file universe; positive values are smoke-prefix size.")
    parser.add_argument("--primary-threshold", type=float, default=PRIMARY_THRESHOLD)
    parser.add_argument("--support-thresholds", default=",".join(str(value) for value in SUPPORT_THRESHOLDS))
    parser.add_argument("--progress-every", type=int, default=100_000)
    parser.add_argument("--verify-output", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return 0
    if args.verify_output:
        expected_rows = EXPECTED_PYTHON_FILES if args.max_files == 0 else args.max_files
        verify_output(args.output_root, expected_rows)
        return 0

    if not math.isclose(args.primary_threshold, PRIMARY_THRESHOLD, rel_tol=0.0, abs_tol=1e-15):
        raise ValueError(f"run-x-a04-v1 freezes primary threshold at {PRIMARY_THRESHOLD}; found {args.primary_threshold}")
    support_thresholds = tuple(float(item.strip()) for item in args.support_thresholds.split(",") if item.strip())
    if PRIMARY_THRESHOLD not in support_thresholds:
        raise ValueError("support threshold grid must include the frozen primary threshold 0.50")
    if any(value < 0 or value > 1 for value in support_thresholds):
        raise ValueError("support thresholds must lie in [0,1]")

    started = time.time()
    checks: list[dict[str, Any]] = []
    args.output_root.mkdir(parents=True, exist_ok=True)

    a03_summary, a03_metadata = load_a03_contract(args.a03_root, checks)
    occurrence_path = args.a03_root / "ml_fun_occurrence_predictions.csv"
    file_manifest = args.a05_root / "python_file_manifest.csv"
    if not file_manifest.is_file():
        raise FileNotFoundError(file_manifest)

    selected_rows, selected_keys, file_manifest_diag = load_file_manifest_info(
        file_manifest, args.max_files, checks
    )

    expected_occurrences = int(a03_summary["expanded_occurrences"])
    expected_agc_occurrences = int(a03_summary["occurrence_label_counts"]["agc"])
    expected_hwc_occurrences = int(a03_summary["occurrence_label_counts"]["human"])
    expected_total_tokens = int(a03_summary["occurrence_body_space_token_weight_total"])
    expected_agc_tokens = int(a03_summary["occurrence_body_space_token_weight_agc"])

    for label, observed, expected in (
        ("a03_summary_occurrences", expected_occurrences, EXPECTED_OCCURRENCES),
        ("a03_summary_agc_occurrences", expected_agc_occurrences, EXPECTED_AGC_OCCURRENCES),
        ("a03_summary_hwc_occurrences", expected_hwc_occurrences, EXPECTED_HWC_OCCURRENCES),
        ("a03_summary_total_tokens", expected_total_tokens, EXPECTED_TOTAL_SPACE_TOKENS),
        ("a03_summary_agc_tokens", expected_agc_tokens, EXPECTED_AGC_SPACE_TOKENS),
    ):
        add_check(checks, label, observed == expected, observed, expected, "A03 frozen summary must match the authoritative full-run accounting.")

    accumulators, occurrence_diag = stream_occurrences(
        occurrence_path,
        selected_keys,
        checks,
        expected_occurrences,
        expected_agc_occurrences,
        expected_hwc_occurrences,
        expected_total_tokens,
        expected_agc_tokens,
        args.progress_every,
    )

    file_diag = write_file_outputs(
        file_manifest,
        selected_rows,
        accumulators,
        args.output_root,
        args.primary_threshold,
        support_thresholds,
        args.max_files,
        checks,
    )

    hard_failures = [row for row in checks if row["severity"] == "hard" and not row["passed"]]
    warning_count = occurrence_diag["mapping_warning_occurrences"]
    status = "FAIL" if hard_failures else ("PASS_WITH_WARNINGS" if warning_count > 0 else "PASS")

    checks_path = args.output_root / "checks.csv"
    atomic_write_csv(checks_path, checks, CHECK_COLUMNS)

    summary = {
        "run": SCRIPT_VERSION,
        "mode": "smoke" if args.max_files > 0 else "full",
        "status": status,
        "failed_hard_checks": len(hard_failures),
        "primary_file_rule": {
            "metric": "file_ml_agc_share_space_by_token_weighted",
            "operator": ">",
            "threshold": args.primary_threshold,
            "weight": "npr_body_space_by_token_count",
            "no_fun_policy": "blank/unclassified; never imputed as HWC",
        },
        "a05_file_manifest": file_manifest_diag,
        "a03_occurrences": occurrence_diag,
        "files": {key: value for key, value in file_diag.items() if key not in {"support_rows"}},
        "support_thresholds": list(support_thresholds),
        "elapsed_seconds": round(time.time() - started, 3),
        "created_at_utc": utc_now(),
    }
    atomic_write_json(args.output_root / "summary.json", summary)

    metadata = {
        "run": SCRIPT_VERSION,
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "inputs": {
            "a03_root": str(args.a03_root.resolve()),
            "a03_summary_sha256": sha256_file(args.a03_root / "summary.json"),
            "a03_metadata_sha256": sha256_file(args.a03_root / "metadata.json"),
            "a03_occurrence_predictions": str(occurrence_path.resolve()),
            "a03_occurrence_predictions_sha256": sha256_file(occurrence_path),
            "a05_root": str(args.a05_root.resolve()),
            "a05_file_manifest": str(file_manifest.resolve()),
            "a05_file_manifest_sha256": sha256_file(file_manifest),
        },
        "upstream_detector_fingerprint": a03_metadata.get("detector_fingerprint", {}),
        "aggregation_contract": {
            "function_universe": "A03-expanded exact A02/A05 primary FUN occurrences",
            "file_key": "snapshot_id + relative_path + file_sha256",
            "primary_weight": "A05/NPR function-body literal-space-token count",
            "primary_metric": "sum(weight * I[predicted_agc]) / sum(weight)",
            "primary_rule": "AGC-like file iff weighted AGC share > 0.50",
            "strict_tie_policy": "share == 0.50 is not selected",
            "no_fun_policy": "prepared file with zero primary FUN remains unclassified",
            "not_prepared_policy": "A05 excluded/not-prepared file remains unclassified",
            "continuous_robustness": "retain weighted mean human decision score and AGC-oriented score",
            "support_grid_role": "descriptive support audit only; 0.50 is the frozen primary rule",
        },
        "created_at_utc": utc_now(),
    }
    atomic_write_json(args.output_root / "metadata.json", metadata)

    print("=" * 80)
    print("run-x-a04 ML FUN file aggregation")
    print(f"Status:                              {status}")
    print(f"A03 FUN occurrences scanned:        {occurrence_diag['rows']}")
    print(f"A03 AGC / HWC occurrences:          {occurrence_diag['agc_occurrences']} / {occurrence_diag['hwc_occurrences']}")
    print(f"A03 body space tokens total:        {occurrence_diag['body_space_tokens_total']}")
    print(f"A03 AGC body space tokens:          {occurrence_diag['body_space_tokens_agc']}")
    print(f"Output Python file rows:            {file_diag['file_rows']}")
    print(f"Files with FUN:                     {file_diag['files_with_fun']}")
    print(f"Primary AGC-like files (> 0.50):    {file_diag['selected_primary_files']}")
    print(f"Files with no ML FUN:               {file_diag['files_no_ml_fun']}")
    print(f"Files not prepared:                 {file_diag['files_not_prepared']}")
    print(f"Mapping-warning file rows:          {file_diag['mapping_warning_files']}")
    print(f"Mapping-warning occurrences:        {occurrence_diag['mapping_warning_occurrences']}")
    print(f"Failed hard checks:                 {len(hard_failures)}")
    print(f"File scores:                        {file_diag['outputs']['file_scores']}")
    print(f"Primary selected files:             {file_diag['outputs']['selected_primary_files']}")
    print(f"Threshold support:                  {file_diag['outputs']['threshold_support']}")
    print("=" * 80)

    return 0 if not hard_failures else 5


if __name__ == "__main__":
    raise SystemExit(main())
