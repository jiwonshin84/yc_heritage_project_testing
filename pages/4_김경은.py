import os
import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
import folium
from streamlit_folium import st_folium
st.set_page_config(page_title="문화재 군집분석", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

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

st.title("🏛 문화재 군집분석")

st.markdown("""
### 📌 군집 기준 

문화재의 **가치점수와 시대점수**를 바탕으로 비슷한 특징을 가진 문화재끼리 4개의 그룹으로 분류

🔵 **A그룹**
- 가치점수와 시대점수가 모두 높은 문화재
- 역사적 가치가 크고 보존 가치가 높은 문화재가 많이 포함됩니다.

🟢 **B그룹**
- 가치점수와 시대점수가 모두 낮은 문화재
- 비교적 역사성과 가치가 낮은 문화재가 포함됩니다.

🟡 **C그룹**
- 가치점수는 높지만 시대점수는 중간 수준인 문화재
- 보존 가치는 높지만 상대적으로 시대가 오래되지 않은 문화재가 포함됩니다.

🔴 **D그룹**
- 가치점수는 낮지만 시대점수가 중간 수준인 문화재
- 역사성은 어느 정도 있지만 가치점수는 비교적 낮은 문화재가 포함됩니다.
""")
st.subheader("📊 군집별 문화재 개수")

cluster_count = df["군집"].value_counts().sort_index()

st.bar_chart(cluster_count)


st.subheader("📅 군집별 평균 문화재 연령")

cluster_age = df.groupby("군집")["문화재연령"].mean()

st.bar_chart(cluster_age)


st.subheader("🪨 군집별 재질")

material = pd.crosstab(df["군집"], df["재질"])

st.dataframe(material, use_container_width=True)

st.bar_chart(material)


st.subheader("🏞 군집별 노출 형태")

exposure = pd.crosstab(df["군집"], df["노출형태"])

st.dataframe(exposure, use_container_width=True)

st.bar_chart(exposure)


st.subheader("📌 군집별 특징")

groups = sorted(df["군집"].unique())

col1, col2 = st.columns(2)

for i, group in enumerate(groups):

    temp = df[df["군집"] == group]

    with col1 if i % 2 == 0 else col2:

        st.metric(
            label=f"{group}",
            value=f"{len(temp)}개"
        )

        st.write(f"📅 평균 연령 : **{round(temp['문화재연령'].mean(),1)}년**")

        st.write(f"🪨 대표 재질 : **{temp['재질'].mode()[0]}**")

        st.write(f"🏞 대표 노출 형태 : **{temp['노출형태'].mode()[0]}**")

        st.divider()

st.subheader("🗺️ 문화재 위치")

m = folium.Map(
    location=[df["위도"].mean(), df["경도"].mean()],
    zoom_start=11
)

color_dict = {
    "A그룹": "blue",
    "B그룹": "green",
    "C그룹": "orange",
    "D그룹": "red"
}

for _, row in df.iterrows():

    folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=f"""
        <b>{row['문화재명(국문)']}</b><br>
        군집 : {row['군집']}<br>
        재질 : {row['재질']}<br>
        노출 형태 : {row['노출형태']}
        """,
        icon=folium.Icon(
            color=color_dict[row["군집"]],
            icon="info-sign"
        )
    ).add_to(m)

st_folium(m, width=900, height=600)
st.subheader("📋 전체 문화재 목록")

st.dataframe(
    df[
        [
            "문화재명(국문)",
            "군집",
            "문화재연령",
            "재질",
            "노출형태"
        ]
    ],
    use_container_width=True
)
