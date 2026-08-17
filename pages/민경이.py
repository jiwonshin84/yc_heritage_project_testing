# ============================================================
# 변수 중요도 분석 (재질·노출 제외)
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# ------------------------------------------------------------
# 1. 앞 단계에서 선정된 최적 모델 불러오기
# ------------------------------------------------------------

best_model = trained_models[best_model_name]


# ------------------------------------------------------------
# 2. 분석할 환경 변수만 선택
#    재질(material), 노출(exposure) 관련 변수는 제외
# ------------------------------------------------------------

feature_cols = [
    c for c in X_train.columns
    if not c.startswith("material_")
    and not c.startswith("exposure_")
    and c != "material"
    and c != "exposure"
]


# ------------------------------------------------------------
# 3. 변수 중요도 계산
# ------------------------------------------------------------

if best_model_name == "LogisticRegression":

    # LogisticRegression을
    # (모델, scaler) 형태로 저장했다고 가정
    lr_model, scaler = best_model

    importance_df = pd.DataFrame({
        "Feature": X_train.columns,
        "Importance": np.mean(
            np.abs(lr_model.coef_),
            axis=0
        )
    })

else:

    # RandomForest, DecisionTree 등
    # feature_importances_를 지원하는 모델
    importance_df = pd.DataFrame({
        "Feature": X_train.columns,
        "Importance": best_model.feature_importances_
    })


# ------------------------------------------------------------
# 4. 재질·노출 관련 변수 제거
# ------------------------------------------------------------

importance_df = importance_df[
    importance_df["Feature"].isin(feature_cols)
].copy()


# ------------------------------------------------------------
# 5. 중요도가 높은 순서대로 정렬
# ------------------------------------------------------------

importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
).reset_index(drop=True)


# ------------------------------------------------------------
# 6. 상위 10개 환경 변수 추출
# ------------------------------------------------------------

top10 = importance_df.head(10)


# ------------------------------------------------------------
# 7. Streamlit 화면에 결과 출력
# ------------------------------------------------------------

st.title("🌦️ 문화재 환경 요인 중요도 분석")

st.write(
    f"사용된 최적 모델: **{best_model_name}**"
)

st.subheader("📊 환경 요인 중요도 TOP 10")

st.dataframe(
    top10,
    use_container_width=True
)


# ------------------------------------------------------------
# 8. 중요도 그래프
# ------------------------------------------------------------

fig, ax = plt.subplots(figsize=(8, 5))

ax.barh(
    top10["Feature"],
    top10["Importance"]
)

ax.invert_yaxis()

ax.set_xlabel("Importance")
ax.set_ylabel("Environmental Feature")
ax.set_title("Environmental Feature Importance")

plt.tight_layout()

st.pyplot(fig)



# ============================================================
# 15. 재질별 환경요인 중요도 분석
# ============================================================

from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# 분석에 사용할 환경 변수
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


# 분석할 문화재 재질
materials = [
    "석조",
    "목조",
    "금속",
    "회화"
]


st.title("🏛️ 재질별 환경요인 중요도 분석")


for material in materials:

    st.subheader(f"📌 {material} 문화재")

    # --------------------------------------------------------
    # 1. 해당 재질의 문화재 데이터만 추출
    # --------------------------------------------------------

    sub_df = dataset[
        dataset["material"] == material
    ].copy()


    # --------------------------------------------------------
    # 2. 데이터가 너무 적으면 분석하지 않음
    # --------------------------------------------------------

    if len(sub_df) < 30:

        st.warning(
            f"{material} 문화재는 데이터가 부족하여 "
            f"분석하지 않았습니다. ({len(sub_df)}건)"
        )

        continue


    # --------------------------------------------------------
    # 3. 필요한 컬럼의 결측값 제거
    # --------------------------------------------------------

    sub_df = sub_df.dropna(
        subset=env_features + ["target"]
    )


    if len(sub_df) < 30:

        st.warning(
            f"{material} 문화재는 결측값 제거 후 "
            f"데이터가 부족합니다. ({len(sub_df)}건)"
        )

        continue


    # --------------------------------------------------------
    # 4. 독립변수 X / 목표변수 y 설정
    # --------------------------------------------------------

    X_sub = sub_df[env_features]

    y_sub = sub_df["target"]


    # target 값이 하나뿐이면 분류 분석 불가능
    if y_sub.nunique() < 2:

        st.warning(
            f"{material} 문화재는 target 값이 "
            "한 종류뿐이라 중요도 분석을 할 수 없습니다."
        )

        continue


    # --------------------------------------------------------
    # 5. Random Forest 모델 학습
    # --------------------------------------------------------

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    model.fit(
        X_sub,
        y_sub
    )


    # --------------------------------------------------------
    # 6. 환경요인 중요도 계산
    # --------------------------------------------------------

    importance_df = pd.DataFrame({

        "Feature": env_features,

        "Importance": model.feature_importances_

    })


    # 중요도가 높은 순서로 정렬
    importance_df = importance_df.sort_values(

        by="Importance",

        ascending=False

    ).reset_index(drop=True)


    # --------------------------------------------------------
    # 7. TOP 10 환경요인 추출
    # --------------------------------------------------------

    top10 = importance_df.head(10)


    # --------------------------------------------------------
    # 8. Streamlit 표 출력
    # --------------------------------------------------------

    st.write(
        f"**{material} 문화재 위험요인 TOP 10**"
    )

    st.dataframe(
        top10,
        use_container_width=True
    )


    # --------------------------------------------------------
    # 9. 그래프 시각화
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    ax.barh(
        top10["Feature"][::-1],
        top10["Importance"][::-1]
    )

    ax.set_title(
        f"{material} 문화재 위험요인 TOP 10"
    )

    ax.set_xlabel(
        "Importance"
    )

    ax.set_ylabel(
        "Environmental Feature"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)
