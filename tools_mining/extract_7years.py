import pdfplumber
import os

# --- 1. 設計図（Toshiyukiのリストをシステム言語に翻訳） ---
# 形式: "年度": {"pdf": "実際のPDFファイル名", "pages": (開始物理ページ, 終了物理ページ)}
TARGET_YEARS = {
    "R7": {"pdf": "input/厚生労働白書R7.pdf", "pages": (16, 146)},
    "R6": {"pdf": "input/厚生労働白書R6.pdf", "pages": (18, 189)}, # ★実際のファイル名に修正せよ
    "R5": {"pdf": "input/厚生労働白書R5.pdf", "pages": (18, 161)}, # ★実際のファイル名に修正せよ
    "R4": {"pdf": "input/厚生労働白書R4.pdf", "pages": (16, 172)}, # ★実際のファイル名に修正せよ
    "R3": {"pdf": "input/厚生労働白書R3.pdf", "pages": (16, 195)}, # ★実際のファイル名に修正せよ
    "R2": {"pdf": "input/厚生労働白書R2.pdf", "pages": (18, 192)}, # ★実際のファイル名に修正せよ
    "R1": {"pdf": "input/厚生労働白書R1H30.pdf", "pages": (18, 242)}
}

print("--- 第1工程：7年分の第1部一括抽出ライン起動 ---")

for year, data in TARGET_YEARS.items():
    pdf_path = data["pdf"]
    start_page, end_page = data["pages"]
    output_txt = f"input/{year}_part1.txt"
    
    # 既に抽出済みの場合はスキップする（無駄な計算の排除）
    if os.path.exists(output_txt):
        print(f"[SKIP] {output_txt} は既に存在します。")
        continue

    if not os.path.exists(pdf_path):
        print(f"[警告] {pdf_path} が見つかりません。ファイル名を確認してください。")
        continue

    print(f"[{year}] の抽出を開始します... ({start_page}〜{end_page}ページ)")
    extracted_text = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        # 物理ページ(1始まり)を、Python用(0始まり)に変換してループ
        for i in range(start_page - 1, end_page):
            if i >= total_pages:
                break # 安全装置
            text = pdf.pages[i].extract_text()
            if text:
                extracted_text.append(text)
                
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(extracted_text))
    print(f"  └ [OK] {output_txt} を保存しました。")

print("--- 第1工程完了 ---")