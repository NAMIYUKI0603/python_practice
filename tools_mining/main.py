import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from janome.tokenizer import Tokenizer
import collections
from matplotlib import font_manager
import re
from datetime import datetime  # ★新たに追加（時間を取得する歯車）

# --- 1. 空間設計（ディレクトリと経路） ---
# ★注意：今は防災白書を分析しているはずなので、ファイル名を確認しろ
STOPWORDS_DIR = "stopwords"               
INPUT_TEXT = "input/input_死傷労災製造業.txt"  
FONT_PATH = "font/BIZ-UDGothicR.ttc"      

# --- ★ロット番号（タイムスタンプ）の自動生成機構 ---
# 現在時刻を取得（例：20260308_1605）
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

# 入力ファイル名から拡張子を削った「名前」だけを抽出（例：bousai_R7_part1）
base_name = os.path.splitext(os.path.basename(INPUT_TEXT))[0]

# 動的に出力ファイル名を生成（名前＋タイムスタンプ）
OUTPUT_WC = f"output/wordcloud_{base_name}_{timestamp}.png"
OUTPUT_CHART = f"output/top50_{base_name}_{timestamp}.png"
OUTPUT_CSV = f"output/top50_{base_name}_{timestamp}.csv"

# 必要な空間（フォルダ）がなければ自動生成する
for d in ["input", "output", STOPWORDS_DIR, "font"]:
    os.makedirs(d, exist_ok=True)

# --- 2. 多段フィルター（ストップワード）の自動一括装填 ---
stop_words_set = set()
# stopwordsフォルダ内のすべての .txt ファイルを自動巡回して取得
stopword_files = glob.glob(os.path.join(STOPWORDS_DIR, "*.txt"))

print(f"--- フィルター（ストップワード辞書）の読み込み ---")
if not stopword_files:
    print(f"[警告] {STOPWORDS_DIR} フォルダにテキストファイルがありません。素通しで分析します。")
else:
    for filepath in stopword_files:
        with open(filepath, "r", encoding="utf-8") as f:
            # 各行を読み込み、前後の空白や改行を削ぎ落としてリストに追加（空行は無視）
            words = [line.strip() for line in f if line.strip()]
            stop_words_set.update(words)
        print(f"  └ [装填完了] {os.path.basename(filepath)} (現在の排除指定: 計 {len(stop_words_set)} 語)")

# PDF抽出時の避けられない残骸（組み込みノイズ）はシステム側で強制排除
system_noise = {"cid", "indd", "iinnnddd", "pdf"}
stop_words_set.update(system_noise)

# --- 3. 形態素解析とフィルタリング実行 ---
print("\nテキストを読み込み、形態素解析を実行中...")
with open(INPUT_TEXT, "r", encoding="utf-8") as f:
    text = f.read()

t = Tokenizer()
words = []
for token in t.tokenize(text):
    word = token.surface
    part = token.part_of_speech.split(',')[0]
    
    # 条件：名詞のみ、2文字以上、数字やアルファベット単体は除外
    if part == '名詞' and len(word) > 1 and not re.match(r'^[0-9a-zA-Z]+$', word):
        # ★ここで多段フィルターに引っかからないか検査
        if word not in stop_words_set:
            words.append(word)

if not words:
    print("[異常終了] 抽出された単語がありません。テキストが空か、フィルターが強すぎます。")
    exit()

# --- 4. 頻度集計とノイズ検知用データの出力 ---
word_counts = collections.Counter(words)
top50 = word_counts.most_common(50)

# A. 経理・分析用データとしてCSV（表）に出力
df_top50 = pd.DataFrame(top50, columns=['単語', '出現回数'])
df_top50.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n[OK] 上位50語の頻度表（CSV）を保存しました: {OUTPUT_CSV}")

# B. 視覚的ノイズ検知用グラフの出力
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()

plt.figure(figsize=(12, 12))
# 棒グラフ（下から上へ描画されるため順序を反転させる）
words_label, counts = zip(*top50[::-1])
plt.barh(words_label, counts, color="steelblue")
plt.title("出現頻度トップ50（ノイズ検証・ストップワード抽出用）", fontsize=16)
plt.xlabel("出現回数")
plt.tight_layout()
plt.savefig(OUTPUT_CHART)
print(f"[OK] 上位50語のグラフを保存しました: {OUTPUT_CHART}")

# --- 5. ワードクラウドの生成（最終プロダクト） ---
print("ワードクラウドを描画中...")
text_for_wc = " ".join(words)
wordcloud = WordCloud(
    font_path=FONT_PATH,
    width=1200, height=800,
    background_color="white",
    colormap="viridis",
    collocations=False # 英語用の連語機能をオフ（日本語の重複ノイズを防ぐ）
).generate(text_for_wc)

plt.figure(figsize=(15, 10))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.savefig(OUTPUT_WC, bbox_inches='tight', pad_inches=0)
print(f"[OK] ワードクラウドを保存しました: {OUTPUT_WC}")