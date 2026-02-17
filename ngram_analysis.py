import os
import re
import collections
import matplotlib.pyplot as plt
import pandas as pd
from janome.tokenizer import Tokenizer
from matplotlib import font_manager

# --- 設定エリア ---
TEXT_FILE = "input/input.txt"
FONT_PATH = "font/BIZ-UDGothicR.ttc" # ※自分の環境に合わせる
OUTPUT_IMAGE = "output/bigram_ranking.png"

# --- 強力なストップワード ---
STOP_WORDS = [
    "もの", "こと", "ため", "それ", "これ", "よう", "さん", "の", 
    "等", "図", "表", "白書", "平成", "令和", "年度", "年", "月", "日",
    "利用", "活用", "実施", "検討", "対応", "推進", "必要", "場合",
    "我が国", "日本", "地域", "社会", "環境", "対策", "構築", "目指",
    "概要", "状況", "保全", "活動", "取組", "部門", "評価", "基本的",
    "世界", "現在", "各種", "重要", "一部", "設定", "関係", "確保",
    "産業", "排出", "削減", "効果", "技術", "開発", "供給", "製品", # 文脈によっては残してもいい
    "indd", "R", "的", "化", "等", "上", "中", "性", "間", "前", "後"
]

# --- 日本語フォント設定 ---
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()

# --- 1. データ読み込み ---
print("テキストを読み込んでいます...")
with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    text = f.read()

# --- 2. クリーニングと形態素解析 ---
print("ノイズを除去し、ペア（2語の連なり）を作成しています...")
t = Tokenizer()
token_list = []

# 文全体をトークン化
tokens = t.tokenize(text)

for token in tokens:
    word = token.surface
    part = token.part_of_speech.split(',')[0]
    
    # 【重要】フィルタリング処理
    # 1. 名詞であること
    # 2. ストップワードではないこと
    # 3. 「数字だけ」ではないこと（regexで判定）
    # 4. 「1文字」ではないこと（"者" "化" "量" などを排除）
    if (part == '名詞' 
        and word not in STOP_WORDS 
        and not re.match(r'^[0-9]+$', word) # 数字のみを排除
        and not re.match(r'^[a-zA-Z]+$', word) # アルファベット1文字などを排除
        and len(word) > 1): # 1文字の単語をすべて排除
        
        token_list.append(word)

# --- 3. N-gram（2語の連なり）を作成 ---
# 例: [A, B, C, D] -> [(A,B), (B,C), (C,D)]
bigrams = list(zip(token_list, token_list[1:]))

# カウント
c = collections.Counter(bigrams)

# トップ20を取得
top_20 = c.most_common(20)

# --- 4. 可視化（横棒グラフ） ---
print("グラフを描画しています...")
# データ整理
labels = [f"{a} + {b}" for (a, b), count in top_20]
values = [count for (a, b), count in top_20]

# グラフ作成
plt.figure(figsize=(12, 10))
# 順位を見やすくするため逆順にする
plt.barh(labels[::-1], values[::-1], color="steelblue") 
plt.title("環境白書における「頻出フレーズ（2語連鎖）」Top 20", fontsize=16)
plt.xlabel("出現回数", fontsize=12)
plt.grid(axis='x', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig(OUTPUT_IMAGE)
print(f"完了！画像を確認してください: {OUTPUT_IMAGE}")