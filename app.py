import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 페이지 설정 (가장 기본적이고 안전한 방식)
st.set_page_config(layout="wide", page_title="KOSPI MARKET HEATMAP")

# 에러의 원인이었던 복잡한 CSS 대신 제목만 깔끔하게 표시합니다.
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
    status.text("데이터 동기화 중...")

    for row in target_df.itertuples():
        ticker_symbol = f"{row.Code}.KS"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # 시가총액 (사각형 크기 결정 - Finviz 방식)
            m_cap = info.get('marketCap', 0)
            
            # 가격 정보
            cur_p = info.get('currentPrice', 0)
            prev_p = info.get('previousClose', 0)
            change = ((cur_p - prev_p) / prev_p * 100) if prev_p else 0
            
            # 재무 지표 (N/A 처리 및 백분율 환산)
            per = info.get('forwardPE') or info.get('trailingPE') or 0
            pbr = info.get('priceToBook') or 0
            roe_val = (info.get('returnOnEquity') or 0) * 100
            div_val = (info.get('dividendYield') or 0) * 100
            
            final_list.append({
                '종목명': row.Name,
                '섹터': row.Sector if pd.notna(row.Sector) else '기타',
                '시가총액': m_cap,
                '등락률': round(change, 2),
                'PER': round(per, 2) if per else "N/A",
                'PBR': round(pbr, 2) if pbr else "N/A",
                'ROE': f"{round(roe_val, 2)}%",
                '배당수익률': f"{round(div_val, 2)}%",
                'val_ROE': roe_val,
                'val_DIV': div_val,
                'val_PER': per,
                'val_PBR': pbr
            })
        except:
            continue
            
    status.empty()
    return pd.DataFrame(final_list)

df = fetch_pro_data(base_df, count)

# 5. 시각화 실행 (Plotly 자체 다크 테마 사용)
if not df.empty:
    # 지표별 색상 맵핑
    if display_metric == "등락률":
        col_name, col_scale, col_mid = "등락률", "RdYlGn", 0
    elif display_metric == "PER":
        col_name, col_scale, col_mid = "val_PER", "RdYlGn_r", 15
    elif display_metric == "PBR":
        col_name, col_scale, col_mid = "val_PBR", "RdYlGn_r", 1.0
    elif display_metric == "ROE":
        col_name, col_scale, col_mid = "val_ROE", "Greens", None
    else: # 배당수익률
        col_name, col_scale, col_mid = "val_DIV", "Greens", None

    fig = px.treemap(df, 
                     path=[px.Constant("KOSPI"), '섹터', '종목명'], 
                     values='시가총액', # 시가총액 크기 반영
                     color=col_name,
                     custom_data=['종목명', display_metric],
                     color_continuous_scale=col_scale,
                     color_continuous_midpoint=col_mid,
                     template="plotly_dark", # 안전한 다크 테마 적용
                     height=800)

    fig.update_traces(
        texttemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}",
        textposition="middle center"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("데이터를 수집하는 중입니다. 잠시 후 새로고침 해주세요.")