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
    # Single file
    python src/app/agc_detector.py \\
        --input src/app/mixed_samples/mixed_sample_003.py

    # One directory of mixed_sample_*.py
    python src/app/agc_detector.py \\
        --input-dir src/app/mixed_samples_50x6

    # A grid root containing blocks_*/ subdirs (each holds mixed_sample_*.py).
    # Predictions go to <subdir>/predictions/, plus a top-level
    # predictions_summary.csv at the grid root.
    python src/app/agc_detector.py \\
        --input-grid src/app/data_mixed_samples_grid_480

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
DEFAULT_MAX_LEN   = 512   # tokenizer truncation; override with --max-len to
                          # match the classifier's training (e.g. 2048 for the
                          # *_maxlen2048 experiments).
MAX_LEN           = DEFAULT_MAX_LEN
SEP                = " </s> "

BLOCK_MARKER_RE = re.compile(
    r"^[ \t]*#[ \t]*===[ \t]*BLOCK[ \t]+\d+[ \t]*\(.*?\)[ \t]*===[ \t]*(?=\n|$)",
    re.MULTILINE,
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


def _node_text(node, source_bytes: bytes) -> str:
    """
    tree-sitter start_byte/end_byte are byte offsets, not Python string indexes.
    Always slice the UTF-8 bytes first, then decode.

    This matters when a previous block contains non-ASCII text such as Chinese
    docstrings. Slicing the Python string directly with byte offsets corrupts
    later block names and code snippets.
    """
    return source_bytes[node.start_byte:node.end_byte].decode("utf8", errors="replace")


def _node_name(node, source_bytes: bytes) -> Optional[str]:
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return _node_text(name_node, source_bytes)
    return None


def extract_blocks(source: str, parser) -> List[Dict]:
    """One dict per top-level def/class with kind, name, start_line, end_line, code."""
    source_bytes = source.encode("utf8")
    tree = parser.parse(source_bytes)
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
        name = _node_name(target, source_bytes) or "<anon>"
        outer = child  # include decorators if present
        code = _node_text(outer, source_bytes)
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
                "source_idx":    row.get("source_idx", ""),
            })
    return rows


def attach_ground_truth(blocks: List[Dict], truth: List[Dict]) -> None:
    """
    Attach labels from <input>.labels.tsv.

    For synthetic mixed samples, block order is the most reliable key:
      block_idx=1 -> first extracted block
      block_idx=2 -> second extracted block
      ...

    We still keep name-based fallback for non-standard sidecars.
    """
    truth_by_idx = {int(t["block_idx"]): t for t in truth}
    used_truth_ids = set()

    by_name = {}
    for t in truth:
        by_name.setdefault(t["function_name"], []).append(t)

    for i, b in enumerate(blocks, start=1):
        t = truth_by_idx.get(i)

        if t is None:
            cands = by_name.get(b["name"], [])
            while cands and id(cands[0]) in used_truth_ids:
                cands.pop(0)
            t = cands.pop(0) if cands else None

        if t is not None:
            used_truth_ids.add(id(t))
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

    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input",
                     help="Path to one .py file to scan.")
    src.add_argument("--input-dir",
                     help="Directory containing mixed_sample_*.py files to scan.")
    src.add_argument("--input-grid",
                     help="Root containing blocks_*/ subdirs, each with mixed_sample_*.py. "
                          "Predictions land in each subdir's own predictions/ folder.")

    ap.add_argument("--pattern", default="mixed_sample_*.py",
                    help="Filename pattern used with --input-dir and --input-grid.")
    ap.add_argument("--subdir-pattern", default="blocks_*",
                    help="Subdir glob used with --input-grid (default: blocks_*).")
    ap.add_argument("--model-pickle", default=None,
                    help=f"Tuned classifier pickle (default: latest match of {DEFAULT_MODEL_GLOB}).")
    ap.add_argument("--embedding", choices=["ast", "code", "combined"], default="ast",
                    help="Which representation to embed and score (default: ast).")
    ap.add_argument("--max-len", type=int, default=DEFAULT_MAX_LEN,
                    help="Tokenizer truncation length. MUST match what the "
                         "classifier trained on (e.g. 2048 for the *_maxlen2048 "
                         f"experiments). Default: {DEFAULT_MAX_LEN}.")
    ap.add_argument("--threshold", type=float, default=None,
                    help="Decision threshold. Default: 0.5 for proba, 0.0 for SVM decision_function.")
    ap.add_argument("--labels-tsv", default=None,
                    help="Optional ground-truth sidecar. Only valid with --input.")
    ap.add_argument("--tree-sitter-lib", default=DEFAULT_TREE_SITTER_LIB)
    ap.add_argument("--ast-helper-dir",  default=DEFAULT_AST_HELPER_DIR)
    ap.add_argument("--device", default=None,
                    help="cuda | cuda:0 | cpu (auto-detect if unset).")
    ap.add_argument("--out-tsv", default=None,
                    help="Per-block prediction TSV. Only valid with --input.")
    ap.add_argument("--out-dir", default=None,
                    help="Where to write per-input prediction TSVs when using --input-dir.")
    return ap.parse_args()


def resolve_input_files(args) -> List[str]:
    if args.input:
        if not os.path.exists(args.input):
            raise SystemExit(f"[ERROR] input file not found: {args.input}")
        if args.out_dir:
            raise SystemExit("[ERROR] --out-dir is only for --input-dir. Use --out-tsv with --input.")
        return [args.input]

    if args.input_dir:
        if not os.path.isdir(args.input_dir):
            raise SystemExit(f"[ERROR] input directory not found: {args.input_dir}")
        files = sorted(glob.glob(os.path.join(args.input_dir, args.pattern)))
        if not files:
            raise SystemExit(
                f"[ERROR] no input files found: {args.input_dir}/{args.pattern}"
            )
        return files

    # args.input_grid
    if not os.path.isdir(args.input_grid):
        raise SystemExit(f"[ERROR] grid root not found: {args.input_grid}")
    if args.out_dir:
        raise SystemExit(
            "[ERROR] --out-dir is incompatible with --input-grid; "
            "predictions are routed to each subdir's own predictions/ folder."
        )

    subdirs = sorted(
        d for d in glob.glob(os.path.join(args.input_grid, args.subdir_pattern))
        if os.path.isdir(d)
    )
    if not subdirs:
        raise SystemExit(
            f"[ERROR] no subdirs matched: {args.input_grid}/{args.subdir_pattern}"
        )

    files: List[str] = []
    for d in subdirs:
        files.extend(sorted(glob.glob(os.path.join(d, args.pattern))))
    if not files:
        raise SystemExit(
            f"[ERROR] no input files found under {args.input_grid}/{args.subdir_pattern}/{args.pattern}"
        )
    return files


def labels_for_input(input_path: str, explicit_labels_tsv: Optional[str]) -> Optional[str]:
    if explicit_labels_tsv:
        return explicit_labels_tsv

    cand = input_path.removesuffix(".py") + ".labels.tsv"
    return cand if os.path.exists(cand) else None


def out_tsv_for_input(input_path: str, args) -> Optional[str]:
    if args.input:
        return args.out_tsv

    if args.input_grid:
        # Each file's predictions live alongside the file, under <subdir>/predictions/.
        out_dir = os.path.join(os.path.dirname(input_path), "predictions")
    else:
        # --input-dir mode
        out_dir = args.out_dir
        if out_dir is None:
            out_dir = os.path.join(args.input_dir, "predictions")

    os.makedirs(out_dir, exist_ok=True)
    base = os.path.basename(input_path).removesuffix(".py")
    return os.path.join(out_dir, f"{base}.predictions.tsv")


def scan_one_file(
    input_path: str,
    args,
    parser,
    F_fn,
    tok,
    embed_model,
    device,
    clf,
) -> Dict:
    labels_path = labels_for_input(input_path, args.labels_tsv if args.input else None)
    truth = load_labels_tsv(labels_path) if labels_path else []

    with open(input_path, "r") as f:
        raw = f.read()

    source = strip_block_markers(raw)
    blocks = extract_blocks(source, parser)

    if not blocks:
        print(f"[WARN] no top-level def/class found in {input_path}")
        return {
            "input": input_path,
            "blocks": 0,
            "truth": 0,
            "correct": 0,
            "accuracy": "",
        }

    if truth:
        attach_ground_truth(blocks, truth)

    out_tsv = out_tsv_for_input(input_path, args)

    print()
    print("------------------------------------------------------------")
    print(f" scanning : {input_path}")
    print(f" labels   : {labels_path if labels_path else '<none>'}")
    print(f" out tsv  : {out_tsv if out_tsv else '<none>'}")
    print("------------------------------------------------------------")

    print(f"{'#':>3}  {'lines':<11}  {'kind':<18}  {'name':<28}  "
          f"{'pred':<5}  {'score':>7}  {'TRUTH':<6}  ok")
    print("-" * 100)

    correct = 0
    have_truth = 0
    out_rows = []

    for i, b in enumerate(blocks, start=1):
        x = build_feature_vector(
            b["code"], args.embedding, parser, F_fn, tok, embed_model, device
        )
        pred_int, score, mode = predict_one(clf, x, args.threshold)
        pred_label = LABEL_REVMAP.get(pred_int, str(pred_int))

        truth_label = b.get("truth_label")
        if truth_label is not None:
            have_truth += 1
            ok = truth_label == pred_label
            if ok:
                correct += 1
            ok_str = "✓" if ok else "✗"
        else:
            truth_label = "?"
            ok_str = "-"

        lines_str = f"{b['start_line']}-{b['end_line']}"
        print(f"{i:>3}  {lines_str:<11}  {b['kind']:<18}  {b['name'][:28]:<28}  "
              f"{pred_label:<5}  {score:>7.3f}  {truth_label:<6}  {ok_str}")

        out_rows.append({
            "file":        input_path,
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
        acc = ""
        print("(no ground truth available; supply --labels-tsv or place <input>.labels.tsv next to <input>)")

    if out_tsv and out_rows:
        with open(out_tsv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(out_rows)
        print(f"Predictions -> {out_tsv}")

    return {
        "input": input_path,
        "blocks": len(blocks),
        "truth": have_truth,
        "correct": correct,
        "accuracy": acc,
    }


def main():
    args = parse_args()

    # Set the tokenizer truncation length used by embed_text() before any
    # embedding happens. This must match the classifier's training length.
    global MAX_LEN
    MAX_LEN = args.max_len

    input_files = resolve_input_files(args)

    print("============================================================")
    print(" agc_detector.py")
    print(f"   input files : {len(input_files)}")
    if args.input_dir:
        print(f"   input dir   : {args.input_dir}")
        print(f"   pattern     : {args.pattern}")
    if args.input_grid:
        print(f"   input grid  : {args.input_grid}")
        print(f"   subdir glob : {args.subdir_pattern}")
        print(f"   pattern     : {args.pattern}")
    print(f"   embedding   : {args.embedding}")
    print(f"   max len     : {MAX_LEN}")
    print(f"   threshold   : {args.threshold if args.threshold is not None else '(default)'}")
    print("============================================================")
    print()

    parser, F_fn = load_parser_and_F(args.tree_sitter_lib, args.ast_helper_dir)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tok, embed_model = load_embedder(device)

    model_pickle = args.model_pickle or find_default_classifier(DEFAULT_MODEL_GLOB)
    emb_prefix = f"{args.embedding}_"
    clf, chosen_key = pick_classifier_from_pickle(model_pickle, emb_prefix)

    print(f"Classifier pickle : {model_pickle}")
    print(f"Classifier key    : {chosen_key}")
    print(f"Embedding type    : {args.embedding}")
    print(f"Threshold         : {args.threshold if args.threshold is not None else '(default)'}")
    print()

    summaries = []
    for input_path in input_files:
        summaries.append(
            scan_one_file(
                input_path,
                args,
                parser,
                F_fn,
                tok,
                embed_model,
                device,
                clf,
            )
        )

    total_blocks = sum(int(r["blocks"]) for r in summaries)
    total_truth = sum(int(r["truth"]) for r in summaries)
    total_correct = sum(int(r["correct"]) for r in summaries)

    # Per-subdir breakdown in grid mode (printed before the overall summary).
    if args.input_grid:
        by_subdir: Dict[str, List[Dict]] = {}
        for s in summaries:
            sub = os.path.dirname(s["input"])
            by_subdir.setdefault(sub, []).append(s)

        print()
        print("============================================================")
        print("Per-subdir summary")
        print("============================================================")
        for sub in sorted(by_subdir.keys()):
            slist = by_subdir[sub]
            n_files   = len(slist)
            n_blocks  = sum(int(r["blocks"]) for r in slist)
            n_truth   = sum(int(r["truth"]) for r in slist)
            n_correct = sum(int(r["correct"]) for r in slist)
            acc_str = f"{n_correct / n_truth:.4f}" if n_truth else "(no truth)"
            print(f"  {os.path.basename(sub):<12} : files={n_files:>4}  "
                  f"blocks={n_blocks:>5}  truth={n_truth:>5}  "
                  f"correct={n_correct:>5}  accuracy={acc_str}")

    print()
    print("============================================================")
    print("Overall summary")
    print("============================================================")
    print(f"files scored  : {len(summaries)}")
    print(f"blocks scored : {total_blocks}")

    if total_truth:
        print(f"truth blocks  : {total_truth}")
        print(f"correct       : {total_correct}")
        print(f"accuracy      : {total_correct / total_truth:.4f}")
    else:
        print("truth blocks  : 0")

    # Write per-subdir summary.csv + grid-level summary in grid mode;
    # write a single summary.csv next to predictions in --input-dir mode.
    if args.input_dir:
        out_dir = args.out_dir or os.path.join(args.input_dir, "predictions")
        path = _write_summary_csv(out_dir, summaries, "summary.csv")
        print(f"summary csv   : {path}")
    elif args.input_grid:
        for sub, slist in by_subdir.items():
            sub_out = os.path.join(sub, "predictions")
            _write_summary_csv(sub_out, slist, "summary.csv")
        grid_path = _write_summary_csv(args.input_grid, summaries, "predictions_summary.csv")
        print(f"per-subdir summaries: <subdir>/predictions/summary.csv")
        print(f"grid summary csv    : {grid_path}")


def _write_summary_csv(out_dir: str, summaries: List[Dict], filename: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, filename)
    with open(summary_path, "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["input", "blocks", "truth", "correct", "accuracy"],
        )
        w.writeheader()
        w.writerows(summaries)
    return summary_path


if __name__ == "__main__":
    main()