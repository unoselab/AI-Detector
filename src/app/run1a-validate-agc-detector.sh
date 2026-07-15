#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run1a-agc-detector-validate.sh
# -----------------------------------------------------------------------------
# Validate one fixed paper result:
#   CodeLlama-7B + SVM + AST
#   4,500-pair complexity-balanced experiment
#
# The script converts the held-out 900-row test CSV into raw Python files,
# runs agc_detector.py with the exact trained SVM pickle, and checks whether
# the detector reproduces the paper metrics after rounding to four decimals.
# 
# Usage:
# cd ~/project-workspace/ai_detector
# bash src/app/run1a-validate-agc-detector.sh > ./logs/run1a-validate-agc-detector-<TIME>.log
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TEST_CSV="src/ml_embeddings/data_codesearchnet/splits/codellama-7b_4500_complexity_stratified_maxlen2048/codesearchnet_codellama-7b_python_merged_4500/test_.csv"
MODEL_PICKLE="src/ml_embeddings/data_codesearchnet/models/codellama-7b_4500_complexity_stratified_maxlen2048/tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl"

OUT_ROOT="src/app/data_agc_detector_validation/codellama-7b_4500_complexity_stratified_maxlen2048/svm_ast"
SOURCE_DIR="${OUT_ROOT}/source_files"
PRED_DIR="${OUT_ROOT}/predictions"
MANIFEST_CSV="${OUT_ROOT}/manifest.csv"
PREDICTIONS_CSV="${OUT_ROOT}/predictions.csv"
METRICS_CSV="${OUT_ROOT}/metrics.csv"
SUMMARY_TXT="${OUT_ROOT}/summary.txt"

TS="$(date +'%Y%m%d_%H%M%S')"
LOG_FILE="src/logs/run1a-agc-detector-validate_${TS}.log"
mkdir -p "$(dirname "${LOG_FILE}")"
exec > >(tee -a "${LOG_FILE}") 2>&1

for path in "${TEST_CSV}" "${MODEL_PICKLE}" "src/app/agc_detector.py"; do
  if [ ! -f "${path}" ]; then
    echo "[ERROR] required file not found: ${path}" >&2
    exit 2
  fi
done

rm -rf "${OUT_ROOT}"
mkdir -p "${SOURCE_DIR}" "${PRED_DIR}"

cat <<INFO
============================================================
 run1a-agc-detector-validate.sh
   test csv     : ${TEST_CSV}
   model pickle : ${MODEL_PICKLE}
   embedding    : ast
   max len      : 2048
   output root  : ${OUT_ROOT}
   device       : ${DEVICE:-<auto>}
   log file     : ${LOG_FILE}
============================================================
INFO

# Build one raw .py file per held-out test row.
TEST_CSV="${TEST_CSV}" SOURCE_DIR="${SOURCE_DIR}" MANIFEST_CSV="${MANIFEST_CSV}" \
python - <<'PY'
import os
import pandas as pd


def normalize_label(value):
    text = str(value).strip().lower()
    if text in {"1", "1.0", "human", "hwc"}:
        return 1
    if text in {"0", "0.0", "lm", "ai", "agc"}:
        return 0
    raise ValueError(f"Unsupported label: {value!r}")


test_csv = os.environ["TEST_CSV"]
source_dir = os.environ["SOURCE_DIR"]
manifest_csv = os.environ["MANIFEST_CSV"]

header = pd.read_csv(test_csv, nrows=0).columns.tolist()
label_col = "actual label" if "actual label" in header else "label"
df = pd.read_csv(test_csv, usecols=["idx", "code", label_col])
df = df[["idx", "code", label_col]]

if len(df) != 900:
    raise SystemExit(f"[ERROR] expected 900 test rows, found {len(df)}")

rows = []
for row_no, row in enumerate(df.itertuples(index=False, name=None), start=1):
    idx, code, label = row
    file_name = f"sample_{row_no:04d}.py"
    file_path = os.path.join(source_dir, file_name)
    text = str(code)
    if not text.endswith("\n"):
        text += "\n"
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    rows.append({
        "file_name": file_name,
        "idx": str(idx),
        "actual_label": normalize_label(label),
    })

pd.DataFrame(rows).to_csv(manifest_csv, index=False)
print(f"Prepared {len(rows)} Python files")
print(f"Manifest: {manifest_csv}")
PY

DETECTOR_ARGS=(
  --input-dir "${SOURCE_DIR}"
  --pattern 'sample_*.py'
  --out-dir "${PRED_DIR}"
  --model-pickle "${MODEL_PICKLE}"
  --embedding ast
  --max-len 2048
)

if [ -n "${DEVICE:-}" ]; then
  DETECTOR_ARGS+=(--device "${DEVICE}")
fi

python src/app/agc_detector.py "${DETECTOR_ARGS[@]}"

# Aggregate detector outputs and compare them with the fixed paper row.
MANIFEST_CSV="${MANIFEST_CSV}" PRED_DIR="${PRED_DIR}" \
PREDICTIONS_CSV="${PREDICTIONS_CSV}" METRICS_CSV="${METRICS_CSV}" \
SUMMARY_TXT="${SUMMARY_TXT}" python - <<'PY'
import os
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

EXPECTED = {
    "acc": 0.7178,
    "human_f1": 0.7221,
    "ai_f1": 0.7133,
    "avg_f1": 0.7177,
    "auroc": 0.7950,
}

manifest = pd.read_csv(os.environ["MANIFEST_CSV"], dtype={"idx": str})
pred_dir = os.environ["PRED_DIR"]
rows = []

for row in manifest.itertuples(index=False):
    stem = os.path.splitext(row.file_name)[0]
    path = os.path.join(pred_dir, f"{stem}.predictions.tsv")
    pred_df = pd.read_csv(path, sep="\t")
    if len(pred_df) != 1:
        raise SystemExit(
            f"[ERROR] expected one top-level block in {row.file_name}, found {len(pred_df)}"
        )

    pred_row = pred_df.iloc[0]
    label = str(pred_row["pred_label"]).strip().lower()
    if label == "human":
        pred = 1
    elif label == "lm":
        pred = 0
    else:
        raise SystemExit(f"[ERROR] unsupported prediction label: {label!r}")

    rows.append({
        "idx": row.idx,
        "actual_label": int(row.actual_label),
        "pred": pred,
        "score": float(pred_row["score"]),
        "score_mode": str(pred_row["score_mode"]),
    })

predictions = pd.DataFrame(rows)
predictions.to_csv(os.environ["PREDICTIONS_CSV"], index=False)

y_true = predictions["actual_label"].to_numpy()
y_pred = predictions["pred"].to_numpy()
scores = predictions["score"].to_numpy()

human_f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
ai_f1 = f1_score(y_true, y_pred, pos_label=0, zero_division=0)
metrics = {
    "n_test": len(predictions),
    "acc": accuracy_score(y_true, y_pred),
    "human_f1": human_f1,
    "ai_f1": ai_f1,
    "avg_f1": (human_f1 + ai_f1) / 2,
    "auroc": roc_auc_score(y_true, scores),
}

pd.DataFrame([metrics]).to_csv(os.environ["METRICS_CSV"], index=False)
metric_match = all(
    round(metrics[name], 4) == round(value, 4)
    for name, value in EXPECTED.items()
)
decision_scores = set(predictions["score_mode"]) == {"decision"}
passed = metrics["n_test"] == 900 and metric_match and decision_scores

summary = [
    "CodeLlama-7B SVM + AST validation",
    "===================================",
    f"Test rows : {metrics['n_test']}",
    f"ACC       : {metrics['acc']:.4f}  expected {EXPECTED['acc']:.4f}",
    f"Human F1  : {metrics['human_f1']:.4f}  expected {EXPECTED['human_f1']:.4f}",
    f"AI F1     : {metrics['ai_f1']:.4f}  expected {EXPECTED['ai_f1']:.4f}",
    f"Avg. F1   : {metrics['avg_f1']:.4f}  expected {EXPECTED['avg_f1']:.4f}",
    f"AUROC     : {metrics['auroc']:.4f}  expected {EXPECTED['auroc']:.4f}",
    f"Score mode: {','.join(sorted(set(predictions['score_mode'])))}",
    f"Status    : {'PASS' if passed else 'FAIL'}",
]

with open(os.environ["SUMMARY_TXT"], "w", encoding="utf-8") as handle:
    handle.write("\n".join(summary) + "\n")

print("\n".join(summary))
print(f"Predictions: {os.environ['PREDICTIONS_CSV']}")
print(f"Metrics    : {os.environ['METRICS_CSV']}")
print(f"Summary    : {os.environ['SUMMARY_TXT']}")

if not passed:
    raise SystemExit(1)
PY

echo "Log        : ${LOG_FILE}"
