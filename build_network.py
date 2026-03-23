import pandas as pd
import itertools
from collections import Counter
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from janome.tokenizer import Tokenizer
import time
import os
import warnings

# --- 1. 安全装置と空間設計 ---
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', category=UserWarning, module='xlrd')

# 【完全防弾版】Windows環境での日本語フォント強制指定
plt.rcParams['font.family'] = 'MS Gothic'

INPUT_CSV = "output/master_sisyou_manufacturing_detailed.csv"
OUTPUT_DIR = "output"

print("--- 第2工程：共起ネットワーク生成エンジン（完全改修版）起動 ---")
start_time = time.time()

# --- 2. ターゲットの装填（セグメンテーション） ---
print("[1/4] データの読み込みとターゲットの絞り込み中...")
df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig', low_memory=False)

# 「一般動力機械」による事故のみをスナイプ
target_df = df[df['起因物_中分類'] == '一般動力機械'].dropna(subset=['災害状況']).copy()

if len(target_df) > 1000:
    target_df = target_df.sample(1000, random_state=42)
print(f" -> 照準セット完了: 一般動力機械の事故 {len(target_df)}件")

# --- 3. 形態素解析（刃によるテキストの解体と濾過） ---
print("[2/4] 災害状況テキストの解体とストップワードの濾過中...")
t = Tokenizer()

STOP_WORDS = {'する', 'ある', 'いる', 'なる', '作業', '機械', 'ため', 'ところ', '際', '時', 'こと', 'もの', 'よう', '発生', '被災'}

docs_words = []
for text in target_df['災害状況']:
    words = []
    for token in t.tokenize(text):
        pos = token.part_of_speech.split(',')[0]
        pos_detail = token.part_of_speech.split(',')[1]
        base_form = token.base_form
        
        if pos in ['名詞', '動詞']:
            if pos_detail not in ['非自立', '代名詞', '数', '接尾']:
                if base_form not in STOP_WORDS and len(base_form) > 1:
                    words.append(base_form)
    docs_words.append(list(set(words)))

# --- 4. 単語間の結びつき（エッジ）の計測 ---
print("[3/4] 単語の交差点（共起関係）の頻度計測中...")
edge_counter = Counter()

for words in docs_words:
    for w1, w2 in itertools.combinations(sorted(words), 2):
        edge_counter[(w1, w2)] += 1

top_edges = edge_counter.most_common(60)

# --- 5. ネットワークグラフの描画 ---
print("[4/4] ネットワークグラフ（死のルート）の描画中...")
G = nx.Graph()

for (w1, w2), weight in top_edges:
    G.add_edge(w1, w2, weight=weight)

plt.figure(figsize=(14, 12)) 

# 斥力を高め（k=1.2）、ノード同士を引き離す
pos = nx.spring_layout(G, k=1.2, iterations=100, seed=42)

weights = [d['weight'] for (u, v, d) in G.edges(data=True)]
max_weight = max(weights)
min_weight = min(weights)

# 線の太さと色を関係性の密度で変更する
edge_widths = [1 + (d['weight'] - min_weight) / (max_weight - min_weight) * 7 for (u, v, d) in G.edges(data=True)]
edge_colors = [d['weight'] for (u, v, d) in G.edges(data=True)]

# DeprecationWarning回避のため、plt.colormaps を使用
edge_cmap = plt.colormaps['Reds']

nx.draw_networkx_nodes(G, pos, node_color='lightcoral', node_size=1600, alpha=0.9)
nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors, edge_cmap=edge_cmap, edge_vmin=min_weight, edge_vmax=max_weight, alpha=0.6)

# ラベル描画時にも明示的に MS Gothic を指定する
nx.draw_networkx_labels(G, pos, font_family='MS Gothic', font_size=13, font_weight='bold')

plt.title("【一般動力機械】労働災害の共起ネットワーク（死のルート可視化・改善版）", fontsize=18)
plt.axis('off')

output_img = os.path.join(OUTPUT_DIR, "network_machinery_improved.png")
plt.savefig(output_img, dpi=300, bbox_inches='tight')
plt.close()

end_time = time.time()
print(f"[完了] 所要時間: {end_time - start_time:.1f}秒")
print(f"[指示] グラフを確認せよ: {os.path.abspath(output_img)}")