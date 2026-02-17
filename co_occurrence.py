import os
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from janome.tokenizer import Tokenizer
from matplotlib import font_manager

# --- ▼▼▼ ここが消えていた設定エリア（復活） ▼▼▼ ---
TEXT_FILE = "input/input.txt"          # そうだ、inputフォルダのファイルだ
OUTPUT_IMAGE = "output/network_graph.png"

# ★重要：君のフォント名に合わせて書き換えること！
# （BIZ-UDGothicR.ttc か msgothic.ttc のはずだ）
FONT_PATH = "font/BIZ-UDGothicR.ttc"   

# 厳しめの設定（ノイズ除去用）
MIN_EDGE_WEIGHT = 50   # 50回以上共起したものだけ
MAX_NODES = 50         # 上位50語だけ
# --- ▲▲▲ ここまで ▲▲▲ ---

# --- ストップワード（完全版・カンマ修正済み） ---
STOP_WORDS = [
    # 基礎的な助詞・代名詞
    "もの", "こと", "ため", "それ", "これ", "よう", "さん", "の", 
    "等", "図", "表", "白書", "平成", "令和", "年度", "年", "月", "日",
    "利用", "活用", "実施", "検討", "対応", "推進", "必要", "場合",
    "我が国", "日本", "地域", "社会", "環境", "対策", "構築", "目指",
    "概要", "状況", "保全", "活動", "取組", "部門", "評価", "基本的",
    "世界", "現在", "各種", "重要", "一部", "設定", "関係", "確保",
    # 追加ノイズ
    "indd", "R", "的", "化", "等", "上", "中", "性",
    # 行政用語・抽象語
    "具体的", "積極的", "総合的", "様々", "これら", "それら",
    "視点", "観点", "側面", "背景", "要因", "分野", "領域",
    "課題", "問題", "事項", "項目", "内容", "結果", "成果", "影響",
    "程度", "水準", "状態", "傾向", "全体", "部分", "中心",
    "促進", "強化", "充実", "図る", "向上", "維持",
    "達成", "実現", "展開", "実行", "措置",
    "連携", "協力", "支援", "参加", "理解", "認識"
]
# ------------------------------------

# 日本語フォント設定（matplotlib用）
from matplotlib import font_manager
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()


# --- 1. テキストを「文単位」で読み込む ---
print("テキストを読み込み、文単位に分割しています...")
with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    text = f.read()
# 「。」や改行で文章を区切る。これが共起の範囲になる。
sentences = text.replace('\n', '').split('。')

# --- 2. 文ごとに名詞ペアを作成し、カウントする ---
print("名詞のペアを探してカウントしています（少し時間がかかります）...")
t = Tokenizer()
pair_counts = {} # ペアの出現回数を記録する辞書

for sentence in sentences:
    # 文から名詞だけを抽出
    nouns = []
    for token in t.tokenize(sentence):
        part_of_speech = token.part_of_speech.split(',')[0]
        if part_of_speech == '名詞' and token.surface not in STOP_WORDS:
            nouns.append(token.surface)
    
    # 同じ文の中にある名詞の組み合わせ（ペア）を作る
    # 重複を除去してソートすることで「AとB」「BとA」を同じものとして扱う
    sorted_nouns = sorted(list(set(nouns)))
    for pair in itertools.combinations(sorted_nouns, 2):
        if pair in pair_counts:
            pair_counts[pair] += 1
        else:
            pair_counts[pair] = 1

# --- 3. ネットワーク・グラフの作成 ---
print("ネットワーク構造を計算しています...")
G = nx.Graph()

# 上位のペアだけをエッジ（線）として追加する
sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
node_degrees = {} # 各ノードのつながりの強さを記録

for pair, count in sorted_pairs:
    if count >= MIN_EDGE_WEIGHT:
        G.add_edge(pair[0], pair[1], weight=count)
        # ノードの重要度を計算用に記録
        node_degrees[pair[0]] = node_degrees.get(pair[0], 0) + count
        node_degrees[pair[1]] = node_degrees.get(pair[1], 0) + count

# ノード数が多すぎる場合は、つながりが弱いものを削除して制限する
if len(G.nodes) > MAX_NODES:
    print(f"ノード数が多すぎるため、上位{MAX_NODES}個に絞り込みます...")
    top_nodes = sorted(node_degrees, key=node_degrees.get, reverse=True)[:MAX_NODES]
    G = G.subgraph(top_nodes)

# --- 4. 可視化（描画） ---
print("グラフを描画しています...")
plt.figure(figsize=(15, 15)) # 画像サイズを大きくする

# ノードの配置を計算（spring_layout: バネモデルで自然な配置にする）
# kの値を大きくするとノード間の反発が強くなり、広がる
pos = nx.spring_layout(G, k=0.6, seed=42) 

# エッジの太さを共起回数（weight）に基づいて変える
edge_width = [G[u][v]['weight'] * 0.05 for u, v in G.edges()]

# ノードの大きさを重要度に基づいて変える
node_size = [node_degrees.get(n, 100) * 5 for n in G.nodes()]

# 描画実行
nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color="skyblue", alpha=0.7)
nx.draw_networkx_edges(G, pos, width=edge_width, edge_color="gray", alpha=0.5)
nx.draw_networkx_labels(G, pos, font_family=plt.rcParams['font.family'], font_size=12)

plt.title("共起ネットワーク図", fontsize=20)
plt.axis('off') # 軸を消す
plt.savefig(OUTPUT_IMAGE, bbox_inches="tight") # 画像保存
print(f"完了！画像を確認してください: {OUTPUT_IMAGE}")
# plt.show() # プレビューは重いのでコメントアウト推奨