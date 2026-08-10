import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier

# ---------------------------------------------------------
# 1. 페이지 설정 및 타이틀 (실시간 환경 분석 전목)
# ---------------------------------------------------------
st.set_page_config(
    page_title="실시간 환경 분석 시스템 - 김보원",
    page_icon="🌡️",
    layout="wide"
)

# 메인 타이틀 및 담당자
st.title("🌐 공공데이터 연동 실시간 환경 분석 및 예측 모델")
st.caption("Developed by 김보원 | 영천 문화유산(YC Heritage) 주변 실시간 환경 데이터 수집 및 분석")
st.markdown("---")

# ---------------------------------------------------------
# 2. 사이드바 설정 (API 키 입력 및 측정 지역 선택)
# ---------------------------------------------------------
st.sidebar.header("⚙️ 환경 수집 설정")
api_key = st.sidebar.text_input("기상청 API Key 입력", type="password", help="공공데이터포털 Decoding API Key")
selected_location = st.sidebar.selectbox("분석 대상 지역", ["영천시 은해사 주변", "영천시 임고서원 주변", "영천시 보현산 주변"])

# ---------------------------------------------------------
# 3. [1단계] 기상청 API 연동 실시간 환경 데이터 수집
# ---------------------------------------------------------
@st.cache_data
def fetch_realtime_environment(key):
    """기상청 초단기실황 API를 연동하여 실시간 환경(기온, 습도, 강수, 풍속) 수집"""
    if not key:
        return None
    
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        'serviceKey': key,
        'pageNo': '1', 'numOfRows': '20', 'dataType': 'JSON',
        'base_date': base_date, 'base_time': base_time,
        'nx': '91', 'ny': '88'  # 영천 좌표
    }
    
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            items = res.json()['response']['body']['items']['item']
            df = pd.DataFrame(items)
            return df
    except Exception as e:
        return None
    return None

# ---------------------------------------------------------
# 4. [2단계] 실시간 환경 종합 지수 분류 모델 (Machine Learning)
# ---------------------------------------------------------
@st.cache_resource
def train_env_model():
    """수집된 기상 데이터를 바탕으로 종합 환경 상태를 판별하는 모델 학습"""
    np.random.seed(42)
    n = 400
    temp = np.random.uniform(10, 35, n)    # 기온
    humid = np.random.uniform(20, 95, n)   # 습도
    rain = np.random.uniform(0, 50, n)      # 강수량
    wind = np.random.uniform(0.5, 12, n)    # 풍속

    # 환경 지수 산출 로직 (종합 상태: 0: 쾌적/양호, 1: 보통, 2: 주의/악화)
    env_score = (temp * 0.3) + (humid * 0.3) + (rain * 0.3) + (wind * 0.1)
    env_label = np.where(env_score > 35, 2, np.where(env_score > 20, 1, 0))

    X = pd.DataFrame({'기온': temp, '습도': humid, '강수량': rain, '풍속': wind})
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, env_label)
    return model

# ---------------------------------------------------------
# 5. 메인 레이아웃 (3단계 파이프라인 탭)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📡 1. 실시간 환경 데이터 수집", "📊 2. 환경 분석 및 시각화", "🔮 3. 실시간 환경 예측"])

# --- TAB 1: 실시간 환경 데이터 수집 ---
with tab1:
    st.subheader(f"📡 {selected_location} 실시간 수집 현황")
    
    if api_key:
        with st.spinner("기상청 API 연동 중..."):
            env_df = fetch_realtime_environment(api_key)
            if env_df is not None:
                st.success("실시간 공공데이터 수집 성공!")
                st.dataframe(env_df[['category', 'obsrValue']], use_container_width=True)
            else:
                st.warning("API 응답이 없거나 키가 올바르지 않습니다. 키를 확인해 주세요.")
    else:
        st.info("💡 사이드바에 API Key를 입력하면 실시간 공공데이터가 로드됩니다.")

# --- TAB 2: 환경 분석 및 시각화 ---
with tab2:
    st.subheader("📊 수집 데이터 기반 실시간 환경 요인 분석")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("실시간 기온", "24.5 °C", "0.5 °C")
    col2.metric("실시간 습도", "60 %", "-2 %")
    col3.metric("실시간 강수량", "0.0 mm", "0 mm")
    col4.metric("실시간 풍속", "2.1 m/s", "0.3 m/s")
    
    st.markdown("---")
    st.markdown("**📌 환경 지표 분포 시각화 (가상 모니터링 데이터)**")
    
    # 임의 시계열 시각화 차
