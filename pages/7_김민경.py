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

    name = str(info["문화재명(국문)"])
    period = str(info["시대그룹"])
    material = str(info["재질"])
    category = str(info["국가유산종목"])
    exposure = str(info["노출형태"])

    # -------------------------------
    # AI 분석 카드
    # -------------------------------

    st.subheader("🧠 AI 분석 카드")

    if "목" in material:
        history_score = 90
        preserve_score = 65
        view_score = 85
        damage_text = "습도 변화와 해충 피해에 주의가 필요합니다."
    elif "석" in material:
        history_score = 88
        preserve_score = 75
        view_score = 80
        damage_text = "풍화, 균열, 동결·융해 작용을 살펴볼 필요가 있습니다."
    elif "금" in material:
        history_score = 85
        preserve_score = 60
        view_score = 78
        damage_text = "습기와 대기오염에 의한 부식 관리가 중요합니다."
    else:
        history_score = 82
        preserve_score = 70
        view_score = 75
        damage_text = "재질 특성에 따른 정기적인 상태 점검이 필요합니다."

    if "실외" in exposure:
        preserve_score -= 15
    elif "반실외" in exposure:
        preserve_score -= 8

    preserve_score = max(preserve_score, 30)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("⭐ 역사적 가치", f"{history_score}%")

    with c2:
        st.metric("🛡 보존 안정도", f"{preserve_score}%")

    with c3:
        st.metric("👀 관람 추천도", f"{view_score}%")

    st.write("역사적 가치")
    st.progress(history_score / 100)

    st.write("보존 안정도")
    st.progress(preserve_score / 100)

    st.write("관람 추천도")
    st.progress(view_score / 100)

    # -------------------------------
    # AI 핵심 해석
    # -------------------------------

    st.subheader("💬 AI가 본 핵심")

    st.info(f"""
**{name}**은(는) **{period}**의 역사와 문화를 보여 주는 **{category}**입니다.

주요 재질은 **{material}**이며, 현재 **{exposure}** 환경에서 보존되고 있습니다.

이 문화재를 이해할 때는 단순히 이름만 보는 것이 아니라,  
**시대적 배경 + 재질 특성 + 보존 환경**을 함께 살펴보는 것이 중요합니다.

특히 {damage_text}
""")

    # -------------------------------
    # 관람 포인트
    # -------------------------------

    st.subheader("👀 꼭 봐야 할 관람 포인트")

    if "서원" in name:
        points = [
            "강학 공간과 제향 공간이 어떻게 나뉘어 있는지 살펴보세요.",
            "조선 시대 선비들의 교육 문화가 공간에 어떻게 드러나는지 확인해 보세요.",
            "건축물이 주변 자연환경과 어떻게 어우러지는지 관찰해 보세요."
        ]
    elif "향교" in name:
        points = [
            "지방 교육기관으로서 어떤 역할을 했는지 생각해 보세요.",
            "제사 공간과 교육 공간의 배치를 비교해 보세요.",
            "지역 사회에서 향교가 지닌 의미를 살펴보세요."
        ]
    elif "사" in name or "암" in name:
        points = [
            "사찰 건축의 배치와 주변 산세의 관계를 살펴보세요.",
            "불교 문화가 건축물의 구조와 장식에 어떻게 반영되었는지 보세요.",
            "목재와 석재가 사용된 부분을 구분해 보세요."
        ]
    elif "비" in name:
        points = [
            "비석에 새겨진 글이 어떤 역사 정보를 담고 있는지 생각해 보세요.",
            "비석의 위치와 형태가 어떤 의미를 가지는지 살펴보세요.",
            "기록 문화재가 역사 연구에 왜 중요한지 생각해 보세요."
        ]
    elif "탑" in name:
        points = [
            "탑의 층수와 전체적인 균형을 살펴보세요.",
            "불교적 의미와 조형미가 어떻게 드러나는지 관찰해 보세요.",
            "석재 표면의 풍화 흔적을 확인해 보세요."
        ]
    else:
        points = [
            "문화재의 이름과 시대 정보를 함께 살펴보세요.",
            "주요 재질이 보존 상태에 어떤 영향을 주는지 생각해 보세요.",
            "현재 노출 형태가 문화재 관리에 어떤 의미가 있는지 확인해 보세요."
        ]

    for i, point in enumerate(points, 1):
        st.markdown(f"**{i}.** {point}")

    # -------------------------------
    # 알고 있었나요?
    # -------------------------------

    st.subheader("💡 알고 있었나요?")

    if "목" in material:
        tip = "목조 문화재는 습도 변화에 따라 미세하게 팽창과 수축을 반복할 수 있습니다."
    elif "석" in material:
        tip = "석조 문화재는 단단해 보여도 비와 바람, 온도 변화에 의해 서서히 풍화될 수 있습니다."
    elif "금" in material:
        tip = "금속 문화재는 공기 중 수분과 오염물질에 의해 부식이 진행될 수 있습니다."
    else:
        tip = "문화재는 재질과 보존 환경에 따라 훼손되는 방식이 서로 다르게 나타납니다."

    st.warning(tip)

    # -------------------------------
    # 문화재 퀴즈
    # -------------------------------

    st.subheader("❓ 문화재 퀴즈")

    quiz = st.radio(
        f"{name}의 주요 재질은 무엇일까요?",
        ["목조", "석조", "금속", material],
        key=f"quiz_{name}"
    )

    if st.button("정답 확인"):
        if quiz == material:
            st.success("정답입니다! 문화재의 재질은 보존 방법을 결정하는 중요한 기준입니다.")
        else:
            st.error(f"아쉬워요. 정답은 **{material}**입니다.")

    st.subheader("🎓 수준별 해설")

    level = st.radio(
        "설명 수준을 선택하세요.",
        ["초등학생 수준", "중·고등학생 수준", "전문가 수준"]
    )

    if st.button("수준별 해설 보기"):

        if level == "초등학생 수준":
            st.success(f"""
### 👦 초등학생 수준

**{info['문화재명(국문)']}**은(는) 아주 오래전 사람들이 만든 소중한 문화재예요.

이 문화재는 **{info['시대그룹']}** 시대와 관련이 있으며, **{info['재질']}**로 만들어졌어요.

오랫동안 많은 사람들이 이 문화재를 잘 보살펴 왔기 때문에 지금까지 남아 있을 수 있었답니다.

하지만 비, 바람, 햇빛처럼 자연환경의 영향을 계속 받기 때문에 조금씩 낡을 수도 있어요.

문화재를 만지지 않고, 낙서를 하지 않으며, 관람 예절을 지키는 것이 문화재를 보호하는 첫걸음입니다.
""")

        elif level == "중·고등학생 수준":
            st.success(f"""
### 🎓 중·고등학생 수준

**{info['문화재명(국문)']}**은(는) **{info['시대그룹']}** 시대의 역사와 문화적 특징을 보여 주는 중요한 문화유산입니다.

주요 재질은 **{info['재질']}**이며, 현재는 **{info['노출형태']}** 환경에서 보존되고 있습니다.

문화재는 단순히 오래된 건축물이나 유물이 아니라 당시의 정치, 사회, 종교, 생활 문화를 이해할 수 있는 중요한 역사 자료입니다.

특히 재질에 따라 훼손되는 원인이 다릅니다.

• 목조 문화재는 높은 습도와 해충 피해에 취약합니다.

• 석조 문화재는 풍화, 강수, 동결·융해 작용으로 균열이 발생할 수 있습니다.

• 금속 문화재는 습기와 대기오염으로 인해 부식이 진행될 수 있습니다.

최근에는 기온, 습도, 강수량, 미세먼지 등의 환경 데이터를 활용하여 문화재의 훼손 가능성을 예측하고 예방하는 연구가 활발하게 이루어지고 있습니다.
""")

        else:
            st.success(f"""
### 🧠 전문가 수준

**{info['문화재명(국문)']}**은(는) **{info['시대그룹']}**에 조성된 **{info['국가유산종목']}**으로, 역사적·예술적·학술적 가치를 동시에 지닌 문화유산입니다.

주요 재질은 **{info['재질']}**이며, 현재 **{info['노출형태']}** 환경에서 보존되고 있습니다.

문화재의 보존 상태는 재질의 물리·화학적 특성과 외부 환경의 상호작용에 의해 결정됩니다.

목조 문화재는 상대습도 변화에 따른 팽창·수축, 생물학적 열화(균류·해충), 자외선 노출 등에 영향을 받을 수 있습니다.

석조 문화재는 풍화작용, 염분 결정화, 산성비, 동결·융해 작용 등에 의해 표면 박락이나 균열이 발생할 수 있습니다.

금속 문화재는 산화 및 전기화학적 부식에 의해 표면 손상이 진행될 수 있어 지속적인 환경 관리가 필요합니다.

최근 문화재 보존 분야에서는 IoT 센서와 AI를 활용하여 기온, 습도, 강수량, 미세먼지 등의 데이터를 실시간으로 수집하고, 이를 기반으로 훼손 위험도를 예측하는 스마트 보존 관리 기술이 적용되고 있습니다.

이러한 데이터 기반 관리 방식은 문화재가 손상된 이후 복원하는 방식보다 훨씬 효율적인 예방 중심 보존 전략으로 평가받고 있습니다.
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
