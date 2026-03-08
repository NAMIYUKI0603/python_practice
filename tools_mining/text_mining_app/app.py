import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from janome.tokenizer import Tokenizer
import collections
import re
import os
import numpy as np
from PIL import Image

# --- ページ設定 ---
st.set_page_config(page_title="テキストマイニングアプリ", layout="wide")

# --- 日本語フォントの設定 ---
# GitHub (Streamlit Community Cloud) 等の環境とローカルWindows環境を考慮
def get_font_path():
    # 1. ローカルに直接配置されたフォント（IPAexGothic等を想定）
    local_fonts = ["font.ttf", "font.ttc", "ipaexg.ttf"]
    for lf in local_fonts:
        if os.path.exists(lf):
            return lf
    
    # 2. Windowsの標準フォント
    win_fonts = ["C:/Windows/Fonts/meiryo.ttc", "C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/YuGothM.ttc"]
    for wf in win_fonts:
        if os.path.exists(wf):
            return wf
            
    # 3. Streamlit Community Cloud (Debian系Linux) の標準的日本語フォントパッケージ
    linux_fonts = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
    ]
    for lxf in linux_fonts:
        if os.path.exists(lxf):
            return lxf
            
    return None

FONT_PATH = get_font_path()

# matplotlibの日本語フォント設定（見つかった場合のみ）
if FONT_PATH:
    if 'meiryo' in FONT_PATH.lower():
        plt.rcParams['font.family'] = 'Meiryo'
    elif 'msgothic' in FONT_PATH.lower():
        plt.rcParams['font.family'] = 'MS Gothic'
    elif 'yugoth' in FONT_PATH.lower():
        plt.rcParams['font.family'] = 'Yu Gothic'
    elif 'noto' in FONT_PATH.lower():
        plt.rcParams['font.family'] = 'Noto Sans CJK JP'
    else:
        plt.rcParams['font.family'] = 'sans-serif'
else:
    # 最終的なフォールバック
    plt.rcParams['font.family'] = 'sans-serif'

st.title("テキストマイニングWebアプリ")

# --- 1. サイドバー（操作・設定パネル） ---
st.sidebar.header("1. 基本設定")

uploaded_file = st.sidebar.file_uploader(
    "ファイルをアップロード (PDFまたはTXT)", 
    type=['pdf', 'txt']
)

stop_words_input = st.sidebar.text_area(
    "除外する単語（カンマ区切り）", 
    value="する,いる,ある,なる,こと,もの", 
    help="分析から除外したい単語をカンマ区切りで入力してください"
)
custom_stop_words = [w.strip() for w in stop_words_input.split(",") if w.strip()]

st.sidebar.markdown("---")
st.sidebar.header("2. ワードクラウド高度な設定")

# 【新機能】解像度の設定
resolution_option = st.sidebar.selectbox(
    "画質の選択", 
    ["標準 (800x400)", "高画質 (1600x800)", "超高画質 (3200x1600)"],
    help="画質を上げると生成に少し時間がかかる場合があります。"
)

# 【新機能】カラーテーマの設定
color_theme = st.sidebar.selectbox(
    "文字のカラーテーマ",
    ["オーシャン (標準)", "青系", "緑系", "赤・オレンジ系", "紫系", "グレースケール", "カラフル", "パステル"],
    help="ワードクラウドの色合いを選択できます。"
)

# カラーマップの変換辞書
cmap_dict = {
    "オーシャン (標準)": "ocean",
    "青系": "Blues",
    "緑系": "Greens",
    "赤・オレンジ系": "Oranges",
    "紫系": "Purples",
    "グレースケール": "gray",
    "カラフル": "Set1",
    "パステル": "Pastel1"
}
selected_cmap = cmap_dict[color_theme]

# 【新機能】マスク画像
mask_file = st.sidebar.file_uploader(
    "マスク画像のアップロード (任意)", type=['png', 'jpg', 'jpeg'],
    help="白黒の画像（シルエット画像など）をアップロードすると、黒い部分に文字が配置されます。"
)

mask_array = None
if mask_file is not None:
    try:
        # 画像をグレースケールで読み込み
        img = Image.open(mask_file).convert("L")
        # numpy配列化
        img_array = np.array(img)
        # 閾値で2極化（黒っぽい部分を確実に0に、白っぽい部分を255に）
        # WordCloudでは白地（255）を背景として無視し、それ以外に描画する
        mask_array = np.where(img_array > 128, 255, 0).astype(np.uint8)
        st.sidebar.success("マスク画像を読み込みました！")
    except Exception as e:
        st.sidebar.error("マスク画像の処理に失敗しました。")

st.sidebar.markdown("---")
analyze_button = st.sidebar.button("分析実行", type="primary", use_container_width=True)

# --- テキスト抽出・前処理・分析用関数 ---

def extract_text(file) -> str:
    file_ext = file.name.lower().split('.')[-1]
    if file_ext == 'pdf':
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text
    elif file_ext == 'txt':
        return file.read().decode('utf-8', errors='replace')
    return ""

def clean_text(text: str) -> str:
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[!"#$%&\'\\\\()*+,-./:;<=>?@[\\]^_`{|}~「」〔〕“”〈〉『』【】＆＊・（）＄＃＠？！｀＋￥％]', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[\r\n\t]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyze_morph(text: str, stop_words: list) -> list:
    t = Tokenizer()
    words = []
    for token in t.tokenize(text):
        if token.part_of_speech.startswith('名詞'):
            word = token.surface
            if len(word) > 1 and word not in stop_words:
                words.append(word)
    return words

# --- メインエリア（結果表示パネル）の処理 ---

if analyze_button:
    if uploaded_file is None:
        st.sidebar.error("テキストファイルをアップロードしてください。")
    else:
        with st.spinner('テキストを抽出・分析中です...お待ちください'):
            raw_text = extract_text(uploaded_file)
            if not raw_text.strip():
                st.error("テキストを抽出できませんでした。ファイルの中身を確認してください。")
            else:
                st.subheader("アップロードされたテキストのプレビュー")
                preview_text = raw_text[:500] + ("..." if len(raw_text) > 500 else "")
                st.text_area("", value=preview_text, height=150, disabled=True)
                
                cleaned_text = clean_text(raw_text)
                words_list = analyze_morph(cleaned_text, custom_stop_words)
                
                if not words_list:
                    st.warning("処理対象となる有効な単語（名詞）が抽出されませんでした。")
                else:
                    word_counts = collections.Counter(words_list)
                    top_20 = word_counts.most_common(20)
                    
                    if top_20:
                        df_top20 = pd.DataFrame(top_20, columns=['単語', '出現回数'])
                        df_top20.index = df_top20.index + 1
                        
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("出現頻度上位20語 (棒グラフ)")
                            fig, ax = plt.subplots(figsize=(8, 6))
                            words = df_top20['単語'][::-1]
                            counts = df_top20['出現回数'][::-1]
                            ax.barh(words, counts, color='skyblue')
                            ax.set_xlabel('出現回数')
                            ax.set_title('単語の出現頻度')
                            fig.tight_layout()
                            st.pyplot(fig)
                            plt.close(fig)
                            
                        with col2:
                            st.subheader("出現頻度上位20語 (データテーブル)")
                            st.dataframe(df_top20, use_container_width=True)
                            
                        st.markdown("---")
                        st.subheader("ワードクラウド")
                        
                        # 画質設定の適用
                        if "標準" in resolution_option:
                            wc_width, wc_height, max_words = 800, 400, 100
                            fig_size = (10, 5)
                            fig_dpi = 100
                        elif "高画質" in resolution_option:
                            wc_width, wc_height, max_words = 1600, 800, 200
                            fig_size = (16, 8)
                            fig_dpi = 200
                        else:  # 超高画質
                            wc_width, wc_height, max_words = 3200, 1600, 400
                            fig_size = (24, 12)
                            fig_dpi = 300
                            
                        wc_kwargs = {
                            "background_color": 'white',
                            "colormap": selected_cmap,
                            "max_words": max_words,
                            "width": wc_width,
                            "height": wc_height
                        }
                        
                        if FONT_PATH:
                            wc_kwargs["font_path"] = FONT_PATH
                        
                        # マスク画像の適用処理
                        if mask_array is not None:
                            wc_kwargs["mask"] = mask_array
                            wc_kwargs["contour_width"] = 1
                            wc_kwargs["contour_color"] = 'skyblue'
                            # マスク指定時は縦横比がマスク画像に依存するため、fig_sizeを調整
                            h, w = mask_array.shape
                            aspect_ratio = w / h
                            # 高さをベースにして幅を計算
                            base_height = fig_size[1]
                            fig_size = (base_height * aspect_ratio, base_height)
                        
                        # 生成
                        wordcloud = WordCloud(**wc_kwargs).generate_from_frequencies(word_counts)
                        
                        # 描画（dpi指定で高画質出力させる）
                        fig_wc, ax_wc = plt.subplots(figsize=fig_size, dpi=fig_dpi)
                        ax_wc.imshow(wordcloud, interpolation='bilinear')
                        ax_wc.axis('off')
                        fig_wc.tight_layout(pad=0)
                        
                        st.pyplot(fig_wc)
                        plt.close(fig_wc)
