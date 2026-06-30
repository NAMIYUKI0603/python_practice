import pandas as pd
import os
import re
from datetime import datetime

# --- 1. 空間設計と抽出条件（ここを毎回書き換えて狙い撃つ） ---
INPUT_CSV = "input/死傷労災_製造業.csv"
OUTPUT_DIR = "input"  
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ★★★ フィルター条件設定（フル階層・複数指定対応版） ★★★
# 複数指定したい場合はリスト形式 ["A", "B"] で記述。全件対象の場合は空リスト [] を指定。

# 【業種フィルター】
TARGET_IND_LARGE  = []                      # 業種_大分類
TARGET_IND_MEDIUM = []                              # 業種_中分類
TARGET_IND_SMALL  = []                              # 業種_小分類

# 【起因物フィルター】
TARGET_CAUSE_LARGE  = []                            # 起因物_大分類
TARGET_CAUSE_MEDIUM = []                            # 起因物_中分類
TARGET_CAUSE_SMALL  = []                            # 起因物_小分類

# 【事故の型フィルター】
TARGET_ACCIDENT_TYPE = []     # 事故の型（例: ["はさまれ、巻き込まれ"]）

# 🔥【最重要：災害状況テキスト・キーワードフィルター】 🔥
# 災害状況の文章中に、以下のいずれかの単語が含まれているものだけを直撃抽出する。
# 絞り込まない（全件対象）の場合は空リスト [] を指定せよ。
TARGET_CONTEXT_KEYWORDS = ["思い込み"] # 例: ["スイッチ", "回転"] などの組み合わせも自由自在

# 【状況・属性フィルター】
TARGET_HOURS = []                                   # 発生時間帯（例: ["08時台", "10時台"]）
TARGET_AGE_GROUPS = []                              # 年代（例: ["50代", "60代"]）

# 将来の米国・英語データフラグ（英語データを扱う場合は True にせよ）
IS_ENGLISH_DATA = False

current_time = datetime.now().strftime("%Y%m%d_%H%M")
print(f"--- 死傷労災テキスト抽出エンジン（災害状況キーワード実装版）起動 [{current_time}] ---")

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

# --- 3. データの読み込みと前処理（文字コード不一致を完全リカバリー） ---
print("死傷労災マスターデータベースを読み込み中...")
if not os.path.exists(INPUT_CSV):
    print(f"[異常終了] マスターCSVが見つかりません: {INPUT_CSV}")
    print("データが input フォルダ内にあるか確認してください。")
    exit()

try:
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig', low_memory=False)
except UnicodeDecodeError:
    print("  └ [通知] utf-8-sigでエラーを検知。cp932（Shift-JIS）に切り替えて再試行します...")
    df = pd.read_csv(INPUT_CSV, encoding='cp932', low_memory=False)
    print("  └ [成功] 文字コードの壁をクリアしました。")

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

if TARGET_ACCIDENT_TYPE:
    filtered_df = filtered_df[filtered_df['事故の型'].isin(TARGET_ACCIDENT_TYPE)]
    filter_names.append(TARGET_ACCIDENT_TYPE[0][:4])

# 🔥【新規実装】災害状況テキスト内のキーワード部分一致フィルター（複数指定時はOR条件）
if TARGET_CONTEXT_KEYWORDS:
    print(f"  └ [キーワード狙撃] 災害状況から「{', '.join(TARGET_CONTEXT_KEYWORDS)}」を検索中...")
    
    # 大文字小文字の違いによるすり抜けを防ぐため、英語フラグ時は小文字で判定
    if IS_ENGLISH_DATA:
        keywords_pattern = '|'.join([re.escape(kw.lower()) for kw in TARGET_CONTEXT_KEYWORDS])
        is_matched = filtered_df['災害状況'].astype(str).str.lower().str.contains(keywords_pattern, na=False, regex=True)
    else:
        keywords_pattern = '|'.join([re.escape(kw) for kw in TARGET_CONTEXT_KEYWORDS])
        is_matched = filtered_df['災害状況'].astype(str).str.contains(keywords_pattern, na=False, regex=True)
        
    filtered_df = filtered_df[is_matched]
    # 出力ファイル名にキーワードの足跡を刻印（先頭要素の3文字）
    filter_names.append(f"kw_{TARGET_CONTEXT_KEYWORDS[0][:3]}")

if TARGET_HOURS:
    filtered_df = filtered_df[filtered_df['発生時間_整形'].isin(TARGET_HOURS)]
if TARGET_AGE_GROUPS and '年代' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['年代'].isin(TARGET_AGE_GROUPS)]

# 抽出件数の確認
record_count = len(filtered_df)
condition_str = "_".join([x for x in filter_names if x]) if filter_names else "all"
print(f"抽出条件の足跡: {condition_str}")
print(f"該当する事故データ: {record_count} 件")

if record_count == 0:
    print("[終了] 条件に一致するデータが文章中に存在しません。キーワード設定を見直してください。")
    exit()

# --- 5. 災害状況テキストの結合と出力 ---
print("災害状況を抽出し、一つのテキストファイルに結合しています...")

disaster_texts = filtered_df['災害状況'].astype(str).tolist()

if IS_ENGLISH_DATA:
    cleaned_texts = []
    eng_stop_pattern = r'\b(the|a|an|and|of|to|in|on|at|by|for|with|from|is|was|were|be|been|it|this|that|he|she|they|them)\b'
    for text in disaster_texts:
        lowered = text.lower()
        no_stops = re.sub(eng_stop_pattern, '', lowered)
        cleaned_text = re.sub(r'\s+', ' ', no_stops).strip()
        cleaned_texts.append(cleaned_text)
    final_text = "\n\n".join(cleaned_texts)
else:
    final_text = "\n\n".join(disaster_texts)

# 出力ファイル名の生成
output_filename = f"input_{condition_str}_{current_time}.txt"
output_path = os.path.join(OUTPUT_DIR, output_filename)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(final_text)

print(f"[完了] 抽出テキストを保存しました: {output_path}")
print("-> 次のステップ：特定の行動文脈が凝縮されたこのファイルを、ワードクラウドやNotebookLMへ流し込め。")