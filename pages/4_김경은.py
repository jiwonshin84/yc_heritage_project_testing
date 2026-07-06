import os
import streamlit as st
import pandas as pd
import numpy as np

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# =====================================================
# ⚙️ 설정
# =====================================================

st.set_page_config(
    page_title="문화재 AI 심층 분석",
    page_icon="🏛",
    layout="wide"
)

# =====================================================
# 🌑 DARK THEME
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    color: white;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
}

h1, h2, h3 {
    color: white !important;
}

[data-testid="stMetric"] {
    background-color: #1c1f26;
    border-radius: 15px;
    padding: 18px;
    border: 1px solid #2a2f3a;
}

[data-testid="stDataFrame"] {
    background-color: #1c1f26;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# 📂 데이터
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

# =====================================================
# 🤖 KMEANS
# =====================================================

features = [
    "문화재연령",
    "국가유산종목",
    "시대그룹",
    "재질",
    "노출형태"
]

data = df[features].copy()

for col in ["국가유산종목","시대그룹","재질","노출형태"]:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col].astype(str))

scaler = StandardScaler()
X = scaler.fit_transform(data)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X)

labels = {0:"A그룹",1:"B그룹",2:"C그룹",3:"D그룹"}
df["군집"] = df["Cluster"].map(labels)

# =====================================================
# 🏛 TITLE
# =====================================================

st.title("🏛 문화재 AI 심층 분석 시스템")

st.caption("군집 + 공간 + 통계 기반 문화재 구조 분석")

st.divider()

# =====================================================
# 📊 KPI
# =====================================================

c1,c2,c3,c4 = st.columns(4)

c1.metric("전체 문화재", len(df))
c2.metric("평균 연령", f"{int(df['문화재연령'].mean())}년")
c3.metric("군집 수", 4)
c4.metric("최대 군집", df["군집"].value_counts().idxmax())

st.divider()

# =====================================================
# 🔍 검색 + 필터
# =====================================================

st.subheader("🔍 문화재 탐색 + 분석 필터")

keyword = st.text_input("문화재 검색 (예: 석탑, 불상, 사찰)")

cluster_filter = st.selectbox(
    "군집 선택",
    ["전체","A그룹","B그룹","C그룹","D그룹"]
)

show = df.copy()

if keyword:
    show = show[show["문화재명(국문)"].str.contains(keyword, na=False)]

if cluster_filter != "전체":
    show = show[show["군집"] == cluster_filter]

st.divider()

# =====================================================
# 📊 군집 분석 (심화)
# =====================================================

st.header("📊 군집 구조 분석")

col1, col2 = st.columns(2)

with col1:

    cluster_count = show["군집"].value_counts().sort_index()

    fig = px.bar(
        cluster_count,
        x=cluster_count.index,
        y=cluster_count.values,
        text=cluster_count.values,
        title="군집 분포"
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    st.info("""
📌 의미

군집 간 데이터 분포 불균형을 확인하는 그래프

→ 특정 군집 집중 여부 확인  
→ 문화재 유형 편향 분석 가능
""")

with col2:

    age = show.groupby("군집")["문화재연령"].mean().reset_index()

    fig = px.bar(
        age,
        x="군집",
        y="문화재연령",
        text_auto=".1f",
        title="군집별 평균 연령"
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    st.info("""
📌 의미

군집별 역사적 깊이 비교

→ 오래된 문화재가 어느 군집에 집중되는지 분석  
→ 역사 가치 구조 파악
""")

st.divider()

# =====================================================
# 🧠 심화 해석 (핵심)
# =====================================================

st.header("🧠 AI 군집 해석")

for g in ["A그룹","B그룹","C그룹","D그룹"]:

    temp = show[show["군집"] == g]

    if len(temp) == 0:
        continue

    st.markdown(f"### {g}")

    st.write(f"📊 개수: {len(temp)}개")
    st.write(f"📅 평균 연령: {round(temp['문화재연령'].mean(),1)}년")
    st.write(f"🪨 대표 재질: {temp['재질'].mode()[0]}")
    st.write(f"🏞 대표 노출: {temp['노출형태'].mode()[0]}")

    st.info(f"""
🔎 해석

{g}는 위 특성으로 볼 때
문화재의 성격이 동일한 유형끼리 군집화된 결과이다.

→ KMeans가 단순 위치가 아니라
→ 구조적 유사성을 기반으로 분류했음을 의미
""")

st.divider()

# =====================================================
# 🗺 공간 분석 (핵심 업그레이드)
# =====================================================

st.header("🗺 공간 분포 분석 (핵심)")

m = folium.Map(
    location=[show["위도"].mean(), show["경도"].mean()],
    zoom_start=11,
    tiles="CartoDB dark_matter"
)

cluster_map = MarkerCluster().add_to(m)

color = {
    "A그룹":"blue",
    "B그룹":"green",
    "C그룹":"orange",
    "D그룹":"red"
}

for _, r in show.iterrows():

    folium.Marker(
        location=[r["위도"], r["경도"]],
        tooltip=r["문화재명(국문)"],
        popup=f"""
        <b>{r['문화재명(국문)']}</b><br>
        군집: {r['군집']}<br>
        연령: {r['문화재연령']}년
        """,
        icon=folium.Icon(color=color[r["군집"]])
    ).add_to(cluster_map)

st_folium(m, use_container_width=True, height=600)

st.info("""
📌 공간 해석

이 지도는 단순 위치 표시가 아니라

→ 군집별 공간적 분포 구조 분석

핵심 질문:
- 특정 군집이 특정 지역에 집중되어 있는가?
- 고가치 문화재는 어디에 분포하는가?
- 관리 취약 지역은 어디인가?
""")

st.success("""
📌 최종 결론

문화재 데이터는 단순한 개별 정보가 아니라
공간 + 속성 + 군집 구조로 해석해야 한다.

→ 본 분석은 문화재 관리 전략 수립에 활용 가능하다.
""")

# =====================================================
# 📋 데이터
# =====================================================

st.header("📋 원본 데이터")

st.dataframe(
    show[
        ["문화재명(국문)","군집","문화재연령","재질","노출형태"]
    ],
    use_container_width=True
)
