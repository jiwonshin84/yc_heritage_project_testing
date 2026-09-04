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
# 1. 필요한 기상 데이터 컬럼
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


# ============================================================
# 2. 프로젝트 안의 CSV 찾기
# ============================================================

st.header("1. 데이터 불러오기")

csv_files = glob.glob(
    "**/*.csv",
    recursive=True
)


if len(csv_files) == 0:

    st.error(
        "❌ 프로젝트 안에서 CSV 파일을 찾을 수 없습니다."
    )

    st.info(
        "GitHub 프로젝트에 CSV 파일이 업로드되어 있는지 확인해주세요."
    )

    st.stop()


st.success(
    f"CSV 파일 {len(csv_files)}개를 찾았습니다."
)


# ============================================================
# 3. 각 CSV의 컬럼 확인
# ============================================================

csv_info = []


for file in csv_files:

    try:

        temp_df = pd.read_csv(
            file,
            encoding="utf-8-sig",
            nrows=5
        )

    except Exception:

        try:

            temp_df = pd.read_csv(
                file,
                encoding="cp949",
                nrows=5
            )

        except Exception:

            continue


    temp_df.columns = (
        temp_df.columns
        .astype(str)
        .str.strip()
    )


    columns = temp_df.columns.tolist()


    # 필요한 기상 컬럼이 몇 개 있는지 계산
    match_count = sum(
        col in columns
        for col in required_cols
    )


    csv_info.append({

        "file": file,

        "columns": columns,

        "match_count": match_count
    })


# ============================================================
# 4. CSV 선택
# ============================================================

if len(csv_info) == 0:

    st.error(
        "CSV 파일을 읽을 수 없습니다."
    )

    st.stop()


# 필요한 컬럼이 가장 많은 CSV
best_csv = max(
    csv_info,
    key=lambda x: x["match_count"]
)


# 필요한 컬럼을 모두 가지고 있는 파일이 있으면
# 그 파일을 자동 선택
perfect_matches = [

    item["file"]

    for item in csv_info

    if item["match_count"] == len(required_cols)
]


if len(perfect_matches) > 0:

    default_file = perfect_matches[0]

else:

    default_file = best_csv["file"]


# ============================================================
# 5. CSV 선택 메뉴
# ============================================================

st.subheader(
    "CSV 파일 선택"
)


csv_names = [
    item["file"]
    for item in csv_info
]


default_index = csv_names.index(
    default_file
)


selected_file = st.selectbox(
    "사용할 CSV 파일",
    csv_names,
    index=default_index
)


# 선택한 파일의 정보
selected_info = next(
    item
    for item in csv_info
    if item["file"] == selected_file
)


st.info(
    f"📂 현재 선택된 파일: `{selected_file}`"
)


st.write(
    f"필요한 기상 컬럼 일치 개수: "
    f"**{selected_info['match_count']} / {len(required_cols)}**"
)


with st.expander(
    "선택된 CSV의 컬럼 확인"
):

    st.write(
        selected_info["columns"]
    )


# ============================================================
# 6. CSV 실제로 읽기
# ============================================================

try:

    df = pd.read_csv(
        selected_file,
        encoding="utf-8-sig"
    )

except UnicodeDecodeError:

    try:

        df = pd.read_csv(
            selected_file,
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


# 컬럼명 정리
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


st.write(
    "데이터 크기:",
    df.shape
)


# ============================================================
# 7. 필요한 컬럼 확인
# ============================================================

missing_cols = [

    col

    for col in required_cols

    if col not in df.columns
]


if missing_cols:

    st.error(
        "❌ 필요한 기상 데이터 컬럼이 없습니다."
    )


    st.write(
        "없는 컬럼:"
    )

    st.write(
        missing_cols
    )


    st.write(
        "현재 CSV에 실제로 존재하는 컬럼:"
    )

    st.code(
        "\n".join(df.columns.tolist())
    )


    st.warning(
        "위의 CSV 선택 메뉴에서 다른 기상 데이터 CSV를 선택해보세요."
    )


    st.stop()


# ============================================================
# 8. 숫자형 변환
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
# 9. 파생변수 생성
# ============================================================

st.header(
    "3. 환경 위험요인 계산"
)


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


df = df.fillna(0)


st.success(
    "환경 위험요인 계산 완료!"
)


# ============================================================
# 10. 재질 × 노출 조합
# ============================================================

st.header(
    "4. 문화재 재질 × 노출환경"
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
# 11. 위험요인 정규화
# ============================================================

st.header(
    "5. 위험도 정규화"
)


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
# 12. 위험도 계산
# ============================================================

st.header(
    "6. 문화재 위험도 계산"
)


def calc_risk(row):

    material = row["material"]

    exposure = row["exposure"]


    # --------------------------------------------------------
    # 석조
    # --------------------------------------------------------

    if material == "석조":

        risk = (

            row["weathering_risk_norm"] * 0.25

            + row["acid_risk_norm"] * 0.20

            + row["rainfall_7d_norm"] * 0.18

            + row["temp_range_norm"] * 0.15

            + row["pm_load_norm"] * 0.12

            + row["corrosion_risk_norm"] * 0.10
        )


    # --------------------------------------------------------
    # 목조
    # --------------------------------------------------------

    elif material == "목조":

        risk = (

            row["mold_risk_norm"] * 0.25

            + row["humidity_std3_norm"] * 0.20

            + row["high_humidity_risk_norm"] * 0.18

            + row["rainfall_7d_norm"] * 0.15

            + row["oxidation_risk_norm"] * 0.12

            + row["pm_load_norm"] * 0.10
        )


    # --------------------------------------------------------
    # 금속
    # --------------------------------------------------------

    elif material == "금속":

        risk = (

            row["corrosion_risk_norm"] * 0.30

            + row["acid_risk_norm"] * 0.22

            + row["high_humidity_risk_norm"] * 0.18

            + row["humidity_std3_norm"] * 0.12

            + row["pm_load_norm"] * 0.10

            + row["weathering_risk_norm"] * 0.08
        )


    # --------------------------------------------------------
    # 회화
    # --------------------------------------------------------

    elif material == "회화":

        risk = (

            row["oxidation_risk_norm"] * 0.28

            + row["pm_load_norm"] * 0.20

            + row["humidity_std3_norm"] * 0.18

            + row["high_humidity_risk_norm"] * 0.14

            + row["temp_range_norm"] * 0.10

            + row["weathering_risk_norm"] * 0.10
        )


    # --------------------------------------------------------
    # 기타
    # --------------------------------------------------------

    else:

        risk = (

            row["weathering_risk_norm"] * 0.20

            + row["acid_risk_norm"] * 0.20

            + row["oxidation_risk_norm"] * 0.20

            + row["corrosion_risk_norm"] * 0.20

            + row["pm_load_norm"] * 0.20
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
# 13. 위험도 라벨
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
# 14. 위험도 분포
# ============================================================

st.header(
    "7. 문화재 위험도 분포"
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
# 15. 머신러닝 데이터 구성
# ============================================================

st.header(
    "8. 머신러닝 분석"
)


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


# 범주형 변수 처리
X = pd.get_dummies(
    X,
    columns=[
        "material",
        "exposure"
    ]
)


X = X.fillna(0)


# ============================================================
# 16. 클래스 확인
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


if y.nunique() < 2:

    st.error(
        "위험도 클래스가 2개 이상 필요합니다."
    )

    st.stop()


# ============================================================
# 17. 데이터 분할
# ============================================================

# 각 클래스가 최소 2개 이상 있는지 확인
if class_count.min() < 2:

    st.error(
        "각 위험도 클래스의 데이터가 최소 2개 이상 필요합니다."
    )

    st.stop()


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
# 18. 모델 정의
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
# 19. RandomForest / GradientBoosting
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
# 20. Logistic Regression
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
# 21. 모델 평가
# ============================================================

st.header(
    "9. 모델 성능 비교"
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
# 22. 결과표
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
# 23. 최고 모델
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
# 24. 상세 평가
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
# 25. 환경요인 중요도
# ============================================================

st.header(
    "10. 환경요인 중요도"
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
        .str.startswith(
            "material_"
        )
    ]
)


importance_df = (
    importance_df[
        ~importance_df["Feature"]
        .str.startswith(
            "exposure_"
        )
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
    "Environmental Feature Importance"
)


plt.tight_layout()


st.pyplot(fig)


plt.close(fig)


# ============================================================
# 27. 재질별 환경요인 중요도
# ============================================================

st.header(
    "11. 재질별 환경요인 중요도"
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


    if y_sub.nunique() < 2:

        st.warning(
            f"{material}: 위험도 클래스가 하나뿐이라 분석할 수 없습니다."
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


    # 그래프
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
# 28. 최종 데이터 확인
# ============================================================

st.header(
    "12. 분석 데이터"
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
    "🎉 모든 문화재 환경 위험도 분석이 완료되었습니다!"
)
