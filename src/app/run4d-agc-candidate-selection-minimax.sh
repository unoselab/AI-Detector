#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run4d-agc-candidate-selection-minimax.sh
# -----------------------------------------------------------------------------
# Statistically compare the five Table (1)-selected AGC detector candidates by
# jointly considering:
#   (1) complexity-balanced matched-source AUROC (Table 1), and
#   (2) exact-test-support cross-generator transfer AUROC (run4c / Table 2).
#
# PRIMARY DECISION RULE
#   Use a Savage-style minimax-regret criterion on the two AUROC regimes.
#   For candidate c and evaluation regime e:
#       regret(c,e) = best_AUROC(e) - AUROC(c,e)
#       max_regret(c) = max_e regret(c,e)
#   The point-estimate candidate is the one with the smallest max_regret.
#
#   This avoids ordinal rank sums and avoids arbitrary weighted averages. Both
#   evaluation regimes use AUROC on the same [0,1] scale, so regret is measured
#   directly in AUROC points.
#
# UNCERTAINTY MODEL
#   Use a pair-cluster bootstrap. The complexity-balanced split was created at
#   the HWC-AGC pair level, so the bootstrap resampling unit is the original
#   pair_id, not an individual function row. For each target generator:
#     * sample 450 pair_ids with replacement;
#     * include both HWC(label=1) and AGC(label=0) rows for every sampled pair;
#     * reuse the SAME sampled pair multiplicities for all five classifiers on
#       that target, preserving paired classifier comparisons.
#
#   Bootstrap draws are propagated through Table (1), Table (2), expected rank,
#   Pareto-front membership, pairwise AUROC differences, and minimax regret.
#
# INPUTS
#   Default run4c result root:
#     src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c/
#
#   Required run4c files:
#     matrix_auroc.csv
#     diagonal_qc.csv
#     predictions/clf-<source>/target-<target>.csv   (25 files)
#
# OUTPUTS
#   Default run4d result root:
#     src/ml_embeddings/data_codesearchnet/candidate_selection_run4d/
#
#   Key outputs:
#     point_estimates.csv
#     bootstrap_table1_summary.csv
#     bootstrap_transfer_summary.csv
#     minimax_regret_summary.csv
#     pairwise_table1_differences.csv
#     pairwise_transfer_common_targets.csv
#     pareto_summary.csv
#     candidate_selection_summary.txt
#     methodology.txt
#     environment.txt
#     bootstrap_candidate_metrics.csv.gz
#
# HARD QC
#   * run4c diagonal_qc.csv must report 5/5 PASS.
#   * exactly 25 run4c prediction CSVs must exist.
#   * every target must contain exactly 450 pair_ids, each with one HWC and one
#     AGC row, and all five classifiers must have identical target row support.
#   * observed AUROCs recomputed from full-precision prediction scores must
#     reproduce run4c matrix_auroc.csv to 1e-12 absolute tolerance.
#
# SERVER NAMING
#   Development files carry -v<num>. The server-ready ZIP removes the version
#   suffix from both this wrapper and the corresponding Python analysis file.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PY_SCRIPT="${PY_SCRIPT:-src/app/compute-agc-candidate-selection-minimax.py}"
RUN4C_ROOT="${RUN4C_ROOT:-src/ml_embeddings/data_codesearchnet/transfer_same_test_run4c}"
OUTPUT_ROOT="${OUTPUT_ROOT:-src/ml_embeddings/data_codesearchnet/candidate_selection_run4d}"
BOOTSTRAP_REPS="${BOOTSTRAP_REPS:-20000}"
BOOTSTRAP_SEED="${BOOTSTRAP_SEED:-20260723}"
BOOTSTRAP_BATCH_SIZE="${BOOTSTRAP_BATCH_SIZE:-1000}"
CI_LEVEL="${CI_LEVEL:-0.95}"
ALLOW_OVERWRITE="${ALLOW_OVERWRITE:-0}"

TS="$(date +'%Y%m%d_%H%M%S')"
RUN_LOG_DIR="${LOG_DIR:-src/logs/run4d-candidate-selection/${TS}}"
MASTER_LOG="${RUN_LOG_DIR}/master.log"
mkdir -p "${RUN_LOG_DIR}"

exec > >(tee -a "${MASTER_LOG}") 2>&1

echo "========================================================================="
echo " run4d: Statistical Candidate Selection by Bootstrap Minimax Regret"
echo " Python script   : ${PY_SCRIPT}"
echo " run4c input     : ${RUN4C_ROOT}"
echo " Output root     : ${OUTPUT_ROOT}"
echo " Bootstrap reps  : ${BOOTSTRAP_REPS}"
echo " Bootstrap seed  : ${BOOTSTRAP_SEED}"
echo " Bootstrap batch : ${BOOTSTRAP_BATCH_SIZE}"
echo " CI level        : ${CI_LEVEL}"
echo " Log directory   : ${RUN_LOG_DIR}"
echo " Started         : $(date -Is)"
echo "========================================================================="

# -----------------------------------------------------------------------------
# Preflight: required standalone Python analysis.
# -----------------------------------------------------------------------------
if [ ! -f "${PY_SCRIPT}" ]; then
  echo "[ERROR] Missing run4d Python script: ${PY_SCRIPT}" >&2
  exit 2
fi

# -----------------------------------------------------------------------------
# Preflight: required run4c artifacts.
# -----------------------------------------------------------------------------
for rel in matrix_auroc.csv diagonal_qc.csv; do
  if [ ! -s "${RUN4C_ROOT}/${rel}" ]; then
    echo "[ERROR] Missing or empty run4c input: ${RUN4C_ROOT}/${rel}" >&2
    exit 2
  fi
done

PRED_COUNT="$(find "${RUN4C_ROOT}/predictions" -type f -name 'target-*.csv' 2>/dev/null | wc -l | tr -d ' ')"
if [ "${PRED_COUNT}" -ne 25 ]; then
  echo "[ERROR] Expected 25 run4c prediction CSVs, found ${PRED_COUNT}" >&2
  exit 2
fi

# -----------------------------------------------------------------------------
# Refuse to mix result revisions unless explicitly requested.
# -----------------------------------------------------------------------------
if [ -d "${OUTPUT_ROOT}" ] && find "${OUTPUT_ROOT}" -type f -print -quit 2>/dev/null | grep -q .; then
  if [ "${ALLOW_OVERWRITE}" != "1" ]; then
    echo "[ERROR] Output root already contains files: ${OUTPUT_ROOT}" >&2
    echo "        Use a new OUTPUT_ROOT or set ALLOW_OVERWRITE=1 explicitly." >&2
    exit 2
  fi
fi
mkdir -p "${OUTPUT_ROOT}"

python "${PY_SCRIPT}" \
  --run4c-root "${RUN4C_ROOT}" \
  --output-root "${OUTPUT_ROOT}" \
  --bootstrap-reps "${BOOTSTRAP_REPS}" \
  --seed "${BOOTSTRAP_SEED}" \
  --batch-size "${BOOTSTRAP_BATCH_SIZE}" \
  --ci-level "${CI_LEVEL}"

# -----------------------------------------------------------------------------
# Paper-facing artifact audit.
# -----------------------------------------------------------------------------
REQUIRED_OUTPUTS=(
  "point_estimates.csv"
  "bootstrap_table1_summary.csv"
  "bootstrap_transfer_summary.csv"
  "minimax_regret_summary.csv"
  "pairwise_table1_differences.csv"
  "pairwise_transfer_common_targets.csv"
  "pareto_summary.csv"
  "candidate_selection_summary.txt"
  "methodology.txt"
  "environment.txt"
  "bootstrap_candidate_metrics.csv.gz"
)

for rel in "${REQUIRED_OUTPUTS[@]}"; do
  if [ ! -s "${OUTPUT_ROOT}/${rel}" ]; then
    echo "[ERROR] Missing or empty expected output: ${OUTPUT_ROOT}/${rel}" >&2
    exit 4
  fi
done

echo "========================================================================="
echo " COMPLETE"
echo " run4c prediction cells : ${PRED_COUNT}/25"
echo " Point estimates        : ${OUTPUT_ROOT}/point_estimates.csv"
echo " Minimax regret         : ${OUTPUT_ROOT}/minimax_regret_summary.csv"
echo " Pairwise transfer      : ${OUTPUT_ROOT}/pairwise_transfer_common_targets.csv"
echo " Selection summary      : ${OUTPUT_ROOT}/candidate_selection_summary.txt"
echo " Master log             : ${MASTER_LOG}"
echo " Finished               : $(date -Is)"
echo "========================================================================="
