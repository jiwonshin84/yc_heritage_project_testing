import streamlit as st

st.title("🌦 김보원")
import streamlit as st
import pandas as pd
import plotly.express as px

# ===========================================
# 페이지 설정
# ===========================================

st.set_page_config(
    page_title="영천 환경데이터 분석",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================================
# 데이터 불러오기
# ===========================================

@st.cache_data
def load_data():
    df = pd.read_csv("data/environment/환경데이터.csv", encoding="cp949")

    # 날짜 변환
    df["일시"] = pd.to_datetime(df["일시"])

    # 연도, 월 생성
    df["연도"] = df["일시"].dt.year
    df["월"] = df["일시"].dt.month

    return df

df = load_data()

# ===========================================
# 제목
# ===========================================

st.title("🌿 영천 지역 환경데이터 분석")

st.markdown("""
기상자료개방포털에서 제공하는 데이터를 활용하여
영천 지역의 **기온**, **습도**, **강수량**을 분석하고
문화재 훼손에 영향을 줄 수 있는 환경요인을 확인합니다.
""")

# ===========================================
# 사이드바
# ===========================================

year = st.sidebar.selectbox(
    "연도 선택",
    sorted(df["연도"].unique())
)

data = df[df["연도"] == year]

# ===========================================
# 통계
# ===========================================

st.subheader("📊 환경 통계")

col1, col2, col3 = st.columns(3)

col1.metric(
    "평균기온",
    f"{data['평균기온(℃)'].mean():.1f}℃"
)

col2.metric(
    "평균습도",
    f"{data['평균상대습도(%)'].mean():.1f}%"
)

col3.metric(
    "총 강수량",
    f"{data['월합강수량(mm)'].sum():.1f} mm"
)

# ===========================================
# 평균기온
# ===========================================

st.subheader("🌡 평균기온 변화")

fig = px.line(
    data,
    x="월",
    y="평균기온(℃)",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ===========================================
# 평균습도
# ===========================================

st.subheader("💧 평균 상대습도")

fig = px.line(
    data,
    x="월",
    y="평균상대습도(%)",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ===========================================
# 강수량
# ===========================================

st.subheader("☔ 월별 강수량")

fig = px.bar(
    data,
    x="월",
    y="월합강수량(mm)"
)

st.plotly_chart(fig, use_container_width=True)

# ===========================================
# 최고/최저기온
# ===========================================

st.subheader("🌡 최고기온 / 최저기온")

fig = px.line(
    data,
    x="월",
    y=["최고기온(℃)", "최저기온(℃)"],
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ===========================================
# 문화재 훼손 위험지수
# ===========================================

st.subheader("⚠ 문화재 훼손 위험지수")

risk = (
    data["평균상대습도(%)"]*0.4
    + data["월합강수량(mm)"]*0.3
    + data["평균기온(℃)"]*0.2
    + data["일최다강수량(mm)"]*0.1
)

risk = (risk-risk.min())/(risk.max()-risk.min())*100

risk_df = pd.DataFrame({
    "월": data["월"],
    "위험지수": risk
})

fig = px.line(
    risk_df,
    x="월",
    y="위험지수",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ===========================================
# 위험등급
# ===========================================

def level(score):
    if score >= 80:
        return "매우 높음"
    elif score >= 60:
        return "높음"
    elif score >= 40:
        return "보통"
    else:
        return "낮음"

risk_df["위험등급"] = risk_df["위험지수"].apply(level)

st.subheader("📋 월별 위험등급")

st.dataframe(
    risk_df,
    use_container_width=True
)




