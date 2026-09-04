# ============================================================
# 7. 파생변수 생성
# ============================================================

df["temp_range"] = df["temp_max"] - df["temp_min"]

df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std()

df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()

df["high_humidity_risk"] = (df["humidity"] >= 75).rolling(3, min_periods=1).sum()

df["weathering_risk"] = (
    df["temp_range"] * 0.4 +
    df["humidity_std3"] * 0.3 +
    df["wind_speed"] * 0.3
)

df["mold_risk"] = ((df["humidity"] >= 75) & (df["ground_temp"] >= 15)).astype(int)

df["pm_load"] = (df["pm10"] + df["pm25"]).rolling(3, min_periods=1).sum()

df["acid_risk"] = df["so2"] * 0.6 + df["no2"] * 0.4

df["oxidation_risk"] = df["o3"] * 0.7 + df["pm25"] * 0.3

df["corrosion_risk"] = df["humidity"] * 0.5 + df["so2"] * 0.5

df = df.fillna(0)
# ============================================================
# 8. 재질 × 노출 조합
# ============================================================
import itertools


materials = ["석조", "목조", "금속", "회화", "기타"]
exposures = ["실외", "반실외", "실내"]

comb = pd.DataFrame(
    list(itertools.product(materials, exposures)),
    columns=["material", "exposure"]
)

df["key"] = 1
comb["key"] = 1

dataset = pd.merge(df, comb, on="key").drop("key", axis=1)
# ============================================================
# 9. 정규화

# rainfall_7d      0 ~ 200
# pm_load          0 ~ 500
# mold_risk        0 ~ 1
# humidity_std3  0 ~ 10

# ============================================================

risk_cols = [
    "weathering_risk","acid_risk","rainfall_7d",
    "temp_range","pm_load","corrosion_risk",
    "mold_risk","humidity_std3","oxidation_risk",
    "high_humidity_risk"
]

# min-max 정규화
for col in risk_cols:
    dataset[col+"_norm"] = (
        (dataset[col] - dataset[col].min()) /
        (dataset[col].max() - dataset[col].min() + 1e-6)
    ) * 100
# ============================================================
# 10. 위험도 계산 (LABEL 생성용)
# ============================================================

def calc_risk(row):

    m = row["material"]
    e = row["exposure"]

    if m == "석조":
        r = (row["weathering_risk_norm"]*0.25 +
             row["acid_risk_norm"]*0.20 +
             row["rainfall_7d_norm"]*0.18 +
             row["temp_range_norm"]*0.15 +
             row["pm_load_norm"]*0.12 +
             row["corrosion_risk_norm"]*0.10)

    elif m == "목조":
        r = (row["mold_risk_norm"]*0.25 +
             row["humidity_std3_norm"]*0.20 +
             row["high_humidity_risk_norm"]*0.18 +
             row["rainfall_7d_norm"]*0.15 +
             row["oxidation_risk_norm"]*0.12 +
             row["pm_load_norm"]*0.10)

    elif m == "금속":
        r = (row["corrosion_risk_norm"]*0.30 +
             row["acid_risk_norm"]*0.22 +
             row["high_humidity_risk_norm"]*0.18 +
             row["humidity_std3_norm"]*0.12 +
             row["pm_load_norm"]*0.10 +
             row["weathering_risk_norm"]*0.08)

    elif m == "회화":
        r = (row["oxidation_risk_norm"]*0.28 +
             row["pm_load_norm"]*0.20 +
             row["humidity_std3_norm"]*0.18 +
             row["high_humidity_risk_norm"]*0.14 +
             row["temp_range_norm"]*0.10 +
             row["weathering_risk_norm"]*0.10)

    else:
        r = (row["weathering_risk_norm"]*0.2 +
             row["acid_risk_norm"]*0.2 +
             row["oxidation_risk_norm"]*0.2 +
             row["corrosion_risk_norm"]*0.2 +
             row["pm_load_norm"]*0.2)

    if e == "실외":
        r *= 1.3
    elif e == "반실외":
        r *= 1.1
    else:
        r *= 0.85

    return min(r, 100)

dataset["material_risk"] = dataset.apply(calc_risk, axis=1)

# ============================================================
# 11. 라벨 생성
# ============================================================

def label(x):
    if x >= 80:
        return "위험"
    elif x >= 40:
        return "주의"
    else:
        return "안전"

dataset["target"] = dataset["material_risk"].apply(label)
# ============================================================
# 12. 머신러닝 데이터 구성
# ============================================================

X = dataset[
    [
        "temp_avg","temp_max","temp_min","humidity",
        "rainfall","wind_speed","solar_radiation",
        "ground_temp","pm10","pm25","o3","no2","co","so2",
        "temp_range","humidity_std3","rainfall_7d",
        "high_humidity_risk","weathering_risk","mold_risk",
        "pm_load","acid_risk","oxidation_risk","corrosion_risk",
        "material","exposure"
    ]
]

y = dataset["target"]

X = pd.get_dummies(X, columns=["material","exposure"])
# ============================================================
# 13. train/test split
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
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
for name, model in trained_models.items():

    if name == "LogisticRegression":
        lr_model, scaler = model
        y_pred = lr_model.predict(X_test_scaled)
    else:
        y_pred = model.predict(X_test)

    print(f"\n===== {name} 결과 =====")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))
    from sklearn.metrics import accuracy_score

results = {}

for name, model in trained_models.items():

    if name == "LogisticRegression":
        lr_model, scaler = model
        y_pred = lr_model.predict(X_test_scaled)
    else:
        y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    results[name] = acc

    print(f"{name} Accuracy : {acc:.4f}")

# ============================================================
# 최고 성능 모델 찾기
# ============================================================

best_model_name = max(results, key=results.get)
best_accuracy = results[best_model_name]

print("\n" + "="*50)
print(f"최고 성능 모델 : {best_model_name}")
print(f"정확도 : {best_accuracy:.4f}")
print("="*50)
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
# ============================================================
# 15. 재질별 환경요인 중요도 분석
# ============================================================

from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import matplotlib.pyplot as plt

env_features = [
    "temp_avg","temp_max","temp_min","humidity",
    "rainfall","wind_speed","solar_radiation",
    "ground_temp","pm10","pm25","o3","no2","co","so2",
    "temp_range","humidity_std3","rainfall_7d",
    "high_humidity_risk","weathering_risk","mold_risk",
    "pm_load","acid_risk","oxidation_risk","corrosion_risk"
]

materials = ["석조","목조","금속","회화"]

for material in materials:

    print("\n" + "="*60)
    print(f"{material} 문화재")
    print("="*60)

    # 해당 재질만 추출
    sub_df = dataset[
        dataset["material"] == material
    ]

    # 데이터가 너무 적으면 건너뜀
    if len(sub_df) < 30:
        print("데이터 부족")
        continue

    X_sub = sub_df[env_features]
    y_sub = sub_df["target"]

    # 모델 학습
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    model.fit(X_sub, y_sub)

    # 중요도 계산
    importance_df = pd.DataFrame({
        "Feature": env_features,
        "Importance": model.feature_importances_
    })

    importance_df = importance_df.sort_values(
        "Importance",
        ascending=False
    )

    # 출력
    print("\nTOP 10 위험 요인")
    print(importance_df.head(10))

    # 시각화
    top10 = importance_df.head(10)

    plt.figure(figsize=(8,5))
    plt.barh(
        top10["Feature"][::-1],
        top10["Importance"][::-1]
    )

    plt.title(f"{material} 문화재 위험요인 TOP 10")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.show()
    
