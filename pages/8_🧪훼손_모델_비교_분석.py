import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

# ==========================================================
# 0. 설정 및 초기화
# ==========================================================
st.set_page_config(page_title="영천 문화재 AI 분석 센터", page_icon="🏛", layout="wide")

# 한글 폰트 설정 (Streamlit Cloud 환경 배포 시 주의 필요)
plt.rc('font', family='NanumGothic') 

# 사이드바 메뉴 구성
menu = st.sidebar.radio("메뉴 선택", ["실시간 위험 예측", "모델 성능 비교 분석"])

# ==========================================================
# 1. 데이터 로드 및 전처리 로직 (구글 시트 기반)
# ==========================================================
@st.cache_data
def get_integrated_data():
    """구글 시트에서 날씨/대기 데이터를 가져와 파생변수를 생성하고 병합함"""
    # 1. 데이터 불러오기 (제공된 URL)
    weather_url = "https://docs.google.com/spreadsheets/d/1l3cH2f6YATxJHxr3QWjIpwvc9QKPmHAJ/export?format=csv&gid=205029320"
    air_url = "https://docs.google.com/spreadsheets/d/1ao2TtZyLMNcpSsFPxdxYWZ5alAgc2aKjn5z7KomD6kA/export?format=csv&gid=1366576330"
    
    weather = pd.read_csv(weather_url)
    air = pd.read_csv(air_url)
    
    # 2. 날짜 형식 통일 및 병합
    weather["date"] = pd.to_datetime(weather["date"])
    air["date"] = pd.to_datetime(air["date"])
    df = pd.merge(weather, air, on="date", how="inner").ffill()
    
    # 3. 파생 변수 생성 (논문 및 기준 근거)
    df["temp_change"] = df["temp"].diff().fillna(0)
    df["humidity_change"] = df["humidity"].diff().fillna(0)
    df["dew_point"] = df["temp"] - ((100 - df["humidity"]) / 5)
    df["dew_gap"] = df["temp"] - df["dew_point"]
    df["humidity_ma3"] = df["humidity"].rolling(3).mean().fillna(df["humidity"])
    df["pm10_ma3"] = df["pm10"].rolling(3).mean().fillna(df["pm10"])
    df["temp_std"] = df["temp"].rolling(3).std().fillna(0)
    df["humidity_std"] = df["humidity"].rolling(3).std().fillna(0)
    df["pm_load"] = (df["pm10"] + df["pm25"]).rolling(3).sum().fillna(0)
    
    # 4. 절대 기준값 기반 Target(위험도) 생성
    def get_risk_label(row):
        # 습도(0.3), 온도(0.2), 결로(0.2), 미세먼지(0.15), 온도급변(0.1), 습도급변(0.05)
        h_score = 2 if (row["humidity"] >= 75 or row["humidity"] < 35) else (1 if (row["humidity"] >= 65 or row["humidity"] < 45) else 0)
        t_score = 2 if (row["temp"] > 30 or row["temp"] < 5) else (1 if (row["temp"] > 25 or row["temp"] < 15) else 0)
        d_score = 2 if row["dew_gap"] < 2 else (1 if row["dew_gap"] < 5 else 0)
        p_score = 2 if row["pm10"] >= 80 else (1 if row["pm10"] >= 30 else 0)
        tc_score = 2 if abs(row["temp_change"]) >= 10 else (1 if abs(row["temp_change"]) >= 5 else 0)
        hc_score = 2 if abs(row["humidity_change"]) >= 30 else (1 if abs(row["humidity_change"]) >= 15 else 0)
        
        weighted = (h_score * 0.3) + (t_score * 0.2) + (d_score * 0.2) + (p_score * 0.15) + (tc_score * 0.1) + (hc_score * 0.05)
        return 2 if weighted >= 1.2 else (1 if weighted >= 0.5 else 0)

    df["risk"] = df.apply(get_risk_label, axis=1)
    return df

# 데이터 로드
train_df = get_integrated_data()
features = ["temp", "humidity", "pm10", "pm25", "temp_change", "humidity_change", "dew_gap", "humidity_ma3", "pm10_ma3", "temp_std", "humidity_std", "pm_load"]

# ==========================================================
# 2. 모델 비교 분석 페이지
# ==========================================================
if menu == "모델 성능 비교 분석":
    st.title("🧪 머신러닝 알고리즘별 성능 비교")
    
    X = train_df[features]
    y = train_df["risk"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    models = {
        "Decision Tree": DecisionTreeClassifier(max_depth=6, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=200, class_weight="balanced"),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100)
    }

    acc_results = {}
    model_objs = {}

    st.subheader("1️⃣ 모델별 예측 정확도")
    cols = st.columns(3)
    
    for idx, (name, model) in enumerate(models.items()):
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        acc_results[name] = acc
        model_objs[name] = model
        cols[idx].metric(name, f"{acc:.2%}")

    # 정확도 그래프
    fig_acc, ax_acc = plt.subplots(figsize=(10, 4))
    sns.barplot(x=list(acc_results.keys()), y=list(acc_results.values()), palette="magma", ax=ax_acc)
    ax_acc.set_title("Algorithm Accuracy Comparison")
    st.pyplot(fig_acc)

    st.divider()

    # 변수 중요도 분석
    st.subheader("2️⃣ 어떤 지표가 위험 결정에 중요했는가? (Feature Importance)")
    selected_model_name = st.selectbox("분석할 모델 선택", list(models.keys()))
    sel_model = model_objs[selected_model_name]
    
    if hasattr(sel_model, "feature_importances_"):
        imp_df = pd.DataFrame({'Feature': features, 'Importance': sel_model.feature_importances_})
        imp_df = imp_df.sort_values(by='Importance', ascending=True)
        
        fig_imp, ax_imp = plt.subplots()
        ax_imp.barh(imp_df['Feature'], imp_df['Importance'], color='teal')
        ax_imp.set_title(f"변수 중요도 - {selected_model_name}")
        st.pyplot(fig_imp)
    else:
        st.warning("선택한 모델은 변수 중요도를 지원하지 않습니다.")

# ==========================================================
# 3. 실시간 위험 예측 페이지 (기존 코드 통합)
# ==========================================================
elif menu == "실시간 위험 예측":
    st.title("🏛 실시간 영천 문화재 훼손 위험 분석")
    
    # [생략] 기존 실시간 API 호출 및 UI 로직 (제공해주신 코드의 Section 3~7)
    # 아래는 모델 연동 부분 예시
    st.info("현재 분석 알고리즘: RandomForest (학습된 모델 사용 중)")
    
    # 학습된 베스트 모델 하나를 고정 사용
    final_model = RandomForestClassifier(n_estimators=200, class_weight="balanced").fit(train_df[features], train_df["risk"])
    
    # [이후 기존 대시보드 UI 코드 배치...]
    st.success("대시보드가 정상적으로 로드되었습니다. 구글 시트 데이터를 기반으로 상시 학습됩니다.")
    
    # (기존 코드의 UI 구성 요소들을 여기에 붙여넣으시면 됩니다.)
