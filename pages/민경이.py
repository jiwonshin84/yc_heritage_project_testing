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

import matplotlib.pyplot as plt

top10 = importance_df.head(10)

plt.figure(figsize=(8,5))
plt.barh(top10["Feature"], top10["Importance"])
plt.gca().invert_yaxis()
plt.xlabel("Importance")
plt.title("Environmental Feature Importance")
plt.show()
