#!/usr/bin/env python3
"""Evaluate the frozen CL-7B SVM+AST detector under controlled decoding regimes.

Inputs (read only):
  - The original CodeLlama-7B 450-pair test_.csv with AST CodeT5+ embeddings.
  - Its original complexity-balanced pair manifest and selected fitted SVM pickle.
  - run-x-06 prepared files, run-x-08 controlled seed-specific matched CSVs and QC.
  - Original tree-sitter Python AST and CodeT5+ embedding Python implementations.

Outputs (new files in --output-dir only):
  - preflight_summary.json and preflight_pairs.csv
  - ast_reference_qc.csv and embedding_provenance.json
  - baseline_predictions.csv and per-seed paired_predictions.csv / paired_metrics.csv
  - per-seed bootstrap_replicates.csv, evaluation_summary.json, findings.txt
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run06-dir", type=Path)
    parser.add_argument("--run08-dir", type=Path)
    parser.add_argument("--phase", choices=["preflight", "run"], default="preflight")
    parser.add_argument("--seeds", default="20260723", help="Comma-separated completed run-x-08 seeds")
    parser.add_argument("--model-file", type=Path)
    parser.add_argument("--embedding-max-len", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20260723, help="Statistical bootstrap RNG seed")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-other-python", action="store_true", help="Offline test only; results not validated on paper environment")
    args = parser.parse_args()
    args.seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    require(args.seeds and len(args.seeds) == len(set(args.seeds)), "SEEDS must be unique nonempty integers")
    return args


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
        "run08": (a.run08_dir or repo / "src/output/run-x-08/20261012-224115-68731").resolve(),
        "ast_src": repo / "src/code-analyzer-tree-sitter/tree_sitter_ast_python.py",
        "grammar": repo / "src/code-analyzer-tree-sitter/build/my-languages.so",
        "embed_src": repo / "src/ml_embeddings/generate_embeddings.py",
        "validator": repo / "src/code-generation/find_validsyntax_mgc.py",
    }


def check_seed(a, paths, test, manifest, run06_reference, seed):
    directory = paths["run08"]
    prefix = f"seed{seed}_"
    t00_path = directory / (prefix + "common_t00_pairs.csv")
    t02_path = directory / (prefix + "common_t02_pairs.csv")
    comparison_path = directory / (prefix + "comparison.csv")
    extraction_qc_path = directory / (prefix + "extraction_qc.csv")
    summary_path = directory / (prefix + "summary.json")
    extracted_path = directory / (prefix + "extracted_functions.jsonl")
    for p in (t00_path, t02_path, comparison_path, extraction_qc_path, summary_path, extracted_path):
        require(p.is_file(), f"Missing run-x-08 seed output: {p}")
    t00 = pd.read_csv(t00_path, keep_default_na=False)
    t02 = pd.read_csv(t02_path, keep_default_na=False)
    comparison = pd.read_csv(comparison_path, keep_default_na=False)
    qc = pd.read_csv(extraction_qc_path, keep_default_na=False)
    extracted = [json.loads(x) for x in extracted_path.read_text().splitlines() if x.strip()]
    require(len(extracted) == 450 and len({x["pair_id"] for x in extracted}) == 450, "Seed extracted JSONL must contain 450 unique records")
    extract_ref = {x["pair_id"]: x for x in extracted}
    summary = json.loads(summary_path.read_text())
    require(summary["status"] == "PASS" and summary["seed"] == seed, "Seed summary mismatch")
    require(summary["generated"] == 450, "Unexpected controlled test generation count")
    if seed == 20260723:
        require(summary["t02_controlled_valid"] == 404, "Reference seed T=0.2 valid count changed")
    require(summary["temperature"] == 0.2 and summary["do_sample"] is True and summary["eos_ids"] == [2]
            and summary["top_p"] == 0.95 and summary["top_k"] == 50 and summary["max_new_tokens"] == 512,
            "Decoding setup differs from run-x-08 controlled generation")
    require(len(comparison) == len(qc) == 450 and comparison.pair_id.is_unique and qc.pair_id.is_unique,
            "Expected 450 unique comparison and extraction QC rows")
    require(set(comparison.pair_id) == set(qc.pair_id) == set(manifest.loc[manifest.split == "test", "pair_id"]),
            "Seed selection IDs differ from original test manifest")
    require((comparison.seed == seed).all() and (qc.seed == seed).all(), "Seed IDs differ")
    require((comparison.split == "test").all() and (qc.split == "test").all(), "Non-test rows in controlled comparison")
    common_ids = set(comparison.loc[comparison.common_valid, "pair_id"])
    require(len(common_ids) == int(summary["common_valid"]), "Common-valid count differs from summary")
    require(len(t00) == len(t02) == 2*len(common_ids), "Matched CSV lengths differ from common-valid count")
    require(set(t00.columns) == set(t02.columns) == {"idx", "code", "label"}, "Unexpected pair CSV columns")
    require(t00.idx.is_unique and t02.idx.is_unique and set(t00.idx) == set(t02.idx), "Mismatched or duplicate matched row IDs")
    test_ref = test.set_index("idx")
    src0 = t00.set_index("idx")
    src2 = t02.set_index("idx")
    cmp = comparison.set_index("pair_id")
    qcx = qc.set_index("pair_id")
    for pid in sorted(common_ids):
        r = cmp.loc[pid]
        require(bool(r.t00_valid) and bool(r.t02_controlled_valid) and bool(r.common_valid), f"Bad common-valid flags {pid}")
        require(qcx.loc[pid, "status"] == "VALID", f"T=0.2 extraction not VALID: {pid}")
        require(bool(run06_reference[pid]["extracted_valid"]), f"T=0.0 reference not valid: {pid}")
        require(extract_ref[pid]["status"] == "VALID", f"T=0.2 JSONL extraction invalid: {pid}")
        require(str(src0.at[pid + "_human", "code"]) == str(src2.at[pid + "_human", "code"]) == str(test_ref.at[pid + "_human", "code"]), f"HWC mismatch: {pid}")
        for suffix, label, target in (("_human", "human", 1), ("_lm", "lm", 0)):
            idx = pid + suffix
            require(src0.at[idx, "label"] == src2.at[idx, "label"] == label, f"Label mismatch: {idx}")
            require(int(test_ref.at[idx, "actual label"]) == target, f"Original test label mismatch: {idx}")
        agc0 = str(src0.at[pid + "_lm", "code"])
        agc2 = str(src2.at[pid + "_lm", "code"])
        require(digest_text(agc0) == r.t00_agc_sha256 == run06_reference[pid]["extracted_agc_sha256"], f"T=0.0 source AGC hash mismatch: {pid}")
        require(digest_text(agc2) == r.t02_agc_sha256 == extract_ref[pid]["extracted_agc_sha256"], f"T=0.2 source AGC hash mismatch: {pid}")
        require(agc0 == run06_reference[pid]["extracted_agc_code"] and agc2 == extract_ref[pid]["extracted_agc_code"], f"Extracted code differs from authoritative JSONL: {pid}")
        require(bool(r.same_code_if_common) == (agc0 == agc2), f"AGC identity flag mismatch: {pid}")
        require(bool(r.t02_incompleteness_warning) == bool(qcx.at[pid, "incompleteness_warning"]), f"T=0.2 completeness flag mismatch: {pid}")
    meta = manifest.set_index("pair_id").loc[sorted(common_ids), ["complexity_score", "complexity_block"]].copy()
    meta["pair_id"] = meta.index
    meta["warning_t02"] = [bool(cmp.at[i, "t02_incompleteness_warning"]) for i in meta.index]
    meta["warning_t00"] = [bool(cmp.at[i, "t00_incompleteness_warning"]) for i in meta.index]
    meta["completeness_warning"] = meta.warning_t02 | meta.warning_t00
    meta["changed_agc"] = [not bool(cmp.at[i, "same_code_if_common"]) for i in meta.index]
    meta = meta.reset_index(drop=True)
    require(int(meta.completeness_warning.sum()) == int(summary["common_valid"] - summary["common_warning_free"]), "Warning-free count mismatch")
    require(int((~meta.changed_agc).sum()) == int(summary["common_identical_agc"]), "Same-code count mismatch")
    if seed == 20260723:
        require(len(common_ids) == 382 and int((~meta.completeness_warning).sum()) == 320 and int(meta.changed_agc.sum()) == 267,
                "Reference seed (382, 320, 267) counts differ")
    return {
        "seed": seed, "t00": t00, "t02": t02, "meta": meta, "summary": summary,
        "sources": {"t00": digest(t00_path), "t02": digest(t02_path),
                    "comparison": digest(comparison_path), "extraction_qc": digest(extraction_qc_path),
                    "summary": digest(summary_path)},
    }


def digest_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def preflight(a, paths):
    require(sys.version_info[:2] == (3, 11) or a.allow_other_python, "Python 3.11 is required")
    require(a.embedding_max_len == 2048, "Original CodeT5+ max_len must be 2048")
    require(a.bootstrap >= 0 and a.batch_size > 0, "Invalid bootstrap or batch size")
    for name in ("test", "manifest", "original", "pickle", "ast_src", "grammar", "embed_src", "validator"):
        require(paths[name].is_file(), f"Missing original source {name}: {paths[name]}")
    for name in ("experiment_config.json", "input_manifest.json", "controlled_summary.json", "test_selection.csv"):
        require((paths["run08"] / name).is_file(), f"Missing run-x-08 {name}")
    for name in ("experiment_config.json", "full_prepared.jsonl", "extracted_functions.jsonl", "full_summary.json"):
        require((paths["run06"] / name).is_file(), f"Missing run-x-06 {name}")
    require(digest(paths["pickle"]) == MODEL_SHA, "Fitted paper SVM SHA-256 mismatch")
    t = pd.read_csv(paths["test"])
    m = pd.read_csv(paths["manifest"])
    original = pd.read_csv(paths["original"])
    require(len(t) == 900 and len(m) == 4500 and len(original) == 9000, "Unexpected baseline row counts")
    require(t.idx.is_unique and original.idx.is_unique and m.pair_id.is_unique, "Duplicate original IDs")
    require(set(t.idx.map(pair_id)) == set(m.loc[m.split == "test", "pair_id"]), "Test IDs differ from manifest")
    feats = [f"ast_{i}" for i in range(256)]
    require(all(c in t.columns for c in feats+["idx", "code", "ast", "actual label"]), "Original test lacks AST CodeT5+ columns")
    ref = t.set_index("idx")
    src = original.set_index("idx")
    for idx in t.idx:
        require(ref.at[idx, "code"] == src.at[idx, "code"], f"Original test differs from source: {idx}")
    conf08 = json.loads((paths["run08"] / "experiment_config.json").read_text())
    inp08 = json.loads((paths["run08"] / "input_manifest.json").read_text())
    summary08 = json.loads((paths["run08"] / "controlled_summary.json").read_text())
    conf06 = json.loads((paths["run06"] / "experiment_config.json").read_text())
    summary06 = json.loads((paths["run06"] / "full_summary.json").read_text())
    require(summary08["status"] == "PASS" and summary08["source_inputs_unmodified"] and not summary08["backfill"], "run-x-08 not PASS or backed up")
    require(summary06["status"] == "PASS" and summary06["generated"] == 4500, "run-x-06 not PASS")
    require(conf08["model"] == conf06["model"] == "codellama/CodeLlama-7b-hf", "Model mismatch")
    require(conf08["eos_ids"] == conf06["eos_ids"] == [2], "EOS mismatch")
    require(conf08["prompt_max_tokens"] == conf06["prompt_max_tokens"] == 128, "Prompt cap mismatch")
    require(conf08["max_new_tokens"] == conf06["max_new_tokens"] == 512, "Output cap mismatch")
    expected = conf08["input_hashes"]
    checks = {"run06_config_sha256": digest(paths["run06"] / "experiment_config.json"),
              "run06_prepared_sha256": digest(paths["run06"] / "full_prepared.jsonl"),
              "run06_extracted_sha256": digest(paths["run06"] / "extracted_functions.jsonl"),
              "run06_summary_sha256": digest(paths["run06"] / "full_summary.json"),
              "original_csv_sha256": digest(paths["original"]),
              "split_manifest_sha256": digest(paths["manifest"]),
              "validator_sha256": digest(paths["validator"])}
    for key, value in checks.items():
        require(expected[key] == value and inp08["source_hashes"][key] == value, f"Provenance hash mismatch: {key}")
    require(inp08["test_prepared_file_sha256"] == digest(paths["run08"] / "test_prepared.jsonl"), "Prepared test input hash mismatch")
    require(sorted(summary08["seeds"]) == sorted(inp08["seeds"]) == sorted(conf08["seeds"]), "run-x-08 seed lists mismatch")
    for seed in a.seeds:
        require(seed in summary08["seeds"], f"Seed {seed} not found in completed run-x-08 output")
    run06_records = [json.loads(line) for line in (paths["run06"] / "extracted_functions.jsonl").read_text().splitlines() if line.strip()]
    require(len(run06_records) == 4500 and len({x["pair_id"] for x in run06_records}) == 4500, "Invalid run-x-06 extraction JSONL")
    run06_reference = {x["pair_id"]: x for x in run06_records}
    sets = [check_seed(a, paths, t, m, run06_reference, seed) for seed in a.seeds]
    info = {"status": "PASS", "run08_id": paths["run08"].name,
            "run06_id": paths["run06"].name, "seeds": a.seeds,
            "original_test_pairs": 450, "input_hashes": checks,
            "test_sha256": digest(paths["test"]), "model_sha256": MODEL_SHA,
            "ast_script_sha256": digest(paths["ast_src"]), "embedding_script_sha256": digest(paths["embed_src"]),
            "per_seed": [{"seed": v["seed"], "matched": len(v["meta"]),
                          "warning_free": int((~v["meta"].completeness_warning).sum()),
                          "changed": int(v["meta"].changed_agc.sum()),
                          "sources": v["sources"]} for v in sets]}
    print("[PREFLIGHT] PASS: original test=450, " + "; ".join(f"seed={v['seed']} common={len(v['meta'])} warning-free={int((~v['meta'].completeness_warning).sum())} changed={int(v['meta'].changed_agc.sum())}" for v in sets))
    print("[PREFLIGHT] Exact paper SVM SHA-256 and run-x-06/run-x-08 provenance verified")
    return t, sets, info


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


def ast_sequences_all(t, sets, paths, out):
    from tree_sitter import Language, Parser
    sys.path.insert(0, str(paths["ast_src"].parent))
    from tree_sitter_ast_python import F
    parser = Parser()
    parser.set_language(Language(str(paths["grammar"]), "python"))

    def sequence(code):
        raw = code.encode("utf-8")
        tree = parser.parse(raw)
        require(not tree.root_node.has_error, "tree-sitter Python AST parse failed")
        return " ".join(F(tree.root_node, raw))

    reference_qc = []
    for row in t.itertuples(index=False):
        computed = sequence(str(row.code))
        require(computed == row.ast, f"Historical CodeT5+ AST sequence mismatch: {row.idx}")
        reference_qc.append({"idx": row.idx, "reference_matches": True})
    pd.DataFrame(reference_qc).to_csv(out / "ast_reference_qc.csv", index=False)
    print(f"[AST] Historical 900 AST strings reproduced: {len(reference_qc)}/900")
    result = {}
    for entry in sets:
        seed = entry["seed"]
        ids = sorted(entry["meta"].pair_id)
        ast_entry = {}
        for condition in ("t00", "t02"):
            indexed = entry[condition].set_index("idx")
            codes = [str(indexed.at[pid + "_lm", "code"]) for pid in ids]
            ast_entry[condition] = [sequence(code) for code in codes]
        result[seed] = ast_entry
        print(f"[AST] Seed {seed}: 2 * {len(ids)} controlled AGC AST strings parsed")
    return result


def embed_all(a, paths, t, sets, all_ast, out):
    cache = out / "ast_embeddings.npz"
    provenance = out / "embedding_provenance.json"
    source_parts = [digest(paths["test"]), digest(paths["ast_src"]), digest(paths["embed_src"]),
                    str(a.embedding_max_len), ",".join(str(x) for x in a.seeds)]
    for entry in sets:
        source_parts.extend(entry["sources"].values())
    source_sha = hashlib.sha256("|".join(source_parts).encode()).hexdigest()
    if a.resume and cache.is_file() and provenance.is_file():
        meta = json.loads(provenance.read_text())
        require(meta["inputs_sha256"] == source_sha and meta["cache_sha256"] == digest(cache),
                "Embedding resume cache changed or inputs differ")
        saved = np.load(cache)
        require(saved["original"].shape == (900, 256), "Cached baseline embedding shape differs")
        for entry in sets:
            for cond in ("t00", "t02"):
                require(saved[f"seed{entry['seed']}_{cond}"].shape == (len(entry["meta"]), 256),
                        "Cached controlled embedding shape differs")
        print("[EMBED] Reusing SHA-256-verified CodeT5+ embedding cache")
        return {key: saved[key] for key in saved.files}

    import torch
    require(a.device != "cuda" or torch.cuda.is_available(), "CUDA requested but unavailable")
    helper = load_embedding_helpers(paths["embed_src"])
    tok, model = helper.load_model(a.device)
    encoded = {"original": helper.embed_batch(
        t.ast.astype(str).tolist(), tok, model, a.device,
        batch_size=a.batch_size, max_len=2048, desc="original 450-pair AST")}
    for entry in sets:
        seed = entry["seed"]
        for cond in ("t00", "t02"):
            key = f"seed{seed}_{cond}"
            encoded[key] = helper.embed_batch(
                all_ast[seed][cond], tok, model, a.device,
                batch_size=a.batch_size, max_len=2048, desc=key)
            require(encoded[key].shape == (len(entry["meta"]), 256), f"Unexpected {key} embedding shape")
    require(encoded["original"].shape == (900, 256), "Unexpected original embedding shape")
    for key, arr in encoded.items():
        require(np.isfinite(arr).all(), f"Nonfinite embedding: {key}")
    np.savez_compressed(cache, **encoded)
    json_write(provenance, {
        "inputs_sha256": source_sha, "cache_sha256": digest(cache),
        "model": helper.MODEL_ID, "max_len": 2048, "batch_size": a.batch_size,
        "device": a.device, "array_shapes": {key: list(arr.shape) for key, arr in encoded.items()},
        "reference_source_ast_sha256": digest(paths["ast_src"]),
        "reference_embed_script_sha256": digest(paths["embed_src"]),
        "note": "Original CodeT5+ AST embedding helpers reused directly; no model retraining"
    })
    print("[EMBED] Verified baseline and controlled AST embeddings saved")
    return encoded


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


def run(a, paths, t, sets, preflight_info):
    out = a.output_dir
    out.mkdir(parents=True, exist_ok=True)
    json_write(out / "preflight_summary.json", preflight_info)
    classifier = unpack_classifier(paths["pickle"])
    cols = [f"ast_{i}" for i in range(256)]
    cached_s, cached_p, mode = scores_for(classifier, t[cols].to_numpy())
    baseline_auc = float(roc_auc_score(t["actual label"], cached_s))
    require(abs(baseline_auc - BASELINE_TARGET) <= 0.000051,
            f"The original CL-7B paper AUROC was not reproduced: {baseline_auc:.8f}")
    base_cached = t[["idx", "actual label"]].copy()
    base_cached["score"] = cached_s
    base_cached["prediction"] = cached_p
    base_cached.to_csv(out / "baseline_cached_predictions.csv", index=False)
    json_write(out / "baseline_cached_summary.json", {
        "reference_test_pairs": 450, "cached_auroc": baseline_auc,
        "paper_auroc": BASELINE_TARGET, "model_sha256": MODEL_SHA, "score_mode": mode})
    print(f"[BASELINE] Original 450-pair cached AUROC={baseline_auc:.8f} mode={mode}")

    ast = ast_sequences_all(t, sets, paths, out)
    enc = embed_all(a, paths, t, sets, ast, out)
    fresh_s, fresh_p, fresh_mode = scores_for(classifier, enc["original"])
    fresh_auc = float(roc_auc_score(t["actual label"], fresh_s))
    max_drift = float(np.max(np.abs(fresh_s - cached_s)))
    require(fresh_mode == mode, "Classifier scoring mode changed")
    require(abs(fresh_auc - baseline_auc) <= 0.005 and max_drift <= 0.001,
            f"Cached vs fresh CodeT5+ baseline drift: AUROC={fresh_auc:.8f}, max score delta={max_drift:.6g}")
    b = t[["idx", "code", "actual label"]].copy()
    b["score_cached"] = cached_s
    b["score_fresh"] = fresh_s
    b["pred_cached"] = cached_p
    b["pred_fresh"] = fresh_p
    b.to_csv(out / "baseline_predictions.csv", index=False)
    print(f"[BASELINE] Fresh AUROC={fresh_auc:.8f}; max absolute SVM score drift={max_drift:.6g}")

    lookup = {ident: i for i, ident in enumerate(t.idx)}
    results = []
    for entry in sets:
        seed = entry["seed"]
        seed_dir = out / f"seed{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        details = entry["meta"].set_index("pair_id")
        ids = sorted(details.index)
        s00, pred00, mode00 = scores_for(classifier, enc[f"seed{seed}_t00"])
        s02, pred02, mode02 = scores_for(classifier, enc[f"seed{seed}_t02"])
        require(mode00 == mode02 == mode, "Score mode inconsistency")
        rows = []
        for j, pid in enumerate(ids):
            info = details.loc[pid]
            for label, suffix in ((1, "human"), (0, "lm")):
                ix = pid + "_" + suffix
                pos = lookup[ix]
                is_hwc = label == 1
                rows.append({
                    "seed": seed, "pair_id": pid, "idx": ix, "label": label,
                    "complexity_score": float(info.complexity_score),
                    "complexity_block": int(info.complexity_block),
                    "completeness_warning": bool(info.completeness_warning),
                    "warning_t00": bool(info.warning_t00), "warning_t02": bool(info.warning_t02),
                    "changed_agc": bool(info.changed_agc),
                    "score_t00": float(fresh_s[pos]) if is_hwc else float(s00[j]),
                    "score_t02": float(fresh_s[pos]) if is_hwc else float(s02[j]),
                    "pred_t00": int(fresh_p[pos]) if is_hwc else int(pred00[j]),
                    "pred_t02": int(fresh_p[pos]) if is_hwc else int(pred02[j]),
                })
        pred = pd.DataFrame(rows)
        require(pred.idx.is_unique and len(pred) == len(ids)*2, "Duplicate or missing prediction rows")
        require((pred.loc[pred.label == 1, "score_t00"] == pred.loc[pred.label == 1, "score_t02"]).all(),
                "HWC prediction changed across decoding conditions")
        unchanged = pred.loc[(pred.label == 0) & (~pred.changed_agc)]
        same_code_score_delta = float(np.abs(unchanged.score_t00 - unchanged.score_t02).max()) if len(unchanged) else 0.0
        require(same_code_score_delta <= 0.001,
                f"Identical AGC codes gave inconsistent SVM scores: {same_code_score_delta}")
        pred.to_csv(seed_dir / "paired_predictions.csv", index=False)
        metrics = [subset_summary(pred, set(ids), "all_common_valid")]
        nowarn = set(details.loc[~details.completeness_warning].index)
        changed = set(details.loc[details.changed_agc].index)
        metrics.append(subset_summary(pred, nowarn, "no_incompleteness_warning"))
        metrics.append(subset_summary(pred, changed, "changed_agc_only"))
        quintile = pd.qcut(details["complexity_score"].rank(method="first"), 5, labels=False)
        for i in range(5):
            metrics.append(subset_summary(pred, set(details.index[quintile == i]), f"complexity_quintile_{i+1}"))
        ci_results = []
        for k, entry_metric in enumerate(metrics):
            name = entry_metric["subset"]
            selection = sorted(set(ids) if k == 0 else (nowarn if k == 1 else changed if k == 2 else set(details.index[quintile == (k-3)])))
            if a.bootstrap:
                samples = bootstrap_matched(pred, selection, a.bootstrap, a.seed + seed*17 + k)
                qlo, qhi = np.quantile(samples[:, 2], [0.025, 0.975]).tolist()
                sign_tail = float(min(1.0, 2*min(np.mean(samples[:, 2] >= 0), np.mean(samples[:, 2] <= 0))))
                if k == 0:
                    pd.DataFrame(samples, columns=["t02_auroc", "t00_auroc", "delta_t00_minus_t02"]).to_csv(seed_dir / "bootstrap_replicates.csv", index=False)
            else:
                qlo, qhi, sign_tail = None, None, None
            entry_metric.update({"ci95_low": qlo, "ci95_high": qhi,
                                 "bootstrap_sign_tail_fraction": sign_tail, "bootstrap_replicates": a.bootstrap})
            ci_results.append(entry_metric)
        pd.DataFrame(ci_results).to_csv(seed_dir / "paired_metrics.csv", index=False)
        accuracy = {}
        for cond in ("t00", "t02"):
            accuracy[cond] = float((pred[f"pred_{cond}"] == pred.label).mean())
        result = {
            "seed": seed, "status": "PASS", "n_common_valid": len(ids),
            "n_warning_free": len(nowarn), "n_changed_agc": len(changed),
            "n_identical_agc": len(unchanged), "matched": ci_results[0],
            "warning_free": ci_results[1], "changed_agc": ci_results[2],
            "complexity_quintiles": ci_results[3:], "accuracy": accuracy,
            "identical_agc_max_score_delta": same_code_score_delta,
            "baseline_cached_450_auroc": baseline_auc, "baseline_fresh_450_auroc": fresh_auc,
            "bootstrap_replicates": a.bootstrap,
            "limitations": ["Sampling (T=0.2) versus greedy (T=0.0) is a decoding-regime comparison, not a pure scalar temperature effect.",
                            "Common-valid subset may select less complex functions.",
                            "AST validity is not functional completeness; completeness flags are only heuristic."]}
        json_write(seed_dir / "evaluation_summary.json", result)
        details.sort_values(["complexity_score", "pair_id"]).to_csv(seed_dir / "matched_pair_metadata.csv", index=False)
        results.append(result)
        primary = ci_results[0]
        print(f"[SEED {seed}] PASS common={len(ids)} warning-free={len(nowarn)} changed={len(changed)} identical={len(unchanged)}")
        print(f"[SEED {seed}] Controlled T=0.2 AUROC={primary['t02_auroc']:.6f}; T=0.0 AUROC={primary['t00_auroc']:.6f}; delta(T00-T02)={primary['delta_t00_minus_t02']:+.6f}")
        print(f"[SEED {seed}] Paired bootstrap CI95=[{primary['ci95_low']}, {primary['ci95_high']}]")
    full = {"experiment": "run-x-09", "version": "v1", "status": "PASS",
            "reference_baseline_450_cached_auroc": baseline_auc,
            "reference_baseline_450_fresh_auroc": fresh_auc,
            "baseline_max_score_delta": max_drift,
            "score_mode": mode, "seeds": a.seeds, "per_seed": results,
            "model_sha256": MODEL_SHA, "bootstrap_seed": a.seed, "bootstrap_replicates": a.bootstrap,
            "environment": {"python": sys.version.split()[0], "numpy": np.__version__,
                            "torch": __import__("torch").__version__, "platform": platform.platform()},
            "source_preflight": preflight_info,
            "no_retraining": True, "no_model_selection": True,
            "note": "Per-seed analyses are separate; repeated procedures across seeds are not treated as independent examples."}
    json_write(out / "evaluation_summary.json", full)
    lines = ["run-x-09 | Controlled T=0.2 sampling versus T=0.0 greedy | PASS",
             f"Original CL-7B SVM+AST baseline 450 AUROC cached={baseline_auc:.8f} fresh={fresh_auc:.8f}"]
    for res in results:
        primary = res["matched"]
        lines.append(f"seed={res['seed']} common={res['n_common_valid']} warning-free={res['n_warning_free']} changed={res['n_changed_agc']} unchanged={res['n_identical_agc']}")
        lines.append(f"  T02={primary['t02_auroc']:.6f} T00={primary['t00_auroc']:.6f} delta(T00-T02)={primary['delta_t00_minus_t02']:+.6f} CI95=[{primary['ci95_low']}, {primary['ci95_high']}]")
    lines += ["Interpretation: Same EOS, prompt, extraction and validation; T=0.2 sampling versus T=0.0 greedy.",
              "No change to the original classifier or paper's cross-generator selection."]
    (out / "findings.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    args = args_parser()
    paths = paths_for(args)
    print("=================================================================")
    print(f"run-x-09 | controlled CL-7B/SVM+AST | phase={args.phase}")
    print(f"Python={sys.version.split()[0]} device={args.device} max_len={args.embedding_max_len} bootstrap={args.bootstrap}")
    print("No model retraining, model re-selection, or source modifications")
    print("=================================================================")
    baseline, sets, info = preflight(args, paths)
    if args.phase == "preflight":
        print("[DRY-RUN] PASS; no model unpickling, GPU inference, or output creation")
        return
    run(args, paths, baseline, sets, info)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[ERROR]", type(e).__name__ + ":", e, file=sys.stderr)
        sys.exit(1)
