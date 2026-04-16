import pandas as pd
import os
import re
from datetime import datetime

# --- 1. 空間設定と抽出条件（ここを毎回書き換えて狙い撃つ） ---
INPUT_CSV = "input/master_sisyou_manufacturing_detailed.csv"
OUTPUT_DIR = "input"  
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ★★★ フィルター条件設定（フル階層・複数指定対応版） ★★★
# 複数指定したい場合はリスト形式 ["A", "B"] で記述しろ。
# 絞り込まない（全件対象）の場合は空リスト [] を指定しろ。

# 【業種フィルター】
TARGET_IND_LARGE  = ["製造業"]                      # 業種_大分類
TARGET_IND_MEDIUM = ["食料品製造業"]                              # 業種_中分類（例: ["食料品製造業"]）
TARGET_IND_SMALL  = []        # 業種_小分類

# 【起因物フィルター】
TARGET_CAUSE_LARGE  = []                            # 起因物_大分類
TARGET_CAUSE_MEDIUM = []                            # 起因物_中分類
TARGET_CAUSE_SMALL  = ["通路"]                      # 起因物_小分類

# 【状況・属性フィルター】
TARGET_HOURS = []                                   # 発生時間帯（例: ["08時台", "10時台"]）
TARGET_AGE_GROUPS = ["50代", "60代", "70代以上"]    # 年代（例: ["50代", "60代", "70代以上"]）

# 出力ファイル名のタイムスタンプ
current_time = datetime.now().strftime("%Y%m%d_%H%M")

print(f"--- 死傷労災テキスト抽出エンジン（フル階層スナイパー版）起動 [{current_time}] ---")

# --- 2. データ整形ロジック（時間と年代の純化） ---
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
print("死傷労災マスターデータベースを読み込み中...")
if not os.path.exists(INPUT_CSV):
    print(f"[異常終了] マスターCSVが見つかりません: {INPUT_CSV}")
    print("データが input フォルダ内にあるか確認してください。")
    exit()

df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig', low_memory=False)

# 必須項目の欠損を除去
df = df.dropna(subset=['災害状況', '年'])

# 時間と年代の整形
if '発生時間' in df.columns:
    df['発生時間_整形'] = df['発生時間'].apply(format_time)

if '年齢' in df.columns:
    df['年代'] = df['年齢'].apply(categorize_age)

# --- 4. フィルターの容赦ない適用（全階層対応） ---
filtered_df = df.copy()
filter_names = []

if TARGET_IND_LARGE:
    filtered_df = filtered_df[filtered_df['業種_大分類'].isin(TARGET_IND_LARGE)]
    # ファイル名が長くなりすぎるのを防ぐため、大分類は名称の先頭要素だけ記録
    filter_names.append(TARGET_IND_LARGE[0][:3])

if TARGET_IND_MEDIUM:
    filtered_df = filtered_df[filtered_df['業種_中分類'].isin(TARGET_IND_MEDIUM)]
    filter_names.append(TARGET_IND_MEDIUM[0][:5])

if TARGET_IND_SMALL:
    filtered_df = filtered_df[filtered_df['業種_小分類'].isin(TARGET_IND_SMALL)]
    filter_names.append(TARGET_IND_SMALL[0][:5])

if TARGET_CAUSE_LARGE:
    filtered_df = filtered_df[filtered_df['起因物_大分類'].isin(TARGET_CAUSE_LARGE)]
    filter_names.append("起大指定")

if TARGET_CAUSE_MEDIUM:
    filtered_df = filtered_df[filtered_df['起因物_中分類'].isin(TARGET_CAUSE_MEDIUM)]
    filter_names.append(TARGET_CAUSE_MEDIUM[0][:4])

if TARGET_CAUSE_SMALL:
    filtered_df = filtered_df[filtered_df['起因物_小分類'].isin(TARGET_CAUSE_SMALL)]
    filter_names.append("_".join(TARGET_CAUSE_SMALL))

if TARGET_HOURS:
    filtered_df = filtered_df[filtered_df['発生時間_整形'].isin(TARGET_HOURS)]
    filter_names.append("時間指定")

if TARGET_AGE_GROUPS and '年代' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['年代'].isin(TARGET_AGE_GROUPS)]
    filter_names.append("高齢層" if "60代" in TARGET_AGE_GROUPS else "年代指定")

# 抽出件数の確認
record_count = len(filtered_df)
print(f"抽出条件の足跡: {', '.join(filter_names) if filter_names else '全件'}")
print(f"該当する死傷事故: {record_count} 件")

if record_count == 0:
    print("[終了] 条件に一致するデータが存在しません。ターゲット設定を見直してください。")
    exit()

# --- 5. 災害状況テキストの結合と出力 ---
print("災害状況を抽出し、一つのテキストファイルに結合しています...")

disaster_texts = filtered_df['災害状況'].astype(str).tolist()
final_text = "\n\n".join(disaster_texts)

# 出力ファイル名の動的生成（長すぎないように制御）
condition_str = "_".join([x for x in filter_names if x]) if filter_names else "all"
output_filename = f"input_{condition_str}_{current_time}.txt"
output_path = os.path.join(OUTPUT_DIR, output_filename)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(final_text)

print(f"[完了] 抽出テキストを保存しました: {output_path}")
print("-> 次のステップ：得られたテキストを共起ネットワークに放り込み、「その他」の闇を暴け。")