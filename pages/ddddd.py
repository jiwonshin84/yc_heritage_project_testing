# ============================================================
# 0. 라이브러리
# ============================================================

import os
import time
import requests
import pandas as pd


# ============================================================
# 1. 기상청 ASOS API 설정
# ============================================================

# GitHub Secrets에 등록한 API 키 불러오기
ASOS_SERVICE_KEY = os.getenv("ASOS_SERVICE_KEY")

if not ASOS_SERVICE_KEY:
    raise ValueError(
        "ASOS_SERVICE_KEY가 설정되지 않았습니다. "
        "GitHub Secrets에 API 키를 등록해주세요."
    )


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

print("=" * 60)
print("영천 기상 데이터 수집 시작")
print("=" * 60)

all_years = []


for year in range(2016, 2026):

    df_year = fetch_asos_year(year)

    if not df_year.empty:
        all_years.append(df_year)

    # API 과부하 방지
    time.sleep(0.5)


# 데이터가 하나도 없는 경우
if not all_years:

    raise ValueError(
        "기상 데이터를 하나도 가져오지 못했습니다."
    )


weather_raw = pd.concat(
    all_years,
    ignore_index=True
)


print()
print(
    f"전체 기상 데이터 : "
    f"{len(weather_raw)}건"
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


print()
print("강수량 결측 처리 완료")

print(
    "강수량 결측 개수 :",
    weather["rainfall"].isna().sum()
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


print()
print("기상 데이터 정제 완료")

print(weather.head())


# ============================================================
# 9. 미세먼지 데이터 불러오기
# ============================================================

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

    raise ValueError(
        f"미세먼지 데이터를 불러오지 못했습니다 : {e}"
    )


air["date"] = pd.to_datetime(
    air["date"],
    errors="coerce"
)


print()
print(
    f"미세먼지 데이터 : "
    f"{len(air)}건"
)

print(air.head())


# ============================================================
# 10. 기상 + 미세먼지 데이터 병합
# ============================================================

df = pd.merge(

    weather,

    air,

    on="date",

    how="left"
)


print()
print(
    f"기상 + 미세먼지 병합 완료 : "
    f"{len(df)}건"
)


# ============================================================
# 11. 결측치 확인
# ============================================================

print()
print("=" * 60)
print("결측치 확인")
print("=" * 60)

print(
    df.isna().sum()
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
# 13. 완료
# ============================================================

print()
print("=" * 60)
print("데이터 수집 및 저장 완료")
print("=" * 60)

print(
    f"저장 위치 : {save_path}"
)

print(
    f"최종 데이터 크기 : "
    f"{df.shape[0]}행 × {df.shape[1]}열"
)
