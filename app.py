import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 페이지 설정 및 제목
st.set_page_config(layout="wide", page_title="PRO KOSPI Heatmap")
st.title("📈 KOSPI 전문 가치평가 히트맵")

# 2. 데이터 불러오기 (기존 CSV 활용)
@st.cache_data
def get_base_data():
    return pd.read_csv("kospi_list.csv", dtype={'Code': str})

base_df = get_base_data()

# 3. 사이드바 - 다양한 옵션 추가 (Finviz 핵심 기능)
st.sidebar.header("⚙️ 시각화 옵션")

# 크기 기준 선택
size_option = st.sidebar.selectbox(
    "사각형 크기 기준 (Size)",
    ["현재가", "등락률(절대값)"] # 나중에 시가총액 데이터를 넣으면 더 완벽해집니다.
)

# 색상 기준 선택
color_option = st.sidebar.selectbox(
    "색상 표시 지표 (Color)",
    ["등락률", "PER", "PBR", "ROE"]
)

count = st.sidebar.slider("분석 종목 수", 10, len(base_df), 30)

# 4. 고급 데이터 수집 함수
def fetch_pro_data(df_base, limit):
    target_df = df_base.head(limit).copy()
    final_list = []
    my_bar = st.progress(0, text="데이터 분석 중...")

    for i, row in enumerate(target_df.itertuples()):
        ticker = row.Code + ".KS"
        try:
            s = yf.Ticker(ticker)
            info = s.info # 상세 재무 지표를 가져옵니다.
            
            # 가격 데이터 (최근 2일치)
            hist = s.history(period="2d")
            change = 0
            if len(hist) >= 2:
                change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            
            final_list.append({
                '종목명': row.Name,
                '섹터': row.Sector if pd.notna(row.Sector) else '기타',
                '현재가': info.get('currentPrice', 0),
                '등락률': change,
                'PER': info.get('forwardPE', 0),
                'PBR': info.get('priceToBook', 0),
                'ROE': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                '등락률(절대값)': abs(change) + 1 # 크기용
            })
        except:
            continue
        my_bar.progress((i + 1) / limit)
    
    my_bar.empty()
    return pd.DataFrame(final_list)

# 5. 실행 및 출력
if st.sidebar.button('📊 히트맵 업데이트'):
    df = fetch_pro_data(base_df, count)
    
    if not df.empty:
        # 지표에 따른 색상 스케일 설정
        if color_option == "등락률":
            scale = 'RdYlGn'
            mid = 0
        elif color_option == "ROE":
            scale = 'Greens'
            mid = None
        else: # PER, PBR은 낮을수록 좋으므로 반전 스케일
            scale = 'RdYlGn_r'
            mid = df[color_option].median() # 중앙값을 기준으로 색상 분리

        fig = px.treemap(df, 
                         path=[px.Constant("KOSPI"), '섹터', '종목명'], 
                         values=size_option, 
                         color=color_option,
                         hover_data=['현재가', '등락률', 'PER', 'PBR', 'ROE'],
                         color_continuous_scale=scale,
                         color_continuous_midpoint=mid,
                         height=800)

        fig.update_traces(textinfo="label+value")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("데이터를 불러오지 못했습니다.")
else:
    st.info("왼쪽 사이드바에서 옵션을 정하고 [히트맵 업데이트]를 눌러주세요!")