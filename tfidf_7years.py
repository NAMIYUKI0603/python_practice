import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from janome.tokenizer import Tokenizer
from matplotlib import font_manager
import re

# --- 1. 設定 ---
YEARS = ["R7", "R6", "R5", "R4", "R3", "R2", "R1"]
FONT_PATH = "font/BIZ-UDGothicR.ttc"
OUTPUT_IMAGE = "output/tfidf_7years_trend.png"

# --- 2. 白書マスター・ストップワード（最強版） ---
STOP_WORDS = [
    "もの", "こと", "ため", "それ", "これ", "よう", "さん", "の", 
    "等", "平成", "令和", "年度", "年", "月", "日", "現在", "過去", "今後",
    "章", "部", "節", "項", "図", "表", "写真", "コラム", "資料", "報告", "報告書", 
    "概要", "ページ", "頁", "ほか", "以上", "以下", "注", "万", "トン", "割", "円",
    "推進", "実施", "検討", "確保", "構築", "形成", "整備", "促進", "向上", "維持", 
    "充実", "展開", "実行", "措置", "達成", "実現", "評価", "把握", "確認", "作成", 
    "開催", "公表", "増加", "減少", "変化", "加速", "対応", "導入", "活用", "利用", 
    "取組", "活動", "対策", "支援", "連携", "協力", "参加", "共有", "貢献", "拡大", "設定", "関係",
    "我が国", "日本", "国", "政府", "地方", "地域", "世界", "国民", "人", "者", 
    "企業", "機関", "施設", "団体", "公共", "事業者", "主体", "全体", "一部", "部門",
    "基本的", "具体的", "総合的", "積極的", "様々", "各種", "新た", "これら", "それら", 
    "状況", "傾向", "影響", "水準", "程度", "重要", "課題", "問題", "事項", "項目", 
    "内容", "結果", "成果", "側面", "背景", "要因", "分野", "領域",
    "的", "化", "性", "間", "前", "後", "上", "中", "下", "場合", "必要",
    "事業", "社会", "厚生", "労働", "医療", "制度", "労働者", "保険", "年金" # ★厚労白書特有の超頻出語を徹底排除
]

def tokenize_and_filter(text):
    t = Tokenizer()
    words = []
    for token in t.tokenize(text):
        word = token.surface
        part = token.part_of_speech.split(',')[0]
        if part == '名詞' and len(word) > 1 and not re.match(r'^[0-9]+$', word) and word not in STOP_WORDS:
            words.append(word)
    return " ".join(words)

# --- 3. データ読み込みと形態素解析 ---
print("--- 第2工程：時系列TF-IDF分析開始 ---")
corpus = []
valid_years = []

for year in YEARS:
    file_path = f"input/{year}_part1.txt"
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

# 3行3列のグラフ領域を作成（余った2枠は非表示にする）
fig, axes = plt.subplots(3, 3, figsize=(18, 15))
axes = axes.flatten()

for i, year in enumerate(valid_years):
    top_words = df_tfidf.loc[year].sort_values(ascending=False).head(10)
    
    # 年代が古い順に見せるか、新しい順に見せるかのレイアウト（ここではそのまま配置）
    axes[i].barh(top_words.index[::-1], top_words.values[::-1], color='teal')
    axes[i].set_title(f'【{year}年度 第1部】 特徴語', fontsize=14)
    axes[i].set_xlabel('TF-IDF スコア')

# 余ったグラフ領域（8個目、9個目）を非表示にする
for j in range(len(valid_years), 9):
    fig.delaxes(axes[j])

plt.suptitle("厚生労働白書（第1部） 7年間のテーマ変遷：TF-IDF分析", fontsize=22)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig(OUTPUT_IMAGE)
print(f"完了。時系列の変遷画像を確認せよ: {os.path.abspath(OUTPUT_IMAGE)}")