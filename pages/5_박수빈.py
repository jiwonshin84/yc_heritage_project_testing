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
# 1. 데이터 불러오기
# ============================================================

st.header("1. 대기환경 데이터 불러오기")


# 현재 네 프로젝트에서 사용하는 CSV
df = None
file_name = None


# ------------------------------------------------------------
# weather.csv가 있으면 사용
# ------------------------------------------------------------

try:

    df = pd.read_csv(
        "weather.csv",
        encoding="utf-8-sig"
    )

    file_name = "weather.csv"

except FileNotFoundError:

    try:

        df = pd.read_csv(
            "weather.csv",
            encoding="cp949"
        )

        file_name = "weather.csv"

    except Exception:

        df = None


# ------------------------------------------------------------
# weather.csv가 없으면 data.csv 시도
# ------------------------------------------------------------

if df is None:

    try:

        df = pd.read_csv(
            "data.csv",
            encoding="utf-8-sig"
        )

        file_name = "data.csv"

    except Exception:

        df = None


# ------------------------------------------------------------
# 그래도 없으면 프로젝트의 CSV 자동 탐색
# ------------------------------------------------------------

if df is None:

    import glob

    csv_files = glob.glob(
        "**/*.csv",
        recursive=True
    )

    if len(csv_files) > 0:

        for csv_file in csv_files:

            try:

                temp_df = pd.read_csv(
                    csv_file,
                    encoding="utf-8-sig"
                )

            except Exception:

                try:

                    temp_df = pd.read_csv(
                        csv_file,
                        encoding="cp949"
                    )

                except Exception:

                    continue


            temp_df.columns = (
                temp_df.columns
                .astype(str)
                .str.strip()
            )


            # 현재 데이터에서 사용하는 대기오염 컬럼
            pollution_cols = [
                "pm10",
                "pm25",
                "o3",
                "no2",
                "co",
                "so2"
            ]


            match_count = sum(
                col in temp_df.columns
                for col in pollution_cols
            )


            if match_count >= 4:

                df = temp_df

                file_name = csv_file

                break


# ------------------------------------------------------------
# CSV를 못 찾은 경우
# ------------------------------------------------------------

if df is None:

    st.error(
        "❌ CSV 파일을 찾을 수 없습니다."
    )

    st.info(
        "weather.csv 파일을 프로젝트에 업로드해주세요."
    )

    st.stop()


st.success(
    f"📂 사용 중인 파일: {file_name}"
)


# ============================================================
# 2. 컬럼명 정리
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

st.code(
    "\n".join(df.columns.tolist())
)


# ============================================================
# 3. 필요한 대기환경 컬럼 확인
# ============================================================

required_cols = [
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


if missing_cols:

    st.error(
        "❌ 필요한 대기환경 컬럼이 없습니다."
    )

    st.write(
        "없는 컬럼:",
        missing_cols
    )

    st.write(
        "현재 CSV의 실제 컬럼:",
        df.columns.tolist()
    )

    st.stop()


# ============================================================
# 4. 날짜 처리
# ============================================================

if "date" in df.columns:

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

else:

    # 날짜 컬럼이 없으면 순번 생성
    df["date"] = range(
        len(df)
    )


# ============================================================
# 5. 숫자 변환
# ============================================================

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
# 6. 현재 데이터 상황 안내
# ============================================================

st.info(
    "현재 CSV에는 기온·습도·강수량 등의 기상 데이터가 없고 "
    "PM10, PM2.5, O3, NO2, CO, SO2 대기오염 데이터만 있습니다. "
    "따라서 이번 분석은 대기오염 중심으로 진행합니다."
)


# ============================================================
# 7. 대기환경 파생변수 생성
# ============================================================

st.header(
    "2. 대기환경 위험요인 계산"
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
# PM10 7일 누적
# ------------------------------------------------------------

df["pm10_7d"] = (

    df["pm10"]

    .rolling(
        7,
        min_periods=1
    )

    .mean()
)


# ------------------------------------------------------------
# PM2.5 7일 평균
# ------------------------------------------------------------

df["pm25_7d"] = (

    df["pm25"]

    .rolling(
        7,
        min_periods=1
    )

    .mean()
)


# ------------------------------------------------------------
# 오존 위험
# ------------------------------------------------------------

df["oxidation_risk"] = (

    df["o3"] * 0.7

    + df["pm25"] * 0.3
)


# ------------------------------------------------------------
# 산성 위험
# ------------------------------------------------------------

df["acid_risk"] = (

    df["so2"] * 0.6

    + df["no2"] * 0.4
)


# ------------------------------------------------------------
# 부식 위험
# ------------------------------------------------------------

df["corrosion_risk"] = (

    df["so2"] * 0.5

    + df["no2"] * 0.3

    + df["pm25"] * 0.2
)


# ------------------------------------------------------------
# 전체 대기오염 위험
# ------------------------------------------------------------

df["air_pollution_risk"] = (

    df["pm10"] * 0.25

    + df["pm25"] * 0.30

    + df["o3"] * 0.15

    + df["no2"] * 0.10

    + df["so2"] * 0.15

    + df["co"] * 0.05
)


df = df.replace(
    [np.inf, -np.inf],
    np.nan
)


df = df.fillna(0)


st.success(
    "대기환경 위험요인 계산 완료!"
)


# ============================================================
# 8. 원본 데이터 확인
# ============================================================

st.subheader(
    "대기환경 데이터 미리보기"
)


st.dataframe(
    df.head(20),
    use_container_width=True
)


# ============================================================
# 9. 재질 × 노출환경
# ============================================================

st.header(
    "3. 문화재 재질 × 노출환경"
)


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


st.write(
    "재질 × 노출환경 적용 후 데이터 크기:",
    dataset.shape
)


# ============================================================
# 10. 위험요인 정규화
# ============================================================

st.header(
    "4. 위험요인 정규화"
)


risk_cols = [

    "pm_load",
    "pm10_7d",
    "pm25_7d",
    "oxidation_risk",
    "acid_risk",
    "corrosion_risk",
    "air_pollution_risk"
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
# 11. 재질별 위험도 계산
# ============================================================

st.header(
    "5. 문화재 위험도 계산"
)


def calc_risk(row):

    material = row["material"]

    exposure = row["exposure"]


    # --------------------------------------------------------
    # 석조
    # --------------------------------------------------------

    if material == "석조":

        risk = (

            row["acid_risk_norm"] * 0.30

            + row["pm_load_norm"] * 0.25

            + row["pm25_7d_norm"] * 0.20

            + row["oxidation_risk_norm"] * 0.15

            + row["corrosion_risk_norm"] * 0.10
        )


    # --------------------------------------------------------
    # 목조
    # --------------------------------------------------------

    elif material == "목조":

        risk = (

            row["pm25_7d_norm"] * 0.30

            + row["oxidation_risk_norm"] * 0.25

            + row["pm_load_norm"] * 0.20

            + row["air_pollution_risk_norm"] * 0.15

            + row["acid_risk_norm"] * 0.10
        )


    # --------------------------------------------------------
    # 금속
    # --------------------------------------------------------

    elif material == "금속":

        risk = (

            row["corrosion_risk_norm"] * 0.35

            + row["acid_risk_norm"] * 0.25

            + row["pm25_7d_norm"] * 0.15

            + row["oxidation_risk_norm"] * 0.15

            + row["pm_load_norm"] * 0.10
        )


    # --------------------------------------------------------
    # 회화
    # --------------------------------------------------------

    elif material == "회화":

        risk = (

            row["oxidation_risk_norm"] * 0.30

            + row["pm25_7d_norm"] * 0.25

            + row["pm_load_norm"] * 0.20

            + row["air_pollution_risk_norm"] * 0.15

            + row["acid_risk_norm"] * 0.10
        )


    # --------------------------------------------------------
    # 기타
    # --------------------------------------------------------

    else:

        risk = (

            row["air_pollution_risk_norm"] * 0.20

            + row["acid_risk_norm"] * 0.20

            + row["oxidation_risk_norm"] * 0.20

            + row["corrosion_risk_norm"] * 0.20

            + row["pm_load_norm"] * 0.20
        )


    # --------------------------------------------------------
    # 노출환경 보정
    # --------------------------------------------------------

    if exposure == "실외":

        risk *= 1.30

    elif exposure == "반실외":

        risk *= 1.10

    else:

        risk *= 0.85


    return min(
        float(risk),
        100
    )


dataset["material_risk"] = (
    dataset.apply(
        calc_risk,
        axis=1
    )
)


# ============================================================
# 12. 위험도 라벨
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
# 13. 위험도 분포
# ============================================================

st.header(
    "6. 문화재 위험도 분포"
)


risk_distribution = (
    dataset["target"]
    .value_counts()
)


st.dataframe(
    risk_distribution.rename("개수"),
    use_container_width=True
)


st.bar_chart(
    risk_distribution
)


# ============================================================
# 14. 머신러닝 데이터 구성
# ============================================================

st.header(
    "7. 머신러닝 분석"
)


feature_columns = [

    "pm10",
    "pm25",
    "o3",
    "no2",
    "co",
    "so2",

    "pm_load",
    "pm10_7d",
    "pm25_7d",

    "oxidation_risk",
    "acid_risk",
    "corrosion_risk",

    "air_pollution_risk",

    "material",
    "exposure"
]


X = dataset[
    feature_columns
].copy()


y = dataset[
    "target"
].copy()


# ------------------------------------------------------------
# 범주형 변수 One-Hot Encoding
# ------------------------------------------------------------

X = pd.get_dummies(
    X,

    columns=[
        "material",
        "exposure"
    ]
)


X = X.fillna(0)


# 숫자형 강제 변환
X = X.astype(float)


# ============================================================
# 15. 클래스 확인
# ============================================================

class_count = (
    y.value_counts()
)


st.subheader(
    "위험도 클래스"
)


st.dataframe(
    class_count.rename("개수"),
    use_container_width=True
)


# 클래스가 2개 미만이면 중단
if y.nunique() < 2:

    st.error(
        "위험도 클래스가 2개 이상 필요합니다."
    )

    st.stop()


# 각 클래스가 최소 2개 이상인지 확인
if class_count.min() < 2:

    st.error(
        "각 위험도 클래스의 데이터가 최소 2개 이상 필요합니다."
    )

    st.stop()


# ============================================================
# 16. 학습 / 테스트 데이터 분할
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
# 17. 모델 정의
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


lr_model = LogisticRegression(

    max_iter=2000,

    solver="lbfgs"
)


trained_models = {}


# ============================================================
# 18. RandomForest / GradientBoosting 학습
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
# 19. Logistic Regression
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
# 20. 모델 평가
# ============================================================

st.header(
    "8. 모델 성능 비교"
)


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
# 21. 모델 결과표
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
# 22. 최고 성능 모델
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
    f"{best_model_name} | "
    f"정확도: {best_accuracy:.4f}"
)


# ============================================================
# 23. 상세 평가
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
# 24. 환경요인 중요도
# ============================================================

st.header(
    "9. 대기환경 요인 중요도"
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


# 재질 / 노출 변수 제외
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


# ============================================================
# 25. 중요도 TOP 10
# ============================================================

st.subheader(
    "대기환경 요인 중요도 TOP 10"
)


st.dataframe(

    importance_df.head(10),

    use_container_width=True
)


# ============================================================
# 26. 중요도 그래프
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
    "Air Pollution Feature Importance"
)


plt.tight_layout()


st.pyplot(fig)


plt.close(fig)


# ============================================================
# 27. 재질별 환경요인 중요도
# ============================================================

st.header(
    "10. 재질별 대기환경 요인 중요도"
)


env_features = [

    "pm10",
    "pm25",
    "o3",
    "no2",
    "co",
    "so2",

    "pm_load",
    "pm10_7d",
    "pm25_7d",

    "oxidation_risk",
    "acid_risk",
    "corrosion_risk",

    "air_pollution_risk"
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


    if len(sub_df) < 30:

        st.warning(
            f"{material}: 데이터가 30개 미만입니다."
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


    # 클래스가 하나뿐이면 RandomForest 학습 불가능
    if y_sub.nunique() < 2:

        st.warning(

            f"{material}: "
            "위험도 클래스가 하나뿐이라 "
            "재질별 중요도를 계산할 수 없습니다."
        )

        continue


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


    st.write(
        "위험요인 TOP 10"
    )


    st.dataframe(

        material_importance.head(10),

        use_container_width=True
    )


    # --------------------------------------------------------
    # 재질별 그래프
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

        f"{material} 문화재 위험요인 TOP 10"
    )


    plt.tight_layout()


    st.pyplot(fig)


    plt.close(fig)


# ============================================================
# 28. 날짜별 대기오염 추이
# ============================================================

st.header(
    "11. 날짜별 대기오염 변화"
)


if "date" in df.columns:

    chart_df = df.copy()

    chart_df = chart_df.set_index(
        "date"
    )


    chart_cols = [

        "pm10",
        "pm25",
        "o3",
        "no2",
        "so2"
    ]


    st.line_chart(
        chart_df[chart_cols]
    )


# ============================================================
# 29. 최종 데이터
# ============================================================

st.header(
    "12. 최종 분석 데이터"
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
    "🎉 모든 문화재 대기환경 위험도 분석이 완료되었습니다!"
)
