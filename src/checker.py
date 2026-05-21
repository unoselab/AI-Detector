import pandas as pd
df = pd.read_csv('src/ml_embeddings/predictions/codesearchnet_starcoder2-7b_python_merged__ast.csv')
df['n_lines'] = df['code'].astype(str).str.count('\n') + 1
df['bucket']  = pd.cut(df['n_lines'], [0, 5, 15, 1000],
                      labels=['short', 'medium', 'long'])
from sklearn.metrics import f1_score
for b, g in df.groupby('bucket', observed=True):
    if len(g) < 10: continue
    hf1 = f1_score(g['actual label'], g['pred'], pos_label=1, zero_division=0)
    af1 = f1_score(g['actual label'], g['pred'], pos_label=0, zero_division=0)
    print(f"{b:6s} n={len(g):4d}  AvgF1={(hf1+af1)/2:.4f}")