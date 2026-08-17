# ============================================================
# 14. 변수 중요도 분석 (재질·노출 제외)
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.ensemble import RandomForestClassifier


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
        "Importance": np.mean(
            np.abs(lr_model.coef_),
            axis=0
        )
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

# 중요도 순으로 정렬
importance_df = importance_df.sort_values(
    "Importance",
    ascending=False
)

# 상위 10개
top10 = importance_df.head(10)

st.subheader("🌦️ 환경 요인 중요도 TOP 10")

st.dataframe(
    top10,
    use_container_width=True
)

fig, ax = plt.subplots(figsize=(8, 5))

ax.barh(
    top10["Feature"],
    top10["Importance"]
)

ax.invert_yaxis()
ax.set_xlabel("Importance")
ax.set_title("Environmental Feature Importance")

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)


# ============================================================
# 15. 재질별 환경요인 중요도 분석
# ============================================================

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

materials = [
    "석조",
    "목조",
    "금속",
    "회화"
]

st.header("🧱 재질별 환경요인 중요도 분석")

for material in materials:

    st.subheader(f"📌 {material} 문화재")

    # 해당 재질만 추출
    sub_df = dataset[
        dataset["material"] == material
    ].copy()

    # 데이터가 너무 적으면 건너뜀
    if len(sub_df) < 30:

        st.warning(
            f"{material} 문화재는 데이터가 부족합니다."
        )

        continue

    X_sub = sub_df[env_features]
    y_sub = sub_df["target"]

    # Random Forest 모델 학습
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    model.fit(
        X_sub,
        y_sub
    )

    # 중요도 계산
    material_importance_df = pd.DataFrame({
        "Feature": env_features,
        "Importance": model.feature_importances_
    })

    material_importance_df = (
        material_importance_df
        .sort_values(
            "Importance",
            ascending=False
        )
    )

    # 상위 10개
    material_top10 = material_importance_df.head(10)

    st.dataframe(
        material_top10,
        use_container_width=True
    )

    # 시각화
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.barh(
        material_top10["Feature"][::-1],
        material_top10["Importance"][::-1]
    )

    ax.set_title(
        f"{material} 문화재 위험요인 TOP 10"
    )

    ax.set_xlabel("Importance")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
