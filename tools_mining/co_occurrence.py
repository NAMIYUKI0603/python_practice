import os
import glob
import itertools
import networkx as nx
import matplotlib.pyplot as plt
import japanize_matplotlib
import re
from janome.tokenizer import Tokenizer
from datetime import datetime

# --- 1. 空間設計（ディレクトリと経路） ---
INPUT_TEXT = "input/input_製造業_一般動力機械_20260403_1542.txt"
STOPWORDS_DIR = "stopwords"
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STOPWORDS_DIR, exist_ok=True)

# タイムスタンプと動的ファイル名の生成
current_time = datetime.now().strftime("%Y%m%d_%H%M")
base_name = os.path.splitext(os.path.basename(INPUT_TEXT))[0]
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, f"network_{base_name}_{current_time}.png")

# ★分析の解像度調整パラメータ
MIN_EDGE_WEIGHT = 5   # 最低何回ペアになったら線を結ぶか
MAX_NODES = 50         # 画面に表示する最大単語数

print(f"--- 共起ネットワーク分析エンジン起動 [{current_time}] ---")

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

# --- 3. データの読み込みと文単位の分割 ---
print("テキストを読み込み、文単位の空間に分割しています...")
if not os.path.exists(INPUT_TEXT):
    print(f"[異常終了] 入力ファイルが見つかりません: {INPUT_TEXT}")
    exit()

with open(INPUT_TEXT, 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'[\r\n\s]+', '', text)
sentences = text.split('。')

# --- 4. 形態素解析と共起（ペア）のカウント ---
print("単語の相関関係を計算中...")
t = Tokenizer()
pair_counts = {}

for sentence in sentences:
    if not sentence: continue
    nouns = []
    for token in t.tokenize(sentence):
        word = token.surface
        part_of_speech = token.part_of_speech.split(',')[0]
        
        if (part_of_speech == '名詞' 
            and word not in stop_words_set
            and not re.match(r'^[0-9]+$', word) 
            and not re.match(r'^[a-zA-Z]+$', word) 
            and len(word) > 1):
            
            nouns.append(word)
    
    sorted_nouns = sorted(list(set(nouns)))
    for pair in itertools.combinations(sorted_nouns, 2):
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

# --- 5. ネットワーク構造の構築 ---
print("ネットワークを構築中...")
G = nx.Graph()

sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
node_degrees = {}

for pair, count in sorted_pairs:
    if count >= MIN_EDGE_WEIGHT:
        G.add_edge(pair[0], pair[1], weight=count)
        node_degrees[pair[0]] = node_degrees.get(pair[0], 0) + count
        node_degrees[pair[1]] = node_degrees.get(pair[1], 0) + count

if len(G.nodes) > MAX_NODES:
    print(f"単語数が多すぎるため、上位 {MAX_NODES} 個に絞り込みます...")
    top_nodes = sorted(node_degrees, key=node_degrees.get, reverse=True)[:MAX_NODES]
    G = G.subgraph(top_nodes)

if len(G.nodes) == 0:
    print("\n[エラー] 条件が厳しすぎて抽出された単語が0個だ。")
    print(f"解決策: コード上部の MIN_EDGE_WEIGHT ({MIN_EDGE_WEIGHT}) を下げて再実行しろ。")
    exit()

# --- 6. 視覚化（描画と相対スケーリング） ---
print("グラフをレンダリングしています...")
plt.figure(figsize=(15, 15))

pos = nx.spring_layout(G, k=0.6, seed=42) 

edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
max_weight = max(edge_weights) if edge_weights else 1
edge_width = [(w / max_weight) * 6 for w in edge_weights] 

node_values = [node_degrees.get(n, 1) for n in G.nodes()]
max_degree = max(node_values) if node_values else 1
node_size = [(v / max_degree) * 4000 for v in node_values] 

nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color="#e60000", alpha=0.7, edgecolors="white")
nx.draw_networkx_edges(G, pos, width=edge_width, edge_color="gray", alpha=0.4)
nx.draw_networkx_labels(G, pos, font_family=plt.rcParams['font.family'], font_size=13, font_weight="bold")

plt.title(f"災害状況テキスト「{base_name}」の共起ネットワーク図", fontsize=20, fontweight="bold")
plt.axis('off')
plt.savefig(OUTPUT_IMAGE, bbox_inches="tight", dpi=300)
print(f"[完了] アセットを出力しました: {OUTPUT_IMAGE}")