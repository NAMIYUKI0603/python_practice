import os
import glob
import re

# --- 1. 空間設計（顕微鏡の設定） ---
# ★調べたい単語（ターゲット）をここに記述
TARGET_WORD = "清掃"  # 例：「予算」「火山」「避難」などに書き換える

# ★対象とする年度のテキストファイルを指定
INPUT_FILES = "input/input_製造業_食料品製造_通路_高齢層_20260416_1302.txt" 

# 【改修】出力先をアセット用フォルダに統一
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"targeting_{TARGET_WORD}_context.txt")

# --- 2. 抽出機構（KWIC：Keyword in Context） ---
WINDOW_SIZE = 50  # 前後何文字を抽出するか

target_paths = glob.glob(INPUT_FILES)
if not target_paths:
    print(f"[異常終了] {INPUT_FILES} が見つかりません。")
    exit()

print(f"--- ターゲット「{TARGET_WORD}」の文脈解剖を開始 ---")
extracted_contexts = []

for file_path in target_paths:
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        # 【根本改修】改行を消さずに、改行を境界線として事故ごとにリスト化する
        raw_text = f.read()
        incidents = re.split(r'\n+', raw_text)
        
    total_matches = 0
    file_contexts = []
    
    for incident in incidents:
        if not incident.strip():
            continue
            
        # 各事故（独立した1行）の中だけでターゲットを探す
        matches = [m.start() for m in re.finditer(TARGET_WORD, incident)]
        
        if matches:
            total_matches += len(matches)
            for idx in matches:
                # 抽出範囲を「その事故（incident）の文字数の限界」までに物理的に制限する
                start = max(0, idx - WINDOW_SIZE)
                end = min(len(incident), idx + len(TARGET_WORD) + WINDOW_SIZE)
                
                context = incident[start:end]
                # ターゲット単語を【】で囲んで目立たせる
                context = context.replace(TARGET_WORD, f"【{TARGET_WORD}】")
                
                # 文の先頭・末尾が切れている場合のみ「...」を付与する
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(incident) else ""
                
                file_contexts.append(f" {len(file_contexts)+1}. {prefix}{context}{suffix}")
                
    if file_contexts:
        extracted_contexts.append(f"\n【{filename}】における「{TARGET_WORD}」の出現（計 {total_matches} 回）")
        extracted_contexts.extend(file_contexts)

# --- 3. 証拠の出力 ---
if not extracted_contexts:
    print(f"\n[結果] ターゲット「{TARGET_WORD}」は発見されませんでした。")
else:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(extracted_contexts))

    print(f"\n[OK] 解剖完了。独立した文脈の生データを確認せよ: {OUTPUT_FILE}")