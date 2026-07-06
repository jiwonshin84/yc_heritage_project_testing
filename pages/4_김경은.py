import os
import streamlit as st
import pandas as pd
import plotly.express as px
import folium

from streamlit_folium import st_folium
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(
    page_title="문화재 군집분석",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

st.title("📊 문화재 군집분석")

st.markdown("""
### 📌 AI는 어떤 기준으로 군집을 나누었을까요?

AI는 **한 가지 기준이 아닌 여러 정보를 동시에 고려**하여
비슷한 특징을 가진 문화재를 자동으로 분류했습니다.

✅ 문화재 연령

✅ 재질

✅ 노출 형태

위 3가지 정보를 **K-Means 군집분석**으로 분석하여
총 **4개의 군집(A~D)** 으로 분류했습니다.
""")

data = df.copy()

material_encoder = LabelEncoder()
expose_encoder = LabelEncoder()

data["재질"] = material_encoder.fit_transform(
    data["재질"].astype(str)
)

data["노출형태"] = expose_encoder.fit_transform(
    data["노출형태"].astype(str)
)

feature = data[
    [
        "문화재연령",
        "재질",
        "노출형태"
    ]
]

scaler = StandardScaler()

feature = scaler.fit_transform(feature)

model = KMeans(
    n_clusters=4,
    random_state=42,
    n_init=10
)

data["cluster"] = model.fit_predict(feature)

cluster_name = {
    0: "A",
    1: "B",
    2: "C",
    3: "D"
}

data["군집"] = data["cluster"].map(cluster_name)

st.divider()

st.subheader("🃏 AI가 발견한 군집 특징")

cols = st.columns(4)

for i, group in enumerate(["A","B","C","D"]):

    temp = data[data["군집"] == group]

    avg_age = int(temp["문화재연령"].mean())

    top_material = (
        temp["재질"]
        .mode()[0]
    )

    top_expose = (
        temp["노출형태"]
        .mode()[0]
    )

    top_material = material_encoder.inverse_transform(
        [top_material]
    )[0]

    top_expose = expose_encoder.inverse_transform(
        [top_expose]
    )[0]

    count = len(temp)

    if avg_age >= 700:
        age_text = "오래된"

    elif avg_age >= 300:
        age_text = "중간 연령의"

    else:
        age_text = "비교적 최근의"

    explain = f"""
**{age_text} 문화재**가 많으며

대표 재질은 **{top_material}**,

주요 노출 형태는 **{top_expose}** 입니다.
"""

    with cols[i]:

        st.metric(
            f"{group} 군집",
            f"{count}개"
        )

        st.write(f"📅 평균 연령 : {avg_age}년")

        st.write(f"🪨 대표 재질 : {top_material}")

        st.write(f"🏛 대표 노출 : {top_expose}")

        st.info(explain)

st.divider()
# =====================================================
# 군집 선택
# =====================================================

st.subheader("🔍 군집 선택")

selected_group = st.selectbox(
    "분석할 군집을 선택하세요.",
    ["A", "B", "C", "D"]
)

group_df = data[data["군집"] == selected_group]

avg_age = int(group_df["문화재연령"].mean())

top_material = material_encoder.inverse_transform(
    [group_df["재질"].mode()[0]]
)[0]

top_expose = expose_encoder.inverse_transform(
    [group_df["노출형태"].mode()[0]]
)[0]

heritage_count = len(group_df)

st.divider()

# =====================================================
# AI 해석
# =====================================================

st.subheader("🤖 AI 군집 해석")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "문화재 수",
        heritage_count
    )

with c2:
    st.metric(
        "평균 연령",
        f"{avg_age}년"
    )

with c3:
    st.metric(
        "대표 재질",
        top_material
    )

with c4:
    st.metric(
        "대표 노출 형태",
        top_expose
    )

st.info(
f"""
### {selected_group} 군집 분석 결과

AI는 **문화재 연령**, **재질**, **노출 형태**를
종합적으로 분석하여 이 문화재들을 같은 군집으로 분류했습니다.

✔ 평균 연령 : **{avg_age}년**

✔ 대표 재질 : **{top_material}**

✔ 대표 노출 형태 : **{top_expose}**

즉,

**{top_material} 재질**의 문화재가 많고,

주로 **{top_expose}** 형태로 보존되며,

평균 연령은 **{avg_age}년**인 문화재들이
비슷한 특성을 보여 하나의 군집으로 분류되었습니다.
"""
)

st.divider()

# =====================================================
# 군집별 문화재 개수
# =====================================================

st.subheader("📊 군집별 문화재 개수")

count_df = (
    data.groupby("군집")
    .size()
    .reset_index(name="문화재 수")
)

fig = px.bar(
    count_df,
    x="군집",
    y="문화재 수",
    color="군집",
    text="문화재 수"
)

fig.update_layout(
    showlegend=False,
    xaxis_title="군집",
    yaxis_title="개수"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# 재질 분포
# =====================================================

st.subheader("🪨 선택한 군집의 재질 분포")

material_df = (
    group_df.groupby("재질")
    .size()
    .reset_index(name="개수")
)

material_df["재질"] = material_encoder.inverse_transform(
    material_df["재질"]
)

fig = px.pie(
    material_df,
    names="재질",
    values="개수",
    hole=0.4
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# 노출 형태 분포
# =====================================================

st.subheader("🏛 선택한 군집의 노출 형태")

expose_df = (
    group_df.groupby("노출형태")
    .size()
    .reset_index(name="개수")
)

expose_df["노출형태"] = expose_encoder.inverse_transform(
    expose_df["노출형태"]
)

fig = px.bar(
    expose_df,
    x="노출형태",
    y="개수",
    color="노출형태",
    text="개수"
)

fig.update_layout(
    showlegend=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

# =====================================================
# 군집별 지도
# =====================================================

st.subheader("🗺️ 선택한 군집의 위치")

color_map = {
    "A": "blue",
    "B": "green",
    "C": "orange",
    "D": "red"
}

center_lat = group_df["위도"].mean()
center_lon = group_df["경도"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11
)

for _, row in group_df.iterrows():

    material = material_encoder.inverse_transform(
        [row["재질"]]
    )[0]

    expose = expose_encoder.inverse_transform(
        [row["노출형태"]]
    )[0]

    popup = f"""
    <b>{row['문화재명(국문)']}</b><br><br>

    <b>군집</b> : {row['군집']}<br>

    <b>국가유산종목</b> : {row['국가유산종목']}<br>

    <b>시대</b> : {row['시대그룹']}<br>

    <b>문화재 연령</b> : {int(row['문화재연령'])}년<br>

    <b>재질</b> : {material}<br>

    <b>노출 형태</b> : {expose}
    """

    folium.Marker(
        location=[row["위도"], row["경도"]],
        tooltip=row["문화재명(국문)"],
        popup=popup,
        icon=folium.Icon(
            color=color_map[selected_group],
            icon="info-sign"
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

# =====================================================
# 문화재 목록
# =====================================================

st.subheader(f"📋 {selected_group} 군집 문화재 목록")

table = group_df[
    [
        "문화재명(국문)",
        "국가유산종목",
        "시대그룹",
        "문화재연령",
        "재질",
        "노출형태"
    ]
].copy()

table["재질"] = material_encoder.inverse_transform(
    table["재질"]
)

table["노출형태"] = expose_encoder.inverse_transform(
    table["노출형태"]
)

table = table.rename(
    columns={
        "문화재명(국문)":"문화재명",
        "국가유산종목":"종목",
        "시대그룹":"시대",
        "문화재연령":"연령(년)"
    }
)

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True
)

st.divider()

# =====================================================
# 군집 비교
# =====================================================

st.subheader("📑 군집 비교")

summary = (
    data.groupby("군집")
    .agg(
        평균연령=("문화재연령","mean"),
        문화재수=("군집","count")
    )
    .reset_index()
)

summary["대표재질"] = ""

summary["대표노출"] = ""

for i in summary.index:

    g = summary.loc[i,"군집"]

    tmp = data[data["군집"]==g]

    summary.loc[i,"대표재질"] = material_encoder.inverse_transform(
        [tmp["재질"].mode()[0]]
    )[0]

    summary.loc[i,"대표노출"] = expose_encoder.inverse_transform(
        [tmp["노출형태"].mode()[0]]
    )[0]

summary["평균연령"] = summary["평균연령"].astype(int)

st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.success("✅ AI 군집분석이 완료되었습니다.")

st.markdown("""
### 💡 분석 결과 해석

이번 군집분석은 하나의 기준이 아닌

- 📅 문화재 연령
- 🪨 재질
- 🏛 노출 형태

를 **동시에 고려**하여 수행되었습니다.

즉, 같은 군집에 속한 문화재는
세 가지 특성이 서로 비슷한 문화재라는 의미입니다.

지도에서는 선택한 군집만 표시되므로
공간적으로 어떤 지역에 분포하는지 쉽게 확인할 수 있으며,

문화재 목록을 통해
같은 특징을 가진 문화재를 한눈에 비교할 수 있습니다.
""")
