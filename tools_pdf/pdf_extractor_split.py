import pdfplumber

INPUT_PDF = "input/厚生労働白書R7.pdf" # ※実際のPDF名に変更しろ
OUTPUT_PART1 = "input/kourou_R7_part1.txt"
OUTPUT_PART2 = "input/kourou_R7_part2.txt"

# 第1部と第2部の境界ページ（0始まりのため131になるが、目次に合わせて調整しろ）
BOUNDARY_PAGE = 146

text_part1 = []
text_part2 = []

print("PDFを分割抽出中...")
with pdfplumber.open(INPUT_PDF) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            # i は 0 から始まる。i < 132 なら 1ページ目〜132ページ目まで
            if i < BOUNDARY_PAGE:
                text_part1.append(text)
            else:
                text_part2.append(text)

with open(OUTPUT_PART1, "w", encoding="utf-8") as f:
    f.write("\n".join(text_part1))
with open(OUTPUT_PART2, "w", encoding="utf-8") as f:
    f.write("\n".join(text_part2))

print(f"抽出完了:\n 第1部: {OUTPUT_PART1}\n 第2部: {OUTPUT_PART2}")