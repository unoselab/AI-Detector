#!/usr/bin/env python3
"""
analyze_did_python_snapshots.py
================================

Apply a validated classifier + representation detector to exact historical
Python snapshots exported by the DiD pipeline.

The script does not reimplement AST extraction, CodeT5+ embedding, or model
selection. It imports the validated logic from src/app/agc_detector.py and adds
only the DiD-specific orchestration:

1. Discover repository/commit snapshots from _snapshot.json files.
2. Read each commit's _files.jsonl as the authoritative Python-file manifest.
3. Analyze regular .py files with the selected representation and classifier.
4. Cache predictions by content hash and model fingerprint.
5. Save commit-level checkpoints so interrupted runs can resume.
6. Combine block-, file-, and commit-level outputs.
7. Join commit results to repo_month_snapshot_manifest.csv.
8. Optionally validate raw-source inference against a labeled test CSV.

Default experiment
------------------
Experiment                : codellama-7b_4500_complexity_stratified_maxlen2048
Classifier                : SVM
Representation            : AST
Embedding max length      : 2048
Expected score mode       : decision
Default threshold         : 0.0 for decision, 0.5 for probability
Label convention          : 1 = human, 0 = AI-generated

The DiD snapshots are an unlabeled external corpus. Accuracy, F1, and AUROC are
calculated only when --validation-test-csv and the expected paper metrics are
provided.

Validation
----------
python src/app/analyze_did_python_snapshots-v2.py \
  --experiment gpt-oss_4500_complexity_stratified_maxlen2048 \
  --classifier mlp \
  --representation ast \
  --model-pickle src/ml_embeddings/data_codesearchnet/models/gpt-oss_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_gpt-oss_4500_complexity_stratified_maxlen2048_mlp_20260527_192034.pkl \
  --expected-model-key codesearchnet_gpt-oss_python_merged_4500ast_ \
  --expected-score-mode proba \
  --max-len 2048 \
  --validation-test-csv src/ml_embeddings/data_codesearchnet/splits/gpt-oss_4500_complexity_stratified_maxlen2048/codesearchnet_gpt-oss_python_merged_4500/test_.csv \
  --validation-only \
  --expected-test-rows 900 \
  --expected-acc 0.8089 \
  --expected-human-f1 0.8072 \
  --expected-ai-f1 0.8106 \
  --expected-avg-f1 0.8089 \
  --expected-auroc 0.8837 \
  --output-root src/app/data_did_agc_analysis/gpt-oss_4500_complexity_stratified_maxlen2048_mlp_ast/strict

"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import statistics
import sys
import tempfile
import tokenize
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# The script lives beside agc_detector.py, so this import works when the file is
# executed as `python src/app/analyze_did_python_snapshots.py`.
import agc_detector as agc_detector_module  # type: ignore

from agc_detector import (  # type: ignore
    EMBEDDING_MODEL_ID,
    build_feature_vector,
    extract_blocks,
    load_embedder,
    load_parser_and_F,
    pick_classifier_from_pickle,
    predict_one,
)


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent

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
DEFAULT_SNAPSHOT_ROOT = (
    WORKSPACE_ROOT / "ai_code_complexity_study_python/python_snapshots"
)
DEFAULT_REPO_MONTH_MANIFEST = (
    WORKSPACE_ROOT
    / "ai_code_complexity_study_python/ai-code-complexity-study"
    / "repo_python/run-py-3a/strict/repo_month_snapshot_manifest.csv"
)
DEFAULT_TREE_SITTER_LIB = (
    REPO_ROOT / "src/code-analyzer-tree-sitter/build/my-languages.so"
)
DEFAULT_AST_HELPER_DIR = REPO_ROOT / "src/code-analyzer-tree-sitter"

BLOCK_FIELDS = [
    "dataset_source",
    "repo_name",
    "repo_slug",
    "commit",
    "relative_path",
    "content_sha256",
    "block_idx",
    "block_kind",
    "block_name",
    "start_line",
    "end_line",
    "pred_label",
    "predicted_agc",
    "human_score",
    "human_decision_score",
    "agc_score",
    "score_mode",
    "model_key",
    "cache_hit",
]

FILE_FIELDS = [
    "dataset_source",
    "repo_name",
    "repo_slug",
    "commit",
    "relative_path",
    "content_sha256",
    "git_blob_sha",
    "git_mode",
    "file_type",
    "size_bytes",
    "line_count",
    "analysis_status",
    "blocks_scored",
    "human_blocks",
    "agc_blocks",
    "agc_block_ratio",
    "mean_human_score",
    "mean_human_decision_score",
    "mean_agc_score",
    "cache_hit",
    "error_message",
]

SNAPSHOT_FIELDS = [
    "dataset_source",
    "repo_name",
    "repo_slug",
    "commit",
    "python_files_manifest",
    "regular_files_expected",
    "files_analyzed",
    "files_with_blocks",
    "files_without_blocks",
    "symlinks_skipped",
    "blocks_scored",
    "human_blocks",
    "agc_blocks",
    "agc_block_ratio",
    "mean_agc_score",
    "median_agc_score",
    "cache_hits",
    "failure_count",
]

VALIDATION_FIELDS = [
    "idx",
    "actual_label",
    "pred",
    "human_score",
    "agc_score",
    "score_mode",
]


@dataclass(frozen=True)
class SnapshotCommit:
    dataset_source: str
    repo_slug: str
    commit: str
    commit_dir: Path
    snapshot_json: Path


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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--experiment",
        default=DEFAULT_EXPERIMENT,
        help="Training experiment identifier used for provenance and metadata.",
    )
    parser.add_argument(
        "--classifier",
        default=DEFAULT_CLASSIFIER,
        help="Classifier family, for example svm, mlp, or lr.",
    )
    parser.add_argument(
        "--representation",
        choices=["ast", "code", "combined"],
        default=DEFAULT_REPRESENTATION,
        help="Embedding representation selected from the trained pickle.",
    )
    parser.add_argument(
        "--max-len",
        type=int,
        default=DEFAULT_MAX_LEN,
        help="Tokenizer truncation length used during training.",
    )
    parser.add_argument(
        "--expected-score-mode",
        choices=["decision", "proba"],
        default=DEFAULT_EXPECTED_SCORE_MODE,
        help="Expected score source returned by the selected classifier.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help=(
            "Optional human-class threshold. When omitted, agc_detector.py uses "
            "0.0 for decision scores and 0.5 for probabilities."
        ),
    )
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        default=DEFAULT_SNAPSHOT_ROOT,
        help="Root containing treatment/ and control/ snapshot directories.",
    )
    parser.add_argument(
        "--dataset-source",
        choices=["treatment", "control", "all"],
        default="treatment",
        help="Snapshot source to analyze. Default: treatment.",
    )
    parser.add_argument(
        "--repo-month-manifest",
        type=Path,
        default=DEFAULT_REPO_MONTH_MANIFEST,
        help="DiD repo-month-to-commit mapping CSV.",
    )
    parser.add_argument(
        "--model-pickle",
        type=Path,
        default=DEFAULT_MODEL_PICKLE,
        help="Exact trained classifier pickle.",
    )
    parser.add_argument(
        "--expected-model-key",
        default=DEFAULT_MODEL_KEY,
        help="Expected representation-specific estimator key inside the pickle.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Root for validation outputs, commit checkpoints, and combined outputs. "
            "When omitted, a model-specific directory is derived automatically."
        ),
    )
    parser.add_argument(
        "--tree-sitter-lib",
        type=Path,
        default=DEFAULT_TREE_SITTER_LIB,
        help="Compiled tree-sitter language library.",
    )
    parser.add_argument(
        "--ast-helper-dir",
        type=Path,
        default=DEFAULT_AST_HELPER_DIR,
        help="Directory containing tree_sitter_ast_python.py.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="cuda, cuda:0, or cpu. Auto-detected when omitted.",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=None,
        help="Optional pilot limit after deterministic commit sorting.",
    )
    parser.add_argument(
        "--max-files-per-commit",
        type=int,
        default=None,
        help="Optional pilot limit for regular files within each commit.",
    )
    parser.add_argument(
        "--verify-hashes",
        action="store_true",
        help="Recompute and verify each regular file's SHA-256.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Reprocess commits even when a matching _SUCCESS checkpoint exists.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable persistent content-hash prediction reuse.",
    )
    parser.add_argument(
        "--skip-repo-month-panel",
        action="store_true",
        help="Do not build the repo-month output CSV.",
    )

    # Optional paper-result validation using raw code from a labeled test split.
    parser.add_argument(
        "--validation-test-csv",
        type=Path,
        default=None,
        help="Optional labeled test CSV containing idx, code, and actual label/label.",
    )
    parser.add_argument(
        "--validation-only",
        action="store_true",
        help="Run labeled test validation and exit without scanning DiD snapshots.",
    )
    parser.add_argument(
        "--expected-test-rows",
        type=int,
        default=900,
        help="Expected number of labeled validation rows.",
    )
    parser.add_argument("--expected-acc", type=float, default=None)
    parser.add_argument("--expected-human-f1", type=float, default=None)
    parser.add_argument("--expected-ai-f1", type=float, default=None)
    parser.add_argument("--expected-avg-f1", type=float, default=None)
    parser.add_argument("--expected-auroc", type=float, default=None)
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
            f"[ERROR] {option_name} must contain only letters, digits, '.', '_', or '-': {value!r}"
        )
    return text


def derive_output_root(args: argparse.Namespace) -> Path:
    tag = f"{args.experiment}_{args.classifier}_{args.representation}"
    return REPO_ROOT / "src/app/data_did_agc_analysis" / tag / "strict"


def validate_args(args: argparse.Namespace) -> None:
    args.experiment = validate_identifier(args.experiment, "--experiment")
    args.classifier = validate_identifier(args.classifier.lower(), "--classifier")
    args.expected_model_key = str(args.expected_model_key).strip()
    if not args.expected_model_key:
        raise SystemExit("[ERROR] --expected-model-key cannot be empty")
    if args.max_len <= 0:
        raise SystemExit("[ERROR] --max-len must be positive")

    args.snapshot_root = args.snapshot_root.expanduser().resolve()
    args.model_pickle = args.model_pickle.expanduser().resolve()
    args.tree_sitter_lib = args.tree_sitter_lib.expanduser().resolve()
    args.ast_helper_dir = args.ast_helper_dir.expanduser().resolve()
    args.repo_month_manifest = args.repo_month_manifest.expanduser().resolve()
    if args.output_root is None:
        args.output_root = derive_output_root(args)
    args.output_root = args.output_root.expanduser().resolve()
    if args.validation_test_csv is not None:
        args.validation_test_csv = args.validation_test_csv.expanduser().resolve()

    require_path(args.model_pickle, "file")
    require_path(args.tree_sitter_lib, "file")
    require_path(args.ast_helper_dir, "dir")

    if args.validation_only and args.validation_test_csv is None:
        raise SystemExit("[ERROR] --validation-only requires --validation-test-csv")

    if args.validation_test_csv is not None:
        require_path(args.validation_test_csv, "file")
        expected_metrics = {
            "--expected-acc": args.expected_acc,
            "--expected-human-f1": args.expected_human_f1,
            "--expected-ai-f1": args.expected_ai_f1,
            "--expected-avg-f1": args.expected_avg_f1,
            "--expected-auroc": args.expected_auroc,
        }
        missing = [name for name, value in expected_metrics.items() if value is None]
        if missing:
            raise SystemExit(
                "[ERROR] validation requires all expected metric arguments: "
                + ", ".join(missing)
            )
        if args.expected_test_rows <= 0:
            raise SystemExit("[ERROR] --expected-test-rows must be positive")

    if not args.validation_only:
        require_path(args.snapshot_root, "dir")
        sources = (
            ["treatment", "control"]
            if args.dataset_source == "all"
            else [args.dataset_source]
        )
        for source in sources:
            require_path(args.snapshot_root / source, "dir")
        if not args.skip_repo_month_panel:
            require_path(args.repo_month_manifest, "file")

    if args.max_commits is not None and args.max_commits <= 0:
        raise SystemExit("[ERROR] --max-commits must be positive")
    if args.max_files_per_commit is not None and args.max_files_per_commit <= 0:
        raise SystemExit("[ERROR] --max-files-per-commit must be positive")


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


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object at {path}:{line_number}")
            rows.append(value)
    return rows


def selected_sources(dataset_source: str) -> List[str]:
    return ["treatment", "control"] if dataset_source == "all" else [dataset_source]


def discover_snapshot_commits(
    snapshot_root: Path,
    dataset_source: str,
) -> List[SnapshotCommit]:
    commits: List[SnapshotCommit] = []
    for source in selected_sources(dataset_source):
        source_root = snapshot_root / source
        for snapshot_json in sorted(source_root.glob("*/*/_snapshot.json")):
            commit_dir = snapshot_json.parent
            commits.append(
                SnapshotCommit(
                    dataset_source=source,
                    repo_slug=commit_dir.parent.name,
                    commit=commit_dir.name,
                    commit_dir=commit_dir,
                    snapshot_json=snapshot_json,
                )
            )
    return sorted(
        commits,
        key=lambda item: (item.dataset_source, item.repo_slug, item.commit),
    )


def validate_snapshot_metadata(
    snapshot: SnapshotCommit,
    metadata: Dict[str, Any],
    file_rows: Sequence[Dict[str, Any]],
) -> str:
    required_snapshot_fields = {
        "dataset_source",
        "repo_name",
        "commit",
        "python_file_count",
    }
    missing = sorted(required_snapshot_fields - metadata.keys())
    if missing:
        raise ValueError(
            f"missing _snapshot.json fields {missing}: {snapshot.snapshot_json}"
        )

    if str(metadata["dataset_source"]) != snapshot.dataset_source:
        raise ValueError(
            f"dataset_source mismatch: directory={snapshot.dataset_source} "
            f"metadata={metadata['dataset_source']}"
        )
    if str(metadata["commit"]) != snapshot.commit:
        raise ValueError(
            f"commit mismatch: directory={snapshot.commit} metadata={metadata['commit']}"
        )

    expected_count = int(metadata["python_file_count"])
    if expected_count != len(file_rows):
        raise ValueError(
            f"python_file_count mismatch for {snapshot.commit_dir}: "
            f"metadata={expected_count} _files.jsonl={len(file_rows)}"
        )

    repo_name = str(metadata["repo_name"])
    required_file_fields = {
        "dataset_source",
        "repo_name",
        "commit",
        "relative_path",
        "file_type",
        "content_sha256",
    }
    for index, row in enumerate(file_rows, start=1):
        missing_row = sorted(required_file_fields - row.keys())
        if missing_row:
            raise ValueError(
                f"missing _files.jsonl fields {missing_row} at row {index}: "
                f"{snapshot.commit_dir / '_files.jsonl'}"
            )
        if str(row["dataset_source"]) != snapshot.dataset_source:
            raise ValueError(f"dataset_source mismatch in file row {index}")
        if str(row["repo_name"]) != repo_name:
            raise ValueError(f"repo_name mismatch in file row {index}")
        if str(row["commit"]) != snapshot.commit:
            raise ValueError(f"commit mismatch in file row {index}")
        validate_relative_path(str(row["relative_path"]))

    return repo_name


def validate_relative_path(relative_path: str) -> PurePosixPath:
    path = PurePosixPath(relative_path)
    if path.is_absolute() or not path.parts:
        raise ValueError(f"invalid relative_path: {relative_path!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe relative_path: {relative_path!r}")
    if path.suffix.lower() != ".py":
        raise ValueError(f"manifest row is not a Python file: {relative_path!r}")
    return path


def resolve_snapshot_file(commit_dir: Path, relative_path: str) -> Path:
    rel = validate_relative_path(relative_path)
    candidate = commit_dir.joinpath(*rel.parts)
    if not candidate.exists() and not candidate.is_symlink():
        raise FileNotFoundError(f"snapshot file not found: {candidate}")

    resolved_commit = commit_dir.resolve()
    resolved_candidate = candidate.resolve(strict=True)
    try:
        resolved_candidate.relative_to(resolved_commit)
    except ValueError as exc:
        raise ValueError(f"snapshot file escapes commit directory: {candidate}") from exc
    return resolved_candidate


def read_python_source(path: Path) -> str:
    # tokenize.open honors PEP 263 encoding declarations.
    with tokenize.open(path) as handle:
        return handle.read()


def safe_mean(values: Sequence[float]) -> Any:
    return statistics.fmean(values) if values else ""


def safe_median(values: Sequence[float]) -> Any:
    return statistics.median(values) if values else ""


def ratio(numerator: int, denominator: int) -> Any:
    return numerator / denominator if denominator else ""


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


def build_model_fingerprint(context: DetectorContext) -> Dict[str, Any]:
    return {
        "experiment": context.experiment,
        "classifier": context.classifier_family,
        "model_sha256": context.model_sha256,
        "model_key": context.model_key,
        "representation": context.representation,
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "max_len": context.max_len,
        "threshold": effective_threshold(context),
        "expected_score_mode": context.expected_score_mode,
    }


def build_cache_key(
    content_sha256: str,
    model_fingerprint: Dict[str, Any],
) -> str:
    payload = {
        "content_sha256": content_sha256,
        **model_fingerprint,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_path_for(cache_root: Path, cache_key: str) -> Path:
    return cache_root / cache_key[:2] / f"{cache_key}.json"


def load_cached_analysis(
    path: Path,
    expected_fingerprint: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        payload = load_json(path)
    except Exception:
        return None
    if payload.get("model_fingerprint") != expected_fingerprint:
        return None
    if not isinstance(payload.get("block_rows"), list):
        return None
    if not isinstance(payload.get("file_result"), dict):
        return None
    return payload


def save_cached_analysis(
    path: Path,
    model_fingerprint: Dict[str, Any],
    block_rows: Sequence[Dict[str, Any]],
    file_result: Dict[str, Any],
) -> None:
    atomic_write_json(
        path,
        {
            "model_fingerprint": model_fingerprint,
            "block_rows": list(block_rows),
            "file_result": file_result,
            "created_at_utc": utc_now(),
        },
    )


def make_base_file_row(
    snapshot: SnapshotCommit,
    repo_name: str,
    manifest_row: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "dataset_source": snapshot.dataset_source,
        "repo_name": repo_name,
        "repo_slug": snapshot.repo_slug,
        "commit": snapshot.commit,
        "relative_path": str(manifest_row.get("relative_path", "")),
        "content_sha256": str(manifest_row.get("content_sha256", "")),
        "git_blob_sha": str(manifest_row.get("git_blob_sha", "")),
        "git_mode": str(manifest_row.get("git_mode", "")),
        "file_type": str(manifest_row.get("file_type", "")),
        "size_bytes": manifest_row.get("size_bytes", ""),
        "line_count": manifest_row.get("line_count", ""),
    }


def analyze_regular_file(
    source: str,
    context: DetectorContext,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    blocks = extract_blocks(source, context.parser)
    if not blocks:
        return [], {
            "analysis_status": "no_top_level_blocks",
            "blocks_scored": 0,
            "human_blocks": 0,
            "agc_blocks": 0,
            "agc_block_ratio": "",
            "mean_human_score": "",
            "mean_human_decision_score": "",
            "mean_agc_score": "",
            "error_message": "",
        }

    generic_block_rows: List[Dict[str, Any]] = []
    human_scores: List[float] = []
    agc_scores: List[float] = []
    human_blocks = 0
    agc_blocks = 0

    for block_index, block in enumerate(blocks, start=1):
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
        pred_label = "agc" if predicted_agc else "human"

        if predicted_agc:
            agc_blocks += 1
        else:
            human_blocks += 1
        human_scores.append(human_score)
        agc_scores.append(agc_score)

        generic_block_rows.append(
            {
                "block_idx": block_index,
                "block_kind": block["kind"],
                "block_name": block["name"],
                "start_line": block["start_line"],
                "end_line": block["end_line"],
                "pred_label": pred_label,
                "predicted_agc": predicted_agc,
                "human_score": human_score,
                "human_decision_score": (
                    human_score if score_mode == "decision" else ""
                ),
                "agc_score": agc_score,
                "score_mode": score_mode,
                "model_key": context.model_key,
            }
        )

    blocks_scored = len(generic_block_rows)
    return generic_block_rows, {
        "analysis_status": "ok",
        "blocks_scored": blocks_scored,
        "human_blocks": human_blocks,
        "agc_blocks": agc_blocks,
        "agc_block_ratio": ratio(agc_blocks, blocks_scored),
        "mean_human_score": safe_mean(human_scores),
        "mean_human_decision_score": (
            safe_mean(human_scores)
            if context.expected_score_mode == "decision"
            else ""
        ),
        "mean_agc_score": safe_mean(agc_scores),
        "error_message": "",
    }


def attach_file_metadata_to_blocks(
    generic_rows: Sequence[Dict[str, Any]],
    base_file_row: Dict[str, Any],
    cache_hit: int,
) -> List[Dict[str, Any]]:
    prefix = {
        "dataset_source": base_file_row["dataset_source"],
        "repo_name": base_file_row["repo_name"],
        "repo_slug": base_file_row["repo_slug"],
        "commit": base_file_row["commit"],
        "relative_path": base_file_row["relative_path"],
        "content_sha256": base_file_row["content_sha256"],
    }
    result: List[Dict[str, Any]] = []
    for row in generic_rows:
        merged = {**prefix, **row, "cache_hit": cache_hit}
        result.append(merged)
    return result


def empty_file_result() -> Dict[str, Any]:
    return {
        "blocks_scored": 0,
        "human_blocks": 0,
        "agc_blocks": 0,
        "agc_block_ratio": "",
        "mean_human_score": "",
        "mean_human_decision_score": "",
        "mean_agc_score": "",
        "cache_hit": 0,
        "error_message": "",
    }


def analyze_manifest_file(
    snapshot: SnapshotCommit,
    repo_name: str,
    manifest_row: Dict[str, Any],
    context: DetectorContext,
    cache_root: Path,
    model_fingerprint: Dict[str, Any],
    verify_hashes: bool,
    use_cache: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base = make_base_file_row(snapshot, repo_name, manifest_row)
    file_type = str(manifest_row.get("file_type", ""))

    if file_type != "file":
        status = (
            "skipped_symlink"
            if file_type == "symlink"
            else "skipped_non_regular"
        )
        return [], {
            **base,
            "analysis_status": status,
            **empty_file_result(),
        }

    content_sha256 = str(manifest_row["content_sha256"])
    cache_key = build_cache_key(content_sha256, model_fingerprint)
    cache_path = cache_path_for(cache_root, cache_key)

    if use_cache:
        cached = load_cached_analysis(cache_path, model_fingerprint)
        if cached is not None:
            block_rows = attach_file_metadata_to_blocks(
                cached["block_rows"],
                base,
                cache_hit=1,
            )
            file_row = {
                **base,
                **cached["file_result"],
                "cache_hit": 1,
            }
            return block_rows, file_row

    try:
        file_path = resolve_snapshot_file(
            snapshot.commit_dir,
            base["relative_path"],
        )
        if file_path.is_symlink():
            raise RuntimeError("regular manifest row resolves to a symlink")

        if verify_hashes:
            actual_hash = sha256_file(file_path)
            if actual_hash != content_sha256:
                raise ValueError(
                    "content SHA-256 mismatch: "
                    f"manifest={content_sha256} actual={actual_hash}"
                )

        source = read_python_source(file_path)
        generic_blocks, generic_file_result = analyze_regular_file(
            source,
            context,
        )
        if use_cache:
            save_cached_analysis(
                cache_path,
                model_fingerprint,
                generic_blocks,
                generic_file_result,
            )
        block_rows = attach_file_metadata_to_blocks(
            generic_blocks,
            base,
            cache_hit=0,
        )
        file_row = {
            **base,
            **generic_file_result,
            "cache_hit": 0,
        }
        return block_rows, file_row

    except (UnicodeDecodeError, SyntaxError) as exc:
        status = "decode_error"
        message = f"{type(exc).__name__}: {exc}"
    except FileNotFoundError as exc:
        status = "missing_file"
        message = str(exc)
    except Exception as exc:  # Continue the corpus run and record the failure.
        status = "inference_error"
        message = f"{type(exc).__name__}: {exc}"

    return [], {
        **base,
        "analysis_status": status,
        **empty_file_result(),
        "error_message": message,
    }


def summarize_commit(
    snapshot: SnapshotCommit,
    repo_name: str,
    manifest_rows: Sequence[Dict[str, Any]],
    block_rows: Sequence[Dict[str, Any]],
    file_rows: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    statuses = [str(row["analysis_status"]) for row in file_rows]
    regular_expected = sum(
        1
        for row in manifest_rows
        if str(row.get("file_type", "")) == "file"
    )
    files_analyzed = sum(
        status in {"ok", "no_top_level_blocks"}
        for status in statuses
    )
    files_with_blocks = sum(status == "ok" for status in statuses)
    files_without_blocks = sum(
        status == "no_top_level_blocks"
        for status in statuses
    )
    symlinks_skipped = sum(status == "skipped_symlink" for status in statuses)
    failure_count = sum(
        status
        not in {
            "ok",
            "no_top_level_blocks",
            "skipped_symlink",
            "skipped_non_regular",
        }
        for status in statuses
    )

    blocks_scored = len(block_rows)
    agc_blocks = sum(int(row["predicted_agc"]) for row in block_rows)
    human_blocks = blocks_scored - agc_blocks
    agc_scores = [float(row["agc_score"]) for row in block_rows]

    return {
        "dataset_source": snapshot.dataset_source,
        "repo_name": repo_name,
        "repo_slug": snapshot.repo_slug,
        "commit": snapshot.commit,
        "python_files_manifest": len(manifest_rows),
        "regular_files_expected": regular_expected,
        "files_analyzed": files_analyzed,
        "files_with_blocks": files_with_blocks,
        "files_without_blocks": files_without_blocks,
        "symlinks_skipped": symlinks_skipped,
        "blocks_scored": blocks_scored,
        "human_blocks": human_blocks,
        "agc_blocks": agc_blocks,
        "agc_block_ratio": ratio(agc_blocks, blocks_scored),
        "mean_agc_score": safe_mean(agc_scores),
        "median_agc_score": safe_median(agc_scores),
        "cache_hits": sum(int(row["cache_hit"]) for row in file_rows),
        "failure_count": failure_count,
    }


def commit_part_dir(output_root: Path, snapshot: SnapshotCommit) -> Path:
    return (
        output_root
        / "parts"
        / snapshot.dataset_source
        / snapshot.repo_slug
        / snapshot.commit
    )


def checkpoint_matches_fingerprint(
    part_dir: Path,
    expected_fingerprint: Dict[str, Any],
) -> bool:
    metadata_path = part_dir / "snapshot_metadata.json"
    if not metadata_path.is_file():
        return False
    try:
        metadata = load_json(metadata_path)
    except Exception:
        return False
    return metadata.get("model_fingerprint") == expected_fingerprint


def process_commit(
    snapshot: SnapshotCommit,
    args: argparse.Namespace,
    context: DetectorContext,
    model_fingerprint: Dict[str, Any],
) -> Dict[str, Any]:
    part_dir = commit_part_dir(args.output_root, snapshot)
    success_marker = part_dir / "_SUCCESS"

    if success_marker.is_file() and not args.no_resume:
        if checkpoint_matches_fingerprint(part_dir, model_fingerprint):
            summary_path = part_dir / "snapshot_summary.csv"
            with summary_path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle))
            if len(rows) != 1:
                raise RuntimeError(f"invalid checkpoint summary: {summary_path}")
            print(
                f"[resume] {snapshot.dataset_source} "
                f"{snapshot.repo_slug} {snapshot.commit}"
            )
            return rows[0]
        print(
            f"[stale checkpoint] {snapshot.dataset_source} "
            f"{snapshot.repo_slug} {snapshot.commit}; reprocessing"
        )

    metadata = load_json(snapshot.snapshot_json)
    files_jsonl = snapshot.commit_dir / "_files.jsonl"
    require_path(files_jsonl, "file")
    manifest_rows = load_jsonl(files_jsonl)
    repo_name = validate_snapshot_metadata(
        snapshot,
        metadata,
        manifest_rows,
    )

    if args.max_files_per_commit is not None:
        regular_seen = 0
        limited_rows: List[Dict[str, Any]] = []
        for row in manifest_rows:
            if str(row.get("file_type", "")) == "file":
                if regular_seen >= args.max_files_per_commit:
                    continue
                regular_seen += 1
            limited_rows.append(row)
        manifest_rows = limited_rows

    print(
        f"[commit] source={snapshot.dataset_source} repo={repo_name} "
        f"commit={snapshot.commit} files={len(manifest_rows)}"
    )

    cache_root = args.output_root / "cache"
    all_blocks: List[Dict[str, Any]] = []
    all_files: List[Dict[str, Any]] = []

    for file_index, manifest_row in enumerate(manifest_rows, start=1):
        relative_path = str(manifest_row.get("relative_path", ""))
        print(f"  [{file_index}/{len(manifest_rows)}] {relative_path}")
        block_rows, file_row = analyze_manifest_file(
            snapshot=snapshot,
            repo_name=repo_name,
            manifest_row=manifest_row,
            context=context,
            cache_root=cache_root,
            model_fingerprint=model_fingerprint,
            verify_hashes=args.verify_hashes,
            use_cache=not args.no_cache,
        )
        all_blocks.extend(block_rows)
        all_files.append(file_row)

    summary = summarize_commit(
        snapshot,
        repo_name,
        manifest_rows,
        all_blocks,
        all_files,
    )

    temp_part_dir = part_dir.with_name(part_dir.name + ".tmp")
    if temp_part_dir.exists():
        shutil.rmtree(temp_part_dir)
    temp_part_dir.mkdir(parents=True, exist_ok=True)

    atomic_write_csv(
        temp_part_dir / "block_predictions.csv",
        all_blocks,
        BLOCK_FIELDS,
    )
    atomic_write_csv(
        temp_part_dir / "file_summary.csv",
        all_files,
        FILE_FIELDS,
    )
    atomic_write_csv(
        temp_part_dir / "snapshot_summary.csv",
        [summary],
        SNAPSHOT_FIELDS,
    )
    atomic_write_json(
        temp_part_dir / "snapshot_metadata.json",
        {
            "snapshot": metadata,
            "files_manifest_path": str(files_jsonl),
            "model_fingerprint": model_fingerprint,
            "completed_at_utc": utc_now(),
        },
    )
    (temp_part_dir / "_SUCCESS").write_text(
        utc_now() + "\n",
        encoding="utf-8",
    )

    if part_dir.exists():
        shutil.rmtree(part_dir)
    os.replace(temp_part_dir, part_dir)
    return summary


def iter_success_part_dirs(
    output_root: Path,
    sources: Sequence[str],
) -> Iterable[Path]:
    for source in sources:
        source_root = output_root / "parts" / source
        if not source_root.is_dir():
            continue
        for success in sorted(source_root.glob("*/*/_SUCCESS")):
            yield success.parent


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def combine_commit_parts(
    output_root: Path,
    dataset_source: str,
) -> Tuple[Path, Path, Path, List[Dict[str, Any]]]:
    sources = selected_sources(dataset_source)
    block_rows: List[Dict[str, Any]] = []
    file_rows: List[Dict[str, Any]] = []
    snapshot_rows: List[Dict[str, Any]] = []

    for part_dir in iter_success_part_dirs(output_root, sources):
        block_rows.extend(
            read_csv_rows(part_dir / "block_predictions.csv")
        )
        file_rows.extend(
            read_csv_rows(part_dir / "file_summary.csv")
        )
        snapshot_rows.extend(
            read_csv_rows(part_dir / "snapshot_summary.csv")
        )

    suffix = dataset_source
    block_path = output_root / f"block_predictions_{suffix}.csv"
    file_path = output_root / f"file_summary_{suffix}.csv"
    snapshot_path = output_root / f"snapshot_summary_{suffix}.csv"

    atomic_write_csv(block_path, block_rows, BLOCK_FIELDS)
    atomic_write_csv(file_path, file_rows, FILE_FIELDS)
    atomic_write_csv(snapshot_path, snapshot_rows, SNAPSHOT_FIELDS)
    return block_path, file_path, snapshot_path, snapshot_rows


def build_repo_month_panel(
    manifest_path: Path,
    snapshot_rows: Sequence[Dict[str, Any]],
    dataset_source: str,
    output_path: Path,
) -> Tuple[int, int]:
    summary_by_key: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for row in snapshot_rows:
        key = (
            str(row["dataset_source"]),
            str(row["repo_name"]),
            str(row["commit"]),
        )
        summary_by_key[key] = row

    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        manifest_fields = reader.fieldnames or []
        required = {
            "dataset_source",
            "repo_name",
            "month",
            "latest_commit",
        }
        missing = sorted(required - set(manifest_fields))
        if missing:
            raise ValueError(
                f"repo-month manifest missing columns {missing}: {manifest_path}"
            )
        manifest_rows = [
            row
            for row in reader
            if str(row["dataset_source"])
            in selected_sources(dataset_source)
        ]

    added_fields = [
        "analysis_status",
        "blocks_scored",
        "human_blocks",
        "agc_blocks",
        "agc_block_ratio",
        "mean_agc_score",
        "median_agc_score",
        "regular_files_expected",
        "files_analyzed",
        "files_with_blocks",
        "files_without_blocks",
        "cache_hits",
        "failure_count",
    ]
    output_fields = list(manifest_fields) + [
        field
        for field in added_fields
        if field not in manifest_fields
    ]

    panel_rows: List[Dict[str, Any]] = []
    matched = 0
    seen_repo_month: set[Tuple[str, str, str]] = set()
    duplicate_repo_month = 0

    for manifest_row in manifest_rows:
        repo_month_key = (
            str(manifest_row["dataset_source"]),
            str(manifest_row["repo_name"]),
            str(manifest_row["month"]),
        )
        if repo_month_key in seen_repo_month:
            duplicate_repo_month += 1
        seen_repo_month.add(repo_month_key)

        summary_key = (
            str(manifest_row["dataset_source"]),
            str(manifest_row["repo_name"]),
            str(manifest_row["latest_commit"]),
        )
        summary = summary_by_key.get(summary_key)
        if summary is None:
            merged = {
                **manifest_row,
                "analysis_status": "missing_snapshot_analysis",
                **{
                    field: ""
                    for field in added_fields
                    if field != "analysis_status"
                },
            }
        else:
            matched += 1
            merged = {
                **manifest_row,
                "analysis_status": "ok",
                **{
                    field: summary.get(field, "")
                    for field in added_fields
                    if field != "analysis_status"
                },
            }
        panel_rows.append(merged)

    atomic_write_csv(output_path, panel_rows, output_fields)
    if duplicate_repo_month:
        print(
            f"[WARN] duplicate repo-month rows in manifest: "
            f"{duplicate_repo_month}"
        )
    return matched, len(panel_rows)


def initialize_detector(args: argparse.Namespace) -> DetectorContext:
    # build_feature_vector() calls embed_text() in agc_detector.py, which reads
    # agc_detector.MAX_LEN from its own module globals.
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


def normalize_label(value: Any) -> int:
    text = str(value).strip().lower()
    if text in {"1", "1.0", "human", "hwc"}:
        return 1
    if text in {"0", "0.0", "lm", "ai", "agc"}:
        return 0
    raise ValueError(f"unsupported label: {value!r}")


def validate_detector_against_test_csv(
    args: argparse.Namespace,
    context: DetectorContext,
) -> Path:
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

    assert args.validation_test_csv is not None
    validation_dir = args.output_root / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = validation_dir / "validation_predictions.csv"
    metrics_path = validation_dir / "validation_metrics.csv"
    summary_path = validation_dir / "validation_summary.txt"

    with args.validation_test_csv.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        label_column = (
            "actual label"
            if "actual label" in fields
            else "label"
            if "label" in fields
            else None
        )
        required = {"idx", "code"}
        missing = sorted(required - set(fields))
        if missing or label_column is None:
            raise SystemExit(
                "[ERROR] validation CSV must contain idx, code, and "
                "actual label or label"
            )
        input_rows = list(reader)

    if len(input_rows) != args.expected_test_rows:
        raise SystemExit(
            f"[ERROR] expected {args.expected_test_rows} validation rows, "
            f"found {len(input_rows)}"
        )

    prediction_rows: List[Dict[str, Any]] = []
    for row_number, row in enumerate(input_rows, start=1):
        source = str(row["code"])
        blocks = extract_blocks(source, context.parser)
        if len(blocks) != 1:
            raise SystemExit(
                f"[ERROR] validation row {row_number} ({row['idx']}) must "
                f"contain exactly one top-level block; found {len(blocks)}"
            )

        block = blocks[0]
        vector = build_feature_vector(
            block["code"],
            context.representation,
            context.parser,
            context.ast_function,
            context.tokenizer,
            context.embedding_model,
            context.device,
        )
        pred_int, human_score_raw, score_mode = predict_one(
            context.classifier,
            vector,
            context.threshold,
        )
        if score_mode != context.expected_score_mode:
            raise SystemExit(
                f"[ERROR] validation score mode mismatch at row {row_number}: "
                f"actual={score_mode} expected={context.expected_score_mode}"
            )

        human_score = float(human_score_raw)
        prediction_rows.append(
            {
                "idx": str(row["idx"]),
                "actual_label": normalize_label(row[label_column]),
                "pred": int(pred_int),
                "human_score": human_score,
                "agc_score": human_score_to_agc_score(
                    human_score,
                    score_mode,
                ),
                "score_mode": score_mode,
            }
        )

        if row_number % 100 == 0 or row_number == len(input_rows):
            print(
                f"[validation] {row_number}/{len(input_rows)} rows scored"
            )

    y_true = [int(row["actual_label"]) for row in prediction_rows]
    y_pred = [int(row["pred"]) for row in prediction_rows]
    human_scores = [float(row["human_score"]) for row in prediction_rows]

    human_f1 = f1_score(
        y_true,
        y_pred,
        pos_label=1,
        zero_division=0,
    )
    ai_f1 = f1_score(
        y_true,
        y_pred,
        pos_label=0,
        zero_division=0,
    )
    metrics = {
        "n_test": len(prediction_rows),
        "acc": accuracy_score(y_true, y_pred),
        "human_f1": human_f1,
        "ai_f1": ai_f1,
        "avg_f1": (human_f1 + ai_f1) / 2,
        "auroc": roc_auc_score(y_true, human_scores),
    }
    expected = {
        "acc": float(args.expected_acc),
        "human_f1": float(args.expected_human_f1),
        "ai_f1": float(args.expected_ai_f1),
        "avg_f1": float(args.expected_avg_f1),
        "auroc": float(args.expected_auroc),
    }

    metric_match = all(
        round(float(metrics[name]), 4) == round(expected[name], 4)
        for name in expected
    )
    score_modes = sorted(
        {str(row["score_mode"]) for row in prediction_rows}
    )
    mode_match = score_modes == [context.expected_score_mode]
    passed = (
        metrics["n_test"] == args.expected_test_rows
        and metric_match
        and mode_match
    )

    atomic_write_csv(
        predictions_path,
        prediction_rows,
        VALIDATION_FIELDS,
    )
    atomic_write_csv(
        metrics_path,
        [metrics],
        [
            "n_test",
            "acc",
            "human_f1",
            "ai_f1",
            "avg_f1",
            "auroc",
        ],
    )

    title = (
        f"{args.experiment} {args.classifier.upper()} + "
        f"{args.representation.upper()} validation"
    )
    summary_lines = [
        title,
        "=" * len(title),
        f"Test rows : {metrics['n_test']}",
        f"ACC       : {metrics['acc']:.4f}  expected {expected['acc']:.4f}",
        (
            f"Human F1  : {metrics['human_f1']:.4f}  "
            f"expected {expected['human_f1']:.4f}"
        ),
        (
            f"AI F1     : {metrics['ai_f1']:.4f}  "
            f"expected {expected['ai_f1']:.4f}"
        ),
        (
            f"Avg. F1   : {metrics['avg_f1']:.4f}  "
            f"expected {expected['avg_f1']:.4f}"
        ),
        (
            f"AUROC     : {metrics['auroc']:.4f}  "
            f"expected {expected['auroc']:.4f}"
        ),
        f"Score mode: {','.join(score_modes)}",
        f"Status    : {'PASS' if passed else 'FAIL'}",
    ]
    summary_path.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print()
    print("\n".join(summary_lines))
    print(f"Predictions: {predictions_path}")
    print(f"Metrics    : {metrics_path}")
    print(f"Summary    : {summary_path}")

    if not passed:
        raise SystemExit(1)
    return summary_path


def write_run_metadata(
    args: argparse.Namespace,
    context: DetectorContext,
    discovered_commits: int,
    selected_commits: int,
) -> Path:
    suffix = args.dataset_source
    path = args.output_root / f"run_metadata_{suffix}.json"
    atomic_write_json(
        path,
        {
            "script": str(SCRIPT_PATH),
            "started_at_utc": utc_now(),
            "repo_root": str(REPO_ROOT),
            "snapshot_root": str(args.snapshot_root),
            "dataset_source": args.dataset_source,
            "repo_month_manifest": str(args.repo_month_manifest),
            "output_root": str(args.output_root),
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
            "verify_hashes": args.verify_hashes,
            "resume": not args.no_resume,
            "cache": not args.no_cache,
            "max_commits": args.max_commits,
            "max_files_per_commit": args.max_files_per_commit,
            "discovered_commits": discovered_commits,
            "selected_commits": selected_commits,
            "python": sys.version,
            "platform": platform.platform(),
        },
    )
    return path


def write_qc_summary(
    args: argparse.Namespace,
    snapshot_rows: Sequence[Dict[str, Any]],
    repo_month_match: Optional[Tuple[int, int]],
) -> Path:
    def sum_int(field: str) -> int:
        total = 0
        for row in snapshot_rows:
            value = row.get(field, 0)
            try:
                total += int(value)
            except (TypeError, ValueError):
                pass
        return total

    payload: Dict[str, Any] = {
        "experiment": args.experiment,
        "classifier": args.classifier,
        "representation": args.representation,
        "dataset_source": args.dataset_source,
        "snapshot_rows": len(snapshot_rows),
        "regular_files_expected": sum_int("regular_files_expected"),
        "files_analyzed": sum_int("files_analyzed"),
        "blocks_scored": sum_int("blocks_scored"),
        "human_blocks": sum_int("human_blocks"),
        "agc_blocks": sum_int("agc_blocks"),
        "cache_hits": sum_int("cache_hits"),
        "failure_count": sum_int("failure_count"),
        "completed_at_utc": utc_now(),
    }
    if repo_month_match is not None:
        payload["repo_month_rows_matched"] = repo_month_match[0]
        payload["repo_month_rows_total"] = repo_month_match[1]
    path = args.output_root / f"qc_summary_{args.dataset_source}.json"
    atomic_write_json(path, payload)
    return path


def print_configuration(args: argparse.Namespace) -> None:
    print("=" * 72)
    print("analyze_did_python_snapshots.py")
    print(f"  experiment          : {args.experiment}")
    print(f"  classifier          : {args.classifier}")
    print(f"  representation      : {args.representation}")
    print(f"  model pickle        : {args.model_pickle}")
    print(f"  expected model key  : {args.expected_model_key}")
    print(f"  expected score mode : {args.expected_score_mode}")
    print(f"  max len             : {args.max_len}")
    print(
        f"  threshold           : "
        f"{args.threshold if args.threshold is not None else '<classifier default>'}"
    )
    print(f"  dataset source      : {args.dataset_source}")
    print(f"  output root         : {args.output_root}")
    if args.validation_test_csv is not None:
        print(f"  validation test CSV : {args.validation_test_csv}")
        print(f"  validation only     : {args.validation_only}")
    if not args.validation_only:
        print(f"  snapshot root       : {args.snapshot_root}")
    print("=" * 72)


def main() -> None:
    args = parse_args()
    validate_args(args)
    args.output_root.mkdir(parents=True, exist_ok=True)
    print_configuration(args)

    context = initialize_detector(args)

    if args.validation_test_csv is not None:
        validate_detector_against_test_csv(args, context)
        if args.validation_only:
            print("Validation completed successfully; snapshot analysis skipped.")
            return

    commits = discover_snapshot_commits(
        args.snapshot_root,
        args.dataset_source,
    )
    discovered_count = len(commits)
    if args.max_commits is not None:
        commits = commits[: args.max_commits]
    if not commits:
        raise SystemExit("[ERROR] no snapshot commits discovered")

    print(f"  commits discovered  : {discovered_count}")
    print(f"  commits selected    : {len(commits)}")

    model_fingerprint = build_model_fingerprint(context)
    metadata_path = write_run_metadata(
        args,
        context,
        discovered_commits=discovered_count,
        selected_commits=len(commits),
    )

    for commit_index, snapshot in enumerate(commits, start=1):
        print()
        print(f"=== Commit {commit_index}/{len(commits)} ===")
        process_commit(
            snapshot,
            args,
            context,
            model_fingerprint,
        )

    block_path, file_path, snapshot_path, snapshot_rows = combine_commit_parts(
        args.output_root,
        args.dataset_source,
    )

    repo_month_match: Optional[Tuple[int, int]] = None
    repo_month_path: Optional[Path] = None
    if not args.skip_repo_month_panel:
        repo_month_path = (
            args.output_root
            / f"repo_month_agc_panel_{args.dataset_source}.csv"
        )
        repo_month_match = build_repo_month_panel(
            args.repo_month_manifest,
            snapshot_rows,
            args.dataset_source,
            repo_month_path,
        )

    qc_path = write_qc_summary(
        args,
        snapshot_rows,
        repo_month_match,
    )

    print()
    print("=" * 72)
    print("Completed")
    print(f"  block predictions   : {block_path}")
    print(f"  file summary        : {file_path}")
    print(f"  snapshot summary    : {snapshot_path}")
    if repo_month_path is not None:
        print(f"  repo-month panel    : {repo_month_path}")
    print(f"  run metadata        : {metadata_path}")
    print(f"  QC summary          : {qc_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
