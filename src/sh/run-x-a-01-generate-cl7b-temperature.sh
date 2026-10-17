#!/usr/bin/env bash
# run-x-a-01-generate-cl7b-temperature.sh
# Purpose: A-01 protocol-v4 matched-prompt temperature sensitivity revision.
# Generation remains the frozen v2 pipeline (same plan/checkpoints/model).
# Primary evaluation: same HWC prompt; AST-valid AGC at ALL three temperatures.
# Secondary evaluation: 100-200 generated-length bins, conditional on quotas.
# Python 3.12 evaluates AST; Python 3.11 owns GPU generation.
# Never change the frozen v2 generator Python or its run_spec SHA256.
# Inputs (read only):
#   INPUT_JSONL: CodeSearchNet original_string dataset
#   EXCLUSION_CSV: historical CL-7B matched human/AGC CSV (required)
# Outputs (new v2 path only):
#   OUT/plan.jsonl, OUT/run_spec.json, OUT/preflight_qc.json
#   OUT/smoke/{checkpoints,model_metadata,generation_qc.json}
#   OUT/production/{checkpoints,model_metadata,pilot_qc.json,accepted_pool.csv,generation_qc.json}
#   OUT/ast_plan_qc_python312.json, OUT/{smoke,production}/ast_*_qc_python312.json
#   logs/run-x-a-01/run-x-a-01-v2-*.log
# The legacy generation algorithm was copied/adapted into the independent
# Python implementation. No existing wrapper/Python is called.
# Existing v1 files and checkpoint directory are never modified.
# Python 3.12 AST audit runs as an additional standalone check; the v2 generator
# and its frozen plan/script SHA256 remain unchanged by this wrapper update.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
SCRIPT="$ROOT/src/py/generate_cl7b_temperature.py"
AST_SCRIPT="$ROOT/src/py/audit_cl7b_ast.py"
REVIEW_SCRIPT="$ROOT/src/py/analyze_cl7b_temperature.py"
MODE="${MODE:-preflight}"
PYTHON="${PYTHON:-python}"
# Separate Python 3.12.13 AST validation from Python 3.11 GPU generation.
PYTHON_AST_BIN="${PYTHON_AST_BIN:-$HOME/miniconda3/envs/agcparse312/bin/python}"
MODEL_ID="${MODEL_ID:-codellama/CodeLlama-7b-hf}"
INPUT_JSONL="${INPUT_JSONL:-$ROOT/data/CodeSearchNet/python/train.jsonl}"
EXCLUSION_CSV="${EXCLUSION_CSV:-$ROOT/src/code-analyzer-tree-sitter/data_codesearchnet/codellama-7b/validsyntax/codesearchnet_codellama-7b_python_merged_4500.csv}"
OUT="${OUT:-$ROOT/output/run-x-a-01/v2}"
V1_OUT="${V1_OUT:-$ROOT/output/run-x-a-01/v1}"
POOL_PER_BUCKET="${POOL_PER_BUCKET:-200}"
PILOT_PER_BUCKET="${PILOT_PER_BUCKET:-20}"
SEED="${SEED:-20260723}"
TOP_P="${TOP_P:-0.95}"
GPU_IDS="${GPU_IDS:-0,1,2}"
LOG_DIR="${LOG_DIR:-$ROOT/logs/run-x-a-01}"

[[ -f "$SCRIPT" ]] || { echo "[ERROR] Missing A-01 Python script: $SCRIPT" >&2; exit 2; }
[[ -f "$AST_SCRIPT" ]] || { echo "[ERROR] Missing independent AST auditor: $AST_SCRIPT" >&2; exit 2; }
[[ -f "$REVIEW_SCRIPT" ]] || { echo "[ERROR] Missing v4 protocol reviewer: $REVIEW_SCRIPT" >&2; exit 2; }
if [[ ! -x "$PYTHON_AST_BIN" ]]; then
  echo "[ERROR] PYTHON_AST_BIN is not executable: $PYTHON_AST_BIN" >&2
  exit 2
fi
"$PYTHON_AST_BIN" "$AST_SCRIPT" --phase self-test
"$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --phase self-test
printf '[A-01-v4] MODE=%s PYTHON=%s\n' "$MODE" "$("$PYTHON" --version 2>&1)"
printf '[SOURCE] %s sha256=%s\n' "$SCRIPT" "$(sha256sum "$SCRIPT" | awk '{print $1}')"
printf '[AST] PYTHON_AST_BIN=%s version=%s\n' "$PYTHON_AST_BIN" "$("$PYTHON_AST_BIN" --version 2>&1)"
printf '[INPUT] train=%s\n[EXCLUSION] paired CSV=%s\n[OUTPUT] %s\n' "$INPUT_JSONL" "$EXCLUSION_CSV" "$OUT"
printf '[PROTOCOL] CL-7B T={0.2,0.4,0.6} top_p=%s max_input=128 max_new=512 seed=%s\n' "$TOP_P" "$SEED"
printf '[DESIGN] %s reference-HWC candidates per bucket; %s per bucket in pilot\n' "$POOL_PER_BUCKET" "$PILOT_PER_BUCKET"
echo '[PROTOCOL-v4] Primary: same prompt, all three Python-3.12-AST-valid; no generated-body length cutoff.'
echo '[PROTOCOL-v4] Secondary: 100..200 generated-body bins; export balanced CSV only if all quotas met.' 

case "$MODE" in
  self-test)
    "$PYTHON" "$SCRIPT" --mode self-test
    ;;
  preflight)
    "$PYTHON" "$SCRIPT" --mode preflight --train "$INPUT_JSONL" \
      --exclude-csv "$EXCLUSION_CSV" --out "$OUT" --model "$MODEL_ID" \
      --pool-per-bucket "$POOL_PER_BUCKET" --pilot-per-bucket "$PILOT_PER_BUCKET" \
      --seed "$SEED" --top-p "$TOP_P"
    "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase plan
    ;;
  audit-v1)
    "$PYTHON" "$SCRIPT" --mode audit-v1 --v1-out "$V1_OUT"
    ;;
  check)
    "$PYTHON" "$SCRIPT" --mode check --out "$OUT"
    "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase check
    ;;
  review-pilot)
    "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase pilot
    "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase pilot
    ;;
  export)
    # Full verification and independent revision-v4 primary/secondary exports.
    "$PYTHON" "$SCRIPT" --mode verify --out "$OUT"
    "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase full
    "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase full
    ;;
  pilot-review)
    "$PYTHON" "$SCRIPT" --mode pilot-review --out "$OUT"
    "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase pilot
    "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase pilot
    ;;
  verify)
    "$PYTHON" "$SCRIPT" --mode verify --out "$OUT"
    "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase full
    "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase full
    ;;
  verify-smoke)
    "$PYTHON" "$SCRIPT" --mode verify --out "$OUT" --smoke
    "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase smoke
    ;;
  ast-plan|ast-smoke|ast-pilot|ast-full)
    phase="${MODE#ast-}"
    "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase "$phase"
    ;;
  smoke|pilot|full)
    if [[ ! -f "$OUT/run_spec.json" || ! -f "$OUT/plan.jsonl" ]]; then
      echo '[ERROR] First run MODE=preflight.' >&2
      exit 2
    fi
    if [[ "$MODE" == full ]]; then
      # Explicit human approval remains mandatory before a 3-GPU full run.
      if [[ "${APPROVE_FULL:-0}" != 1 ]]; then
        echo '[ERROR] Set APPROVE_FULL=1 only after reviewing analysis-v4/pilot_review.json.' >&2
        exit 2
      fi
      # Re-evaluate the 600 existing pilot checkpoints using the new matching
      # criterion, instead of trusting the obsolete v2 length-acceptance gate.
      "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase pilot
      "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase pilot
      "$PYTHON" - "$OUT/analysis-v4/pilot_review.json" "$OUT/run_spec.json" <<'PYTHON_GATE'
import json
import sys
from pathlib import Path
review = json.loads(Path(sys.argv[1]).read_text())
spec = json.loads(Path(sys.argv[2]).read_text())
assert review['plan_sha256'] == spec['plan_sha256'], 'Pilot plan checksum mismatch'
assert review['selection_size'] == spec['pilot_size'], 'Pilot size mismatch'
assert review['complete_triplets'] == spec['pilot_size'], 'Incomplete pilot checkpoints'
assert review['recommend_full'] is True, 'v4 matched-prompt pilot gate failed'
PYTHON_GATE
    fi
    IFS=',' read -r -a physical_gpus <<< "$GPU_IDS"
    if [[ "${#physical_gpus[@]}" -ne 3 ]]; then
      echo '[ERROR] GPU_IDS must contain exactly three physical GPU indices.' >&2
      exit 2
    fi
    mkdir -p "$LOG_DIR"
    stamp="$(date +%Y%m%d-%H%M%S)-$$"
    tags=(t02 t04 t06)
    pids=()
    cleanup() {
      # Stop only child GPU jobs created by this specific wrapper invocation.
      for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
      wait 2>/dev/null || true
    }
    trap 'cleanup; exit 130' INT
    trap 'cleanup; exit 143' TERM
    for idx in 0 1 2; do
      tag="${tags[$idx]}"
      gpu="${physical_gpus[$idx]}"
      log_file="$LOG_DIR/run-x-a-01-v2-${MODE}-${stamp}-${tag}-gpu${gpu}.log"
      opts=()
      [[ "$MODE" != smoke ]] || opts+=(--smoke)
      [[ "$MODE" != pilot ]] || opts+=(--pilot)
      CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" "$SCRIPT" --mode worker \
        --tag "$tag" --model "$MODEL_ID" --out "$OUT" "${opts[@]}" \
        > "$log_file" 2>&1 &
      pids+=("$!")
      printf '[WORKER] %s gpu=%s pid=%s log=%s\n' "$tag" "$gpu" "${pids[$idx]}" "$log_file"
    done
    failed=0
    for idx in 0 1 2; do
      if ! wait "${pids[$idx]}"; then
        echo "[ERROR] GPU worker ${tags[$idx]} failed" >&2
        failed=1
      fi
    done
    trap - INT TERM
    for idx in 0 1 2; do
      echo "[TAIL] ${tags[$idx]} GPU ${physical_gpus[$idx]}"
      tail -n 12 "$LOG_DIR/run-x-a-01-v2-${MODE}-${stamp}-${tags[$idx]}-gpu${physical_gpus[$idx]}.log" || true
    done
    [[ "$failed" -eq 0 ]] || exit 1
    if [[ "$MODE" == smoke ]]; then
      "$PYTHON" "$SCRIPT" --mode verify --out "$OUT" --smoke
      "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase smoke
    elif [[ "$MODE" == pilot ]]; then
      "$PYTHON" "$SCRIPT" --mode pilot-review --out "$OUT"
      "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase pilot
      "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase pilot
    else
      "$PYTHON" "$SCRIPT" --mode verify --out "$OUT"
      "$PYTHON_AST_BIN" "$AST_SCRIPT" --out "$OUT" --phase full
      "$PYTHON_AST_BIN" "$REVIEW_SCRIPT" --out "$OUT" --phase full
    fi
    ;;
  *)
    echo '[ERROR] MODE must be audit-v1, self-test, preflight, smoke, pilot, check, review-pilot, export, pilot-review, full, verify, verify-smoke, ast-plan, ast-smoke, ast-pilot, ast-full' >&2
    exit 2
    ;;
esac
