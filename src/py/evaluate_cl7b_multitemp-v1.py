#!/usr/bin/env python3
"""Run-x-11: Evaluate frozen CL-7B SVM+AST across T=0.2/0.4/0.6.

Inputs (read-only):
  * Original 450-pair test_.csv, original pair manifest and fitted SVM.
  * run-x-06 source provenance, run-x-08 T=0.2 generation reference.
  * run-x-10 common-valid CSVs and extraction metadata for all 3 temperatures.
  * Original tree-sitter AST representation and CodeT5+ embedding code.

Outputs (output directory only):
  * Provenance/preflight audit, original cached and fresh 450-pair baseline.
  * CodeT5+ 256-dimensional embedding cache with SHA-256 provenance.
  * 370-pair predictions, three AUROCs and two matched 20,000-replicate CIs.
  * No code generation, SVM fitting, tuning, or optional subgroup analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
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
TAGS = ("t02", "t04", "t06")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    sha = hashlib.sha256()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def digest_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    raise ValueError("Unexpected row index suffix: " + str(idx))


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--run06-dir", type=Path)
    p.add_argument("--run08-dir", type=Path)
    p.add_argument("--run10-dir", type=Path)
    p.add_argument("--model-file", type=Path)
    p.add_argument("--seed", type=int, default=20260723, help="Generation seed from run-x-10")
    p.add_argument("--stat-seed", type=int, default=20260723, help="Bootstrap random seed")
    p.add_argument("--phase", choices=("preflight", "run"), default="preflight")
    p.add_argument("--embedding-max-len", type=int, default=2048)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--bootstrap", type=int, default=20000)
    p.add_argument("--device", default="cuda")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--allow-other-python", action="store_true", help="Offline verification only; not for research production")
    return p.parse_args()


def source_paths(a):
    root = a.repo_root.resolve()
    return {
        "test": root / "src/ml_embeddings/data_codesearchnet/splits" / EXPERIMENT / DATASET / "test_.csv",
        "manifest": root / "src/ml_embeddings/data_codesearchnet/splits" / EXPERIMENT / "complexity_stratified_pair_manifest.csv",
        "original": root / "src/code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/validsyntax_4500_complexity" / (DATASET + ".csv"),
        "pickle": (a.model_file or root / "src/ml_embeddings/data_codesearchnet/models" / EXPERIMENT / MODEL_FILE).resolve(),
        "run06": (a.run06_dir or root / "src/output/run-x-06/20261012-154334-48074").resolve(),
        "run08": (a.run08_dir or root / "src/output/run-x-08/20261012-224115-68731").resolve(),
        "run10": (a.run10_dir or root / "src/output/run-x-10/20261013-000056-94778").resolve(),
        "ast_src": root / "src/code-analyzer-tree-sitter/tree_sitter_ast_python.py",
        "grammar": root / "src/code-analyzer-tree-sitter/build/my-languages.so",
        "embed_src": root / "src/ml_embeddings/generate_embeddings.py",
        "validator": root / "src/code-generation/find_validsyntax_mgc.py",
    }


def verify_hashes(directory, expected, files):
    for key, filename in files.items():
        path = directory / filename
        require(path.is_file(), f"Missing reference: {path}")
        require(expected[key] == digest(path), f"SHA-256 mismatch: {path}")


def preflight(a, p):
    require(sys.version_info[:2] == (3, 11) or a.allow_other_python, "Python 3.11 is required")
    require(a.embedding_max_len == 2048 and a.batch_size > 0 and a.bootstrap > 0, "Invalid evaluation configuration")
    for key in ("test", "manifest", "original", "pickle", "ast_src", "grammar", "embed_src", "validator"):
        require(p[key].is_file(), f"Missing required source {key}: {p[key]}")
    require(digest(p["pickle"]) == MODEL_SHA, "Historical fitted SVM SHA-256 mismatch")

    test = pd.read_csv(p["test"], keep_default_na=False)
    manifest = pd.read_csv(p["manifest"])
    original = pd.read_csv(p["original"], keep_default_na=False)
    require(len(test) == 900 and len(manifest) == 4500 and len(original) == 9000, "Original dataset size mismatch")
    require(test.idx.is_unique and manifest.pair_id.is_unique and original.idx.is_unique, "Duplicate original row IDs")
    test_ids = set(manifest.loc[manifest.split == "test", "pair_id"])
    require(len(test_ids) == 450 and set(test.idx.map(pair_id)) == test_ids, "Original test split mismatch")
    require(all(f"ast_{j}" in test.columns for j in range(256)), "Missing cached AST embedding columns")
    require({"code", "ast", "actual label"} <= set(test.columns), "Original test representation missing")
    reference_code = original.set_index("idx")
    for row in test.itertuples(index=False):
        require(str(row.code) == str(reference_code.at[row.idx, "code"]), f"Original test code drift: {row.idx}")
    require(set(test["actual label"].astype(int)) == {0, 1}, "Unexpected target labels")

    run06, run08, run10 = p["run06"], p["run08"], p["run10"]
    conf06 = json.loads((run06 / "experiment_config.json").read_text())
    sum06 = json.loads((run06 / "full_summary.json").read_text())
    conf08 = json.loads((run08 / "experiment_config.json").read_text())
    sum08 = json.loads((run08 / "controlled_summary.json").read_text())
    conf10 = json.loads((run10 / "experiment_config.json").read_text())
    sum10 = json.loads((run10 / "multitemp_summary.json").read_text())
    man10 = json.loads((run10 / "input_manifest.json").read_text())
    require(sum06["status"] == sum08["status"] == sum10["status"] == "PASS", "Upstream experiment not PASS")
    require(sum06["generated"] == 4500 and sum10["generated_new"] == 900 and sum10["reused_t02"] == 450,
            "Upstream generation sizes changed")
    require(conf06["model"] == conf08["model"] == conf10["model"] == "codellama/CodeLlama-7b-hf", "Generator changed")
    require(conf06["eos_ids"] == conf08["eos_ids"] == conf10["eos_ids"] == [2], "EOS differs")
    require(conf06["prompt_max_tokens"] == conf08["prompt_max_tokens"] == conf10["prompt_max_tokens"] == 128,
            "Prompt limit differs")
    require(conf06["max_new_tokens"] == conf08["max_new_tokens"] == conf10["max_new_tokens"] == 512,
            "Generation limit differs")
    require(conf08["temperature"] == 0.2 and conf10["temperatures"] == {"t04": 0.4, "t06": 0.6},
            "Controlled temperature configuration differs")
    require(conf08["top_p"] == conf10["top_p"] == 0.95 and conf08["top_k"] == conf10["top_k"] == 50,
            "Sampling parameters differ")
    require(conf08["do_sample"] is True and conf10["do_sample"] is True, "Sampling policy mismatch")
    require(conf10["seed"] == sum10["seed"] == man10["seed"] == a.seed, "Generation seed mismatch")
    require(sum10["temperatures"] == {"t02": 0.2, "t04": 0.4, "t06": 0.6}, "Expected 3 temperature levels")
    require(not sum10["source_data_modified"] and not sum10["invalid_backfilled"], "Source altered or backfilled")

    source_checks = {
        "run06_config_sha256": (run06 / "experiment_config.json"),
        "run06_prepared_sha256": (run06 / "full_prepared.jsonl"),
        "run06_extracted_sha256": (run06 / "extracted_functions.jsonl"),
        "run06_summary_sha256": (run06 / "full_summary.json"),
        "original_csv_sha256": p["original"],
        "split_manifest_sha256": p["manifest"],
        "validator_sha256": p["validator"],
    }
    for key, path in source_checks.items():
        require(path.is_file() and digest(path) == conf10["run06_source_hashes"][key]
                == sum10["input_hashes"][key] == man10["run06_source_hashes"][key],
                f"run-x-06 reference SHA mismatch: {key}")
    reference_08 = {
        "experiment_config.json": "experiment_config.json",
        "input_manifest.json": "input_manifest.json",
        f"seed{a.seed}_summary.json": f"seed{a.seed}_summary.json",
        "test_prepared.jsonl": "test_prepared.jsonl",
        f"seed{a.seed}_generation.jsonl": f"seed{a.seed}_generation.jsonl",
        f"seed{a.seed}_extracted_functions.jsonl": f"seed{a.seed}_extracted_functions.jsonl",
        f"seed{a.seed}_comparison.csv": f"seed{a.seed}_comparison.csv",
        f"seed{a.seed}_t02_valid_pairs.csv": f"seed{a.seed}_t02_valid_pairs.csv",
    }
    verify_hashes(run08, conf10["run08_source_hashes"], reference_08)
    for key in reference_08:
        require(conf10["run08_source_hashes"][key] == sum10["t02_reference_hashes"][key]
                == man10["run08_source_hashes"][key], f"run-x-08 manifest SHA mismatch: {key}")
    prepared_path = run10 / "test_prepared.jsonl"
    require(digest(prepared_path) == man10["test_prepared_file_sha256"],
            "run-x-10 prepared test file SHA mismatch")
    prepared_items = [json.loads(line) for line in prepared_path.read_text().splitlines() if line.strip()]
    canonical = json.dumps(prepared_items, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    require(digest_text(canonical) == conf10["test_prepared_sha256"],
            "run-x-10 prepared test logical content differs")
    require(man10["test_prepared_file_sha256"] == digest(run08 / "test_prepared.jsonl"),
            "run-x-08 authoritative prompt file changed")
    require(digest(run10 / "test_selection.csv") == digest(run08 / "test_selection.csv"),
            "run-x-10 test assignment differs from run-x-08")

    prefix = f"seed{a.seed}_"
    summary_by_temp = {}
    extracted_by_temp = {}
    for tag in ("t04", "t06"):
        s = json.loads((run10 / (prefix + tag + "_summary.json")).read_text())
        require(s["status"] == "PASS" and s["seed"] == a.seed, f"{tag} generation status differs")
        summary_by_temp[tag] = s
        items = [json.loads(line) for line in (run10 / (prefix + tag + "_extracted_functions.jsonl")).read_text().splitlines() if line.strip()]
        require(len(items) == 450 and len({x["pair_id"] for x in items}) == 450, f"{tag} extraction record count mismatch")
        extracted_by_temp[tag] = {x["pair_id"]: x for x in items}
    extract_02 = [json.loads(line) for line in (run08 / (prefix + "extracted_functions.jsonl")).read_text().splitlines() if line.strip()]
    require(len(extract_02) == 450, "T=0.2 extracted functions missing")
    extracted_by_temp["t02"] = {x["pair_id"]: x for x in extract_02}
    require(len(extracted_by_temp["t02"]) == 450, "Duplicated T=0.2 records")

    comparison = pd.read_csv(run10 / (prefix + "comparison.csv"), keep_default_na=False)
    ids_csv = pd.read_csv(run10 / (prefix + "common_ids.csv"), keep_default_na=False)
    require(len(comparison) == 450 and comparison.pair_id.is_unique and set(comparison.pair_id) == test_ids,
            "run-x-10 selection ID mismatch")
    require(len(ids_csv) == sum10["common_valid_all3"] == 370 and ids_csv.pair_id.is_unique,
            "Common-valid 370 ID count mismatch")
    ids = sorted(ids_csv.pair_id.tolist())
    cmp = comparison.set_index("pair_id")
    require(set(ids) == set(cmp.index[cmp.common_valid_all3]), "Selection flags differ from common IDs")
    require(sum10["valid_by_temperature"] == {"t02": 404, "t04": 407, "t06": 421},
            "Reference seed validity counts changed")
    for tag in TAGS:
        require(int(comparison[f"{tag}_valid"].sum()) == sum10["valid_by_temperature"][tag],
                f"{tag} validity count does not match summary")
    require(int(comparison["common_warning_free_all3"].sum()) == sum10["common_warning_free_all3"] == 300,
            "Warning-free count changed")
    require((comparison.seed == a.seed).all() and (comparison.split == "test").all(), "Bad seed or split")

    src_test = test.set_index("idx")
    pair_frames = {}
    metadata = []
    for tag in TAGS:
        csv_path = run10 / (prefix + f"common_{tag}_pairs.csv")
        require(csv_path.is_file(), f"Missing common valid CSV: {csv_path}")
        frame = pd.read_csv(csv_path, keep_default_na=False)
        require(len(frame) == 740 and frame.idx.is_unique and set(frame.idx) == {pid + suffix for pid in ids for suffix in ("_human", "_lm")},
                f"{tag} common-valid rows do not match IDs")
        pair_frames[tag] = frame.set_index("idx")
    for pid in ids:
        row = cmp.loc[pid]
        require(all(bool(row[f"{tag}_valid"]) for tag in TAGS), f"Common-valid false flag: {pid}")
        require(bool(row.common_valid_all3), f"Missing common flag: {pid}")
        for tag in TAGS:
            require(extracted_by_temp[tag][pid]["status"] == "VALID", f"Invalid AGC in common set: {tag} {pid}")
            agc = str(pair_frames[tag].at[pid + "_lm", "code"])
            expected_sha = row[f"{tag}_agc_sha256"]
            require(digest_text(agc) == expected_sha == extracted_by_temp[tag][pid]["extracted_agc_sha256"],
                    f"AGC code hash mismatch: {tag} {pid}")
            require(agc == extracted_by_temp[tag][pid]["extracted_agc_code"], f"AGC source mismatch: {tag} {pid}")
            require(pair_frames[tag].at[pid + "_lm", "label"] == "lm", f"AGC label mismatch: {tag} {pid}")
            require(pair_frames[tag].at[pid + "_human", "label"] == "human", f"HWC label mismatch: {tag} {pid}")
            hwc = str(pair_frames[tag].at[pid + "_human", "code"])
            require(hwc == str(src_test.at[pid + "_human", "code"]), f"HWC code differs from original test: {tag} {pid}")
            require(int(src_test.at[pid + "_human", "actual label"]) == 1 and int(src_test.at[pid + "_lm", "actual label"]) == 0,
                    f"Original label assignment changed: {pid}")
        require(all(pair_frames[tag].at[pid + "_human", "code"] == pair_frames["t02"].at[pid + "_human", "code"] for tag in TAGS),
                f"HWC changed by temperature: {pid}")
        metadata.append({"pair_id": pid, "complexity_score": float(row.complexity_score),
                         "complexity_block": int(row.complexity_block),
                         "warning_any": any(bool(row[f"{tag}_warning"]) for tag in TAGS)})
    meta = pd.DataFrame(metadata)
    require(len(meta) == 370 and meta.pair_id.is_unique, "Matched procedure metadata invalid")
    require(int((~meta.warning_any).sum()) == 300, "Matched warning-free count differs")
    manifest_ref = manifest.set_index("pair_id")
    for row in meta.itertuples():
        require(np.isclose(row.complexity_score, float(manifest_ref.at[row.pair_id, "complexity_score"])),
                f"Complexity score drift: {row.pair_id}")
        require(row.complexity_block == int(manifest_ref.at[row.pair_id, "complexity_block"]),
                f"Complexity block drift: {row.pair_id}")

    input_hashes = {"test": digest(p["test"]), "manifest": digest(p["manifest"]), "original": digest(p["original"]),
                    "model": digest(p["pickle"]), "ast_source": digest(p["ast_src"]),
                    "embedding_source": digest(p["embed_src"]), "run10_summary": digest(run10 / "multitemp_summary.json"),
                    "run10_comparison": digest(run10 / (prefix + "comparison.csv")),
                    "run10_common_ids": digest(run10 / (prefix + "common_ids.csv"))}
    input_hashes.update({f"common_{tag}": digest(run10 / (prefix + f"common_{tag}_pairs.csv")) for tag in TAGS})
    info = {"status": "PASS", "experiment": "run-x-11", "seed": a.seed, "test_pairs": 450,
            "common_valid_pairs": len(ids), "common_warning_free": 300,
            "valid_by_temperature": sum10["valid_by_temperature"], "model_sha256": MODEL_SHA,
            "input_sha256": input_hashes, "generation_settings": {"eos": [2], "max_new_tokens": 512,
            "prompt_cap": 128, "top_p": 0.95, "top_k": 50}}
    print(f"[PREFLIGHT] PASS: original test=450; T02={sum10['valid_by_temperature']['t02']} T04={sum10['valid_by_temperature']['t04']} T06={sum10['valid_by_temperature']['t06']}; common={len(ids)}")
    print("[PREFLIGHT] Exact paper SVM, T=0.2/T=0.4/T=0.6 source hashes, code and split IDs verified")
    return test, ids, pair_frames, meta, info


def unpack_classifier(model_path):
    # The pickle is a trusted, locally generated research artifact.
    with open(model_path, "rb") as file:
        models = pickle.load(file)
    require(MODEL_KEY in models, f"Selected AST model key missing: {MODEL_KEY}")
    entry = models[MODEL_KEY]
    clf = entry[0] if isinstance(entry, (list, tuple)) else entry
    require(getattr(clf, "n_features_in_", None) == 256, "SVM input dimensionality changed")
    require(list(clf.classes_) == [0, 1], "Expected classes [0,1] with human positive")
    return clf


def scores_for(clf, features):
    x = np.asarray(features, dtype=np.float64)
    prediction = clf.predict(x)
    if hasattr(clf, "predict_proba"):
        try:
            score = clf.predict_proba(x)[:, list(clf.classes_).index(1)]
            return np.asarray(score, float), np.asarray(prediction, int), "proba"
        except Exception:
            pass
    require(hasattr(clf, "decision_function"), "Selected classifier lacks continuous scores")
    return np.asarray(clf.decision_function(x), float).ravel(), np.asarray(prediction, int), "decision"


def build_ast(test, ids, pair_frames, p, out_dir):
    from tree_sitter import Language, Parser
    sys.path.insert(0, str(p["ast_src"].parent))
    from tree_sitter_ast_python import F
    parser = Parser()
    parser.set_language(Language(str(p["grammar"]), "python"))

    def sequence(code):
        raw = code.encode("utf-8")
        tree = parser.parse(raw)
        require(not tree.root_node.has_error, "Tree-sitter Python parsing failed")
        return " ".join(F(tree.root_node, raw))

    reference = []
    for row in test.itertuples(index=False):
        calculated = sequence(str(row.code))
        require(calculated == row.ast, f"Historical AST reference mismatch: {row.idx}")
        reference.append({"idx": row.idx, "reference_matches": True})
    pd.DataFrame(reference).to_csv(out_dir / "ast_reference_qc.csv", index=False)
    print("[AST] Historical AST reference 900/900 verified")
    new_ast = {}
    for tag in TAGS:
        indexed = pair_frames[tag]
        new_ast[tag] = [sequence(str(indexed.at[pid + "_lm", "code"])) for pid in ids]
    print(f"[AST] {len(ids)} AGC AST sequences per temperature verified")
    return new_ast


def embedding_helpers(path):
    spec = importlib.util.spec_from_file_location("historical_codet5p_embeddings", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.MODEL_ID == "Salesforce/codet5p-110m-embedding" and module.EMBED_DIM == 256,
            "Historical CodeT5+ encoder changed")
    return module


def make_embeddings(a, p, test, ids, meta, new_ast, preflight_info, output_dir):
    cache = output_dir / "ast_embeddings.npz"
    provenance = output_dir / "embedding_provenance.json"
    input_digest = hashlib.sha256(json.dumps(preflight_info["input_sha256"], sort_keys=True).encode()).hexdigest()
    if a.resume and cache.is_file() and provenance.is_file():
        record = json.loads(provenance.read_text())
        require(record["input_digest"] == input_digest and record["cache_sha256"] == digest(cache),
                "Resume cache inputs or bytes changed")
        with np.load(cache) as arrays:
            checked = {k: arrays[k].copy() for k in arrays.files}
        require(checked["original"].shape == (900, 256), "Resume original embedding shape differs")
        for tag in TAGS:
            require(checked[tag].shape == (len(ids), 256), f"Resume {tag} embeddings shape differs")
        require(all(np.isfinite(x).all() for x in checked.values()), "Nonfinite resume embeddings")
        print("[EMBED] SHA-256 verified embeddings reused")
        return checked

    import torch
    require(a.device != "cuda" or torch.cuda.is_available(), "CUDA is unavailable")
    helper = embedding_helpers(p["embed_src"])
    tokenizer, model = helper.load_model(a.device)
    encoded = {"original": helper.embed_batch(test.ast.astype(str).tolist(), tokenizer, model, a.device,
                                                  batch_size=a.batch_size, max_len=2048, desc="original AST 900")}
    for tag in TAGS:
        encoded[tag] = helper.embed_batch(new_ast[tag], tokenizer, model, a.device,
                                          batch_size=a.batch_size, max_len=2048, desc=tag + " AST")
    require(encoded["original"].shape == (900, 256), "Original embedded reference size incorrect")
    for tag in TAGS:
        require(encoded[tag].shape == (len(ids), 256), f"{tag} embedded output size incorrect")
    require(all(np.isfinite(x).all() for x in encoded.values()), "Nonfinite CodeT5+ embeddings")
    np.savez_compressed(cache, **encoded)
    json_write(provenance, {"input_digest": input_digest, "cache_sha256": digest(cache),
                            "embedding_model": helper.MODEL_ID, "max_len": 2048, "batch_size": a.batch_size,
                            "device": a.device, "shapes": {k: list(v.shape) for k, v in encoded.items()},
                            "reused_historical_embedding_implementation": True})
    print("[EMBED] Saved original + three temperature CodeT5+ AST embeddings")
    return encoded


def auc_from_balanced_scores(hwc, agc):
    # Midrank AUROC, equivalent to sklearn's roc_auc_score for balanced labels.
    n = len(hwc)
    require(len(agc) == n and n > 0, "Paired bootstrap requires balanced procedure pairs")
    scores = np.concatenate([hwc, agc])
    labels = np.concatenate([np.ones(n, dtype=int), np.zeros(n, dtype=int)])
    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    starts = np.r_[0, np.flatnonzero(sorted_scores[1:] != sorted_scores[:-1]) + 1]
    ends = np.r_[starts[1:], 2 * n]
    positive_counts = np.add.reduceat(sorted_labels, starts)
    rank_sum = np.dot((starts + 1 + ends) / 2.0, positive_counts)
    return float((rank_sum - n * (n + 1) / 2.0) / (n * n))


def bootstrap_three_conditions(hwc, agc_by_tag, repeats, rng_seed):
    # Resample original procedure IDs, keeping all four scores within a pair.
    n = len(hwc)
    random = np.random.default_rng(rng_seed)
    results = np.empty((repeats, 5), dtype=np.float64)
    for i in range(repeats):
        selection = random.integers(0, n, n)
        values = [auc_from_balanced_scores(hwc[selection], agc_by_tag[tag][selection]) for tag in TAGS]
        results[i, :] = values[0], values[1], values[2], values[1] - values[0], values[2] - values[0]
        if (i + 1) % 5000 == 0:
            print(f"[BOOTSTRAP] {i + 1}/{repeats}")
    return results


def execute(a, p, test, ids, frames, meta, info):
    out = a.output_dir
    out.mkdir(parents=True, exist_ok=True)
    json_write(out / "preflight_summary.json", info)
    classifier = unpack_classifier(p["pickle"])
    original_features = test[[f"ast_{j}" for j in range(256)]].to_numpy()
    cached_score, cached_prediction, mode = scores_for(classifier, original_features)
    baseline_auc = float(roc_auc_score(test["actual label"].astype(int), cached_score))
    require(abs(baseline_auc - BASELINE_TARGET) <= 0.000051,
            f"Original SVM 450-pair baseline AUROC did not reproduce: {baseline_auc}")
    json_write(out / "baseline_cached_summary.json", {"original_test_pairs": 450,
                "paper_baseline_auroc": BASELINE_TARGET, "cached_auroc": baseline_auc,
                "model_sha256": MODEL_SHA, "score_mode": mode})
    print(f"[BASELINE] Original cached 450-pair AUROC={baseline_auc:.8f}, mode={mode}")

    sequences = build_ast(test, ids, frames, p, out)
    emb = make_embeddings(a, p, test, ids, meta, sequences, info, out)
    fresh_score, fresh_prediction, fresh_mode = scores_for(classifier, emb["original"])
    fresh_auc = float(roc_auc_score(test["actual label"].astype(int), fresh_score))
    score_drift = float(np.max(np.abs(fresh_score - cached_score)))
    require(fresh_mode == mode and abs(fresh_auc - baseline_auc) <= 0.005 and score_drift <= 0.001,
            f"Historical cached vs fresh SVM score mismatch: auc={fresh_auc} delta={score_drift}")
    baseline_rows = test[["idx", "actual label"]].copy()
    baseline_rows["score_cached"] = cached_score
    baseline_rows["score_fresh"] = fresh_score
    baseline_rows["prediction_cached"] = cached_prediction
    baseline_rows["prediction_fresh"] = fresh_prediction
    baseline_rows.to_csv(out / "baseline_predictions.csv", index=False)
    print(f"[BASELINE] Fresh 450-pair AUROC={fresh_auc:.8f}; max_score_delta={score_drift:.6g}")

    index_ref = {idx: pos for pos, idx in enumerate(test.idx)}
    tag_score = {}
    tag_prediction = {}
    for tag in TAGS:
        tag_score[tag], tag_prediction[tag], tag_mode = scores_for(classifier, emb[tag])
        require(tag_mode == mode, f"Unexpected scoring mode for {tag}")
    records = []
    for j, pid in enumerate(ids):
        details = meta.iloc[j]
        for label, suffix in ((1, "human"), (0, "lm")):
            row_id = pid + "_" + suffix
            pos = index_ref[row_id]
            item = {"seed": a.seed, "pair_id": pid, "idx": row_id, "label": label,
                    "complexity_score": float(details.complexity_score),
                    "complexity_block": int(details.complexity_block)}
            for tag in TAGS:
                item["score_" + tag] = float(fresh_score[pos] if label == 1 else tag_score[tag][j])
                item["prediction_" + tag] = int(fresh_prediction[pos] if label == 1 else tag_prediction[tag][j])
            records.append(item)
    predicted = pd.DataFrame(records)
    require(len(predicted) == 740 and predicted.idx.is_unique, "Unexpected prediction rows")
    human_rows = predicted[predicted.label == 1]
    for tag in ("t04", "t06"):
        require(np.array_equal(human_rows["score_t02"], human_rows["score_" + tag]),
                "Human-code score changed with temperature")
    predicted.to_csv(out / "paired_predictions.csv", index=False)
    meta.to_csv(out / "matched_pair_metadata.csv", index=False)

    aucs = {tag: float(roc_auc_score(predicted.label, predicted["score_" + tag])) for tag in TAGS}
    require(all(0 <= auc <= 1 for auc in aucs.values()), "Invalid AUROC result")
    selected = predicted.set_index(["pair_id", "label"])
    hwc_scores = np.array([selected.loc[(pid, 1), "score_t02"] for pid in ids])
    agc_scores = {tag: np.array([selected.loc[(pid, 0), "score_" + tag] for pid in ids]) for tag in TAGS}
    require(all(abs(auc_from_balanced_scores(hwc_scores, agc_scores[tag]) - aucs[tag]) <= 1e-12 for tag in TAGS),
            "Independent midrank AUROC disagrees with sklearn")
    replicates = bootstrap_three_conditions(hwc_scores, agc_scores, a.bootstrap, a.stat_seed)
    pd.DataFrame(replicates, columns=["t02_auroc", "t04_auroc", "t06_auroc", "delta_t04_minus_t02", "delta_t06_minus_t02"]).to_csv(
        out / "bootstrap_replicates.csv", index=False)
    primary = []
    for tag in TAGS:
        row = {"temperature": {"t02": 0.2, "t04": 0.4, "t06": 0.6}[tag], "tag": tag,
               "common_valid_pairs": len(ids), "auroc": aucs[tag], "delta_vs_t02": aucs[tag] - aucs["t02"]}
        if tag == "t02":
            row.update({"ci95_delta_low": None, "ci95_delta_high": None})
        else:
            col = 3 if tag == "t04" else 4
            ci = np.quantile(replicates[:, col], [0.025, 0.975]).tolist()
            row.update({"ci95_delta_low": ci[0], "ci95_delta_high": ci[1]})
        primary.append(row)
    pd.DataFrame(primary).to_csv(out / "temperature_auroc.csv", index=False)
    result = {"experiment": "run-x-11", "version": "v1", "status": "PASS",
              "generation_seed": a.seed, "bootstrap_seed": a.stat_seed, "bootstrap_replicates": a.bootstrap,
              "baseline_450_cached_auroc": baseline_auc, "baseline_450_fresh_auroc": fresh_auc,
              "baseline_max_score_drift": score_drift, "score_mode": mode,
              "matched_test_pairs": len(ids), "valid_by_temperature": info["valid_by_temperature"],
              "comparison_table": primary, "preflight": info,
              "retraining": False, "model_reselection": False, "agc_generation": False,
              "environment": {"python": sys.version.split()[0], "numpy": np.__version__, "torch": __import__("torch").__version__,
                              "platform": platform.platform()},
              "limitations": ["One stochastic generation seed only; inference is conditional on its outputs.",
                              "Common-valid inclusion can vary with procedure complexity.",
                              "AST validity does not prove functional correctness."]}
    json_write(out / "evaluation_summary.json", result)
    lines = ["run-x-11 | T=0.2 vs T=0.4 vs T=0.6 CodeLlama detector AUROC | PASS",
             f"Original baseline 450: cached={baseline_auc:.8f} fresh={fresh_auc:.8f}",
             f"Generation seed={a.seed} common-valid={len(ids)}/450; {a.bootstrap} pair-cluster bootstrap resamples"]
    for row in primary:
        if row["tag"] == "t02":
            lines.append(f"T=0.2 AUROC={row['auroc']:.6f} (reference)")
        else:
            lines.append(f"T={row['temperature']:.1f} AUROC={row['auroc']:.6f} delta_vs_T02={row['delta_vs_t02']:+.6f} CI95=[{row['ci95_delta_low']:.6f}, {row['ci95_delta_high']:.6f}]")
    lines.append("No subgroup analysis, model retraining, model selection or additional source generation.")
    (out / "findings.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    a = parse_args()
    p = source_paths(a)
    print("=================================================================")
    print(f"run-x-11 | Three-temperature SVM+AST AUROC | phase={a.phase}")
    print(f"Python={sys.version.split()[0]} device={a.device} max_len={a.embedding_max_len} bootstrap={a.bootstrap}")
    print("Source inputs=READ_ONLY; no retraining, reselection, or code generation")
    print("=================================================================")
    t, ids, frames, meta, info = preflight(a, p)
    if a.phase == "preflight":
        print("[DRY-RUN] PASS; no unpickling, model loading, GPU inference, or output directory creation")
        return
    execute(a, p, t, ids, frames, meta, info)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[ERROR]", type(e).__name__ + ":", e, file=sys.stderr)
        sys.exit(1)
