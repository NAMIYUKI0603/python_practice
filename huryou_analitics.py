import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# データの読み込み (日本語エンコーディングに注意)
df = pd.read_csv('不良集計（2022-2025）.csv', encoding='shift_jis')

# 日本語フォントの設定（文字化け対策: 環境に合わせてインストール等が必要です）
plt.rcParams['font.family'] = 'Meiryo' # Windowsの場合

# -----------------------------------------
# 1. ヒートマップ：月度 × 不良現象の「不良数」合計
# -----------------------------------------
plt.figure(figsize=(10, 6))
# クロス集計表を作成
pivot_df = df.pivot_table(index='現象', columns='月度', values='不良数', aggfunc='sum', fill_value=0)
sns.heatmap(pivot_df, cmap='Reds', annot=True, fmt='g')
plt.title('月度別・現象別の不良数ヒートマップ')
plt.show()

# -----------------------------------------
# 2. バイオリンプロット：作業分類ごとの不良数のばらつき
# -----------------------------------------
plt.figure(figsize=(12, 6))
sns.violinplot(x='作業分類', y='不良数', data=df)
plt.title('作業分類ごとの不良数の分布')
plt.xticks(rotation=45)
plt.show()