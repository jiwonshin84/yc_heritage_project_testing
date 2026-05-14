import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score

# ==========================================================
# 0. 그래프 한글 설정 (Streamlit 환경용)
# ==========================================================
# 운영체제별 폰트 설정 (Windows/Linux/Colab 공용)
import platform
from matplotlib import font_manager, rc

@st.cache_resource
def set_korean_font():
    try:
        if platform.system() == 'Windows':
            font_name = font_manager.FontProperties(family='Malgun Gothic').get_name()
            rc('font', family=font_name)
        else:
            # 리눅스/Streamlit Cloud 환경 (폰트가 없을 경우 대비)
            plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass

set_korean_font()

# 한글 변수명 매핑 사전
KOR_NAMES = {
    "temp": "기온(℃)",
    "humidity": "습도(%)",
    "pm10": "미세먼지(PM10)",
    "pm25": "초미세먼지(PM2.5)",
    "temp_change": "기온 변화량",
    "humidity_change": "습도 변화량",
    "dew_gap": "결로 위험 지수(이슬점 차이)",
    "humidity_ma3": "3일 평균 습도",
    "pm10_ma3": "3일 평균 미세먼지",
    "temp_std": "기온 변동성(표준편차)",
    "humidity_std": "습도 변동성(표준편차)",
    "pm_load": "미세먼지 누적 노출량"
}

# ==========================================================
# 1. 데이터 로드 및 전처리 (구글 시트 연동)
# ==========================================================
@st.cache_data
def load_and_preprocess_data():
    weather_url = "https://docs.google.com/spreadsheets/d/1l3cH2f6YATxJHxr3QWjIpwvc9QKPmHAJ/export?format=csv&gid=205029320"
    air_url = "https://docs.google.com/spreadsheets/d/1ao2TtZyLMNcpSsFPxdxYWZ5alAgc2aKjn5z7KomD6kA/export?format=csv&gid=1366576330"
    
    # 데이터 읽기
    weather = pd.read_csv(weather_url)
    air = pd.read_csv(air_url)
    
    # 날짜 병합
    weather["date"] = pd.to_datetime(weather["date"])
    air["date"] = pd.to_datetime(air["date"])
    df = pd.merge(weather, air, on="date", how="inner").ffill()
    
    # 파생 변수 생성
    df["temp_change"] = df["temp"].diff().fillna(0)
    df["humidity_change"] = df["humidity"].diff().fillna(0)
    df["dew_point"] = df["temp"] - ((100 - df["humidity"]) / 5)
    df["dew_gap"] = df["temp"] - df["dew_point"]
    df["humidity_ma3"] = df["humidity"].rolling(3).mean().fillna(df["humidity"])
    df["pm10_ma3"] = df["pm10"].rolling(3).mean().fillna(df["pm10"])
    df["temp_std"] = df["temp"].rolling(3).std().fillna(0)
    df["humidity_std"] = df["humidity"].rolling(3).std().fillna(0)
    df["pm_load"] = (df["pm10"] + df["pm25"]).rolling(3).sum().fillna(0)
    
    # 위험도 라벨링 (절대 기준값)
    def classify(r):
        h_risk = 2 if (r["humidity"] >= 75 or r["humidity"] < 35) else (1 if (r["humidity"] >= 65 or r["humidity"] < 45) else 0)
        t_risk = 2 if (r["temp"] > 30 or r["temp"] < 5) else (1 if (r["temp"] > 25 or r["temp"] < 15) else 0)
        d_risk = 2 if r["dew_gap"] < 2 else (1 if r["dew_gap"] < 5 else 0)
        p_risk = 2 if r["pm10"] >= 80 else (1 if r["pm10"] >= 30 else 0)
        score = (h_risk * 0.3) + (t_risk * 0.2) + (d_risk * 0.2) + (p_risk * 0.15) + (abs(r["temp_change"])*0.01) # 단순화된 가중치
        return 2 if score >= 1.2 else (1 if score >= 0.5 else 0)

    df["risk"] = df.apply(classify, axis=1)
    return df

# ==========================================================
# 2. 메인 화면 구성
# ==========================================================
st.title("🧪 문화재 훼손 위험 예측 모델 비교 분석")
st.markdown("전통 문화재 보존을 위한 최적의 AI 알고리즘을 탐색하고, 위험 결정의 핵심 지표를 분석합니다.")

df = load_and_preprocess_data()
features = list(KOR_NAMES.keys())
X = df[features]
y = df["risk"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 모델 정의
models = {
    "의사결정나무(DT)": DecisionTreeClassifier(max_depth=6, class_weight="balanced"),
    "랜덤포레스트(RF)": RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42),
    "그라디언트 부스팅(GBM)": GradientBoostingClassifier(n_estimators=200, random_state=42)
}

# ----------------------------------------------------------
# 모델 학습 및 정확도 비교
# ----------------------------------------------------------
st.header("1. 모델별 예측 정확도 비교")

acc_scores = {}
trained_models = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    acc_scores[name] = acc
    trained_models[name] = model

# 수치가 표시된 막대 그래프 생성
fig1, ax1 = plt.subplots(figsize=(10, 5))
sns.set_style("whitegrid")
bars = ax1.bar(acc_scores.keys(), acc_scores.values(), color=['#3498db', '#e74c3c', '#2ecc71'])

# 막대 위에 수치 표시
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{height:.2%}', ha='center', va='bottom', fontweight='bold', fontsize=12)

ax1.set_title("AI 모델별 성능 비교 (정확도)", fontsize=15, pad=20)
ax1.set_ylabel("정확도 (Accuracy)", fontsize=12)
ax1.set_ylim(0, 1.1)
st.pyplot(fig1)

# ----------------------------------------------------------
# 변수 중요도 분석 (한글화 적용)
# ----------------------------------------------------------
st.divider()
st.header("2. 위험 결정에 기여한 핵심 지표 분석")

selected_name = st.selectbox("지표 중요도를 확인할 모델을 선택하세요", list(models.keys()))
best_model = trained_models[selected_name]

if hasattr(best_model, 'feature_importances_'):
    # 중요도 추출 및 한글화
    importances = best_model.feature_importances_
    imp_df = pd.DataFrame({
        '지표': [KOR_NAMES[f] for f in features],
        '중요도': importances
    }).sort_values(by='중요도', ascending=True)

    fig2, ax2 = plt.subplots(figsize=(10, 7))
    ax2.barh(imp_df['지표'], imp_df['중요도'], color='#f1c40f')
    ax2.set_title(f"[{selected_name}] 가 판단한 위험 결정 요인", fontsize=15, pad=20)
    ax2.set_xlabel("상대적 중요도", fontsize=12)
    
    # 수치 표시
    for i, v in enumerate(imp_df['중요도']):
        ax2.text(v + 0.005, i, f'{v:.3f}', va='center', fontsize=10)
        
    st.pyplot(fig2)
    
    st.info(f"💡 **분석 결과:** {selected_name} 모델에 따르면 현재 문화재 훼손 위험에 가장 큰 영향을 주는 요소는 **'{imp_df.iloc[-1]['지표']}'**(이)가 높게 나타납니다.")
else:
    st.warning("선택한 모델은 변수 중요도 시각화를 지원하지 않습니다.")

# ----------------------------------------------------------
# 하단 상세 데이터
# ----------------------------------------------------------
with st.expander("📄 학습에 사용된 최신 전처리 데이터 확인"):
    st.dataframe(df.tail(10))

st.caption("제6회 학생 SW·AI 인재양성 프로젝트 | 선화여고 - 영천 헤리티지 AI 탐구단")
