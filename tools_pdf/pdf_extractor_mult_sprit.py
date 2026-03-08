import pdfplumber

INPUT_PDF = "input/厚生労働白書R1H30.pdf"

# 形式: "出力ファイル名": (開始ページ, 終了ページ)
CHAPTER_RANGES = {
    "R1H30_part1": (0, 106), 
    "R1H30_part2": (107, 212), 
    "R1H30_part3": (213, 318), 
    "R1H30_part4": (319, 424), 
    "R1H30_part5": (425, 530), # 仮に実在しない大きな数字を入れても、下の安全装置が働く
}

print("PDFの多段抽出を開始...")
with pdfplumber.open(INPUT_PDF) as pdf:
    # PDFの真の総ページ数（赤色の壁）を取得
    total_pages = len(pdf.pages)
    print(f"※PDFの物理的な総ページ数: {total_pages}ページ")

    for chapter_name, (start_page, end_page) in CHAPTER_RANGES.items():
        extracted_text = []
        
        for i in range(start_page, end_page + 1):
            # 【安全装置】i が総ページ数（壁）に到達、または超えたらループを強制脱出
            if i >= total_pages:
                print(f"  [警告] インデックス {i} は存在しません。上限に達したため抽出を終了します。")
                break
            
            text = pdf.pages[i].extract_text()
            if text:
                extracted_text.append(text)
        
        output_name = f"input/{chapter_name}.txt"
        with open(output_name, "w", encoding="utf-8") as f:
            f.write("\n".join(extracted_text))
        print(f"[OK] {output_name} を抽出完了 ({start_page}〜{min(end_page, total_pages - 1)}ページ)")