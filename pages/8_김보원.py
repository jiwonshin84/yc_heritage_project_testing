import streamlit as st

st.title("🌦 김보원")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =====================================
# 페이지 설정
# =====================================

st.set_page_config(
    page_title="영천 환경데이터 분석",
    layout="wide"
)

# =====================================
# 데이터 불러오기
# =====================================

@st.cache_data
def load_data():
    df = pd.read_csv("data/environment/환경데이터.csv", encoding="cp949")

    # 날짜 변환
    df["일시"] = pd.to_datetime(df["일시"])

    return df

df = load_data()

# =====================================
# 제목
# =====================================

st.title("🌿 영천 지역 환경데이터 분석")

st.markdown("""
문화재 훼손에 영향을 줄 수 있는
기온, 습도, 강수량 데이터를 분석합니다.
""")

# =====================================
# 연도 선택
# =====================================

year = st.sidebar.selectbox(
    "연도 선택",
    sorted(df["일시"].dt.year.unique())
)

data = df[df["일시"].dt.year == year]

# =====================================
# 데이터 보기
# =====================================

st.subheader("환경데이터")

st.dataframe(data)

# =====================================
# 평균기온
# =====================================

st.subheader("평균기온 변화")

fig, ax = plt.subplots(figsize=(10,4))

ax.plot(
    data["일시"],
    data["평균기온(°C)"],
    marker="o"
)

ax.set_xlabel("월")
ax.set_ylabel("℃")

st.pyplot(fig)

# =====================================
# 평균습도
# =====================================

st.subheader("평균 상대습도")

fig, ax = plt.subplots(figsize=(10,4))

ax.plot(
    data["일시"],
    data["평균상대습도(%)"],
    color="green",
    marker="o"
)

ax.set_xlabel("월")
ax.set_ylabel("%")

st.pyplot(fig)

# =====================================
# 강수량
# =====================================

st.subheader("월별 강수량")

fig, ax = plt.subplots(figsize=(10,4))

ax.bar(
    data["일시"],
    data["월합강수량(00~24h만)(mm)"]
)

ax.set_ylabel("mm")

st.pyplot(fig)

# =====================================
# 통계
# =====================================

st.subheader("환경 통계")

col1, col2, col3 = st.columns(3)

col1.metric(
    "평균기온",
    f"{data['평균기온(°C)'].mean():.1f} ℃"
)

col2.metric(
    "평균습도",
    f"{data['평균상대습도(%)'].mean():.1f} %"
)

col3.metric(
    "총 강수량",
    f"{data['월합강수량(00~24h만)(mm)'].sum():.1f} mm"
)
