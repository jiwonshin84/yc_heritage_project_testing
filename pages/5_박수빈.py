import streamlit as st
import pandas as pd
import numpy as np
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
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
### 환경 데이터를 활용한 문화재 보존 AI 시스템

기상 데이터와 대기질 데이터를 기반으로
문화재 훼손 위험도를 분석합니다.
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

# ---------------------------------------------------
# 데이터 로드
# ---------------------------------------------------

try:

    df = load_data()

except Exception as e:

    st.error(f"데이터 로드 오류: {e}")

    st.stop()

# ---------------------------------------------------
# 데이터 미리보기
# ---------------------------------------------------

st.subheader("📊 데이터 미리보기")

st.dataframe(df.head())

# ---------------------------------------------------
# 결측치 처리
# ---------------------------------------------------

df = df.fillna(0)

# ---------------------------------------------------
# 숫자형 컬럼 선택
# ---------------------------------------------------

numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

st.subheader("📌 숫자형 컬럼")

st.write(numeric_cols)

# ---------------------------------------------------
# 숫자형 컬럼 부족 체크
# ---------------------------------------------------

if len(numeric_cols) < 5:

    st.error("숫자형 컬럼이 부족합니다.")

    st.stop()

# ---------------------------------------------------
# feature 선택
# ---------------------------------------------------

selected_features = numeric_cols[:5]

st.subheader("✅ 위험도 계산에 사용된 컬럼")

st.write(selected_features)

# ---------------------------------------------------
# 위험도 점수 생성
# ---------------------------------------------------

df["risk_score"] = (

    df[selected_features[0]] * 0.3 +

    df[selected_features[1]] * 0.2 +

    df[selected_features[2]] * 0.2 +

    df[selected_features[3]] * 0.2 +

    df[selected_features[4]] * 0.1

)

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
# 위험도 결과 출력
# ---------------------------------------------------

st.subheader("⚠ 위험도 결과")

st.dataframe(

    df[["risk_score", "risk_label"]].head()

)

# ---------------------------------------------------
# 위험도 분포 그래프
# ---------------------------------------------------

st.subheader("📈 위험도 분포")

risk_count = df["risk_label"].value_counts()

fig1, ax1 = plt.subplots(figsize=(6, 4))

ax1.bar(

    risk_count.index,

    risk_count.values

)

ax1.set_title("Risk Distribution")

ax1.set_xlabel("Risk Level")

ax1.set_ylabel("Count")

st.pyplot(fig1)

# ---------------------------------------------------
# 머신러닝 데이터 준비
# ---------------------------------------------------

X = df[numeric_cols]

le = LabelEncoder()

y = le.fit_transform(df["risk_label"])

# ---------------------------------------------------
# train / test split
# ---------------------------------------------------

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

# ---------------------------------------------------
# 결과 저장 리스트
# ---------------------------------------------------

results = []

# ---------------------------------------------------
# 모델 학습
# ---------------------------------------------------

st.subheader("🤖 머신러닝 모델 비교")

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

# ---------------------------------------------------
# 결과 데이터프레임
# ---------------------------------------------------

result_df = pd.DataFrame(results)

st.dataframe(result_df)

# ---------------------------------------------------
# Accuracy 그래프
# ---------------------------------------------------

st.subheader("📊 Accuracy 비교")

fig2, ax2 = plt.subplots(figsize=(8, 5))

ax2.bar(

    result_df["Model"],

    result_df["Accuracy"]

)

ax2.set_title("Model Accuracy")

ax2.set_ylabel("Accuracy")

st.pyplot(fig2)

# ---------------------------------------------------
# F1 Score 그래프
# ---------------------------------------------------

st.subheader("📊 F1-Score 비교")

fig3, ax3 = plt.subplots(figsize=(8, 5))

ax3.bar(

    result_df["Model"],

    result_df["F1-Score"]

)

ax3.set_title("Model F1-Score")

ax3.set_ylabel("F1 Score")

st.pyplot(fig3)

# ---------------------------------------------------
# Random Forest Feature Importance
# ---------------------------------------------------

st.subheader("🔥 Feature Importance")

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

top10 = importance.head(10)

# ---------------------------------------------------
# importance 그래프
# ---------------------------------------------------

fig4, ax4 = plt.subplots(figsize=(10, 6))

ax4.barh(

    top10["Feature"],

    top10["Importance"]

)

ax4.invert_yaxis()

ax4.set_title("Top 10 Important Features")

st.pyplot(fig4)

# ---------------------------------------------------
# confusion matrix
# ---------------------------------------------------

st.subheader("🧠 Confusion Matrix")

pred_rf = rf_model.predict(X_test)

cm = confusion_matrix(y_test, pred_rf)

fig5, ax5 = plt.subplots(figsize=(5, 5))

ax5.imshow(cm)

ax5.set_title("Random Forest Confusion Matrix")

ax5.set_xlabel("Predicted")

ax5.set_ylabel("Actual")

for i in range(len(cm)):

    for j in range(len(cm)):

        ax5.text(

            j,

            i,

            cm[i, j],

            ha="center",

            va="center"

        )

st.pyplot(fig5)

# ---------------------------------------------------
# 샘플 예측
# ---------------------------------------------------

st.subheader("🎯 샘플 위험도 예측")

sample = X.iloc[0:1]

prediction = rf_model.predict(sample)

label = le.inverse_transform(prediction)

st.success(f"예측 결과 : {label[0]}")

# ---------------------------------------------------
# 전체 데이터 보기
# ---------------------------------------------------

with st.expander("📄 전체 데이터 보기"):

    st.dataframe(df)

# ---------------------------------------------------
# footer
# ---------------------------------------------------

st.markdown("---")

st.markdown("""

### 👨‍💻 프로젝트 정보

- 프로젝트명 : 문화재 훼손 위험도 예측 시스템
- 개발도구 : Python / Streamlit
- 머신러닝 모델 :
    - Logistic Regression
    - Decision Tree
    - Random Forest

""")
