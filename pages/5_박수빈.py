```python
import streamlit as st
import pandas as pd
import numpy as np
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# ---------------------------------------------------
# 페이지 설정
# ---------------------------------------------------

st.set_page_config(
    page_title="문화재 훼손 위험도 예측",
    layout="wide"
)

# ---------------------------------------------------
# 제목
# ---------------------------------------------------

st.title("🏛 문화재 훼손 위험도 예측 시스템")

st.markdown("""
환경 데이터를 기반으로  
문화재 훼손 위험도를 예측하는 AI 시스템입니다.
""")

# ---------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------

@st.cache_data
def load_data():

    BASE_DIR = os.path.dirname(
        os.path.dirname(__file__)
    )

    file_path = os.path.join(
        BASE_DIR,
        "data",
        "processed",
        "yc_heritage_feature.csv"
    )

    df = pd.read_csv(file_path)

    return df

try:

    df = load_data()

except Exception as e:

    st.error(f"데이터 로드 오류 : {e}")

    st.stop()

# ---------------------------------------------------
# 결측치 처리
# ---------------------------------------------------

df = df.fillna(0)

# ---------------------------------------------------
# 컬럼 확인
# ---------------------------------------------------

st.subheader("📌 데이터 컬럼")

st.write(df.columns.tolist())

# ---------------------------------------------------
# 환경 데이터 컬럼 선택
# 실제 컬럼명에 맞게 수정 가능
# ---------------------------------------------------

environment_features = [

    "temp",
    "humidity",
    "rainfall",
    "wind_speed",
    "pm10",
    "pm25"

]

# ---------------------------------------------------
# 실제 존재하는 컬럼만 사용
# ---------------------------------------------------

selected_features = []

for col in environment_features:

    if col in df.columns:

        selected_features.append(col)

# ---------------------------------------------------
# 컬럼 부족 체크
# ---------------------------------------------------

if len(selected_features) < 3:

    st.warning("환경 컬럼명이 다를 수 있습니다.")

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    selected_features = numeric_cols[:5]

# ---------------------------------------------------
# 사용 컬럼 출력
# ---------------------------------------------------

st.subheader("🌎 사용 환경 데이터")

st.write(selected_features)

# ---------------------------------------------------
# 위험도 점수 생성
# ---------------------------------------------------

weights = [0.3, 0.2, 0.2, 0.2, 0.1]

risk_score = 0

for i in range(len(selected_features)):

    risk_score += df[selected_features[i]] * weights[i]

df["risk_score"] = risk_score

# ---------------------------------------------------
# 정규화
# ---------------------------------------------------

min_score = df["risk_score"].min()

max_score = df["risk_score"].max()

df["risk_score"] = (

    (df["risk_score"] - min_score)

    /

    (max_score - min_score)

) * 100

# ---------------------------------------------------
# 위험도 라벨 생성
# ---------------------------------------------------

def classify_risk(score):

    if score < 33:

        return "안전"

    elif score < 66:

        return "주의"

    else:

        return "위험"

df["risk_label"] = df["risk_score"].apply(classify_risk)

# ---------------------------------------------------
# 상단 카드 UI
# ---------------------------------------------------

safe_count = len(df[df["risk_label"] == "안전"])

warn_count = len(df[df["risk_label"] == "주의"])

danger_count = len(df[df["risk_label"] == "위험"])

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "전체 데이터",
        len(df)
    )

with col2:

    st.success(f"안전 : {safe_count}")

with col3:

    st.warning(f"주의 : {warn_count}")

with col4:

    st.error(f"위험 : {danger_count}")

# ---------------------------------------------------
# 탭 생성
# ---------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([

    "📊 대시보드",

    "🤖 모델 비교",

    "🔥 환경 영향도",

    "🎯 위험도 예측"

])

# ---------------------------------------------------
# 대시보드
# ---------------------------------------------------

with tab1:

    st.subheader("위험도 분포")

    risk_count = df["risk_label"].value_counts()

    st.bar_chart(risk_count)

    st.subheader("데이터 미리보기")

    st.dataframe(df.head())

# ---------------------------------------------------
# 머신러닝 데이터 준비
# ---------------------------------------------------

X = df[selected_features]

le = LabelEncoder()

y = le.fit_transform(df["risk_label"])

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.2,
    random_state=42

)

# ---------------------------------------------------
# 모델 정의
# ---------------------------------------------------

models = {

    "Logistic Regression": LogisticRegression(max_iter=1000),

    "Decision Tree": DecisionTreeClassifier(),

    "Random Forest": RandomForestClassifier()

}

results = []

# ---------------------------------------------------
# 모델 학습
# ---------------------------------------------------

for name, model in models.items():

    model.fit(X_train, y_train)

    pred = model.predict(X_test)

    acc = accuracy_score(y_test, pred)

    pre = precision_score(
        y_test,
        pred,
        average="weighted"
    )

    rec = recall_score(
        y_test,
        pred,
        average="weighted"
    )

    f1 = f1_score(
        y_test,
        pred,
        average="weighted"
    )

    results.append({

        "Model": name,

        "Accuracy": round(acc, 3),

        "Precision": round(pre, 3),

        "Recall": round(rec, 3),

        "F1-Score": round(f1, 3)

    })

result_df = pd.DataFrame(results)

# ---------------------------------------------------
# 모델 비교 탭
# ---------------------------------------------------

with tab2:

    st.subheader("모델 성능 비교")

    st.dataframe(result_df)

    st.subheader("Accuracy 비교")

    st.bar_chart(
        result_df.set_index("Model")["Accuracy"]
    )

    st.subheader("F1-Score 비교")

    st.bar_chart(
        result_df.set_index("Model")["F1-Score"]
    )

# ---------------------------------------------------
# Random Forest Feature Importance
# ---------------------------------------------------

rf_model = RandomForestClassifier()

rf_model.fit(X_train, y_train)

importance = pd.DataFrame({

    "Feature": X.columns,

    "Importance": rf_model.feature_importances_

})

importance = importance.sort_values(

    by="Importance",

    ascending=False

)

# ---------------------------------------------------
# 환경 영향도 탭
# ---------------------------------------------------

with tab3:

    st.subheader("환경요인 중요도")

    st.bar_chart(
        importance.set_index("Feature")
    )

    st.dataframe(importance)

# ---------------------------------------------------
# 위험도 예측 탭
# ---------------------------------------------------

with tab4:

    st.subheader("실시간 위험도 예측")

    input_values = {}

    for feature in selected_features:

        input_values[feature] = st.slider(

            feature,

            0.0,

            100.0,

            50.0

        )

    if st.button("위험도 예측"):

        input_df = pd.DataFrame([input_values])

        pred = rf_model.predict(input_df)

        label = le.inverse_transform(pred)

        if label[0] == "안전":

            st.success(f"예측 결과 : {label[0]}")

        elif label[0] == "주의":

            st.warning(f"예측 결과 : {label[0]}")

        else:

            st.error(f"예측 결과 : {label[0]}")

# ---------------------------------------------------
# footer
# ---------------------------------------------------

st.markdown("---")

st.markdown("""

### 👨‍💻 프로젝트 정보

- 프로젝트명 : 문화재 훼손 위험도 예측 시스템
- 사용기술 : Python / Streamlit / Machine Learning
- 머신러닝 모델 :
    - Logistic Regression
    - Decision Tree
    - Random Forest

""")
```
