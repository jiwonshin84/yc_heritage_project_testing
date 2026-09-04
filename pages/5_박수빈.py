import streamlit as st
import pandas as pd
import numpy as np
import itertools
import matplotlib.pyplot as plt
import os
import glob

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler


# ============================================================
# 페이지 설정
# ============================================================

st.set_page_config(
    page_title="문화재 환경 위험도 분석",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ 문화재 환경 위험도 분석")


# ============================================================
# 1. CSV 파일 자동 찾기
# ============================================================

st.header("1. 데이터 불러오기")


# 현재 프로젝트 위치 확인
current_dir = os.getcwd()

st.write(
    f"현재 작업 폴더: `{current_dir}`"
)


# 프로젝트 내부의 모든 CSV 검색
csv_files = glob.glob(
    "**/*.csv",
    recursive=True
)


# CSV가 없는 경우
if len(csv_files) == 0:

    st.error(
        "❌ 프로젝트 안에서 CSV 파일을 찾을 수 없습니다."
    )

    st.info(
        "CSV 파일을 GitHub 프로젝트에 업로드했는지 확인해주세요."
    )

    st.stop()


# CSV 파일 목록 표시
st.success(
    f"CSV 파일 {len(csv_files)}개를 찾았습니다."
)


with st.expander("찾은 CSV 파일 확인"):

    for file in csv_files:

        st.write(
            f"- {file}"
        )


# ============================================================
# 2. CSV 선택
# ============================================================

# CSV가 하나면 자동 선택
if len(csv_files) == 1:

    csv_path = csv_files[0]

else:

    csv_path = st.selectbox(
        "사용할 CSV 파일을 선택하세요.",
        csv_files
    )


st.info(
    f"📂 사용 중인 데이터: `{csv_path}`"
)


# ============================================================
# 3. CSV 읽기
# ============================================================

try:

    df = pd.read_csv(
        csv_path,
        encoding="utf-8-sig"
    )

except UnicodeDecodeError:

    try:

        df = pd.read_csv(
            csv_path,
            encoding="cp949"
        )

    except Exception as e:

        st.error(
            f"CSV 파일을 읽을 수 없습니다: {e}"
        )

        st.stop()

except Exception as e:

    st.error(
        f"CSV 파일을 읽을 수 없습니다: {e}"
    )

    st.stop()


# ============================================================
# 4. 컬럼명 정리
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


st.write(
    "데이터 크기:",
    df.shape
)


st.write(
    "현재 CSV 컬럼:"
)


st.write(
    df.columns.tolist()
)


# ============================================================
# 5. 필수 컬럼 확인
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

    col

    for col in required_cols

    if col not in df.columns
]


# 필수 컬럼이 없는 경우
if missing_cols:

    st.error(
        "❌ 필요한 컬럼이 없습니다."
    )

    st.write(
        "없는 컬럼:",
        missing_cols
    )

    st.warning(
        "현재 CSV의 컬럼명과 코드가 요구하는 컬럼명이 다릅니다."
    )

    st.write(
        "코드가 요구하는 컬럼:"
    )

    st.write(
        required_cols
    )

    st.stop()


# ============================================================
# 6. 숫자형 변환
# ============================================================

st.header("2. 데이터 전처리")


for col in required_cols:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# 결측값 처리
df[required_cols] = (
    df[required_cols]
    .fillna(0)
)


# ============================================================
# 7. 파생변수 생성
# ============================================================

st.header("3. 환경 위험요인 계산")


# ------------------------------------------------------------
# 일교차
# ------------------------------------------------------------

df["temp_range"] = (
    df["temp_max"]
    - df["temp_min"]
)


# ------------------------------------------------------------
# 3일 습도 표준편차
# ------------------------------------------------------------

df["humidity_std3"] = (
    df["humidity"]
    .rolling(
        3,
        min_periods=1
    )
    .std()
)


# ------------------------------------------------------------
# 7일 누적 강수량
# ------------------------------------------------------------

df["rainfall_7d"] = (
    df["rainfall"]
    .rolling(
        7,
        min_periods=1
    )
    .sum()
)


# ------------------------------------------------------------
# 고습도 위험
# ------------------------------------------------------------

df["high_humidity_risk"] = (
    (df["humidity"] >= 75)
    .rolling(
        3,
        min_periods=1
    )
    .sum()
)


# ------------------------------------------------------------
# 풍화 위험
# ------------------------------------------------------------

df["weathering_risk"] = (

    df["temp_range"] * 0.4

    + df["humidity_std3"] * 0.3

    + df["wind_speed"] * 0.3
)


# ------------------------------------------------------------
# 곰팡이 위험
# ------------------------------------------------------------

df["mold_risk"] = (

    (
        (df["humidity"] >= 75)

        &

        (df["ground_temp"] >= 15)
    )

    .astype(int)
)


# ------------------------------------------------------------
# 미세먼지 부하
# ------------------------------------------------------------

df["pm_load"] = (

    (df["pm10"] + df["pm25"])

    .rolling(
        3,
        min_periods=1
    )

    .sum()
)


# ------------------------------------------------------------
# 산성 위험
# ------------------------------------------------------------

df["acid_risk"] = (

    df["so2"] * 0.6

    + df["no2"] * 0.4
)


# ------------------------------------------------------------
# 산화 위험
# ------------------------------------------------------------

df["oxidation_risk"] = (

    df["o3"] * 0.7

    + df["pm25"] * 0.3
)


# ------------------------------------------------------------
# 부식 위험
# ------------------------------------------------------------

df["corrosion_risk"] = (

    df["humidity"] * 0.5

    + df["so2"] * 0.5
)


# 모든 결측값 0 처리
df = df.fillna(0)


st.success(
    "환경 위험요인 계산 완료!"
)


# ============================================================
# 8. 재질 × 노출 조합
# ============================================================

st.header("4. 문화재 재질 × 노출환경")


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


# Cartesian Product
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


st.write(
    "재질 × 노출 조합 후 데이터:",
    dataset.shape
)


# ============================================================
# 9. 위험요인 정규화
# ============================================================

st.header("5. 위험도 정규화")


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


st.success(
    "정규화 완료!"
)


# ============================================================
# 10. 재질별 위험도 계산
# ============================================================

st.header("6. 문화재 위험도 계산")


def calc_risk(row):

    material = row["material"]

    exposure = row["exposure"]


    # --------------------------------------------------------
    # 석조
    # --------------------------------------------------------

    if material == "석조":

        risk = (

            row["weathering_risk_norm"]
            * 0.25

            + row["acid_risk_norm"]
            * 0.20

            + row["rainfall_7d_norm"]
            * 0.18

            + row["temp_range_norm"]
            * 0.15

            + row["pm_load_norm"]
            * 0.12

            + row["corrosion_risk_norm"]
            * 0.10
        )


    # --------------------------------------------------------
    # 목조
    # --------------------------------------------------------

    elif material == "목조":

        risk = (

            row["mold_risk_norm"]
            * 0.25

            + row["humidity_std3_norm"]
            * 0.20

            + row["high_humidity_risk_norm"]
            * 0.18

            + row["rainfall_7d_norm"]
            * 0.15

            + row["oxidation_risk_norm"]
            * 0.12

            + row["pm_load_norm"]
            * 0.10
        )


    # --------------------------------------------------------
    # 금속
    # --------------------------------------------------------

    elif material == "금속":

        risk = (

            row["corrosion_risk_norm"]
            * 0.30

            + row["acid_risk_norm"]
            * 0.22

            + row["high_humidity_risk_norm"]
            * 0.18

            + row["humidity_std3_norm"]
            * 0.12

            + row["pm_load_norm"]
            * 0.10

            + row["weathering_risk_norm"]
            * 0.08
        )


    # --------------------------------------------------------
    # 회화
    # --------------------------------------------------------

    elif material == "회화":

        risk = (

            row["oxidation_risk_norm"]
            * 0.28

            + row["pm_load_norm"]
            * 0.20

            + row["humidity_std3_norm"]
            * 0.18

            + row["high_humidity_risk_norm"]
            * 0.14

            + row["temp_range_norm"]
            * 0.10

            + row["weathering_risk_norm"]
            * 0.10
        )


    # --------------------------------------------------------
    # 기타
    # --------------------------------------------------------

    else:

        risk = (

            row["weathering_risk_norm"]
            * 0.20

            + row["acid_risk_norm"]
            * 0.20

            + row["oxidation_risk_norm"]
            * 0.20

            + row["corrosion_risk_norm"]
            * 0.20

            + row["pm_load_norm"]
            * 0.20
        )


    # --------------------------------------------------------
    # 노출환경 보정
    # --------------------------------------------------------

    if exposure == "실외":

        risk *= 1.3


    elif exposure == "반실외":

        risk *= 1.1


    else:

        risk *= 0.85


    return min(
        risk,
        100
    )


dataset["material_risk"] = (
    dataset.apply(
        calc_risk,
        axis=1
    )
)


# ============================================================
# 11. 위험도 라벨
# ============================================================

def make_label(value):

    if value >= 80:

        return "위험"

    elif value >= 40:

        return "주의"

    else:

        return "안전"


dataset["target"] = (
    dataset["material_risk"]
    .apply(make_label)
)


# ============================================================
# 12. 위험도 분포
# ============================================================

st.subheader(
    "문화재 위험도 분포"
)


risk_distribution = (
    dataset["target"]
    .value_counts()
)


st.dataframe(
    risk_distribution
    .rename("개수")
)


st.bar_chart(
    risk_distribution
)


# ============================================================
# 13. 머신러닝 데이터 구성
# ============================================================

st.header("7. 머신러닝 분석")


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


# 범주형 변수 One-Hot Encoding
X = pd.get_dummies(

    X,

    columns=[
        "material",
        "exposure"
    ]
)


X = X.fillna(0)


# ============================================================
# 14. 클래스 확인
# ============================================================

class_count = (
    y.value_counts()
)


st.subheader(
    "위험도 클래스"
)


st.dataframe(
    class_count
    .rename("개수")
)


if y.nunique() < 2:

    st.error(
        "위험도 클래스가 2개 이상 필요합니다."
    )

    st.stop()


# ============================================================
# 15. Train / Test Split
# ============================================================

X_train, X_test, y_train, y_test = (

    train_test_split(

        X,
        y,

        test_size=0.2,

        random_state=42,

        stratify=y
    )
)


# ============================================================
# 16. 모델 정의
# ============================================================

models = {

    "RandomForest":

        RandomForestClassifier(

            n_estimators=300,

            random_state=42,

            n_jobs=-1
        ),


    "GradientBoosting":

        GradientBoostingClassifier(

            n_estimators=200,

            learning_rate=0.05,

            random_state=42
        )
}


# Logistic Regression
lr_model = LogisticRegression(

    max_iter=2000,

    solver="lbfgs"
)


trained_models = {}


# ============================================================
# 17. Random Forest / Gradient Boosting 학습
# ============================================================

for name, model in models.items():

    with st.spinner(
        f"{name} 학습 중..."
    ):

        model.fit(
            X_train,
            y_train
        )


    trained_models[name] = model


# ============================================================
# 18. Logistic Regression 학습
# ============================================================

with st.spinner(
    "Logistic Regression 학습 중..."
):

    scaler = StandardScaler()


    X_train_scaled = (
        scaler.fit_transform(
            X_train
        )
    )


    X_test_scaled = (
        scaler.transform(
            X_test
        )
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
# 19. 모델 평가
# ============================================================

st.header("8. 모델 성능 비교")


results = {}

reports = {}


for name, model in trained_models.items():

    if name == "LogisticRegression":

        model_obj, scaler_obj = model


        y_pred = (
            model_obj.predict(
                X_test_scaled
            )
        )


    else:

        y_pred = (
            model.predict(
                X_test
            )
        )


    accuracy = accuracy_score(
        y_test,
        y_pred
    )


    results[name] = accuracy


    reports[name] = (
        classification_report(
            y_test,
            y_pred,
            zero_division=0
        )
    )


# ============================================================
# 20. 성능표
# ============================================================

result_df = pd.DataFrame({

    "모델":
        list(results.keys()),

    "정확도":
        list(results.values())
})


result_df = (
    result_df
    .sort_values(
        "정확도",
        ascending=False
    )
)


st.dataframe(
    result_df,
    use_container_width=True
)


# ============================================================
# 21. 최고 모델
# ============================================================

best_model_name = max(
    results,
    key=results.get
)


best_accuracy = results[
    best_model_name
]


st.success(

    f"🏆 최고 성능 모델: "
    f"{best_model_name}  |  "
    f"정확도: {best_accuracy:.4f}"
)


# ============================================================
# 22. Classification Report
# ============================================================

st.subheader(
    "모델별 상세 평가"
)


for name in results.keys():

    with st.expander(
        f"{name} 상세 결과"
    ):

        st.text(
            reports[name]
        )


# ============================================================
# 23. 최고 모델 변수 중요도
# ============================================================

st.header(
    "9. 환경요인 중요도"
)


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

    "Feature":
        X_train.columns,

    "Importance":
        importance
})


# 재질 / 노출 변수 제거
importance_df = (
    importance_df[
        ~importance_df["Feature"]
        .str.startswith("material_")
    ]
)


importance_df = (
    importance_df[
        ~importance_df["Feature"]
        .str.startswith("exposure_")
    ]
)


importance_df = (
    importance_df
    .sort_values(
        "Importance",
        ascending=False
    )
)


st.subheader(
    "환경 요인 중요도 TOP 10"
)


st.dataframe(

    importance_df.head(10),

    use_container_width=True
)


# ============================================================
# 24. 중요도 그래프
# ============================================================

top10 = (
    importance_df
    .head(10)
    .sort_values(
        "Importance"
    )
)


fig, ax = plt.subplots(
    figsize=(9, 6)
)


ax.barh(

    top10["Feature"],

    top10["Importance"]
)


ax.set_xlabel(
    "Importance"
)


ax.set_title(
    "Environmental Feature Importance"
)


plt.tight_layout()


st.pyplot(fig)


# ============================================================
# 25. 재질별 환경요인 중요도
# ============================================================

st.header(
    "10. 재질별 환경요인 중요도"
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

    st.subheader(
        f"🏛️ {material} 문화재"
    )


    sub_df = dataset[
        dataset["material"]
        == material
    ].copy()


    # 데이터 부족
    if len(sub_df) < 30:

        st.warning(
            f"{material}: 데이터가 30개 미만이라 분석하지 않습니다."
        )

        continue


    X_sub = (
        sub_df[
            env_features
        ]
        .fillna(0)
    )


    y_sub = (
        sub_df[
            "target"
        ]
    )


    # 클래스 하나만 존재
    if y_sub.nunique() < 2:

        st.warning(

            f"{material}: "
            "위험도 클래스가 하나뿐이라 "
            "분석할 수 없습니다."
        )

        continue


    # 재질별 Random Forest
    material_model = (
        RandomForestClassifier(

            n_estimators=300,

            random_state=42,

            n_jobs=-1
        )
    )


    material_model.fit(

        X_sub,

        y_sub
    )


    # 중요도
    material_importance = pd.DataFrame({

        "Feature":
            env_features,

        "Importance":
            material_model
            .feature_importances_
    })


    material_importance = (

        material_importance

        .sort_values(

            "Importance",

            ascending=False
        )
    )


    # TOP 10
    st.write(
        "위험요인 TOP 10"
    )


    st.dataframe(

        material_importance.head(10),

        use_container_width=True
    )


    # --------------------------------------------------------
    # 그래프
    # --------------------------------------------------------

    top10_material = (

        material_importance

        .head(10)

        .sort_values(
            "Importance"
        )
    )


    fig, ax = plt.subplots(

        figsize=(9, 6)
    )


    ax.barh(

        top10_material["Feature"],

        top10_material["Importance"]
    )


    ax.set_xlabel(
        "Importance"
    )


    ax.set_title(

        f"{material} 문화재 "
        "위험요인 TOP 10"
    )


    plt.tight_layout()


    st.pyplot(fig)


# ============================================================
# 26. 최종 데이터 확인
# ============================================================

st.header(
    "11. 분석 데이터"
)


with st.expander(
    "최종 데이터 확인"
):

    st.write(
        "최종 데이터 크기:",
        dataset.shape
    )


    st.dataframe(

        dataset.head(100),

        use_container_width=True
    )


# ============================================================
# 완료
# ============================================================

st.success(
    "🎉 문화재 환경 위험도 분석이 완료되었습니다!"
)
