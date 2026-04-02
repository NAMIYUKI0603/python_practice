import pandas as pd
import os
import re
from datetime import datetime

# --- 1. 空間設定と抽出条件（ここを毎回書き換えて狙い撃つ） ---
INPUT_CSV = "output/master_sibou_all_industries.csv"
OUTPUT_DIR = "input"  # 次の分析エンジンの入力フォルダに直接吐き出す
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ★★★ フィルター条件設定 ★★★
# 絞り込まない場合は None を指定しろ
TARGET_INDUSTRY = "製造業"           # 大分類（例: "製造業", "建設業", None）
TARGET_CAUSE = "動力運搬機"          # 起因物の中分類（例: "動力運搬機", "一般動力機械", None）
TARGET_HOUR = "19時台"               # 発生時間帯（例: "10時台", "08時台", None）

# 出力ファイル名のタイムスタンプ
current_time = datetime.now().strftime("%Y%m%d_%H%M")

print(f"--- テキスト抽出エンジン起動 [{current_time}] ---")

# --- 2. 時間の整形ロジック（お馴染みの防衛線） ---
def format_time(t_str):
    if pd.isna(t_str) or '不明' in str(t_str) or '8～7' in str(t_str):
        return '不明'
    match = re.search(r'(\d+)', str(t_str))
    if match:
        hour = int(match.group(1))
        return f"{hour:02d}時台"
    return '不明'

# --- 3. データの読み込みと純化 ---
print("マスターデータベースを読み込み中...")
if not os.path.exists(INPUT_CSV):
    print(f"[異常終了] マスターCSVが見つかりません: {INPUT_CSV}")
    exit()

df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig', low_memory=False)

# 必須項目の欠損を除去
df = df.dropna(subset=['災害状況', '年'])

# 時間の整形
if '発生時間' in df.columns:
    df['発生時間_整形'] = df['発生時間'].apply(format_time)

# --- 4. フィルターの容赦ない適用 ---
filtered_df = df.copy()
filter_names = []

if TARGET_INDUSTRY:
    filtered_df = filtered_df[filtered_df['業種_大分類'] == TARGET_INDUSTRY]
    filter_names.append(TARGET_INDUSTRY)

if TARGET_CAUSE:
    filtered_df = filtered_df[filtered_df['起因物_中分類'] == TARGET_CAUSE]
    filter_names.append(TARGET_CAUSE)

if TARGET_HOUR:
    filtered_df = filtered_df[filtered_df['発生時間_整形'] == TARGET_HOUR]
    filter_names.append(TARGET_HOUR)

# 抽出件数の確認
record_count = len(filtered_df)
print(f"抽出条件: {' / '.join(filter_names) if filter_names else '全件'}")
print(f"該当する死亡事故: {record_count} 件")

if record_count == 0:
    print("[終了] 条件に一致するデータが存在しません。設定を見直してください。")
    exit()

# --- 5. 災害状況テキストの結合と出力 ---
print("災害状況を抽出し、一つのテキストファイルに結合しています...")

# 災害状況の列だけを抽出し、文字列として結合（文の区切りを明確にするために改行を挟む）
disaster_texts = filtered_df['災害状況'].astype(str).tolist()
final_text = "\n\n".join(disaster_texts)

# 出力ファイル名の動的生成（条件名をファイル名に組み込む）
condition_str = "_".join(filter_names) if filter_names else "all"
output_filename = f"input_{condition_str}_{current_time}.txt"
output_path = os.path.join(OUTPUT_DIR, output_filename)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(final_text)

print(f"[完了] 抽出テキストを保存しました: {output_path}")
print("-> このファイルを ngram_analysis.py や co_occurrence.py の INPUT_TEXT に指定しろ。")