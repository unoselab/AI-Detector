"""
generate_starcoder15b.py
====================

Path C (signature-preserving) generation for instruction-tuned code LLMs.

Differences from `generate.py`:
  * Uses instruction-tuned model (chat template + bf16 + ### terminator).
  * Instruction includes the function signature + docstring so MGC matches
    HWC's signature (required by find_validsyntax_mgc.py's HWC/MGC pairing).
  * Extracts only the function body from the AI response, then writes it
    as `output` so downstream pairing remains:
        HWC = prompt + solution
        MGC = prompt + output
    where `prompt` is the function header up to and including the docstring.

Per CSN sample, the flow is:
  1. Parse the original_string into (prompt, body).
       prompt = header + docstring (inclusive of closing triple-quote)
       body   = the human implementation
  2. Build an instruction asking the model to implement that exact signature.
  3. Apply chat template, generate with bf16, terminate on EOS or ###.
  4. Extract the body from the response (drop fences, drop the re-emitted
     signature/docstring, cut at the next def/class).
  5. Save record with keys (prompt, output, solution) matching generate.py.

Reference paper
---------------
Suh et al., ICSE 2025, "How Far Are We?"
"""

import argparse
import json
import os
import re

import numpy as np
import torch
from loguru import logger
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

os.environ["TOKENIZERS_PARALLELISM"] = "false"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# -----------------------------------------------------------------------------
# Parse a CodeSearchNet sample into (prompt, body) using generate.py's split
# -----------------------------------------------------------------------------
def split_prompt_body(original_string: str):
    """
    prompt = function header + docstring (through closing triple-quote)
    body   = everything after
    """
    s = original_string.replace("'''", '"""')
    parts = s.split('"""')
    if len(parts) < 3:
        return None, None
    prompt = parts[0] + '"""' + parts[1] + '"""'
    body   = parts[2]
    return prompt, body


def load_data_codesearchnet_instruct(path, language="python", max_num=10_000, seed=42):
    path_to_data = f"{path}/{language}/train.jsonl"
    logger.info(f"Loading data from {path_to_data}")

    prompts, solutions = [], []
    failed = success = 0
    min_prompt_words, max_prompt_words = 5, 128
    min_body_words,   max_body_words   = 5, 256

    with open(path_to_data, "r") as f:
        for line in tqdm(f, desc="reading CSN"):
            data = json.loads(line)
            prompt, body = split_prompt_body(data["original_string"])
            if prompt is None:
                failed += 1
                continue
            if not (min_prompt_words <= len(prompt.split()) <= max_prompt_words):
                continue
            if not (min_body_words   <= len(body.split())   <= max_body_words):
                continue
            prompts.append(prompt)
            solutions.append(body)
            success += 1

    logger.info(f"Parsed {success} / {success + failed} samples")
    logger.info(f"Loaded {len(prompts)} (prompt, solution) pairs")

    if len(prompts) > max_num:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(prompts), size=max_num, replace=False)
        prompts   = [prompts[i]   for i in idx]
        solutions = [solutions[i] for i in idx]
        logger.info(f"Sampled {len(prompts)} (seed={seed})")

    return prompts, solutions


# -----------------------------------------------------------------------------
# Build instruction from prompt (signature + docstring)
# -----------------------------------------------------------------------------
INSTRUCTION_TEMPLATE = (
    "Implement the following Python function. Match the signature and "
    "docstring exactly, and write only the function body.\n\n"
    "{prompt}"
)


def build_instruction(prompt: str) -> str:
    return INSTRUCTION_TEMPLATE.format(prompt=prompt.rstrip())


# -----------------------------------------------------------------------------
# Reduce raw response -> function body only
# -----------------------------------------------------------------------------
CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)


def strip_code_fences(text: str) -> str:
    m = CODE_FENCE_RE.search(text)
    return m.group(1) if m else text


def extract_body(response: str, prompt: str) -> str:
    """
    1. Stop at '###' and '<file_sep>'.
    2. Extract code from ```python ... ``` fence if present.
    3. If response re-emits 'def ...': slice from def, drop through closing
       docstring triple-quote; what remains is the body.
    4. Cut at next top-level def/class.
    5. Ensure leading/trailing newlines so `prompt + body` composes well.
    """
    text = response
    text = text.split("###", 1)[0]
    text = text.split("<file_sep>", 1)[0]
    text = strip_code_fences(text).strip("\n")

    def_match = re.search(r"^(\s*)(async\s+)?def\s+\w+\s*\(", text, re.MULTILINE)
    if def_match:
        sliced  = text[def_match.start():]
        sliced2 = sliced.replace("'''", '"""')
        parts   = sliced2.split('"""')
        if len(parts) >= 3:
            text = parts[2]
        else:
            nl = sliced.find("\n")
            text = sliced[nl + 1:] if nl != -1 else ""

    cut = len(text)
    for pat in [
        r"\n\n(?=def\s+\w+\s*\()",
        r"\n\n(?=async\s+def\s+\w+\s*\()",
        r"\n\n(?=class\s+\w+)",
    ]:
        m = re.search(pat, text)
        if m:
            cut = min(cut, m.start())
    text = text[:cut].rstrip()

    if not text.startswith("\n"):
        text = "\n" + text
    if not text.endswith("\n"):
        text = text + "\n"
    return text


# -----------------------------------------------------------------------------
# Generation
# -----------------------------------------------------------------------------
def generate_instruct(model_name, prompts, solutions,
                      max_new_tokens=512, temperature=0.2,
                      top_p=0.95, do_sample=True):
    logger.info(f"Loading tokenizer + model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16,
        trust_remote_code=True, device_map="auto",
    )
    model.eval()

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    eos_ids = [tokenizer.eos_token_id]
    try:
        hash_id = tokenizer.convert_tokens_to_ids("###")
        if hash_id is not None and hash_id != tokenizer.unk_token_id:
            eos_ids.append(hash_id)
    except Exception:
        pass
    logger.info(f"Terminator token ids: {eos_ids}")

    outputs = []
    for prompt in tqdm(prompts, desc="generating", ncols=80):
        messages = [{"role": "user", "content": build_instruction(prompt)}]
        chat_prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        enc = tokenizer(chat_prompt, return_tensors="pt",
                        truncation=True, max_length=1024).to(device)
        input_len = enc["input_ids"].shape[1]

        with torch.no_grad():
            out = model.generate(
                **enc,
                do_sample=do_sample,
                max_new_tokens=max_new_tokens,
                temperature=temperature, top_p=top_p,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=eos_ids,
                use_cache=True,
            )

        raw  = tokenizer.decode(out[0, input_len:], skip_special_tokens=True)
        body = extract_body(raw, prompt)
        outputs.append(body)

    logger.info(f"Generated {len(outputs)} outputs")
    for i in range(min(3, len(outputs))):
        logger.info(f"--- Example {i} ---")
        logger.info(f"Prompt (first 200): {prompts[i][:200]}")
        logger.info(f"Output body (first 400): {outputs[i][:400]}")
        logger.info(f"Solution (first 200): {solutions[i][:200]}")

    return prompts, outputs, solutions


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path",        default="../data/CodeSearchNet")
    ap.add_argument("--model_name",  default="bigcode/starcoder2-15b-instruct-v0.1")
    ap.add_argument("--max_num",     type=int,   default=200)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--max_length",  type=int,   default=512)
    ap.add_argument("--output-root", default="../../outputs",
                    help="Root directory for generation outputs "
                         "(default: ../../outputs, relative to script location).")
    args = ap.parse_args()
    logger.info(f"args: {args}")

    prompts, solutions = load_data_codesearchnet_instruct(
        path=args.path, language="python", max_num=args.max_num,
    )
    prompts, outputs, solutions = generate_instruct(
        model_name=args.model_name,
        prompts=prompts, solutions=solutions,
        max_new_tokens=args.max_length,
        temperature=args.temperature,
        top_p=0.95, do_sample=True,
    )

    model_label  = args.model_name.split("/")[-1]
    dataset_name = args.path.rstrip("/").split("/")[-1]
    save_dir = os.path.join(
        args.output_root,
        dataset_name,
        f"{model_label}-{args.max_num}-tp{args.temperature}",
    )
    os.makedirs(save_dir, exist_ok=True)

    out_file = f"{save_dir}/outputs-{args.max_length}token.txt"
    if os.path.exists(out_file):
        os.remove(out_file)
    with open(out_file, "w") as f:
        for p, o, s in zip(prompts, outputs, solutions):
            f.write(json.dumps({"prompt": p, "output": o, "solution": s}) + "\n")
    logger.info(f"Wrote -> {out_file}")

    out_v2 = f"{save_dir}/outputs-{args.max_length}token_v2.txt"
    if os.path.exists(out_v2):
        os.remove(out_v2)
    with open(out_v2, "w") as f:
        for i, (p, o, s) in enumerate(zip(prompts, outputs, solutions)):
            f.write("-" * 20 + f" Sample {i} " + "-" * 20 + "\n")
            f.write(f"Prompt:\n{p}\n" + "-" * 10 + "\n")
            f.write(f"Output (body only):\n{o}\n" + "-" * 10 + "\n")
            f.write(f"Solution (body):\n{s}\n\n")
    logger.info(f"Wrote -> {out_v2}")


if __name__ == "__main__":
    main()