import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium


# -----------------------------------
# 페이지 기본 설정
# -----------------------------------

st.set_page_config(
    page_title="AI 문화재 해설",
    layout="wide"
)

if "selected_heritage" not in st.session_state:
    st.session_state.selected_heritage = None


# -----------------------------------
# 데이터 불러오기
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")


# -----------------------------------
# 기본 함수
# -----------------------------------

def safe_text(value, default="정보 없음"):
    if pd.isna(value):
        return default

    value = str(value).strip()

    if value == "":
        return default

    return value


def make_period_text(period):

    if period in ["기타", "미상", "정보 없음", "nan"]:
        return "정확한 조성 시기는 자료에서 확인하기 어렵습니다."

    return f"{period}와 관련된 문화재입니다."


def calculate_scores(period, material, category, exposure):

    # -------------------------------
    # 역사적 가치
    # -------------------------------

    history_score = 70

    if "국보" in category:
        history_score += 25

    elif "보물" in category:
        history_score += 20

    elif "사적" in category:
        history_score += 18

    elif "기념물" in category:
        history_score += 15

    elif category != "정보 없음":
        history_score += 10

    if period not in ["기타", "미상", "정보 없음"]:
        history_score += 5

    history_score = min(history_score, 100)


    # -------------------------------
    # 보존 안정도
    # -------------------------------

    preserve_score = 85

    if "목" in material:
        preserve_score -= 15

    elif "금" in material:
        preserve_score -= 12

    elif "석" in material:
        preserve_score -= 5

    if exposure == "실외":
        preserve_score -= 20

    elif exposure == "반실외":
        preserve_score -= 10

    preserve_score = max(30, min(preserve_score, 100))


    # -------------------------------
    # 관람 추천도
    # -------------------------------

    view_score = 70

    if history_score >= 90:
        view_score += 15

    elif history_score >= 80:
        view_score += 10

    if category != "정보 없음":
        view_score += 5

    view_score = min(view_score, 100)


    return history_score, preserve_score, view_score


def make_preservation_text(material, exposure):

    if "목" in material:
        text = (
            "목재는 습도 변화에 따라 팽창과 수축이 반복될 수 있고 "
            "해충이나 미생물의 영향을 받을 수 있습니다."
        )

    elif "석" in material:
        text = (
            "석재는 비교적 안정적인 재질이지만 비와 바람, "
            "온도 변화가 반복되면 표면 풍화가 진행될 수 있습니다."
        )

    elif "금" in material:
        text = (
            "금속은 공기 중의 수분이나 오염물질과 반응하여 "
            "부식이 진행될 수 있습니다."
        )

    else:
        text = (
            "문화재는 재질의 특성에 따라 환경 변화에 "
            "서로 다른 영향을 받을 수 있습니다."
        )

    if exposure == "실외":
        text += " 특히 실외에 노출되어 있어 기상 변화의 영향을 지속적으로 받을 수 있습니다."

    elif exposure == "반실외":
        text += " 반실외 환경이므로 외부의 온도와 습도 변화에도 주의할 필요가 있습니다."

    return text


# -----------------------------------
# 제목
# -----------------------------------

st.title("💡 AI 문화재 해설")

st.write(
    "궁금한 문화재를 검색하면 문화재의 기본 정보와 "
    "재질·보존 환경을 바탕으로 한 분석을 확인할 수 있습니다."
)


# -----------------------------------
# 문화재 검색
# -----------------------------------

st.subheader("🔍 문화재 검색")

heritage_list = sorted(
    df["문화재명(국문)"].dropna().unique()
)

default_index = None

if st.session_state.selected_heritage is not None:

    if st.session_state.selected_heritage in heritage_list:
        default_index = heritage_list.index(
            st.session_state.selected_heritage
        )


heritage = st.selectbox(
    "문화재를 검색하거나 선택하세요.",
    heritage_list,
    index=default_index,
    placeholder="예) 은해사"
)


if heritage is None:

    st.info("문화재를 검색하거나 선택해 주세요.")
    st.stop()


st.session_state.selected_heritage = heritage

info = df[
    df["문화재명(국문)"] == heritage
].iloc[0]


# -----------------------------------
# 데이터 정리
# -----------------------------------

name = safe_text(info["문화재명(국문)"])

period = safe_text(info["시대그룹"])

material = safe_text(info["재질"])

category = safe_text(info["국가유산종목"])

exposure = safe_text(info["노출형태"])


period_text = make_period_text(period)

history_score, preserve_score, view_score = calculate_scores(
    period,
    material,
    category,
    exposure
)

preservation_text = make_preservation_text(
    material,
    exposure
)


# -----------------------------------
# 문화재 정보 + 문화재 해설
# -----------------------------------

st.divider()

col1, col2 = st.columns([1, 2])


with col1:

    st.subheader("🏛️ 문화재 정보")

    st.markdown(f"### {name}")

    st.write(f"📅 시대 : {period}")

    st.write(f"🪨 재질 : {material}")

    st.write(f"🏛️ 국가유산종목 : {category}")

    st.write(f"🏞️ 노출 형태 : {exposure}")


with col2:

    st.subheader("💡 AI 문화재 해설")

    explanation = f"""
**{name}**은(는) 영천 지역의 역사와 문화를 보여 주는 문화유산입니다.

{period_text}

국가유산종목은 **{category}**이며,
주요 재질은 **{material}**입니다.

현재 **{exposure}** 환경에서 보존되고 있어
재질뿐만 아니라 주변의 온도, 습도, 강수 등의 환경 조건을
함께 고려한 관리가 중요합니다.

{preservation_text}
"""

    st.info(explanation)


# -----------------------------------
# 데이터 기반 문화재 분석
# -----------------------------------

st.divider()

st.subheader("📊 데이터 기반 문화재 분석")

st.caption(
    "문화재의 시대, 국가유산종목, 재질, 노출 환경을 "
    "조건문으로 분석하여 점수를 계산했습니다."
)

c1, c2, c3 = st.columns(3)


with c1:

    st.metric(
        "⭐ 역사적 가치",
        f"{history_score}%"
    )


with c2:

    st.metric(
        "🛡️ 보존 안정도",
        f"{preserve_score}%"
    )


with c3:

    st.metric(
        "👀 관람 추천도",
        f"{view_score}%"
    )


st.write("역사적 가치")

st.progress(
    history_score / 100
)


st.write("보존 안정도")

st.progress(
    preserve_score / 100
)


st.write("관람 추천도")

st.progress(
    view_score / 100
)


# -----------------------------------
# 분석 결과
# -----------------------------------

st.subheader("🔎 분석 결과")

st.info(
    f"""
**{name}**의 주요 재질은 **{material}**이고,
현재 노출 환경은 **{exposure}**입니다.

{preservation_text}

따라서 이 문화재를 이해하고 보존할 때에는
역사적 가치뿐만 아니라 **재질의 특성과 주변 환경의 관계**를
함께 살펴보는 것이 중요합니다.
"""
)


# -----------------------------------
# 문화재 Q&A
# -----------------------------------

st.divider()

st.subheader("💬 문화재 Q&A")

question = st.text_input(
    "문화재에 대해 궁금한 점을 입력하세요.",
    placeholder="예) 왜 이 문화재가 중요한가요?"
)


if st.button("질문하기"):

    question = question.strip()

    if question == "":

        st.warning(
            "질문을 입력해 주세요."
        )


    elif "중요" in question or "가치" in question:

        st.info(
            f"""
**{name}**은(는) 영천 지역의 역사와 문화를 이해할 수 있는
**{category}**입니다.

문화재는 단순히 오래된 건축물이나 유물이 아니라
당시 사람들의 생활, 기술, 문화적 특징을 보여 주는
역사 자료라는 점에서 가치가 있습니다.
"""
        )


    elif (
        "재질" in question
        or "무엇으로" in question
        or "만들" in question
    ):

        st.info(
            f"""
**{name}**의 주요 재질은 **{material}**입니다.

{preservation_text}

따라서 문화재의 재질을 파악하는 것은
적절한 보존 방법을 결정하는 데 중요합니다.
"""
        )


    elif (
        "시대" in question
        or "언제" in question
    ):

        if period in [
            "기타",
            "미상",
            "정보 없음"
        ]:

            st.info(
                f"""
**{name}**의 정확한 조성 시기는
현재 데이터에서는 명확하게 확인하기 어렵습니다.

다만 국가유산종목은 **{category}**이며,
문화재의 역사적 배경과 지역적 의미를 함께 살펴보는 것이 중요합니다.
"""
            )

        else:

            st.info(
                f"""
**{name}**은(는) **{period}**와 관련된 문화재입니다.

시대 정보를 살펴보면 문화재가 만들어진 배경과
당시 사회와 문화의 특징을 이해하는 데 도움이 됩니다.
"""
            )


    elif (
        "보존" in question
        or "훼손" in question
        or "관리" in question
    ):

        st.info(
            f"""
**{name}**은(는) **{material}** 재질이며
현재 **{exposure}** 환경에서 보존되고 있습니다.

{preservation_text}

따라서 문화재의 상태를 지속적으로 확인하고
환경 변화에 맞추어 관리하는 것이 중요합니다.
"""
        )


    elif (
        "위치" in question
        or "어디" in question
    ):

        st.info(
            "아래의 문화재 위치 지도에서 "
            "정확한 위치를 확인할 수 있습니다."
        )


    else:

        st.info(
            f"""
**{name}**은(는) **{category}**으로 분류되는 문화재입니다.

주요 재질은 **{material}**이며
현재 **{exposure}** 환경에서 보존되고 있습니다.

문화재를 자세히 이해하려면
시대, 재질, 국가유산종목, 위치와 보존 환경을
함께 살펴보는 것이 좋습니다.
"""
        )


# -----------------------------------
# 문화재 위치
# -----------------------------------

st.divider()

st.subheader("🗺️ 문화재 위치")


lat = pd.to_numeric(
    info["위도"],
    errors="coerce"
)

lon = pd.to_numeric(
    info["경도"],
    errors="coerce"
)


if pd.notna(lat) and pd.notna(lon):

    m = folium.Map(
        location=[
            lat,
            lon
        ],
        zoom_start=15,
        tiles="OpenStreetMap"
    )


    popup_html = f"""
    <h4>{name}</h4>

    <b>📅 시대</b> : {period}<br>

    <b>🪨 재질</b> : {material}<br>

    <b>🏛 국가유산종목</b> : {category}<br>

    <b>🏞 노출 형태</b> : {exposure}
    """


    folium.Marker(
        location=[
            lat,
            lon
        ],
        popup=folium.Popup(
            popup_html,
            max_width=300
        ),
        tooltip=name,
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


    st.caption(
        "📍 지도의 핀을 클릭하면 문화재 정보를 확인할 수 있습니다."
    )


else:

    st.warning(
        "이 문화재의 위치 정보가 없습니다."
    )
