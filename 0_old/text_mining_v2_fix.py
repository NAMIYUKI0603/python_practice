import MeCab
import networkx as nx
import matplotlib.pyplot as plt
import japanize_matplotlib
import itertools
from collections import Counter
import os
import sys

# ==========================================
# 設定
# ==========================================
TARGET_FILE = "diary.txt"
OUTPUT_IMAGE = "network_graph.png" # 保存する画像ファイル名
STOP_WORDS = ["よう", "こと", "もの", "これ", "それ", "ん", "ため", "日", "2025", "2024", "1", "2", "3", "月", "火", "水", "木", "金", "年", "時", "分", "円"]

print("=== 処理開始 ===")

# 1. ファイル読み込み
print(f"1. ファイル読み込み中: {TARGET_FILE} ... ", end="")
text = ""
if not os.path.exists(TARGET_FILE):
    print(f"\n[Error] {TARGET_FILE} が見つかりません。")
    sys.exit()

try:
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    print("UTF-8で成功")
except:
    try:
        with open(TARGET_FILE, "r", encoding="cp932") as f:
            text = f.read()
        print("Shift-JISで成功")
    except Exception as e:
        print(f"\n[Fatal Error] 読み込み失敗: {e}")
        sys.exit()

if not text:
    print("[Error] テキストが空です。")
    sys.exit()

# 2. 形態素解析とペア作成
print("2. 形態素解析とペア作成中 ... ", end="")
tagger = MeCab.Tagger()
sentences = []
node = tagger.parseToNode(text)
current_sentence = []

while node:
    features = node.feature.split(",")
    word = node.surface
    
    # 名詞のみ抽出
    if features[0] == "名詞" and features[1] not in ["代名詞", "数", "非自立", "接尾"]:
        if word not in STOP_WORDS and len(word) > 1: # 1文字の単語（例：私、手、目）もノイズになりやすいので除外
            current_sentence.append(word)
    
    # 文の区切り（改行や句点）
    if word in ["。", "\n", "．"]:
        if len(current_sentence) >= 2: # 単語が2つ以上ないとペアが作れない
            sentences.append(current_sentence)
        current_sentence = []
    
    node = node.next

print(f"完了 (有効な文の数: {len(sentences)})")

if len(sentences) == 0:
    print("[Error] ペアを作れる文が見つかりませんでした。")
    sys.exit()

# 3. ネットワーク構築
print("3. ネットワーク計算中 ... ", end="")
pair_list = []
for sentence in sentences:
    pair_list.extend(itertools.combinations(set(sentence), 2))

cnt_pairs = Counter(pair_list)
TOP_N = 100 # 多すぎると潰れるので少し減らす
common_pairs = cnt_pairs.most_common(TOP_N)

if not common_pairs:
    print("\n[Error] 共起ペアが見つかりませんでした。")
    sys.exit()

G = nx.Graph()
for (u, v), w in common_pairs:
    G.add_edge(u, v, weight=w)

print(f"完了 (ノード数: {len(G.nodes)}, エッジ数: {len(G.edges)})")

# 4. 描画と保存
print(f"4. 画像描画と保存中 ({OUTPUT_IMAGE}) ... ", end="")
try:
    plt.figure(figsize=(15, 15))
    
    # レイアウト決定（k値を大きくすると反発が強くなり広がる）
    pos = nx.spring_layout(G, k=0.5, seed=42) 
    
    # ノードの大きさ
    d = dict(G.degree)
    node_sizes = [v * 300 for v in d.values()]
    
    # 線の太さ
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [(w / max_weight) * 5 for w in edge_weights]

    # 描画
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="#a0c8ff", alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color="#aaaaaa", alpha=0.6)
    nx.draw_networkx_labels(G, pos, font_family='IPAexGothic', font_size=12, font_weight="bold")
    
    plt.title("2025年業務日誌 共起ネットワーク", fontsize=24)
    plt.axis("off")
    
    # 保存
    plt.savefig(OUTPUT_IMAGE, bbox_inches="tight")
    print("成功！")
    print(f"=== 完了 ===\n同じフォルダに作成された '{OUTPUT_IMAGE}' を開いて確認せよ。")

except Exception as e:
    print(f"\n[Fatal Error] 描画失敗: {e}")
    import traceback
    traceback.print_exc()