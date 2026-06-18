import os
import glob
import re

# --- 1. 空間設計（顕微鏡の設定） ---
# ★調べたい単語（ターゲット）をここに記述
TARGET_WORD = "落下"  # 例：「清掃」「切断」などに書き換える

# ★対象とする年度のテキストファイルを指定（適宜変更せよ）
INPUT_FILES = "input/input_製造業_金属製品製_材料_20260618_1320.txt" 

# 出力先をアセット用フォルダに統一
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# ファイル名に full_context を付与して以前のものと区別する
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"targeting_{TARGET_WORD}_full_context.txt")

# --- 2. 抽出機構（全文抽出：Full-Text Context） ---
target_paths = glob.glob(INPUT_FILES)
if not target_paths:
    print(f"[異常終了] {INPUT_FILES} が見つかりません。")
    exit()

print(f"--- ターゲット「{TARGET_WORD}」を含む全事象の解剖を開始 ---")
extracted_contexts = []

for file_path in target_paths:
    filename = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        # 改行を境界線として事故ごとにリスト化する
        raw_text = f.read()
        incidents = re.split(r'\n+', raw_text)
        
    total_matches = 0  # ターゲットが含まれる「事象」の総数
    file_contexts = []
    
    for incident in incidents:
        if not incident.strip():
            continue
            
        # その事象（事故の全容）の中にターゲット単語が存在するか判定
        if TARGET_WORD in incident:
            total_matches += 1
            
            # 視覚的ハイライト：事象内のターゲット単語をすべて【】で囲む
            highlighted_incident = incident.replace(TARGET_WORD, f"【{TARGET_WORD}】")
            
            # 断片ではなく、事象の全文をそのままリストに追加
            file_contexts.append(f" {total_matches}. {highlighted_incident}")
            
    if file_contexts:
        extracted_contexts.append(f"\n【{filename}】における「{TARGET_WORD}」を含む事象（計 {total_matches} 件）")
        extracted_contexts.extend(file_contexts)

# --- 3. 証拠の出力 ---
if not extracted_contexts:
    print(f"\n[結果] ターゲット「{TARGET_WORD}」は発見されませんでした。")
else:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(extracted_contexts))

    print(f"\n[OK] 全文抽出完了。A-B-Cチェーンが完全保存された生データを確認せよ: {OUTPUT_FILE}")