import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# --- 1. 空間設定とデータの精製 ---
# Windows環境での日本語フォント強制指定
plt.rcParams['font.family'] = 'MS Gothic'
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("--- 記事用アセット（画像）生成エンジン起動 ---")

df = pd.read_csv("output/master_sibou_all_industries.csv", encoding='utf-8-sig', low_memory=False)
mfg_df = df[df['業種_大分類'] == '製造業'].copy()

mfg_df = mfg_df.dropna(subset=['年', '発生時間'])
mfg_df['起因物_中分類'] = mfg_df['起因物_中分類'].fillna('不明')

# --- 発生時間の表記揺れ粉砕とゼロ埋め（00時台〜23時台） ---
def format_time(t_str):
    if pd.isna(t_str) or '不明' in str(t_str):
        return '不明'
    match = re.search(r'(\d+)', str(t_str))
    if match:
        hour = int(match.group(1))
        return f"{hour:02d}時台"
    return '不明'

mfg_df['発生時間_整形'] = mfg_df['発生時間'].apply(format_time)
mfg_df = mfg_df[mfg_df['発生時間_整形'] != '不明']

print(f"対象データ: 製造業の死亡事故 {len(mfg_df)} 件")

# --- 2. 視覚兵器①：10年推移と起因物の構造（面グラフ） ---
print("1/2: 10年推移グラフ（面グラフ）の生成中...")

top_causes = mfg_df['起因物_中分類'].value_counts().nlargest(3).index.tolist()
mfg_df['起因物_表示用'] = mfg_df['起因物_中分類'].apply(lambda x: x if x in top_causes else 'その他')

trend_data = pd.crosstab(mfg_df['年'], mfg_df['起因物_表示用'])

fig, ax = plt.subplots(figsize=(12, 7))
colors = ['#8B0000', '#CD5C5C', '#F08080', '#D3D3D3'] 

trend_data.plot(kind='area', stacked=True, color=colors, ax=ax, alpha=0.8)

plt.title("【製造業】死亡労災の10年推移と主要起因物の構造（面グラフ）", fontsize=16, fontweight='bold')
plt.xlabel("発生年", fontsize=12)
plt.ylabel("死亡者数（人）", fontsize=12)
plt.legend(title='起因物（中分類）', bbox_to_anchor=(1.05, 1), loc='upper left')

# 【バグ修正】内部の絶対座標（0, 1, 2...）に対して、文字列ラベル（H21, H22...）を強制的にマッピングする
plt.xticks(range(len(trend_data.index)), trend_data.index, rotation=0)
plt.xlim(0, len(trend_data.index) - 1)

plt.tight_layout()
trend_img = os.path.join(OUTPUT_DIR, "trend_10years_area_mfg.png")
plt.savefig(trend_img, dpi=300)
plt.close()

# --- 3. 視覚兵器②：死の交差点ヒートマップ（時間軸の整流化） ---
print("2/2: 時間帯×起因物のヒートマップ生成中...")

time_order = [f"{i:02d}時台" for i in range(24)]

top_10_causes = mfg_df['起因物_中分類'].value_counts().nlargest(10).index.tolist()
heatmap_df = mfg_df[mfg_df['起因物_中分類'].isin(top_10_causes)]

matrix_data = pd.crosstab(heatmap_df['起因物_中分類'], heatmap_df['発生時間_整形'])
matrix_data = matrix_data.reindex(columns=time_order, fill_value=0)

plt.figure(figsize=(15, 8))
sns.heatmap(matrix_data, annot=True, fmt="d", cmap="Reds", linewidths=.5, cbar_kws={'label': '死亡件数'})
plt.title("【製造業】起因物 × 発生時間帯の死のヒートマップ（完全整流化版）", fontsize=16, fontweight='bold')
plt.xlabel("発生時間帯（00時〜23時）", fontsize=12)
plt.ylabel("起因物（中分類）", fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()

heatmap_img = os.path.join(OUTPUT_DIR, "heatmap_time_vs_cause_mfg_fixed.png")
plt.savefig(heatmap_img, dpi=300)
plt.close()

print(f"[完了] 記事用アセットを {OUTPUT_DIR} に出力しました。")