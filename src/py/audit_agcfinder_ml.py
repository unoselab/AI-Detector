#!/usr/bin/env python3
"""Audit AGCFinderML baseline artifacts and reproduce saved-prediction AUROCs.

Input (read-only):
  <repo>/src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c/
    source_config_manifest.csv, target_test_manifest.csv, cell_metrics.csv,
    matrix_auroc.csv, predictions/clf-*/target-*.csv
  <repo>/src/ml_embeddings/data_codesearchnet/candidate_selection_run4d/
    point_estimates.csv
  <repo>/src/ml_embeddings/data_codesearchnet/splits/<experiment>/
    complexity_stratified_pair_manifest.csv and <dataset>/{train_,dev_,test_}.csv
  Referenced model pickle files and original CodeLlama paired dataset.

Output (new files only under --output-dir):
  artifact_inventory.csv, baseline_cells.csv, baseline_summary.csv,
  pair_split_manifest.csv, run_summary.json, findings.txt.

No models are unpickled; no original experiments or shell scripts are invoked.
Positive AUROC label is HWC=1, as in the original test_embedding.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_SOURCES = ("CL-7B", "SC2-7B", "SC2-15B", "GO-120B", "GM4-31B")
EXPECTED_PAPER = {
    "same_auroc": 0.7950,
    "transfer_auroc": 0.7319,
    "maximum_regret": 0.0887,
}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--target-source", default="CL-7B")
    p.add_argument("--expected-pairs", type=int, default=4500)
    p.add_argument("--expected-test-pairs", type=int, default=450)
    p.add_argument("--comparison-tolerance", type=float, default=1e-8)
    p.add_argument("--paper-tolerance", type=float, default=0.0001)
    p.add_argument("--hash-models", choices=("none", "selected", "all"), default="selected")
    p.add_argument("--strict-missing", action="store_true",
                   help="Fail when critical model/dataset artifacts are missing.")
    return p.parse_args()


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, records, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def sha256_file(path):
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda: f.read(8 * 1024 * 1024), b""):
            sha.update(buf)
    return sha.hexdigest()


def file_in_root(raw_path, repo_root):
    """Map authoritative absolute paths to the supplied cloned repo root."""
    text = str(raw_path).strip()
    if not text:
        return None
    value = Path(text)
    if not value.is_absolute():
        return repo_root / value
    if value.exists():
        return value
    parts = list(value.parts)
    indices = [i for i, part in enumerate(parts) if part == "ai_detector"]
    if indices:
        return repo_root.joinpath(*parts[indices[-1] + 1:])
    return value


def finite_number(value):
    n = float(value)
    if not math.isfinite(n):
        raise ValueError(f"Non-finite score: {value}")
    return n


def midrank_auroc(labels, scores):
    """Equivalent to sklearn roc_auc_score for binary, continuous scores."""
    if len(labels) != len(scores):
        raise ValueError("Mismatched score/label counts")
    n_pos = sum(v == 1 for v in labels)
    n_neg = sum(v == 0 for v in labels)
    if n_pos * n_neg == 0 or n_pos + n_neg != len(labels):
        raise ValueError("AUROC needs both binary classes")
    ordered = sorted(zip(scores, labels), key=lambda pair: pair[0])
    pos_rank_sum = 0.0
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][0] == ordered[i][0]:
            j += 1
        average_rank = (i + 1 + j) / 2.0
        pos_rank_sum += average_rank * sum(label == 1 for _, label in ordered[i:j])
        i = j
    return (pos_rank_sum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def read_prediction(path):
    labels, scores, pairs = [], [], defaultdict(set)
    idx_labels = {}
    modes = set()
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"idx", "actual label", "pred", "score", "score_mode"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing prediction columns: {required - set(reader.fieldnames or [])}")
        for row in reader:
            idx = row["idx"].strip()
            label = int(row["actual label"])
            if label not in (0, 1) or idx in idx_labels:
                raise ValueError(f"Duplicate idx or invalid label: {idx}")
            suffix = "_human" if label == 1 else "_lm"
            if not idx.endswith(suffix):
                raise ValueError(f"Unexpected pair label/suffix: {idx} label={label}")
            pair_id = idx[:-len(suffix)]
            pairs[pair_id].add(label)
            idx_labels[idx] = label
            labels.append(label)
            scores.append(finite_number(row["score"]))
            modes.add(row["score_mode"].strip())
    if any(classes != {0, 1} for classes in pairs.values()):
        raise ValueError("Every procedure pair must have HWC and AGC rows")
    if modes != {"decision"} and modes != {"proba"}:
        raise ValueError(f"Unexpected score modes: {sorted(modes)}")
    return {
        "auroc": midrank_auroc(labels, scores),
        "n_rows": len(labels),
        "n_hwc": labels.count(1),
        "n_agc": labels.count(0),
        "n_pairs": len(pairs),
        "score_mode": next(iter(modes)),
        "idx_labels": idx_labels,
    }


def count_split(path):
    rows = 0
    labels = Counter()
    pair_rows = defaultdict(set)
    idx_labels = {}
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "idx" not in (reader.fieldnames or []) or "actual label" not in (reader.fieldnames or []):
            raise ValueError(f"Split CSV missing idx/actual label: {path}")
        for row in reader:
            rows += 1
            label = int(row["actual label"])
            idx = row["idx"]
            suffix = "_human" if label == 1 else "_lm"
            if not idx.endswith(suffix):
                raise ValueError(f"Bad suffix on {idx}")
            if idx in idx_labels:
                raise ValueError(f"Duplicate split idx: {idx}")
            pair_rows[idx[:-len(suffix)]].add(label)
            idx_labels[idx] = label
            labels[label] += 1
    if any(s != {0, 1} for s in pair_rows.values()):
        raise ValueError("An HWC/AGC pair has been split or duplicated")
    return rows, len(pair_rows), labels, set(pair_rows), idx_labels


class Audit:
    def __init__(self, args):
        self.a = args
        self.root = args.repo_root.expanduser().resolve()
        self.out = args.output_dir.expanduser().resolve()
        self.ml = self.root / "src/ml_embeddings/data_codesearchnet"
        self.transfer = self.ml / "transfer_same_test_run4c"
        self.selection = self.ml / "candidate_selection_run4d"
        self.inventory = []
        self.errors = []
        self.warnings = []
        self.pass_checks = []
        self.cells = []
        self.summaries = []
        self.split_manifest_rows = []

    def warn(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def check(self, condition, text):
        (self.pass_checks if condition else self.errors).append(text)
        return condition

    def item(self, label, path, kind, expected_hash="", do_hash=False, critical=True):
        if path is None:
            return False
        exists = path.is_file()
        size = path.stat().st_size if exists else ""
        computed = ""
        status = "PRESENT" if exists else "MISSING"
        if exists and do_hash:
            computed = sha256_file(path)
            if expected_hash and computed.lower() != expected_hash.lower():
                status = "HASH_MISMATCH"
                self.error(f"SHA-256 mismatch ({label}): {path}")
            elif expected_hash:
                status = "SHA256_OK"
        if not exists:
            msg = f"Missing {kind} ({label}): {path}"
            if critical and self.a.strict_missing:
                self.error(msg)
            else:
                self.warn(msg)
        self.inventory.append({
            "label": label, "kind": kind, "path": str(path), "exists": exists,
            "bytes": size, "status": status, "expected_sha256": expected_hash,
            "actual_sha256": computed,
        })
        return exists and status != "HASH_MISMATCH"

    def audit_split_manifest(self, experiment, dataset):
        folder = self.ml / "splits" / experiment
        manifest = folder / "complexity_stratified_pair_manifest.csv"
        if not self.item("cl_pair_manifest", manifest, "split manifest"):
            return
        rows = read_csv(manifest)
        splits = Counter(row["split"] for row in rows)
        IDs = {row["pair_id"] for row in rows}
        expected = self.a.expected_pairs
        self.check(len(rows) == expected and len(IDs) == expected,
                   f"CodeLlama pair manifest: {len(rows)} unique pairs expected {expected}")
        for split, expected_n in (("train", expected * 8 // 10),
                                  ("dev", expected // 10), ("test", expected // 10)):
            self.check(splits[split] == expected_n,
                       f"CodeLlama manifest {split}: {splits[split]} expected {expected_n}")
        for row in rows:
            self.split_manifest_rows.append({
                "pair_id": row["pair_id"], "split": row["split"],
                "complexity_block": row.get("complexity_block", ""),
                "complexity_score": row.get("complexity_score", ""),
            })
        for split, expected_n in (("train", expected * 8 // 10),
                                  ("dev", expected // 10), ("test", expected // 10)):
            path = folder / dataset / f"{split}_.csv"
            if not self.item(f"cl_split_{split}", path, "split CSV"):
                continue
            try:
                nrows, npairs, labels, ids, idx_labels = count_split(path)
                self.check(npairs == expected_n and nrows == 2 * expected_n and
                           labels[0] == expected_n and labels[1] == expected_n,
                           f"CL {split} paired rows={nrows}, pairs={npairs}, labels={dict(labels)}")
                expected_ids = {r["pair_id"] for r in rows if r["split"] == split}
                self.check(ids == expected_ids, f"CL {split} IDs match pair manifest")
            except Exception as exc:
                self.error(f"Could not audit CodeLlama {split}: {exc}")

    def execute(self):
        for label, path in (
            ("source_config_manifest", self.transfer / "source_config_manifest.csv"),
            ("target_test_manifest", self.transfer / "target_test_manifest.csv"),
            ("cell_metrics", self.transfer / "cell_metrics.csv"),
            ("matrix_auroc", self.transfer / "matrix_auroc.csv"),
            ("point_estimates", self.selection / "point_estimates.csv"),
        ):
            self.item(label, path, "baseline reference")
        source_file = self.transfer / "source_config_manifest.csv"
        target_file = self.transfer / "target_test_manifest.csv"
        metrics_file = self.transfer / "cell_metrics.csv"
        matrix_file = self.transfer / "matrix_auroc.csv"
        point_file = self.selection / "point_estimates.csv"
        if not all(p.is_file() for p in (source_file, target_file, metrics_file, matrix_file, point_file)):
            self.error("Cannot reproduce the baseline: required run4c/run4d reference files missing")
            return

        src_rows = read_csv(source_file)
        target_rows = read_csv(target_file)
        metrics_rows = read_csv(metrics_file)
        matrix_rows = read_csv(matrix_file)
        points_rows = read_csv(point_file)
        sources = {r["train_source"]: r for r in src_rows}
        targets = {r["target_source"]: r for r in target_rows}
        self.check(set(sources) == set(EXPECTED_SOURCES), "Expected five train sources")
        self.check(set(targets) == set(EXPECTED_SOURCES), "Expected five target sources")
        self.check(len(metrics_rows) == 25, f"Expected 25 cross-generator cells, found {len(metrics_rows)}")

        selected = sources.get(self.a.target_source)
        if not selected:
            self.error(f"Selected training source unavailable: {self.a.target_source}")
            return

        for label, row in sources.items():
            model = file_in_root(row["model_pickle"], self.root)
            should_hash = self.a.hash_models == "all" or (self.a.hash_models == "selected" and label == self.a.target_source)
            self.item(f"model_{label}", model, "model pickle", row.get("model_sha256", ""), should_hash)

        target_signatures = {}
        for label, row in targets.items():
            test = file_in_root(row["test_csv"], self.root)
            if self.item(f"test_{label}", test, "target test CSV", row.get("test_sha256", ""), do_hash=True):
                try:
                    nrows, npairs, labels, _ids, signature = count_split(test)
                    target_signatures[label] = signature
                    self.check(nrows == int(row["rows"]) and
                               labels[1] == int(row["hwc_label1"]) and
                               labels[0] == int(row["agc_label0"]),
                               f"{label}: target test rows and labels match manifest")
                except Exception as exc:
                    self.error(f"Failed to check target test CSV {label}: {exc}")

        self.audit_split_manifest(selected["source_experiment"], selected["source_dataset"])
        original_csv = (self.root / "src/code-analyzer-tree-sitter/data_codesearchnet" /
                        selected["source_slug"] / "validsyntax_4500_complexity" /
                        f"{selected['source_dataset']}.csv")
        self.item("original_cl_4500_pairs", original_csv, "original HWC/AGC data")
        original_raw = (self.root / "src/output/CodeSearchNet/CodeLlama-7b-hf-9000-tp0.2/outputs.txt")
        self.item("original_cl_generation_jsonl", original_raw, "generation evidence", critical=False)

        matrix = {r["train_source"]: r for r in matrix_rows}
        cells_by_source = defaultdict(dict)
        signatures_by_target = {}
        for row in metrics_rows:
            source = row["train_source"]
            target = row["target_source"]
            pred = file_in_root(row["predictions_csv"], self.root)
            if not self.item(f"prediction_{source}_to_{target}", pred, "saved predictions"):
                continue
            try:
                p = read_prediction(pred)
                expected = self.a.expected_test_pairs
                self.check(p["n_pairs"] == expected and p["n_rows"] == 2 * expected and
                           p["n_hwc"] == expected and p["n_agc"] == expected,
                           f"{source}->{target}: pair count/labels verified")
                if target in target_signatures:
                    self.check(p["idx_labels"] == target_signatures[target],
                               f"{source}->{target}: predictions match source test CSV")
                if target in signatures_by_target:
                    self.check(p["idx_labels"] == signatures_by_target[target],
                               f"{source}->{target}: same target rows and labels")
                else:
                    signatures_by_target[target] = p["idx_labels"]
                expected_auc = finite_number(row["auroc"])
                self.check(abs(p["auroc"] - expected_auc) <= self.a.comparison_tolerance,
                           f"{source}->{target} AUROC vs cell_metrics.csv")
                if source in matrix:
                    self.check(abs(p["auroc"] - finite_number(matrix[source][target])) <= self.a.comparison_tolerance,
                               f"{source}->{target} AUROC vs matrix_auroc.csv")
                self.check(int(row["n_rows"]) == p["n_rows"],
                           f"{source}->{target} row count matches reference")
                cells_by_source[source][target] = p["auroc"]
                self.cells.append({"train_source": source, "target_source": target,
                                   "auroc_recomputed": f"{p['auroc']:.15f}",
                                   "auroc_reference": row["auroc"],
                                   "delta": f"{p['auroc'] - expected_auc:.15g}",
                                   "n_rows": p["n_rows"], "n_hwc": p["n_hwc"],
                                   "n_agc": p["n_agc"], "score_mode": p["score_mode"]})
            except Exception as exc:
                self.error(f"Could not reproduce {source}->{target}: {exc}")

        if set(cells_by_source) != set(EXPECTED_SOURCES) or any(
            set(cells_by_source[s]) != set(EXPECTED_SOURCES) for s in EXPECTED_SOURCES
            if s in cells_by_source
        ):
            self.error("Incomplete 5x5 prediction matrix: cannot verify transfer/regret")
            return

        diag = {s: cells_by_source[s][s] for s in EXPECTED_SOURCES}
        transfers = {s: sum(v for target, v in cells_by_source[s].items() if target != s) / 4
                     for s in EXPECTED_SOURCES}
        max_same = max(diag.values())
        max_transfer = max(transfers.values())
        points = {row["candidate"]: row for row in points_rows}
        for source in EXPECTED_SOURCES:
            regret = max(max_same - diag[source], max_transfer - transfers[source])
            self.summaries.append({"train_source": source, "same_auroc": f"{diag[source]:.15f}",
                                   "transfer_auroc": f"{transfers[source]:.15f}",
                                   "maximum_regret": f"{regret:.15f}",
                                   "is_selected": source == self.a.target_source})
            self.check(abs(transfers[source] - finite_number(matrix[source]["Transfer"])) <= self.a.comparison_tolerance,
                       f"{source}: transfer AUROC matches matrix")
            if source in points:
                for col, val in (("table1_auroc", diag[source]),
                                 ("transfer_auroc", transfers[source]),
                                 ("max_regret", regret)):
                    self.check(abs(val - finite_number(points[source][col])) <= self.a.comparison_tolerance,
                               f"{source}: {col} matches run4d point estimates")
        winner = min(self.summaries, key=lambda x: float(x["maximum_regret"]))["train_source"]
        self.check(winner == self.a.target_source, f"Minimax regret winner is {winner}")
        selected_regret = next(float(s["maximum_regret"]) for s in self.summaries
                               if s["train_source"] == self.a.target_source)
        for metric, value in (("same_auroc", diag[self.a.target_source]),
                              ("transfer_auroc", transfers[self.a.target_source]),
                              ("maximum_regret", selected_regret)):
            self.check(abs(value - EXPECTED_PAPER[metric]) <= self.a.paper_tolerance,
                       f"Paper Table II {metric}: {value:.9f} vs {EXPECTED_PAPER[metric]:.4f}")

    def save(self):
        self.out.mkdir(parents=True, exist_ok=True)
        write_csv(self.out / "artifact_inventory.csv", self.inventory,
                  ["label", "kind", "path", "exists", "bytes", "status", "expected_sha256", "actual_sha256"])
        write_csv(self.out / "baseline_cells.csv", self.cells,
                  ["train_source", "target_source", "auroc_recomputed", "auroc_reference", "delta",
                   "n_rows", "n_hwc", "n_agc", "score_mode"])
        write_csv(self.out / "baseline_summary.csv", self.summaries,
                  ["train_source", "same_auroc", "transfer_auroc", "maximum_regret", "is_selected"])
        write_csv(self.out / "pair_split_manifest.csv", self.split_manifest_rows,
                  ["pair_id", "split", "complexity_block", "complexity_score"])
        full_baseline = len(self.cells) == 25 and len(self.summaries) == 5
        selected_model_ok = any(v["label"] == f"model_{self.a.target_source}" and
                                v["status"] in ("PRESENT", "SHA256_OK") for v in self.inventory)
        status = "FAIL" if self.errors else ("PASS_WITH_WARNINGS" if self.warnings else "PASS")
        report = {
            "experiment": "run-x-01", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(self.root), "out_dir": str(self.out), "status": status,
            "prediction_baseline_reproduced": full_baseline and not self.errors,
            "selected_model_available": selected_model_ok,
            "model_inference_reexecuted": False,
            "new_agc_generated": False,
            "errors": self.errors, "warnings": self.warnings,
            "checks_passed": len(self.pass_checks), "predictions_recomputed": len(self.cells),
            "expected_paper": EXPECTED_PAPER,
        }
        (self.out / "run_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        lines = [f"Experiment: run-x-01", f"Status: {status}",
                 f"Prediction matrix: {len(self.cells)}/25", f"Selected model available: {selected_model_ok}",
                 f"Model inference rerun: NO (saved predictions only)",
                 f"Checks passed: {len(self.pass_checks)}", f"Errors: {len(self.errors)}",
                 f"Warnings: {len(self.warnings)}", ""]
        if self.summaries:
            lines.extend(["Reproduced baseline (HWC=1, AGC=0):"])
            for x in self.summaries:
                lines.append(f"  {x['train_source']}: same={float(x['same_auroc']):.6f} "
                             f"transfer={float(x['transfer_auroc']):.6f} regret={float(x['maximum_regret']):.6f}")
        for label, data in (("ERROR", self.errors), ("WARNING", self.warnings)):
            if data:
                lines.extend(["", f"{label}:"] + [f"  - {s}" for s in data])
        (self.out / "findings.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return (2 if self.errors or (self.a.strict_missing and self.warnings) else 0)


def main():
    args = parse_args()
    if not args.repo_root.expanduser().is_dir():
        print(f"[ERROR] Repository root does not exist: {args.repo_root}", file=sys.stderr)
        return 2
    audit = Audit(args)
    try:
        audit.execute()
    except Exception as exc:
        audit.error(f"Uncaught audit error: {exc}")
    return audit.save()


if __name__ == "__main__":
    raise SystemExit(main())
