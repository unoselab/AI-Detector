"""
agc_detector.py
===============

Per-block AI-generated-code (AGC) detector.

Takes a raw `.py` file, splits it into top-level function/class blocks,
generates an AST sequence and a CodeT5+ embedding for each block on the
fly, runs a pre-trained ML classifier per block, and prints HWC / AGC
labels with confidence.

Pipeline-from-scratch
---------------------
This script intentionally does NOT depend on the precomputed AST CSVs or
embedding CSVs in `data_codesearchnet/`. It re-runs the full sequence per
block (tree-sitter parse -> F() AST traversal -> CodeT5+ embedding) so it
can be applied to any .py file, not just rows that already exist in the
training corpus.

The trained classifier pickle (from hyperparameter_tuning.py) is the only
persistent artifact the detector loads.

Block unit
----------
Top-level function_definition / class_definition nodes (including
decorated and async variants) per tree-sitter. Module-level statements
(imports, constants, scripts) are skipped: they're not what the
classifier was trained on.

Ground-truth comparison (optional)
----------------------------------
If a sibling <input>.labels.tsv exists (produced by build_mixed_samples.py),
the detector reads it and reports per-block correctness + summary accuracy.
Marker lines `# === BLOCK N (label=..., ...) ===` are stripped from the
input BEFORE parsing so the detector cannot peek at the truth.

Usage
-----
    python src/app/agc_detector.py \\
        --input src/app/mixed_samples/mixed_sample_003.py

    python src/app/agc_detector.py \\
        --input my_file.py \\
        --model-pickle path/to/tuned_models_..._lr_....pkl \\
        --embedding ast --threshold 0.42
"""

import argparse
import csv
import glob
import os
import pickle
import re
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from tree_sitter import Language, Parser


DEFAULT_TREE_SITTER_LIB = "src/code-analyzer-tree-sitter/build/my-languages.so"
DEFAULT_AST_HELPER_DIR  = "src/code-analyzer-tree-sitter"
DEFAULT_MODEL_GLOB      = (
    "src/ml_embeddings/data_codesearchnet/models/"
    "starcoder2-15b-instruct-v0.1/tuned_models_*_svm_*.pkl"
)
EMBEDDING_MODEL_ID = "Salesforce/codet5p-110m-embedding"
MAX_LEN            = 512
SEP                = " </s> "

BLOCK_MARKER_RE = re.compile(
    r"^\s*#\s*===\s*BLOCK\s+\d+\s*\(.*?\)\s*===\s*$", re.MULTILINE
)

LABEL_MAP    = {"human": 1, "lm": 0}
LABEL_REVMAP = {v: k for k, v in LABEL_MAP.items()}


# -----------------------------------------------------------------------------
# Tree-sitter
# -----------------------------------------------------------------------------
def load_parser_and_F(lib_path: str, helper_dir: str):
    if not os.path.exists(lib_path):
        raise SystemExit(
            f"[ERROR] tree-sitter library not built: {lib_path}\n"
            "        Run `python tree-sitter-test.py` in code-analyzer-tree-sitter/"
        )
    lang = Language(lib_path, "python")
    parser = Parser()
    parser.set_language(lang)

    helper_dir_abs = os.path.abspath(helper_dir)
    if helper_dir_abs not in sys.path:
        sys.path.insert(0, helper_dir_abs)
    from tree_sitter_ast_python import F  # noqa: E402
    return parser, F


def strip_block_markers(text: str) -> str:
    return BLOCK_MARKER_RE.sub("", text)


def _node_name(node, source: str) -> Optional[str]:
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return source[name_node.start_byte:name_node.end_byte]
    return None


def extract_blocks(source: str, parser) -> List[Dict]:
    """One dict per top-level def/class with kind, name, start_line, end_line, code."""
    tree = parser.parse(bytes(source, "utf8"))
    root = tree.root_node

    blocks: List[Dict] = []
    for child in root.children:
        target = None
        if child.type in ("function_definition", "class_definition"):
            target = child
        elif child.type == "decorated_definition":
            for c in child.children:
                if c.type in ("function_definition", "class_definition"):
                    target = c
                    break
        elif child.type == "async_function_definition":
            target = child

        if target is None:
            continue

        kind = "class_definition" if target.type == "class_definition" else "function_definition"
        name = _node_name(target, source) or "<anon>"
        outer = child  # include decorators
        code = source[outer.start_byte:outer.end_byte]
        start_line = outer.start_point[0] + 1
        end_line   = outer.end_point[0]   + 1

        blocks.append({
            "kind":       kind,
            "name":       name,
            "start_line": start_line,
            "end_line":   end_line,
            "code":       code,
        })
    return blocks


def generate_ast_sequence(code: str, parser, F_fn) -> str:
    code_b = bytes(code, "utf8")
    tree = parser.parse(code_b)
    return " ".join(F_fn(tree.root_node, code_b))


# -----------------------------------------------------------------------------
# Embedder
# -----------------------------------------------------------------------------
def load_embedder(device: str):
    from transformers import AutoModel, AutoTokenizer
    print(f"Loading {EMBEDDING_MODEL_ID} on {device} ...")
    tok = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_ID, trust_remote_code=True)
    model = AutoModel.from_pretrained(EMBEDDING_MODEL_ID, trust_remote_code=True).to(device).eval()
    return tok, model


@torch.no_grad()
def embed_text(text: str, tok, model, device) -> np.ndarray:
    enc = tok(text, return_tensors="pt", padding=True,
              truncation=True, max_length=MAX_LEN).to(device)
    out = model(**enc)
    if isinstance(out, (tuple, list)):
        vec = out[0]
    elif hasattr(out, "last_hidden_state"):
        attn = enc["attention_mask"].unsqueeze(-1).float()
        vec = (out.last_hidden_state * attn).sum(1) / attn.sum(1)
    else:
        vec = out
    arr = vec.cpu().numpy()
    return arr[0] if arr.ndim == 2 else arr


# -----------------------------------------------------------------------------
# Classifier
# -----------------------------------------------------------------------------
def find_default_classifier(glob_pattern: str) -> str:
    cands = sorted(glob.glob(glob_pattern))
    if not cands:
        raise SystemExit(
            f"[ERROR] no classifier pickles match: {glob_pattern}\n"
            "        Pass --model-pickle explicitly."
        )
    return cands[-1]


def pick_classifier_from_pickle(pickle_path: str, emb_prefix: str):
    """
    The pickle is a dict keyed by `<dataset_folder>` + `<emb_prefix>` (e.g.
    "..._python_merged_2250" + "ast_"). For per-block scoring on a foreign
    file we don't know which dataset's classifier to use, so we pick the
    LARGEST training dataset (by inferred suffix _NNNN) for the requested
    embedding prefix. If no _NNNN suffix is present, the lexicographically
    last key wins (stable tiebreak).
    """
    with open(pickle_path, "rb") as f:
        tuned = pickle.load(f)
    if not tuned:
        raise SystemExit(f"[ERROR] pickle is empty: {pickle_path}")

    keys_for_emb = [k for k in tuned.keys() if k.endswith(emb_prefix)]
    if not keys_for_emb:
        keys_preview = sorted(tuned.keys())[:5]
        raise SystemExit(
            f"[ERROR] no key ends with '{emb_prefix}' in {pickle_path}\n"
            f"        Sample keys: {keys_preview}"
        )

    def size_score(k: str) -> int:
        m = re.search(r"_(\d{3,5})" + re.escape(emb_prefix) + r"$", k)
        return int(m.group(1)) if m else -1

    chosen_key = max(keys_for_emb, key=lambda k: (size_score(k), k))
    clf_list = tuned[chosen_key]
    if isinstance(clf_list, (list, tuple)) and len(clf_list) > 0:
        clf = clf_list[0]
    else:
        clf = clf_list
    return clf, chosen_key


def predict_one(clf, x: np.ndarray, threshold: Optional[float]):
    """
    Return (predicted_label_int, score_for_class_1, score_mode).
    score_mode is 'proba' (in [0,1]) or 'decision' (signed margin).
    threshold is the cutoff above which we call class 1 (human).
    """
    x = x.reshape(1, -1)
    if hasattr(clf, "predict_proba"):
        try:
            proba = clf.predict_proba(x)
            col = list(clf.classes_).index(1)
            s = float(proba[0, col])
            t = 0.5 if threshold is None else float(threshold)
            return (1 if s >= t else 0), s, "proba"
        except Exception:
            pass
    if hasattr(clf, "decision_function"):
        s = float(clf.decision_function(x).ravel()[0])
        t = 0.0 if threshold is None else float(threshold)
        return (1 if s >= t else 0), s, "decision"
    # Fallback: predict() directly with no confidence.
    pred = int(clf.predict(x)[0])
    return pred, float(pred), "discrete"


# -----------------------------------------------------------------------------
# Ground-truth sidecar
# -----------------------------------------------------------------------------
def load_labels_tsv(path: str) -> List[Dict]:
    rows = []
    with open(path, "r") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            rows.append({
                "block_idx":     int(row["block_idx"]),
                "function_name": row["function_name"],
                "start_line":    int(row["start_line"]),
                "end_line":      int(row["end_line"]),
                "label":         row["label"].strip().lower(),
                "source_idx":    int(row.get("source_idx", -1)),
            })
    return rows


def attach_ground_truth(blocks: List[Dict], truth: List[Dict]) -> None:
    """Match by function name + 1-block ordinal. Mutates `blocks` in place."""
    by_name = {}
    for t in truth:
        by_name.setdefault(t["function_name"], []).append(t)

    for b in blocks:
        cands = by_name.get(b["name"], [])
        if cands:
            t = cands.pop(0)
            b["truth_label"] = t["label"]
            b["truth_block_idx"] = t["block_idx"]
        else:
            b["truth_label"] = None
            b["truth_block_idx"] = None


# -----------------------------------------------------------------------------
# Build the input vector for the requested embedding type
# -----------------------------------------------------------------------------
def build_feature_vector(
    block_code: str, embedding: str, parser, F_fn, tok, model, device,
) -> np.ndarray:
    if embedding == "code":
        return embed_text(block_code, tok, model, device)
    if embedding == "ast":
        ast_seq = generate_ast_sequence(block_code, parser, F_fn)
        return embed_text(ast_seq, tok, model, device)
    if embedding == "combined":
        ast_seq = generate_ast_sequence(block_code, parser, F_fn)
        return embed_text(block_code + SEP + ast_seq, tok, model, device)
    raise SystemExit(f"[ERROR] unknown --embedding: {embedding}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--input", required=True,
                    help="Path to a .py file to scan.")
    ap.add_argument("--model-pickle", default=None,
                    help=f"Tuned classifier pickle (default: latest match of {DEFAULT_MODEL_GLOB}).")
    ap.add_argument("--embedding", choices=["ast", "code", "combined"], default="ast",
                    help="Which representation to embed and score (default: ast).")
    ap.add_argument("--threshold", type=float, default=None,
                    help="Decision threshold. Default: 0.5 for proba, 0.0 for SVM decision_function.")
    ap.add_argument("--labels-tsv", default=None,
                    help="Optional ground-truth sidecar (default: <input>.labels.tsv if it exists).")
    ap.add_argument("--tree-sitter-lib", default=DEFAULT_TREE_SITTER_LIB)
    ap.add_argument("--ast-helper-dir",  default=DEFAULT_AST_HELPER_DIR)
    ap.add_argument("--device", default=None,
                    help="cuda | cuda:0 | cpu (auto-detect if unset).")
    ap.add_argument("--out-tsv", default=None,
                    help="If set, write per-block predictions to this TSV.")
    return ap.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(f"[ERROR] input file not found: {args.input}")

    # Locate the ground truth sidecar.
    labels_path = args.labels_tsv
    if labels_path is None:
        cand = args.input.removesuffix(".py") + ".labels.tsv"
        if os.path.exists(cand):
            labels_path = cand
    truth = load_labels_tsv(labels_path) if labels_path else []

    # 1) Read + strip block markers
    with open(args.input, "r") as f:
        raw = f.read()
    source = strip_block_markers(raw)

    # 2) Tree-sitter setup, extract blocks
    parser, F_fn = load_parser_and_F(args.tree_sitter_lib, args.ast_helper_dir)
    blocks = extract_blocks(source, parser)
    if not blocks:
        raise SystemExit(f"[WARN] no top-level def/class found in {args.input}")

    # 3) Attach ground truth if available
    if truth:
        attach_ground_truth(blocks, truth)

    # 4) Embedder
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tok, embed_model = load_embedder(device)

    # 5) Classifier
    model_pickle = args.model_pickle or find_default_classifier(DEFAULT_MODEL_GLOB)
    emb_prefix = f"{args.embedding}_"
    clf, chosen_key = pick_classifier_from_pickle(model_pickle, emb_prefix)
    print(f"Classifier pickle : {model_pickle}")
    print(f"Classifier key    : {chosen_key}")
    print(f"Embedding type    : {args.embedding}")
    print(f"Threshold         : {args.threshold if args.threshold is not None else '(default)'}")
    print()

    # 6) Per-block scoring
    print(f"{'#':>3}  {'lines':<11}  {'kind':<18}  {'name':<28}  "
          f"{'pred':<5}  {'score':>7}  {'TRUTH':<6}  ok")
    print("-" * 100)

    correct = 0
    have_truth = 0
    out_rows = []

    for i, b in enumerate(blocks, start=1):
        x = build_feature_vector(
            b["code"], args.embedding, parser, F_fn,
            tok, embed_model, device,
        )
        pred_int, score, mode = predict_one(clf, x, args.threshold)
        pred_label = LABEL_REVMAP.get(pred_int, str(pred_int))

        truth_label = b.get("truth_label")
        if truth_label is not None:
            have_truth += 1
            ok = (truth_label == pred_label)
            if ok:
                correct += 1
            ok_str = "✓" if ok else "✗"
        else:
            ok_str = "-"
            truth_label = "?"

        lines_str = f"{b['start_line']}-{b['end_line']}"
        print(f"{i:>3}  {lines_str:<11}  {b['kind']:<18}  {b['name'][:28]:<28}  "
              f"{pred_label:<5}  {score:>7.3f}  {truth_label:<6}  {ok_str}")

        out_rows.append({
            "block_idx":   i,
            "start_line":  b["start_line"],
            "end_line":    b["end_line"],
            "kind":        b["kind"],
            "name":        b["name"],
            "pred_label":  pred_label,
            "score":       round(score, 4),
            "score_mode":  mode,
            "truth_label": truth_label,
            "correct":     "" if truth_label == "?" else (1 if truth_label == pred_label else 0),
        })

    print("-" * 100)
    print(f"Blocks scored : {len(blocks)}")
    if have_truth:
        acc = correct / have_truth
        print(f"With ground truth : {have_truth}  | correct: {correct}  | accuracy: {acc:.4f}")
    else:
        print("(no ground truth available; supply --labels-tsv or place <input>.labels.tsv next to <input>)")

    if args.out_tsv:
        with open(args.out_tsv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(out_rows)
        print(f"\nPredictions -> {args.out_tsv}")


if __name__ == "__main__":
    main()