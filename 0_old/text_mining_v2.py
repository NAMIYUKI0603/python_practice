import MeCab
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import japanize_matplotlib  # 日本語表示用
import itertools
from collections import Counter

# ==========================================
# 設定
# ==========================================
TARGET_FILE = "diary.txt"  # 分析するファイル
STOP_WORDS = ["よう", "こと", "もの", "これ", "それ", "ん", "ため", "日", "2025", "2024", "1", "2", "3", "月", "火", "水", "木", "金"] # ストップワードに追加

def get_coocurance(text):
    tagger = MeCab.Tagger()
    node = tagger.parseToNode(text)
    
    sentences = []
    current_sentence = []
    
    while node:
        # 句点「。」で文を区切るのが理想だが、簡易的に名詞のリストを作る
        features = node.feature.split(",")
        word = node.surface
        
        if features[0] == "名詞" and features[1] not in ["代名詞", "数", "非自立", "接尾"]:
            if word not in STOP_WORDS:
                current_sentence.append(word)
        
        # 文末判定（簡易版）
        if word in ["。", "．", "\n"]:
            if current_sentence:
                sentences.append(current_sentence)
                current_sentence = []
        
        node = node.next
        
    return sentences

def draw_network(sentences):
    # 共起ペアの作成
    pair_list = []
    for sentence in sentences:
        # 1文の中にある単語の組み合わせを全通り作る
        pair_list.extend(itertools.combinations(set(sentence), 2))
    
    # ペアの頻度をカウント
    cnt_pairs = Counter(pair_list)
    
    # 上位N件のペアに絞る（多すぎると見えないため）
    TOP_N = 150 # 線の数。多すぎたら減らせ
    common_pairs = cnt_pairs.most_common(TOP_N)
    
    # グラフの作成
    G = nx.Graph()
    # 重み付きの枝を加える
    for (u, v), w in common_pairs:
        G.add_edge(u, v, weight=w)
    
    # 描画設定
    plt.figure(figsize=(15, 15))
    pos = nx.spring_layout(G, k=0.3) # kの値でノード間の反発力を調整
    
    # ノードの大きさ（次数中心性＝つながりの多さで決める）
    d = dict(G.degree)
    
    # エッジ（線）の描画
    # 重み（出現回数）によって太さを変える
    edge_width = [d['weight']*0.1 for (u, v, d) in G.edges(data=True)]
    
    nx.draw_networkx_nodes(G, pos, node_size=[v * 100 for v in d.values()], node_color="#66ccff", alpha=0.6)
    nx.draw_networkx_edges(G, pos, width=edge_width, edge_color="#999999", alpha=0.5)
    nx.draw_networkx_labels(G, pos, font_family='IPAexGothic', font_size=12) # フォントはjapanize_matplotlibが自動適用するはずだが念のため
    
    plt.title("業務日誌 共起ネットワーク図", fontsize=20)
    plt.axis("off")
    plt.show()

# ==========================================
# 実行
# ==========================================
if __name__ == "__main__":
    try:
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            text = f.read()
    except:
        with open(TARGET_FILE, "r", encoding="cp932") as f: # Shift-JIS対応
            text = f.read()

    sentences = get_coocurance(text)
    draw_network(sentences)