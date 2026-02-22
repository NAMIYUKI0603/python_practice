import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from janome.tokenizer import Tokenizer
from matplotlib import font_manager
import re

# --- 白書用マスター・ストップワード ---
STOP_WORDS = [
    "もの", "こと", "ため", "それ", "これ", "よう", "さん", "の", 
    "等", "平成", "令和", "年度", "年", "月", "日", "現在", "過去", "今後",
    "章", "部", "節", "項", "図", "表", "写真", "コラム", "資料", "報告", 
    "報告書", "概要", "ページ", "頁", "ほか", "以上", "以下", "注", "万", "トン", "割", "円",
    "推進", "実施", "検討", "確保", "構築", "形成", "整備", "促進", "向上", 
    "維持", "充実", "展開", "実行", "措置", "達成", "実現", "評価", "把握", 
    "確認", "作成", "開催", "公表", "増加", "減少", "変化", "加速", "対応", 
    "導入", "活用", "利用", "取組", "活動", "対策", "支援", "連携", "協力", 
    "参加", "共有", "貢献", "拡大", "設定", "関係",
    "我が国", "日本", "国", "政府", "地方", "地域", "社会", "世界", "国民", 
    "人", "者", "企業", "機関", "施設", "団体", "公共", "事業者", "主体", 
    "全体", "一部", "部門",
    "基本的", "具体的", "総合的", "積極的", "様々", "各種", "新た", "これら", 
    "それら", "状況", "傾向", "影響", "水準", "程度", "重要", "課題", "問題", 
    "事項", "項目", "内容", "結果", "成果", "側面", "背景", "要因", "分野", "領域",
    "的", "化", "性", "間", "前", "後", "上", "中", "下", "場合", "必要",
    "医療", "労働", "制度", "労働者", "事業", "社会", "平成", "厚生"# ←厚労白書特有の当たり前すぎる言葉を追加
]

# --- 1. 設定エリア ---
FILE_PART1 = "input/kourou_R7_part1.txt"
FILE_PART2 = "input/kourou_R7_part2.txt"
FONT_PATH = "font/BIZ-UDGothicR.ttc"
OUTPUT_IMAGE = "output/tfidf_comparison.png"

# --- 2. 実行前・完全自動チェック ---
print("--- システム事前チェック開始 ---")
def check_path(filepath, name):
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        print(f"[異常検知] {name} が存在しません。\n 探している場所: {abs_path}")
        sys.exit(1) # ここで強制終了させる
    else:
        print(f"[OK] {name} を確認: {abs_path}")

check_path(FILE_PART1, "第1部テキスト")
check_path(FILE_PART2, "第2部テキスト")
check_path(FONT_PATH, "フォントファイル")

if not os.path.exists("output"):
    os.makedirs("output")
    print("[OK] outputフォルダを新規作成しました")
print("--- システム事前チェック完了 ---\n")

# --- 3. メイン処理 ---
def tokenize_and_filter(text):
    t = Tokenizer()
    words = []
    for token in t.tokenize(text):
        word = token.surface
        part = token.part_of_speech.split(',')[0]
        # ストップワードに含まれていないかチェックを追加
        if part == '名詞' and len(word) > 1 and not re.match(r'^[0-9]+$', word) and word not in STOP_WORDS:
            words.append(word)
    return " ".join(words)

font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()

print("テキストを読み込み、形態素解析を実行中...（時間がかかる）")
with open(FILE_PART1, 'r', encoding='utf-8') as f:
    text1 = tokenize_and_filter(f.read())
with open(FILE_PART2, 'r', encoding='utf-8') as f:
    text2 = tokenize_and_filter(f.read())

corpus = [text1, text2]

print("TF-IDFを計算中...")
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(corpus)
feature_names = vectorizer.get_feature_names_out()

df_tfidf = pd.DataFrame(tfidf_matrix.toarray(), columns=feature_names, index=['第1部', '第2部'])

top_n = 15
top_part1 = df_tfidf.loc['第1部'].sort_values(ascending=False).head(top_n)
top_part2 = df_tfidf.loc['第2部'].sort_values(ascending=False).head(top_n)

print("グラフを描画中...")
fig, axes = plt.subplots(1, 2, figsize=(15, 8))

axes[0].barh(top_part1.index[::-1], top_part1.values[::-1], color='coral')
axes[0].set_title('第1部（テーマ編）の特徴語', fontsize=16)
axes[0].set_xlabel('TF-IDF スコア')

axes[1].barh(top_part2.index[::-1], top_part2.values[::-1], color='steelblue')
axes[1].set_title('第2部（定点観測編）の特徴語', fontsize=16)
axes[1].set_xlabel('TF-IDF スコア')

plt.suptitle("令和7年 厚生労働白書：第1部と第2部の特徴語比較（TF-IDF）", fontsize=20)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig(OUTPUT_IMAGE)
print(f"完了。画像を確認せよ: {os.path.abspath(OUTPUT_IMAGE)}")