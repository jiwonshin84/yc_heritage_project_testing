import streamlit as st

# ============================================================
# 0. Streamlit 레이아웃 설정 (Streamlit Cloud 최상단 위치 필수)
# ============================================================
try:
    st.set_page_config(
        page_title="영천 문화재 위험도 예측 시스템",
        page_layout="wide"
    )
except Exception:
    pass

# ============================================================
# 0. 라이브러리 임포트
# ============================================================
import itertools
import json
import time
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

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

st.title("🏛️ 영천시 문화재 환경 위험도 실시간 예측 시스템")

# ============================================================
# 1. 기상청 ASOS API
# ============================================================
ASOS_SERVICE_KEY = (
    "feb2bfabd299d5d05e89c7aec49ba7e706112603e76549a92e868bd86ec60323"
)
ASOS_URL = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
STN_ID = "281"  # 영천 관측소


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
        response = requests.get(ASOS_URL, params=params, timeout=15)
        result = response.json()
        items = result["response"]["body"]["items"]["item"]
        df = pd.DataFrame(items)
        return df
    except Exception:
        return pd.DataFrame()


# ============================================================
# 2. 전체 기상 + 미세먼지 데이터 수집 및 전처리
# ============================================================
@st.cache_data(ttl=3600)
def load_and_process_data():
    all_years = []
    for year in range(2016, 2026):
        df_year = fetch_asos_year(year)
        if not df_year.empty:
            all_years.append(df_year)

    if all_years:
        weather_raw = pd.concat(all_years, ignore_index=True)
    else:
        weather_raw = pd.DataFrame()

    if not weather_raw.empty and "tm" in weather_raw.columns:
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
    else:
        weather = pd.DataFrame(
            columns=[
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
        )

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
    try:
        air = pd.read_csv(air_url)
        air["date"] = pd.to_datetime(air["date"], errors="coerce")
    except Exception:
        air = pd.DataFrame(
            columns=["date", "pm10", "pm25", "o3", "no2", "co", "so2"]
        )

    df = pd.merge(weather, air, on="date", how="left")

    air_cols = ["pm10", "pm25", "o3", "no2", "co", "so2"]
    for col in air_cols:
        if col not in df.columns:
            df[col] = 0.0

    # 7. 파생변수 생성
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

    # 8. 재질 × 노출 조합
    materials = ["석조", "목조", "금속", "회화", "기타"]
    exposures = ["실외", "반실외", "실내"]
    comb = pd.DataFrame(
        list(itertools.product(materials, exposures)),
        columns=["material", "exposure"],
    )

    df["key"] = 1
    comb["key"] = 1
    dataset = pd.merge(df, comb, on="key").drop("key", axis=1)

    # calc_risk에서 사용하는 _norm 변수 생성 로직
    norm_targets = [
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
    for target in norm_targets:
        min_v = dataset[target].min()
        max_v = dataset[target].max()
        if max_v - min_v == 0:
            dataset[f"{target}_norm"] = 0
        else:
            dataset[f"{target}_norm"] = (dataset[target] - min_v) / (
                max_v - min_v
            )

    # 10. 위험도 계산 (calc_risk)
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

        return min(r, 100)

    dataset["material_risk"] = dataset.apply(calc_risk, axis=1)

    # 11. 라벨 생성
    def label(x):
        if x >= 80:
            return "위험"
        elif x >= 40:
            return "주의"
        else:
            return "안전"

    dataset["target"] = dataset["material_risk"].apply(label)
    return dataset, air_url


with st.spinner("기상 및 대기환경 데이터 로딩 중..."):
    dataset, air_url = load_and_process_data()

# ============================================================
# 12. 머신러닝 데이터 구성
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

# ============================================================
# 13. train/test split
# ============================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ============================================================
# 14. 모델 학습 (3개 모델 비교)
# ============================================================
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

# LogisticRegression 스케일링 적용
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr_model = LogisticRegression(max_iter=2000, solver="lbfgs")
lr_model.fit(X_train_scaled, y_train)

trained_models["LogisticRegression"] = (lr_model, scaler)
y_pred_lr = lr_model.predict(X_test_scaled)
accuracies["LogisticRegression"] = accuracy_score(y_test, y_pred_lr)

# 최고 모델 결정 로직
best_model_name = max(accuracies, key=accuracies.get)
best_model = trained_models[best_model_name]

st.sidebar.subheader("🤖 모델 정확도 평가")
for m_name, acc in accuracies.items():
    st.sidebar.text(f"{m_name}: {acc:.4f}")
st.sidebar.success(f"최고 성능 모델: {best_model_name}")

# ============================================================
# 변수 중요도 분석 (재질·노출 제외)
# ============================================================
feature_cols = [
    c
    for c in X_train.columns
    if not c.startswith("material_")
    and not c.startswith("exposure_")
    and c != "material"
    and c != "exposure"
]

if best_model_name == "LogisticRegression":
    lr_obj, scaler_obj = best_model
    importance_df = pd.DataFrame(
        {
            "Feature": X_train.columns,
            "Importance": np.mean(np.abs(lr_obj.coef_), axis=0),
        }
    )
else:
    importance_df = pd.DataFrame(
        {
            "Feature": X_train.columns,
            "Importance": best_model.feature_importances_,
        }
    )

importance_df = (
    importance_df[importance_df["Feature"].isin(feature_cols)]
    .sort_values("Importance", ascending=False)
    .head(10)
)

st.subheader("🌲 전체 환경 요인 중요도 TOP 10")
st.dataframe(importance_df, use_container_width=True)

# ============================================================
# 15. 재질별 환경요인 중요도 분석
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
# 16. 영천 문화재 위험등급 예측
# ============================================================
st.header("🔍 영천 문화재 실시간 위험등급 예측")

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
                "문화재명(국문)": [
                    "영천 은해사 거조암 영산전",
                    "영천 청제비",
                    "영천 신월리 삼층석탑",
                ],
                "재질": ["목조", "석조", "석조"],
                "노출형태": ["반실외", "실외", "실외"],
            }
        )

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

    # 최근 7일 데이터 기반 파생변수 생성
    latest = recent_df.iloc[-1]

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

    # 현재 수집된 기상·대기환경 요약 출력
    st.subheader("현재 수집된 기상·대기환경 요약")
    env_df = pd.DataFrame(
        [
            {
                "date": latest["date"].strftime("%Y-%m-%d"),
                "temp_avg": latest["temp_avg"],
                "humidity": latest["humidity"],
                "pm10": latest["pm10"],
            }
        ]
    )
    st.dataframe(env_df, use_container_width=True)

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
            lr_obj, scaler_obj = best_model
            predict_df_scaled = scaler_obj.transform(predict_df)
            prediction = lr_obj.predict(predict_df_scaled)[0]
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

    # 위험도 등급 분포 차트
    st.subheader("영천 문화재 위험도 예측 결과 분포")
    counts = result_df["예측위험등급"].value_counts()

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = {"안전": "green", "주의": "orange", "위험": "red"}
    bar_colors = [colors.get(x, "blue") for x in counts.index]
    counts.plot(kind="bar", color=bar_colors, edgecolor="black", ax=ax)
    ax.set_title("영천 문화재 예측위험등급 분포")
    ax.set_ylabel("개수")
    plt.xticks(rotation=0)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # 예측 위험 등급별 문화재 리스트 출력
    for level in ["위험", "주의", "안전"]:
        sub_df = result_df[result_df["예측위험등급"] == level]

        st.subheader(f"🚨 [예측위험등급: {level}] 문화재 리스트 (총 {len(sub_df)}건)")

        if len(sub_df) > 0:
            formatted_df = (
                sub_df.reset_index(drop=True)
                .rename_axis("번호")
                .reset_index()
                .set_index("번호")
                .assign(번호=lambda x: x.index + 1)
                .set_index("번호")
            )
            st.dataframe(formatted_df, use_container_width=True)
        else:
            st.info(f"현재 환경 데이터 기준 '{level}' 등급으로 예측된 문화재가 없습니다.")

except Exception as e:
    st.error(f"실시간 데이터 예측 중 오류가 발생했습니다: {e}")
