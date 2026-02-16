import os
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

# --- 設定エリア（Control Panel） ---
TEXT_FILE = "input/input.txt"          # テキストファイル
FONT_PATH = "font/BIZ-UDGothicR.ttc"   # フォントファイル（※自分のファイル名に合わせる！）
MASK_IMAGE = "input/mask.jpg"          # シルエット画像
OUTPUT_IMAGE = "output/result_cloud_final.png"

# 除外したい単語（ストップワード）を強化
STOP_WORDS = [
    "もの", "こと", "ため", "それ", "これ", "よう", "さん", "の", 
    "等", "図", "表", "白書", "平成", "令和", "年度", "年", "月", "日",
    "利用", "活用", "実施", "検討", "対応", "推進", "必要", "場合",
    "我が国", "日本", "地域", "社会", "環境", "対策", "構築", "目指",
    "概要", "状況", "保全", "活動", "取組", "部門", "評価", "基本的",
    "世界", "現在", "各種", "重要", "一部", "設定", "関係", "確保"
]

# --- 1. データ読み込み ---
print("テキストを読み込んでいます...")
with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    text = f.read()

# --- 2. 形態素解析 ---
print("言葉を分解しています...")
t = Tokenizer()
words = []

for token in t.tokenize(text):
    part_of_speech = token.part_of_speech.split(',')[0]
    # 名詞だけを取り出し、かつストップワードに含まれないもの
    if part_of_speech == '名詞' and token.surface not in STOP_WORDS:
        words.append(token.surface)

text_chain = ' '.join(words)

# --- 3. マスク画像の準備 ---
print("金型（マスク）を準備しています...")
try:
    mask_array = np.array(Image.open(MASK_IMAGE))
    
    # ▼▼▼ 【追加】 金型の洗浄処理（ここが重要） ▼▼▼
    # 「200より白い（明るい）場所は、すべて255（完全な白）にする」という命令
    # これでJPEG特有のノイズや薄いグレーが一掃される
    mask_array[mask_array > 200] = 255
    # ▲▲▲ここまで▲▲▲
except FileNotFoundError:
    print(f"【エラー】画像が見つかりません: {MASK_IMAGE}")
    print("inputフォルダに mask.png があるか確認してください。")
    exit()

# --- 4. 可視化生成 ---
print("画像を生成しています...")
wc = WordCloud(
    background_color="white",
    font_path=FONT_PATH,
    mask=mask_array,            # 型抜き指定
    contour_width=1,            # 輪郭線の太さ
    contour_color='steelblue',  # 輪郭線の色
    colormap="viridis",         # 色使い
    stopwords=set(STOP_WORDS)
)

wc.generate(text_chain)

# --- 5. 出力 ---
wc.to_file(OUTPUT_IMAGE)
print(f"完了！画像を確認してください: {OUTPUT_IMAGE}")

# プレビュー表示
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.show()