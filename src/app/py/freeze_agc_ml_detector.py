#!/usr/bin/env python3
"""
Freeze and audit the CodeLlama-7B SVM+AST AGC detector after ground-truth validation.

This script does not run embeddings or classifier inference. The existing validated
`analyze_did_python_snapshots.py` program performs the labeled 900-row validation.
This script independently audits those validation artifacts and writes a compact,
versioned detector-freeze record for the run-x-a01 experiment.

Inputs
------
- validation_predictions.csv produced by analyze_did_python_snapshots.py
- validation_metrics.csv produced by analyze_did_python_snapshots.py
- validation_summary.txt produced by analyze_did_python_snapshots.py
- Frozen SVM pickle used by validation
- Complexity-balanced CodeLlama-7B held-out test CSV
- Existing analyzer Python script used for validation

Outputs
-------
- detector_freeze_checks.csv
- detector_freeze_summary.json
- detector_freeze_metadata.json

The frozen function-level decision rule is the native SVM boundary:
    human decision score >= 0  -> HWC
    human decision score < 0   -> AGC
For downstream analysis, an AGC-oriented continuous score is retained as:
    agc_score = -human_decision_score

The downstream file-composition rule is prespecified but is not applied by A01:
    file_ml_agc_share_space_by_token_weighted > 0.5
where the weights are the same function-body literal-space-token coordinate used
for the NPR-side function-occurrence aggregation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

SCRIPT_VERSION = "run-x-a01-v2"
DETECTOR_NAME = "codellama-7b_svm_ast"
EMBEDDING_MODEL_ID = "Salesforce/codet5p-110m-embedding"
EXPECTED_CLASSIFIER = "svm"
EXPECTED_REPRESENTATION = "ast"
EXPECTED_SCORE_MODE = "decision"
EXPECTED_THRESHOLD = 0.0
EXPECTED_TEST_ROWS = 900
EXPECTED_HUMAN_ROWS = 450
EXPECTED_AGC_ROWS = 450
DEFAULT_EXPECTED_METRICS = {
    "acc": 0.7178,
    "human_f1": 0.7221,
    "ai_f1": 0.7133,
    "avg_f1": 0.7177,
    "auroc": 0.7950,
}

CHECK_FIELDS = ["check_name", "severity", "passed", "observed", "expected"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def atomic_write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHECK_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    tmp.replace(path)


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise SystemExit(f"[ERROR] {label} not found: {path}")


def parse_float(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"[ERROR] invalid float for {label}: {value!r}") from exc
    if not math.isfinite(result):
        raise SystemExit(f"[ERROR] non-finite value for {label}: {value!r}")
    return result


def add_check(
    checks: List[Dict[str, Any]],
    name: str,
    passed: bool,
    observed: Any,
    expected: Any,
    severity: str = "hard",
) -> None:
    checks.append(
        {
            "check_name": name,
            "severity": severity,
            "passed": "1" if passed else "0",
            "observed": observed,
            "expected": expected,
        }
    )


def audit(args: argparse.Namespace) -> int:
    required = {
        "validation predictions": args.validation_predictions,
        "validation metrics": args.validation_metrics,
        "validation summary": args.validation_summary,
        "model pickle": args.model_pickle,
        "test CSV": args.test_csv,
        "analyzer script": args.analyzer_script,
    }
    for label, path in required.items():
        require_file(path, label)

    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

    predictions = read_csv_rows(args.validation_predictions)
    metrics_rows = read_csv_rows(args.validation_metrics)
    summary_text = args.validation_summary.read_text(encoding="utf-8")

    checks: List[Dict[str, Any]] = []

    add_check(checks, "validation_row_count", len(predictions) == args.expected_test_rows, len(predictions), args.expected_test_rows)
    add_check(checks, "metrics_single_row", len(metrics_rows) == 1, len(metrics_rows), 1)

    required_prediction_columns = {
        "idx",
        "actual_label",
        "pred",
        "human_score",
        "agc_score",
        "score_mode",
    }
    observed_prediction_columns = set(predictions[0].keys()) if predictions else set()
    missing_prediction_columns = sorted(required_prediction_columns - observed_prediction_columns)
    add_check(
        checks,
        "validation_prediction_schema",
        not missing_prediction_columns,
        ";".join(sorted(observed_prediction_columns)),
        "contains:" + ";".join(sorted(required_prediction_columns)),
    )

    ids = [row.get("idx", "") for row in predictions]
    add_check(checks, "validation_idx_unique", len(set(ids)) == len(ids), len(set(ids)), len(ids))

    labels: List[int] = []
    preds: List[int] = []
    score_modes = set()
    human_scores_for_metrics: List[float] = []
    score_transform_failures = 0
    boundary_failures = 0
    nonfinite_scores = 0

    for row in predictions:
        try:
            label = int(row["actual_label"])
            pred = int(row["pred"])
        except (KeyError, TypeError, ValueError):
            label = -1
            pred = -1
        labels.append(label)
        preds.append(pred)
        score_modes.add(str(row.get("score_mode", "")))

        try:
            human_score = float(row["human_score"])
            agc_score = float(row["agc_score"])
        except (KeyError, TypeError, ValueError):
            nonfinite_scores += 1
            continue
        if not math.isfinite(human_score) or not math.isfinite(agc_score):
            nonfinite_scores += 1
            continue
        human_scores_for_metrics.append(human_score)
        if not math.isclose(agc_score, -human_score, rel_tol=0.0, abs_tol=1e-12):
            score_transform_failures += 1
        expected_pred = 1 if human_score >= EXPECTED_THRESHOLD else 0
        if pred != expected_pred:
            boundary_failures += 1

    human_rows = sum(label == 1 for label in labels)
    agc_rows = sum(label == 0 for label in labels)
    invalid_labels = sum(label not in {0, 1} for label in labels)
    invalid_preds = sum(pred not in {0, 1} for pred in preds)

    add_check(checks, "ground_truth_human_rows", human_rows == args.expected_human_rows, human_rows, args.expected_human_rows)
    add_check(checks, "ground_truth_agc_rows", agc_rows == args.expected_agc_rows, agc_rows, args.expected_agc_rows)
    add_check(checks, "ground_truth_labels_binary", invalid_labels == 0, invalid_labels, 0)
    add_check(checks, "predictions_binary", invalid_preds == 0, invalid_preds, 0)
    add_check(checks, "score_mode_decision", score_modes == {EXPECTED_SCORE_MODE}, ";".join(sorted(score_modes)), EXPECTED_SCORE_MODE)
    add_check(checks, "decision_scores_finite", nonfinite_scores == 0, nonfinite_scores, 0)
    add_check(checks, "agc_score_is_negative_human_score", score_transform_failures == 0, score_transform_failures, 0)
    add_check(checks, "native_svm_boundary_zero", boundary_failures == 0, boundary_failures, 0)

    expected_metrics = {
        "acc": float(args.expected_acc),
        "human_f1": float(args.expected_human_f1),
        "ai_f1": float(args.expected_ai_f1),
        "avg_f1": float(args.expected_avg_f1),
        "auroc": float(args.expected_auroc),
    }

    recomputed_metrics: Dict[str, float] = {}
    if invalid_labels == 0 and invalid_preds == 0 and nonfinite_scores == 0 and len(human_scores_for_metrics) == len(predictions):
        human_f1 = f1_score(labels, preds, pos_label=1, zero_division=0)
        ai_f1 = f1_score(labels, preds, pos_label=0, zero_division=0)
        recomputed_metrics = {
            "acc": float(accuracy_score(labels, preds)),
            "human_f1": float(human_f1),
            "ai_f1": float(ai_f1),
            "avg_f1": float((human_f1 + ai_f1) / 2.0),
            "auroc": float(roc_auc_score(labels, human_scores_for_metrics)),
        }

    metric_values: Dict[str, float] = {}
    if metrics_rows:
        metrics_row = metrics_rows[0]
        try:
            metric_n_test = int(float(metrics_row.get("n_test", "nan")))
        except ValueError:
            metric_n_test = -1
        add_check(checks, "metrics_test_rows", metric_n_test == args.expected_test_rows, metric_n_test, args.expected_test_rows)
        for name, expected in expected_metrics.items():
            actual = parse_float(metrics_row.get(name), name)
            metric_values[name] = actual
            passed = round(actual, 4) == round(expected, 4)
            add_check(checks, f"metric_{name}_matches_reference", passed, f"{actual:.8f}", f"{expected:.4f}")
            recomputed = recomputed_metrics.get(name, float("nan"))
            add_check(
                checks,
                f"metric_{name}_recomputed_matches_output",
                math.isfinite(recomputed) and math.isclose(recomputed, actual, rel_tol=0.0, abs_tol=1e-12),
                f"{recomputed:.12f}" if math.isfinite(recomputed) else "nan",
                f"{actual:.12f}",
            )
            add_check(
                checks,
                f"metric_{name}_recomputed_matches_reference",
                math.isfinite(recomputed) and round(recomputed, 4) == round(expected, 4),
                f"{recomputed:.8f}" if math.isfinite(recomputed) else "nan",
                f"{expected:.4f}",
            )

    add_check(checks, "validation_summary_pass", "Status    : PASS" in summary_text, "PASS" if "Status    : PASS" in summary_text else "not PASS", "PASS")

    failed_hard = [row for row in checks if row["severity"] == "hard" and row["passed"] != "1"]
    status = "PASS" if not failed_hard else "FAIL"

    args.output_root.mkdir(parents=True, exist_ok=True)
    checks_path = args.output_root / "detector_freeze_checks.csv"
    summary_path = args.output_root / "detector_freeze_summary.json"
    metadata_path = args.output_root / "detector_freeze_metadata.json"

    frozen_spec = {
        "detector_name": DETECTOR_NAME,
        "generation_source": "CodeLlama-7B",
        "classifier": EXPECTED_CLASSIFIER,
        "representation": EXPECTED_REPRESENTATION,
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "max_len": args.max_len,
        "score_mode": EXPECTED_SCORE_MODE,
        "label_convention": {"human": 1, "agc": 0},
        "human_decision_threshold": EXPECTED_THRESHOLD,
        "agc_score_transform": "agc_score=-human_decision_score",
        "function_prediction_rule": "agc if human_decision_score < 0 else human",
        "selection_policy": "preselected_before_downstream_github_quality_outcomes",
        "downstream_equality_contract": [
            "same_repository",
            "same_repo_month",
            "same_historical_commit",
            "same_python_file",
            "same_function_occurrence_identity_when_available",
        ],
        "downstream_function_input_contract": {
            "npr": "function_body",
            "ml": "full_standalone_function_source_to_ast_to_codet5plus_to_svm",
        },
        "prespecified_file_aggregation": {
            "weight": "function_body_literal_space_token_count",
            "metric": "file_ml_agc_share_space_by_token_weighted",
            "selection_rule": "file_ml_agc_share_space_by_token_weighted > 0.5",
            "unscored_function_policy": "exclude_from_denominator",
            "no_scored_function_file_policy": "NA_no_ml_fun_not_HWC",
        },
    }

    summary_payload = {
        "run": SCRIPT_VERSION,
        "status": status,
        "failed_hard_checks": len(failed_hard),
        "hard_checks": sum(row["severity"] == "hard" for row in checks),
        "validation_rows": len(predictions),
        "human_rows": human_rows,
        "agc_rows": agc_rows,
        "metrics": metric_values,
        "reference_metrics": expected_metrics,
        "recomputed_metrics": recomputed_metrics,
        "frozen_detector_spec": frozen_spec,
        "created_at_utc": utc_now(),
    }

    metadata_payload = {
        "run": SCRIPT_VERSION,
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "python": sys.version,
        "platform": platform.platform(),
        "inputs": {
            "validation_predictions": str(args.validation_predictions),
            "validation_predictions_sha256": sha256_file(args.validation_predictions),
            "validation_metrics": str(args.validation_metrics),
            "validation_metrics_sha256": sha256_file(args.validation_metrics),
            "validation_summary": str(args.validation_summary),
            "validation_summary_sha256": sha256_file(args.validation_summary),
            "model_pickle": str(args.model_pickle),
            "model_pickle_sha256": sha256_file(args.model_pickle),
            "test_csv": str(args.test_csv),
            "test_csv_sha256": sha256_file(args.test_csv),
            "analyzer_script": str(args.analyzer_script),
            "analyzer_script_sha256": sha256_file(args.analyzer_script),
        },
        "expected_model_key": args.expected_model_key,
        "frozen_detector_spec": frozen_spec,
        "created_at_utc": utc_now(),
    }

    atomic_write_csv(checks_path, checks)
    atomic_write_json(summary_path, summary_payload)
    atomic_write_json(metadata_path, metadata_payload)

    print("=" * 78)
    print("run-x-a01 detector freeze audit")
    print(f"Status:                         {status}")
    print(f"Validation rows:                {len(predictions)}")
    print(f"Human / AGC rows:               {human_rows} / {agc_rows}")
    if metric_values:
        print(f"ACC:                            {metric_values.get('acc', float('nan')):.4f}")
        print(f"Human F1:                       {metric_values.get('human_f1', float('nan')):.4f}")
        print(f"AGC F1:                         {metric_values.get('ai_f1', float('nan')):.4f}")
        print(f"Avg. F1:                        {metric_values.get('avg_f1', float('nan')):.4f}")
        print(f"AUROC:                          {metric_values.get('auroc', float('nan')):.4f}")
    print(f"Function decision boundary:     {EXPECTED_THRESHOLD:.1f} (native SVM)")
    print("AGC score orientation:          -human_decision_score")
    print("Prespecified file rule:         weighted AGC share > 0.5")
    print(f"Failed hard checks:              {len(failed_hard)}")
    print(f"Checks:                          {checks_path}")
    print(f"Summary:                         {summary_path}")
    print(f"Metadata:                        {metadata_path}")
    print("=" * 78)

    return 0 if status == "PASS" else 1



def verify_output(args: argparse.Namespace) -> int:
    """Verify frozen A01 artifacts without re-running detector inference."""
    output_root = args.output_root.expanduser().resolve()
    checks_path = output_root / "detector_freeze_checks.csv"
    summary_path = output_root / "detector_freeze_summary.json"
    metadata_path = output_root / "detector_freeze_metadata.json"

    for path, label in (
        (checks_path, "detector freeze checks"),
        (summary_path, "detector freeze summary"),
        (metadata_path, "detector freeze metadata"),
    ):
        require_file(path, label)

    checks = read_csv_rows(checks_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    failures: List[str] = []

    status = str(summary.get("status", ""))
    failed_hard_checks = int(summary.get("failed_hard_checks", -1))
    if status != "PASS":
        failures.append(f"summary status is {status!r}, expected 'PASS'")
    if failed_hard_checks != 0:
        failures.append(
            f"summary failed_hard_checks={failed_hard_checks}, expected 0"
        )

    hard_rows = [row for row in checks if row.get("severity") == "hard"]
    failed_rows = [row for row in hard_rows if row.get("passed") != "1"]
    if failed_rows:
        sample = ", ".join(row.get("check_name", "<unnamed>") for row in failed_rows[:10])
        failures.append(f"{len(failed_rows)} hard checks failed: {sample}")

    expected_counts = {
        "validation_rows": args.expected_test_rows,
        "human_rows": args.expected_human_rows,
        "agc_rows": args.expected_agc_rows,
    }
    for field, expected in expected_counts.items():
        try:
            observed = int(summary.get(field, -1))
        except (TypeError, ValueError):
            observed = -1
        if observed != expected:
            failures.append(f"{field}={observed}, expected {expected}")

    expected_metrics = {
        "acc": float(args.expected_acc),
        "human_f1": float(args.expected_human_f1),
        "ai_f1": float(args.expected_ai_f1),
        "avg_f1": float(args.expected_avg_f1),
        "auroc": float(args.expected_auroc),
    }
    observed_metrics = summary.get("metrics", {})
    for name, expected in expected_metrics.items():
        try:
            observed = float(observed_metrics.get(name, "nan"))
        except (TypeError, ValueError):
            observed = float("nan")
        if not math.isfinite(observed) or round(observed, 4) != round(expected, 4):
            failures.append(
                f"metric {name}={observed!r}, expected {expected:.4f} at four decimals"
            )

    frozen = summary.get("frozen_detector_spec", {})
    expected_spec = {
        "detector_name": DETECTOR_NAME,
        "classifier": EXPECTED_CLASSIFIER,
        "representation": EXPECTED_REPRESENTATION,
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "score_mode": EXPECTED_SCORE_MODE,
        "human_decision_threshold": EXPECTED_THRESHOLD,
    }
    for field, expected in expected_spec.items():
        observed = frozen.get(field)
        if observed != expected:
            failures.append(f"frozen detector {field}={observed!r}, expected {expected!r}")

    aggregation = frozen.get("prespecified_file_aggregation", {})
    expected_aggregation = {
        "weight": "function_body_literal_space_token_count",
        "metric": "file_ml_agc_share_space_by_token_weighted",
        "selection_rule": "file_ml_agc_share_space_by_token_weighted > 0.5",
        "unscored_function_policy": "exclude_from_denominator",
        "no_scored_function_file_policy": "NA_no_ml_fun_not_HWC",
    }
    for field, expected in expected_aggregation.items():
        observed = aggregation.get(field)
        if observed != expected:
            failures.append(
                f"file aggregation {field}={observed!r}, expected {expected!r}"
            )

    metadata_frozen = metadata.get("frozen_detector_spec", {})
    if metadata_frozen != frozen:
        failures.append("summary and metadata frozen_detector_spec differ")

    if failures:
        print("A01 output verification: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"[ERROR] {failure}", file=sys.stderr)
        return 1

    print("A01 output verification: PASS")
    print(f"Status:                    {status}")
    print(f"Validation rows:           {summary['validation_rows']}")
    print(f"Human / AGC rows:          {summary['human_rows']} / {summary['agc_rows']}")
    print(f"ACC:                       {float(observed_metrics['acc']):.4f}")
    print(f"Avg. F1:                   {float(observed_metrics['avg_f1']):.4f}")
    print(f"AUROC:                     {float(observed_metrics['auroc']):.4f}")
    print(f"Failed hard checks:        {failed_hard_checks}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-predictions", type=Path)
    parser.add_argument("--validation-metrics", type=Path)
    parser.add_argument("--validation-summary", type=Path)
    parser.add_argument("--model-pickle", type=Path)
    parser.add_argument("--test-csv", type=Path)
    parser.add_argument("--analyzer-script", type=Path)
    parser.add_argument("--expected-model-key", required=False, default="codesearchnet_codellama-7b_python_merged_4500ast_")
    parser.add_argument("--max-len", type=int, default=2048)
    parser.add_argument("--expected-test-rows", type=int, default=EXPECTED_TEST_ROWS)
    parser.add_argument("--expected-human-rows", type=int, default=EXPECTED_HUMAN_ROWS)
    parser.add_argument("--expected-agc-rows", type=int, default=EXPECTED_AGC_ROWS)
    parser.add_argument("--expected-acc", type=float, default=DEFAULT_EXPECTED_METRICS["acc"])
    parser.add_argument("--expected-human-f1", type=float, default=DEFAULT_EXPECTED_METRICS["human_f1"])
    parser.add_argument("--expected-ai-f1", type=float, default=DEFAULT_EXPECTED_METRICS["ai_f1"])
    parser.add_argument("--expected-avg-f1", type=float, default=DEFAULT_EXPECTED_METRICS["avg_f1"])
    parser.add_argument("--expected-auroc", type=float, default=DEFAULT_EXPECTED_METRICS["auroc"])
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-output", action="store_true", help="Verify existing A01 freeze artifacts only")
    return parser


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="run-x-a01-selftest-") as tmp_dir:
        root = Path(tmp_dir)
        predictions = root / "validation_predictions.csv"
        metrics = root / "validation_metrics.csv"
        summary = root / "validation_summary.txt"
        model = root / "model.pkl"
        test_csv = root / "test.csv"
        analyzer = root / "analyzer.py"
        output = root / "out"

        with predictions.open("w", encoding="utf-8", newline="") as handle:
            fields = ["idx", "actual_label", "pred", "human_score", "agc_score", "score_mode"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for i in range(EXPECTED_TEST_ROWS):
                label = 1 if i < EXPECTED_HUMAN_ROWS else 0
                score = 1.0 if label == 1 else -1.0
                writer.writerow(
                    {
                        "idx": f"row-{i}",
                        "actual_label": label,
                        "pred": label,
                        "human_score": score,
                        "agc_score": -score,
                        "score_mode": EXPECTED_SCORE_MODE,
                    }
                )

        with metrics.open("w", encoding="utf-8", newline="") as handle:
            fields = ["n_test", "acc", "human_f1", "ai_f1", "avg_f1", "auroc"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerow({"n_test": EXPECTED_TEST_ROWS, "acc": 1.0, "human_f1": 1.0, "ai_f1": 1.0, "avg_f1": 1.0, "auroc": 1.0})

        summary.write_text("Status    : PASS\n", encoding="utf-8")
        model.write_bytes(b"synthetic-model")
        test_csv.write_text("idx,code,label\n", encoding="utf-8")
        analyzer.write_text("# synthetic analyzer\n", encoding="utf-8")

        args = argparse.Namespace(
            validation_predictions=predictions,
            validation_metrics=metrics,
            validation_summary=summary,
            model_pickle=model,
            test_csv=test_csv,
            analyzer_script=analyzer,
            expected_model_key="synthetic",
            max_len=2048,
            expected_test_rows=EXPECTED_TEST_ROWS,
            expected_human_rows=EXPECTED_HUMAN_ROWS,
            expected_agc_rows=EXPECTED_AGC_ROWS,
            expected_acc=1.0,
            expected_human_f1=1.0,
            expected_ai_f1=1.0,
            expected_avg_f1=1.0,
            expected_auroc=1.0,
            output_root=output,
        )
        rc = audit(args)
        if rc != 0:
            raise SystemExit("[ERROR] self-test audit failed")
        payload = json.loads((output / "detector_freeze_summary.json").read_text(encoding="utf-8"))
        if payload.get("status") != "PASS":
            raise SystemExit("[ERROR] self-test summary did not PASS")
        verify_args = argparse.Namespace(
            output_root=output,
            expected_test_rows=EXPECTED_TEST_ROWS,
            expected_human_rows=EXPECTED_HUMAN_ROWS,
            expected_agc_rows=EXPECTED_AGC_ROWS,
            expected_acc=1.0,
            expected_human_f1=1.0,
            expected_ai_f1=1.0,
            expected_avg_f1=1.0,
            expected_auroc=1.0,
        )
        if verify_output(verify_args) != 0:
            raise SystemExit("[ERROR] self-test output verification failed")
    print("freeze_agc_ml_detector self-test: PASS")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    if args.verify_output:
        if args.output_root is None:
            parser.error("--verify-output requires --output-root")
        return verify_output(args)

    required_args = [
        "validation_predictions",
        "validation_metrics",
        "validation_summary",
        "model_pickle",
        "test_csv",
        "analyzer_script",
        "output_root",
    ]
    missing = [name for name in required_args if getattr(args, name) is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join("--" + name.replace("_", "-") for name in missing))

    for name in required_args:
        value = getattr(args, name)
        if isinstance(value, Path):
            setattr(args, name, value.expanduser().resolve())
    return audit(args)


if __name__ == "__main__":
    raise SystemExit(main())
