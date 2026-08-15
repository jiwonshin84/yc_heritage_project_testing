# ============================================================
# 0. 라이브러리
# ============================================================

import os
import time
import requests
import pandas as pd
import streamlit as st  # Streamlit 라이브러리 추가

# 화면 타이틀 설정
st.title("☀️ 영천 기상 & 미세먼지 데이터 수집기")


# ============================================================
# 1. 기상청 ASOS API 설정
# ============================================================

# GitHub Secrets에 등록한 API 키 불러오기
ASOS_SERVICE_KEY = os.getenv("ASOS_SERVICE_KEY")

if not ASOS_SERVICE_KEY:
    ASOS_SERVICE_KEY = "feb2bfabd299d5d05e89c7aec49ba7e706112603e76549a92e868bd86ec60323"

ASOS_URL = (
    "http://apis.data.go.kr/"
    "1360000/AsosDalyInfoService/getWthrDataList"
)

# 영천 관측소
STN_ID = "281"


# ============================================================
# 2. 연도별 기상 데이터 수집 함수
# ============================================================

def fetch_asos_year(year):

    start_dt = f"{year}0101"
    end_dt = f"{year}1231"

    params = {
        "serviceKey": ASOS_SERVICE_KEY,

        "numOfRows": "400",
        "pageNo": "1",

        "dataType": "JSON",

        "dataCd": "ASOS",
        "dateCd": "DAY",

        "startDt": start_dt,
        "endDt": end_dt,

        "stnIds": STN_ID
    }

    try:

        response = requests.get(
            ASOS_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        items = result["response"]["body"]["items"]["item"]

        df = pd.DataFrame(items)

        print(
            f"{year}년 수집 완료 : "
            f"{len(df)}건"
        )

        return df

    except Exception as e:

        print(
            f"{year}년 수집 실패 : {e}"
        )

        return pd.DataFrame()


# ============================================================
# 3. 전체 기상 데이터 수집
# ============================================================

st.subheader("1. 기상 데이터 수집 중...")
progress_bar = st.progress(0)
status_text = st.empty()

all_years = []
years = list(range(2016, 2026))

for idx, year in enumerate(years):

    status_text.text(f"⏳ {year}년 기상 데이터 수집 중...")
    df_year = fetch_asos_year(year)

    if not df_year.empty:
        all_years.append(df_year)

    # 진행 바 업데이트
    progress_bar.progress((idx + 1) / len(years))

    # API 과부하 방지
    time.sleep(0.5)

status_text.text("✅ 연도별 기상 데이터 수집 완료!")


# 데이터가 하나도 없는 경우
if not all_years:

    st.error("기상 데이터를 하나도 가져오지 못했습니다.")
    raise ValueError(
        "기상 데이터를 하나도 가져오지 못했습니다."
    )


weather_raw = pd.concat(
    all_years,
    ignore_index=True
)


# ============================================================
# 4. 필요한 컬럼 추출
# ============================================================

weather = weather_raw[
    [
        "tm",

        # 기온
        "avgTa",
        "maxTa",
        "minTa",

        # 습도
        "avgRhm",

        # 강수량
        "sumRn",

        # 풍속
        "avgWs",

        # 일사량
        "sumSsHr",

        # 지면온도
        "avgTs"
    ]
].copy()


# ============================================================
# 5. 컬럼명 변경
# ============================================================

weather.columns = [

    "date",

    # 기온
    "temp_avg",
    "temp_max",
    "temp_min",

    # 습도
    "humidity",

    # 강수량
    "rainfall",

    # 풍속
    "wind_speed",

    # 일사량
    "solar_radiation",

    # 지면온도
    "ground_temp"
]


# ============================================================
# 6. 날짜 및 숫자 데이터 타입 변환
# ============================================================

weather["date"] = pd.to_datetime(
    weather["date"],
    errors="coerce"
)


numeric_cols = [

    "temp_avg",
    "temp_max",
    "temp_min",

    "humidity",

    "rainfall",

    "wind_speed",

    "solar_radiation",

    "ground_temp"
]


for col in numeric_cols:

    weather[col] = pd.to_numeric(
        weather[col],
        errors="coerce"
    )


# ============================================================
# 7. 강수량 결측값 처리
# ============================================================

weather["rainfall"] = (
    weather["rainfall"]
    .fillna(0)
)


# ============================================================
# 8. 정렬 및 결측 제거
# ============================================================

weather = (
    weather
    .dropna(subset=["date"])
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# 9. 미세먼지 데이터 불러오기
# ============================================================

st.subheader("2. 미세먼지 데이터 불러오기")

air_url = (
    "https://docs.google.com/spreadsheets/d/"
    "1fBEnheVOP-23Hmv_5ZJZVy6m9VmNkpVd2XutOdmlYc8/"
    "export?format=csv&gid=700055413"
)


try:

    air = pd.read_csv(
        air_url
    )

except Exception as e:

    st.error(f"미세먼지 데이터를 불러오지 못했습니다 : {e}")
    raise ValueError(
        f"미세먼지 데이터를 불러오지 못했습니다 : {e}"
    )


air["date"] = pd.to_datetime(
    air["date"],
    errors="coerce"
)


# ============================================================
# 10. 기상 + 미세먼지 데이터 병합
# ============================================================

df = pd.merge(

    weather,

    air,

    on="date",

    how="left"
)


# ============================================================
# 12. 데이터 저장
# ============================================================

# GitHub 프로젝트 내부에 data 폴더 생성
os.makedirs(
    "data",
    exist_ok=True
)


save_path = (
    "data/"
    "yeongcheon_2016_2025.csv"
)


df.to_csv(

    save_path,

    index=False,

    encoding="utf-8-sig"
)


# ============================================================
# 13. 완료 및 Streamlit 화면 출력
# ============================================================

st.success(f"🎉 데이터 수집 및 저장 완료! (총 {len(df)}건)")

# 요약 정보 표
col1, col2 = st.columns(2)
col1.metric("최종 행 수", f"{df.shape[0]} 행")
col2.metric("최종 열 수", f"{df.shape[1]} 열")

st.subheader("📊 최종 데이터 미리보기")
st.dataframe(df.head(10), use_container_width=True)

# 결측치 정보 보여주기
with st.expander("🔍 컬럼별 결측치(Null) 개수 확인"):
    st.dataframe(df.isna().sum().to_frame(name="결측치 수"))
