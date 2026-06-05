#!/bin/bash
# Run from inside a tmux session.
# Regenerate the empty-body / docstring-only pairs that were dropped from the
# StarCoder2-7B validsyntax_4500 CSV, using LOCAL-GPU generation that matches the
# original run. Targets the original pair count (4500): revalidation removes the
# empty-body pairs and exactly that many replacements are generated.
#
# Generation is local-GPU StarCoder2 (generate_more.py reuses code_generation/
# generate.py's generate_hf logic with the model loaded once), and the
# empty-body / docstring-only gate is code_has_required_structure().

set -euo pipefail

cd ~/project-workspace/ai_detector

mkdir -p logs
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

# =====================================================================
# Configuration  (match the original StarCoder2-7B run)
# =====================================================================
DATASET_NAME="${DATASET_NAME:-CodeSearchNet}"
GEN_MODEL="${GEN_MODEL:-starcoder2-7b}"
GEN_MODEL_HF="${GEN_MODEL_HF:-bigcode/starcoder2-7b}"

GEN_TEMPERATURE="${GEN_TEMPERATURE:-0.2}"
GEN_TOP_P="${GEN_TOP_P:-0.95}"
GEN_MAX_LENGTH="${GEN_MAX_LENGTH:-128}"            # prompt truncation cap
GEN_MAX_LENGTH_SAMPLE="${GEN_MAX_LENGTH_SAMPLE:-512}"  # generation budget (=> eos_id_list branch)

TARGET_PAIRS="${TARGET_PAIRS:-4500}"              # final valid-pair count to maintain

# CodeSearchNet source for new candidates.
CSN_ROOT="${CSN_ROOT:-data/CodeSearchNet}"
LANGUAGE="${LANGUAGE:-python}"

# Existing paired CSV to revalidate + extend (empty-body pairs get replaced).
# CSV_ROOT="src/code-analyzer-tree-sitter/data_codesearchnet/${GEN_MODEL}/validsyntax_4500_complexity"
CSV_ROOT="src/code-analyzer-tree-sitter/data_codesearchnet/${GEN_MODEL}/validsyntax"
CSV_PATH="${CSV_PATH:-${CSV_ROOT}/codesearchnet_${GEN_MODEL}_python_merged_4500.csv}"

# Pass DRY_RUN=1 to plan only (no model load / no write).
DRY_RUN="${DRY_RUN:-0}"

TIMESTAMP=$(date +%m-%d_%H-%M)
LOG_FILE="logs/generate_more_${GEN_MODEL}_csn_t${GEN_TEMPERATURE}_${TIMESTAMP}.log"

# =====================================================================
echo "=== Additional (regeneration) configuration ==="
echo "  HF model:          ${GEN_MODEL_HF}"
echo "  Existing CSV:      ${CSV_PATH}"
echo "  CodeSearchNet:     ${CSN_ROOT}/${LANGUAGE}/train.jsonl"
echo "  Target pairs:      ${TARGET_PAIRS}"
echo "  Temperature:       ${GEN_TEMPERATURE}   top_p: ${GEN_TOP_P}"
echo "  Max length:        ${GEN_MAX_LENGTH}   max_length_sample: ${GEN_MAX_LENGTH_SAMPLE}"
echo "  Dry run:           ${DRY_RUN}"
echo "  Log file:          ${LOG_FILE}"
echo "==============================================="
echo ""

if [[ ! -f "${CSV_PATH}" ]]; then
  echo "[ERROR] existing CSV not found: ${CSV_PATH}" >&2
  exit 1
fi
if [[ ! -f "${CSN_ROOT}/${LANGUAGE}/train.jsonl" ]]; then
  echo "[ERROR] CodeSearchNet train.jsonl not found: ${CSN_ROOT}/${LANGUAGE}/train.jsonl" >&2
  exit 1
fi

DRY_RUN_FLAG=""
if [[ "${DRY_RUN}" == "1" ]]; then
  DRY_RUN_FLAG="--dry-run"
fi

python src/code_generation/generate_more.py \
    "${CSV_PATH}" \
    "${TARGET_PAIRS}" \
    --codesearchnet-root "${CSN_ROOT}" \
    --language "${LANGUAGE}" \
    --model-name "${GEN_MODEL_HF}" \
    --temperature "${GEN_TEMPERATURE}" \
    --top-p "${GEN_TOP_P}" \
    --max-length "${GEN_MAX_LENGTH}" \
    --max-length-sample "${GEN_MAX_LENGTH_SAMPLE}" \
    ${DRY_RUN_FLAG} \
    2>&1 | tee "${LOG_FILE}"

echo ""
if [[ "${DRY_RUN}" == "1" ]]; then
  echo "Dry run complete. Check 'invalid existing pairs removed' and 'needed new valid pairs' above."
  echo "If the plan looks right, re-run without DRY_RUN=1 to generate."
else
  echo "Regeneration complete. Updated CSV: ${CSV_PATH}"
  echo "Row count:"
  wc -l "${CSV_PATH}"
  echo ""
  echo "Next, re-score NPR on the refreshed CSV (in detect_code_gpt/code-detection):"
  echo "  python main_adapter.py --csv_path ${CSV_PATH} \\"
  echo "      --base_model_name ${GEN_MODEL_HF} \\"
  echo "      --output_name ${GEN_MODEL}_4500_refreshed"
fi