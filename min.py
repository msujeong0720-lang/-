import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(
    page_title="Global Current Account Dashboard",
    layout="wide"
)

st.title("🌎 국가별 경상수지 분석 대시보드")

# 국가 목록
countries = {
    "대한민국": "KOR",
    "미국": "USA",
    "일본": "JPN",
    "독일": "DEU",
    "중국": "CHN",
    "영국": "GBR"
}

@st.cache_data
def get_current_account():
    data = []
    for country, code in countries.items():
        # &order=date:asc 를 추가하여 연도 순 정렬 보장
        url = (
            f"https://api.worldbank.org/v2/country/{code}"
            "/indicator/BN.CAB.XOKA.GD.ZS"
            "?format=json&per_page=100&order=date:asc"
        )
        try:
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if len(result) < 2:
                continue
                
            for row in result[1]:
                if row["value"] is not None:
                    data.append({
                        "국가": country,
                        "코드": code,
                        "연도": int(row["date"]),
                        "경상수지비율": row["value"]
                    })
        except Exception as e:
            # API 호출 실패 시 에러를 뿜지 않고 넘어가도록 예외 처리
            continue
            
    return pd.DataFrame(data)

df = get_current_account()

if df.empty:
    st.error("World Bank API로부터 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

# 1. 안전하게 전체 데이터셋을 연도 순으로 미리 정렬
df = df.sort_values(by=["국가", "연도"]).reset_index(drop=True)

# 2. 최신 데이터 추출 (각 국가별 가장 최근 연도의 데이터)
latest = df.groupby("국가").last().reset_index()

st.subheader("🌍 세계 경상수지 지도")

map_chart = px.choropleth(
    latest,
    locations="코드",
    color="경상수지비율",
    hover_name="국가",
    color_continuous_scale="RdBu",
    title="GDP 대비 경상수지 (%)"
)
st.plotly_chart(map_chart, use_container_width=True)

st.divider()

country = st.selectbox("분석할 국가 선택", list(countries.keys()))

# 선택한 국가 데이터 필터링
country_data = df[df["국가"] == country]

if country_data.empty:
    st.warning(f"{country}의 데이터가 존재하지 않습니다.")
else:
    # 이미 위에서 연도순 정렬을 했으므로, 맨 마지막 행이 최신 데이터임이 보장됨
    last = country_data.iloc[-1]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label=f"최근 경상수지/GDP ({last['연도']}년)",
            value=f"{last['경상수지비율']:.2f}%"
        )
    with col2:
        status = "흑자" if last["경상수지비율"] > 0 else "적자"
        st.metric(label="상태", value=status)

    st.subheader(f"📈 {country} 경상수지 변화")
    line = px.line(
        country_data,
        x="연도",
        y="경상수지비율",
        markers=True
    )
    st.plotly_chart(line, use_container_width=True)

    st.subheader("🔎 간단 분석")
    value = last["경상수지비율"]
    if value > 3:
        st.success("높은 흑자 국가입니다. 수출 경쟁력과 해외 소득이 주요 요인일 가능성이 있습니다.")
    elif value < -3:
        st.error("적자 국가입니다. 수입 규모, 소비 구조, 해외 투자 등이 영향을 줄 수 있습니다.")
    else:
        st.info("경상수지가 비교적 균형 상태입니다.")
