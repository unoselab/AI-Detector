#!/usr/bin/env python3
"""Evaluate the existing CL-7B SVM+AST detector under T=0.0 generation.

Inputs (read only):
  - The original CodeLlama-7B 450-pair test_.csv with AST CodeT5+ embeddings.
  - Its original complexity-balanced pair manifest and selected fitted SVM pickle.
  - run-x-06 common_valid_pairs_full.csv and extraction_qc.csv.
  - Original tree-sitter Python AST and CodeT5+ embedding Python implementations.

Outputs (new files in --output-dir only):
  - preflight_summary.json and preflight_pairs.csv
  - ast_reference_qc.csv and embedding_provenance.json
  - baseline_predictions.csv, paired_predictions.csv, paired_metrics.csv
  - bootstrap_replicates.csv, evaluation_summary.json, findings.txt
  - cached AST embedding arrays to support resume; never alters baseline.

The original selected classifier is NEVER refitted or reselected. The original
source AST function, CodeT5+ model, and max_length=2048 are reused as-is.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import pickle
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

EXPERIMENT = "codellama-7b_4500_complexity_stratified_maxlen2048"
DATASET = "codesearchnet_codellama-7b_python_merged_4500"
MODEL_FILE = "tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"
MODEL_SHA = "a7425af490022045d40da3aa660a38bfd2aabc22a27dd70a4f8ee5ebf1a61ce7"
MODEL_KEY = DATASET + "ast_"
BASELINE_TARGET = 0.7950
SELECTED_LABEL = {"human": 1, "lm": 0}


def args_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--run06-dir", type=Path)
    p.add_argument("--phase", choices=["preflight", "run"], default="preflight")
    p.add_argument("--model-file", type=Path)
    p.add_argument("--embedding-max-len", type=int, default=2048)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--device", default="cuda")
    p.add_argument("--bootstrap", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260723)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--allow-baseline-drift", action="store_true", help="Diagnostic only; do not treat as primary evaluation.")
    return p.parse_args()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    sha = hashlib.sha256()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def json_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(value, file, indent=2, ensure_ascii=False, allow_nan=False)
        file.write("\n")


def pair_id(idx):
    if idx.endswith("_human"):
        return idx[:-6]
    if idx.endswith("_lm"):
        return idx[:-3]
    raise ValueError("Unexpected procedure ID suffix: " + str(idx))


def paths_for(a):
    repo = a.repo_root.resolve()
    return {
        "root": repo,
        "test": repo / "src/ml_embeddings/data_codesearchnet/splits" / EXPERIMENT / DATASET / "test_.csv",
        "manifest": repo / "src/ml_embeddings/data_codesearchnet/splits" / EXPERIMENT / "complexity_stratified_pair_manifest.csv",
        "original": repo / "src/code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/validsyntax_4500_complexity" / (DATASET + ".csv"),
        "pickle": a.model_file or repo / "src/ml_embeddings/data_codesearchnet/models" / EXPERIMENT / MODEL_FILE,
        "run06": (a.run06_dir or repo / "src/output/run-x-06/20261012-154334-48074").resolve(),
        "ast_src": repo / "src/code-analyzer-tree-sitter/tree_sitter_ast_python.py",
        "grammar": repo / "src/code-analyzer-tree-sitter/build/my-languages.so",
        "embed_src": repo / "src/ml_embeddings/generate_embeddings.py",
    }


def preflight(a, paths):
    require(sys.version_info[:2] == (3, 11), "Python 3.11 required for historical compatibility")
    require(a.embedding_max_len == 2048, "Original selected model uses CodeT5+ max_len=2048")
    for label in ("test", "manifest", "original", "pickle", "ast_src", "grammar", "embed_src"):
        require(paths[label].is_file(), f"Missing required {label}: {paths[label]}")
    for label in ("common_valid_pairs_full.csv", "extraction_qc.csv", "full_summary.json", "input_manifest.json"):
        require((paths["run06"] / label).is_file(), f"Missing run-x-06 {label}")
    require(digest(paths["pickle"]) == MODEL_SHA, "Selected fitted SVM pickle SHA-256 mismatch")
    t = pd.read_csv(paths["test"])
    m = pd.read_csv(paths["manifest"])
    o = pd.read_csv(paths["original"])
    c = pd.read_csv(paths["run06"] / "common_valid_pairs_full.csv")
    q = pd.read_csv(paths["run06"] / "extraction_qc.csv")
    orig_hash = digest(paths["original"])
    manifest_hash = digest(paths["manifest"])
    run_manifest = json.loads((paths["run06"] / "input_manifest.json").read_text())
    run_summary = json.loads((paths["run06"] / "full_summary.json").read_text())
    require(run_manifest["source_csv_sha256"] == orig_hash, "run-x-06 original CSV digest mismatch")
    require(run_manifest["split_sha256"] == manifest_hash, "run-x-06 split manifest digest mismatch")
    require(run_summary["generated"] == 4500 and run_summary["common_valid_pairs"] == 3893, "Run-06 counts differ")
    require(len(t) == 900 and len(m) == 4500 and len(o) == 9000 and len(c) == 7786 and len(q) == 4500, "Unexpected input row counts")
    require(t.idx.is_unique and o.idx.is_unique and c.idx.is_unique and q.pair_id.is_unique and m.pair_id.is_unique, "Duplicate IDs")
    require(set(t["actual label"].unique()) == {0, 1}, "Unexpected original test labels")
    require(set(c.label.unique()) == {"human", "lm"}, "Unexpected generated labels")
    feats = [f"ast_{i}" for i in range(256)]
    require(all(x in t.columns for x in ["idx", "code", "ast", "actual label"] + feats), "Missing original AST CodeT5+ features")
    all_test = set(m.loc[m.split == "test", "pair_id"])
    test_ids = set(t.idx.map(pair_id))
    require(len(all_test) == len(test_ids) == 450 and test_ids == all_test, "Original test IDs not consistent with manifest")
    c["pair_id"] = c.idx.map(pair_id)
    common_ids = set(c.pair_id)
    require(len(common_ids) == 3893 and all(c.groupby("pair_id").label.nunique() == 2), "Missing common-valid pairs")
    ids = sorted(test_ids & common_ids)
    require(len(ids) == 380, "Expected 380 common-valid test pair IDs")
    c_test = c[c.pair_id.isin(ids)].copy()
    require(len(c_test) == 760, "Expected 760 T=0.0 test rows")
    # Check HWC reference against the original 450-pair test and original source.
    source = o.set_index("idx")
    reference = t.set_index("idx")
    newly = c_test.set_index("idx")
    for ident in ids:
        for label, s in (("human", 1), ("lm", 0)):
            ix = ident + "_" + label
            require(ix in reference.index, f"Missing baseline test row: {ix}")
            require(reference.at[ix, "actual label"] == s, f"Incorrect baseline label {ix}")
            require(source.at[ix, "code"] == reference.at[ix, "code"], f"Baseline code altered: {ix}")
        require(newly.at[ident + "_human", "code"] == reference.at[ident + "_human", "code"], f"HWC mismatch {ident}")
    qc = q.set_index("pair_id")
    joined = m.set_index("pair_id").loc[ids].copy()
    joined["pair_id"] = joined.index
    joined["completeness_warning"] = [(bool(qc.at[i, "missing_return_vs_hwc"]) or bool(qc.at[i, "length_cap_and_full_continuation"])) for i in ids]
    joined["changed_agc"] = [reference.at[i + "_lm", "code"] != newly.at[i + "_lm", "code"] for i in ids]
    joined["prompt_truncated"] = [bool(qc.at[i, "prompt_truncated"]) for i in ids]
    require(sum(joined.completeness_warning) == 51 and sum(joined.changed_agc) == 269, "Known test subset warning/change counts differ")
    require(not any(joined.prompt_truncated), "Prompt-truncated pair unexpectedly in common-valid test")
    require(sum(~joined.completeness_warning) == 329, "Expected 329 warning-free test pairs")
    out = a.output_dir
    out.mkdir(parents=True, exist_ok=True)
    joined = joined.reset_index(drop=True)
    joined.sort_values(["complexity_score", "pair_id"]).to_csv(out / "preflight_pairs.csv", index=False)
    meta = {
        "status": "PASS", "python": sys.version.split()[0], "executable": sys.executable,
        "baseline_pairs": 450, "matched_pairs": len(ids), "warning_free_pairs": 329,
        "changed_pairs": 269, "model_key": MODEL_KEY, "expected_baseline_auroc": BASELINE_TARGET,
        "model_sha256": MODEL_SHA, "original_sha256": orig_hash,
        "split_sha256": manifest_hash, "test_sha256": digest(paths["test"]),
        "common_sha256": digest(paths["run06"] / "common_valid_pairs_full.csv"),
        "qc_sha256": digest(paths["run06"] / "extraction_qc.csv"),
        "ast_script_sha256": digest(paths["ast_src"]),
        "embed_script_sha256": digest(paths["embed_src"]),
        "output_dir": str(out),
    }
    json_write(out / "preflight_summary.json", meta)
    print("[PREFLIGHT] PASS: baseline test=450; common-valid=380; warning-free=329; changed=269")
    print("[PREFLIGHT] Selected fitted SVM SHA-256 matches paper selection")
    return t, c_test, joined, meta


def unpack_classifier(model_path):
    # The pickle is a trusted, locally generated artifact. Never load untrusted pickle files.
    with open(model_path, "rb") as file:
        models = pickle.load(file)
    require(MODEL_KEY in models, f"Selected AST model key missing from pickle: {MODEL_KEY}; available={list(models)}")
    entry = models[MODEL_KEY]
    clf = entry[0] if isinstance(entry, (list, tuple)) else entry
    require(getattr(clf, "n_features_in_", None) == 256, "Selected classifier feature width must be 256")
    require(list(clf.classes_) == [0, 1], "Expected classifier labels [0,1] human=1")
    return clf


def scores_for(clf, features):
    x = np.asarray(features, dtype=np.float64)
    pred = clf.predict(x)
    if hasattr(clf, "predict_proba"):
        try:
            s = clf.predict_proba(x)[:, list(clf.classes_).index(1)]
            return np.asarray(s, float), np.asarray(pred, int), "proba"
        except Exception:
            pass
    require(hasattr(clf, "decision_function"), "SVM does not support continuous classification scores")
    s = np.asarray(clf.decision_function(x), float).ravel()
    return s, np.asarray(pred, int), "decision"


def ast_reference_sequences(t, novel, paths, out_dir):
    from tree_sitter import Language, Parser
    srcdir = str(paths["ast_src"].parent)
    sys.path.insert(0, srcdir)
    from tree_sitter_ast_python import F
    parser = Parser()
    parser.set_language(Language(str(paths["grammar"]), "python"))
    def sequence(code):
        raw = code.encode("utf-8")
        tree = parser.parse(raw)
        require(not tree.root_node.has_error, "Unexpected tree-sitter parse error")
        return " ".join(F(tree.root_node, raw))
    # Compare all original 900 test ASTs, not only a few examples.
    qc = []
    for row in t.itertuples(index=False):
        new_ast = sequence(row.code)
        same = new_ast == row.ast
        qc.append({"idx": row.idx, "reference_matches": same})
        require(same, f"Historical tree-sitter AST mismatch: {row.idx}")
    pd.DataFrame(qc).to_csv(out_dir / "ast_reference_qc.csv", index=False)
    novel_ast = [sequence(x) for x in novel.code.tolist()]
    print(f"[AST] Historical source AST reproduced {len(qc)}/{len(qc)}; T=0.0 AGC={len(novel_ast)}")
    return novel_ast


def load_embedding_helpers(path):
    spec = importlib.util.spec_from_file_location("historical_codet5p_embeddings", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.MODEL_ID == "Salesforce/codet5p-110m-embedding" and module.EMBED_DIM == 256, "Unexpected historical CodeT5+ implementation")
    return module


def embed_all(a, paths, t, novel, ast_new, out):
    cache = out / "ast_embeddings.npz"
    manifest = out / "embedding_provenance.json"
    input_digest = hashlib.sha256((digest(paths["test"]) + digest(paths["run06"] / "common_valid_pairs_full.csv") + digest(paths["ast_src"]) + digest(paths["embed_src"]) + str(a.embedding_max_len)).encode()).hexdigest()
    if a.resume and cache.exists() and manifest.exists():
        info = json.loads(manifest.read_text())
        require(info["input_sha256"] == input_digest and info["cache_sha256"] == digest(cache), "Cached embeddings do not match source inputs")
        mat = np.load(cache)
        require(mat["original"].shape == (900, 256) and mat["novel"].shape == (380, 256), "Incorrect cached embedding shapes")
        print("[EMBED] Reusing verified existing CodeT5+ embedding cache")
        return mat["original"], mat["novel"]
    require(a.device != "cuda" or __import__("torch").cuda.is_available(), "CUDA requested but unavailable; use --device cpu if necessary")
    helper = load_embedding_helpers(paths["embed_src"])
    tok, model = helper.load_model(a.device)
    original = helper.embed_batch(t.ast.astype(str).tolist(), tok, model, a.device, batch_size=a.batch_size, max_len=2048, desc="historical test AST")
    novel_emb = helper.embed_batch(ast_new, tok, model, a.device, batch_size=a.batch_size, max_len=2048, desc="new T=0.0 AST")
    require(original.shape == (900, 256) and novel_emb.shape == (380, 256), "Unexpected CodeT5+ feature shapes")
    require(np.isfinite(original).all() and np.isfinite(novel_emb).all(), "Nonfinite CodeT5+ features")
    np.savez_compressed(cache, original=original, novel=novel_emb)
    json_write(manifest, {
        "input_sha256": input_digest, "cache_sha256": digest(cache),
        "model": helper.MODEL_ID, "max_len": 2048, "batch_size": a.batch_size,
        "device": a.device, "original_rows": 900, "novel_rows": 380,
        "tree_sitter_ast_script_sha256": digest(paths["ast_src"]),
        "embedding_script_sha256": digest(paths["embed_src"]),
        "note": "AST-only embeddings via unchanged original generate_embeddings.py load_model and embed_batch",
    })
    print("[EMBED] Saved verified 900 original and 380 novel AST embeddings")
    return original, novel_emb


def paired_auroc(frame, column):
    return float(roc_auc_score(frame.label.to_numpy(), frame[column].to_numpy()))


def subset_summary(frame, select_ids, name):
    sub = frame[frame.pair_id.isin(select_ids)]
    require(len(sub) == 2 * len(select_ids), "Subgroup has incomplete paired observations: " + name)
    base = paired_auroc(sub, "score_t02")
    new = paired_auroc(sub, "score_t00")
    return {"subset": name, "pairs": len(select_ids), "t02_auroc": base, "t00_auroc": new, "delta_t00_minus_t02": new-base}


def bootstrap_matched(frame, all_ids, repeats, seed):
    rng = np.random.default_rng(seed)
    grouped = frame.set_index(["pair_id", "label"])
    n = len(all_ids)
    h0 = np.array([grouped.loc[(p, 1), "score_t02"] for p in all_ids])
    l0 = np.array([grouped.loc[(p, 0), "score_t02"] for p in all_ids])
    h1 = np.array([grouped.loc[(p, 1), "score_t00"] for p in all_ids])
    l1 = np.array([grouped.loc[(p, 0), "score_t00"] for p in all_ids])
    # Midrank AUROC for balanced HWC/AGC pair bootstrap (equiv to sklearn).
    def auc_from_scores(h, l):
        s = np.concatenate((h, l))
        y = np.concatenate((np.ones(len(h), dtype=int), np.zeros(len(l), dtype=int)))
        order = np.argsort(s, kind="mergesort")
        sorted_s = s[order]
        sorted_y = y[order]
        starts = np.r_[0, np.flatnonzero(sorted_s[1:] != sorted_s[:-1]) + 1]
        ends = np.r_[starts[1:], len(s)]
        positive_counts = np.add.reduceat(sorted_y, starts)
        rank_sums = np.dot((starts + 1 + ends) / 2.0, positive_counts)
        return float((rank_sums - n * (n + 1) / 2.0) / (n*n))
    results = np.empty((repeats, 3), dtype=np.float64)
    for i in range(repeats):
        sample = rng.integers(0, n, n)
        b0 = auc_from_scores(h0[sample], l0[sample])
        b1 = auc_from_scores(h1[sample], l1[sample])
        results[i, :] = b0, b1, b1-b0
        if (i+1) % 5000 == 0:
            print(f"[BOOTSTRAP] {i+1}/{repeats}")
    return results


def run(a, paths, t, common, metadata, preflight_info):
    out = a.output_dir
    clf = unpack_classifier(paths["pickle"])
    columns = [f"ast_{i}" for i in range(256)]
    cached_s, cached_p, cached_mode = scores_for(clf, t[columns].to_numpy())
    reference_auroc = float(roc_auc_score(t["actual label"].to_numpy(), cached_s))
    print(f"[BASELINE] Original cached-features test=450 AUROC={reference_auroc:.8f} score_mode={cached_mode}")
    baseline_cached = t[["idx", "actual label"]].copy()
    baseline_cached["score"] = cached_s
    baseline_cached["prediction"] = cached_p
    baseline_cached.to_csv(out / "baseline_cached_predictions.csv", index=False)
    json_write(out / "baseline_cached_summary.json", {"test_pairs": 450, "rows": 900,
        "cached_auroc": reference_auroc, "expected_paper_auroc": BASELINE_TARGET,
        "score_mode": cached_mode, "model_sha256": MODEL_SHA})
    require(abs(reference_auroc - BASELINE_TARGET) <= 0.000051, "Original paper AUROC 0.7950 not reproduced; stop")
    require(cached_mode in {"proba", "decision"}, "Missing continuous scores")
    novel = common[common.label == "lm"].copy()
    novel["pair_id"] = novel.idx.map(pair_id)
    novel = novel.set_index("pair_id").loc[sorted(metadata.pair_id)].reset_index()
    ast_new = ast_reference_sequences(t, novel, paths, out)
    fresh_original, fresh_novel = embed_all(a, paths, t, novel, ast_new, out)
    fresh_s, fresh_p, fresh_mode = scores_for(clf, fresh_original)
    novel_s, novel_p, novel_mode = scores_for(clf, fresh_novel)
    require(fresh_mode == cached_mode == novel_mode, "Score mode changed between old and new embedding paths")
    fresh_baseline_auroc = float(roc_auc_score(t["actual label"], fresh_s))
    score_abs_drift = np.abs(fresh_s - cached_s)
    max_diff = float(np.max(score_abs_drift))
    print(f"[BASELINE] Fresh 450-pair AUROC={fresh_baseline_auroc:.8f} vs cached={reference_auroc:.8f}; max_score_delta={max_diff:.6g}")
    baseline_ok = abs(fresh_baseline_auroc - reference_auroc) <= 0.005
    if not baseline_ok and not a.allow_baseline_drift:
        raise RuntimeError("Fresh embeddings do not reproduce the original AUROC within 0.005; investigate upstream environment")
    b = t[["idx", "code", "actual label"]].copy()
    b["score_cached"] = cached_s
    b["score_fresh"] = fresh_s
    b["pred_cached"] = cached_p
    b["pred_fresh"] = fresh_p
    b.to_csv(out / "baseline_predictions.csv", index=False)
    lookup = dict(zip(t.idx.tolist(), range(len(t))))
    newlookup = dict(zip(novel.pair_id.tolist(), range(len(novel))))
    pair_rows = []
    detail = metadata.set_index("pair_id")
    for pid in sorted(detail.index):
        info = detail.loc[pid]
        for label, suffix in [(1, "human"), (0, "lm")]:
            ix = pid + "_" + suffix
            pos = lookup[ix]
            pos_new = newlookup[pid] if label == 0 else None
            score_b = float(fresh_s[pos])
            score_n = score_b if label == 1 else float(novel_s[pos_new])
            pair_rows.append({
                "pair_id": pid, "idx": ix, "label": label, "complexity_score": float(info.complexity_score),
                "complexity_block": int(info.complexity_block), "completeness_warning": bool(info.completeness_warning),
                "changed_agc": bool(info.changed_agc), "score_t02": score_b, "score_t00": score_n,
                "pred_t02": int(fresh_p[pos]), "pred_t00": int(fresh_p[pos]) if label == 1 else int(novel_p[pos_new]),
            })
    p = pd.DataFrame(pair_rows)
    require(len(p) == 760 and p.idx.is_unique and p.pair_id.nunique() == 380, "Invalid matched prediction pairs")
    require((p[p.label == 1].score_t02 == p[p.label == 1].score_t00).all(), "HWC scores unexpectedly differ")
    unchanged = p[(p.label == 0) & (~p.changed_agc)]
    tol = float(np.max(np.abs(unchanged.score_t02 - unchanged.score_t00))) if len(unchanged) else 0.0
    print(f"[QC] Identical AGC code cases={len(unchanged)}; max prediction score difference={tol:.6g}")
    if tol > 0.005 and not a.allow_baseline_drift:
        raise RuntimeError("Identical AGC code has inconsistent score >0.005; investigate CodeT5+/AST provenance")
    p.to_csv(out / "paired_predictions.csv", index=False)
    all_ids = sorted(detail.index)
    nowarn = set(detail.loc[~detail.completeness_warning].index)
    changed = set(detail.loc[detail.changed_agc].index)
    metrics = [subset_summary(p, set(all_ids), "all_common_valid")]
    metrics.append(subset_summary(p, nowarn, "no_incompleteness_warning"))
    metrics.append(subset_summary(p, changed, "changed_agc_only"))
    # Equal-sized complexity quintiles of the 380-pair matched test set.
    quintiles = pd.qcut(detail["complexity_score"].rank(method="first"), 5, labels=False)
    for group in range(5):
        metrics.append(subset_summary(p, set(detail.index[quintiles == group]), f"complexity_quintile_{group+1}"))
    pd.DataFrame(metrics).to_csv(out / "paired_metrics.csv", index=False)
    if a.bootstrap:
        samples = bootstrap_matched(p, all_ids, a.bootstrap, a.seed)
        pd.DataFrame(samples, columns=["t02_auroc", "t00_auroc", "delta_t00_minus_t02"]).to_csv(out / "bootstrap_replicates.csv", index=False)
        ci = np.quantile(samples[:, 2], [0.025, 0.975]).tolist()
        p_two_sided = float(min(1.0, 2*min(np.mean(samples[:, 2] >= 0), np.mean(samples[:, 2] <= 0))))
    else:
        ci = None
        p_two_sided = None
    result = {
        "status": "PASS" if (baseline_ok and tol <= 0.005) else "BASELINE_DRIFT_DIAGNOSTIC",
        "reference_450_auroc": reference_auroc,
        "fresh_450_auroc": fresh_baseline_auroc,
        "reference_vs_fresh_max_score_delta": max_diff,
        "reference_vs_fresh_mean_score_delta": float(np.mean(score_abs_drift)),
        "matched_380": metrics[0], "warning_free_329": metrics[1], "changed_269": metrics[2],
        "matched_delta_ci95": ci, "matched_delta_bootstrap_sign_p_two_sided": p_two_sided,
        "bootstrap_replicates": a.bootstrap, "bootstrap_seed": a.seed,
        "identical_agc_score_max_delta": tol, "score_mode": fresh_mode,
        "environment": {"python": sys.version.split()[0], "torch": __import__("torch").__version__, "numpy": np.__version__, "platform": platform.platform()},
        "limitations": ["Generation settings and extraction policy differ across T=0.2/T=0.0.", "Common-valid selection may depend on complexity and prompt length.", "AST validity is not behavioral completeness."],
    }
    json_write(out / "evaluation_summary.json", result)
    lines = [
        f"run-x-07 | Status: {result['status']}",
        f"Baseline 450 cached AUROC: {reference_auroc:.6f}; fresh AUROC: {fresh_baseline_auroc:.6f}",
        f"Common-valid test=380; T=0.2: {metrics[0]['t02_auroc']:.6f}  T=0.0: {metrics[0]['t00_auroc']:.6f}  delta: {metrics[0]['delta_t00_minus_t02']:+.6f}",
        f"Matched bootstrap CI95: {ci}",
        f"Warning-free test=329; T=0.2: {metrics[1]['t02_auroc']:.6f} T=0.0: {metrics[1]['t00_auroc']:.6f}",
        f"Changed AGC test=269; T=0.2: {metrics[2]['t02_auroc']:.6f} T=0.0: {metrics[2]['t00_auroc']:.6f}",
        "Interpret as generation+extraction robustness, not a temperature-only effect.",
    ]
    (out / "findings.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    a = args_parser()
    paths = paths_for(a)
    print("=================================================================")
    print(f"run-x-07 | CL-7B/SVM+AST | phase={a.phase} | output={a.output_dir}")
    print(f"Python={sys.version.split()[0]} device={a.device} max_len={a.embedding_max_len} bootstrap={a.bootstrap}")
    print("No retraining, no hyperparameter selection, no original-file modification")
    print("=================================================================")
    t, common, metadata, info = preflight(a, paths)
    if a.phase == "preflight":
        print("[PREFLIGHT] No GPU model loaded; no detector pickle deserialized")
        return
    run(a, paths, t, common, metadata, info)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("[ERROR]", type(exc).__name__ + ":", exc, file=sys.stderr)
        sys.exit(1)
