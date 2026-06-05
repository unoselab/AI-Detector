python - <<'PY'
import pandas as pd
df = pd.read_csv("src/code-analyzer-tree-sitter/data_codesearchnet/starcoder2-7b/validsyntax_4500_complexity/codesearchnet_starcoder2-7b_python_merged_4500.csv")
print("rows:", len(df), "pairs:", len(df)//2)
print("human:", (df['label']=='human').sum(), "lm:", (df['label']=='lm').sum())
print("max line idx:", df['idx'].str.extract(r'line(\d+)')[0].astype(int).max())
PY