#!/usr/bin/env bash
# =============================================================================
# run-x-03-audit-temperature-pairs.sh
# Read-only validity/provenance comparison of original T=0.2 pairs and run-x-02
# T=0.0 pilot. Adapted from run-x-02's parameter/logging pattern; does NOT call
# the original or run-x-02 shell wrappers and does NOT require a GPU.
#
# Read-only INPUTS (override paths through environment variables):
#   ORIGINAL_PAIRS : Original 4,500-pair HWC/T=0.2 AGC CSV (idx,code,label).
#   SPLIT_MANIFEST : Original 4,500-pair complexity-stratified split manifest.
#   VALIDATOR_PY   : Existing original Python syntax/structure validator.
#   PILOT_DIR      : Completed run-x-02 directory with pilot JSONL/CSV/config.
#   Tokenizer      : Locally cached CodeLlama-7B tokenizer, optionally.
#
# NEW OUTPUTS (never overwrite):
#   src/output/run-x-03/<RUN_ID>/{original_t02_qc.csv,
#      pilot_temperature_comparison.csv,common_valid_pilot_pairs.csv,
#      tokenizer_audit.json,audit_summary.json,audit_findings.txt}
#   src/logs/run-x-03/run-x-03-<RUN_ID>.log
#
# Usage (from ai_detector repository root):
#   bash src/sh/run-x-03-audit-temperature-pairs.sh
#   PILOT_DIR=/path/to/run-x-02/ID bash src/sh/run-x-03-audit-temperature-pairs.sh
#   TOKENIZER_MODE=required bash src/sh/run-x-03-audit-temperature-pairs.sh
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "${SRC_DIR}/.." && pwd)}"
PYTHON="${PYTHON:-python}"
EXPERIMENT="codellama-7b_4500_complexity_stratified_maxlen2048"
ORIGINAL_PAIRS="${ORIGINAL_PAIRS:-${SRC_DIR}/code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/validsyntax_4500_complexity/codesearchnet_codellama-7b_python_merged_4500.csv}"
SPLIT_MANIFEST="${SPLIT_MANIFEST:-${SRC_DIR}/ml_embeddings/data_codesearchnet/splits/${EXPERIMENT}/complexity_stratified_pair_manifest.csv}"
VALIDATOR_PY="${VALIDATOR_PY:-${SRC_DIR}/code-generation/find_validsyntax_mgc.py}"
PILOT_DIR="${PILOT_DIR:-${SRC_DIR}/output/run-x-02/20261012-140235-6379}"
ORIGINAL_COUNT="${ORIGINAL_COUNT:-4500}"
PILOT_COUNT="${PILOT_COUNT:-100}"
PROMPT_MAX_TOKENS="${PROMPT_MAX_TOKENS:-128}"
TOKENIZER_MODE="${TOKENIZER_MODE:-auto}"  # auto|required|skip; loads only local cache
TOKENIZER_NAME="${TOKENIZER_NAME:-codellama/CodeLlama-7b-hf}"
EOS_IDS="${EOS_IDS:-2,822,29871}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)-$$}"
OUT_DIR="${OUT_DIR:-${SRC_DIR}/output/run-x-03/${RUN_ID}}"
LOG_DIR="${LOG_DIR:-${SRC_DIR}/logs/run-x-03}"
LOG_FILE="${LOG_DIR}/run-x-03-${RUN_ID}.log"

for file in "${ORIGINAL_PAIRS}" "${SPLIT_MANIFEST}" "${VALIDATOR_PY}" "${PILOT_DIR}/pilot_generation.jsonl" "${PILOT_DIR}/pilot_prepared.jsonl" "${SRC_DIR}/py/audit_temperature_pairs.py"; do
  if [[ ! -f "${file}" ]]; then
    echo "[ERROR] Missing required input: ${file}" >&2
    exit 2
  fi
done
if [[ -e "${OUT_DIR}" || -e "${LOG_FILE}" ]]; then
  echo "[ERROR] Output/log already exists for RUN_ID=${RUN_ID}; refusing overwrite" >&2
  exit 2
fi
mkdir -p "${LOG_DIR}"
{
  echo '================================================================='
  echo 'run-x-03 | original T=0.2 / CodeLlama-7B T=0.0 pilot QC'
  echo "repo_root=${REPO_ROOT}"
  echo "run_id=${RUN_ID}"
  echo "original_pairs=${ORIGINAL_PAIRS}"
  echo "split_manifest=${SPLIT_MANIFEST}"
  echo "validator=${VALIDATOR_PY}"
  echo "pilot_dir=${PILOT_DIR}"
  echo "tokenizer_mode=${TOKENIZER_MODE} tokenizer=${TOKENIZER_NAME}"
  echo "output_dir=${OUT_DIR}"
  echo 'No GPU inference; read-only source data.'
  echo '================================================================='
  "${PYTHON}" -u "${SRC_DIR}/py/audit_temperature_pairs.py" \
    --original-pairs "${ORIGINAL_PAIRS}" \
    --split-manifest "${SPLIT_MANIFEST}" \
    --validator-script "${VALIDATOR_PY}" \
    --pilot-dir "${PILOT_DIR}" \
    --output-dir "${OUT_DIR}" \
    --original-count "${ORIGINAL_COUNT}" \
    --pilot-count "${PILOT_COUNT}" \
    --prompt-max-tokens "${PROMPT_MAX_TOKENS}" \
    --tokenizer-mode "${TOKENIZER_MODE}" \
    --tokenizer-name "${TOKENIZER_NAME}" \
    --eos-ids "${EOS_IDS}"
} 2>&1 | tee "${LOG_FILE}"
printf '\nSaved outputs: %s\nSaved log: %s\n' "${OUT_DIR}" "${LOG_FILE}"
