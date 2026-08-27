# ==========================================================
# 라이브러리
# ==========================================================
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ==========================================================
# 페이지 설정
# ==========================================================
st.set_page_config(
    page_title="공공 환경 데이터 기반 영천 지역 문화재 훼손 위험 예측",
    page_icon="🏛",
    layout="wide"
)


# ==========================================================
# API KEY
# ==========================================================
# Streamlit Cloud에서는
# Settings → Secrets에 아래처럼 입력하세요.
#
# SERVICE_KEY = "새로운_API_키"
#
# ==========================================================

try:
    SERVICE_KEY = st.secrets["SERVICE_KEY"]
except Exception:
    SERVICE_KEY = ""


# ==========================================================
# 1. 기상청 ASOS 전날 최신 기상자료
# ==========================================================

ASOS_URL = (
    "https://apis.data.go.kr/"
    "1360000/AsosHourlyInfoService/getWthrDataList"
)

# 영천 관측소
STN_ID = "281"

# 한국시간
now = datetime.now(ZoneInfo("Asia/Seoul"))

# 전날
yesterday = now - timedelta(days=1)

base_date = yesterday.strftime("%Y%m%d")
base_hour = "23"


# ==========================================================
# 기본값
# ==========================================================

tm = "-"
temp = "-"
humidity = "-"
rainfall = "-"
wind_speed = "-"


# ==========================================================
# ASOS API 요청
# ==========================================================

if SERVICE_KEY:

    asos_params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": "1",
        "numOfRows": "1",
        "dataType": "JSON",

        "dataCd": "ASOS",
        "dateCd": "HR",

        # 전날 23시
        "startDt": base_date,
        "startHh": base_hour,

        "endDt": base_date,
        "endHh": base_hour,

        # 영천 관측소
        "stnIds": STN_ID
    }

    try:

        response = requests.get(
            ASOS_URL,
            params=asos_params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        # 데이터가 존재하는지 확인
        items = (
            data
            .get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )

        if items:

            item = items[0]

            # 관측 시각
            tm = item.get("tm", "-")

            # 기온
            temp = item.get("ta", "-")

            # 습도
            humidity = item.get("hm", "-")

            # 강수량
            rainfall = item.get("rn", "-")

            # 풍속
            wind_speed = item.get("ws", "-")

        else:

            st.warning(
                "기상청 API에서 전날 23시 데이터를 찾지 못했습니다."
            )

    except Exception as e:

        st.warning(
            f"기상 데이터 조회에 실패했습니다: {e}"
        )

else:

    st.warning(
        "SERVICE_KEY가 설정되지 않았습니다. "
        "Streamlit Secrets에 API 키를 등록해주세요."
    )


# ==========================================================
# 2. 대기오염 최신 데이터
# ==========================================================

AIR_URL = (
    "https://apis.data.go.kr/"
    "B552584/ArpltnInforInqireSvc/"
    "getCtprvnRltmMesureDnsty"
)


# ==========================================================
# 기본값
# ==========================================================

pm10 = "-"
pm25 = "-"

o3 = "-"
no2 = "-"

co = "-"
so2 = "-"

data_time = "-"


# ==========================================================
# 대기오염 API 요청
# ==========================================================

if SERVICE_KEY:

    air_params = {
        "serviceKey": SERVICE_KEY,
        "returnType": "json",

        "numOfRows": "100",
        "pageNo": "1",

        # 경북
        "sidoName": "경북",

        "ver": "1.0"
    }

    try:

        air_response = requests.get(
            AIR_URL,
            params=air_params,
            timeout=30
        )

        air_response.raise_for_status()

        air_data = air_response.json()

        items = (
            air_data
            .get("response", {})
            .get("body", {})
            .get("items", [])
        )

        # 영천 측정소 찾기
        target = None

        for item in items:

            station_name = item.get("stationName", "")

            if "영천" in station_name:

                target = item
                break

        if target:

            data_time = target.get("dataTime", "-")

            pm10 = target.get("pm10Value", "-")
            pm25 = target.get("pm25Value", "-")

            o3 = target.get("o3Value", "-")
            no2 = target.get("no2Value", "-")

            co = target.get("coValue", "-")
            so2 = target.get("so2Value", "-")

        else:

            st.warning(
                "대기오염 API에서 영천 측정소를 찾지 못했습니다."
            )

    except Exception as e:

        st.warning(
            f"대기오염 데이터 조회에 실패했습니다: {e}"
        )


# ==========================================================
# 3. 문화재 데이터 불러오기
# ==========================================================

DATA_PATH = "data/processed/yc_heritage_detail_enriched.csv"


try:

    df = pd.read_csv(DATA_PATH)

except FileNotFoundError:

    st.error(
        f"문화재 데이터 파일을 찾을 수 없습니다.\n\n"
        f"파일 경로: `{DATA_PATH}`"
    )

    st.stop()

except Exception as e:

    st.error(
        f"문화재 데이터 불러오기에 실패했습니다: {e}"
    )

    st.stop()


# ==========================================================
# 중요
# ==========================================================
# 기존 코드에서
#
# X = dataset[...]
#
# 처럼 작성되어 있었다면 오류가 발생합니다.
#
# 현재 데이터프레임 이름은 df이므로
#
# X = df[...]
#
# 로 사용해야 합니다.
#
# ==========================================================


# ==========================================================
# 제목
# ==========================================================

st.markdown(
    """
    <h1 style='font-size:30px;'>
    🏛 공공 환경 데이터 기반 영천 지역 문화재 훼손 위험 예측
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    영천 지역 문화재와 공공 환경데이터를 분석하여
    문화재 훼손 위험을 사전에 예측하는 데이터 분석 프로젝트입니다.
    """
)

st.divider()


# ==========================================================
# 상단 환경 대시보드
# ==========================================================

st.markdown(
    """
    <h3 style="
        font-size:25px;
        margin-bottom:10px;
    ">
    🌿 영천시 환경 데이터 및 문화재 현황
    </h3>
    """,
    unsafe_allow_html=True
)


# ==========================================================
# 메인 영역
# ==========================================================

left, center, right = st.columns([1.4, 2.0, 1.0])


# ==========================================================
# 공통 스타일
# ==========================================================

card_style = """
background-color:#f8f9fa;
padding:22px;
border-radius:20px;
border:1px solid #e5e7eb;
box-shadow:0 4px 12px rgba(0,0,0,0.05);
height:350px;
"""

title_style = """
font-size:24px;
font-weight:700;
margin-bottom:14px;
color:#1f2937;
"""

label_style = """
font-size:14px;
color:#6b7280;
margin-bottom:4px;
"""

value_style = """
font-size:22px;
font-weight:700;
color:#111827;
margin-bottom:18px;
"""

time_style = """
font-size:13px;
color:#9ca3af;
margin-top:12px;
position:absolute;
bottom:20px;
"""


# ==========================================================
# 1열 : 기상 환경
# ==========================================================

with left:

    st.markdown(
        f"""
        <div style="{card_style}; position:relative;">

            <div style="{title_style}">
                🌦 기상 환경
            </div>

            <hr>

            <div style="
                display:grid;
                grid-template-columns:1fr 1fr;
                gap:16px;
                margin-top:20px;
            ">

                <div>
                    <div style="{label_style}">
                        🌡 기온
                    </div>

                    <div style="{value_style}">
                        {temp} °C
                    </div>
                </div>


                <div>
                    <div style="{label_style}">
                        💧 습도
                    </div>

                    <div style="{value_style}">
                        {humidity} %
                    </div>
                </div>


                <div>
                    <div style="{label_style}">
                        🌧 강수량
                    </div>

                    <div style="{value_style}">
                        {rainfall} mm
                    </div>
                </div>


                <div>
                    <div style="{label_style}">
                        💨 풍속
                    </div>

                    <div style="{value_style}">
                        {wind_speed} m/s
                    </div>
                </div>

            </div>

            <div style="{time_style}">
                ⏱ 측정 시각 : {tm}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# 2열 : 대기오염 현황
# ==========================================================

with center:

    st.markdown(
        f"""
        <div style="{card_style}; position:relative;">

            <div style="{title_style}">
                🌫 대기오염 현황
            </div>

            <hr>

            <div style="
                display:grid;
                grid-template-columns:1fr 1fr 1fr;
                gap:20px;
                margin-top:20px;
            ">

                <div>

                    <div style="{label_style}">
                        PM10
                    </div>

                    <div style="{value_style}">
                        {pm10}
                    </div>


                    <div style="{label_style}">
                        O₃
                    </div>

                    <div style="{value_style}">
                        {o3}
                    </div>

                </div>


                <div>

                    <div style="{label_style}">
                        PM2.5
                    </div>

                    <div style="{value_style}">
                        {pm25}
                    </div>


                    <div style="{label_style}">
                        NO₂
                    </div>

                    <div style="{value_style}">
                        {no2}
                    </div>

                </div>


                <div>

                    <div style="{label_style}">
                        CO
                    </div>

                    <div style="{value_style}">
                        {co}
                    </div>


                    <div style="{label_style}">
                        SO₂
                    </div>

                    <div style="{value_style}">
                        {so2}
                    </div>

                </div>

            </div>

            <div style="{time_style}">
                ⏱ 측정 시각 : {data_time}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# 3열 : 문화재 현황
# ==========================================================

with right:

    st.markdown(
        f"""
        <div style="{card_style}; position:relative;">

            <div style="{title_style}">
                🏛 문화재 현황
            </div>

            <hr>

            <div style="margin-top:20px;">

                <div style="{label_style}">
                    분석 문화재 수
                </div>

                <div style="{value_style}">
                    {len(df)}개
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# 데이터 확인 영역
# ==========================================================

st.divider()

st.subheader("📊 문화재 데이터 확인")

st.write(
    f"총 **{len(df)}개**의 문화재 데이터를 불러왔습니다."
)

with st.expander("문화재 데이터 미리보기"):

    st.dataframe(
        df.head(10),
        use_container_width=True
    )


# ==========================================================
# 하단 안내
# ==========================================================

st.divider()

st.caption(
    "제6회 학생 SW·AI 인재양성 프로젝트 | "
    "선화여고 - 영천 헤리티지 AI 탐구단"
)
