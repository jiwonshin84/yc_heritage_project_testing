# ============================================================
# 3. 머신러닝 데이터 학습
# ============================================================
X = dataset[
    [
        "temp_avg", "temp_max", "temp_min", "humidity",
        "rainfall", "wind_speed", "solar_radiation", "ground_temp",
        "pm10", "pm25", "o3", "no2", "co", "so2",
        "temp_range", "humidity_std3", "rainfall_7d",
        "high_humidity_risk", "weathering_risk", "mold_risk",
        "pm_load", "acid_risk", "oxidation_risk", "corrosion_risk",
        "material", "exposure"
    ]
]

y = dataset["target"]

X = pd.get_dummies(
    X,
    columns=["material", "exposure"]
)

# ----------------------------------------
# 데이터 상태 확인
# ----------------------------------------
if len(X) < 10:
    st.error(f"머신러닝 학습 데이터가 너무 적습니다. 현재 데이터: {len(X)}개")
    st.stop()

class_counts = y.value_counts()

# 위험등급이 2개 미만이면 학습 불가능
if len(class_counts) < 2:
    st.error("위험등급이 하나만 존재하여 머신러닝 학습이 불가능합니다.")
    st.write("현재 위험등급 분포:", class_counts)
    st.stop()

# ----------------------------------------
# stratify 가능 여부 확인
# ----------------------------------------
test_count = max(1, int(np.ceil(len(X) * 0.2)))

if class_counts.min() >= 2 and test_count >= len(class_counts):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
else:
    # 클래스별 데이터가 너무 적으면 stratify 사용 안 함
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

# ----------------------------------------
# Random Forest 학습
# ----------------------------------------
rf_model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train)

y_pred = rf_model.predict(X_test)

acc = accuracy_score(y_test, y_pred)

st.sidebar.subheader("🤖 모델 성능")
st.sidebar.text(f"RandomForest 정확도: {acc:.4f}")
