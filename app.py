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

# --- 2. データの読み込みと安全処理 ---
@st.cache_data
def load_data():
    df = pd.read_csv("output/master_sibou_all_industries.csv", encoding='utf-8-sig', low_memory=False)
    
    # 階層グラフ（サンバースト）は欠損値(NaN)で描画エラーを起こすため、防御機構として「不明」で埋める
    fill_cols = ['起因物_大分類', '起因物_中分類', '起因物_小分類', '事業場規模', '発生時間']
    for col in fill_cols:
        if col in df.columns:
            df[col] = df[col].fillna('不明')
            
    # 月や年の欠損も除外しておく
    df = df.dropna(subset=['年', '月'])
    return df

df = load_data()

# --- 3. サイドバー（全方位フィルター設定） ---
st.sidebar.header("🔍 フィルター設定")

# ① 業種（階層連動）
st.sidebar.subheader("🏢 業種")
industry_l_list = ["すべて"] + sorted(df['業種_大分類'].unique().tolist())
selected_l = st.sidebar.selectbox("業種（大分類）", industry_l_list)

if selected_l != "すべて":
    df_m = df[df['業種_大分類'] == selected_l]
    industry_m_list = ["すべて"] + sorted(df_m['業種_中分類'].unique().tolist())
else:
    industry_m_list = ["すべて"]
selected_m = st.sidebar.selectbox("業種（中分類）", industry_m_list)

if selected_m != "すべて":
    df_s = df_m[df_m['業種_中分類'] == selected_m]
    industry_s_list = ["すべて"] + sorted(df_s['業種_小分類'].unique().tolist())
else:
    industry_s_list = ["すべて"]
selected_s = st.sidebar.selectbox("業種（小分類）", industry_s_list)

st.sidebar.markdown("---")

# ② 日時と規模（マルチセレクト）
st.sidebar.subheader("⏱ 発生状況・規模")
year_list = sorted(df['年'].unique().tolist())
selected_years = st.sidebar.multiselect("発生年", year_list, default=year_list)

month_list = sorted(df['月'].unique().tolist())
selected_months = st.sidebar.multiselect("発生月", month_list, default=month_list)

time_list = sorted(df['発生時間'].unique().tolist())
selected_times = st.sidebar.multiselect("発生時間帯", time_list, default=time_list)

size_list = sorted(df['事業場規模'].unique().tolist())
selected_sizes = st.sidebar.multiselect("事業場規模", size_list, default=size_list)

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
if selected_months:
    filtered_df = filtered_df[filtered_df['月'].isin(selected_months)]
if selected_times:
    filtered_df = filtered_df[filtered_df['発生時間'].isin(selected_times)]
if selected_sizes:
    filtered_df = filtered_df[filtered_df['事業場規模'].isin(selected_sizes)]

# --- 5. メイン画面の描画（グラフの生成） ---
st.markdown(f"### 現在の抽出件数: {len(filtered_df)} 件")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 事故の型（何が起きたか）")
    if not filtered_df.empty:
        type_counts = filtered_df['事故の型'].value_counts().reset_index()
        type_counts.columns = ['事故の型', '件数']
        
        fig_bar = px.bar(type_counts, x='件数', y='事故の型', orientation='h', color='件数', color_continuous_scale='Reds', text='件数')
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis=dict(showgrid=True, gridcolor='lightgray'),
            plot_bgcolor='white',
            margin=dict(l=0, r=0, t=30, b=0)
        ) 
        st.plotly_chart(fig_bar, width="stretch")
    else:
        st.info("条件に一致するデータがありません。")

with col2:
    st.subheader("🎯 起因物（大→中→小 クリックでドリルダウン）")
    if not filtered_df.empty:
        # 【中核の改修】サンバースト・チャート（階層型ドリルダウン）の適用
        fig_sunburst = px.sunburst(
            filtered_df, 
            path=['起因物_大分類', '起因物_中分類', '起因物_小分類'], 
            color_discrete_sequence=px.colors.sequential.Reds_r
        )
        # 内訳のパーセンテージとラベルを表示
        fig_sunburst.update_traces(textinfo="label+percent parent")
        fig_sunburst.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_sunburst, width="stretch")
    else:
        st.info("条件に一致するデータがありません。")

st.markdown("---")
st.subheader("📋 抽出データ一覧（災害状況の確認）")
if not filtered_df.empty:
    st.dataframe(filtered_df[['年', '月', '発生時間', '事業場規模', '業種_小分類', '起因物_小分類', '事故の型', '災害状況']].head(100))