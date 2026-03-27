import streamlit as st
import pandas as pd
import plotly.express as px

# --- 0. 防弾ドア（セキュリティロック） ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "namiyuki2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        st.error("パスワードが間違っています。")
        return False
    return True

if not check_password():
    st.stop()

# --- 1. アプリの基本設定 ---
st.set_page_config(page_title="労災分析ダッシュボード", layout="wide")
st.title("⚡ 労働災害 統合分析ダッシュボード")

# --- 2. データの読み込み ---
@st.cache_data
def load_data():
    df = pd.read_csv("output/master_sibou_all_industries.csv", encoding='utf-8-sig', low_memory=False)
    return df

df = load_data()

# --- 3. サイドバー（連動型フィルター設定） ---
st.sidebar.header("🔍 フィルター設定")

# ① 大分類の選択
industry_l_list = ["すべて"] + sorted(df['業種_大分類'].dropna().unique().tolist())
selected_l = st.sidebar.selectbox("業種（大分類）を選択", industry_l_list)

# ② 中分類の選択（大分類の選択結果でリストを絞り込む）
if selected_l != "すべて":
    df_m = df[df['業種_大分類'] == selected_l]
    industry_m_list = ["すべて"] + sorted(df_m['業種_中分類'].dropna().unique().tolist())
else:
    industry_m_list = ["すべて"]
selected_m = st.sidebar.selectbox("業種（中分類）を選択", industry_m_list)

# ③ 小分類の選択（中分類の選択結果でリストを絞り込む）
if selected_m != "すべて":
    df_s = df_m[df_m['業種_中分類'] == selected_m]
    industry_s_list = ["すべて"] + sorted(df_s['業種_小分類'].dropna().unique().tolist())
else:
    industry_s_list = ["すべて"]
selected_s = st.sidebar.selectbox("業種（小分類）を選択", industry_s_list)

# ④ 発生年の選択
year_list = sorted(df['年'].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("発生年を選択", year_list, default=year_list)

# --- 4. 空間のフィルタリング（階層的な絞り込み） ---
filtered_df = df.copy()
if selected_l != "すべて":
    filtered_df = filtered_df[filtered_df['業種_大分類'] == selected_l]
if selected_m != "すべて":
    filtered_df = filtered_df[filtered_df['業種_中分類'] == selected_m]
if selected_s != "すべて":
    filtered_df = filtered_df[filtered_df['業種_小分類'] == selected_s]
if selected_years:
    filtered_df = filtered_df[filtered_df['年'].isin(selected_years)]

# --- 5. メイン画面の描画（グラフの生成） ---
st.markdown(f"### 現在の抽出件数: {len(filtered_df)} 件")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 事故の型（何が起きたか）")
    type_counts = filtered_df['事故の型'].value_counts().reset_index()
    type_counts.columns = ['事故の型', '件数']
    
    # 【改修】テキスト（件数）をグラフに付与
    fig_bar = px.bar(type_counts, x='件数', y='事故の型', orientation='h', color='件数', color_continuous_scale='Reds', text='件数')
    
    # 【改修】メモリ線の追加と、テキストの右側外出し配置
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis=dict(showgrid=True, gridcolor='lightgray'), # 縦のメモリ線を表示
        plot_bgcolor='white' # 背景を白にしてメモリ線を見やすくする
    ) 
    st.plotly_chart(fig_bar, width="stretch")

with col2:
    st.subheader("🍩 起因物（何が原因か）")
    cause_counts = filtered_df['起因物_大分類'].value_counts().reset_index()
    cause_counts.columns = ['起因物', '件数']
    fig_pie = px.pie(cause_counts, names='起因物', values='件数', hole=0.4)
    st.plotly_chart(fig_pie, width="stretch")

st.markdown("---")
st.subheader("📋 抽出データ一覧（災害状況の確認）")
st.dataframe(filtered_df[['年', '月', '発生時間', '業種_大分類', '業種_中分類', '業種_小分類', '事故の型', '災害状況']].head(100))