import streamlit as st

st.title("🌦 김보원")
import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# 페이지 설정
# =====================================================

st.set_page_config(
    page_title="영천 지역 환경데이터 분석",
    page_icon="🌿",
    layout="wide"
)

# =====================================================
# CSV 파일명
# =====================================================

CSV_FILE = "OBS_ASOS_MNH_20260629185804 환경데이터"   # ← 실제 파일명으로 수정

# =====================================================
# 데이터 불러오기
# =====================================================

@st.cache_data
def load_data():

    df = pd.read_csv(CSV_FILE, encoding="cp949")

    # 날짜 변환
    df["일시"] = pd.to_datetime(df["일시"])

    # 연도 / 월 생성
    df["연도"] = df["일시"].dt.year
    df["월"] = df["일시"].dt.month

    return df

df = load_data()

# =====================================================
# 제목
# =====================================================

st.title("🌿 영천 지역 환경데이터 분석")

st.markdown("""
기상자료개방포털 데이터를 활용하여
영천 지역의 기온, 습도, 강수량을 분석하고
문화재 훼손에 영향을 줄 수 있는 환경요인을 확인합니다.
""")

# =====================================================
# 사이드바
# =====================================================

year = st.sidebar.selectbox(
    "연도 선택",
    sorted(df["연도"].unique())
)

data = df[df["연도"] == year]

# =====================================================
# 환경 통계
# =====================================================

st.subheader("📊 환경 통계")

c1, c2, c3 = st.columns(3)

c1.metric(
    "평균기온",
    f"{data['평균기온(°C)'].mean():.1f}°C"
)

c2.metric(
    "평균습도",
    f"{data['평균상대습도(%)'].mean():.1f}%"
)

c3.metric(
    "총 강수량",
    f"{data['월합강수량(00~24h만)(mm)'].sum():.1f} mm"
)

# =====================================================
# 평균기온
# =====================================================

st.subheader("🌡 월별 평균기온")

fig = px.line(
    data,
    x="월",
    y="평균기온(°C)",
    markers=True
)

fig.update_layout(xaxis_title="월", yaxis_title="기온(°C)")

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 평균습도
# =====================================================

st.subheader("💧 월별 평균 상대습도")

fig = px.line(
    data,
    x="월",
    y="평균상대습도(%)",
    markers=True
)

fig.update_layout(xaxis_title="월", yaxis_title="습도(%)")

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 강수량
# =====================================================

st.subheader("☔ 월별 강수량")

fig = px.bar(
    data,
    x="월",
    y="월합강수량(00~24h만)(mm)"
)

fig.update_layout(xaxis_title="월", yaxis_title="강수량(mm)")

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 최고기온 / 최저기온
# =====================================================

st.subheader("🌡 최고기온 · 최저기온")

temp_df = data[[
    "월",
    "평균최고기온(°C)",
    "평균최저기온(°C)"
]]

temp_df = temp_df.melt(
    id_vars="월",
    var_name="구분",
    value_name="기온"
)

fig = px.line(
    temp_df,
    x="월",
    y="기온",
    color="구분",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 문화재 훼손 위험지수
# =====================================================

st.subheader("⚠ 문화재 훼손 위험지수")

risk = (
    data["평균상대습도(%)"] * 0.4 +
    data["월합강수량(00~24h만)(mm)"] * 0.3 +
    data["평균기온(°C)"] * 0.2 +
    data["일최다강수량(mm)"] * 0.1
)

risk = (risk - risk.min()) / (risk.max() - risk.min()) * 100

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

fig.update_layout(
    yaxis_range=[0,100]
)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 위험등급
# =====================================================

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
