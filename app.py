# ==========================================================
# 라이브러리
# ==========================================================
import streamlit as st
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


# ==========================================================
# 페이지 설정
# ==========================================================
st.set_page_config(
    page_title="영천 문화재 훼손 위험 예측",
    page_icon="🏛️",
    layout="wide"
)


# ==========================================================
# API KEY
# ==========================================================
# Streamlit Cloud
#
# Settings → Secrets
#
# SERVICE_KEY = "새로운_API_KEY"
# ==========================================================

try:
    SERVICE_KEY = st.secrets["SERVICE_KEY"]
except Exception:
    SERVICE_KEY = ""


# ==========================================================
# 데이터 파일
# ==========================================================
DATA_PATH = "data/processed/yc_heritage_detail_enriched.csv"


# ==========================================================
# 문화재 데이터 불러오기
# ==========================================================
try:

    df = pd.read_csv(DATA_PATH)

except FileNotFoundError:

    st.error(
        "❌ 문화재 데이터 파일을 찾을 수 없습니다.\n\n"
        f"현재 경로: `{DATA_PATH}`"
    )

    st.stop()

except Exception as e:

    st.error(
        f"❌ 문화재 데이터 불러오기 실패: {e}"
    )

    st.stop()


# ==========================================================
# 제목
# ==========================================================
st.markdown(
    """
    <h1 style="font-size:30px;">
    🏛️ 공공 환경 데이터 기반 영천 지역 문화재 훼손 위험 예측
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    영천 지역 문화재 데이터와 기상·대기오염 공공데이터를 활용하여
    문화재 훼손 위험을 분석하는 프로젝트입니다.
    """
)

st.divider()


# ==========================================================
# 현재 한국시간
# ==========================================================
now = datetime.now(
    ZoneInfo("Asia/Seoul")
)

yesterday = now - timedelta(days=1)

base_date = yesterday.strftime("%Y%m%d")
base_hour = "23"


# ==========================================================
# 기본값
# ==========================================================

# ------------------------------
# 기상
# ------------------------------

tm = "-"
temp = "-"
humidity = "-"
rainfall = "-"
wind_speed = "-"


# ------------------------------
# 대기오염
# ------------------------------

pm10 = "-"
pm25 = "-"

o3 = "-"
no2 = "-"

co = "-"
so2 = "-"

data_time = "-"


# ==========================================================
# API 상태
# ==========================================================

weather_success = False
air_success = False


# ==========================================================
# 1. 기상청 ASOS API
# ==========================================================

ASOS_URL = (
    "https://apis.data.go.kr/"
    "1360000/AsosHourlyInfoService/getWthrDataList"
)

STN_ID = "281"


if SERVICE_KEY:

    asos_params = {

        "serviceKey": SERVICE_KEY,

        "pageNo": "1",

        "numOfRows": "1",

        "dataType": "JSON",

        "dataCd": "ASOS",

        "dateCd": "HR",

        "startDt": base_date,

        "startHh": base_hour,

        "endDt": base_date,

        "endHh": base_hour,

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

        items = (
            data
            .get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )

        if items:

            item = items[0]

            tm = item.get("tm", "-")

            temp = item.get("ta", "-")

            humidity = item.get("hm", "-")

            rainfall = item.get("rn", "-")

            wind_speed = item.get("ws", "-")

            weather_success = True

        else:

            st.warning(
                "⚠️ 기상청 API에서 데이터를 찾지 못했습니다."
            )

    except Exception as e:

        st.warning(
            f"⚠️ 기상 데이터 조회 실패: {e}"
        )

else:

    st.warning(
        "⚠️ SERVICE_KEY가 없습니다."
    )


# ==========================================================
# 2. 대기오염 API
# ==========================================================

AIR_URL = (
    "https://apis.data.go.kr/"
    "B552584/ArpltnInforInqireSvc/"
    "getCtprvnRltmMesureDnsty"
)


if SERVICE_KEY:

    air_params = {

        "serviceKey": SERVICE_KEY,

        "returnType": "json",

        "numOfRows": "100",

        "pageNo": "1",

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

        target = None

        for item in items:

            station_name = item.get(
                "stationName",
                ""
            )

            if "영천" in station_name:

                target = item

                break

        if target:

            data_time = target.get(
                "dataTime",
                "-"
            )

            pm10 = target.get(
                "pm10Value",
                "-"
            )

            pm25 = target.get(
                "pm25Value",
                "-"
            )

            o3 = target.get(
                "o3Value",
                "-"
            )

            no2 = target.get(
                "no2Value",
                "-"
            )

            co = target.get(
                "coValue",
                "-"
            )

            so2 = target.get(
                "so2Value",
                "-"
            )

            air_success = True

        else:

            st.warning(
                "⚠️ 영천 대기오염 측정소 데이터를 찾지 못했습니다."
            )

    except Exception as e:

        st.warning(
            f"⚠️ 대기오염 데이터 조회 실패: {e}"
        )


# ==========================================================
# 숫자 변환 함수
# ==========================================================

def to_number(value):

    try:

        if value in ["-", "", None]:

            return None

        return float(value)

    except:

        return None


# ==========================================================
# API 데이터 숫자 변환
# ==========================================================

temp_num = to_number(temp)

humidity_num = to_number(humidity)

rainfall_num = to_number(rainfall)

wind_speed_num = to_number(wind_speed)

pm10_num = to_number(pm10)

pm25_num = to_number(pm25)

o3_num = to_number(o3)

no2_num = to_number(no2)

co_num = to_number(co)

so2_num = to_number(so2)


# ==========================================================
# 현재 환경 데이터
# ==========================================================

environment_data = pd.DataFrame({

    "temp": [temp_num],

    "humidity": [humidity_num],

    "rainfall": [rainfall_num],

    "wind_speed": [wind_speed_num],

    "pm10": [pm10_num],

    "pm25": [pm25_num],

    "o3": [o3_num],

    "no2": [no2_num],

    "co": [co_num],

    "so2": [so2_num]

})


# ==========================================================
# API 데이터 상태 표시
# ==========================================================

st.subheader("🔌 공공데이터 API 연결 상태")

status1, status2 = st.columns(2)


with status1:

    if weather_success:

        st.success(
            "✅ 기상청 API 정상 연결"
        )

    else:

        st.error(
            "❌ 기상청 API 데이터 없음"
        )


with status2:

    if air_success:

        st.success(
            "✅ 대기오염 API 정상 연결"
        )

    else:

        st.error(
            "❌ 대기오염 API 데이터 없음"
        )


# ==========================================================
# 환경 데이터가 없는 경우
# ==========================================================

if environment_data.dropna(
    axis=1,
    how="all"
).empty:

    st.error(
        "❌ 머신러닝에 사용할 환경 데이터가 없습니다. "
        "기상청 API 키 또는 API 데이터 수집 상태를 확인해주세요."
    )

else:

    st.success(
        "✅ 환경 데이터가 정상적으로 생성되었습니다."
    )


# ==========================================================
# 환경 데이터 확인
# ==========================================================

with st.expander(
    "🔍 머신러닝 입력 데이터 확인"
):

    st.dataframe(
        environment_data,
        use_container_width=True
    )


# ==========================================================
# 상단 대시보드
# ==========================================================

st.divider()

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
# 카드
# ==========================================================

left, center, right = st.columns(
    [1.4, 2.0, 1.0]
)


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
# 기상 카드
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
# 대기오염 카드
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
# 문화재 카드
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

                <div style="{label_style}">
                    데이터 상태
                </div>

                <div style="{value_style}">
                    정상
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# 머신러닝
# ==========================================================

st.divider()

st.subheader("🤖 문화재 훼손 위험 머신러닝")


# ==========================================================
# 학습용 Target 컬럼 찾기
# ==========================================================

possible_targets = [

    "risk",

    "risk_level",

    "damage_risk",

    "damage",

    "damage_level",

    "위험도",

    "훼손위험",

    "훼손_위험",

    "훼손위험도"

]


target_column = None


for column in possible_targets:

    if column in df.columns:

        target_column = column

        break


# ==========================================================
# Target이 없는 경우
# ==========================================================

if target_column is None:

    st.info(
        "ℹ️ 현재 문화재 CSV에서 머신러닝 정답값(Target)을 찾지 못했습니다."
    )

    st.write(
        "현재 CSV 컬럼:"
    )

    st.code(
        ", ".join(df.columns.tolist())
    )

    st.warning(
        "실제 머신러닝을 학습하려면 "
        "각 문화재의 훼손 여부 또는 위험도와 같은 Target 컬럼이 필요합니다."
    )


# ==========================================================
# Target이 있는 경우
# ==========================================================

else:

    st.success(
        f"✅ 머신러닝 Target 컬럼 발견: `{target_column}`"
    )


    # ------------------------------------------------------
    # 사용할 Feature
    # ------------------------------------------------------

    feature_columns = [

        "temp",

        "humidity",

        "rainfall",

        "wind_speed",

        "pm10",

        "pm25",

        "o3",

        "no2",

        "co",

        "so2"

    ]


    # ------------------------------------------------------
    # 문화재 데이터에 환경 데이터가 있는지 확인
    # ------------------------------------------------------

    available_features = [

        column

        for column in feature_columns

        if column in df.columns

    ]


    if len(available_features) == 0:

        st.warning(
            "문화재 CSV에 머신러닝 Feature가 없습니다."
        )

    else:

        ml_df = df[
            available_features + [target_column]
        ].copy()


        # 숫자형 변환

        for column in available_features:

            ml_df[column] = pd.to_numeric(
                ml_df[column],
                errors="coerce"
            )


        ml_df = ml_df.dropna()


        # --------------------------------------------------
        # 데이터 확인
        # --------------------------------------------------

        if len(ml_df) < 10:

            st.warning(
                "머신러닝을 학습하기 위한 데이터가 너무 적습니다."
            )

        else:

            X = ml_df[
                available_features
            ]

            y = ml_df[
                target_column
            ]


            # ------------------------------------------------
            # Target 클래스 확인
            # ------------------------------------------------

            if y.nunique() < 2:

                st.warning(
                    "Target 값이 한 종류뿐이라 "
                    "분류 머신러닝을 학습할 수 없습니다."
                )

            else:

                # --------------------------------------------
                # 학습 / 테스트 분리
                # --------------------------------------------

                try:

                    X_train, X_test, y_train, y_test = train_test_split(

                        X,

                        y,

                        test_size=0.2,

                        random_state=42,

                        stratify=y

                    )

                except ValueError:

                    X_train, X_test, y_train, y_test = train_test_split(

                        X,

                        y,

                        test_size=0.2,

                        random_state=42

                    )


                # --------------------------------------------
                # Random Forest
                # --------------------------------------------

                model = RandomForestClassifier(

                    n_estimators=100,

                    random_state=42

                )


                model.fit(
                    X_train,
                    y_train
                )


                # --------------------------------------------
                # 정확도
                # --------------------------------------------

                prediction = model.predict(
                    X_test
                )


                accuracy = accuracy_score(
                    y_test,
                    prediction
                )


                st.metric(
                    "머신러닝 정확도",
                    f"{accuracy * 100:.1f}%"
                )


                # --------------------------------------------
                # 현재 환경 위험 예측
                # --------------------------------------------

                current_ml = environment_data[
                    available_features
                ].copy()


                # 결측치 처리

                current_ml = current_ml.fillna(
                    ml_df[available_features].median()
                )


                current_prediction = model.predict(
                    current_ml
                )[0]


                st.subheader(
                    "🔮 현재 환경 기반 예측"
                )


                st.success(
                    f"예측 결과: **{current_prediction}**"
                )


                # --------------------------------------------
                # Feature 중요도
                # --------------------------------------------

                importance_df = pd.DataFrame({

                    "환경 요인":
                        available_features,

                    "중요도":
                        model.feature_importances_

                }).sort_values(

                    "중요도",

                    ascending=False

                )


                st.subheader(
                    "📊 환경 요인 중요도"
                )


                st.bar_chart(
                    importance_df.set_index(
                        "환경 요인"
                    )
                )


# ==========================================================
# 데이터 미리보기
# ==========================================================

st.divider()

st.subheader("📊 문화재 데이터")

st.write(
    f"총 **{len(df)}개**의 문화재 데이터가 있습니다."
)


with st.expander(
    "문화재 데이터 미리보기"
):

    st.dataframe(
        df.head(20),
        use_container_width=True
    )


# ==========================================================
# API 원본 환경 데이터
# ==========================================================

with st.expander(
    "🌱 현재 수집된 환경 데이터"
):

    st.dataframe(
        environment_data,
        use_container_width=True
    )


# ==========================================================
# 하단
# ==========================================================

st.divider()

st.caption(
    "제6회 학생 SW·AI 인재양성 프로젝트 | "
    "선화여고 - 영천 헤리티지 AI 탐구단"
)
