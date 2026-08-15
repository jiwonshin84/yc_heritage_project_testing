# ============================================================
# 13. 데이터 분할 (X_train, y_train 정의 추가)
# ============================================================
from sklearn.model_selection import train_test_split

# FIXME: 아래 X, y에는 사용하시는 데이터프레임의 특성(X)과 타겟(y) 변수명을 넣어주세요.
# 예시: X = df.drop(columns=['target_column'])
# 예시: y = df['target_column']

# 학습용/테스트용 데이터 분할 (이 과정에서 X_train, y_train이 생성됩니다)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
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
