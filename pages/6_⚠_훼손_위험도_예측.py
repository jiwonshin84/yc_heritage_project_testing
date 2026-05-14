import streamlit as st
import pandas as pd
import numpy as np
import requests
import os

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sklearn.ensemble import RandomForestClassifier

# ==========================================================
# 0. 설정 및 API 키
# ==========================================================
st.set_page_config(
    page_title="영천 지역 문화재 훼손 위험 예측",
    page_icon="🏛",
    layout="wide"
)

SERVICE_KEY = "YOUR_SERVICE_KEY"

now = datetime.now(ZoneInfo("Asia/Seoul"))
yesterday = now - timedelta(days=1)

base_date = yesterday.strftime("%Y%m%d")
base_hour = "23"

if 'danger_count' not in st.session_state:
    st.session_state['danger_count'] = 0

# ==========================================================
# 1. 모델 학습 로직
# ==========================================================
@st.cache_resource
def train_heritage_model():

    weather_path = "data/processed/[2016_2025] yeongcheon_weather_daily.csv"
    air_path = "data/processed/[2019_2025] air_quality.csv"

    if not os.path.exists(weather_path) or not os.path.exists(air_path):
        return None, None

    # ------------------------------------------------------
    # 데이터 로드
    # ------------------------------------------------------
    w_df = pd.read_csv(weather_path)
    a_df = pd.read_csv(air_path)

    w_df = w_df.rename(columns={
        'avg_temperature_c': 'temp',
        'daily_precipitation_mm': 'rainfall',
        'avg_wind_speed_ms': 'wind',
        'avg_relative_humidity_pct': 'humidity'
    })

    df = pd.merge(w_df, a_df, on='date', how='inner')

    df = df.ffill()

    # ======================================================
    # 2. 파생변수 생성
    # ======================================================

    # ---------------------------
    # 변화량
    # ---------------------------
    df["temp_change"] = df["temp"].diff().fillna(0)
    df["humidity_change"] = df["humidity"].diff().fillna(0)

    # ---------------------------
    # 이슬점 / 결로
    # ---------------------------
    df["dew_point"] = df["temp"] - ((100 - df["humidity"]) / 5)
    df["dew_gap"] = df["temp"] - df["dew_point"]

    # ---------------------------
    # 이동평균
    # ---------------------------
    df["humidity_ma3"] = (
        df["humidity"]
        .rolling(3)
        .mean()
        .fillna(df["humidity"])
    )

    df["pm10_ma3"] = (
        df["pm10"]
        .rolling(3)
        .mean()
        .fillna(df["pm10"])
    )

    # ---------------------------
    # 변동성
    # ---------------------------
    df["temp_std"] = (
        df["temp"]
        .rolling(3)
        .std()
        .fillna(0)
    )

    df["humidity_std"] = (
        df["humidity"]
        .rolling(3)
        .std()
        .fillna(0)
    )

    # ---------------------------
    # 결로 위험
    # ---------------------------
    df["condensation_risk"] = df["dew_gap"].apply(
        lambda x: 1 if x < 2 else (0.5 if x < 5 else 0)
    )

    # ---------------------------
    # 곰팡이 위험
    # ---------------------------
    df["mold_risk"] = (
        (df["humidity"] >= 75)
        .rolling(3)
        .sum()
        >= 2
    ).astype(int)

    # ---------------------------
    # 미세먼지 누적
    # ---------------------------
    df["pm_load"] = (
        (df["pm10"] + df["pm25"])
        .rolling(3)
        .sum()
        .fillna(0)
    )

    # ======================================================
    # 위험도 분류 함수
    # ======================================================

    def classify_humidity(h):
        if h >= 75 or h < 35:
            return 2
        elif h >= 65 or h < 45:
            return 1
        else:
            return 0

    def classify_temp(t):
        if t > 30 or t < 5:
            return 2
        elif t > 25 or t < 15:
            return 1
        else:
            return 0

    def classify_dew(d):
        if d < 2:
            return 2
        elif d < 5:
            return 1
        else:
            return 0

    def classify_pm10(p):
        if p >= 80:
            return 2
        elif p >= 30:
            return 1
        else:
            return 0

    def classify_temp_change(tc):
        if abs(tc) >= 10:
            return 2
        elif abs(tc) >= 5:
            return 1
        else:
            return 0

    def classify_humidity_change(hc):
        if abs(hc) >= 30:
            return 2
        elif abs(hc) >= 15:
            return 1
        else:
            return 0

    # ======================================================
    # 변수별 위험등급
    # ======================================================

    df["grade_humidity"] = df["humidity"].apply(classify_humidity)
    df["grade_temp"] = df["temp"].apply(classify_temp)
    df["grade_dew"] = df["dew_gap"].apply(classify_dew)
    df["grade_pm10"] = df["pm10"].apply(classify_pm10)
    df["grade_temp_change"] = df["temp_change"].apply(classify_temp_change)
    df["grade_humidity_change"] = df["humidity_change"].apply(classify_humidity_change)

    # ======================================================
    # 가중 위험지수
    # ======================================================

    df["weighted_risk"] = (
        df["grade_humidity"] * 0.30 +
        df["grade_temp"] * 0.20 +
        df["grade_dew"] * 0.20 +
        df["grade_pm10"] * 0.15 +
        df["grade_temp_change"] * 0.10 +
        df["grade_humidity_change"] * 0.05
    )

    # ======================================================
    # 최종 위험등급
    # ======================================================

    def final_classify(score):
        if score >= 1.2:
            return 2
        elif score >= 0.5:
            return 1
        else:
            return 0

    df["risk"] = df["weighted_risk"].apply(final_classify)

    # ======================================================
    # 문화재 정보
    # ======================================================

    mats = {
        '목조':0,
        '석조':1,
        '금속':2,
        '벽화':3,
        '기타':4
    }

    exps = {
        '실외':0,
        '실내':1,
        '반실외':2
    }

    # ======================================================
    # 학습 데이터 생성
    # ======================================================

    train_rows = []

    for _, r in df.tail(1200).iterrows():

        for m_name, m_code in mats.items():

            for e_name, e_code in exps.items():

                train_rows.append({

                    # 기본 변수
                    'temp': r['temp'],
                    'humidity': r['humidity'],
                    'rainfall': r['rainfall'],
                    'wind': r['wind'],
                    'pm10': r['pm10'],
                    'pm25': r['pm25'],
                    'so2': r['so2'],
                    'no2': r['no2'],
                    'co': r['co'],
                    'o3': r['o3'],

                    # 파생변수
                    'temp_change': r['temp_change'],
                    'humidity_change': r['humidity_change'],
                    'dew_gap': r['dew_gap'],
                    'humidity_ma3': r['humidity_ma3'],
                    'pm10_ma3': r['pm10_ma3'],
                    'temp_std': r['temp_std'],
                    'humidity_std': r['humidity_std'],
                    'condensation_risk': r['condensation_risk'],
                    'mold_risk': r['mold_risk'],
                    'pm_load': r['pm_load'],

                    # 문화재 변수
                    'mat_code': m_code,
                    'exp_code': e_code,

                    # 타겟
                    'target': r['risk']
                })

    tdf = pd.DataFrame(train_rows)

    # ======================================================
    # 모델 feature
    # ======================================================

    features = [

        'temp',
        'humidity',
        'rainfall',
        'wind',

        'pm10',
        'pm25',
        'so2',
        'no2',
        'co',
        'o3',

        # 파생변수
        'temp_change',
        'humidity_change',
        'dew_gap',
        'humidity_ma3',
        'pm10_ma3',
        'temp_std',
        'humidity_std',
        'condensation_risk',
        'mold_risk',
        'pm_load',

        # 문화재 변수
        'mat_code',
        'exp_code'
    ]

    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42
    )

    model.fit(
        tdf[features].fillna(0),
        tdf['target']
    )

    return model, features


ai_model, feature_names = train_heritage_model()

# ==========================================================
# 2. 실시간 데이터 수집
# ==========================================================

tm, temp, humidity, rainfall, wind_speed = "-", "-", "-", "-", "-"

try:

    asos_params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": "1",
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "HR",
        "startDt": base_date,
        "startHh": base_hour,
        "endDt": base_date,
        "endHh": base_hour,
        "stnIds": "281"
    }

    res = requests.get(
        "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList",
        params=asos_params,
        timeout=10
    ).json()

    item = res["response"]["body"]["items"]["item"][0]

    tm = item["tm"]
    temp = item["ta"]
    humidity = item["hm"]
    rainfall = item["rn"]
    wind_speed = item["ws"]

except:
    pass

pm10, pm25, o3, no2, co, so2, data_time = "-", "-", "-", "-", "-", "-", "-"

try:

    air_params = {
        "serviceKey": SERVICE_KEY,
        "returnType": "json",
        "numOfRows": "100",
        "sidoName": "경북",
        "ver": "1.0"
    }

    res = requests.get(
        "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty",
        params=air_params,
        timeout=10
    ).json()

    target = next(
        (
            i for i in res["response"]["body"]["items"]
            if "영천" in i["stationName"]
        ),
        None
    )

    if target:
        pm10 = target["pm10Value"]
        pm25 = target["pm25Value"]
        o3 = target["o3Value"]
        no2 = target["no2Value"]
        co = target["coValue"]
        so2 = target["so2Value"]
        data_time = target["dataTime"]

except:
    pass
