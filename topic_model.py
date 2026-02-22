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
    # 基礎的な助詞・代名詞・時間
    "もの", "こと", "ため", "それ", "これ", "よう", "さん", "の", 
    "等", "平成", "令和", "年度", "年", "月", "日", "現在", "過去", "今後",
    
    # 1. 文書構造・フォーマット・単位
    "章", "部", "節", "項", "図", "表", "写真", "コラム", "資料", "報告", 
    "報告書", "概要", "ページ", "頁", "ほか", "以上", "以下", "注", "万", "トン",
    
    # 2. 官僚的アクション（無色透明な動詞・名詞）
    "推進", "実施", "検討", "確保", "構築", "形成", "整備", "促進", "向上", 
    "維持", "充実", "展開", "実行", "措置", "達成", "実現", "評価", "把握", 
    "確認", "作成", "開催", "公表", "増加", "減少", "変化", "加速", "対応", 
    "導入", "活用", "利用", "取組", "活動", "対策", "支援", "連携", "協力", 
    "参加", "共有", "貢献", "拡大", "設定", "関係",
    
    # 3. 汎用的な主体・客体
    "我が国", "日本", "国", "政府", "地方", "地域", "社会", "世界", "国民", 
    "人", "者", "企業", "機関", "施設", "団体", "公共", "事業者", "主体", 
    "全体", "一部", "部門",
    
    # 4. 程度・抽象表現・その他ノイズ
    "基本的", "具体的", "総合的", "積極的", "様々", "各種", "新た", "これら", 
    "それら", "状況", "傾向", "影響", "水準", "程度", "重要", "課題", "問題", 
    "事項", "項目", "内容", "結果", "成果", "側面", "背景", "要因", "分野", "領域",
    
    # 解析エラー対策（1文字・アルファベット等）
    "indd", "R", "的", "化", "性", "間", "前", "後", "上", "中", "下"
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