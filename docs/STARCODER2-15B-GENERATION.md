# StarCoder2-15B-Instruct Generation Setup

This document records how to generate machine-generated code (MGC) using
**StarCoder2-15B-Instruct-v0.1** for the AI-Detector pipeline. It is the
instruction-tuned counterpart to the existing StarCoder2-7B base run.

The instruction-tuned run answers a different research question than the
base run: *does instruction tuning increase detectability?* (The paper's
ChatGPT/Gemini results are on instruction-tuned chat models, which is why
their reported F1 is higher than the StarCoder2-7B base result.)

---

## Quick start

```bash
# 1. Activate the dedicated generation env (see "Conda env" below).
conda activate aidetector-gen

# 2. Pilot run (200 samples, ~15-20 min on RTX 6000 Ada).
cd ~/project-workspace/ai_detector
bash src/run0a-generate-starcoder15b.sh

# 3. Inspect the v2 file. If outputs look clean, scale up:
GEN_MAX_NUM=3000 bash src/run0a-generate-starcoder15b.sh

# 4. Switch back to the analysis env for downstream stages.
conda deactivate
conda activate aidetector

# 5. Syntax-validate and pair HWC/MGC.
GEN_MODEL=starcoder2-15b-instruct-v0.1 GEN_MAX_NUM=200 \
  bash src/run0b-find-validsyntax-mgc.sh
```

After stage 0b, the existing stages 1-4 (AST generation, CodeT5+ embedding,
splitting, classifier training) run unchanged. Only the dataset basename
changes - it carries the `starcoder2-15b-instruct-v0.1` label, which the
later scripts pick up automatically.

---

## Why a separate generation env

`transformers==4.36.2` (pinned in `requirements.txt`) predates the
StarCoder2 model family and raises `KeyError: 'starcoder2'` when loading
StarCoder2-15B-Instruct.

The fix is to clone `aidetector` into `aidetector-gen` and upgrade only the
two packages needed for StarCoder2 architecture support. The downstream
analysis pipeline (CodeT5+ embedding, sklearn classifiers, PyCaret) stays
pinned to the original versions in `aidetector`. Two envs, two roles:

| Env                | Role                          | Critical pins                          |
| ------------------ | ----------------------------- | -------------------------------------- |
| `aidetector`       | Embedding + classification    | `transformers==4.36.2`                 |
| `aidetector-gen`   | LLM code generation           | `transformers>=4.39,<4.45`, `accelerate>=0.27` |

Setup:

```bash
conda deactivate                                # ensure no env is active
conda create --name aidetector-gen --clone aidetector
conda activate aidetector-gen
pip install --upgrade 'transformers>=4.39,<4.45' 'accelerate>=0.27'
```

Smoke test that StarCoder2 is recognized:

```bash
python -c "
from transformers import AutoConfig
cfg = AutoConfig.from_pretrained('bigcode/starcoder2-15b-instruct-v0.1')
print('model_type:', cfg.model_type)        # expected: starcoder2
"
```

---

## Prompting strategy: signature-preserving Path C

The paper's ChatGPT/Gemini setup uses **instruction-following code
generation**: tell the model what the function should do in natural
language, get a complete function back. This is the most faithful
comparison for instruction-tuned models.

But the AI-Detector pipeline pairs HWC and MGC by sharing the **same
function signature**. `find_validsyntax_mgc.py` builds:

```
HWC = prompt + solution     # human function = header + docstring + human body
MGC = prompt + output       # AI function    = header + docstring + AI body
```

For the pairing to work, the AI must produce a body that fits the same
header. Three prompting strategies considered:

| Path | Description                                                                 | Pair-compatible? | Faithful to paper? |
| ---- | --------------------------------------------------------------------------- | ---------------- | ------------------ |
| A    | Wrap the code prefix as an instruction: "Complete the following: <prompt>"  | Yes              | Partial            |
| B    | Feed the raw prompt without chat template                                   | Yes              | No (degraded mode) |
| C    | Pure docstring-as-instruction: "Write a Python function that ..."           | **No**           | Yes                |
| C'   | **Signature-preserving Path C** (what this pipeline uses)                   | **Yes**          | Yes                |

**Path C' (chosen)**: build an instruction that includes the *exact*
function header and docstring, ask the model to write only the body, then
post-process the response to keep only the body. This preserves the
signature-pairing assumption while keeping the prompting style faithful to
how instruction-tuned models are normally used.

The instruction template is:

```
Implement the following Python function. Match the signature and docstring
exactly, and write only the function body.

<header + docstring>
```

The chat template (`apply_chat_template`) wraps this in the model's
expected user/assistant turn structure.

---

## Files

| Path                                           | Role                                |
| ---------------------------------------------- | ----------------------------------- |
| `src/code-generation/generate_starcoder15b.py` | Generation script (Path C')         |
| `src/run0a-generate-starcoder15b.sh`           | Driver: env vars + invocation       |
| `src/output/CodeSearchNet/<model_label>-<N>-tp<T>/outputs-512token.txt`     | JSONL output    |
| `src/output/CodeSearchNet/<model_label>-<N>-tp<T>/outputs-512token_v2.txt`  | Human-readable companion |

Output schema in `outputs-512token.txt` (one JSON object per line):

```json
{
  "prompt":   "<function header + docstring (through closing triple-quote)>",
  "output":   "<AI-generated function body only>",
  "solution": "<human function body>"
}
```

This schema matches `generate.py`'s base-7B output exactly, so
`find_validsyntax_mgc.py` consumes it without modification.

---

## Generation details

| Parameter            | Value                                  | Notes                                  |
| -------------------- | -------------------------------------- | -------------------------------------- |
| Model                | `bigcode/starcoder2-15b-instruct-v0.1` | Per model card: bf16, chat template    |
| Precision            | `torch.bfloat16`                       | Required (fp16 underflows on this LM)  |
| Device map           | `auto`                                 | Fits on one RTX 6000 Ada (~30 GB / 49) |
| Max new tokens       | `512`                                  | Same as the 7B base run                |
| Temperature          | `0.2`                                  | Same as 7B run, for clean comparison   |
| Top-p                | `0.95`                                 | Same as 7B run                         |
| Sampling             | `do_sample=True`                       | Same as 7B run                         |
| Termination tokens   | `eos_token_id` + `###`                 | `###` is Instruct's turn separator     |
| Chat template        | `apply_chat_template(...)`             | Required for Instruct models           |

Sample-by-sample inference (`batch_size=1`) is currently the default. The
sequence length varies per sample, and batching at 15B with mixed lengths
costs more in padding than it saves in throughput. If you have multiple
GPUs and want to parallelize, use `CUDA_VISIBLE_DEVICES=0,1` with two
processes splitting the input rather than batching within one process.

---

## Post-processing: `extract_body()`

The model's raw response is reduced to just the function body via:

1. Cut at `###` (chat turn separator) and `<file_sep>` (StarCoder
   repository separator). Hard stops.
2. Extract content inside ``` ```python ... ``` ``` fence if present.
   Instruct models often wrap code in fences.
3. If the response re-emits `def <name>(...):` (the model ignored
   "write only the function body" and rewrote the signature), slice
   from the `def` and drop through the closing `"""` of the re-emitted
   docstring. What remains is the body.
4. Cut at the next top-level `def`/`class` if the model added stray
   follow-up code.
5. Ensure leading/trailing newlines so `prompt + body` composes into
   a syntactically valid Python module.

Step 3 is the most fragile and the one most likely to need tweaking. If
the syntax-validation pass rate in stage 0b is low, inspect the v2 file
for outputs that still start with `def` - the extractor missed those.

---

## Inspection checklist (after pilot run)

Open `outputs-512token_v2.txt` and verify in the first 10-20 samples:

- [ ] `output` starts with **body indentation** (typically 4 spaces),
      not with `def` or prose.
- [ ] `prompt + output` reads like one valid Python function.
- [ ] No leftover ``` ```python ``` fences or `Here is the function...`
      preambles in `output`.
- [ ] `output` doesn't include a second `def` block at the bottom.

If most samples pass, proceed to the full 3000 run. If many fail in the
same way, tighten the extractor in `generate_starcoder15b.py` before
spending the 3-4 hours.

---

## Expected runtimes (RTX 6000 Ada, single GPU)

| Stage                      | 200 pilot     | 3000 full      |
| -------------------------- | ------------- | -------------- |
| Generation (0a)            | ~15-20 min    | ~3-4 hours     |
| Syntax/pair filter (0b)    | <30 sec       | ~1-2 min       |
| AST generation (1)         | <1 min        | ~10 min        |
| CodeT5+ embedding (2)      | ~1 min        | ~5-10 min      |
| Split (3)                  | <10 sec       | <30 sec        |
| Train + evaluate (4)       | ~1 min        | ~5 min         |

First generation run also downloads the 30 GB checkpoint to
`~/.cache/huggingface/` (~10 min on a fast connection).

---

## Pair count expectations

The 7B base run produced these filter rates on 3000 generations
(see `CODESEARCHNET_STARCODER2_7B_RESULTS.md`):

```
total_lines:       3000
mgc_valid_total:   2306   (77%)
paired_valid:      2257   (75%)
```

For Instruct-15B, expected outcomes:

- **Best case**: higher paired-valid rate (>85%). Instruct models follow
  the "write only the body" instruction reliably, the extractor rarely
  misfires, and the body fits the signature cleanly. This is the goal.
- **Likely**: comparable rate (75-85%). Some over-generation, some
  fence misses; salvage step recovers most.
- **Worst case**: lower rate (<70%). Model frequently re-emits the
  signature with subtle variations (different parameter names, type
  annotations, etc.) that the extractor can't reconcile. Would require
  prompt tightening or extractor work.

The pilot tells you which case you're in before committing to the full
run.

---

## Reporting framing

For the write-up, frame this experiment as an investigation of *whether
instruction tuning increases code detectability*, not as a replacement
for the 7B baseline. Both results should be reported side by side:

```
CodeSearchNet Python / StarCoder2-7B-base   / LR / AST: F1 = 0.6750
CodeSearchNet Python / StarCoder2-15B-Inst. / LR / AST: F1 = X.XXXX
                                                Δ = +X.XX
```

A meaningful positive delta (≥ 3 F1 points) supports the hypothesis that
the paper's high F1 on ChatGPT/Gemini is at least partly a consequence
of instruction tuning. A flat delta would suggest detectability is
dominated by other factors (data scale, model capacity, prompting setup).

---

## Reference

Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
Source Code: How Far Are We?", ICSE 2025.

Model card:
https://huggingface.co/bigcode/starcoder2-15b-instruct-v0.1