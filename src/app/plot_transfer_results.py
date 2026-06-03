#!/usr/bin/env python3
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 고정된 모델 순서 및 깔끔한 논문용 이름 매핑
MODEL_ORDER = [
    "codellama-7b",
    "gemma",
    "gpt-oss",
    "starcoder2-15b-instruct-v0.1",
    "starcoder2-7b"
]

SHORT_NAMES = {
    "codellama-7b": "CodeLlama-7B",
    "gemma": "Gemma",
    "gpt-oss": "GPT-OSS",
    "starcoder2-15b-instruct-v0.1": "SC2-15B",
    "starcoder2-7b": "SC2-7B"
}

def load_and_stitch_data():
    """5개의 csv 파일을 읽어서 하나의 긴 데이터프레임으로 통합"""
    all_rows = []
    for clf in MODEL_ORDER:
        csv_path = f"src/app/data_mixed_samples_transfer/clf-{clf}/agc_transfer.csv"
        if not os.path.exists(csv_path):
            csv_path = f"data_mixed_samples_transfer/clf-{clf}/agc_transfer.csv"
            
        if not os.path.exists(csv_path):
            print(f"[Warning] Missing file: {csv_path}")
            continue
            
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            tgt = row['target']
            # Target 이름 정규화
            tgt_matched = None
            for m in MODEL_ORDER:
                if m == tgt or m.startswith(tgt) or tgt.startswith(m.split('-')):
                    tgt_matched = m
                    break
            
            if tgt_matched:
                all_rows.append({
                    "Classifier": SHORT_NAMES[clf],
                    "Target": SHORT_NAMES[tgt_matched],
                    "AUROC": float(row['auroc']),
                    "AGC_F1": float(row['agc_f1']),
                    "is_diagonal": (clf == tgt_matched)
                })
    return pd.DataFrame(all_rows)

def plot_candidate_a_heatmap(df, metric="AUROC"):
    """Candidate A: 전이 성능 히트맵 매트릭스 그리기"""
    pivot_df = df.pivot(index="Classifier", columns="Target", values=metric)
    pivot_df = pivot_df.reindex(index=[SHORT_NAMES[m] for m in MODEL_ORDER], 
                                columns=[SHORT_NAMES[m] for m in MODEL_ORDER])
    
    plt.figure(figsize=(7, 5.5))
    sns.set_theme(style="white")
    
    # 논문 스타일의 컬러맵 (AUROC는 Blues나 Viridis가 잘 어울립니다)
    ax = sns.heatmap(pivot_df, annot=True, fmt=".4f", cmap="Blues", cbar_kws={'label': metric},
                     linewidths=.5, annot_kws={"size": 11, "weight": "bold"})
    
    # 대각선(자체 성능) 강조를 위한 가이드 라인 긋기
    for i in range(len(pivot_df)):
        ax.add_patch(plt.Rectangle((i, i), 1, 1, fill=False, edgecolor='red', lw=2.5, clip_on=False))
        
    plt.title(f"Cross-Generator Transfer Matrix ({metric})", fontsize=13, pad=15, weight='bold')
    plt.ylabel("Trained Classifier (Source)", fontsize=11, labelpad=10)
    plt.xlabel("Tested Generator (Target)", fontsize=11, labelpad=10)
    plt.tight_layout()
    
    filename = f"transfer_heatmap_{metric.lower()}.pdf"
    plt.savefig(filename, dpi=300)
    print(f"[Success] Saved Heatmap Matrix to: {filename}")
    plt.close()

def plot_candidate_b_gap_chart(df, metric="AUROC"):
    """Candidate B: 일반화 간극(Generalization Gap) 덤벨 그래프 그리기"""
    classifiers = [SHORT_NAMES[m] for m in MODEL_ORDER]
    
    self_vals = []
    transfer_means = []
    
    for clf in classifiers:
        # 자기 자신 점수
        self_val = df[(df['Classifier'] == clf) & (df['Target'] == clf)][metric].values
        # 남의 AI 점수 평균 (순수 전이)
        transfer_mean = df[(df['Classifier'] == clf) & (df['Target'] != clf)][metric].mean()
        
        self_vals.append(self_val)
        transfer_means.append(transfer_mean)
        
    gap_df = pd.DataFrame({
        "Classifier": classifiers,
        "Self": self_vals,
        "Transfer_Avg": transfer_means,
        "Gap": np.array(self_vals) - np.array(transfer_means)
    }).sort_values("Transfer_Avg", ascending=True) # 전이 평균 순 정렬
    
    plt.figure(figsize=(6.5, 4.5))
    sns.set_style("whitegrid")
    
    # 덤벨 바 라인 그리기
    plt.hlines(y=gap_df['Classifier'], xmin=gap_df['Transfer_Avg'], xmax=gap_df['Self'], 
               color='grey', alpha=0.5, linewidth=2.5)
    
    # 점 찍기 (Self = 파란색 스타, Transfer = 주황색 동그라미)
    plt.scatter(gap_df['Self'], gap_df['Classifier'], color='darkblue', alpha=0.9, s=120, 
                marker='*', label='In-Distribution (Self)')
    plt.scatter(gap_df['Transfer_Avg'], gap_df['Classifier'], color='darkorange', alpha=0.9, s=100, 
                marker='o', label='Pure Transfer Avg (Off-Diag)')
    
    # 간극 수치 텍스트 표시
    for idx, row in gap_df.iterrows():
        mid_x = (row['Self'] + row['Transfer_Avg']) / 2
        plt.text(mid_x, row['Classifier'], f"  Gap: {row['Gap']:.3f}", 
                 va='bottom', ha='center', fontsize=9, color='brown', weight='bold')
                 
    plt.title(f"Generalization Gap Analysis ({metric})", fontsize=12, pad=15, weight='bold')
    plt.xlabel(f"{metric} Score", fontsize=11)
    plt.xlim(df[metric].min() - 0.05, max(df[metric].max() + 0.05, 1.0))
    plt.legend(loc='lower left', frameon=True)
    plt.tight_layout()
    
    filename = f"transfer_gap_{metric.lower()}.pdf"
    plt.savefig(filename, dpi=300)
    print(f"[Success] Saved Generalization Gap Chart to: {filename}")
    plt.close()

def print_latex_matrix(df, metric="AUROC"):
    """논문에 바로 집어넣을 수 있는 전이 매트릭스 LaTeX 코드 출력"""
    pivot_df = df.pivot(index="Classifier", columns="Target", values=metric)
    clfs = [SHORT_NAMES[m] for m in MODEL_ORDER]
    pivot_df = pivot_df.reindex(index=clfs, columns=clfs)
    
    print("\n" + "="*80)
    print(f" LaTeX Code for {metric} Transfer Matrix Table")
    print("="*80)
    print("\\begin{table}[htbp]")
    print("\\centering")
    print(f"\\caption{{Cross-Generator Evaluation Matrix ({metric})}}")
    print(f"\\label{{tab:transfer_matrix_{metric.lower()}}}")
    print("\\begin{tabular}{lcccccc}")
    print("\\hline")
    print("\\textbf{Classifier} & " + " & ".join([f"\\textbf{{{c}}}" for c in clfs]) + " & \\textbf{Pure Transfer Avg} \\\\ \\hline")
    
    for clf in clfs:
        row_str = f"\\textbf{{{clf}}}"
        pure_vals = []
        for tgt in clfs:
            val = pivot_df.loc[clf, tgt]
            if clf == tgt:
                row_str += f" & \\textbf{{{val:.4f}}}"
            else:
                row_str += f" & {val:.4f}"
                pure_vals.append(val)
        row_str += f" & {np.mean(pure_vals):.4f} \\\\"
        print(row_str)
        
    print("\\hline")
    print("\\end{tabular}")
    print("\\end{table}\n")

if __name__ == "__main__":
    data = load_and_stitch_data()
    if len(data) == 0:
        print("[Error] No data loaded. Check your file paths.")
    else:
        # 1. 가장 중요한 AUROC 기반 그래프 및 테이블 생성
        plot_candidate_a_heatmap(data, metric="AUROC")
        plot_candidate_b_gap_chart(data, metric="AUROC")
        print_latex_matrix(data, metric="AUROC")
        
        # 2. 필요시 AGC F1-Score 기반으로도 생성 (주석 해제 후 사용 가능)
        plot_candidate_a_heatmap(data, metric="AGC_F1")
        plot_candidate_b_gap_chart(data, metric="AGC_F1")