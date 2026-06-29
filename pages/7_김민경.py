import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="AI 문화재 해설", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

st.title("🤖 AI 문화재 해설")

st.write("문화재 이름을 검색하거나 많이 찾는 문화재를 선택해 보세요.")

    "문화재 이름을 입력하세요.",
    placeholder="예) 은해사"


heritage_list = sorted(df["문화재명(국문)"].dropna().unique())

if search:
    heritage_list = [h for h in heritage_list if search in h]

if len(heritage_list) == 0:
    st.warning("검색 결과가 없습니다.")
    st.stop()

heritage = heritage_list[0]

if len(heritage_list) > 1:
    st.info(f"'{search}' 검색 결과 {len(heritage_list)}건이 있습니다. 첫 번째 결과를 표시합니다.")

info = df[df["문화재명(국문)"] == heritage].iloc[0]

# -------------------------------
# 많이 찾는 문화재
# -------------------------------

st.subheader("⭐ 많이 찾는 문화재")

popular = [
    "은해사",
    "영천향교",
    "임고서원",
    "거조암",
    "청제비"
]

cols = st.columns(len(popular))

selected = None

for i, name in enumerate(popular):

    with cols[i]:
        if st.button(name):
            selected = name

# -------------------------------
# 문화재 선택
# -------------------------------

heritage = st.selectbox(
    "문화재 선택",
    heritage_list
)

if selected is not None:

    for h in heritage_list:
        if selected in h:
            heritage = h
            break

info = df[df["문화재명(국문)"] == heritage].iloc[0]

st.divider()

col1, col2 = st.columns([1,2])

with col1:

    st.subheader("🏛 문화재 정보")

    st.metric("문화재명", info["문화재명(국문)"])

    st.write(f"📅 시대 : {info['시대그룹']}")

    st.write(f"🪨 재질 : {info['재질']}")

    st.write(f"🏛 국가유산종목 : {info['국가유산종목']}")

    st.write(f"🏞 노출 형태 : {info['노출형태']}")

with col2:

    st.subheader("🤖 AI 문화재 해설")

    explanation = f"""
**{info['문화재명(국문)']}**은(는)
**{info['시대그룹']}**에 만들어진 문화재입니다.

주요 재질은 **{info['재질']}**이며,
현재 **{info['노출형태']}** 형태로 보존되고 있습니다.

문화재의 재질과 노출 환경에 따라
기후 변화나 풍화의 영향을 받을 수 있으므로
정기적인 점검과 보존 관리가 중요합니다.

문화재를 직접 방문할 때에는
문화재를 만지거나 훼손하지 않도록
관람 예절을 지켜 소중한 문화유산을 함께 보호해야 합니다.
"""

    st.info(explanation)

st.divider()

st.subheader("🗺️ 문화재 위치")

m = folium.Map(
    location=[info["위도"], info["경도"]],
    zoom_start=15
)

folium.Marker(
    [info["위도"], info["경도"]],
    popup=info["문화재명(국문)"],
    tooltip=info["문화재명(국문)"],
    icon=folium.Icon(color="red")
).add_to(m)

st_folium(m, width=900, height=500)
