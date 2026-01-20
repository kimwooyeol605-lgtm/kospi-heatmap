import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="PRO KOSPI Heatmap")
st.title("📈 KOSPI 전문 가치평가 히트맵")

# 2. 데이터 불러오기 (Code 앞의 0을 살려서 불러옵니다)
@st.cache_data
def get_base_data():
    df = pd.read_csv("kospi_list.csv")
    df['Code'] = df['Code'].astype(str).str.zfill(6) # 6자리 숫자로 고정 (005930 형태)
    return df

base_df = get_base_data()

# 3. 사이드바 설정
st.sidebar.header("⚙️ 시각화 옵션")
size_option = st.sidebar.selectbox("사각형 크기 기준", ["현재가", "등락률(절대값)"])
color_option = st.sidebar.selectbox("색상 표시 지표", ["등락률", "PER", "PBR", "ROE"])
count = st.sidebar.slider("분석 종목 수", 10, len(base_df), 30)

# 4. 데이터 수집 함수 (더 안전한 방식)
@st.cache_data(ttl=3600) # 1시간 동안은 데이터를 저장해서 서버 차단 방지
def fetch_pro_data(df_base, limit):
    target_df = df_base.head(limit).copy()
    tickers = [f"{c}.KS" for c in target_df['Code']]
    
    final_list = []
    # 한꺼번에 가져오지 않고 하나씩 가져오되 에러를 철저히 무시합니다.
    for i, row in target_df.iterrows():
        ticker_symbol = f"{row['Code']}.KS"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # 가격 정보
            current_price = info.get('currentPrice', 0)
            prev_close = info.get('previousClose', 0)
            
            # 등락률 계산
            if prev_close != 0:
                change = ((current_price - prev_close) / prev_close) * 100
            else:
                change = 0
            
            final_list.append({
                '종목명': row['Name'],
                '섹터': row['Sector'] if pd.notna(row['Sector']) else '기타',
                '현재가': current_price,
                '등락률': change,
                'PER': info.get('forwardPE', 0) or info.get('trailingPE', 0) or 0,
                'PBR': info.get('priceToBook', 0) or 0,
                'ROE': (info.get('returnOnEquity', 0) or 0) * 100,
                '등락률(절대값)': abs(change) + 0.1
            })
        except:
            continue
            
    return pd.DataFrame(final_list)

# 5. 실행 및 출력 (버튼 없이 바로 실행)
df = fetch_pro_data(base_df, count)

if not df.empty:
    # 색상 설정 로직
    if color_option == "등락률":
        scale = 'RdYlGn'
        mid = 0
    elif color_option == "ROE":
        scale = 'Greens'
        mid = None
    else:
        scale = 'RdYlGn_r' # PER, PBR은 낮을수록 좋으므로 반대로
        mid = df[color_option].median()

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
    st.error("데이터 수집 중입니다. 잠시만 기다려주시거나 페이지를 새로고침 해주세요.")