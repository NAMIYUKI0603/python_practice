import fitz  # PyMuPDF
import os
from pathlib import Path

# ==========================================
# 設定エリア
# ==========================================
INPUT_DIR = "pdf_input"
OUTPUT_DIR = "jpg_output"
ZOOM_FACTOR = 2.0
# ==========================================

def convert_pdf_to_jpg():
    input_path = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)
    
    if not input_path.exists():
        os.makedirs(input_path, exist_ok=True)
        return

    os.makedirs(output_path, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"[警告] '{INPUT_DIR}' 内にPDFファイルが見つかりません。")
        return

    print(f"--- 全 {len(pdf_files)} 件のPDFを画像変換開始 ---")

    for pdf_file in pdf_files:
        print(f"処理中: {pdf_file.name}")
        
        try:
            # ★真の解決策：Pythonの空間(RAM)にファイルを「純粋なバイトデータ」として完全吸収する
            with open(pdf_file, "rb") as f:
                pdf_bytes = f.read()
            
            # Cエンジンにはファイルパスではなく、メモリ上の「データ」を直接渡す
            doc = fitz.open("pdf", pdf_bytes)
            
            for page_index in range(len(doc)):
                page = doc[page_index]
                mat = fitz.Matrix(ZOOM_FACTOR, ZOOM_FACTOR)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                
                out_name = f"{pdf_file.stem}_page_{page_index + 1}.jpg"
                out_path = output_path / out_name
                
                pix.save(str(out_path))
                
                # ★片付けの徹底：Cエンジンがパニックを起こさないよう、子オブジェクトを先に明示的に破壊する
                pix = None
                page = None
                
            doc.close()
            print(f"  └ [完了] {len(doc)} ページ分を保存しました。")
            
        except Exception as e:
            print(f"  └ [エラー] {pdf_file.name} の処理中に不具合が発生: {e}")

    print("\n--- 全工程完了 ---")

if __name__ == "__main__":
    convert_pdf_to_jpg()