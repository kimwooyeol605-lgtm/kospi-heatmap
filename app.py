import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="Advanced KOSPI Heatmap")
st.title("📊 Finviz 스타일 KOSPI 전문 분석기")

# 2. 데이터 불러오기
@st.cache_data
def get_base_data():
    df = pd.read_csv("kospi_list.csv")
    df['Code'] = df['Code'].astype(str).str.zfill(6)
    return df

base_df = get_base_data()

# 3. 사이드바 설정 (Finviz 항목 대거 추가)
st.sidebar.header("🔍 필터 및 옵션")

# 색상 및 텍스트 표시 지표 선택
# 사용자가 선택한 이 항목이 사각형 안에 숫자로 표시됩니다.
display_metric = st.sidebar.selectbox(
    "표시 및 색상 지표 선택",
    ["등락률", "PER", "PBR", "ROE", "배당수익률", "PEG"]
)

size_option = st.sidebar.selectbox("사각형 크기 기준", ["현재가", "등락률(절대값)"])
count = st.sidebar.slider("분석 종목 수", 10, len(base_df), 40)

# 4. 데이터 수집 함수
@st.cache_data(ttl=3600)
def fetch_finviz_data(df_base, limit):
    target_df = df_base.head(limit).copy()
    final_list = []
    
    status_text = st.empty()
    status_text.text("데이터 분석 중... 잠시만 기다려주세요.")

    for i, row in target_df.iterrows():
        ticker_symbol = f"{row['Code']}.KS"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # 가격 및 등락률
            current_price = info.get('currentPrice', 0)
            prev_close = info.get('previousClose', 0)
            change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            
            final_list.append({
                '종목명': row['Name'],
                '섹터': row['Sector'] if pd.notna(row['Sector']) else '기타',
                '현재가': current_price,
                '등락률': round(change, 2),
                'PER': round(info.get('forwardPE') or info.get('trailingPE') or 0, 2),
                'PBR': round(info.get('priceToBook') or 0, 2),
                'ROE': round((info.get('returnOnEquity') or 0) * 100, 2),
                '배당수익률': round((info.get('dividendYield') or 0) * 100, 2),
                'PEG': round(info.get('pegRatio') or 0, 2),
                '등락률(절대값)': abs(change) + 0.1
            })
        except:
            continue
            
    status_text.empty()
    return pd.DataFrame(final_list)

# 5. 실행 및 히트맵 생성
df = fetch_finviz_data(base_df, count)

if not df.empty:
    # Finviz 스타일 색상 로직 (빨강=고평가/하락, 초록=저평가/상승)
    # PER, PBR, PEG는 낮을수록 초록색(저평가)으로 표시합니다.
    if display_metric in ["PER", "PBR", "PEG"]:
        color_scale = 'RdYlGn_r' # _r은 색상 반전 (낮은 게 초록)
        mid_val = df[display_metric].median()
    elif display_metric == "ROE" or display_metric == "배당수익률":
        color_scale = 'YlGn' # 높은 게 좋은 것이므로 초록 계열
        mid_val = None
    else: # 등락률
        color_scale = 'RdYlGn'
        mid_val = 0

    # 히트맵 생성
    fig = px.treemap(df, 
                     path=[px.Constant("KOSPI"), '섹터', '종목명'], 
                     values=size_option, 
                     color=display_metric,
                     # 사각형 안에 종목명과 함께 사용자가 선택한 지표 숫자를 표시
                     custom_data=['종목명', display_metric],
                     color_continuous_scale=color_scale,
                     color_continuous_midpoint=mid_val,
                     height=800)

    # 텍스트 표시 설정 (Finviz처럼 종목명 아래에 숫자가 나오게 함)
    fig.update_traces(
        texttemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}",
        textposition="middle center",
        textfont=dict(size=15)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("데이터를 수집하지 못했습니다. 잠시 후 새로고침 해주세요.")