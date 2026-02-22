import os
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

# --- 設定エリア（Control Panel） ---
TEXT_FILE = "input/input.txt"          # テキストファイル
FONT_PATH = "font/BIZ-UDGothicR.ttc"   # フォントファイル（※自分のファイル名に合わせる！）
MASK_IMAGE = "input/mask.jpg"          # シルエット画像
OUTPUT_IMAGE = "output/result_cloud_final.png"

# 除外したい単語（ストップワード）を強化
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

# --- 1. データ読み込み ---
print("テキストを読み込んでいます...")
with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    text = f.read()

# --- 2. 形態素解析 ---
print("言葉を分解しています...")
t = Tokenizer()
words = []

for token in t.tokenize(text):
    part_of_speech = token.part_of_speech.split(',')[0]
    # 名詞だけを取り出し、かつストップワードに含まれないもの
    if part_of_speech == '名詞' and token.surface not in STOP_WORDS:
        words.append(token.surface)

text_chain = ' '.join(words)

# --- 3. マスク画像の準備 ---
print("金型（マスク）を準備しています...")
try:
    mask_array = np.array(Image.open(MASK_IMAGE))
    
    # ▼▼▼ 【追加】 金型の洗浄処理（ここが重要） ▼▼▼
    # 「200より白い（明るい）場所は、すべて255（完全な白）にする」という命令
    # これでJPEG特有のノイズや薄いグレーが一掃される
    mask_array[mask_array > 200] = 255
    # ▲▲▲ここまで▲▲▲
except FileNotFoundError:
    print(f"【エラー】画像が見つかりません: {MASK_IMAGE}")
    print("inputフォルダに mask.png があるか確認してください。")
    exit()

# --- 4. 可視化生成 ---
print("画像を生成しています...")
wc = WordCloud(
    background_color="white",
    font_path=FONT_PATH,
    mask=mask_array,
    contour_width=0,
    colormap="viridis",
    # ▼▼▼【追加】ここがポイントだ▼▼▼
    scale=5,  # デフォルトは1。ここを3や4にすると超高画質になる
    # ▲▲▲ここまで▲▲▲
    stopwords=set(STOP_WORDS)
)

wc.generate(text_chain)

# --- 5. 出力 ---
wc.to_file(OUTPUT_IMAGE)
print(f"完了！画像を確認してください: {OUTPUT_IMAGE}")

# プレビュー表示
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.show()