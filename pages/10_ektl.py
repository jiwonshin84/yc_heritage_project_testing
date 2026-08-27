import streamlit as st

# ============================================================
# 0. Streamlit 레이아웃 설정 (페이지 최상단 위치 필수)
# ============================================================
try:
    st.set_page_config(
        page_title="영천 문화재 위험도 예측 시스템",
        page_layout="wide"
    )
except Exception:
    pass

import itertools
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import requests

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ============================================================
# Matplotlib 한글 폰트 설정
# ============================================================
def set_korean_font():
    system_name = platform.system()
    if system_name == "Windows":
        plt.rc('font', family='Malgun Gothic')
    elif system_name == "Darwin":
        plt.rc('font', family='AppleGothic')
    else:
        font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
        
        if not os.path.exists(font_path):
            try:
                subprocess.run(["apt-get", "update"], check=False)
                subprocess.run(["apt-get", "install", "-y", "fonts-nanum"], check=False)
            except Exception:
                pass
                
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            plt.rc('font', family=font_prop.get_name())
            fm.fontManager.addfont(font_path)
        else:
            plt.rc('font', family='DejaVu Sans')
            
    plt.rc('axes', unicode_minus=False)

set_korean_font()

st.title("영천시 문화재 환경 위험도 실시간 예측 시스템")

# ============================================================
# 1. 기상청 ASOS API
# ============================================================
ASOS_SERVICE_KEY = (
    "feb2bfabd299d5d05e89c7aec49ba7e706112603e76549a92e868bd86ec60323"
)
ASOS_URL = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
STN_ID = "281"  # 영천 관측소

def fetch_asos_year(year):
    current_year = datetime.now().year
    start_dt = f"{year}0101"
    
    if year == current_year:
        end_dt = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    else:
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
        "stnIds": STN_ID,
    }
    try:
        response = requests.get(ASOS_URL, params=params, timeout=7)
        result = response.json()
        
        if "response" in result and "body" in result["response"] and "items" in result["response"]["body"]:
            items = result["response"]["body"]["items"]["item"]
            return pd.DataFrame(items)
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ============================================================
# 2. 데이터 수집, 가공 및 대체(Mock) 데이터 방어 로직
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_data():
    all_years = []
    current_year = datetime.now().year
    years = list(range(2016, current_year + 1))
    
    progress_text = "기상청 과거 데이터 수집 중..."
    my_bar = st.progress(0, text=progress_text)

    for idx, year in enumerate(years):
        df_year = fetch_asos_year(year)
        if not df_year.empty:
            all_years.append(df_year)
        my_bar.progress(int((idx + 1) / len(years) * 100), text=f"기상 데이터 수집 중... ({year}년)")

    my_bar.empty()

    if all_years:
        weather_raw = pd.concat(all_years, ignore_index=True)
    else:
        st.warning("⚠️ 기상청 API 과거 데이터 연결 실패로 인해 임시 학습 데이터로 실행합니다.")
        dates = pd.date_range(start="2023-01-01", end="2025-12-31", freq="D")
        weather_raw = pd.DataFrame({
            "tm": dates.strftime("%Y-%m-%d"),
            "avgTa": np.random.uniform(10, 25, len(dates)),
            "maxTa": np.random.uniform(20, 32, len(dates)),
            "minTa": np.random.uniform(0, 15, len(dates)),
            "avgRhm": np.random.uniform(40, 85, len(dates)),
            "sumRn": np.random.choice([0, 0, 0, 5, 12, 30], len(dates)),
            "avgWs": np.random.uniform(1, 5, len(dates)),
            "sumSsHr": np.random.uniform(5, 12, len(dates)),
            "avgTs": np.random.uniform(10, 28, len(dates)),
        })

    if "tm" in weather_raw.columns:
        weather = weather_raw[
            ["tm", "avgTa", "maxTa", "minTa", "avgRhm", "sumRn", "avgWs", "sumSsHr", "avgTs"]
        ].copy()
    else:
        weather = pd.DataFrame(
            columns=["tm", "avgTa", "maxTa", "minTa", "avgRhm", "sumRn", "avgWs", "sumSsHr", "avgTs"]
        )

    weather.columns = [
        "date", "temp_avg", "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", "solar_radiation", "ground_temp"
    ]

    weather["date"] = pd.to_datetime(weather["date"], errors="coerce")
    numeric_cols = [
        "temp_avg", "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", "solar_radiation", "ground_temp"
    ]
    for col in numeric_cols:
        weather[col] = pd.to_numeric(weather[col], errors="coerce")

    weather["rainfall"] = weather["rainfall"].fillna(0)
    weather = weather.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    air_url = "https://docs.google.com/spreadsheets/d/1fBEnheVOP-23Hmv_5ZJZVy6m9VmNkpVd2XutOdmlYc8/export?format=csv&gid=700055413"
    try:
        air = pd.read_csv(air_url)
        air["date"] = pd.to_datetime(air["date"], errors="coerce")
    except Exception:
        air = pd.DataFrame(columns=["date", "pm10", "pm25", "o3", "no2", "co", "so2"])

    df = pd.merge(weather, air, on="date", how="left")

    air_cols = ["pm10", "pm25", "o3", "no2", "co", "so2"]
    for col in air_cols:
        if col not in df.columns:
            df[col] = 0.0

    df["temp_range"] = df["temp_max"] - df["temp_min"]
    df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std()
    df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()
    df["high_humidity_risk"] = (df["humidity"] >= 75).rolling(3, min_periods=1).sum()
    df["weathering_risk"] = (df["temp_range"] * 0.4 + df["humidity_std3"] * 0.3 + df["wind_speed"] * 0.3)
    df["mold_risk"] = ((df["humidity"] >= 75) & (df["ground_temp"] >= 15)).astype(int)
    df["pm_load"] = (df["pm10"] + df["pm25"]).rolling(3, min_periods=1).sum()
    df["acid_risk"] = df["so2"] * 0.6 + df["no2"] * 0.4
    df["oxidation_risk"] = df["o3"] * 0.7 + df["pm25"] * 0.3
    df["corrosion_risk"] = df["humidity"] * 0.5 + df["so2"] * 0.5
    df = df.fillna(0)

    materials = ["석조", "목조", "금속", "회화", "기타"]
    exposures = ["실외", "반실외", "실내"]
    comb = pd.DataFrame(list(itertools.product(materials, exposures)), columns=["material", "exposure"])

    df["key"] = 1
    comb["key"] = 1
    dataset = pd.merge(df, comb, on="key").drop("key", axis=1)

    norm_targets = [
        "weathering_risk", "acid_risk", "rainfall_7d", "temp_range", "pm_load",
        "corrosion_risk", "mold_risk", "humidity_std3", "high_humidity_risk", "oxidation_risk"
    ]
    for target in norm_targets:
        min_v = dataset[target].min()
        max_v = dataset[target].max()
        if max_v - min_v == 0:
            dataset[f"{target}_norm"] = 0
        else:
            dataset[f"{target}_norm"] = (dataset[target] - min_v) / (max_v - min_v)

    def calc_risk(row):
        m = row["material"]
        e = row["exposure"]

        if m == "석조":
            r = (row["weathering_risk_norm"] * 0.25 + row["acid_risk_norm"] * 0.20 + row["rainfall_7d_norm"] * 0.18 + row["temp_range_norm"] * 0.15 + row["pm_load_norm"] * 0.12 + row["corrosion_risk_norm"] * 0.10)
        elif m == "목조":
            r = (row["mold_risk_norm"] * 0.25 + row["humidity_std3_norm"] * 0.20 + row["high_humidity_risk_norm"] * 0.18 + row["rainfall_7d_norm"] * 0.15 + row["oxidation_risk_norm"] * 0.12 + row["pm_load_norm"] * 0.10)
        elif m == "금속":
            r = (row["corrosion_risk_norm"] * 0.30 + row["acid_risk_norm"] * 0.22 + row["high_humidity_risk_norm"] * 0.18 + row["humidity_std3_norm"] * 0.12 + row["pm_load_norm"] * 0.10 + row["weathering_risk_norm"] * 0.08)
        elif m == "회화":
            r = (row["oxidation_risk_norm"] * 0.28 + row["pm_load_norm"] * 0.20 + row["humidity_std3_norm"] * 0.18 + row["high_humidity_risk_norm"] * 0.14 + row["temp_range_norm"] * 0.10 + row["weathering_risk_norm"] * 0.10)
        else:
            r = (row["weathering_risk_norm"] * 0.2 + row["acid_risk_norm"] * 0.2 + row["oxidation_risk_norm"] * 0.2 + row["corrosion_risk_norm"] * 0.2 + row["pm_load_norm"] * 0.2)

        if e == "실외":
            r *= 1.3
        elif e == "반실외":
            r *= 1.1
        else:
            r *= 0.85

        return min(r * 100, 100)

    dataset["material_risk"] = dataset.apply(calc_risk, axis=1)

    q75 = dataset["material_risk"].quantile(0.75)
    q40 = dataset["material_risk"].quantile(0.40)

    def label(x):
        if x >= q75:
            return "위험"
        elif x >= q40:
            return "주의"
        else:
            return "안전"

    dataset["target"] = dataset["material_risk"].apply(label)
    return dataset, air_url

dataset, air_url = load_and_process_data()

# ============================================================
# 3. 머신러닝 데이터 학습
# ============================================================
X = dataset[
    [
        "temp_avg", "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", "solar_radiation", "ground_temp",
        "pm10", "pm25", "o3", "no2", "co", "so2", "temp_range", "humidity_std3", "rainfall_7d", "high_humidity_risk",
        "weathering_risk", "mold_risk", "pm_load", "acid_risk", "oxidation_risk", "corrosion_risk", "material", "exposure"
    ]
]

y = dataset["target"]
X = pd.get_dummies(X, columns=["material", "exposure"])

mask_notna = y.notna()
X_clean = X[mask_notna]
y_clean = y[mask_notna]

class_counts = y_clean.value_counts()
valid_classes = class_counts[class_counts >= 2].index
mask_valid = y_clean.isin(valid_classes)

X_filtered = X_clean[mask_valid]
y_filtered = y_clean[mask_valid]

min_class_count = y_filtered.value_counts().min() if not y_filtered.empty else 0
use_stratify = y_filtered if min_class_count >= 2 else None

X_train, X_test, y_train, y_test = train_test_split(
    X_filtered, 
    y_filtered, 
    test_size=0.2, 
    random_state=42, 
    stratify=use_stratify
)

rf_model = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)
y_pred = rf_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

st.sidebar.subheader("모델 성능")
st.sidebar.text(f"RandomForest 정확도: {acc:.4f}")

# ============================================================
# 4. 전체 환경 요인 중요도 TOP 10
# ============================================================
feature_cols = [
    c for c in X_train.columns if not c.startswith("material_") and not c.startswith("exposure_")
]

importance_df = pd.DataFrame({
    "Feature": X_train.columns,
    "Importance": rf_model.feature_importances_
})

importance_df = (
    importance_df[importance_df["Feature"].isin(feature_cols)]
    .sort_values("Importance", ascending=False)
    .head(10)
    .reset_index(drop=True)
)

st.subheader("전체 환경 요인 중요도 TOP 10")
st.dataframe(importance_df, use_container_width=True)

# ============================================================
# 5. 재질별 환경 요인 중요도 차트
# ============================================================
st.header("재질별 주요 환경 위험요인 TOP 10")

env_features = [
    "temp_avg", "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", "solar_radiation", "ground_temp",
    "pm10", "pm25", "o3", "no2", "co", "so2", "temp_range", "humidity_std3", "rainfall_7d", "high_humidity_risk",
    "weathering_risk", "mold_risk", "pm_load", "acid_risk", "oxidation_risk", "corrosion_risk"
]

materials_list = ["석조", "목조", "금속", "회화"]
cols = st.columns(2)

for idx, material in enumerate(materials_list):
    sub_df = dataset[dataset["material"] == material]

    if len(sub_df) >= 30:
        X_sub = sub_df[env_features]
        y_sub = sub_df["target"]

        if len(y_sub.unique()) > 1:
            try:
                rf_sub = RandomForestClassifier(n_estimators=300, random_state=42)
                rf_sub.fit(X_sub, y_sub)

                imp_df = (
                    pd.DataFrame({"Feature": env_features, "Importance": rf_sub.feature_importances_})
                    .sort_values("Importance", ascending=False)
                    .head(10)
                )

                fig, ax = plt.subplots(figsize=(6, 3.5))
                ax.barh(imp_df["Feature"][::-1], imp_df["Importance"][::-1], color="#2b5c8f")
                ax.set_title(f"[{material}] 문화재 위험요인 TOP 10", fontsize=11)
                ax.set_xlabel("Importance")
                plt.tight_layout()

                with cols[idx % 2]:
                    st.pyplot(fig)
                    plt.close(fig)
            except Exception:
                pass

# ============================================================
# 6. 영천시 문화재 실시간 위험도 예측 (안전 예외 처리 적용)
# ============================================================
st.header("영천시 문화재 실시간 위험등급 예측")

heritage_path = "영천_문화재_특성데이터셋.csv"
try:
    heritage_df = pd.read_csv(heritage_path)
except FileNotFoundError:
    heritage_path_colab = "/content/drive/MyDrive/00. 2026학년도 인재양성프로젝트/공공데이터 기반 프로젝트/dataset/영천_문화재_특성데이터셋.csv"
    try:
        heritage_df = pd.read_csv(heritage_path_colab)
    except FileNotFoundError:
        heritage_df = pd.DataFrame(
            {
                "문화재명(국문)": ["영천 은해사 거조암 영산전", "영천 청제비", "영천 신월리 삼층석탑"],
                "재질": ["목조", "석조", "석조"],
                "노출형태": ["반실외", "실외", "실외"],
            }
        )

end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=6)

params = {
    "serviceKey": ASOS_SERVICE_KEY,
    "numOfRows": "20",
    "pageNo": "1",
    "dataType": "JSON",
    "dataCd": "ASOS",
    "dateCd": "DAY",
    "startDt": start_date.strftime("%Y%m%d"),
    "endDt": end_date.strftime("%Y%m%d"),
    "stnIds": STN_ID,
}

# --- 실시간 API 호출 안전 처리 ---
try:
    response = requests.get(ASOS_URL, params=params, timeout=7)
    items = response.json()["response"]["body"]["items"]["item"]
    weather_recent = pd.DataFrame(items)
except Exception:
    st.warning("⚠️ 실시간 기상 API 접속 시간이 초과되어 최근 표준 기상 데이터(임시)로 실시간 예측을 구동합니다.")
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    weather_recent = pd.DataFrame({
        "tm": dates.strftime("%Y-%m-%d"),
        "avgTa": [22.0] * len(dates),
        "maxTa": [28.0] * len(dates),
        "minTa": [17.0] * len(dates),
        "avgRhm": [65.0] * len(dates),
        "sumRn": [0.0] * len(dates),
        "avgWs": [2.1] * len(dates),
        "sumSsHr": [8.0] * len(dates),
        "avgTs": [23.5] * len(dates)
    })

weather_recent = weather_recent[["tm", "avgTa", "maxTa", "minTa", "avgRhm", "sumRn", "avgWs", "sumSsHr", "avgTs"]].copy()
weather_recent.columns = ["date", "temp_avg", "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", "solar_radiation", "ground_temp"]
weather_recent["date"] = pd.to_datetime(weather_recent["date"])
for c in weather_recent.columns[1:]:
    weather_recent[c] = pd.to_numeric(weather_recent[c], errors="coerce")

try:
    air_recent = pd.read_csv(air_url)
    air_recent["date"] = pd.to_datetime(air_recent["date"])
    air_recent = air_recent[air_recent["date"].between(start_date, end_date)]
except Exception:
    air_recent = pd.DataFrame(columns=["date", "pm10", "pm25", "o3", "no2", "co", "so2"])

recent_df = pd.merge(weather_recent, air_recent, on="date", how="left").sort_values("date").ffill().fillna(0)

# 대기 정보 열이 빠져있는 경우 예외 채우기
for col in ["pm10", "pm25", "o3", "no2", "co", "so2"]:
    if col not in recent_df.columns:
        recent_df[col] = 0.0

latest = recent_df.iloc[-1]

temp_range = latest["temp_max"] - latest["temp_min"]
humidity_std3 = recent_df["humidity"].tail(3).std()
if pd.isna(humidity_std3): humidity_std3 = 0
rainfall_7d = recent_df["rainfall"].sum()
high_humidity_risk = int(latest["humidity"] >= 75)
weathering_risk = temp_range * 0.4 + humidity_std3 * 0.3 + latest["wind_speed"] * 0.3
mold_risk = int((latest["humidity"] >= 75) and (latest["ground_temp"] >= 15))
pm_load = latest["pm10"] + latest["pm25"]
acid_risk = latest["so2"] * 0.6 + latest["no2"] * 0.4
oxidation_risk = latest["o3"] * 0.7 + latest["pm25"] * 0.3
corrosion_risk = latest["humidity"] * 0.5 + latest["so2"] * 0.5

st.subheader("실시간 수집 기상/대기 요약")
env_df = pd.DataFrame([{
    "기준일자": latest["date"].strftime("%Y-%m-%d"),
    "평균기온(℃)": latest["temp_avg"],
    "습도(%)": latest["humidity"],
    "강수량(mm)": latest["rainfall"],
    "미세먼지(PM10)": latest["pm10"],
    "초미세먼지(PM2.5)": latest["pm25"]
}])
st.dataframe(env_df, use_container_width=True)

results = []
for _, heritage in heritage_df.iterrows():
    predict_df = pd.DataFrame([{
        "temp_avg": latest["temp_avg"], "temp_max": latest["temp_max"], "temp_min": latest["temp_min"],
        "humidity": latest["humidity"], "rainfall": latest["rainfall"], "wind_speed": latest["wind_speed"],
        "solar_radiation": latest["solar_radiation"], "ground_temp": latest["ground_temp"],
        "pm10": latest["pm10"], "pm25": latest["pm25"], "o3": latest["o3"], "no2": latest["no2"],
        "co": latest["co"], "so2": latest["so2"], "temp_range": temp_range, "humidity_std3": humidity_std3,
        "rainfall_7d": rainfall_7d, "high_humidity_risk": high_humidity_risk, "weathering_risk": weathering_risk,
        "mold_risk": mold_risk, "pm_load": pm_load, "acid_risk": acid_risk, "oxidation_risk": oxidation_risk,
        "corrosion_risk": corrosion_risk, "material": heritage["재질"], "exposure": heritage["노출형태"]
    }])

    predict_df = pd.get_dummies(predict_df, columns=["material", "exposure"])
    predict_df = predict_df.reindex(columns=X_train.columns, fill_value=0)

    prediction = rf_model.predict(predict_df)[0]
    results.append([heritage["문화재명(국문)"], heritage["재질"], heritage["노출형태"], prediction])

result_df = pd.DataFrame(results, columns=["문화재명", "재질", "노출형태", "예측위험등급"])

st.subheader("예측 위험등급 분포")
counts = result_df["예측위험등급"].value_counts().reindex(["위험", "주의", "안전"], fill_value=0)

fig, ax = plt.subplots(figsize=(7, 3.5))
colors = {"위험": "#d9534f", "주의": "#f0ad4e", "안전": "#5cb85c"}
bar_colors = [colors[x] for x in counts.index]

bars = ax.bar(counts.index, counts.values, color=bar_colors, edgecolor="black", width=0.4)
ax.set_title("영천시 문화재 위험등급별 수량", fontsize=12, pad=10)
ax.set_ylabel("수량 (개)", fontsize=10)

for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.markdown("---")
for level in ["위험", "주의", "안전"]:
    sub_df = result_df[result_df["예측위험등급"] == level].copy()
    
    st.subheader(f"[{level} 등급] 문화재 목록 (총 {len(sub_df)}건)")

    if len(sub_df) > 0:
        display_df = sub_df[["문화재명", "재질", "노출형태"]].reset_index(drop=True)
        display_df.index = display_df.index + 1
        display_df.index.name = "번호"
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info(f"현재 기상 조건상 '{level}' 등급에 해당되는 문화재가 없습니다.")
