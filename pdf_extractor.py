import pdfplumber
import os

# --- 設定エリア ---
INPUT_PDF = "input/厚生労働白書R7.pdf"  # 読み込む白書のPDF
OUTPUT_TXT = "input/kourou_R7_text.txt"    # 出力するテキストファイル

print(f"[{INPUT_PDF}] のテキスト抽出を開始します...")

extracted_text = []

# PDFを開く
with pdfplumber.open(INPUT_PDF) as pdf:
    total_pages = len(pdf.pages)
    print(f"全 {total_pages} ページを検出。処理中...")
    
    for i, page in enumerate(pdf.pages):
        # テキストのみを抽出（図表や画像は自動的に無視される）
        text = page.extract_text()
        
        if text:
            extracted_text.append(text)
        
        # 進行状況の表示（50ページごと）
        if (i + 1) % 50 == 0:
            print(f"... {i + 1} / {total_pages} ページ完了")

# テキストファイルとして保存
with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(extracted_text))

print(f"抽出完了。{OUTPUT_TXT} に保存しました。")