import pandas as pd
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Salesforce/codet5p-110m-embedding", trust_remote_code=True)

df = pd.read_csv('ml_embeddings/data_codesearchnet/embeddings/codesearchnet_starcoder2-7b_python_merged_2250.csv',
                 usecols=['code'])
df['n_tokens'] = df['code'].astype(str).apply(lambda s: len(tok.encode(s, add_special_tokens=False)))
print(df['n_tokens'].describe(percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]))
print(f"truncated (>=512): {(df['n_tokens']>=512).sum()} / {len(df)}  ({(df['n_tokens']>=512).mean()*100:.1f}%)")




# import pandas as pd
# df = pd.read_csv('/home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/predictions/codesearchnet_lr_20260520_232005/codesearchnet_starcoder2-7b_python_merged__ast.csv')
# df['n_lines'] = df['code'].astype(str).str.count('\n') + 1
# df['bucket']  = pd.cut(df['n_lines'], [0, 5, 15, 1000],
#                       labels=['short', 'medium', 'long'])
# from sklearn.metrics import f1_score
# for b, g in df.groupby('bucket', observed=True):
#     if len(g) < 10: continue
#     hf1 = f1_score(g['actual label'], g['pred'], pos_label=1, zero_division=0)
#     af1 = f1_score(g['actual label'], g['pred'], pos_label=0, zero_division=0)
#     print(f"{b:6s} n={len(g):4d}  AvgF1={(hf1+af1)/2:.4f}")

# print("--------"*10)

# import pandas as pd
# df = pd.read_csv('/home/user1-system12/project-workspace/ai_detector/src/ml_embeddings/data_codesearchnet/predictions/codesearchnet_lr_20260520_232005/codesearchnet_starcoder2-7b_python_merged_2250__ast.csv')
# df['n_lines'] = df['code'].astype(str).str.count('\n') + 1
# df['bucket']  = pd.cut(df['n_lines'], [0, 5, 15, 1000],
#                       labels=['short', 'medium', 'long'])
# from sklearn.metrics import f1_score
# for b, g in df.groupby('bucket', observed=True):
#     if len(g) < 10: continue
#     hf1 = f1_score(g['actual label'], g['pred'], pos_label=1, zero_division=0)
#     af1 = f1_score(g['actual label'], g['pred'], pos_label=0, zero_division=0)
#     print(f"{b:6s} n={len(g):4d}  AvgF1={(hf1+af1)/2:.4f}")    

    