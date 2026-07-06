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
    page_title="영천시 문화재 AI 분석",
    page_icon="🏛",
    layout="wide"
)

# =====================================================
# 🌑 DARK UI STYLE
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    color: #ffffff;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
}

/* 제목 */
h1, h2, h3 {
    color: white !important;
}

/* metric 카드 */
[data-testid="stMetric"] {
    background-color: #1c1f26;
    border: 1px solid #2a2f3a;
    padding: 18px;
    border-radius: 15px;
}

/* dataframe */
[data-testid="stDataFrame"] {
    background-color: #1c1f26;
    border-radius: 12px;
    overflow: hidden;
}

/* input */
input {
    background-color: #1c1f26 !important;
    color: white !important;
}

/* selectbox */
div[data-baseweb="select"] > div {
    background-color: #1c1f26;
    color: white;
}

hr {
    border-color: #2a2f3a;
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
# 🤖 KMEANS CLUSTERING
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

kmeans = KMeans(
    n_clusters=4,
    random_state=42,
    n_init=10
)

df["Cluster"] = kmeans.fit_predict(X)

cluster_name = {
    0: "A그룹",
    1: "B그룹",
    2: "C그룹",
    3: "D그룹"
}

df["군집"] = df["Cluster"].map(cluster_name)

cluster_count = df["군집"].value_counts().sort_index()

# =====================================================
# 🏛 TITLE
# =====================================================

st.markdown("""
<h1 style='text-align:center;font-size:48px;'>
🏛 영천시 문화재 AI 군집분석 시스템
</h1>

<p style='text-align:center;color:gray;font-size:18px;'>
K-Means 기반 문화재 데이터 분석 Dashboard
</p>
""", unsafe_allow_html=True)

st.divider()

# =====================================================
# 📊 KPI CARDS
# =====================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("🏛 총 문화재", len(df))
c2.metric("📅 평균 연령", f"{int(df['문화재연령'].mean())}년")
c3.metric("🧠 군집 수", 4)
c4.metric("⭐ 최다 군집", cluster_count.idxmax())

st.divider()

# =====================================================
# 🔍 FILTER
# =====================================================

keyword = st.text_input("🔍 문화재 검색")

show = df.copy()

if keyword:
    show = show[
        show["문화재명(국문)"].str.contains(keyword, na=False)
    ]

select = st.selectbox(
    "군집 선택",
    ["전체", "A그룹", "B그룹", "C그룹", "D그룹"]
)

if select != "전체":
    show = show[show["군집"] == select]

st.divider()

# =====================================================
# 📊 GRAPHS (DARK PLOTLY)
# =====================================================

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        cluster_count,
        x=cluster_count.index,
        y=cluster_count.values,
        color=cluster_count.index,
        text=cluster_count.values,
        color_discrete_sequence=["#4ea8de","#52b788","#f4a261","#e63946"]
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font_color="white",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:

    avg_age = show.groupby("군집")["문화재연령"].mean().reset_index()

    fig = px.bar(
        avg_age,
        x="군집",
        y="문화재연령",
        color="군집",
        text_auto=".1f",
        color_discrete_sequence=["#4ea8de","#52b788","#f4a261","#e63946"]
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font_color="white",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

# =====================================================
# 🗺 MAP (DARK MODE)
# =====================================================

st.header("🗺 문화재 위치")

m = folium.Map(
    location=[show["위도"].mean(), show["경도"].mean()],
    zoom_start=11,
    tiles="CartoDB dark_matter"
)

marker_cluster = MarkerCluster().add_to(m)

color_dict = {
    "A그룹": "blue",
    "B그룹": "green",
    "C그룹": "orange",
    "D그룹": "red"
}

for _, row in show.iterrows():

    popup = f"""
    <b>{row['문화재명(국문)']}</b><br>
    군집: {row['군집']}<br>
    연령: {int(row['문화재연령'])}년<br>
    재질: {row['재질']}
    """

    folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=popup,
        icon=folium.Icon(color=color_dict[row["군집"]])
    ).add_to(marker_cluster)

st_folium(m, use_container_width=True, height=600)

st.divider()

# =====================================================
# 📋 TABLE
# =====================================================

st.header("📋 문화재 목록")

st.dataframe(
    show[
        [
            "문화재명(국문)",
            "군집",
            "문화재연령",
            "재질",
            "노출형태"
        ]
    ],
    use_container_width=True,
    height=450
)

st.divider()

# =====================================================
# 📈 SUMMARY
# =====================================================

st.header("📈 AI 분석 결과")

st.success(f"""
✔ 총 {len(show)}개의 문화재 분석

✔ 4개의 군집으로 자동 분류

✔ 가장 큰 군집: {cluster_count.idxmax()}

✔ 평균 연령: {int(show['문화재연령'].mean())}년

이 분석은 문화재의 특성을 기반으로 유사 그룹을 분류하여
보존 우선순위 및 정책 수립에 활용할 수 있습니다.
""")
