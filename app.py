import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 페이지 설정 및 다크 테마 적용
st.set_page_config(layout="wide", page_title="PRO KOSPI Heatmap")

st.markdown("""
    <style>
    .main { background-color: #121212 !important; }
    header { background-color: #121212 !important; }
    section[data-testid="stSidebar"] { background-color: #1e1e1e !important; }
    .stMarkdown h1 { color: #ffffff !important; text-align: center; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("⬛ KOSPI MARKET HEATMAP (PRO)")

# 2. 데이터 불러오기
@st.cache_data
def get_base_data():
    df = pd.read_csv("kospi_list.csv")
    df['Code'] = df['Code'].astype(str).str.zfill(6)
    return df

base_df = get_base_data()

# 3. 사이드바 설정
st.sidebar.header("🛠️ DASHBOARD SETTINGS")
display_metric = st.sidebar.selectbox(
    "지표 선택 (Color & Label)",
    ["등락률", "PER", "PBR", "ROE", "배당수익률"]
)
count = st.sidebar.slider("표시 종목 수 (시총 상위순)", 10, 100, 50)

# 4. 데이터 수집 함수
@st.cache_data(ttl=3600)
def fetch_pro_data(df_base, limit):
    target_df = df_base.head(limit).copy()
    final_list = []
    
    status = st.empty()
    status.text("Finviz 데이터 동기화 중...")

    for row in target_df.itertuples():
        ticker_symbol = f"{row.Code}.KS"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            m_cap = info.get('marketCap', 0)
            cur_p = info.get('currentPrice', 0)
            prev_p = info.get('previousClose', 0)
            change = ((cur_p - prev_p) / prev_p * 100) if prev_p else 0
            
            per = info.get('forwardPE') or info.get('trailingPE') or 0
            pbr = info.get('priceToBook') or 0
            roe = (info.get('returnOnEquity') or 0) * 100
            div = (info.get('dividendYield') or 0) * 100
            
            final_list.append({
                '종목명': row.Name,
                '섹터': row.Sector if pd.notna(row.Sector) else '기타',
                '시가총액': m_cap,
                '등락률': round(change, 2),
                'PER': round(per, 2) if per else "N/A",
                'PBR': round(pbr, 2) if pbr else "N/A",
                'ROE': f"{round(roe, 2)}%",
                '배당수익률': f"{round(div, 2)}%",
                'val_ROE': roe,
                'val_DIV': div,
                'val_PER': per,
                'val_PBR': pbr
            })
        except:
            continue
            
    status.empty()
    return pd.DataFrame(final_list)

df = fetch_pro_data(base_df, count)

# 5. 시각화 실행
if not df.empty:
    metric_map = {
        "등락률": ("등락률", "RdYlGn", 0),
        "PER": ("val_PER", "RdYlGn_r", 15),
        "PBR": ("val_PBR", "RdYlGn_r", 1.0),
        "ROE": ("val_ROE", "Greens", None),
        "배당수익률": ("val_DIV", "Greens", None)
    }
    
    col_name, col_scale, col_mid = metric_map[display_metric]

    fig = px.treemap(df, 
                     path=[px.Constant("KOSPI"), '섹터', '종목명'], 
                     values='시가총액', 
                     color=col_name,
                     custom_data=['종목명', display_metric],
                     color_continuous_scale=col_scale,
                     color_continuous_midpoint=col_mid,
                     template="plotly_dark",
                     height=800)

    fig.update_traces(
        texttemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}",
        textposition="middle center",
        hovertemplate="<b>%{label}</b><br>시가총액: %{value:,.0f}<br>지표: %{customdata[1]}"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("데이터를 수집 중입니다. 잠시만 기다려주세요.")