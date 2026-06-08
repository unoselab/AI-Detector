python - <<'PY'
import pandas as pd

path = "src/code-analyzer-tree-sitter/data_codesearchnet/gemma/validsyntax_4500_complexity/codesearchnet_gemma_python_merged_4500.csv"
df = pd.read_csv(path)

print("rows:", len(df))
print("pairs:", len(df) // 2)
print(df["label"].value_counts())
print("odd rows?", len(df) % 2)
PY