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
