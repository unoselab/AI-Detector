#!/usr/bin/env python3
"""
score_ml_cfun_sources-v1.py
==========================

Run the frozen run-x-a01 CodeLlama-7B SVM+AST detector on the exact standalone
Python C_FUN method sources prepared and repaired by run-x-a05-v3.

The script keeps detector scoring separate from downstream file aggregation.
It performs four tasks only:

1. Verify the frozen A01 detector contract and the repaired A05 input contract.
2. Score each unique A05 standalone-method source exactly once.
3. Expand the unique-source prediction back to every A05 C_FUN occurrence.
4. Emit strict provenance/QC artifacts for the next file-level aggregation run.

Primary frozen detector
-----------------------
Generator/source         : CodeLlama-7B
Classifier               : SVM
Representation           : AST
Embedding                 : Salesforce/codet5p-110m-embedding
Embedding max length      : 2048
Score mode                : decision
Human label               : 1
AGC label                 : 0
Human decision boundary   : 0.0
AGC-oriented score        : -human_decision_score

Important design rule
---------------------
The ML inference deduplication key is ml_source_sha256, not the NPR body SHA.
A05 showed that the same NPR body can map to multiple distinct standalone
method sources because names, signatures, decorators, or other header text
can differ.

A06 does NOT:
- retrain or tune the classifier,
- search for a new decision threshold,
- aggregate predictions to files,
- access SonarQube outcomes,
- run a DiD model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import shutil
import sys
import tempfile
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Sequence

SCRIPT_VERSION = "run-x-a06-v1"
EXPECTED_OCCURRENCES = 1_677_916
EXPECTED_UNIQUE_ML_SOURCES = 232_653
EXPECTED_UNIQUE_NPR_BODY_SHA = 195_193
EXPECTED_FILES_WITH_CFUN = 196_190
EXPECTED_A05_RUN = "run-x-a05-v3"
EXPECTED_A05_MODE = "repair"
EXPECTED_A05_V2_SUCCESS_OCCURRENCES = 1_676_970
EXPECTED_A05_V3_RECOVERED_OCCURRENCES = 946
EXPECTED_A05_SUMMARY_SHA256 = "49afbbf1c0b42aab142530fb5909f158c75bc0acdf023d0da46162ae163f46e4"
EXPECTED_A05_METADATA_SHA256 = "ccdd8d8e926d8f46b2cc6c50083d0b5c3d6554524699015e116ccfba318cf8af"
EXPECTED_NPR_A05_CODE_MANIFEST_SHA256 = "1acb3726f5c62e6154672f1aff592973c65a13e58dbfd37f8058560d1a474e6c"
EXPECTED_CLASSIFIER = "svm"
EXPECTED_REPRESENTATION = "ast"
EXPECTED_SCORE_MODE = "decision"
EXPECTED_THRESHOLD = 0.0
EXPECTED_EMBEDDING_MODEL_ID = "Salesforce/codet5p-110m-embedding"
EXPECTED_MAX_LEN = 2048
FULL_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

SOURCE_PREDICTION_COLUMNS = [
    "ml_source_sha256",
    "ml_source_relative_path",
    "occurrence_count",
    "function_name",
    "function_kind",
    "ml_source_character_count",
    "ml_source_utf8_byte_count",
    "ml_source_physical_line_count",
    "ml_ast_sequence_character_count_a05",
    "ml_ast_sequence_token_count_a05",
    "a05_mapping_warning_present",
    "source_artifact_sha256_verified",
    "detector_blocks_found",
    "detector_block_kind",
    "detector_block_name",
    "detector_block_covers_full_source",
    "pred_label",
    "predicted_agc",
    "human_score",
    "human_decision_score",
    "ml_agc_score",
    "score_mode",
    "model_key",
    "scoring_status",
    "error_type",
    "error_message",
]

FAILURE_COLUMNS = [
    "ml_source_sha256",
    "ml_source_relative_path",
    "function_name",
    "stage",
    "error_type",
    "error_message",
]

OCCURRENCE_PREDICTION_COLUMNS = [
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
    "function_name",
    "function_kind",
    "occurrence_index",
    "npr_body_sha256",
    "npr_body_space_by_token_count",
    "ml_source_sha256",
    "a05_mapping_warning",
    "pred_label",
    "predicted_agc",
    "human_decision_score",
    "ml_agc_score",
    "score_mode",
    "model_key",
]

CHECK_COLUMNS = ["check", "severity", "passed", "observed", "expected", "detail"]


@dataclass
class FrozenContract:
    a01_summary: dict[str, Any]
    a01_metadata: dict[str, Any]
    model_pickle: Path
    model_sha256: str
    expected_model_key: str
    validation_test_csv: Path
    validation_predictions_csv: Path
    max_len: int


@dataclass
class DetectorContext:
    module: Any
    parser: Any
    ast_function: Any
    tokenizer: Any
    embedding_model: Any
    device: str
    classifier: Any
    model_key: str
    model_pickle: Path
    model_sha256: str
    max_len: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def as_int(value: Any, field: str) -> int:
    text = clean(value)
    if not text:
        raise ValueError(f"missing integer field {field}")
    return int(text)


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


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(payload.encode("utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


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
        temp = Path(handle.name)
    os.replace(temp, path)


def atomic_write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Sequence[str]) -> None:
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
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        temp = Path(handle.name)
    os.replace(temp, path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise SystemExit(f"[ERROR] {label} not found: {path}")


def require_dir(path: Path, label: str) -> None:
    if not path.is_dir():
        raise SystemExit(f"[ERROR] {label} not found: {path}")


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe relative path: {value!r}")
    return path


def resolve_under(root: Path, relative: str) -> Path:
    rel = safe_relative_path(relative)
    candidate = root.joinpath(*rel.parts)
    resolved_root = root.resolve()
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {relative!r}") from exc
    return resolved


def add_check(
    checks: list[dict[str, Any]],
    name: str,
    severity: str,
    passed: bool,
    observed: Any,
    expected: Any,
    detail: str = "",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a01-root", type=Path, required=False)
    parser.add_argument("--a05-root", type=Path, required=False)
    parser.add_argument("--output-root", type=Path, required=False)
    parser.add_argument("--tree-sitter-lib", type=Path, required=False)
    parser.add_argument("--ast-helper-dir", type=Path, required=False)
    parser.add_argument("--device", default=None)
    parser.add_argument("--max-sources", type=int, default=0)
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--progress-every", type=int, default=500)
    parser.add_argument("--compatibility-check-rows", type=int, default=32)
    parser.add_argument("--compatibility-score-tolerance", type=float, default=1e-5)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verify-output", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--expected-occurrences", type=int, default=EXPECTED_OCCURRENCES)
    parser.add_argument("--expected-unique-ml-sources", type=int, default=EXPECTED_UNIQUE_ML_SOURCES)
    parser.add_argument("--expected-unique-npr-body-sha", type=int, default=EXPECTED_UNIQUE_NPR_BODY_SHA)
    parser.add_argument("--expected-files-with-cfun", type=int, default=EXPECTED_FILES_WITH_CFUN)
    return parser.parse_args()


def validate_cli(args: argparse.Namespace) -> None:
    if args.self_test:
        return
    required = {
        "--a01-root": args.a01_root,
        "--a05-root": args.a05_root,
        "--output-root": args.output_root,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit("[ERROR] missing required arguments: " + ", ".join(missing))
    if not args.verify_output:
        for name, value in {
            "--tree-sitter-lib": args.tree_sitter_lib,
            "--ast-helper-dir": args.ast_helper_dir,
        }.items():
            if value is None:
                raise SystemExit(f"[ERROR] {name} is required for scoring")
    if args.max_sources < 0:
        raise SystemExit("[ERROR] --max-sources must be >= 0")
    if args.chunk_size <= 0 or args.progress_every <= 0:
        raise SystemExit("[ERROR] --chunk-size and --progress-every must be positive")
    if args.compatibility_check_rows < 0:
        raise SystemExit("[ERROR] --compatibility-check-rows must be >= 0")
    if args.compatibility_score_tolerance <= 0:
        raise SystemExit("[ERROR] --compatibility-score-tolerance must be positive")


def load_a01_contract(a01_root: Path) -> FrozenContract:
    summary_path = a01_root / "detector_freeze_summary.json"
    metadata_path = a01_root / "detector_freeze_metadata.json"
    predictions_path = a01_root / "validation/validation_predictions.csv"
    require_file(summary_path, "A01 freeze summary")
    require_file(metadata_path, "A01 freeze metadata")
    require_file(predictions_path, "A01 validation predictions")
    summary = read_json(summary_path)
    metadata = read_json(metadata_path)
    if summary.get("status") != "PASS" or int(summary.get("failed_hard_checks", -1)) != 0:
        raise SystemExit("[ERROR] A01 detector freeze is not a clean PASS")
    spec = summary.get("frozen_detector_spec", {})
    expected = {
        "classifier": EXPECTED_CLASSIFIER,
        "representation": EXPECTED_REPRESENTATION,
        "embedding_model_id": EXPECTED_EMBEDDING_MODEL_ID,
        "max_len": EXPECTED_MAX_LEN,
        "score_mode": EXPECTED_SCORE_MODE,
        "human_decision_threshold": EXPECTED_THRESHOLD,
    }
    for field, value in expected.items():
        if spec.get(field) != value:
            raise SystemExit(f"[ERROR] A01 frozen detector {field}={spec.get(field)!r}, expected {value!r}")
    if spec.get("label_convention") != {"human": 1, "agc": 0}:
        raise SystemExit("[ERROR] unexpected A01 label convention")
    if spec.get("function_prediction_rule") != "agc if human_decision_score < 0 else human":
        raise SystemExit("[ERROR] unexpected A01 function prediction rule")
    if metadata.get("frozen_detector_spec") != spec:
        raise SystemExit("[ERROR] A01 summary/metadata frozen detector specs differ")
    inputs = metadata.get("inputs", {})
    model_pickle = Path(clean(inputs.get("model_pickle"))).expanduser()
    test_csv = Path(clean(inputs.get("test_csv"))).expanduser()
    require_file(model_pickle, "A01 model pickle")
    require_file(test_csv, "A01 validation test CSV")
    model_sha = sha256_file(model_pickle)
    if model_sha != clean(inputs.get("model_pickle_sha256")):
        raise SystemExit("[ERROR] A01 model pickle SHA-256 no longer matches frozen metadata")
    if sha256_file(test_csv) != clean(inputs.get("test_csv_sha256")):
        raise SystemExit("[ERROR] A01 test CSV SHA-256 no longer matches frozen metadata")
    return FrozenContract(
        a01_summary=summary,
        a01_metadata=metadata,
        model_pickle=model_pickle.resolve(),
        model_sha256=model_sha,
        expected_model_key=clean(metadata.get("expected_model_key")),
        validation_test_csv=test_csv.resolve(),
        validation_predictions_csv=predictions_path.resolve(),
        max_len=int(spec["max_len"]),
    )


def load_a05_contract(
    a05_root: Path,
    expected_occurrences: int,
    expected_unique_sources: int,
    expected_unique_npr_body_sha: int,
    expected_files_with_cfun: int,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    """Load and strictly validate the repaired A05-v3 C_FUN input contract."""
    summary_path = a05_root / "summary.json"
    metadata_path = a05_root / "metadata.json"
    checks_path = a05_root / "checks.csv"
    unique_path = a05_root / "python_ml_cfun_unique_source_manifest.csv"
    occurrence_path = a05_root / "python_ml_cfun_occurrence_manifest.csv"
    failure_path = a05_root / "python_ml_cfun_mapping_failures.csv"
    for path, label in [
        (summary_path, "A05-v3 repaired summary"),
        (metadata_path, "A05-v3 repaired metadata"),
        (checks_path, "A05-v3 repaired checks"),
        (unique_path, "A05-v3 repaired unique source manifest"),
        (occurrence_path, "A05-v3 repaired occurrence manifest"),
        (failure_path, "A05-v3 repaired mapping failure manifest"),
    ]:
        require_file(path, label)

    observed_summary_sha = sha256_file(summary_path)
    observed_metadata_sha = sha256_file(metadata_path)
    if observed_summary_sha != EXPECTED_A05_SUMMARY_SHA256:
        raise SystemExit(
            "[ERROR] A05-v3 repaired summary SHA-256 differs from the frozen production artifact\n"
            f"        observed: {observed_summary_sha}\n"
            f"        expected: {EXPECTED_A05_SUMMARY_SHA256}"
        )
    if observed_metadata_sha != EXPECTED_A05_METADATA_SHA256:
        raise SystemExit(
            "[ERROR] A05-v3 repaired metadata SHA-256 differs from the frozen production artifact\n"
            f"        observed: {observed_metadata_sha}\n"
            f"        expected: {EXPECTED_A05_METADATA_SHA256}"
        )

    summary = read_json(summary_path)
    metadata = read_json(metadata_path)
    if summary.get("status") not in {"PASS", "PASS_WITH_WARNINGS"}:
        raise SystemExit(f"[ERROR] A05-v3 repaired status is not acceptable: {summary.get('status')!r}")
    if clean(summary.get("run")) != EXPECTED_A05_RUN or clean(summary.get("mode")) != EXPECTED_A05_MODE:
        raise SystemExit(
            f"[ERROR] expected repaired A05 run/mode {EXPECTED_A05_RUN}/{EXPECTED_A05_MODE}, "
            f"observed {summary.get('run')!r}/{summary.get('mode')!r}"
        )

    expected_summary = {
        "selected_occurrences": expected_occurrences,
        "mapped_occurrences": expected_occurrences,
        "mapping_failures": 0,
        "unique_npr_body_sha": expected_unique_npr_body_sha,
        "unique_ml_source_sha": expected_unique_sources,
        "files_with_cfun": expected_files_with_cfun,
        "v2_success_occurrences_reused": EXPECTED_A05_V2_SUCCESS_OCCURRENCES,
        "v3_recovered_occurrences": EXPECTED_A05_V3_RECOVERED_OCCURRENCES,
        "failed_hard_checks": 0,
    }
    for field, value in expected_summary.items():
        if int(summary.get(field, -1)) != int(value):
            raise SystemExit(f"[ERROR] A05-v3 {field}={summary.get(field)!r}, expected {value}")

    if clean(metadata.get("run")) != EXPECTED_A05_RUN or clean(metadata.get("mode")) != EXPECTED_A05_MODE:
        raise SystemExit("[ERROR] A05-v3 summary/metadata run or mode disagree")
    if int(metadata.get("mapping_failures", -1)) != 0:
        raise SystemExit("[ERROR] A05-v3 metadata reports mapping failures")
    if bool(metadata.get("embedding_generated")) or bool(metadata.get("classifier_inference")):
        raise SystemExit("[ERROR] A05-v3 input stage unexpectedly reports embedding/classifier inference")
    if clean(metadata.get("a05_code_manifest_sha256")) != EXPECTED_NPR_A05_CODE_MANIFEST_SHA256:
        raise SystemExit("[ERROR] A05-v3 provenance points to an unexpected NPR A05 code manifest")

    hard_failed = [
        row for row in read_csv(checks_path)
        if clean(row.get("severity")) == "hard" and clean(row.get("passed")) != "1"
    ]
    if hard_failed:
        raise SystemExit(f"[ERROR] A05-v3 checks.csv contains {len(hard_failed)} failed hard checks")

    with failure_path.open("r", encoding="utf-8-sig", newline="") as handle:
        if any(True for _ in csv.DictReader(handle)):
            raise SystemExit("[ERROR] A05-v3 mapping failure manifest is not empty")

    return summary, metadata, unique_path, occurrence_path

def load_unique_source_rows(
    path: Path,
    expected_unique_sources: int,
    expected_occurrences: int,
) -> list[dict[str, str]]:
    rows = read_csv(path)
    if len(rows) != expected_unique_sources:
        raise SystemExit(f"[ERROR] A05 unique source rows={len(rows)}, expected {expected_unique_sources}")
    seen: set[str] = set()
    occurrence_sum = 0
    for row in rows:
        sha = clean(row.get("ml_source_sha256")).lower()
        if not FULL_SHA256_RE.fullmatch(sha):
            raise SystemExit(f"[ERROR] invalid ml_source_sha256 in A05 manifest: {sha!r}")
        if sha in seen:
            raise SystemExit(f"[ERROR] duplicate ml_source_sha256 in A05 manifest: {sha}")
        source_rel = clean(row.get("ml_source_relative_path"))
        if not source_rel.startswith("ml_cfun_sources/"):
            raise SystemExit(f"[ERROR] unexpected C_FUN source path in A05 manifest: {source_rel!r}")
        function_kind = clean(row.get("function_kind"))
        if function_kind not in {"method", "async_method"}:
            raise SystemExit(f"[ERROR] unexpected C_FUN function_kind in A05 manifest: {function_kind!r}")
        seen.add(sha)
        occurrence_sum += as_int(row.get("occurrence_count"), "occurrence_count")
    if occurrence_sum != expected_occurrences:
        raise SystemExit(f"[ERROR] A05 unique-source occurrence sum={occurrence_sum}, expected {expected_occurrences}")
    return sorted(rows, key=lambda row: clean(row.get("ml_source_sha256")))


def initialize_detector(
    contract: FrozenContract,
    tree_sitter_lib: Path,
    ast_helper_dir: Path,
    device_override: str | None,
) -> DetectorContext:
    require_file(tree_sitter_lib, "Tree-sitter library")
    require_dir(ast_helper_dir, "AST helper directory")
    script_path = Path(__file__).resolve()
    app_dir = script_path.parents[1]
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    import torch
    import agc_detector as module  # type: ignore

    if clean(getattr(module, "EMBEDDING_MODEL_ID", "")) != EXPECTED_EMBEDDING_MODEL_ID:
        raise SystemExit("[ERROR] current agc_detector embedding model ID differs from A01 frozen contract")
    module.MAX_LEN = contract.max_len
    device = device_override or ("cuda" if torch.cuda.is_available() else "cpu")
    parser, ast_function = module.load_parser_and_F(str(tree_sitter_lib), str(ast_helper_dir))
    tokenizer, embedding_model = module.load_embedder(device)
    classifier, model_key = module.pick_classifier_from_pickle(str(contract.model_pickle), "ast_")
    if model_key != contract.expected_model_key:
        raise SystemExit(
            "[ERROR] unexpected classifier key\n"
            f"        selected: {model_key}\n"
            f"        expected: {contract.expected_model_key}"
        )
    return DetectorContext(
        module=module,
        parser=parser,
        ast_function=ast_function,
        tokenizer=tokenizer,
        embedding_model=embedding_model,
        device=device,
        classifier=classifier,
        model_key=model_key,
        model_pickle=contract.model_pickle,
        model_sha256=contract.model_sha256,
        max_len=contract.max_len,
    )


def score_source_text(source: str, expected_name: str, detector: DetectorContext) -> dict[str, Any]:
    blocks = detector.module.extract_blocks(source, detector.parser)
    if len(blocks) != 1:
        raise RuntimeError(f"standalone ML source must yield exactly one detector block; found {len(blocks)}")
    block = blocks[0]
    block_kind = clean(block.get("kind"))
    block_name = clean(block.get("name"))
    block_code = str(block.get("code", ""))
    if block_kind != "function_definition":
        raise RuntimeError(f"unexpected detector block kind: {block_kind!r}")
    if block_name != expected_name:
        raise RuntimeError(f"detector block name {block_name!r} != A05 method name {expected_name!r}")
    covers = int(block_code.strip() == source.strip())
    if not covers:
        raise RuntimeError("detector block does not cover the complete A05 standalone method source")
    vector = detector.module.build_feature_vector(
        block_code,
        EXPECTED_REPRESENTATION,
        detector.parser,
        detector.ast_function,
        detector.tokenizer,
        detector.embedding_model,
        detector.device,
    )
    pred_int, human_score_raw, score_mode = detector.module.predict_one(
        detector.classifier,
        vector,
        EXPECTED_THRESHOLD,
    )
    if score_mode != EXPECTED_SCORE_MODE:
        raise RuntimeError(f"unexpected score mode {score_mode!r}; expected {EXPECTED_SCORE_MODE!r}")
    human_score = float(human_score_raw)
    if not math.isfinite(human_score):
        raise RuntimeError(f"non-finite human decision score: {human_score!r}")
    predicted_agc = 1 if int(pred_int) == 0 else 0
    expected_agc = 1 if human_score < EXPECTED_THRESHOLD else 0
    if predicted_agc != expected_agc:
        raise RuntimeError(
            f"SVM prediction disagrees with frozen native boundary: pred={pred_int}, score={human_score}"
        )
    agc_score = -human_score
    return {
        "detector_blocks_found": 1,
        "detector_block_kind": block_kind,
        "detector_block_name": block_name,
        "detector_block_covers_full_source": covers,
        "pred_label": "agc" if predicted_agc else "human",
        "predicted_agc": predicted_agc,
        "human_score": human_score,
        "human_decision_score": human_score,
        "ml_agc_score": agc_score,
        "score_mode": score_mode,
        "model_key": detector.model_key,
        "scoring_status": "PASS",
        "error_type": "",
        "error_message": "",
    }


def compatibility_indices(total: int, requested: int) -> list[int]:
    if requested <= 0 or total <= 0:
        return []
    n = min(total, requested)
    if n == total:
        return list(range(total))
    if n == 1:
        return [0]
    return sorted({round(i * (total - 1) / (n - 1)) for i in range(n)})


def run_a01_compatibility_check(
    contract: FrozenContract,
    detector: DetectorContext,
    requested_rows: int,
    tolerance: float,
) -> dict[str, Any]:
    if requested_rows == 0:
        return {"requested": 0, "checked": 0, "failures": 0, "max_abs_score_diff": 0.0}
    test_rows = read_csv(contract.validation_test_csv)
    prediction_rows = read_csv(contract.validation_predictions_csv)
    by_idx = {clean(row.get("idx")): row for row in prediction_rows}
    indices = compatibility_indices(len(test_rows), requested_rows)
    failures: list[str] = []
    max_diff = 0.0
    for row_index in indices:
        row = test_rows[row_index]
        idx = clean(row.get("idx"))
        expected = by_idx.get(idx)
        if expected is None:
            failures.append(f"idx={idx}: missing A01 prediction")
            continue
        source = str(row.get("code", ""))
        try:
            scored = score_source_text(source, clean(detector.module.extract_blocks(source, detector.parser)[0].get("name")), detector)
            expected_pred = int(float(clean(expected.get("pred"))))
            expected_score = float(clean(expected.get("human_score")))
            observed_pred = 0 if int(scored["predicted_agc"]) else 1
            observed_score = float(scored["human_decision_score"])
            diff = abs(observed_score - expected_score)
            max_diff = max(max_diff, diff)
            if observed_pred != expected_pred or diff > tolerance:
                failures.append(
                    f"idx={idx}: pred {observed_pred}!={expected_pred} or score diff {diff:.3g}>{tolerance:.3g}"
                )
        except Exception as exc:
            failures.append(f"idx={idx}: {type(exc).__name__}: {exc}")
    if failures:
        preview = "\n".join(f"  - {item}" for item in failures[:10])
        raise SystemExit(
            f"[ERROR] A06 detector compatibility check failed for {len(failures)}/{len(indices)} rows\n{preview}"
        )
    return {
        "requested": requested_rows,
        "checked": len(indices),
        "failures": 0,
        "max_abs_score_diff": max_diff,
        "score_tolerance": tolerance,
    }


def model_fingerprint(contract: FrozenContract, detector: DetectorContext, tree_sitter_lib: Path) -> dict[str, Any]:
    module_path = Path(detector.module.__file__).resolve()
    model_config = getattr(detector.embedding_model, "config", None)
    embedding_commit = clean(getattr(model_config, "_commit_hash", ""))
    embedding_name = clean(getattr(model_config, "_name_or_path", ""))
    tokenizer_name = clean(getattr(detector.tokenizer, "name_or_path", ""))
    return {
        "a01_run": contract.a01_summary.get("run"),
        "model_pickle_sha256": detector.model_sha256,
        "model_key": detector.model_key,
        "classifier": EXPECTED_CLASSIFIER,
        "representation": EXPECTED_REPRESENTATION,
        "embedding_model_id": EXPECTED_EMBEDDING_MODEL_ID,
        "embedding_model_name_or_path": embedding_name,
        "embedding_model_commit_hash": embedding_commit,
        "tokenizer_name_or_path": tokenizer_name,
        "max_len": detector.max_len,
        "score_mode": EXPECTED_SCORE_MODE,
        "human_decision_threshold": EXPECTED_THRESHOLD,
        "agc_score_transform": "-human_decision_score",
        "device_type": detector.device.split(":", 1)[0],
        "agc_detector_module_sha256": sha256_file(module_path),
        "tree_sitter_library_sha256": sha256_file(tree_sitter_lib),
    }


def chunk_paths(root: Path, chunk_index: int) -> tuple[Path, Path]:
    stem = f"chunk-{chunk_index:06d}"
    return root / f"{stem}.csv", root / f"{stem}.json"


def expected_chunk_fingerprint(source_rows: Sequence[dict[str, str]], fingerprint: dict[str, Any]) -> str:
    payload = {
        "model": fingerprint,
        "source_sha256s": [clean(row.get("ml_source_sha256")) for row in source_rows],
    }
    return sha256_json(payload)


def validate_reusable_chunk(
    csv_path: Path,
    meta_path: Path,
    source_rows: Sequence[dict[str, str]],
    fingerprint: dict[str, Any],
) -> list[dict[str, str]] | None:
    if not csv_path.is_file() or not meta_path.is_file():
        return None
    try:
        meta = read_json(meta_path)
        expected_fp = expected_chunk_fingerprint(source_rows, fingerprint)
        if meta.get("chunk_fingerprint") != expected_fp:
            return None
        rows = read_csv(csv_path)
        expected_shas = [clean(row.get("ml_source_sha256")) for row in source_rows]
        observed_shas = [clean(row.get("ml_source_sha256")) for row in rows]
        if observed_shas != expected_shas:
            return None
        if len(rows) != len(source_rows):
            return None
        return rows
    except Exception:
        return None


def score_source_row(row: dict[str, str], a05_root: Path, detector: DetectorContext) -> dict[str, Any]:
    source_sha = clean(row.get("ml_source_sha256")).lower()
    relative = clean(row.get("ml_source_relative_path"))
    expected_name = clean(row.get("function_name"))
    base = {
        "ml_source_sha256": source_sha,
        "ml_source_relative_path": relative,
        "occurrence_count": clean(row.get("occurrence_count")),
        "function_name": expected_name,
        "function_kind": clean(row.get("function_kind")),
        "ml_source_character_count": clean(row.get("ml_source_character_count")),
        "ml_source_utf8_byte_count": clean(row.get("ml_source_utf8_byte_count")),
        "ml_source_physical_line_count": clean(row.get("ml_source_physical_line_count")),
        "ml_ast_sequence_character_count_a05": clean(row.get("ml_ast_sequence_character_count")),
        "ml_ast_sequence_token_count_a05": clean(row.get("ml_ast_sequence_token_count")),
        "a05_mapping_warning_present": clean(row.get("any_tree_sitter_standalone_warning")),
    }
    stage = "source_artifact"
    try:
        source_path = resolve_under(a05_root, relative)
        payload = source_path.read_bytes()
        if sha256_bytes(payload) != source_sha:
            raise RuntimeError("A05 standalone method source artifact SHA-256 mismatch")
        source = payload.decode("utf-8", errors="strict")
        stage = "detector_inference"
        scored = score_source_text(source, expected_name, detector)
        return {**base, "source_artifact_sha256_verified": 1, **scored}
    except Exception as exc:
        return {
            **base,
            "source_artifact_sha256_verified": 0 if stage == "source_artifact" else 1,
            "detector_blocks_found": "",
            "detector_block_kind": "",
            "detector_block_name": "",
            "detector_block_covers_full_source": "",
            "pred_label": "",
            "predicted_agc": "",
            "human_score": "",
            "human_decision_score": "",
            "ml_agc_score": "",
            "score_mode": "",
            "model_key": detector.model_key,
            "scoring_status": "FAIL",
            "error_type": type(exc).__name__,
            "error_message": f"{stage}: {exc}",
        }


def write_prediction_chunk(
    csv_path: Path,
    meta_path: Path,
    rows: Sequence[dict[str, Any]],
    source_rows: Sequence[dict[str, str]],
    fingerprint: dict[str, Any],
    chunk_index: int,
) -> None:
    atomic_write_csv(csv_path, rows, SOURCE_PREDICTION_COLUMNS)
    atomic_write_json(
        meta_path,
        {
            "run": SCRIPT_VERSION,
            "chunk_index": chunk_index,
            "rows": len(rows),
            "chunk_fingerprint": expected_chunk_fingerprint(source_rows, fingerprint),
            "model_fingerprint": fingerprint,
            "created_at_utc": utc_now(),
        },
    )


def combine_chunks(
    chunk_root: Path,
    selected_rows: Sequence[dict[str, str]],
    chunk_size: int,
    output_path: Path,
) -> list[dict[str, str]]:
    combined: list[dict[str, str]] = []
    expected_shas = [clean(row.get("ml_source_sha256")) for row in selected_rows]
    for chunk_index, start in enumerate(range(0, len(selected_rows), chunk_size)):
        csv_path, _ = chunk_paths(chunk_root, chunk_index)
        require_file(csv_path, f"A06 prediction chunk {chunk_index}")
        combined.extend(read_csv(csv_path))
    observed_shas = [clean(row.get("ml_source_sha256")) for row in combined]
    if observed_shas != expected_shas:
        raise SystemExit("[ERROR] combined prediction chunks do not match selected A05 source order")
    atomic_write_csv(output_path, combined, SOURCE_PREDICTION_COLUMNS)
    return combined


def stream_expand_occurrences(
    occurrence_manifest: Path,
    prediction_rows: Sequence[dict[str, str]],
    output_path: Path,
) -> tuple[int, int, Counter[str], int, int]:
    predictions = {clean(row.get("ml_source_sha256")): row for row in prediction_rows if clean(row.get("scoring_status")) == "PASS"}
    selected_shas = set(predictions)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    missing_predictions = 0
    label_counts: Counter[str] = Counter()
    total_weight = 0
    agc_weight = 0
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=OCCURRENCE_PREDICTION_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        with occurrence_manifest.open("r", encoding="utf-8-sig", newline="") as source_handle:
            reader = csv.DictReader(source_handle)
            for row in reader:
                source_sha = clean(row.get("ml_source_sha256"))
                if source_sha not in selected_shas:
                    continue
                if clean(row.get("code_unit_type")) != "method_body":
                    raise SystemExit(
                        f"[ERROR] A05 occurrence {clean(row.get('code_unit_id'))!r} is not method_body"
                    )
                if clean(row.get("aggregation_role")) != "primary":
                    raise SystemExit(
                        f"[ERROR] A05 occurrence {clean(row.get('code_unit_id'))!r} is not primary"
                    )
                if clean(row.get("function_kind")) not in {"method", "async_method"}:
                    raise SystemExit(
                        f"[ERROR] A05 occurrence has unexpected function_kind={clean(row.get('function_kind'))!r}"
                    )
                pred = predictions.get(source_sha)
                if pred is None:
                    missing_predictions += 1
                    continue
                weight = as_int(row.get("npr_body_space_by_token_count"), "npr_body_space_by_token_count")
                predicted_agc = int(float(clean(pred.get("predicted_agc"))))
                total_weight += weight
                if predicted_agc:
                    agc_weight += weight
                label_counts["agc" if predicted_agc else "human"] += 1
                writer.writerow(
                    {
                        "snapshot_id": clean(row.get("snapshot_id")),
                        "dataset_source": clean(row.get("dataset_source")),
                        "repo_name": clean(row.get("repo_name")),
                        "repo_key": clean(row.get("repo_key")),
                        "snapshot_time": clean(row.get("snapshot_time")),
                        "snapshot_commit": clean(row.get("snapshot_commit")),
                        "relative_path": clean(row.get("relative_path")),
                        "file_sha256": clean(row.get("file_sha256")),
                        "code_unit_id": clean(row.get("code_unit_id")),
                        "code_unit_type": clean(row.get("code_unit_type")),
                        "aggregation_role": clean(row.get("aggregation_role")),
                        "qualified_name": clean(row.get("qualified_name")),
                        "function_name": clean(row.get("function_name")),
                        "function_kind": clean(row.get("function_kind")),
                        "occurrence_index": clean(row.get("occurrence_index")),
                        "npr_body_sha256": clean(row.get("npr_body_sha256")),
                        "npr_body_space_by_token_count": weight,
                        "ml_source_sha256": source_sha,
                        "a05_mapping_warning": clean(row.get("mapping_warning")),
                        "pred_label": clean(pred.get("pred_label")),
                        "predicted_agc": predicted_agc,
                        "human_decision_score": clean(pred.get("human_decision_score")),
                        "ml_agc_score": clean(pred.get("ml_agc_score")),
                        "score_mode": clean(pred.get("score_mode")),
                        "model_key": clean(pred.get("model_key")),
                    }
                )
                row_count += 1
        temp = Path(handle.name)
    os.replace(temp, output_path)
    return row_count, missing_predictions, label_counts, total_weight, agc_weight


def verify_output(output_root: Path, expected_sources: int | None, expected_occurrences: int | None) -> int:
    summary_path = output_root / "summary.json"
    checks_path = output_root / "checks.csv"
    source_path = output_root / "ml_cfun_unique_source_predictions.csv"
    occurrence_path = output_root / "ml_cfun_occurrence_predictions.csv"
    failure_path = output_root / "scoring_failures.csv"
    metadata_path = output_root / "metadata.json"
    for path, label in [
        (summary_path, "A06 summary"),
        (checks_path, "A06 checks"),
        (source_path, "A06 unique-source predictions"),
        (occurrence_path, "A06 occurrence predictions"),
        (failure_path, "A06 scoring failures"),
        (metadata_path, "A06 metadata"),
    ]:
        require_file(path, label)
    summary = read_json(summary_path)
    checks = read_csv(checks_path)
    failures: list[str] = []
    if summary.get("status") != "PASS":
        failures.append(f"status={summary.get('status')!r}, expected PASS")
    if int(summary.get("failed_hard_checks", -1)) != 0:
        failures.append(f"failed_hard_checks={summary.get('failed_hard_checks')!r}, expected 0")
    hard_failed = [row for row in checks if clean(row.get("severity")) == "hard" and clean(row.get("passed")) != "1"]
    if hard_failed:
        failures.append(f"checks.csv has {len(hard_failed)} failed hard checks")
    if int(summary.get("scoring_failures", -1)) != 0:
        failures.append(f"scoring_failures={summary.get('scoring_failures')!r}, expected 0")
    if int(summary.get("occurrence_join_missing_predictions", -1)) != 0:
        failures.append("occurrence expansion has missing predictions")
    if expected_sources is not None and int(summary.get("selected_unique_sources", -1)) != expected_sources:
        failures.append(f"selected_unique_sources={summary.get('selected_unique_sources')!r}, expected {expected_sources}")
    if expected_occurrences is not None and int(summary.get("expanded_occurrences", -1)) != expected_occurrences:
        failures.append(f"expanded_occurrences={summary.get('expanded_occurrences')!r}, expected {expected_occurrences}")
    with failure_path.open("r", encoding="utf-8-sig", newline="") as handle:
        failure_rows = sum(1 for _ in csv.DictReader(handle))
    if failure_rows != 0:
        failures.append(f"scoring_failures.csv contains {failure_rows} rows")
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = sum(1 for _ in csv.DictReader(handle))
    if expected_sources is not None and source_rows != expected_sources:
        failures.append(f"unique-source prediction CSV rows={source_rows}, expected {expected_sources}")
    with occurrence_path.open("r", encoding="utf-8-sig", newline="") as handle:
        occurrence_rows = sum(1 for _ in csv.DictReader(handle))
    if expected_occurrences is not None and occurrence_rows != expected_occurrences:
        failures.append(f"occurrence prediction CSV rows={occurrence_rows}, expected {expected_occurrences}")
    if failures:
        print("A06 output verification: FAIL", file=sys.stderr)
        for item in failures:
            print(f"[ERROR] {item}", file=sys.stderr)
        return 1
    print("A06 output verification: PASS")
    print(f"Status:                    {summary['status']}")
    print(f"Unique sources scored:     {summary['selected_unique_sources']}")
    print(f"Expanded occurrences:      {summary['expanded_occurrences']}")
    print(f"Unique AGC sources:        {summary['unique_source_label_counts']['agc']}")
    print(f"Unique HWC sources:        {summary['unique_source_label_counts']['human']}")
    print(f"AGC occurrences:           {summary['occurrence_label_counts']['agc']}")
    print(f"HWC occurrences:           {summary['occurrence_label_counts']['human']}")
    print(f"Scoring failures:          {summary['scoring_failures']}")
    print(f"Failed hard checks:        {summary['failed_hard_checks']}")
    return 0


def run_scoring(args: argparse.Namespace) -> int:
    started = time.time()
    a01_root = args.a01_root.expanduser().resolve()
    a05_root = args.a05_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    tree_sitter_lib = args.tree_sitter_lib.expanduser().resolve()
    ast_helper_dir = args.ast_helper_dir.expanduser().resolve()
    require_dir(a01_root, "A01 root")
    require_dir(a05_root, "A05 root")
    if output_root.exists() and args.overwrite:
        shutil.rmtree(output_root)
    if output_root.exists() and not args.resume:
        raise SystemExit(f"[ERROR] A06 output exists: {output_root}; use --resume or --overwrite")
    output_root.mkdir(parents=True, exist_ok=True)

    contract = load_a01_contract(a01_root)
    a05_summary, a05_metadata, unique_manifest, occurrence_manifest = load_a05_contract(
        a05_root,
        args.expected_occurrences,
        args.expected_unique_ml_sources,
        args.expected_unique_npr_body_sha,
        args.expected_files_with_cfun,
    )
    all_sources = load_unique_source_rows(unique_manifest, args.expected_unique_ml_sources, args.expected_occurrences)
    selected_sources = all_sources[: args.max_sources] if args.max_sources else all_sources
    full_mode = args.max_sources == 0

    detector = initialize_detector(contract, tree_sitter_lib, ast_helper_dir, args.device)
    compatibility = run_a01_compatibility_check(
        contract,
        detector,
        args.compatibility_check_rows,
        args.compatibility_score_tolerance,
    )
    fingerprint = model_fingerprint(contract, detector, tree_sitter_lib)

    print("=" * 80)
    print("run-x-a06 frozen ML C_FUN scoring")
    print(f"Mode:                                {'full' if full_mode else 'smoke'}")
    print(f"A05 unique sources available:        {len(all_sources)}")
    print(f"Unique sources selected:             {len(selected_sources)}")
    print(f"A05 C_FUN occurrences available:       {args.expected_occurrences}")
    print(f"Device:                              {detector.device}")
    print(f"Model key:                           {detector.model_key}")
    print(f"Model pickle SHA256:                 {detector.model_sha256}")
    print(f"A01 compatibility rows checked:      {compatibility['checked']}")
    print(f"A01 compatibility max score diff:    {compatibility['max_abs_score_diff']:.3g}")
    print(f"Output root:                         {output_root}")
    print("=" * 80)

    chunk_root = output_root / "source_prediction_chunks"
    chunk_root.mkdir(parents=True, exist_ok=True)
    processed = 0
    reused_chunks = 0
    total_chunks = (len(selected_sources) + args.chunk_size - 1) // args.chunk_size
    for chunk_index, start in enumerate(range(0, len(selected_sources), args.chunk_size)):
        source_rows = selected_sources[start : start + args.chunk_size]
        csv_path, meta_path = chunk_paths(chunk_root, chunk_index)
        reusable = None
        if args.resume:
            reusable = validate_reusable_chunk(csv_path, meta_path, source_rows, fingerprint)
        if reusable is not None:
            reused_chunks += 1
            processed += len(source_rows)
        else:
            prediction_rows = [score_source_row(row, a05_root, detector) for row in source_rows]
            write_prediction_chunk(csv_path, meta_path, prediction_rows, source_rows, fingerprint, chunk_index)
            processed += len(source_rows)
        if processed % args.progress_every == 0 or chunk_index + 1 == total_chunks:
            print(
                f"[score] {processed}/{len(selected_sources)} unique sources "
                f"chunks={chunk_index + 1}/{total_chunks} reused_chunks={reused_chunks}"
            )

    source_predictions_path = output_root / "ml_cfun_unique_source_predictions.csv"
    combined = combine_chunks(chunk_root, selected_sources, args.chunk_size, source_predictions_path)
    failure_rows: list[dict[str, Any]] = []
    source_label_counts: Counter[str] = Counter()
    source_prediction_rule_failures = 0
    for row in combined:
        if clean(row.get("scoring_status")) != "PASS":
            failure_rows.append(
                {
                    "ml_source_sha256": clean(row.get("ml_source_sha256")),
                    "ml_source_relative_path": clean(row.get("ml_source_relative_path")),
                    "function_name": clean(row.get("function_name")),
                    "stage": clean(row.get("error_message")).split(":", 1)[0],
                    "error_type": clean(row.get("error_type")),
                    "error_message": clean(row.get("error_message")),
                }
            )
            continue
        predicted_agc = int(float(clean(row.get("predicted_agc"))))
        score = float(clean(row.get("human_decision_score")))
        source_label_counts["agc" if predicted_agc else "human"] += 1
        if predicted_agc != (1 if score < 0.0 else 0):
            source_prediction_rule_failures += 1
    atomic_write_csv(output_root / "scoring_failures.csv", failure_rows, FAILURE_COLUMNS)

    occurrence_path = output_root / "ml_cfun_occurrence_predictions.csv"
    expanded, join_missing, occurrence_counts, total_weight, agc_weight = stream_expand_occurrences(
        occurrence_manifest,
        combined,
        occurrence_path,
    )
    selected_occurrence_expected = sum(as_int(row.get("occurrence_count"), "occurrence_count") for row in selected_sources)

    checks: list[dict[str, Any]] = []
    add_check(checks, "a01_detector_freeze_pass", "hard", contract.a01_summary.get("status") == "PASS", contract.a01_summary.get("status"), "PASS")
    add_check(checks, "a01_compatibility_check", "hard", compatibility["failures"] == 0, compatibility["failures"], 0)
    add_check(checks, "a05_mapping_failures_zero", "hard", int(a05_summary.get("mapping_failures", -1)) == 0, a05_summary.get("mapping_failures"), 0)
    add_check(checks, "selected_source_prediction_count", "hard", len(combined) == len(selected_sources), len(combined), len(selected_sources))
    add_check(checks, "unique_source_scoring_failures_zero", "hard", len(failure_rows) == 0, len(failure_rows), 0)
    add_check(checks, "source_prediction_rule_consistency", "hard", source_prediction_rule_failures == 0, source_prediction_rule_failures, 0)
    add_check(checks, "occurrence_expansion_count", "hard", expanded == selected_occurrence_expected, expanded, selected_occurrence_expected)
    add_check(checks, "occurrence_join_missing_predictions", "hard", join_missing == 0, join_missing, 0)
    if full_mode:
        add_check(checks, "full_unique_source_count", "hard", len(combined) == args.expected_unique_ml_sources, len(combined), args.expected_unique_ml_sources)
        add_check(checks, "full_occurrence_count", "hard", expanded == args.expected_occurrences, expanded, args.expected_occurrences)
    hard_failures = [row for row in checks if row["severity"] == "hard" and int(row["passed"]) == 0]
    status = "PASS" if not hard_failures else "FAIL"

    summary = {
        "run": SCRIPT_VERSION,
        "mode": "full" if full_mode else "smoke",
        "status": status,
        "failed_hard_checks": len(hard_failures),
        "a05_run": clean(a05_summary.get("run")),
        "a05_mode": clean(a05_summary.get("mode")),
        "a05_unique_sources_available": len(all_sources),
        "selected_unique_sources": len(selected_sources),
        "selected_occurrences_expected": selected_occurrence_expected,
        "expanded_occurrences": expanded,
        "scoring_failures": len(failure_rows),
        "occurrence_join_missing_predictions": join_missing,
        "unique_source_label_counts": {
            "agc": int(source_label_counts.get("agc", 0)),
            "human": int(source_label_counts.get("human", 0)),
        },
        "occurrence_label_counts": {
            "agc": int(occurrence_counts.get("agc", 0)),
            "human": int(occurrence_counts.get("human", 0)),
        },
        "occurrence_body_space_token_weight_total": total_weight,
        "occurrence_body_space_token_weight_agc": agc_weight,
        "occurrence_body_space_token_weight_agc_share": (agc_weight / total_weight if total_weight else None),
        "reused_prediction_chunks": reused_chunks,
        "total_prediction_chunks": total_chunks,
        "a01_compatibility": compatibility,
        "elapsed_seconds": round(time.time() - started, 3),
        "created_at_utc": utc_now(),
    }
    metadata = {
        "run": SCRIPT_VERSION,
        "mode": summary["mode"],
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "python": sys.version,
        "platform": platform.platform(),
        "inputs": {
            "a01_summary": str(a01_root / "detector_freeze_summary.json"),
            "a01_summary_sha256": sha256_file(a01_root / "detector_freeze_summary.json"),
            "a01_metadata": str(a01_root / "detector_freeze_metadata.json"),
            "a01_metadata_sha256": sha256_file(a01_root / "detector_freeze_metadata.json"),
            "a05_summary": str(a05_root / "summary.json"),
            "a05_summary_sha256": sha256_file(a05_root / "summary.json"),
            "a05_metadata": str(a05_root / "metadata.json"),
            "a05_metadata_sha256": sha256_file(a05_root / "metadata.json"),
            "a05_unique_source_manifest": str(unique_manifest),
            "a05_unique_source_manifest_sha256": sha256_file(unique_manifest),
            "a05_occurrence_manifest": str(occurrence_manifest),
            "a05_occurrence_manifest_sha256": sha256_file(occurrence_manifest),
            "model_pickle": str(contract.model_pickle),
            "model_pickle_sha256": contract.model_sha256,
            "tree_sitter_library": str(tree_sitter_lib),
            "tree_sitter_library_sha256": sha256_file(tree_sitter_lib),
            "ast_helper_dir": str(ast_helper_dir),
        },
        "detector_fingerprint": fingerprint,
        "category": "C_FUN",
        "code_unit_type": "method_body",
        "aggregation_role": "primary",
        "deduplication_key": "ml_source_sha256",
        "expansion_key": "ml_source_sha256",
        "function_prediction_rule": "AGC iff human_decision_score < 0.0; otherwise HWC",
        "agc_score_transform": "ml_agc_score=-human_decision_score",
        "downstream_note": "A06 does not aggregate to files; A07 will use A05 C_FUN method-body space-token weights.",
        "created_at_utc": utc_now(),
    }
    atomic_write_csv(output_root / "checks.csv", checks, CHECK_COLUMNS)
    atomic_write_json(output_root / "summary.json", summary)
    atomic_write_json(output_root / "metadata.json", metadata)

    print("=" * 80)
    print("run-x-a06 ML C_FUN source scoring summary")
    print(f"Status:                              {status}")
    print(f"Unique sources selected/scored:      {len(selected_sources)} / {len(combined)}")
    print(f"Unique source AGC / HWC:             {source_label_counts.get('agc', 0)} / {source_label_counts.get('human', 0)}")
    print(f"Expanded C_FUN occurrences:           {expanded}")
    print(f"Occurrence AGC / HWC:                {occurrence_counts.get('agc', 0)} / {occurrence_counts.get('human', 0)}")
    print(f"Scoring failures:                    {len(failure_rows)}")
    print(f"Occurrence join missing predictions: {join_missing}")
    print(f"Reused prediction chunks:            {reused_chunks} / {total_chunks}")
    print(f"Failed hard checks:                  {len(hard_failures)}")
    print(f"Elapsed seconds:                     {time.time() - started:.3f}")
    print(f"Output root:                         {output_root}")
    print("=" * 80)
    return 0 if not hard_failures else 5


def run_self_test() -> int:
    assert compatibility_indices(10, 1) == [0]
    assert compatibility_indices(10, 3) == [0, 4, 9]
    assert safe_relative_path("ml_cfun_sources/aa/test.py").parts[0] == "ml_cfun_sources"
    try:
        safe_relative_path("../escape.py")
        raise AssertionError("unsafe path was accepted")
    except ValueError:
        pass
    human_score = 0.25
    assert -human_score == -0.25
    assert (1 if -0.1 < 0.0 else 0) == 1
    assert (1 if 0.0 < 0.0 else 0) == 0
    with tempfile.TemporaryDirectory(prefix="run-x-a06-selftest-") as temp_dir:
        root = Path(temp_dir)
        output = root / "out"
        output.mkdir()
        atomic_write_csv(output / "scoring_failures.csv", [], FAILURE_COLUMNS)
        assert (output / "scoring_failures.csv").read_text(encoding="utf-8").startswith("ml_source_sha256,")
        payload = {"x": 1, "y": [2, 3]}
        atomic_write_json(output / "test.json", payload)
        assert read_json(output / "test.json") == payload
    print("score_ml_cfun_sources-v1 self-test: PASS")
    return 0


def main() -> int:
    args = parse_args()
    validate_cli(args)
    if args.self_test:
        return run_self_test()
    assert args.output_root is not None
    if args.verify_output:
        expected_sources = args.expected_unique_ml_sources if args.max_sources == 0 else args.max_sources
        expected_occurrences = args.expected_occurrences if args.max_sources == 0 else None
        return verify_output(args.output_root.expanduser().resolve(), expected_sources, expected_occurrences)
    return run_scoring(args)


if __name__ == "__main__":
    raise SystemExit(main())
