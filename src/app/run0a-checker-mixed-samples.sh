#!/usr/bin/env bash
set -euo pipefail

# Check that generated mixed_sample_*.py files align with their .labels.tsv files.
#
# Usage:
#   ./run0a-checker-mixed-samples.sh
#   ./run0a-checker-mixed-samples.sh mixed_samples_50x6
#   ./run0a-checker-mixed-samples.sh mixed_samples_50x6/mixed_sample_001.py
#   ./run0a-checker-mixed-samples.sh mixed_samples_50x6/mixed_sample_001.labels.tsv
#   ./run0a-checker-mixed-samples.sh mixed_samples_50x6/mixed_sample_001.labels.tsv mixed_samples_50x6/mixed_sample_001.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

CHECKER_SRC="src/app/checker_mixed_samples.java"
BUILD_DIR="src/app/.checker_build"

DEFAULT_TARGET="src/app/mixed_samples_50x6"

mkdir -p "${BUILD_DIR}"

echo "============================================================"
echo " run0a-checker-mixed-samples.sh"
echo "   repo root   : ${REPO_ROOT}"
echo "   checker src : ${CHECKER_SRC}"
echo "   build dir   : ${BUILD_DIR}"
echo "   default     : ${DEFAULT_TARGET}"
echo "============================================================"
echo

javac -encoding UTF-8 -d "${BUILD_DIR}" "${CHECKER_SRC}"

if [ "$#" -eq 0 ]; then
  java -cp "${BUILD_DIR}" checker_mixed_samples "${DEFAULT_TARGET}"
else
  ARGS=()
  for a in "$@"; do
    if [[ "${a}" = /* ]]; then
      ARGS+=("${a}")
    elif [ -e "${a}" ]; then
      ARGS+=("${a}")
    elif [ -e "src/app/${a}" ]; then
      ARGS+=("src/app/${a}")
    else
      ARGS+=("${a}")
    fi
  done

  java -cp "${BUILD_DIR}" checker_mixed_samples "${ARGS[@]}"
fi
