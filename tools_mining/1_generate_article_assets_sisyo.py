import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime

# --- 1. 空間設計と抽出条件（ここを毎回書き換えて狙い撃つ） ---
plt.rcParams['font.family'] = 'MS Gothic' # Windows標準フォント

INPUT_CSV = "input/master_sisyou_all_cleaned.csv" 
OUTPUT_DIR = "output_assets"  
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ★★★ フィルター条件設定（フル階層・複数指定対応版） ★★★
# 複数指定したい場合はリスト形式 ["A", "B"] で記述。全件対象の場合は空リスト [] を指定。

# 【業種フィルター】
TARGET_IND_LARGE  = ["製造業"]                      # 業種_大分類
TARGET_IND_MEDIUM = ["金属製品製造業"]                              # 業種_中分類
TARGET_IND_SMALL  = []                              # 業種_小分類

# 【起因物フィルター】
TARGET_CAUSE_LARGE  = []                            # 起因物_大分類
TARGET_CAUSE_MEDIUM = ["金属加工用機械"]            # 起因物_中分類
TARGET_CAUSE_SMALL  = []                            # 起因物_小分類

# 【事故の型フィルター】 ★★★ 新規追加の狙撃兵器 ★★★
TARGET_ACCIDENT_TYPE = []                           # 事故の型（例: ["はさまれ、巻き込まれ", "転倒", "切れ物との接触"]）

# 【状況・属性フィルター】
TARGET_HOURS = []                                   # 発生時間帯（例: ["08時台", "10時台"]）
TARGET_AGE_GROUPS = []                              # 年代（例: ["50代", "60代"]）

current_time = datetime.now().strftime("%Y%m%d_%H%M")
print(f"--- スナイパー型アセット生成エンジン（事故の型フィルター実装版）起動 [{current_time}] ---")

# --- 2. データ整形ロジック ---
def format_time(t_str):
    if pd.isna(t_str) or '不明' in str(t_str) or '8～7' in str(t_str):
        return '不明'
    match = re.search(r'(\d+)', str(t_str))
    if match:
        hour = int(match.group(1))
        return f"{hour:02d}時台"
    return '不明'

def categorize_age(age_val):
    if pd.isna(age_val) or str(age_val).strip() == '不明':
        return '不明'
    try:
        age = int(float(age_val))
        if age < 20: 
            return '10代以下'
        elif age >= 70: 
            return '70代以上'
        else: 
            return f"{age // 10 * 10}代"
    except:
        return '不明'

# --- 3. データの読み込みと前処理 ---
if not os.path.exists(INPUT_CSV):
    print(f"[異常終了] マスターCSVが見つかりません: {INPUT_CSV}")
    exit()

try:
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig', low_memory=False)
except UnicodeDecodeError:
    df = pd.read_csv(INPUT_CSV, encoding='cp932', low_memory=False)

df = df.dropna(subset=['災害状況', '年', '発生時間'])
df['発生時間_整形'] = df['発生時間'].apply(format_time)
df = df[df['発生時間_整形'] != '不明']

if '年齢' in df.columns:
    df['年代'] = df['年齢'].apply(categorize_age)

# --- 4. フィルターの容赦ない適用（全階層対応） ---
filtered_df = df.copy()
filter_names = []

if TARGET_IND_LARGE:
    filtered_df = filtered_df[filtered_df['業種_大分類'].isin(TARGET_IND_LARGE)]
    filter_names.append(TARGET_IND_LARGE[0][:3])
if TARGET_IND_MEDIUM:
    filtered_df = filtered_df[filtered_df['業種_中分類'].isin(TARGET_IND_MEDIUM)]
    filter_names.append(TARGET_IND_MEDIUM[0][:5])
if TARGET_IND_SMALL:
    filtered_df = filtered_df[filtered_df['業種_小分類'].isin(TARGET_IND_SMALL)]
    filter_names.append(TARGET_IND_SMALL[0][:5])

if TARGET_CAUSE_LARGE:
    filtered_df = filtered_df[filtered_df['起因物_大分類'].isin(TARGET_CAUSE_LARGE)]
if TARGET_CAUSE_MEDIUM:
    filtered_df = filtered_df[filtered_df['起因物_中分類'].isin(TARGET_CAUSE_MEDIUM)]
if TARGET_CAUSE_SMALL:
    filtered_df = filtered_df[filtered_df['起因物_小分類'].isin(TARGET_CAUSE_SMALL)]

# 【改修】事故の型フィルターの適用
if TARGET_ACCIDENT_TYPE:
    filtered_df = filtered_df[filtered_df['事故の型'].isin(TARGET_ACCIDENT_TYPE)]
    # 出力ファイル名に事故の型を一部反映
    filter_names.append(TARGET_ACCIDENT_TYPE[0][:4])

if TARGET_HOURS:
    filtered_df = filtered_df[filtered_df['発生時間_整形'].isin(TARGET_HOURS)]
if TARGET_AGE_GROUPS and '年代' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['年代'].isin(TARGET_AGE_GROUPS)]

record_count = len(filtered_df)
condition_str = "_".join([x for x in filter_names if x]) if filter_names else "全業種"
print(f"ターゲットスコープ: 【{condition_str}】 該当件数: {record_count} 件")

if record_count == 0:
    print("[終了] 条件に一致するデータが存在しません。設定を見直してください。")
    exit()

# --- 5. 集計軸・カラムの動的決定 ---
if TARGET_CAUSE_SMALL:
    TARGET_AXIS_COL = '起因物_小分類'
elif TARGET_CAUSE_MEDIUM:
    TARGET_AXIS_COL = '起因物_小分類'  # 中分類固定なら、自動で小分類へドリルダウン
else:
    TARGET_AXIS_COL = '起因物_中分類'

filtered_df[TARGET_AXIS_COL] = filtered_df[TARGET_AXIS_COL].fillna('不明')

# --- 6. 視覚兵器①：数値ラベル付き積み上げ棒グラフ（上位5分類） ---
print("1/2: 数値ラベル付き推移グラフ（積み上げ棒グラフ）の生成中...")

top_causes = filtered_df[TARGET_AXIS_COL].value_counts().nlargest(5).index.tolist()
filtered_df['起因物_表示用'] = filtered_df[TARGET_AXIS_COL].apply(lambda x: x if x in top_causes else 'その他')

# クロス集計と時系列の整流化
trend_data = pd.crosstab(filtered_df['年'], filtered_df['起因物_表示用'])
year_order = ['H24', 'H25', 'H26', 'H27', 'H28', 'H29', 'H30', 'H31', 'R1', 'R2', 'R3']
year_order = [y for y in year_order if y in trend_data.index]
trend_data = trend_data.reindex(year_order)

ordered_cols = top_causes + ['その他']
ordered_cols = [c for c in ordered_cols if c in trend_data.columns]
trend_data = trend_data[ordered_cols]

# 【依存関係防御】tabulateが環境になくても通常出力で救済する設計
print("\n▼▼▼ 【コピペ用】各年の正確な数値データテーブル ▼▼▼")
try:
    print(trend_data.to_markdown())
except ImportError:
    print(trend_data.to_string())
print("▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲\n")

# キャンバス設計
fig, ax = plt.subplots(figsize=(13, 8))
colors = ['#5c0000', '#8a0000', '#b80000', '#e60000', '#ff4d4d', '#D3D3D3']
colors = colors[:len(ordered_cols)]

# 積み上げ棒グラフとしてプロット
trend_data.plot(kind='bar', stacked=True, color=colors, ax=ax, alpha=0.9, width=0.7)

# 各ブロックの内部に、正確な被災者数を自動刻印（0または極小値は非表示にして視覚崩れを防止）
for p in ax.patches:
    width, height = p.get_width(), p.get_height()
    x, y = p.get_xy() 
    if height > (record_count * 0.015): 
        ax.text(
            x + width/2, y + height/2, f'{int(height)}',
            horizontalalignment='center', verticalalignment='center',
            color='white', fontsize=10, fontweight='bold'
        )

# タイトル途切れ防止（pad=20でヘッダー余白を動的確保）
plt.title(f"【{condition_str}】死傷労災推移と主要原因の内訳（{TARGET_AXIS_COL} 上位5）", fontsize=15, fontweight='bold', pad=20)
plt.xlabel("発生年", fontsize=11)
plt.ylabel("死傷者数（人）", fontsize=11)
plt.legend(title=f'{TARGET_AXIS_COL}', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
plt.xticks(rotation=0) 
plt.tight_layout()

trend_img = os.path.join(OUTPUT_DIR, f"trend_labeled_{condition_str}_{current_time}.png")
plt.savefig(trend_img, dpi=300, bbox_inches='tight')
plt.close()

# --- 7. 視覚兵器②：時間軸ヒートマップ（上位10分類） ---
print("2/2: 時間帯×原因のヒートマップ生成中...")

time_order = [f"{i:02d}時台" for i in range(24)]
top_10_causes = filtered_df[TARGET_AXIS_COL].value_counts().nlargest(10).index.tolist()
heatmap_df = filtered_df[filtered_df[TARGET_AXIS_COL].isin(top_10_causes)]

matrix_data = pd.crosstab(heatmap_df[TARGET_AXIS_COL], heatmap_df['発生時間_整形'])
matrix_data = matrix_data.reindex(columns=time_order, fill_value=0)
matrix_data = matrix_data.reindex(top_10_causes)

fig, ax = plt.subplots(figsize=(16, 9)) # 16:9 黄金比キャンバス
sns.heatmap(matrix_data, annot=True, fmt="d", cmap="Reds", linewidths=.5, cbar_kws={'label': '死傷件数'}, ax=ax)

# タイトル途切れ防止（pad=25 ＆ bbox_inches='tight' の多重防衛）
plt.title(f"【{condition_str}】{TARGET_AXIS_COL} × 発生時間帯の死傷ヒートマップ", fontsize=15, fontweight='bold', pad=25)
plt.xlabel("発生時間帯（00時〜23時）", fontsize=11)
plt.ylabel(f"{TARGET_AXIS_COL}", fontsize=11)
plt.xticks(rotation=45)
plt.tight_layout()

heatmap_img = os.path.join(OUTPUT_DIR, f"heatmap_{condition_str}_{current_time}.png")
plt.savefig(heatmap_img, dpi=300, bbox_inches='tight')
plt.close()

print(f"\n[大成功] 『事故の型』フィルターが完全連動したアセットが出荷されました。")
print(f"  └ 推移グラフ（数値ラベル付） : {trend_img}")
print(f"  └ 死傷ヒートマップ          : {heatmap_img}")