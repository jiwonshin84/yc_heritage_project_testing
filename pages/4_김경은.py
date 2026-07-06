import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(page_title="문화재 군집분석", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

st.title("🗺️ 문화재 군집분석")
st.write("문화재의 연령, 재질, 노출 형태를 기준으로 비슷한 특징을 가진 문화재를 4개의 그룹으로 분류했습니다.")

# -----------------------------
# 전처리
# -----------------------------

data = df.copy()

label1 = LabelEncoder()
label2 = LabelEncoder()

data["재질"] = label1.fit_transform(data["재질"].astype(str))
data["노출형태"] = label2.fit_transform(data["노출형태"].astype(str))

X = data[["문화재연령", "재질", "노출형태"]]

scaler = StandardScaler()
X = scaler.fit_transform(X)

kmeans = KMeans(
    n_clusters=4,
    random_state=42,
    n_init=10
)

data["cluster"] = kmeans.fit_predict(X)

cluster_name = {
    0: "A",
    1: "B",
    2: "C",
    3: "D"
}

data["군집"] = data["cluster"].map(cluster_name)

# -----------------------------
# 군집 카드
# -----------------------------

st.subheader("📌 군집별 특징")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.info(f"""
### 🟦 A그룹

문화재 수

## {len(data[data["군집"]=="A"])}개
""")

with c2:
    st.success(f"""
### 🟩 B그룹

문화재 수

## {len(data[data["군집"]=="B"])}개
""")

with c3:
    st.warning(f"""
### 🟨 C그룹

문화재 수

## {len(data[data["군집"]=="C"])}개
""")

with c4:
    st.error(f"""
### 🟥 D그룹

문화재 수

## {len(data[data["군집"]=="D"])}개
""")

st.divider()

# -----------------------------
# 군집 선택
# -----------------------------

selected_group = st.selectbox(
    "군집 선택",
    ["전체", "A", "B", "C", "D"]
)

if selected_group == "전체":
    view = data.copy()
else:
    view = data[data["군집"] == selected_group]

# -----------------------------
# 군집 개수
# -----------------------------

st.subheader("📊 군집별 문화재 개수")

count = (
    data["군집"]
    .value_counts()
    .sort_index()
    .reset_index()
)

count.columns = ["군집", "개수"]

fig = px.bar(
    count,
    x="군집",
    y="개수",
    color="군집",
    text="개수"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 평균 연령
# -----------------------------

st.subheader("📅 군집별 평균 문화재 연령")

age = (
    data.groupby("군집")["문화재연령"]
    .mean()
    .reset_index()
)

fig = px.bar(
    age,
    x="군집",
    y="문화재연령",
    color="군집",
    text_auto=".0f"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 재질
# -----------------------------

st.subheader("🪨 군집별 재질")

material = (
    view.groupby(["군집","재질"])
    .size()
    .reset_index(name="개수")
)

material["재질"] = label1.inverse_transform(material["재질"])

fig = px.bar(
    material,
    x="재질",
    y="개수",
    color="군집",
    barmode="group"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 노출 형태
# -----------------------------

st.subheader("🏛 군집별 노출 형태")

expose = (
    view.groupby(["군집","노출형태"])
    .size()
    .reset_index(name="개수")
)

expose["노출형태"] = label2.inverse_transform(expose["노출형태"])

fig = px.bar(
    expose,
    x="노출형태",
    y="개수",
    color="군집",
    barmode="group"
)

st.plotly_chart(fig, use_container_width=True)

import folium
from streamlit_folium import st_folium

st.divider()

st.subheader("🗺️ 군집별 문화재 위치")

# 군집별 핀 색상
color_map = {
    "A": "blue",
    "B": "green",
    "C": "orange",
    "D": "red"
}

# 지도 중심
center_lat = data["위도"].mean()
center_lon = data["경도"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11
)

# 군집 선택에 따라 지도 표시
if selected_group == "전체":
    map_data = data
else:
    map_data = data[data["군집"] == selected_group]

# 핀 생성
for _, row in map_data.iterrows():

    popup = f"""
    <b>{row['문화재명(국문)']}</b><br>

    <hr>

    <b>군집</b> : {row['군집']}<br>

    <b>국가유산종목</b> : {row['국가유산종목']}<br>

    <b>시대</b> : {row['시대그룹']}<br>

    <b>문화재 연령</b> : {int(row['문화재연령'])}년<br>

    <b>재질</b> : {label1.inverse_transform([row['재질']])[0]}<br>

    <b>노출 형태</b> : {label2.inverse_transform([row['노출형태']])[0]}
    """

    folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=popup,
        tooltip=row["문화재명(국문)"],
        icon=folium.Icon(
            color=color_map[row["군집"]],
            icon="glyphicon-map-marker"
        )
    ).add_to(m)

st_folium(
    m,
    width=None,
    height=600,
    use_container_width=True
)

st.caption("📍 핀을 클릭하면 문화재 정보를 확인할 수 있습니다.")

st.divider()

st.subheader("📋 군집별 문화재 목록")

show = map_data[
    [
        "문화재명(국문)",
        "군집",
        "국가유산종목",
        "시대그룹",
        "문화재연령",
        "재질",
        "노출형태"
    ]
].copy()

show["재질"] = label1.inverse_transform(show["재질"])
show["노출형태"] = label2.inverse_transform(show["노출형태"])

show = show.rename(
    columns={
        "문화재명(국문)": "문화재명",
        "국가유산종목": "종목",
        "시대그룹": "시대",
        "문화재연령": "연령(년)"
    }
)

st.dataframe(
    show,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.success("✅ 군집분석이 완료되었습니다.")

st.markdown(
"""
### 📖 군집분석 결과 해석

- 🟦 **A그룹** : 비슷한 특징을 가진 문화재 집합입니다.
- 🟩 **B그룹** : 비슷한 특징을 가진 문화재 집합입니다.
- 🟨 **C그룹** : 비슷한 특징을 가진 문화재 집합입니다.
- 🟥 **D그룹** : 비슷한 특징을 가진 문화재 집합입니다.

지도에서는 같은 군집의 문화재를 같은 색상의 핀으로 표시하여
공간적으로 어떻게 분포하는지 쉽게 확인할 수 있습니다.
"""
)
