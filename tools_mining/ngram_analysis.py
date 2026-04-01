import os
import glob
import re
import collections
import matplotlib.pyplot as plt
import japanize_matplotlib
from janome.tokenizer import Tokenizer
from datetime import datetime

# --- 1. 空間設計（ディレクトリと経路） ---
INPUT_TEXT = "input/input.txt"  # 分析対象のテキスト
STOPWORDS_DIR = "stopwords"     # ストップワード群を格納するフォルダ
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STOPWORDS_DIR, exist_ok=True)

# タイムスタンプと動的ファイル名の生成
current_time = datetime.now().strftime("%Y%m%d_%H%M")
base_name = os.path.splitext(os.path.basename(INPUT_TEXT))[0]
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, f"ngram_{base_name}_{current_time}.png")

print(f"--- N-gram分析エンジン起動 [{current_time}] ---")

# --- 2. ストップワードの自動一括装填 ---
print(f"'{STOPWORDS_DIR}' フォルダ内の全辞書ファイルを一括装填中...")
stop_words_set = set()
for txt_path in glob.glob(os.path.join(STOPWORDS_DIR, "*.txt")):
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith("#"):
                stop_words_set.add(word)
print(f"装填完了: 計 {len(stop_words_set)} 語のノイズを粉砕リストに登録")

# --- 3. データの読み込みと形態素解析 ---
print("テキストを読み込み、ノイズを粉砕しています...")
if not os.path.exists(INPUT_TEXT):
    print(f"[異常終了] 入力ファイルが見つかりません: {INPUT_TEXT}")
    exit()

with open(INPUT_TEXT, 'r', encoding='utf-8') as f:
    text = f.read()

t = Tokenizer()
token_list = []
tokens = t.tokenize(text)

for token in tokens:
    word = token.surface
    part = token.part_of_speech.split(',')[0]
    
    # 多段フィルター（名詞、ストップワード除外、数字・アルファベット1文字除外、1文字単語除外）
    if (part == '名詞' 
        and word not in stop_words_set 
        and not re.match(r'^[0-9]+$', word) 
        and not re.match(r'^[a-zA-Z]+$', word) 
        and len(word) > 1):
        
        token_list.append(word)

# --- 4. N-gram（2語の連なり）の生成と集計 ---
print("2語連鎖（N-gram）の構造を計算中...")
bigrams = list(zip(token_list, token_list[1:]))
c = collections.Counter(bigrams)
top_20 = c.most_common(20)

if not top_20:
    print("[異常終了] 抽出された連鎖がありません。")
    exit()

# --- 5. 視覚化（グラフ描画） ---
print("グラフを描画しています...")
labels = [f"{a} + {b}" for (a, b), count in top_20]
values = [count for (a, b), count in top_20]

plt.figure(figsize=(12, 10))
plt.barh(labels[::-1], values[::-1], color="#b80000", edgecolor="black") 
plt.title(f"災害状況テキスト「{base_name}」における死の連鎖フレーズ Top 20", fontsize=16, fontweight='bold')
plt.xlabel("出現回数", fontsize=12)
plt.grid(axis='x', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig(OUTPUT_IMAGE, dpi=300)
print(f"[完了] アセットを出力しました: {OUTPUT_IMAGE}")