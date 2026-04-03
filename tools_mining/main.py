import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from janome.tokenizer import Tokenizer
import collections
from matplotlib import font_manager
import re
from datetime import datetime
import numpy as np
from PIL import Image

# --- 1. 空間設計と制御パラメータ ---
INPUT_TEXT = "input/input_製造業_動力運搬機_20260403_1523.txt" 
STOPWORDS_DIR = "stopwords"               
FONT_PATH = "font/BIZ-UDGothicR.ttc"      

MASK_IMAGE_PATH = "input/mask.png"  
MAX_WORDS_COUNT = 150               
COLOR_MAP = "Reds"                  

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
base_name = os.path.splitext(os.path.basename(INPUT_TEXT))[0]

OUTPUT_WC = f"output_assets/wordcloud_{base_name}_{timestamp}.png"
OUTPUT_CHART = f"output_assets/top50_{base_name}_{timestamp}.png"
OUTPUT_CSV = f"output_assets/top50_{base_name}_{timestamp}.csv"

for d in ["input", "output", STOPWORDS_DIR, "font"]:
    os.makedirs(d, exist_ok=True)

print(f"--- ワードクラウド生成エンジン起動 [{timestamp}] ---")

# --- 2. 多段フィルター（ストップワード）の自動一括装填 ---
stop_words_set = set()
stopword_files = glob.glob(os.path.join(STOPWORDS_DIR, "*.txt"))

print(f"--- フィルター（ストップワード辞書）の読み込み ---")
if not stopword_files:
    print(f"[警告] {STOPWORDS_DIR} フォルダにテキストファイルがありません。素通しで分析します。")
else:
    for filepath in stopword_files:
        with open(filepath, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            stop_words_set.update(words)
        print(f"  └ [装填完了] {os.path.basename(filepath)} (現在の排除指定: 計 {len(stop_words_set)} 語)")

system_noise = {"cid", "indd", "iinnnddd", "pdf"}
stop_words_set.update(system_noise)

# --- 3. 形態素解析とフィルタリング実行 ---
print("\nテキストを読み込み、形態素解析を実行中...")
if not os.path.exists(INPUT_TEXT):
    print(f"[異常終了] 入力ファイルが見つかりません: {INPUT_TEXT}")
    exit()

with open(INPUT_TEXT, "r", encoding="utf-8") as f:
    text = f.read()

t = Tokenizer()
words = []
for token in t.tokenize(text):
    word = token.surface
    part = token.part_of_speech.split(',')[0]
    
    if part == '名詞' and len(word) > 1 and not re.match(r'^[0-9a-zA-Z]+$', word):
        if word not in stop_words_set:
            words.append(word)

if not words:
    print("[異常終了] 抽出された単語がありません。テキストが空か、フィルターが強すぎます。")
    exit()

# --- 4. 頻度集計とノイズ検知用データの出力 ---
word_counts = collections.Counter(words)
top50 = word_counts.most_common(50)

df_top50 = pd.DataFrame(top50, columns=['単語', '出現回数'])
df_top50.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

try:
    font_manager.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()
except Exception as e:
    print(f"[警告] フォント設定エラー。OS標準フォントで続行します: {e}")

plt.figure(figsize=(12, 12))
words_label, counts = zip(*top50[::-1])
plt.barh(words_label, counts, color="darkred")
plt.title(f"出現頻度トップ50 ({base_name})", fontsize=16, fontweight='bold')
plt.xlabel("出現回数")
plt.tight_layout()
plt.savefig(OUTPUT_CHART)
print(f"[OK] 上位50語のグラフを保存しました: {OUTPUT_CHART}")

# --- 5. ワードクラウドの生成（MASK対応・境界線消去） ---
print("ワードクラウドを描画中...")
text_for_wc = " ".join(words)

mask_array = None
if os.path.exists(MASK_IMAGE_PATH):
    try:
        img = Image.open(MASK_IMAGE_PATH).convert('RGBA')
        white_bg = Image.new("RGBA", img.size, "WHITE")
        white_bg.paste(img, (0, 0), img)
        final_mask = white_bg.convert('RGB')
        mask_array = np.array(final_mask)
        print(f"  └ [適用] マスク画像の透過背景を白に変換して空間に適用: {MASK_IMAGE_PATH}")
    except Exception as e:
        print(f"  └ [警告] マスク画像の処理に失敗しました。通常の長方形で描画します: {e}")
else:
    print(f"  └ [通知] マスク画像 ({MASK_IMAGE_PATH}) が無いため、通常の長方形で描画します。")

wordcloud = WordCloud(
    font_path=FONT_PATH,
    width=1200 if mask_array is None else None, 
    height=800 if mask_array is None else None,
    background_color="white",
    colormap=COLOR_MAP,             
    collocations=False,
    max_words=MAX_WORDS_COUNT,      
    mask=mask_array,                
    contour_width=0,                # ★ここを0にして境界線を完全に消去
    contour_color='darkred'
).generate(text_for_wc)

plt.figure(figsize=(15, 10))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.savefig(OUTPUT_WC, bbox_inches='tight', pad_inches=0)
print(f"[OK] ワードクラウドを保存しました: {OUTPUT_WC}")