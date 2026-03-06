import os
import glob
import pdfplumber
import docx  # Wordファイル抽出用

# --- 1. 空間設計（入力ホッパーと出力コンテナ） ---
INPUT_DIR = "input_sds"
OUTPUT_DIR = "output_sds"

# フォルダが存在しない場合は自動作成
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 入力フォルダ内のすべてのファイルを取得
target_files = glob.glob(os.path.join(INPUT_DIR, "*"))

if not target_files:
    print(f"[警告] {INPUT_DIR} フォルダが空です。SDSのPDFやWordファイルを投入してください。")
    exit()

print(f"--- 全 {len(target_files)} 件のファイルを一括処理開始 ---")

# --- 2. 一括処理ループ（コンベア稼働） ---
for file_path in target_files:
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    ext = ext.lower() # 拡張子を小文字に統一
    
    output_path = os.path.join(OUTPUT_DIR, f"{name}.txt")
    
    # 既に抽出済みの場合はスキップ
    if os.path.exists(output_path):
        print(f"[SKIP] {filename} は処理済みです。")
        continue

    extracted_text = []

    try:
        # 選別機：PDFの場合
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
        
        # 選別機：Wordの場合
        elif ext == ".docx":
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    extracted_text.append(para.text)
        
        # 対象外の拡張子は弾く
        else:
            print(f"[IGNORE] {filename} は未対応のファイル形式です。")
            continue

        # --- 3. テキストの排出 ---
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(extracted_text))
        print(f"[OK] {filename} -> テキスト化完了")

    except Exception as e:
        print(f"[ERROR] {filename} の処理中にエラーが発生しました: {e}")

print("--- 全工程完了 ---")