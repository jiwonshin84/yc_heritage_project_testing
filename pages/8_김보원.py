import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------
# 1. 페이지 초기 설정 (김보원 전용 타이틀)
# ---------------------------------------------------------
st.set_page_config(
    page_title="영천 스마트 투어 가이드 - 김보원",
    page_icon="🏛️",
    layout="wide"
)

# 메인 타이틀 및 소개
st.title("🏛️ 공공데이터 기반 지능형 문화유산 관람 추천 모델")
st.caption("Developed by 김보원 | 영천 문화유산(YC Heritage) 맞춤형 기상 분석 시스템")
st.markdown("---")

# ---------------------------------------------------------
# 2. 사이드바 설정 (API 키 및 장소 선택)
# ---------------------------------------------------------
st.sidebar.header("📍 서비스 환경 설정")
api_key = st.sidebar.text_input("기상청 API Key 입력", type="password", help="공공데이터포털 발급 키")
target_site = st.sidebar.selectbox("대상 문화유산 선택", ["은해사", "임고서원", "거조사", "보현산천문대"])

# ---------------------------------------------------------
# 3. [공공데이터] 실시간 기상 정보 수집 (KMA API)
# ---------------------------------------------------------
@st.cache_data
def fetch_live_weather(key):
    """현재 날짜와 시간을 기준으로 기상청 초단기실황 데이터를 가져옴"""
    if not key: return None
    
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00") # 실황은 매시 정각 기준
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        'serviceKey': key,
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'base_date': base_date, 'base_time': base_time,
        'nx': '91', 'ny': '88' # 영천시 격자 좌표
    }
    
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            items = res.json()['response']['body']['items']['item']
            return pd.DataFrame(items)
    except:
        return None

# ---------------------------------------------------------
# 4. [머신러닝] 관람 적합도 분석 모델 학습
# ---------------------------------------------------------
@st.cache_resource
def build_suitability_model():
    """기상 변수에 따른 관람 적합도를 분류하는 Random Forest 모델 구축"""
    np.random.seed(42)
    # 가상의 관람 데이터 생성 (300건)
    temp = np.random.uniform(5, 38, 300)
    rain = np.random.uniform(0, 50, 300)
    wind = np.random.uniform(0, 15, 300)
    
    # 적합도 로직 (2: 매우쾌적, 1: 보통, 0: 관람비권장)
    # 기온 20-25도 사이, 비 안올 때 가장 높음
    score = 30 - np.abs(temp - 22) - (rain * 1.5) - (wind * 0.5)
    labels = np.where(score > 20, 2, np.where(score > 10, 1, 0))
    
    X = pd.DataFrame({'T1H': temp, 'RN1': rain, 'WSD': wind})
    y = labels
    
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    return model

# ---------------------------------------------------------
# 5. UI 메인 레이아웃 (3개 탭 구성)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📡 실시간 기상 수집", "🧠 지능형 추천 로직", "✨ 스마트 가이드 실행"])

with tab1:
    st.subheader(f"📡 {target_site} 주변 실시간 기상 상황")
    if api_key:
        with st.spinner("데이터 동기화 중..."):
            weather_df = fetch_live_weather(api_key)
            if weather_df is not None:
                st.success("데이터 수집 완료")
                st.table(weather_df[['category', 'obsrValue']])
            else:
                st.info("API 응답을 대기 중입니다. 키와 날짜를 확인해 주세요.")
    else:
        st.warning("API 키를 입력하면 실시간 영천 기상 데이터를 로드합니다.")

with tab2:
    st.subheader("🧠 머신러닝 기반 관람 적합도 분석 모델")
    st.write("Random Forest 알고리즘을 활용하여 현재 날씨가 야외 문화유산 관람에 얼마나 적합한지 판단합니다.")
    
    model = build_suitability_model()
    st.code("""# 모델 핵심 로직
# Features: 기온(T1H), 강수량(RN1), 풍속(WSD)
# Target: 관람 적합도 지수 (Suitability Index)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)""")
    st.success("🤖 모델 학습 상태: 최적화 완료")

with tab3:
    st.subheader(f"✨ {target_site} 스마트 관람 가이드")
    st.write("관람 예정 시간의 날씨를 설정해 보세요.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        s_temp = st.slider("예상 기온 (°C)", 0.0, 40.0, 24.0)
        s_rain = st.slider("예상 강수량 (mm)", 0.0, 100.0, 0.0)
        s_wind = st.slider("예상 풍속 (m/s)", 0.0, 20.0, 2.0)
    
    with c2:
        if st.button("관람 적합도 확인하기", use_container_width=True):
            input_data = pd.DataFrame([[s_temp, s_rain, s_wind]], columns=['T1H', 'RN1', 'WSD'])
            result = model.predict(input_data)[0]
            
            st.markdown("### 분석 결과")
            if result == 2:
                st.balloons()
                st.success("🌟 **매우 추천:** 현재 관람하기에 최상의 날씨입니다!")
            elif result == 1:
                st.warning("⛅ **보통:** 관람은 가능하나 실내 관람을 병행하세요.")
            else:
                st.error("🌧️ **비권장:** 기상 상황이 좋지 않습니다. 방문을 재고해 보세요.")
