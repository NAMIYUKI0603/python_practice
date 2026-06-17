import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime

# --- 1. 空間設計とデータの精製 ---
# Windows標準の「MS Gothic」または環境に構築した「BIZ-UDGothicR.ttc」等を指定せよ
plt.rcParams['font.family'] = 'MS Gothic'

# 成果物の出荷先をアセット用フォルダに固定
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

current_time = datetime.now().strftime("%Y%m%d_%H%M")

print(f"--- 記事用アセット（画像）生成エンジン起動 [{current_time}] ---")

# ★【構造確定】inputフォルダ内のマスターデータを直接指定
INPUT_CSV = "input/死傷労災_製造業.csv" 

# 文字コードエラーの自動リカバリー読込
if not os.path.exists(INPUT_CSV):
    print(f"[異常終了] 指定されたマスターCSVが発見できません: {INPUT_CSV}")
    print("  └ 統合・クレンジング処理が完了しているか、ファイル名が正しいか直ちに確認せよ。")
    exit()

try:
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig', low_memory=False)
except UnicodeDecodeError:
    print("  └ [通知] utf-8-sigでエラーを検知。cp932（Shift-JIS拡張）に切り替えて読み込みます...")
    df = pd.read_csv(INPUT_CSV, encoding='cp932', low_memory=False)

# 特定の業界へのフィルタリングを一切行わず、全業種のデータをフラットに集計
clean_df = df.dropna(subset=['年', '発生時間']).copy()
clean_df['起因物_中分類'] = clean_df['起因物_中分類'].fillna('不明')

# --- 発生時間の表記揺れ粉砕とゼロ埋め（00時台〜23時台） ---
def format_time(t_str):
    if pd.isna(t_str) or '不明' in str(t_str):
        return '不明'
    if '8～7' in str(t_str):
        return '不明'
    match = re.search(r'(\d+)', str(t_str))
    if match:
        hour = int(match.group(1))
        return f"{hour:02d}時台"
    return '不明'

clean_df['発生時間_整形'] = clean_df['発生時間'].apply(format_time)
clean_df = clean_df[clean_df['発生時間_整形'] != '不明']

record_count = len(clean_df)
print(f"解析対象データ総数 (全業種丸ごと): {record_count} 件")

# --- 2. 視覚兵器①：経年推移と主要起因物の構造（面グラフ / トップ5抽出） ---
print("1/2: 経年推移グラフ（面グラフ）の生成中...")

# 発生件数順に真のトップ5をリスト化
top_causes = clean_df['起因物_中分類'].value_counts().nlargest(5).index.tolist()
clean_df['起因物_表示用'] = clean_df['起因物_中分類'].apply(lambda x: x if x in top_causes else 'その他')

# クロス集計
trend_data = pd.crosstab(clean_df['年'], clean_df['起因物_表示用'])

# 時系列（H24～R3）が歪まないよう厳格に順序を定義して再配列
year_order = ['H24', 'H25', 'H26', 'H27', 'H28', 'H29', 'H30', 'H31', 'R1', 'R2', 'R3']
year_order = [y for y in year_order if y in trend_data.index]  
trend_data = trend_data.reindex(year_order)

# 列の並び順を「トップ1〜5 ＋ その他」に強制再配列
ordered_cols = top_causes + ['その他']
trend_data = trend_data[ordered_cols]

# subplotsを用いた安全なキャンバス設計
fig, ax = plt.subplots(figsize=(12, 7))

# グラデーションカラー：1位(極濃) → 2位(濃) → 3位(赤) → 4位(薄赤) → 5位(極薄) → その他(グレー)
colors = ['#5c0000', '#8a0000', '#b80000', '#e60000', '#ff4d4d', '#D3D3D3'] 

trend_data.plot(kind='area', stacked=True, color=colors, ax=ax, alpha=0.8)

plt.title("死傷労働災害の経年推移と主要起因物の構造（上位5分類）", fontsize=16, fontweight='bold')
plt.xlabel("発生年", fontsize=12)
plt.ylabel("死傷者数（人）", fontsize=12)
plt.legend(title='起因物（中分類）', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.xticks(range(len(trend_data.index)), trend_data.index, rotation=0)
plt.xlim(0, len(trend_data.index) - 1)
plt.tight_layout()

trend_img = os.path.join(OUTPUT_DIR, f"trend_years_area_sisyou_{current_time}.png")
plt.savefig(trend_img, dpi=300)
plt.close()

# --- 3. 視覚兵器②：時間軸ヒートマップ（時間軸・起因物軸の完全整流化） ---
print("2/2: 時間帯×起因物のヒートマップ生成中...")

time_order = [f"{i:02d}時台" for i in range(24)]

# 上位10位の主要起因物を抽出
top_10_causes = clean_df['起因物_中分類'].value_counts().nlargest(10).index.tolist()
heatmap_df = clean_df[clean_df['起因物_中分類'].isin(top_10_causes)]

matrix_data = pd.crosstab(heatmap_df['起因物_中分類'], heatmap_df['発生時間_整形'])
matrix_data = matrix_data.reindex(columns=time_order, fill_value=0)
matrix_data = matrix_data.reindex(top_10_causes) # 縦軸（起因物）も発生件数が多い順にソート

# subplotsを用いた安全なキャンバス設計
fig, ax = plt.subplots(figsize=(15, 8))
sns.heatmap(matrix_data, annot=True, fmt="d", cmap="Reds", linewidths=.5, cbar_kws={'label': '死傷件数'}, ax=ax)

plt.title("主要起因物 × 発生時間帯の死傷労働災害ヒートマップ", fontsize=16, fontweight='bold')
plt.xlabel("発生時間帯（00時〜23時）", fontsize=12)
plt.ylabel("起因物（中分類）", fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()

heatmap_img = os.path.join(OUTPUT_DIR, f"heatmap_time_vs_cause_sisyou_{current_time}.png")
plt.savefig(heatmap_img, dpi=300)
plt.close()

print(f"\n[大成功] 全業種対応のビジュアルアセットが出荷されました。")
print(f"  └ 経年推移グラフ : {os.path.abspath(trend_img)}")
print(f"  └ 死傷ヒートマップ : {os.path.abspath(heatmap_img)}")