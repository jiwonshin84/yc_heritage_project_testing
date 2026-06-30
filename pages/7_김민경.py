import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="AI 문화재 해설", layout="wide")

if "selected_heritage" not in st.session_state:
    st.session_state.selected_heritage = None

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

st.title("🤖 AI 문화재 해설")

st.write("궁금한 문화재를 검색하거나 아래의 많이 찾는 문화재를 선택해 보세요.")

# -------------------------------
# 많이 찾는 문화재
# -------------------------------

popular = [
    "은해사",
    "영천향교",
    "임고서원",
    "거조암",
    "청제비"
]



# -------------------------------
# 검색
# -------------------------------

st.subheader("🔍 문화재 검색")

heritage_list = sorted(df["문화재명(국문)"].dropna().unique())

default_index = None

if st.session_state.selected_heritage is not None:
    for h in heritage_list:
        if st.session_state.selected_heritage in h:
            default_index = heritage_list.index(h)
            break

heritage = st.selectbox(
    "문화재를 검색하거나 선택하세요.",
    heritage_list,
    index=default_index,
    placeholder="예) 은해사"
)

heritage = st.selectbox(
    "문화재를 검색하거나 선택하세요.",
    heritage_list,
    index=index,
    placeholder="예) 은해사"
)

if heritage is None:
    st.info("문화재를 검색하거나 선택해 주세요.")
    st.stop()

info = df[df["문화재명(국문)"] == heritage].iloc[0]

st.divider()

col1, col2 = st.columns([1, 2])

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
**{info['문화재명(국문)']}**은(는) **{info['시대그룹']}**에 만들어진 문화재입니다.

주요 재질은 **{info['재질']}**이며,
현재 **{info['노출형태']}** 형태로 보존되고 있습니다.

문화재의 재질과 노출 환경에 따라 기후 변화와 풍화의 영향을 받을 수 있으므로
정기적인 점검과 보존 관리가 중요합니다.

문화재를 방문할 때에는 문화재를 만지거나 훼손하지 않고
관람 예절을 지키는 것이 중요합니다.
"""

    st.info(explanation)




st.divider()

st.subheader("🗺️ 문화재 위치")

m = folium.Map(
    location=[info["위도"], info["경도"]],
    zoom_start=15,
    tiles="OpenStreetMap"
)

popup_html = f"""
<h4>{info['문화재명(국문)']}</h4>

<b>📅 시대</b> : {info['시대그룹']}<br>

<b>🪨 재질</b> : {info['재질']}<br>

<b>🏛 국가유산종목</b> : {info['국가유산종목']}<br>

<b>🏞 노출 형태</b> : {info['노출형태']}
"""

folium.Marker(
    location=[info["위도"], info["경도"]],
    popup=folium.Popup(popup_html, max_width=300),
    tooltip=info["문화재명(국문)"],
    icon=folium.Icon(
        color="red",
        icon="glyphicon-map-marker"
    )
).add_to(m)

st_folium(
    m,
    width=None,
    height=500,
    use_container_width=True
)

st.caption("📍 지도의 핀을 클릭하면 문화재 정보를 확인할 수 있습니다.")
