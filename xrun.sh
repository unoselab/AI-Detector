CSV_FILE="/home/user1-system12/project-workspace/ai_code_complexity_study_python/python_snapshots_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/block_predictions_treatment.csv"

python - "$CSV_FILE" <<'PY'
import csv
import sys
from collections import Counter

csv_file = sys.argv[1]
counts = Counter()
total = 0

with open(csv_file, "r", encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle)

    if "block_kind" not in (reader.fieldnames or []):
        raise SystemExit("ERROR: column 'block_kind' was not found.")

    for row in reader:
        value = (row.get("block_kind") or "").strip()
        counts[value if value else "(missing)"] += 1
        total += 1

print(f"Total data rows: {total:,}")
print()
print(f"{'block_kind':35s} {'count':>12s} {'percent':>10s}")
print("-" * 61)

for value, count in counts.most_common():
    percent = count / total * 100 if total else 0
    print(f"{value:35s} {count:12,d} {percent:9.2f}%")

print("-" * 61)
print(f"{'TOTAL':35s} {total:12,d} {100.00:9.2f}%")
PY

