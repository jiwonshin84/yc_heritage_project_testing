import os
import streamlit as st
import pandas as pd

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# =====================================================
# ⚙️ 기본 설정
# =====================================================

st.set_page_config(
    page_title="문화재 AI 분석 시스템",
    page_icon="🏛",
    layout="wide"
)

# =====================================================
# 🌑 DARK UI
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

input, textarea {
    background-color: #1c1f26 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# 📂 데이터 로드
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

for col in ["국가유산종목", "시대그룹", "재질", "노출형태"]:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col].astype(str))

scaler = StandardScaler()
X = scaler.fit_transform(data)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X)

labels = {
    0: "A그룹",
    1: "B그룹",
    2: "C그룹",
    3: "D그룹"
}

df["군집"] = df["Cluster"].map(labels)

# =====================================================
# 🏛 TITLE
# =====================================================

st.title("🏛 문화재 AI 심층 분석 시스템")
st.caption("검색 + 군집 + 공간 + 구조 분석")

st.divider()

# =====================================================
# 📊 KPI
# =====================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("전체 문화재", len(df))
c2.metric("평균 연령", f"{int(df['문화재연령'].mean())}년")
c3.metric("군집 수", 4)
c4.metric("최다 군집", df["군집"].value_counts().idxmax())

st.divider()

# =====================================================
# 🔍 검색 (자동완성 포함)
# =====================================================

st.subheader("🔍 문화재 검색")

keyword = st.text_input("", placeholder="예: 은, 불상, 사찰, 석탑...")

show = df.copy()

# ---------------- 연관검색 ---------------- #
if keyword:

    suggestions = df[
        df["문화재명(국문)"].str.contains(keyword, na=False)
    ]["문화재명(국문)"].head(5).tolist()

    if suggestions:
        st.markdown("### 💡 연관 검색 결과")

        for s in suggestions:
            if st.button(f"📌 {s}"):
                keyword = s

# ---------------- 검색 필터 ---------------- #
if keyword:
    show = df[df["문화재명(국문)"].str.contains(keyword, na=False)]

# =====================================================
# 🧠 검색 결과 AI 분석
# =====================================================

if keyword and len(show) > 0:

    item = show.iloc[0]

    st.markdown("## 🧠 AI 문화재 특징 분석")

    st.info(f"""
### 📌 {item['문화재명(국문)']}

- 🏛 군집: {item['군집']}
- 📅 연령: {item['문화재연령']}년
- 🪨 재질: {item['재질']}
- 🏞 노출 형태: {item['노출형태']}

---

### 🔎 AI 해석

이 문화재는 **{item['군집']}** 군집에 속하며,
동일 군집 내 문화재들과 구조적으로 유사한 특성을 가집니다.

→ KMeans 기반으로 유형이 자동 분류된 결과  
→ 문화재의 시대적/물리적 특성이 반영됨
""")

st.divider()

# =====================================================
# 🪨 군집별 재질 분석 (핵심 그래프)
# =====================================================

st.header("🪨 군집별 재질 구조 분석")

material = pd.crosstab(
    show["군집"],
    show["재질"]
)

fig = px.bar(
    material,
    title="군집별 재질 분포",
    barmode="group"
)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# =====================================================
# 🧠 군집별 특징 요약
# =====================================================

st.header("🧠 군집 구조 해석")

groups = ["A그룹","B그룹","C그룹","D그룹"]

for g in groups:

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

{g}는 유사한 속성을 가진 문화재들이 모인 군집으로,
KMeans 알고리즘이 구조적 유사성을 기반으로 분류한 결과이다.
""")

st.divider()

# =====================================================
# 🗺 지도 분석
# =====================================================

st.header("🗺 문화재 공간 분포 분석")

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
        popup=f"{r['문화재명(국문)']}<br>{r['군집']}",
        icon=folium.Icon(color=color[r["군집"]])
    ).add_to(cluster_map)

st_folium(m, use_container_width=True, height=600)

st.divider()

# =====================================================
# 📋 데이터 테이블
# =====================================================

st.header("📋 문화재 데이터")

st.dataframe(
    show[
        ["문화재명(국문)","군집","문화재연령","재질","노출형태"]
    ],
    use_container_width=True
)

st.divider()

# =====================================================
# 📌 최종 결론
# =====================================================

st.header("📌 분석 결론")

st.success(f"""
✔ 총 {len(show)}개의 문화재 분석

✔ KMeans 기반 4개 군집 구조 확인

✔ 검색 기반 문화재 개별 특징 분석 가능

✔ 군집별 재질 구조 차이 존재

✔ 공간 분포까지 포함한 다차원 분석 시스템

→ 문화재는 단순 객체가 아니라
→ 공간 + 속성 + 군집 구조로 해석해야 함
""")
