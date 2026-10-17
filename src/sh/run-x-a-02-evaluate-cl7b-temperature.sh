#!/usr/bin/env bash
# A-02: Frozen CL-7B/SVM+AST evaluation on independent A-01-v4 matched prompts.
# Inputs: A-01-v4 analysis-v4 CSVs and original fitted SVM / AST / CodeT5+ files.
# Outputs: new output/run-x-a-02/v1, with read-only inputs and resumable embeddings.
# No earlier experiment shell wrapper is invoked.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"
MODE="${MODE:-preflight}"
ANALYSIS_DIR="${ANALYSIS_DIR:-$ROOT/output/run-x-a-01/v2/analysis-v4}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT/output/run-x-a-02/v1}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export CUDA_VISIBLE_DEVICES
ARGS=(--repo-root "$ROOT" --analysis-dir "$ANALYSIS_DIR" --output-dir "$OUTPUT_DIR" --mode "$MODE" --device "${DEVICE:-cuda}" --batch-size "${BATCH_SIZE:-16}" --bootstrap "${BOOTSTRAP:-20000}" --stat-seed "${STAT_SEED:-20260723}")
if [[ "${RESUME:-0}" == 1 ]]; then ARGS+=(--resume); fi
if [[ -n "${MODEL_FILE:-}" ]]; then ARGS+=(--model-file "$MODEL_FILE"); fi
"$PYTHON_BIN" -u "$ROOT/src/py/evaluate_cl7b_temperature_a01-v1.py" "${ARGS[@]}"
