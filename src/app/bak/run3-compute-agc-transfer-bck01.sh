#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run3-compute-agc-transfer.sh
# -----------------------------------------------------------------------------
# Cross-generator TRANSFER evaluation.
#
# Holds ONE classifier fixed (default: GPT-OSS) and scores the existing 50x6
# mixed-sample .py sets of OTHER generators with it. This isolates the
# classifier as the only changed variable: the input .py files are reused
# unchanged from data_mixed_samples/<target>/50x6/.
#
# The classifier's OWN generator is skipped (that is the matched diagonal,
# already produced by run1-agc-detector.sh).
#
# Outputs (never collide with matched results):
#   data_mixed_samples_transfer/clf-<CLF_GEN>/<target>/50x6/predictions/
#
# Usage
#   bash src/app/run3-compute-agc-transfer.sh
#   CLF_GEN=starcoder2-15b-instruct-v0.1 bash src/app/run3-compute-agc-transfer.sh
# =============================================================================


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/src/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run3-compute-agc-transfer_${TS}.log}"
mkdir -p "${LOG_DIR}"

pwd

cd ./src/app/compute-agc-transfer-summary
java LogSummarizer "${LOG_FILE}"