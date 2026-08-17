# ============================================================
# 0. 라이브러리
# ============================================================

import requests
import json
import time
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split

from sklearn.tree import DecisionTreeClassifier

from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier
)

from sklearn.metrics import (
    classification_report,
    accuracy_score
)

import matplotlib.pyplot as plt

!pip install koreanize-matplotlib -q
import koreanize_matplotlib

from google.colab import drive
drive.mount('/content/drive')

# ============================================================
# 1. 기상청 ASOS API
# ============================================================

ASOS_SERVICE_KEY = "feb2bfabd299d5d05e89c7aec49ba7e706112603e76549a92e868bd86ec60323"

ASOS_URL = (
    "http://apis.data.go.kr/"
    "1360000/AsosDalyInfoService/getWthrDataList"
)

# 영천 관측소
STN_ID = "281"


# ------------------------------------------------------------
# 연도별 수집 함수
# ------------------------------------------------------------
def fetch_asos_year(year):

    start_dt = f"{year}0101"
    end_dt   = f"{year}1231"

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

        result = response.json()

        items = result["response"]["body"]["items"]["item"]

        df = pd.DataFrame(items)

        print(f"{year}년 수집 완료 : {len(df)}건")

        return df

    except Exception as e:

        print(f"{year}년 실패 :", e)

        return pd.DataFrame()


# ============================================================
# 2. 전체 기상 데이터 수집
# ============================================================

print("=" * 60)
print("기상 데이터 수집 시작")
print("=" * 60)

all_years = []

for year in range(2016, 2026):

    df_year = fetch_asos_year(year)

    all_years.append(df_year)

    # API 과부하 방지
    time.sleep(0.5)

weather_raw = pd.concat(
    all_years,
    ignore_index=True
)

print("\n전체 수집 :", len(weather_raw))


# ============================================================
# 3. 필요한 컬럼 추출
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
# 4. 컬럼명 변경
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
# 5. 타입 변환
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
# 5-1. 강수량 결측값 처리
# ============================================================

weather["rainfall"] = weather["rainfall"].fillna(0)

print("강수량 결측 처리 완료")
print("강수량 결측 개수 :", weather["rainfall"].isna().sum())


# ============================================================
# 6. 정렬 및 결측 제거
# ============================================================

weather = (
    weather
    .dropna(subset=["date"])
    .sort_values("date")
    .reset_index(drop=True)
)

print("\n기상 데이터 정제 완료")
print(weather.head())


# ============================================================
# 7. 미세먼지 데이터 불러오기
# ============================================================

air_url = (
    "https://docs.google.com/spreadsheets/d/"
    "1fBEnheVOP-23Hmv_5ZJZVy6m9VmNkpVd2XutOdmlYc8/"
    "export?format=csv&gid=700055413"
)

air = pd.read_csv(air_url)

air["date"] = pd.to_datetime(
    air["date"],
    errors="coerce"
)

print("\n미세먼지 데이터 :", len(air))
print(air.head())

# ============================================================
# 8. 기상 + 미세먼지 병합
# ============================================================

df = pd.merge(
    weather,
    air,
    on="date",
    how="left"
)

print("\n병합 완료 :", len(df))

print("\n결측치 확인")
print(df.isna().sum())

# ----------------------------------------------------------
# CSV 저장
# ----------------------------------------------------------
save_path = (
    "/content/drive/MyDrive/"
    "00. 2026학년도 인재양성프로젝트/"
    "공공데이터 기반 프로젝트/"
    "dataset/[2016_2025] yeongcheon.csv"
)

df.to_csv(
    save_path,
    index=False,
    encoding="utf-8-sig"
)

print("기상 및 미세먼지 데이터 저장 완료")


# ============================================================
# 7. 파생변수 생성
# ============================================================

df["temp_range"] = df["temp_max"] - df["temp_min"]

df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std()

df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()

df["high_humidity_risk"] = (df["humidity"] >= 75).rolling(3, min_periods=1).sum()

df["weathering_risk"] = (
    df["temp_range"] * 0.4 +
    df["humidity_std3"] * 0.3 +
    df["wind_speed"] * 0.3
)

df["mold_risk"] = ((df["humidity"] >= 75) & (df["ground_temp"] >= 15)).astype(int)

df["pm_load"] = (df["pm10"] + df["pm25"]).rolling(3, min_periods=1).sum()

df["acid_risk"] = df["so2"] * 0.6 + df["no2"] * 0.4

df["oxidation_risk"] = df["o3"] * 0.7 + df["pm25"] * 0.3

df["corrosion_risk"] = df["humidity"] * 0.5 + df["so2"] * 0.5

df = df.fillna(0)


# ============================================================
# 8. 재질 × 노출 조합
# ============================================================
import itertools


materials = ["석조", "목조", "금속", "회화", "기타"]
exposures = ["실외", "반실외", "실내"]

comb = pd.DataFrame(
    list(itertools.product(materials, exposures)),
    columns=["material", "exposure"]
)

df["key"] = 1
comb["key"] = 1

dataset = pd.merge(df, comb, on="key").drop("key", axis=1)


# ============================================================
# 10. 위험도 계산 (LABEL 생성용)
# ============================================================

def calc_risk(row):

    m = row["material"]
    e = row["exposure"]

    if m == "석조":
        r = (row["weathering_risk_norm"]*0.25 +
             row["acid_risk_norm"]*0.20 +
             row["rainfall_7d_norm"]*0.18 +
             row["temp_range_norm"]*0.15 +
             row["pm_load_norm"]*0.12 +
             row["corrosion_risk_norm"]*0.10)

    elif m == "목조":
        r = (row["mold_risk_norm"]*0.25 +
             row["humidity_std3_norm"]*0.20 +
             row["high_humidity_risk_norm"]*0.18 +
             row["rainfall_7d_norm"]*0.15 +
             row["oxidation_risk_norm"]*0.12 +
             row["pm_load_norm"]*0.10)

    elif m == "금속":
        r = (row["corrosion_risk_norm"]*0.30 +
             row["acid_risk_norm"]*0.22 +
             row["high_humidity_risk_norm"]*0.18 +
             row["humidity_std3_norm"]*0.12 +
             row["pm_load_norm"]*0.10 +
             row["weathering_risk_norm"]*0.08)

    elif m == "회화":
        r = (row["oxidation_risk_norm"]*0.28 +
             row["pm_load_norm"]*0.20 +
             row["humidity_std3_norm"]*0.18 +
             row["high_humidity_risk_norm"]*0.14 +
             row["temp_range_norm"]*0.10 +
             row["weathering_risk_norm"]*0.10)

    else:
        r = (row["weathering_risk_norm"]*0.2 +
             row["acid_risk_norm"]*0.2 +
             row["oxidation_risk_norm"]*0.2 +
             row["corrosion_risk_norm"]*0.2 +
             row["pm_load_norm"]*0.2)

    if e == "실외":
        r *= 1.3
    elif e == "반실외":
        r *= 1.1
    else:
        r *= 0.85

    return min(r, 100)

dataset["material_risk"] = dataset.apply(calc_risk, axis=1)

# ============================================================
# 11. 라벨 생성
# ============================================================

def label(x):
    if x >= 80:
        return "위험"
    elif x >= 40:
        return "주의"
    else:
        return "안전"

dataset["target"] = dataset["material_risk"].apply(label)



# ============================================================
# 12. 머신러닝 데이터 구성
# ============================================================

X = dataset[
    [
        "temp_avg","temp_max","temp_min","humidity",
        "rainfall","wind_speed","solar_radiation",
        "ground_temp","pm10","pm25","o3","no2","co","so2",
        "temp_range","humidity_std3","rainfall_7d",
        "high_humidity_risk","weathering_risk","mold_risk",
        "pm_load","acid_risk","oxidation_risk","corrosion_risk",
        "material","exposure"
    ]
]

y = dataset["target"]

X = pd.get_dummies(X, columns=["material","exposure"])



# ============================================================
# 13. train/test split
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)



# ============================================================
# 14. 모델 학습 (3개 모델 비교)
# ============================================================

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# ----------------------------
# 1. 모델 정의
# ----------------------------

models = {
    "RandomForest": RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    ),

    "GradientBoosting": GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        random_state=42
    )
}

# LogisticRegression은 따로 처리
lr_model = LogisticRegression(
    max_iter=2000,
    solver="lbfgs"
)

# ----------------------------
# 2. 모델 학습
# ----------------------------

trained_models = {}

# (1) RandomForest, GradientBoosting 학습
for name, model in models.items():
    print(f"\n===== {name} 학습 중 =====")
    model.fit(X_train, y_train)
    trained_models[name] = model

# (2) LogisticRegression → 스케일링 적용
print("\n===== LogisticRegression 학습 중 =====")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr_model.fit(X_train_scaled, y_train)

trained_models["LogisticRegression"] = (lr_model, scaler)


for name, model in trained_models.items():

    if name == "LogisticRegression":
        lr_model, scaler = model
        y_pred = lr_model.predict(X_test_scaled)
    else:
        y_pred = model.predict(X_test)

    print(f"\n===== {name} 결과 =====")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))


# ============================================================
# 변수 중요도 분석 (재질·노출 제외)
# ============================================================

best_model = trained_models[best_model_name]

# 재질·노출 관련 컬럼 제거
feature_cols = [
    c for c in X_train.columns
    if not c.startswith("material_")
    and not c.startswith("exposure_")
    and c != "material"
    and c != "exposure"
]

# 중요도 계산
if best_model_name == "LogisticRegression":

    lr_model, scaler = best_model

    importance_df = pd.DataFrame({
        "Feature": X_train.columns,
        "Importance": np.mean(np.abs(lr_model.coef_), axis=0)
    })

else:

    importance_df = pd.DataFrame({
        "Feature": X_train.columns,
        "Importance": best_model.feature_importances_
    })

# 재질·노출 제거
importance_df = importance_df[
    importance_df["Feature"].isin(feature_cols)
]

# 정렬
importance_df = importance_df.sort_values(
    "Importance",
    ascending=False
)

# 상위 10개 출력
print("\n환경 요인 중요도 TOP 10")
print(importance_df.head(10))


# ============================================================
# 15. 재질별 환경요인 중요도 분석
# ============================================================

from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import matplotlib.pyplot as plt

env_features = [
    "temp_avg","temp_max","temp_min","humidity",
    "rainfall","wind_speed","solar_radiation",
    "ground_temp","pm10","pm25","o3","no2","co","so2",
    "temp_range","humidity_std3","rainfall_7d",
    "high_humidity_risk","weathering_risk","mold_risk",
    "pm_load","acid_risk","oxidation_risk","corrosion_risk"
]

materials = ["석조","목조","금속","회화"]

for material in materials:

    print("\n" + "="*60)
    print(f"{material} 문화재")
    print("="*60)

    # 해당 재질만 추출
    sub_df = dataset[
        dataset["material"] == material
    ]

    # 데이터가 너무 적으면 건너뜀
    if len(sub_df) < 30:
        print("데이터 부족")
        continue

    X_sub = sub_df[env_features]
    y_sub = sub_df["target"]

    # 모델 학습
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    model.fit(X_sub, y_sub)

    # 중요도 계산
    importance_df = pd.DataFrame({
        "Feature": env_features,
        "Importance": model.feature_importances_
    })

    importance_df = importance_df.sort_values(
        "Importance",
        ascending=False
    )

    # 출력
    print("\nTOP 10 위험 요인")
    print(importance_df.head(10))

    # 시각화
    top10 = importance_df.head(10)

    plt.figure(figsize=(8,5))
    plt.barh(
        top10["Feature"][::-1],
        top10["Importance"][::-1]
    )

    plt.title(f"{material} 문화재 위험요인 TOP 10")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.show()


# ============================================================
# 16. 영천 문화재 위험등급 예측
# ============================================================

results = []

heritage_df = pd.read_csv(
    "/content/drive/MyDrive/"
    "00. 2026학년도 인재양성프로젝트/"
    "공공데이터 기반 프로젝트/"
    "dataset/영천_문화재_특성데이터셋.csv"
)

print(heritage_df.head())


from datetime import datetime, timedelta

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
    "stnIds": STN_ID
}

response = requests.get(
    ASOS_URL,
    params=params
)

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
        "avgTs"
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
    "ground_temp"
]

weather_recent["date"] = pd.to_datetime(weather_recent["date"])
for c in weather_recent.columns[1:]:
    weather_recent[c] = pd.to_numeric(weather_recent[c], errors="coerce")



air_recent = pd.read_csv(air_url)

air_recent["date"] = pd.to_datetime(
    air_recent["date"]
)

air_recent = air_recent[
    air_recent["date"].between(
        start_date,
        end_date
    )
]


recent_df = pd.merge(
    weather_recent,
    air_recent,
    on="date",
    how="left"
)

recent_df = recent_df.sort_values("date").ffill().fillna(0)


# --------------------------------------------------------
# 최근 7일 데이터 기반 파생변수 생성
# --------------------------------------------------------
latest = recent_df.iloc[-1]

# 1. 온도차
temp_range = latest["temp_max"] - latest["temp_min"]

# 2. 최근 3일 습도 변동성 (데이터가 부족할 경우 std가 NaN이 되는 것을 방지하기 위해 fillna(0))
humidity_std3 = recent_df["humidity"].tail(3).std()
if pd.isna(humidity_std3): humidity_std3 = 0

# 3. 최근 7일 누적강수량
rainfall_7d = recent_df["rainfall"].sum()

# 4. 고습도 위험 (최근 3일 중 습도가 75 이상인 일수 수집과 유사하게 처리하되, 단일 시점이므로 대용 조치)
high_humidity_risk = int(latest["humidity"] >= 75)

# 5. 풍화 위험 (수식 일치)
weathering_risk = temp_range * 0.4 + humidity_std3 * 0.3 + latest["wind_speed"] * 0.3

# 6. 곰팡이 위험 (수식 일치: 1 또는 0)
mold_risk = int((latest["humidity"] >= 75) and (latest["ground_temp"] >= 15))

# 7. 미세먼지 부하
pm_load = (latest["pm10"] + latest["pm25"]) # rolling 3일 기준이나 단일 시점 대용

# 8. 산성 위험 (수식 일치)
acid_risk = latest["so2"] * 0.6 + latest["no2"] * 0.4

# 9. 산화 위험 (수식 일치)
oxidation_risk = latest["o3"] * 0.7 + latest["pm25"] * 0.3

# 10. 부식 위험 (수식 일치)
corrosion_risk = latest["humidity"] * 0.5 + latest["so2"] * 0.5


for _, heritage in heritage_df.iterrows():

    predict_df = pd.DataFrame([{
        "temp_avg": latest["temp_avg"], "temp_max": latest["temp_max"], "temp_min": latest["temp_min"],
        "humidity": latest["humidity"], "rainfall": latest["rainfall"],
        "wind_speed": latest["wind_speed"], "solar_radiation": latest["solar_radiation"], "ground_temp": latest["ground_temp"],
        "pm10": latest["pm10"], "pm25": latest["pm25"],
        "o3": latest["o3"], "no2": latest["no2"], "co": latest["co"], "so2": latest["so2"],
        "temp_range": temp_range, "humidity_std3": humidity_std3, "rainfall_7d": rainfall_7d,
        "high_humidity_risk": high_humidity_risk, "weathering_risk": weathering_risk, "mold_risk": mold_risk,
        "pm_load": pm_load, "acid_risk": acid_risk, "oxidation_risk": oxidation_risk, "corrosion_risk": corrosion_risk,
        "material": heritage["재질"], "exposure": heritage["노출형태"]
    }])

    predict_df = pd.get_dummies(predict_df, columns=["material", "exposure"])
    predict_df = predict_df.reindex(columns=X_train.columns, fill_value=0)

    # 최고 모델이 로지스틱 회귀인 경우와 트리 모델인 경우 분기 처리
    if best_model_name == "LogisticRegression":
        lr_model, scaler_obj = best_model  # 튜플 언패킹
        predict_df_scaled = scaler_obj.transform(predict_df)
        prediction = lr_model.predict(predict_df_scaled)[0]
    else:
        prediction = best_model.predict(predict_df)[0]

    results.append([
        heritage["문화재명(국문)"],
        heritage["재질"],
        heritage["노출형태"],
        prediction
    ])


# ============================================================
# 현재 환경 데이터 확인
# ============================================================

env_df = pd.DataFrame([{
    "date": latest["date"],
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
    "corrosion_risk": corrosion_risk
}])

print("\n" + "="*80)
print("현재 수집된 기상·대기환경 데이터")
print("="*80)
display(env_df)


# ============================================================
# 현재 환경 데이터 및 결과 출력
# ============================================================
env_df = pd.DataFrame([{"date": latest["date"], "temp_avg": latest["temp_avg"], "humidity": latest["humidity"], "pm10": latest["pm10"]}])
print("\n" + "="*80); print("현재 수집된 기상·대기환경 요약"); print("="*80)
print(env_df)

result_df = pd.DataFrame(results, columns=["문화재명", "재질", "노출형태", "예측위험등급"])
print("\n" + "="*80); print("영천 문화재 위험도 예측 결과"); print("="*80)
print(result_df.head())



danger_df = result_df[
    result_df["예측위험등급"] == "위험"
]

print("\n" + "="*80)
print("위험 등급 문화재")
print("="*80)
display(danger_df)



print("\n" + "="*80)
print("위험도 등급 분포")
print("="*80)

display(
    result_df["예측위험등급"]
    .value_counts()
    .reset_index()
    .rename(columns={
        "index":"위험등급",
        "예측위험등급":"개수"
    })
)


plt.figure(figsize=(6, 4))


counts = result_df["예측위험등급"].value_counts()


colors = {"안전": "green", "주의": "orange", "위험": "red"}
bar_colors = [colors.get(x, "blue") for x in counts.index]

counts.plot(kind="bar", color=bar_colors, edgecolor="black")

plt.title("영천 문화재 예측위험등급 분포")
plt.ylabel("개수")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()



# ============================================================
# 예측 위험 등급별 문화재 리스트 출력
# ============================================================

for level in ["위험", "주의", "안전"]:
    # 해당 등급의 문화재만 필터링
    sub_df = result_df[result_df["예측위험등급"] == level]

    print("\n" + "="*80)
    print(f"🚨 [예측위험등급: {level}] 문화재 리스트 (총 {len(sub_df)}건)")
    print("="*80)

    if len(sub_df) > 0:
        # 인덱스를 1부터 시작하도록 조정하여 깔끔하게 출력
        display(sub_df.reset_index(drop=True).rename_axis("번호").reset_index().set_index("번호").assign(번호=lambda x: x.index + 1).set_index("번호"))
    else:
        print(f"현재 환경 데이터 기준 '{level}' 등급으로 예측된 문화재가 없습니다.")





