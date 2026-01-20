import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 페이지 설정 (다크 모드 테마 적용)
st.set_page_config(layout="wide", page_title="PRO KOSPI Heatmap")

# CSS를 이용한 강제 다크 모드 스타일링
st.markdown("""
    <style>
    .main { background-color: #121212; }
    header { background-color: #121212 !important; }
    section[data-testid="stSidebar"] { background-color: #1e1e1e; }
    .stMarkdown h1 { color: #ffffff; text-align: center; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("⬛ KOSPI MARKET HEATMAP (PRO)")

# 2. 데이터 불러오기 (종목 코드 6자리 유지)
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
# 이제 시가총액이 기본 크기 기준이 됩니다.
count = st.sidebar.slider("표시 종목 수 (시총 상위순)", 10, len(base_df), 50)

# 4. 데이터 수집 함수 (시가총액 포함)
@st.cache_data(ttl=3600)
def fetch_pro_data(df_base, limit):
    target_df = df_base.head(limit).copy()
    final_list = []
    
    progress_bar = st.progress(0, text="Finviz 데이터 동기화 중...")

    for i, row in enumerate(target_df.itertuples()):
        ticker_symbol = f"{row.Code}.KS"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # 시가총액 (Market Cap) - 사각형 크기 결정용
            m_cap = info.get('marketCap', 0)
            
            # 가격 및 등락률
            current_price = info.get('currentPrice', 0)
            prev_close = info.get('previousClose', 0)
            change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            
            # 재무 지표 (N/A 값 처리 포함)
            per = info.get('forwardPE') or info.get('trailingPE') or 0
            pbr = info.get('priceToBook') or 0
            roe = (info.get('returnOnEquity') or 0) * 100
            div = (info.get('dividendYield') or 0) * 100 # 백분율 환산
            
            final_list.append({
                '종목명': row.Name,
                '섹터': row.Sector if pd.notna(row.Sector) else '기타',
                '시가총액': m_cap,
                '등락률': round(change, 2),
                'PER': round(per, 2) if per != 0 else "N/A",
                'PBR': round(pbr, 2) if pbr != 0 else "N/A",
                'ROE': f"{round(roe, 2)}%",
                '배당수익률': f"{round(div, 2)}%",
                # 시각화 수치용 (숫자형)
                'val_ROE': roe,
                'val_DIV': div,
                'val_PER': per,
                'val_PBR': pbr
            })
        except:
            continue
        progress_bar.progress((i + 1) / limit)
            
    progress_bar.empty()
    return pd.DataFrame(final_list)

# 5. 시각화 실행
df = fetch_pro_data(base_df, count)

if not df.empty:
    # 지표별 색상 및 데이터 맵핑
    metric_map = {
        "등락률": ("등락률", "RdYlGn", 0),
        "PER": ("val_PER", "RdYlGn_r", df[df['val_PER']>0]['val_PER'].median() if not df.empty else 15),
        "PBR": ("val_PBR", "RdYlGn_r", 1.0),
        "ROE": ("val_ROE", "Greens", None),
        "배당수익률": ("val_DIV", "Greens", None)
    }
    
    col_name, col_scale, col_mid = metric_map[display_metric]

    fig = px.treemap(df, 
                     path=[px.Constant("KOSPI"), '섹터', '종목명'], 
                     values='시가총액',  # 시가총액 가중평균 방식 적용
                     color=col_name,
                     custom_data=['종목명', display_metric], # 실제 표시될 텍스트