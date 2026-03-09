import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from janome.tokenizer import Tokenizer
from matplotlib import font_manager
import re
from datetime import datetime

# --- 1. 空間設計（設定と出力） ---
# ★分析対象に合わせてここを書き換えろ
THEME_NAME = "防災白書"          # グラフのタイトル用
INPUT_PREFIX = "bousai"         # 入力ファイル名の接頭辞（例: input/bousai_R7_part1.txt の 'bousai'）
YEARS = ["R7", "R6", "R5", "R4", "R3", "R2", "R1"]

STOPWORDS_DIR = "stopwords"
FONT_PATH = "font/BIZ-UDGothicR.ttc"

# ロット番号（タイムスタンプ）の自動生成
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
OUTPUT_IMAGE = f"output/tfidf_{INPUT_PREFIX}_7years_{timestamp}.png"

# --- 2. 共通カートリッジ（ストップワード）の自動装填 ---
stop_words_set = set()
stopword_files = glob.glob(os.path.join(STOPWORDS_DIR, "*.txt"))

print("--- フィルター（ストップワード辞書）の読み込み ---")
if not stopword_files:
    print(f"[警告] {STOPWORDS_DIR} フォルダにテキストがありません。素通しで分析します。")
else:
    for filepath in stopword_files:
        with open(filepath, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
            stop_words_set.update(words)
        print(f"  └ [装填完了] {os.path.basename(filepath)}")

# 組み込みノイズの強制排除
system_noise = {"cid", "indd", "iinnnddd", "pdf", "データ"}
stop_words_set.update(system_noise)
print(f"  └ [完了] 総排除指定: {len(stop_words_set)} 語")

def tokenize_and_filter(text):
    t = Tokenizer()
    words = []
    for token in t.tokenize(text):
        word = token.surface
        part = token.part_of_speech.split(',')[0]
        # アルファベット単独や数字を弾き、共通フィルターに検知されない単語のみ抽出
        if part == '名詞' and len(word) > 1 and not re.match(r'^[0-9a-zA-Z]+$', word):
            if word not in stop_words_set:
                words.append(word)
    return " ".join(words)

# --- 3. データ読み込みと形態素解析 ---
print("\n--- 第2工程：時系列TF-IDF分析開始 ---")
corpus = []
valid_years = []

for year in YEARS:
    # 空間設計で設定した接頭辞を使ってパスを動的に生成
    file_path = f"input/{INPUT_PREFIX}_{year}_part1.txt"
    if not os.path.exists(file_path):
        print(f"[警告] {file_path} が存在しません。スキップします。")
        continue
    
    print(f"[{year}] の形態素解析を実行中...（時間がかかります）")
    with open(file_path, "r", encoding="utf-8") as f:
        corpus.append(tokenize_and_filter(f.read()))
    valid_years.append(year)

if len(corpus) < 2:
    print("分析には2年分以上のデータが必要です。処理を中止します。")
    exit()

# --- 4. TF-IDFの計算 ---
print("TF-IDFを計算し、各年度の特異点を抽出中...")
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(corpus)
feature_names = vectorizer.get_feature_names_out()

df_tfidf = pd.DataFrame(tfidf_matrix.toarray(), columns=feature_names, index=valid_years)

# --- 5. グラフの描画（7年分の一覧） ---
print("グラフを生成中...")
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()

fig, axes = plt.subplots(3, 3, figsize=(18, 15))
axes = axes.flatten()

for i, year in enumerate(valid_years):
    top_words = df_tfidf.loc[year].sort_values(ascending=False).head(10)
    
    axes[i].barh(top_words.index[::-1], top_words.values[::-1], color='teal')
    axes[i].set_title(f'【{year}年度 第1部】 特徴語', fontsize=14)
    axes[i].set_xlabel('TF-IDF スコア')

# 余ったグラフ領域を非表示にする
for j in range(len(valid_years), 9):
    fig.delaxes(axes[j])

plt.suptitle(f"{THEME_NAME}（第1部） 7年間のテーマ変遷：TF-IDF分析", fontsize=22)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig(OUTPUT_IMAGE)
print(f"完了。時系列の変遷画像を確認せよ: {os.path.abspath(OUTPUT_IMAGE)}")