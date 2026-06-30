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

st.title("💡 AI 문화재 해설")

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

    st.subheader("💡 AI 문화재 해설")

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

    st.subheader("🎓 수준별 해설")

    level = st.radio(
        "설명 수준을 선택하세요.",
        ["초등학생 수준", "중·고등학생 수준", "전문가 수준"]
    )

    if st.button("수준별 해설 보기"):
        if level == "초등학생 수준":
            st.success(f"""
**{info['문화재명(국문)']}**은(는) 오래전 사람들이 남긴 소중한 문화재입니다.

이 문화재는 **{info['시대그룹']}**와 관련이 있고, 주로 **{info['재질']}**로 이루어져 있습니다.

옛날 사람들의 생활 모습과 생각을 알 수 있게 해 주기 때문에 잘 보존해야 합니다.
""")

        elif level == "중·고등학생 수준":
            st.success(f"""
**{info['문화재명(국문)']}**은(는) **{info['시대그룹']}**의 역사와 문화를 이해하는 데 중요한 자료입니다.

주요 재질은 **{info['재질']}**이며, 현재 **{info['노출형태']}** 상태로 보존되고 있습니다.

이 문화재를 통해 당시의 건축 방식, 생활 문화, 지역의 역사적 특징을 살펴볼 수 있습니다.
""")

        else:
            st.success(f"""
**{info['문화재명(국문)']}**은(는) 역사적·학술적·보존학적 가치를 지닌 문화유산입니다.

제작 시기인 **{info['시대그룹']}**, 주요 재질인 **{info['재질']}**, 그리고 **{info['노출형태']}**이라는 보존 환경을 함께 고려할 때, 이 문화재는 지역 문화와 보존 관리 연구의 중요한 자료가 됩니다.
""")

    st.subheader("💬 AI Q&A")

    question = st.text_input(
        "문화재에 대해 궁금한 점을 입력하세요.",
        placeholder="예) 왜 이 문화재가 중요한가요?"
    )

    if st.button("질문하기"):
        if question.strip() == "":
            st.warning("질문을 입력해 주세요.")
        elif "중요" in question:
            st.info(f"""
**{info['문화재명(국문)']}**이/가 중요한 이유는 **{info['시대그룹']}**의 역사와 문화를 보여 주기 때문입니다.

문화재는 단순히 오래된 물건이 아니라, 당시 사람들의 생활 방식과 기술, 가치관을 알려 주는 자료입니다.
""")
        elif "재질" in question or "무엇" in question:
            st.info(f"""
**{info['문화재명(국문)']}**의 주요 재질은 **{info['재질']}**입니다.

재질에 따라 보존 방법과 훼손 양상이 달라지기 때문에 문화재 해설에서 재질 정보는 중요합니다.
""")
        elif "시대" in question or "언제" in question:
            st.info(f"""
**{info['문화재명(국문)']}**은(는) **{info['시대그룹']}**와 관련된 문화재입니다.

시대 정보를 알면 문화재가 만들어진 배경과 당시 사회 모습을 이해하는 데 도움이 됩니다.
""")
        else:
            st.info(f"""
**{info['문화재명(국문)']}**에 대한 좋은 질문입니다.

이 문화재는 **{info['시대그룹']}**의 역사와 지역 문화를 이해하는 데 중요한 자료입니다.  
더 자세히 보려면 시대, 재질, 위치, 보존 상태를 함께 살펴보면 좋습니다.
""")


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
