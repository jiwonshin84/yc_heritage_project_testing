import streamlit as st
import pandas as pd
import numpy as np
import itertools
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler


st.title("문화재 환경 위험도 분석")


# ============================================================
# 1. 데이터 불러오기
# ============================================================

df = pd.read_csv("weather.csv")

st.write("데이터 크기:", df.shape)
st.write("컬럼:", df.columns.tolist())


# ============================================================
# 2. 컬럼명 정리
# ============================================================

df.columns = df.columns.astype(str).str.strip()


# ============================================================
# 3. 필요한 컬럼
# ============================================================

required_cols = [
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
    "so2"
]


missing_cols = [
    col for col in required_cols
    if col not in df.columns
]


if missing_cols:

    st.error(
        "다음 컬럼이 없습니다: "
        + str(missing_cols)
    )

    st.stop()


# ============================================================
# 4. 숫자 변환
# ============================================================

for col in required_cols:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


df[required_cols] = df[required_cols].fillna(0)


# ============================================================
# 5. 파생변수
# ============================================================

df["temp_range"] = (
    df["temp_max"]
    - df["temp_min"]
)


df["humidity_std3"] = (
    df["humidity"]
    .rolling(
        3,
        min_periods=1
    )
    .std()
)


df["rainfall_7d"] = (
    df["rainfall"]
    .rolling(
        7,
        min_periods=1
    )
    .sum()
)


df["high_humidity_risk"] = (
    (df["humidity"] >= 75)
    .rolling(
        3,
        min_periods=1
    )
    .sum()
)


df["weathering_risk"] = (
    df["temp_range"] * 0.4
    + df["humidity_std3"] * 0.3
    + df["wind_speed"] * 0.3
)


df["mold_risk"] = (
    (
        (df["humidity"] >= 75)
        &
        (df["ground_temp"] >= 15)
    )
    .astype(int)
)


df["pm_load"] = (
    (df["pm10"] + df["pm25"])
    .rolling(
        3,
        min_periods=1
    )
    .sum()
)


df["acid_risk"] = (
    df["so2"] * 0.6
    + df["no2"] * 0.4
)


df["oxidation_risk"] = (
    df["o3"] * 0.7
    + df["pm25"] * 0.3
)


df["corrosion_risk"] = (
    df["humidity"] * 0.5
    + df["so2"] * 0.5
)


df = df.fillna(0)


# ============================================================
# 6. 재질 × 노출
# ============================================================

materials = [
    "석조",
    "목조",
    "금속",
    "회화",
    "기타"
]


exposures = [
    "실외",
    "반실외",
    "실내"
]


comb = pd.DataFrame(
    itertools.product(
        materials,
        exposures
    ),
    columns=[
        "material",
        "exposure"
    ]
)


df["key"] = 1
comb["key"] = 1


dataset = pd.merge(
    df,
    comb,
    on="key"
)


dataset = dataset.drop(
    columns=["key"]
)


# ============================================================
# 7. 정규화
# ============================================================

risk_cols = [
    "weathering_risk",
    "acid_risk",
    "rainfall_7d",
    "temp_range",
    "pm_load",
    "corrosion_risk",
    "mold_risk",
    "humidity_std3",
    "oxidation_risk",
    "high_humidity_risk"
]


for col in risk_cols:

    min_value = dataset[col].min()
    max_value = dataset[col].max()

    dataset[col + "_norm"] = (
        (
            dataset[col]
            - min_value
        )
        /
        (
            max_value
            - min_value
            + 1e-6
        )
    ) * 100


# ============================================================
# 8. 위험도 계산
# ============================================================

def calc_risk(row):

    material = row["material"]
    exposure = row["exposure"]

    if material == "석조":

        risk = (
            row["weathering_risk_norm"] * 0.25
            + row["acid_risk_norm"] * 0.20
            + row["rainfall_7d_norm"] * 0.18
            + row["temp_range_norm"] * 0.15
            + row["pm_load_norm"] * 0.12
            + row["corrosion_risk_norm"] * 0.10
        )

    elif material == "목조":

        risk = (
            row["mold_risk_norm"] * 0.25
            + row["humidity_std3_norm"] * 0.20
            + row["high_humidity_risk_norm"] * 0.18
            + row["rainfall_7d_norm"] * 0.15
            + row["oxidation_risk_norm"] * 0.12
            + row["pm_load_norm"] * 0.10
        )

    elif material == "금속":

        risk = (
            row["corrosion_risk_norm"] * 0.30
            + row["acid_risk_norm"] * 0.22
            + row["high_humidity_risk_norm"] * 0.18
            + row["humidity_std3_norm"] * 0.12
            + row["pm_load_norm"] * 0.10
            + row["weathering_risk_norm"] * 0.08
        )

    elif material == "회화":

        risk = (
            row["oxidation_risk_norm"] * 0.28
            + row["pm_load_norm"] * 0.20
            + row["humidity_std3_norm"] * 0.18
            + row["high_humidity_risk_norm"] * 0.14
            + row["temp_range_norm"] * 0.10
            + row["weathering_risk_norm"] * 0.10
        )

    else:

        risk = (
            row["weathering_risk_norm"] * 0.20
            + row["acid_risk_norm"] * 0.20
            + row["oxidation_risk_norm"] * 0.20
            + row["corrosion_risk_norm"] * 0.20
            + row["pm_load_norm"] * 0.20
        )

    if exposure == "실외":

        risk *= 1.3

    elif exposure == "반실외":

        risk *= 1.1

    else:

        risk *= 0.85

    return min(risk, 100)


dataset["material_risk"] = dataset.apply(
    calc_risk,
    axis=1
)


# ============================================================
# 9. 위험도 라벨
# ============================================================

def make_label(value):

    if value >= 80:
        return "위험"

    elif value >= 40:
        return "주의"

    else:
        return "안전"


dataset["target"] = dataset[
    "material_risk"
].apply(make_label)


# ============================================================
# 10. 머신러닝 데이터
# ============================================================

feature_columns = [
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
    "exposure"
]


X = dataset[
    feature_columns
].copy()


y = dataset[
    "target"
].copy()


X = pd.get_dummies(
    X,
    columns=[
        "material",
        "exposure"
    ]
)


X = X.fillna(0)


# ============================================================
# 11. 데이터 분할
# ============================================================

if y.nunique() < 2:

    st.error(
        "위험도 클래스가 2개 이상 필요합니다."
    )

    st.stop()


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# ============================================================
# 12. 모델
# ============================================================

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


lr_model = LogisticRegression(
    max_iter=2000,
    solver="lbfgs"
)


trained_models = {}


# ============================================================
# 13. RandomForest / GradientBoosting
# ============================================================

for name, model in models.items():

    model.fit(
        X_train,
        y_train
    )

    trained_models[name] = model


# ============================================================
# 14. Logistic Regression
# ============================================================

scaler = StandardScaler()


X_train_scaled = scaler.fit_transform(
    X_train
)


X_test_scaled = scaler.transform(
    X_test
)


lr_model.fit(
    X_train_scaled,
    y_train
)


trained_models[
    "LogisticRegression"
] = (
    lr_model,
    scaler
)


# ============================================================
# 15. 모델 평가
# ============================================================

results = {}


for name, model in trained_models.items():

    if name == "LogisticRegression":

        model_obj, scaler_obj = model

        y_pred = model_obj.predict(
            X_test_scaled
        )

    else:

        y_pred = model.predict(
            X_test
        )

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    results[name] = accuracy


# ============================================================
# 16. 결과 출력
# ============================================================

st.subheader("모델 성능 비교")


result_df = pd.DataFrame({
    "Model": list(results.keys()),
    "Accuracy": list(results.values())
})


st.dataframe(
    result_df,
    use_container_width=True
)


best_model_name = max(
    results,
    key=results.get
)


best_accuracy = results[
    best_model_name
]


st.success(
    f"최고 성능 모델: {best_model_name} "
    f"/ 정확도: {best_accuracy:.4f}"
)


# ============================================================
# 17. 위험도 분포
# ============================================================

st.subheader("문화재 위험도 분포")


risk_distribution = (
    dataset["target"]
    .value_counts()
)


st.bar_chart(
    risk_distribution
)


# ============================================================
# 18. 환경요인 중요도
# ============================================================

best_model = trained_models[
    best_model_name
]


if best_model_name == "LogisticRegression":

    model_obj, scaler_obj = best_model

    importance = np.mean(
        np.abs(
            model_obj.coef_
        ),
        axis=0
    )

else:

    importance = (
        best_model
        .feature_importances_
    )


importance_df = pd.DataFrame({
    "Feature": X_train.columns,
    "Importance": importance
})


importance_df = importance_df[
    ~importance_df["Feature"].str.startswith(
        "material_"
    )
]


importance_df = importance_df[
    ~importance_df["Feature"].str.startswith(
        "exposure_"
    )
]


importance_df = importance_df.sort_values(
    "Importance",
    ascending=False
)


st.subheader(
    "환경 요인 중요도 TOP 10"
)


st.dataframe(
    importance_df.head(10),
    use_container_width=True
)


# ============================================================
# 19. 중요도 그래프
# ============================================================

top10 = importance_df.head(10)


fig, ax = plt.subplots(
    figsize=(8, 5)
)


ax.barh(
    top10["Feature"],
    top10["Importance"]
)


ax.invert_yaxis()


ax.set_xlabel(
    "Importance"
)


ax.set_title(
    "Environmental Feature Importance"
)


plt.tight_layout()


st.pyplot(fig)


# ============================================================
# 20. 재질별 중요도
# ============================================================

st.subheader(
    "재질별 환경요인 중요도"
)


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
    "corrosion_risk"
]


materials_analysis = [
    "석조",
    "목조",
    "금속",
    "회화"
]


for material in materials_analysis:

    sub_df = dataset[
        dataset["material"]
        == material
    ].copy()


    if len(sub_df) < 30:

        st.warning(
            f"{material}: 데이터 부족"
        )

        continue


    X_sub = sub_df[
        env_features
    ].fillna(0)


    y_sub = sub_df[
        "target"
    ]


    if y_sub.nunique() < 2:

        st.warning(
            f"{material}: 위험도 클래스가 하나뿐입니다."
        )

        continue


    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )


    model.fit(
        X_sub,
        y_sub
    )


    material_importance = pd.DataFrame({

        "Feature": env_features,

        "Importance":
            model.feature_importances_
    })


    material_importance = (
        material_importance
        .sort_values(
            "Importance",
            ascending=False
        )
    )


    st.write(
        f"### {material} 문화재 TOP 10"
    )


    st.dataframe(
        material_importance.head(10),
        use_container_width=True
    )


    top10_material = (
        material_importance
        .head(10)
    )


    fig, ax = plt.subplots(
        figsize=(8, 5)
    )


    ax.barh(
        top10_material["Feature"][::-1],
        top10_material["Importance"][::-1]
    )


    ax.set_title(
        f"{material} 문화재 위험요인 TOP 10"
    )


    ax.set_xlabel(
        "Importance"
    )


    plt.tight_layout()


    st.pyplot(fig)


# ============================================================
# 완료
# ============================================================

st.success(
    "모든 분석이 완료되었습니다!"
)
