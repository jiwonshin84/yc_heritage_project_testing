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
