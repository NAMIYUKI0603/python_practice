import pandas as pd
import matplotlib.pyplot as plt
from janome.tokenizer import Tokenizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from matplotlib import font_manager
import re

# --- 設定エリア ---
TEXT_FILE = "input/input.txt"
FONT_PATH = "font/BIZ-UDGothicR.ttc" # ★要確認
OUTPUT_IMAGE = "output/topic_model_5.png"
NUM_TOPICS = 5  # 文書をいくつに分類するか（5つくらいが丁度いい）

# --- ストップワード（前回の強力版） ---
STOP_WORDS = [
    # --- 基礎的な助詞・代名詞 ---
    "もの", "こと", "ため", "それ", "これ", "よう", "さん", "の", 
    "等", "図", "表", "白書", "平成", "令和", "年度", "年", "月", "日",
    "利用", "活用", "実施", "検討", "対応", "推進", "必要", "場合",
    "我が国", "日本", "地域", "社会", "環境", "対策", "構築", "目指",
    "概要", "状況", "保全", "活動", "取組", "部門", "評価", "基本的",
    "世界", "現在", "各種", "重要", "一部", "設定", "関係", "確保",
    # --- 追加ノイズ（画像分析による特定） ---
    "indd", "R", "的", "化", "等", "上", "中", "性", "節", "章"
    # --- 行政用語・抽象語 ---
    "具体的", "積極的", "総合的", "様々", "これら", "それら",
    "視点", "観点", "側面", "背景", "要因", "分野", "領域",
    "課題", "問題", "事項", "項目", "内容", "結果", "成果", "影響",
    "程度", "水準", "状態", "傾向", "全体", "部分", "中心",
    "促進", "強化", "充実", "図る", "向上", "維持",
    "達成", "実現", "展開", "実行", "措置",
    "連携", "協力", "支援", "参加", "理解", "認識"
]

# --- 日本語フォント設定 ---
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()

# --- 1. データを文単位でリスト化 ---
print("テキストを読み込み、文単位に分割しています...")
with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    text = f.read()
# 「。」で区切って、1文ずつを分析対象にする
sentences = text.replace('\n', '').split('。')

# --- 2. 形態素解析（分かち書き） ---
print("ベクトル化の準備（分かち書き）をしています...")
t = Tokenizer()
corpus = []

for sentence in sentences:
    words = []
    for token in t.tokenize(sentence):
        word = token.surface
        part = token.part_of_speech.split(',')[0]
        # 名詞かつ、ストップワードでなく、数字・1文字でないもの
        if (part == '名詞' 
            and word not in STOP_WORDS 
            and not re.match(r'^[0-9]+$', word) 
            and len(word) > 1):
            words.append(word)
            
    if len(words) > 0:
        corpus.append(" ".join(words))

# --- 3. ベクトル化とLDA実行 ---
print(f"トピックモデル（LDA）を計算中...（{NUM_TOPICS}分類）")
# 文書を行列に変換
vectorizer = CountVectorizer(max_df=0.95, min_df=2)
dtm = vectorizer.fit_transform(corpus)

# LDA（トピック抽出）を実行
lda = LatentDirichletAllocation(n_components=NUM_TOPICS, random_state=42)
lda.fit(dtm)

# --- 4. 可視化（各トピックの重要語を表示） ---
print("結果をグラフ化しています...")
feature_names = vectorizer.get_feature_names_out()

fig, axes = plt.subplots(1, NUM_TOPICS, figsize=(20, 10), sharex=True)
axes = axes.flatten()

for topic_idx, topic in enumerate(lda.components_):
    # 各トピックの上位10単語を取得
    top_features_ind = topic.argsort()[:-11:-1]
    top_features = [feature_names[i] for i in top_features_ind]
    weights = topic[top_features_ind]

    ax = axes[topic_idx]
    ax.barh(top_features, weights, height=0.7, color="teal")
    ax.set_title(f'Topic {topic_idx + 1}', fontdict={'fontsize': 20})
    ax.invert_yaxis()
    ax.tick_params(axis='both', which='major', labelsize=14)
    for i in 'top right left'.split():
        ax.spines[i].set_visible(False)

plt.suptitle("環境白書の構造分析：主要な5つのトピック", fontsize=24)
plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)
plt.savefig(OUTPUT_IMAGE)
print(f"完了！画像を確認してください: {OUTPUT_IMAGE}")