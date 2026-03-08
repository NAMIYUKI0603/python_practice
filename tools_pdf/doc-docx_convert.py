import os
import glob
import win32com.client as win32

# .docが入っている入力ホッパーの空間指定
INPUT_DIR = os.path.abspath("input_sds")

# Wordを裏側で起動（画面には出さない）
word = win32.gencache.EnsureDispatch('Word.Application')
word.Visible = False

doc_files = glob.glob(os.path.join(INPUT_DIR, "*.doc"))

print(f"--- 時代遅れの .doc ファイル {len(doc_files)} 件を .docx へ強制変換開始 ---")

for doc_path in doc_files:
    # 既に .docx ならスキップ (.doc を検索しているので基本は該当しないが安全装置として)
    if doc_path.endswith(".docx"):
        continue

    docx_path = doc_path + "x" # 拡張子に x を追加

    try:
        # Wordで開き、新しいフォーマット(16 = wdFormatXMLDocument)で保存し直す
        wb = word.Documents.Open(doc_path)
        wb.SaveAs2(docx_path, FileFormat=16)
        wb.Close()
        
        # 変換元の古い .doc は削除（負債の完全抹消）
        os.remove(doc_path)
        print(f"[変換完了＆原本破棄] {os.path.basename(doc_path)} -> .docx")
        
    except Exception as e:
        print(f"[エラー] {os.path.basename(doc_path)} の変換に失敗: {e}")

word.Quit()
print("--- 変換完了 ---")