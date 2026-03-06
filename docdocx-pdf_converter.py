import os
import glob
import win32com.client as win32

# 入力ホッパーの空間指定（ここに .doc や .docx を入れる）
INPUT_DIR = os.path.abspath("input_sds")
# 出力コンテナ（変換されたPDFが入る）
OUTPUT_PDF_DIR = os.path.abspath("input_sds_pdf")
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

# Wordを裏側で起動（画面には出さない）
word = win32.gencache.EnsureDispatch('Word.Application')
word.Visible = False

# .doc と .docx の両方を対象とする
word_files = glob.glob(os.path.join(INPUT_DIR, "*.doc*"))

print(f"--- Wordファイル {len(word_files)} 件を PDF へ強制変換開始 ---")

for word_path in word_files:
    # 拡張子を除いたファイル名を取得
    filename = os.path.splitext(os.path.basename(word_path))[0]
    pdf_path = os.path.join(OUTPUT_PDF_DIR, f"{filename}.pdf")

    # 既にPDF化済みの場合はスキップ
    if os.path.exists(pdf_path):
        continue

    try:
        # Wordで開き、PDFフォーマット(17 = wdFormatPDF)で出力する
        wb = word.Documents.Open(word_path)
        wb.SaveAs2(pdf_path, FileFormat=17)
        wb.Close()
        
        print(f"[PDF化完了] {filename}")
        
    except Exception as e:
        print(f"[エラー] {os.path.basename(word_path)} の変換に失敗: {e}")

word.Quit()
print("--- 変換完了 ---")