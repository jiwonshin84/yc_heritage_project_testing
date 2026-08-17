import itertools
import json
import time
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

import streamlit as st
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 한글 폰트 설정
try:
    import koreanize_matplotlib
except ImportError:
    pass

# ============================================================
# Streamlit 기본 레이아웃 설정
# ============================================================
st.set_page_config(
    page_title="영천 문화재 위험도 예측 시스템", page_layout="wide"
)
st.title("🏛️ 영천시 문화재 환경 위험도 실시간 예측 시스템")

# ============================================================
# 1. 기상청 ASOS API 설정
# ============================================================
ASOS_SERVICE_KEY = (
    "feb2bfabd299d5d05e89c7aec49ba7e706112603e76549a92e868bd86ec60323"
)
ASOS_URL = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
STN_ID = "281"  # 영천 관측소


@st.cache_data
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
        "stnIds": STN_ID,
    }
    try:
        response = requests.get(ASOS_URL, params=params, timeout=30)
        result = response.json()
        items = result["response"]["body"]["items"]["item"]
        df = pd.DataFrame(items)
        return df
    except Exception as e:
        return pd.DataFrame()


# ============================================================
# 2. 데이터 수집 및 파생변수 생성 (캐싱 적용)
# ============================================================
@st.cache_data
def load_and_process_data():
    all_years = []
    for year in range(2016, 2026):
        df_year = fetch_asos_year(year)
        all_years.append(df_year)
        time.sleep(0.1)

    weather_raw = pd.concat(all_years, ignore_index=True)

    weather = weather_raw[
        [
            "tm",
            "avgTa",
            "maxTa",
            "minTa",
            "avgRhm",
            "sumRn",
            "avgWs",
            "sumSsHr",
            "avgTs",
        ]
    ].copy()
    weather.columns = [
        "date",
        "temp_avg",
        "temp_max",
        "temp_min",
        "humidity",
        "rainfall",
        "wind_speed",
        "solar_radiation",
        "ground_temp",
    ]

    weather["date"] = pd.to_datetime(weather["date"], errors="coerce")
    numeric_cols = [
        "temp_avg",
        "temp_max",
        "temp_min",
        "humidity",
        "rainfall",
        "wind_speed",
        "solar_radiation",
        "ground_temp",
    ]
    for col in numeric_cols:
        weather[col] = pd.to_numeric(weather[col], errors="coerce")

    weather["rainfall"] = weather["rainfall"].fillna(0)
    weather = (
        weather.dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    air_url = "https://docs.google.com/spreadsheets/d/1fBEnheVOP-23Hmv_5ZJZVy6m9VmNkpVd2XutOdmlYc8/export?format=csv&gid=700055413"
    air = pd.read_csv(air_url)
    air["date"] = pd.to_datetime(air["date"], errors="coerce")

    df = pd.merge(weather, air, on="date", how="left")

    # 파생변수 생성
    df["temp_range"] = df["temp_max"] - df["temp_min"]
    df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std()
    df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()
    df["high_humidity_risk"] = (
        (df["humidity"] >= 75).rolling(3, min_periods=1).sum()
    )
    df["weathering_risk"] = (
        df["temp_range"] * 0.4
        + df["humidity_std3"] * 0.3
        + df["wind_speed"] * 0.3
    )
    df["mold_risk"] = (
        (df["humidity"] >= 75) & (df["ground_temp"] >= 15)
    ).astype(int)
    df["pm_load"] = (df["pm10"] + df["pm25"]).rolling(3, min_periods=1).sum()
    df["acid_risk"] = df["so2"] * 0.6 + df["no2"] * 0.4
    df["oxidation_risk"] = df["o3"] * 0.7 + df["pm25"] * 0.3
    df["corrosion_risk"] = df["humidity"] * 0.5 + df["so2"] * 0.5
    df = df.fillna(0)

    # 재질 x 노출 조합 생성
    materials = ["석조", "목조", "금속", "회화", "기타"]
    exposures = ["실외", "반실외", "실내"]
    comb = pd.DataFrame(
        list(itertools.product(materials, exposures)),
        columns=["material", "exposure"],
    )

    df["key"] = 1
    comb["key"] = 1
    dataset = pd.merge(df, comb, on="key").drop("key", axis=1)

    # 정규화 (calc_risk용 _norm 컬럼 생성)
    risk_cols = [
        "weathering_risk",
        "acid_risk",
        "rainfall_7d",
        "temp_range",
        "pm_load",
        "corrosion_risk",
        "mold_risk",
        "humidity_std3",
        "high_humidity_risk",
        "oxidation_risk",
    ]
    for col in risk_cols:
        min_val = dataset[col].min()
        max_val = dataset[col].max()
        if max_val - min_val == 0:
            dataset[f"{col}_norm"] = 0
        else:
            dataset[f"{col}_norm"] = (dataset[col] - min_val) / (
                max_val - min_val
            )

    def calc_risk(row):
        m = row["material"]
        e = row["exposure"]

        if m == "석조":
            r = (
                row["weathering_risk_norm"] * 0.25
                + row["acid_risk_norm"] * 0.20
                + row["rainfall_7d_norm"] * 0.18
                + row["temp_range_norm"] * 0.15
                + row["pm_load_norm"] * 0.12
                + row["corrosion_risk_norm"] * 0.10
            )
        elif m == "목조":
            r = (
                row["mold_risk_norm"] * 0.25
                + row["humidity_std3_norm"] * 0.20
                + row["high_humidity_risk_norm"] * 0.18
                + row["rainfall_7d_norm"] * 0.15
                + row["oxidation_risk_norm"] * 0.12
                + row["pm_load_norm"] * 0.10
            )
        elif m == "금속":
            r = (
                row["corrosion_risk_norm"] * 0.30
                + row["acid_risk_norm"] * 0.22
                + row["high_humidity_risk_norm"] * 0.18
                + row["humidity_std3_norm"] * 0.12
                + row["pm_load_norm"] * 0.10
                + row["weathering_risk_norm"] * 0.08
            )
        elif m == "회화":
            r = (
                row["oxidation_risk_norm"] * 0.28
                + row["pm_load_norm"] * 0.20
                + row["humidity_std3_norm"] * 0.18
                + row["high_humidity_risk_norm"] * 0.14
                + row["temp_range_norm"] * 0.10
                + row["weathering_risk_norm"] * 0.10
            )
        else:
            r = (
                row["weathering_risk_norm"] * 0.2
                + row["acid_risk_norm"] * 0.2
                + row["oxidation_risk_norm"] * 0.2
                + row["corrosion_risk_norm"] * 0.2
                + row["pm_load_norm"] * 0.2
            )

        if e == "실외":
            r *= 1.3
        elif e == "반실외":
            r *= 1.1
        else:
            r *= 0.85

        return min(r * 100, 100)

    dataset["material_risk"] = dataset.apply(calc_risk, axis=1)

    def label(x):
        if x >= 80:
            return "위험"
        elif x >= 40:
            return "주의"
        else:
            return "안전"

    dataset["target"] = dataset["material_risk"].apply(label)
    return dataset, air_url


dataset, air_url = load_and_process_data()

# ============================================================
# 3. 모델 학습 및 최적 모델 자동 선정
# ============================================================
X = dataset[
    [
        "temp_avg",
        "temp_max",
        "temp_min",
        "humidity",
        "rainfall",
        "wind_speed",
        "solar_radiation",
        "ground_temp",
        "pm10",
        "pm25",
        "o3",
        "no2",
        "co",
        "so2",
        "temp_range",
        "humidity_std3",
        "rainfall_7d",
        "high_humidity_risk",
        "weathering_risk",
        "mold_risk",
        "pm_load",
        "acid_risk",
        "oxidation_risk",
        "corrosion_risk",
        "material",
        "exposure",
    ]
]
y = dataset["target"]
X = pd.get_dummies(X, columns=["material", "exposure"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

models = {
    "RandomForest": RandomForestClassifier(
        n_estimators=300, random_state=42, n_jobs=-1
    ),
    "GradientBoosting": GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05, random_state=42
    ),
}

trained_models = {}
accuracies = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    trained_models[name] = model
    y_pred = model.predict(X_test)
    accuracies[name] = accuracy_score(y_test, y_pred)

# LogisticRegression
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
lr_model = LogisticRegression(max_iter=2000, solver="lbfgs")
lr_model.fit(X_train_scaled, y_train)

trained_models["LogisticRegression"] = (lr_model, scaler)
y_pred_lr = lr_model.predict(X_test_scaled)
accuracies["LogisticRegression"] = accuracy_score(y_test, y_pred_lr)

# 최적 모델 선정 (오류 수정 핵심)
best_model_name = max(accuracies, key=accuracies.get)
best_model = trained_models[best_model_name]

st.sidebar.subheader("🤖 모델 성능 비교")
for m_name, acc in accuracies.items():
    st.sidebar.text(f"{m_name}: {acc:.4f}")
st.sidebar.success(
    f"최적 모델: {best_model_name} ({accuracies[best_model_name]:.4f})"
)

# ============================================================
# 4. 재질별 환경 요인 중요도 시각화
# ============================================================
st.header("📊 재질별 환경 위험 요인 TOP 10")

env_features = [
    "temp_avg",
    "temp_max",
    "temp_min",
    "humidity",
    "rainfall",
    "wind_speed",
    "solar_radiation",
    "ground_temp",
    "pm10",
    "pm25",
    "o3",
    "no2",
    "co",
    "so2",
    "temp_range",
    "humidity_std3",
    "rainfall_7d",
    "high_humidity_risk",
    "weathering_risk",
    "mold_risk",
    "pm_load",
    "acid_risk",
    "oxidation_risk",
    "corrosion_risk",
]
materials_list = ["석조", "목조", "금속", "회화"]

cols = st.columns(2)
for idx, material in enumerate(materials_list):
    sub_df = dataset[dataset["material"] == material]
    if len(sub_df) >= 30:
        X_sub = sub_df[env_features]
        y_sub = sub_df["target"]

        rf_sub = RandomForestClassifier(n_estimators=300, random_state=42)
        rf_sub.fit(X_sub, y_sub)

        imp_df = (
            pd.DataFrame(
                {"Feature": env_features, "Importance": rf_sub.feature_importances_}
            )
            .sort_values("Importance", ascending=False)
            .head(10)
        )

        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.barh(imp_df["Feature"][::-1], imp_df["Importance"][::-1])
        ax.set_title(f"{material} 문화재 위험요인 TOP 10")
        ax.set_xlabel("Importance")
        plt.tight_layout()

        with cols[idx % 2]:
            st.pyplot(fig)
            plt.close(fig)

# ============================================================
# 5. 최근 기상·대기 기반 실시간 영천 문화재 위험도 예측
# ============================================================
st.header("🔍 영천 문화재 실시간 위험등급 예측")

# 최근 기상 데이터 불러오기
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=6)
start_dt = start_date.strftime("%Y%m%d")
end_dt = end_date.strftime("%Y%m%d")

params = {
    "serviceKey": ASOS_SERVICE_KEY,
    "numOfRows": "20",
    "pageNo": "1",
    "dataType": "JSON",
    "dataCd": "ASOS",
    "dateCd": "DAY",
    "startDt": start_dt,
    "endDt": end_dt,
    "stnIds": STN_ID,
}

try:
    response = requests.get(ASOS_URL, params=params, timeout=10)
    items = response.json()["response"]["body"]["items"]["item"]
    weather_recent = pd.DataFrame(items)

    weather_recent = weather_recent[
        [
            "tm",
            "avgTa",
            "maxTa",
            "minTa",
            "avgRhm",
            "sumRn",
            "avgWs",
            "sumSsHr",
            "avgTs",
        ]
    ].copy()
    weather_recent.columns = [
        "date",
        "temp_avg",
        "temp_max",
        "temp_min",
        "humidity",
        "rainfall",
        "wind_speed",
        "solar_radiation",
        "ground_temp",
    ]
    weather_recent["date"] = pd.to_datetime(weather_recent["date"])
    for c in weather_recent.columns[1:]:
        weather_recent[c] = pd.to_numeric(weather_recent[c], errors="coerce")

    air_recent = pd.read_csv(air_url)
    air_recent["date"] = pd.to_datetime(air_recent["date"])
    air_recent = air_recent[air_recent["date"].between(start_date, end_date)]

    recent_df = pd.merge(weather_recent, air_recent, on="date", how="left")
    recent_df = recent_df.sort_values("date").ffill().fillna(0)

    latest = recent_df.iloc[-1]

    # 파생변수 계산
    temp_range = latest["temp_max"] - latest["temp_min"]
    humidity_std3 = recent_df["humidity"].tail(3).std()
    if pd.isna(humidity_std3):
        humidity_std3 = 0
    rainfall_7d = recent_df["rainfall"].sum()
    high_humidity_risk = int(latest["humidity"] >= 75)
    weathering_risk = (
        temp_range * 0.4 + humidity_std3 * 0.3 + latest["wind_speed"] * 0.3
    )
    mold_risk = int(
        (latest["humidity"] >= 75) and (latest["ground_temp"] >= 15)
    )
    pm_load = latest["pm10"] + latest["pm25"]
    acid_risk = latest["so2"] * 0.6 + latest["no2"] * 0.4
    oxidation_risk = latest["o3"] * 0.7 + latest["pm25"] * 0.3
    corrosion_risk = latest["humidity"] * 0.5 + latest["so2"] * 0.5

    # 수집된 기상 요약 표기
    env_summary = pd.DataFrame(
        [
            {
                "날짜": latest["date"].strftime("%Y-%m-%d"),
                "평균기온(℃)": latest["temp_avg"],
                "습도(%)": latest["humidity"],
                "미세먼지(PM10)": latest["pm10"],
                "초미세먼지(PM2.5)": latest["pm25"],
            }
        ]
    )
    st.subheader("📌 최근 수집된 환경 정보")
    st.dataframe(env_summary, use_container_width=True)

    # 문화재 목록 불러오기 및 예측
    heritage_path = "/content/drive/MyDrive/00. 2026학년도 인재양성프로젝트/공공데이터 기반 프로젝트/dataset/영천_문화재_특성데이터셋.csv"

    try:
        heritage_df = pd.read_csv(heritage_path)
    except FileNotFoundError:
        # 파일이 없을 때 대비 샘플 생성
        heritage_df = pd.DataFrame(
            {
                "문화재명(국문)": ["영천 은해사 거조암 영산전", "영천 청제비"],
                "재질": ["목조", "석조"],
                "노출형태": ["반실외", "실외"],
            }
        )

    results = []
    for _, heritage in heritage_df.iterrows():
        predict_df = pd.DataFrame(
            [
                {
                    "temp_avg": latest["temp_avg"],
                    "temp_max": latest["temp_max"],
                    "temp_min": latest["temp_min"],
                    "humidity": latest["humidity"],
                    "rainfall": latest["rainfall"],
                    "wind_speed": latest["wind_speed"],
                    "solar_radiation": latest["solar_radiation"],
                    "ground_temp": latest["ground_temp"],
                    "pm10": latest["pm10"],
                    "pm25": latest["pm25"],
                    "o3": latest["o3"],
                    "no2": latest["no2"],
                    "co": latest["co"],
                    "so2": latest["so2"],
                    "temp_range": temp_range,
                    "humidity_std3": humidity_std3,
                    "rainfall_7d": rainfall_7d,
                    "high_humidity_risk": high_humidity_risk,
                    "weathering_risk": weathering_risk,
                    "mold_risk": mold_risk,
                    "pm_load": pm_load,
                    "acid_risk": acid_risk,
                    "oxidation_risk": oxidation_risk,
                    "corrosion_risk": corrosion_risk,
                    "material": heritage["재질"],
                    "exposure": heritage["노출형태"],
                }
            ]
        )

        predict_df = pd.get_dummies(
            predict_df, columns=["material", "exposure"]
        )
        predict_df = predict_df.reindex(columns=X_train.columns, fill_value=0)

        if best_model_name == "LogisticRegression":
            lr_m, scaler_m = best_model
            predict_df_scaled = scaler_m.transform(predict_df)
            prediction = lr_m.predict(predict_df_scaled)[0]
        else:
            prediction = best_model.predict(predict_df)[0]

        results.append(
            [
                heritage["문화재명(국문)"],
                heritage["재질"],
                heritage["노출형태"],
                prediction,
            ]
        )

    result_df = pd.DataFrame(
        results, columns=["문화재명", "재질", "노출형태", "예측위험등급"]
    )

    # 차트 및 리스트 출력
    res_col1, res_col2 = st.columns([1, 2])

    with res_col1:
        st.subheader("📈 위험등급 분포")
        counts = result_df["예측위험등급"].value_counts()
        fig, ax = plt.subplots(figsize=(4, 3))
        colors = {"안전": "green", "주의": "orange", "위험": "red"}
        bar_colors = [colors.get(x, "blue") for x in counts.index]
        counts.plot(kind="bar", color=bar_colors, edgecolor="black", ax=ax)
        ax.set_ylabel("개수")
        plt.xticks(rotation=0)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with res_col2:
        st.subheader("📋 위험등급별 리스트")
        tab1, tab2, tab3 = st.tabs(["🚨 위험", "⚠️ 주의", "✅ 안전"])

        for tab, level in zip([tab1, tab2, tab3], ["위험", "주의", "안전"]):
            with tab:
                sub_df = result_df[result_df["예측위험등급"] == level]
                if len(sub_df) > 0:
                    st.dataframe(
                        sub_df.reset_index(drop=True), use_container_width=True
                    )
                else:
                    st.info(f"현재 등급이 '{level}'인 문화재가 없습니다.")

except Exception as e:
    st.error(f"최근 데이터 수집 중 오류가 발생했습니다: {e}")
