import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="KOSPI Heatmap")
st.title("🚀 KOSPI 전 종목 리얼 히트맵")

# 2. 데이터 불러오기 함수
@st.cache_data
def get_base_data():
    return pd.read_csv("kospi_list.csv", dtype={'Code': str})

try:
    base_df = get_base_data()

    # 3. 사이드바 설정
    st.sidebar.header("설정")
    color_metric = st.sidebar.selectbox("색상 기준", ["등락률", "현재가"])
    count = st.sidebar.slider("종목 수", 5, len(base_df), 20)

    # 4. 데이터 수집 (안정적인 개별 호출 방식)
    def fetch_data(df_base, limit):
        target_df = df_base.head(limit).copy()
        final_list = []
        
        progress_text = "주식 시세를 가져오는 중입니다..."
        my_bar = st.progress(0, text=progress_text)

        for i, row in enumerate(target_df.itertuples()):
            ticker = row.Code + ".KS"
            try:
                s = yf.Ticker(ticker)
                # fast_info를 사용하여 속도를 높입니다
                hist = s.history(period="2d")
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = ((current_price - prev_price) / prev_price) * 100
                else:
                    current_price = 0
                    change = 0
                
                final_list.append({
                    '종목명': row.Name,
                    '섹터': row.Sector if pd.notna(row.Sector) else '기타',
                    '현재가': current_price,
                    '등락률': change
                })
            except:
                continue
            my_bar.progress((i + 1) / limit)
        
        my_bar.empty()
        return pd.DataFrame(final_list)

    if st.button('데이터 업데이트 시작'):
        df = fetch_data(base_df, count)
        
        if not df.empty:
            # 5. 히트맵 그리기 (사각형 크기를 등락률 절대값으로 설정)
            df['abs_change'] = df['등락률'].abs() + 1 # 크기가 0이면 안되므로 +1
            
            fig = px.treemap(df, 
                             path=[px.Constant("KOSPI"), '섹터', '종목명'], 
                             values='abs_change', # 사각형 크기
                             color='등락률',      # 색상 기준
                             hover_data=['현재가', '등락률'],
                             color_continuous_scale='RdYlGn',
                             color_continuous_midpoint=0,
                             height=700)

            fig.update_traces(textinfo="label+value")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("데이터를 가져오지 못했습니다. 잠시 후 다시 시도하세요.")
    else:
        st.info("왼쪽에서 종목 수를 정하고 '데이터 업데이트 시작' 버튼을 눌러주세요!")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")