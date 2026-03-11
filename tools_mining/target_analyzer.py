import os
import glob
import re

# --- 1. 空間設計（顕微鏡の設定） ---
# ★調べたい単語（ターゲット）をここに記述
TARGET_WORD = "事業"  # 例：「予算」「火山」「避難」などに書き換える

# ★対象とする年度のテキストファイルを指定
# （7年分一気に調べたい場合は input/bousai_*_part1.txt にする）
INPUT_FILES = "input/南場智子「ますます“速さ”が命題に」DeNA AI Day2026全文書き起こし - コピー.txt" 
OUTPUT_FILE = f"output/targeting_{TARGET_WORD}_context.txt"

# --- 2. 抽出機構（KWIC：Keyword in Context） ---
WINDOW_SIZE = 50  # 前後何文字を抽出するか

target_paths = glob.glob(INPUT_FILES)
if not target_paths:
    print(f"[警告] {INPUT_FILES} が見つかりません。")
    exit()

print(f"--- ターゲット「{TARGET_WORD}」の文脈解剖を開始 ---")
extracted_contexts = []

for file_path in target_paths:
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        # 改行を削除し、一つの繋がった空間（文字列）にする
        text = f.read().replace("\n", " ") 
        
    # ターゲット単語の出現位置をすべて見つける
    matches = [m.start() for m in re.finditer(TARGET_WORD, text)]
    
    if matches:
        extracted_contexts.append(f"\n【{filename}】における「{TARGET_WORD}」の出現（計 {len(matches)} 回）")
        for i, idx in enumerate(matches):
            start = max(0, idx - WINDOW_SIZE)
            end = min(len(text), idx + len(TARGET_WORD) + WINDOW_SIZE)
            context = text[start:end]
            # ターゲット単語を【】で囲んで目立たせる
            context = context.replace(TARGET_WORD, f"【{TARGET_WORD}】")
            extracted_contexts.append(f" {i+1}. ...{context}...")

# --- 3. 証拠の出力 ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(extracted_contexts))

print(f"\n[OK] 解剖完了。文脈の生データを確認せよ: {OUTPUT_FILE}")