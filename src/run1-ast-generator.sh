#!/usr/bin/env bash
# =============================================================================
# run1-ast-generator.sh
# -----------------------------------------------------------------------------
# Driver script for the AST generation stage of the AI-Detector replication.
#
# Reference paper:
#   Suh et al., "An Empirical Study on Automatically Detecting AI-Generated
#   Source Code: How Far Are We?", ICSE 2025.
#
# What this script does
#   Wraps src/code-analyzer-tree-sitter/ast-generator.py and runs it once per
#   mode requested. ast-generator.py parses each source-code CSV with
#   tree-sitter, optionally applies a transformation, and writes a sibling
#   CSV with the AST sequence column appended.
#
# Modes (mapped to research questions in the paper)
#   baseline                -> RQ2-D, Section IV.D.
#                              "Machine Learning Classifiers with Embeddings".
#                              The AST is produced from the *original* code
#                              with no transformation. Output goes to
#                              data_main/ and feeds CodeT5+ embedding generation.
#
#   uniform_variables_name  -> RQ3, Section IV.E ablation (Table IX, row 1).
#                              All variable identifiers are renamed to var_1,
#                              var_2, ... before the AST is generated. Used to
#                              measure how much variable naming contributes
#                              to detector performance.
#
#   uniform_methods_name    -> RQ3, Section IV.E ablation (Table IX, row 2).
#                              All function/method names are renamed to
#                              func_1, func_2, ... Measures the contribution
#                              of method/function naming style.
#
#   no_comments             -> RQ3, Section IV.E ablation (Table IX, row 3).
#                              Comments are stripped before AST generation.
#                              Measures the contribution of comments.
#
# Outputs
#   Each mode writes 9 CSVs (one per input dataset) to its own directory.
#   - baseline               -> data_main/                                     [feeds RQ2-D]
#   - uniform_variables_name -> data_ablation_study_code_embedding/uniform_variables_name/
#   - uniform_methods_name   -> data_ablation_study_code_embedding/uniform_methods_name/
#   - no_comments            -> data_ablation_study_code_embedding/no_comments/
#
# Prerequisites (one-time)
#   1. conda env active (e.g. `conda activate aidetector`).
#   2. The three tree-sitter grammars cloned alongside ast-generator.py:
#        tree-sitter-python/, tree-sitter-java/, tree-sitter-cpp/
#      and the combined library built at build/my-languages.so. Verify with
#        python tree-sitter-test.py
#   3. Input CSVs staged in data_temp1/ with columns: idx, code, label
#      (label: 1 = human, 0 = AI). The basename must match the convention
#      <dataset>_<llm>_<language>_merged.csv since the language is inferred
#      from parts[2] of the basename split by underscore.
#
# Usage
#   From repository root:
#     bash src/run1-ast-generator.sh                  # default: baseline only
#     bash src/run1-ast-generator.sh all              # baseline + 3 ablations
#     bash src/run1-ast-generator.sh ablations        # 3 ablations only
#     bash src/run1-ast-generator.sh baseline uniform_variables_name
#   Or from the target directory:
#     cd src/code-analyzer-tree-sitter && bash ../run1-ast-generator.sh all
#
# Customization
#   INPUT_DIR and the per-mode output directories can be overridden via the
#   environment variables defined immediately below.
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configurable variables (override via env, e.g. INPUT_DIR=foo bash ...sh)
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Where ast-generator.py lives. The script `cd`s here before running so all
# relative paths inside ast-generator.py (build/, data_temp1/, ...) resolve.
TARGET_DIR="${TARGET_DIR:-${SCRIPT_DIR}/code-analyzer-tree-sitter}"

# Input directory holding the 9 merged CSVs from the paper's datasets
# (HumanEval / MBPP x ChatGPT / ChatGPT-4 / Gemini x Python / Java).
# INPUT_DIR="${INPUT_DIR:-data_temp1}"                 # Original before additional datasets.
INPUT_DIR="${INPUT_DIR:-data_temp1_codesearchnet}"     # CodeSearchNet corpus.

# Output directories per mode. Defaults match ast-generator.py's defaults so
# downstream scripts (generate_embeddings.py, code-feature-extractor.py)
# can find the data without further configuration.
# OUT_BASELINE="${OUT_BASELINE:-data_main}"              # Original before additional datasets.
OUT_BASELINE="${OUT_BASELINE:-data_temp1_codesearchnet}" # CodeSearchNet corpus.

OUT_UNIFORM_VARS="${OUT_UNIFORM_VARS:-data_ablation_study_code_embedding/uniform_variables_name}"
OUT_UNIFORM_METHODS="${OUT_UNIFORM_METHODS:-data_ablation_study_code_embedding/uniform_methods_name}"
OUT_NO_COMMENTS="${OUT_NO_COMMENTS:-data_ablation_study_code_embedding/no_comments}"

# Python interpreter. Use whatever's on PATH; users wanting a specific env
# should activate it before invoking this script.
PYTHON="${PYTHON:-python}"

# -----------------------------------------------------------------------------
# Mode selection
# -----------------------------------------------------------------------------
ALL_MODES=(baseline uniform_variables_name uniform_methods_name no_comments)
ABLATION_MODES=(uniform_variables_name uniform_methods_name no_comments)

if [ "$#" -eq 0 ]; then
  MODES=(baseline)
else
  case "$1" in
    all)        MODES=("${ALL_MODES[@]}") ;;
    ablations)  MODES=("${ABLATION_MODES[@]}") ;;
    *)          MODES=("$@") ;;
  esac
fi

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
output_for_mode() {
  case "$1" in
    baseline)               echo "${OUT_BASELINE}" ;;
    uniform_variables_name) echo "${OUT_UNIFORM_VARS}" ;;
    uniform_methods_name)   echo "${OUT_UNIFORM_METHODS}" ;;
    no_comments)            echo "${OUT_NO_COMMENTS}" ;;
    *) echo "[ERROR] unknown mode: $1" >&2; exit 2 ;;
  esac
}

# -----------------------------------------------------------------------------
# Pre-flight checks
# -----------------------------------------------------------------------------
if [ ! -d "${TARGET_DIR}" ]; then
  echo "[ERROR] TARGET_DIR does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

cd "${TARGET_DIR}"

if [ ! -f "ast-generator.py" ]; then
  echo "[ERROR] ast-generator.py not found in ${TARGET_DIR}" >&2
  exit 1
fi

if [ ! -f "build/my-languages.so" ]; then
  echo "[ERROR] build/my-languages.so missing. Build it first:" >&2
  echo "          cd ${TARGET_DIR} && python tree-sitter-test.py" >&2
  exit 1
fi

if [ ! -d "${INPUT_DIR}" ] || [ -z "$(ls -A "${INPUT_DIR}" 2>/dev/null)" ]; then
  echo "[ERROR] INPUT_DIR is missing or empty: ${TARGET_DIR}/${INPUT_DIR}" >&2
  echo "        Stage the merged CSVs there (see header for the file-naming convention)." >&2
  exit 1
fi

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
echo "============================================================"
echo " run1-ast-generator.sh"
echo "   target dir : ${TARGET_DIR}"
echo "   input dir  : ${INPUT_DIR}"
echo "   modes      : ${MODES[*]}"
echo "============================================================"

for mode in "${MODES[@]}"; do
  out_dir="$(output_for_mode "${mode}")"
  echo
  echo "------------------------------------------------------------"
  echo " mode       : ${mode}"
  echo " output dir : ${out_dir}"
  echo "------------------------------------------------------------"
  "${PYTHON}" ast-generator.py \
    --mode "${mode}" \
    --input-dir "${INPUT_DIR}" \
    --output-dir "${out_dir}"
done

echo
echo "============================================================"
echo " Done. Summary of outputs:"
for mode in "${MODES[@]}"; do
  out_dir="$(output_for_mode "${mode}")"
  count=$(find "${out_dir}" -name '*.csv' 2>/dev/null | wc -l)
  printf "   %-26s -> %3d CSV(s) in %s\n" "${mode}" "${count}" "${out_dir}"
done
echo "============================================================"