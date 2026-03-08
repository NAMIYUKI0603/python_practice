from pypdf import PdfWriter
import os
import glob

# --- 1. 空間設計（入力ホッパーと出力先） ---
# ここに結合したいPDF（名前順）を入れる
INPUT_DIR = "input_merge" 
# 結合後の完成品の名前
OUTPUT_FILE = "output/防災白書R1_結合版.pdf" 

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs("output", exist_ok=True)

# フォルダ内のPDFを名前順（昇順）に取得
target_pdfs = sorted(glob.glob(os.path.join(INPUT_DIR, "*.pdf")))

if not target_pdfs:
    print(f"[警告] {INPUT_DIR} フォルダが空です。結合するPDFを投入してください。")
    exit()

print(f"--- 全 {len(target_pdfs)} 件のPDFをプレスマシンに投入します ---")

# 結合用の空のコンテナを用意
merger = PdfWriter()

# 順番にコンテナに流し込む
for pdf_path in target_pdfs:
    filename = os.path.basename(pdf_path)
    print(f"  └ 追加中: {filename}")
    merger.append(pdf_path)

# 一つのファイルとして物理的に書き出す
merger.write(OUTPUT_FILE)
merger.close()

print(f"\n[OK] 結合完了。出力ファイルを確認せよ: {OUTPUT_FILE}")