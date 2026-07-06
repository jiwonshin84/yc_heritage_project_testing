import os
import streamlit as st
import pandas as pd

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

import plotly.express as px

st.set_page_config(
    page_title="영천시 문화재 AI 군집분석",
    page_icon="🏛",
    layout="wide"
)

# ---------------- CSS ---------------- #

st.markdown("""
<style>

.stApp{
    background:linear-gradient(135deg,#eef4ff,#ffffff);
}

.block-container{
    padding-top:2rem;
    max-width:1450px;
}

[data-testid="stMetric"]{
    background:white;
    border-radius:18px;
    padding:18px;
    box-shadow:0px 6px 18px rgba(0,0,0,.08);
    border:1px solid #E8E8E8;
}

div[data-testid="stDataFrame"]{
    border-radius:15px;
    overflow:hidden;
}

h1{
    text-align:center;
    color:#123B6D;
}

h2,h3{
    color:#1D4E89;
}

</style>
""",unsafe_allow_html=True)

# ---------------- 데이터 불러오기 ---------------- #

BASE_DIR=os.path.dirname(os.path.dirname(__file__))

DATA_PATH=os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df=pd.read_csv(
    DATA_PATH,
    encoding="utf-8-sig"
)

features=[
    "문화재연령",
    "국가유산종목",
    "시대그룹",
    "재질",
    "노출형태"
]

data=df[features].copy()

for col in [
    "국가유산종목",
    "시대그룹",
    "재질",
    "노출형태"
]:
    le=LabelEncoder()
    data[col]=le.fit_transform(
        data[col].astype(str)
    )

scaler=StandardScaler()

X=scaler.fit_transform(data)

kmeans=KMeans(
    n_clusters=4,
    random_state=42,
    n_init=10
)

df["Cluster"]=kmeans.fit_predict(X)

cluster_name={
    0:"A그룹",
    1:"B그룹",
    2:"C그룹",
    3:"D그룹"
}

df["군집"]=df["Cluster"].map(cluster_name)

# ---------------- 제목 ---------------- #

st.markdown("""
<h1>
🏛 영천시 문화재 AI 군집분석 시스템
</h1>

<p style="text-align:center;
font-size:20px;
color:gray;">
K-Means Clustering 기반 문화재 특성 분석
</p>
""",unsafe_allow_html=True)

st.divider()

# ---------------- KPI ---------------- #

cluster_count=df["군집"].value_counts().sort_index()

c1,c2,c3,c4=st.columns(4)

with c1:

    st.metric(
        "🏛 문화재 수",
        len(df)
    )

with c2:

    st.metric(
        "📅 평균 연령",
        f"{int(df['문화재연령'].mean())}년"
    )

with c3:

    st.metric(
        "🧠 군집 수",
        4
    )

with c4:

    st.metric(
        "⭐ 가장 많은 군집",
        cluster_count.idxmax()
    )

st.divider()

# ---------------- 군집 설명 ---------------- #

st.info("""

### 🔵 A그룹
가치점수와 시대점수가 모두 높은 문화재

### 🟢 B그룹
가치와 시대성이 모두 낮은 문화재

### 🟠 C그룹
가치는 높고 시대는 비교적 최근인 문화재

### 🔴 D그룹
역사성은 있으나 가치점수가 비교적 낮은 문화재

""")

st.divider()

# ---------------- 검색 ---------------- #

keyword=st.text_input(
    "🔍 문화재 검색"
)

show=df.copy()

if keyword:

    show=df[
        df["문화재명(국문)"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

select=st.selectbox(
    "군집 선택",
    ["전체","A그룹","B그룹","C그룹","D그룹"]
)

if select!="전체":

    show=show[
        show["군집"]==select
    ]
# =====================================================
# 📊 분석 그래프
# =====================================================

st.header("📊 군집 분석 결과")

left, right = st.columns(2)

# ---------------- 군집별 문화재 개수 ---------------- #

with left:

    cluster_count = (
        show["군집"]
        .value_counts()
        .sort_index()
        .reset_index()
    )

    cluster_count.columns = ["군집", "개수"]

    fig = px.bar(
        cluster_count,
        x="군집",
        y="개수",
        color="군집",
        text="개수",
        title="군집별 문화재 개수",
        color_discrete_map={
            "A그룹":"#1f77b4",
            "B그룹":"#2ca02c",
            "C그룹":"#ff9800",
            "D그룹":"#e53935"
        }
    )

    fig.update_layout(
        height=430,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ---------------- 평균 문화재 연령 ---------------- #

with right:

    cluster_age = (
        show.groupby("군집")["문화재연령"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        cluster_age,
        x="군집",
        y="문화재연령",
        color="군집",
        text_auto=".1f",
        title="군집별 평균 문화재 연령",
        color_discrete_map={
            "A그룹":"#1f77b4",
            "B그룹":"#2ca02c",
            "C그룹":"#ff9800",
            "D그룹":"#e53935"
        }
    )

    fig.update_layout(
        height=430,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()

# =====================================================
# 🪨 재질 / 노출형태
# =====================================================

left, right = st.columns(2)

# ---------------- 재질 ---------------- #

with left:

    material = pd.crosstab(
        show["군집"],
        show["재질"]
    )

    fig = px.bar(
        material,
        title="군집별 재질 분포",
        barmode="group"
    )

    fig.update_layout(
        height=450,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ---------------- 노출 형태 ---------------- #

with right:

    exposure = pd.crosstab(
        show["군집"],
        show["노출형태"]
    )

    fig = px.bar(
        exposure,
        title="군집별 노출 형태",
        barmode="group"
    )

    fig.update_layout(
        height=450,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()

# =====================================================
# 📌 군집별 특징
# =====================================================

st.header("📌 군집별 특징")

cols = st.columns(4)

groups = ["A그룹","B그룹","C그룹","D그룹"]

for i, group in enumerate(groups):

    temp = show[
        show["군집"] == group
    ]

    with cols[i]:

        st.metric(
            label=group,
            value=f"{len(temp)}개"
        )

        if len(temp) > 0:

            st.write(
                f"📅 평균 연령 : **{round(temp['문화재연령'].mean(),1)}년**"
            )

            st.write(
                f"🪨 대표 재질 : **{temp['재질'].mode()[0]}**"
            )

            st.write(
                f"🏞 대표 노출 형태 : **{temp['노출형태'].mode()[0]}**"
            )

        else:

            st.write("데이터 없음")
# =====================================================
# 🗺️ 문화재 위치 지도
# =====================================================

st.header("🗺️ 문화재 위치")

m = folium.Map(
    location=[
        show["위도"].mean(),
        show["경도"].mean()
    ],
    zoom_start=11,
    tiles="CartoDB positron"
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
    <div style="width:220px">
        <h4>{row['문화재명(국문)']}</h4>

        <hr>

        <b>군집</b> :
        {row['군집']}<br>

        <b>문화재 연령</b> :
        {int(row['문화재연령'])}년<br>

        <b>재질</b> :
        {row['재질']}<br>

        <b>노출 형태</b> :
        {row['노출형태']}
    </div>
    """

    folium.Marker(
        location=[
            row["위도"],
            row["경도"]
        ],
        popup=popup,
        tooltip=row["문화재명(국문)"],
        icon=folium.Icon(
            color=color_dict[row["군집"]],
            icon="info-sign"
        )
    ).add_to(marker_cluster)

st_folium(
    m,
    width=None,
    height=650,
    use_container_width=True
)

st.divider()

# =====================================================
# 📋 문화재 목록
# =====================================================

st.header("📋 문화재 목록")

table = show[
    [
        "문화재명(국문)",
        "군집",
        "문화재연령",
        "국가유산종목",
        "시대그룹",
        "재질",
        "노출형태"
    ]
].copy()

table = table.sort_values(
    by=["군집","문화재연령"],
    ascending=[True,False]
)

st.dataframe(
    table,
    use_container_width=True,
    height=450
)

st.divider()

# =====================================================
# 📈 AI 분석 결과
# =====================================================

st.header("📈 AI 분석 결과")

largest_cluster = cluster_count.idxmax()

avg_age = int(show["문화재연령"].mean())

st.success(f"""
### 분석 요약

• 총 **{len(show)}개**의 문화재를 분석했습니다.

• K-Means 알고리즘을 이용하여 **4개의 군집**으로 분류했습니다.

• 가장 많은 문화재가 속한 군집은 **{largest_cluster}**입니다.

• 전체 평균 문화재 연령은 **{avg_age}년**입니다.

• 군집 분석을 통해 문화재의 특성과 분포를 시각적으로 확인할 수 있으며,
향후 문화재 보존 우선순위 설정 및 관리 정책 수립에 활용할 수 있습니다.
""")

st.divider()

# =====================================================
# Footer
# =====================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:gray;
        font-size:14px;
        padding:20px;
    ">
        영천시 문화재 AI 군집분석 시스템<br>
        K-Means Clustering · Streamlit Dashboard
    </div>
    """,
    unsafe_allow_html=True
)
