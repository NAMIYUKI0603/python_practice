import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib
import os

# --- 1. 空間設定とデータの精製 ---
plt.rcParams['font.family'] = 'MS Gothic'
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("--- 記事用アセット（画像）生成エンジン起動 ---")

# 死亡DBの読み込みと「製造業」への純化
df = pd.read_csv("output/master_sibou_all_industries.csv", encoding='utf-8-sig', low_memory=False)
mfg_df = df[df['業種_大分類'] == '製造業'].copy()

# 欠損値と不要なノイズの排除
mfg_df = mfg_df.dropna(subset=['年', '発生時間'])
mfg_df['起因物_中分類'] = mfg_df['起因物_中分類'].fillna('不明')
mfg_df['発生時間'] = mfg_df['発生時間'].fillna('不明')

print(f"対象データ: 製造業の死亡事故 {len(mfg_df)} 件")

# --- 2. 視覚兵器①：10年推移と起因物の構造（積層型トレンド） ---
print("1/2: 10年推移グラフの生成中...")

# 年別の総件数と、主要な起因物（トップ3）のクロス集計
top_causes = mfg_df['起因物_中分類'].value_counts().nlargest(3).index.tolist()

# 上位3つ以外を「その他」にまとめる
mfg_df['起因物_表示用'] = mfg_df['起因物_中分類'].apply(lambda x: x if x in top_causes else 'その他')
trend_data = pd.crosstab(mfg_df['年'], mfg_df['起因物_表示用'])

# グラフ描画（積み上げ棒グラフ）
fig, ax = plt.subplots(figsize=(12, 7))
# 色のパターン設定（危険度を感じさせる赤〜グレーの配色）
colors = ['#8B0000', '#CD5C5C', '#F08080', '#D3D3D3'] 

trend_data.plot(kind='bar', stacked=True, color=colors, ax=ax, edgecolor='black')
plt.title("【製造業】死亡労災の10年推移と主要起因物の構造", fontsize=16, fontweight='bold')
plt.xlabel("発生年", fontsize=12)
plt.ylabel("死亡者数（人）", fontsize=12)
plt.legend(title='起因物（中分類）', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=0)
plt.tight_layout()

trend_img = os.path.join(OUTPUT_DIR, "trend_10years_mfg.png")
plt.savefig(trend_img, dpi=300)
plt.close()

# --- 3. 視覚兵器②：死の交差点ヒートマップ（マトリクス分析） ---
print("2/2: 時間帯×起因物のヒートマップ生成中...")

# 時間帯の表記揺れや順序を整理するためのリスト（存在するものだけ抽出）
time_order = sorted([t for t in mfg_df['発生時間'].unique() if '～' in str(t)])

# 上位10の起因物に絞る（Y軸が長くなりすぎるのを防ぐ）
top_10_causes = mfg_df['起因物_中分類'].value_counts().nlargest(10).index.tolist()
heatmap_df = mfg_df[mfg_df['起因物_中分類'].isin(top_10_causes)]

# クロス集計（マトリクスの生成）
matrix_data = pd.crosstab(heatmap_df['起因物_中分類'], heatmap_df['発生時間'])
# 存在する時間帯列だけを並び替え
matrix_data = matrix_data[[c for c in time_order if c in matrix_data.columns]]

# ヒートマップの描画
plt.figure(figsize=(14, 8))
# cmap='Reds' で件数が多いセルほど血のような濃い赤で染まる
sns.heatmap(matrix_data, annot=True, fmt="d", cmap="Reds", linewidths=.5, cbar_kws={'label': '死亡件数'})
plt.title("【製造業】起因物 × 発生時間帯の死のヒートマップ（濃い赤＝極大危険地帯）", fontsize=16, fontweight='bold')
plt.xlabel("発生時間帯", fontsize=12)
plt.ylabel("起因物（中分類）", fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()

heatmap_img = os.path.join(OUTPUT_DIR, "heatmap_time_vs_cause_mfg.png")
plt.savefig(heatmap_img, dpi=300)
plt.close()

print(f"[完了] 記事用アセットを {OUTPUT_DIR} に出力しました。")