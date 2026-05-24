"""
generate_embeddings.py
======================

Generate CodeT5+ embeddings for AI-generated source code detection (RQ2-D).

Reference paper
---------------
Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
Source Code: How Far Are We?", ICSE 2025.
Section IV.D ("RQ2: Machine Learning Classifiers with Embeddings") describes
three input representations fed to ML classifiers:
    * Code Only      -> source code text
    * AST Only       -> AST token sequence from tree-sitter
    * Code + AST     -> concatenation of the two

Each representation is embedded into a 256-dim vector with the
`Salesforce/codet5p-110m-embedding` model (Wang et al., 2023), which contains
the CodeT5+ encoder plus a projection head producing L2-normalized 256-dim
vectors usable as features for downstream classifiers.

Input
-----
CSVs produced by `ast-generator.py` (any mode). Required columns:
    - idx, code, ast, label
    - optional: new_code (present for ablation modes; preserved on output)
`label` is the string {'human', 'lm'} as it appears in the upstream dataset.

Output
------
CSV files with the same basename in the chosen output directory, with:
    - idx, code, ast, (new_code if present)
    - code_0      ..  code_255      (256-dim Code Only embedding)
    - ast_0       ..  ast_255       (256-dim AST Only embedding)
    - combined_0  ..  combined_255  (256-dim Code + AST embedding)
    - actual label                  (renamed from `label`; 'human'->1, 'lm'->0)

The column naming (`code_*`, `ast_*`, `combined_*`) and the `actual label`
column name match what `ml_embeddings/hyperparameter_tuning.py` and
`ml_embeddings/test_embedding.py` expect.
"""

import argparse
import os
from glob import glob

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
MODEL_ID  = "Salesforce/codet5p-110m-embedding"
EMBED_DIM = 256
DEFAULT_MAX_LEN = 512               # CodeT5+ tokenizer truncation length
SEP       = " </s> "                # separator for "Code + AST" representation
LABEL_MAP = {"human": 1, "lm": 0}   # paper convention: human=positive, AI=negative


# -----------------------------------------------------------------------------
# Model loading + batch encoding
# -----------------------------------------------------------------------------
def load_model(device):
    print(f"Loading {MODEL_ID} on {device} ...")
    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModel.from_pretrained(MODEL_ID, trust_remote_code=True).to(device).eval()
    return tok, model


@torch.no_grad()
def embed_batch(texts, tok, model, device, batch_size=32, max_len=DEFAULT_MAX_LEN, desc="encoding"):    
    """Return an (N, EMBED_DIM) numpy array of embeddings for `texts`."""
    if len(texts) == 0:
        return np.zeros((0, EMBED_DIM), dtype=np.float32)

    out_chunks = []
    for i in tqdm(range(0, len(texts), batch_size), desc=desc, leave=False):
        batch = texts[i : i + batch_size]
        enc = tok(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_len,
        ).to(device)

        out = model(**enc)

        # The codet5p-110m-embedding model returns a (batch, 256) tensor, but
        # different transformers versions wrap it as a tuple or ModelOutput.
        # Handle the three plausible shapes defensively.
        if isinstance(out, (tuple, list)):
            emb = out[0]
        elif hasattr(out, "last_hidden_state"):
            # Fallback only -- shouldn't trigger for the dedicated embedding ckpt.
            attn = enc["attention_mask"].unsqueeze(-1).float()
            emb = (out.last_hidden_state * attn).sum(1) / attn.sum(1)
        else:
            emb = out

        assert emb.dim() == 2 and emb.shape[1] == EMBED_DIM, (
            f"Unexpected embedding shape {tuple(emb.shape)}; expected (B, {EMBED_DIM})."
        )
        out_chunks.append(emb.cpu().numpy())

    return np.concatenate(out_chunks, axis=0)


# -----------------------------------------------------------------------------
# CSV processing
# -----------------------------------------------------------------------------
def process_csv(csv_in, csv_out, tok, model, device, batch_size, max_len):
    df = pd.read_csv(csv_in)

    required = {"idx", "code", "ast", "label"}
    missing = required - set(df.columns)
    if missing:
        print(f"  [SKIP] missing required columns {sorted(missing)} in {csv_in}")
        return

    # Drop rows with missing code or ast (rare; safety net).
    df = df.dropna(subset=["code", "ast"]).copy()
    df["code"] = df["code"].astype(str)
    df["ast"]  = df["ast"].astype(str)

    # Normalize string labels to integers per paper convention.
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    unknown = set(df["label"]) - LABEL_MAP.keys()
    if unknown:
        print(f"  [WARN] dropping rows with unknown labels: {unknown}")
        df = df[df["label"].isin(LABEL_MAP)].copy()
    df["actual label"] = df["label"].map(LABEL_MAP).astype(int)

    n = len(df)
    if n == 0:
        print(f"  [SKIP] no usable rows in {csv_in}")
        return
    print(f"  rows: {n}")

    # Build the "Code + AST" representation.
    combined_texts = (df["code"] + SEP + df["ast"]).tolist()

    # Three forward passes per CSV.
    code_emb     = embed_batch(df["code"].tolist(), tok, model, device, batch_size, max_len=max_len, desc="code")
    ast_emb      = embed_batch(df["ast"].tolist(),  tok, model, device, batch_size, max_len=max_len, desc="ast")
    combined_emb = embed_batch(combined_texts,       tok, model, device, batch_size, max_len=max_len, desc="combined")

    # Assemble the output frame.
    out_cols = {
        "idx":  df["idx"].values,
        "code": df["code"].values,
        "ast":  df["ast"].values,
    }
    if "new_code" in df.columns:
        out_cols["new_code"] = df["new_code"].values
    for j in range(EMBED_DIM):
        out_cols[f"code_{j}"]     = code_emb[:, j]
    for j in range(EMBED_DIM):
        out_cols[f"ast_{j}"]      = ast_emb[:, j]
    for j in range(EMBED_DIM):
        out_cols[f"combined_{j}"] = combined_emb[:, j]
    out_cols["actual label"] = df["actual label"].values

    out_df = pd.DataFrame(out_cols)
    os.makedirs(os.path.dirname(csv_out) or ".", exist_ok=True)
    out_df.to_csv(csv_out, index=False)
    print(f"  -> {csv_out}  shape={out_df.shape}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--input-dir", default="../code-analyzer-tree-sitter/data_main",
        help="Directory of AST CSVs produced by ast-generator.py "
             "(default: ../code-analyzer-tree-sitter/data_main).",
    )
    ap.add_argument(
        "--output-dir", default="data_main_with_embeddings",
        help="Where to write embedding-augmented CSVs "
             "(default: data_main_with_embeddings).",
    )
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument(
        "--max-len", type=int, default=DEFAULT_MAX_LEN,
        help="Tokenizer max_length for CodeT5+ embedding inputs. "
             "Increase this to reduce truncation of long AST sequences.",
    )
    ap.add_argument(
        "--device", default=None,
        help="cuda | cuda:0 | cpu (auto-detect if unset).",
    )
    ap.add_argument(
        "--overwrite", action="store_true",
        help="Re-embed and overwrite even if the output CSV already exists.",
    )
    return ap.parse_args()


def main():
    args = parse_args()

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tok, model = load_model(device)

    csv_files = sorted(
        glob(os.path.join(args.input_dir, "**", "*.csv"), recursive=True)
    )
    csv_files = [
        p for p in csv_files
        if not os.path.basename(p).endswith("_manifest.csv")
        and not os.path.basename(p).endswith("_candidate_report.csv")
    ]
    if not csv_files:
        print(f"[ERROR] no CSVs found under {args.input_dir}")
        return

    print(f"\nFound {len(csv_files)} CSV(s) to process.")
    print(f"Input  : {args.input_dir}")
    print(f"Output : {args.output_dir}\n")
    print(f"Max len: {args.max_len}\n")

    for csv_in in csv_files:
        rel     = os.path.relpath(csv_in, args.input_dir)
        csv_out = os.path.join(args.output_dir, rel)
        print(f"=== {rel} ===")
        if os.path.exists(csv_out) and not args.overwrite:
            print(f"  skip (exists): {csv_out}")
            continue
        process_csv(csv_in, csv_out, tok, model, device, args.batch_size, args.max_len)

    print("\nDone.")


if __name__ == "__main__":
    main()