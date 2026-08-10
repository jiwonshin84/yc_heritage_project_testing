import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 제목 (김보원 영역)
# ---------------------------------------------------------
st.set_page_config(
    page_title="위험도 예측 시스템 - 김보원",
    page_icon="🌤️",
    layout="wide"
)

st.title("🌤️ 기상청 공공데이터 기반 위험도 예측 시스템")
st.caption("담당: 김보원")
st.markdown("---")

# ---------------------------------------------------------
# 2. 사이드바 - 설정 및 API 키 입력
# ---------------------------------------------------------
st.sidebar.header("⚙️ 프로젝트 설정")
api_key = st.sidebar.text_input("기상청 API Key 입력", type="password", help="공공데이터포털에서 발급받은 Decoding API Key를 입력하세요.")

# ---------------------------------------------------------
# 3. 공공데이터 수집 함수 (기상청 API)
# ---------------------------------------------------------
@st.cache_data
def fetch_weather_data(service_key):
    """
    기상청 API로부터 데이터를 수집하는 함수
    """
    if not service_key:
        return None

    # 기상청 단기예보/초단기실황 API URL
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        'serviceKey': service_key,
        'pageNo': '1',
        'numOfRows': '1000',
        'dataType': 'JSON',
        'base_date': '20260811', # 날짜 설정
        'base_time': '0600',
        'nx': '55',
        'ny': '127'
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            items = res_json['response']['body']['items']['item']
            df = pd.DataFrame(items)
            return df
    except Exception as e:
        st.error(f"API 데이터 수집 중 오류 발생: {e}")
        return None

# ---------------------------------------------------------
# 4. 데이터셋 생성 및 모의 데이터 로드
# ---------------------------------------------------------
@st.cache_data
def load_risk_dataset():
    """
    위험도 예측 모델 학습을 위한 데이터 구축 (기온, 습도, 강수량, 풍속 -> 위험도 레벨)
    """
    np.random.seed(42)
    n_samples = 300
    
    temperature = np.random.uniform(15, 38, n_samples)  # 기온
    humidity = np.random.uniform(30, 95, n_samples)     # 습도
    rainfall = np.random.uniform(0, 100, n_samples)     # 강수량
    wind_speed = np.random.uniform(0.5, 15, n_samples)  # 풍속

    # 위험도 산출 기준 (0: 안전, 1: 주의, 2: 위험)
    risk_score = (temperature * 0.3) + (humidity * 0.2) + (rainfall * 0.4) + (wind_speed * 0.1)
    risk_level = np.where(risk_score > 60, 2, np.where(risk_score > 40, 1, 0))

    df = pd.DataFrame({
        '기온(°C)': np.round(temperature, 1),
        '습도(%)': np.round(humidity, 1),
        '강수량(mm)': np.round(rainfall, 1),
        '풍속(m/s)': np.round(wind_speed, 1),
        '위험도_단계': risk_level
    })
    return df

# ---------------------------------------------------------
# 5. 메인 화면 탭 구성 (수집 -> 구축/학습 -> 예측)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📡 1. 공공데이터 수집", "📊 2. 데이터 구축 및 모델 학습", "🚨 3. 실시간 위험도 예측"])

# --- TAB 1: 공공데이터 수집 ---
with tab1:
    st.subheader("공공데이터 수집 (기상청 API)")
    
    if api_key:
        with st.spinner("기상청 API 데이터 불러오는 중..."):
            api_data = fetch_weather_data(api_key)
            if api_data is not None:
                st.success("데이터 수집 성공!")
                st.dataframe(api_data, use_container_width=True)
            else:
                st.warning("API 응답이 없거나 키가 올바르지 않아 기본 설정을 확인해주세요.")
    else:
        st.info("💡 왼쪽 사이드바에 기상청 API 키를 입력하면 실제 데이터를 가져옵니다.")

# --- TAB 2: 데이터 구축 및 모델 학습 ---
with tab2:
    st.subheader("위험도 예측 데이터 구축 및 머신러닝 모델 학습")
    
    df_risk = load_risk_dataset()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**📌 구축된 학습 데이터셋 (상위 10개)**")
        st.dataframe(df_risk.head(10), use_container_width=True)
    
    with col2:
        st.markdown("**🤖 모델 학습 실행 (Random Forest)**")
        
        X = df_risk[['기온(°C)', '습도(%)', '강수량(mm)', '풍속(m/s)']]
        y = df_risk['위험도_단계']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        
        st.metric(label="모델 정확도(Accuracy)", value=f"{acc * 100:.1f}%")
        st.success("모델 학습 완료!")

# --- TAB 3: 실시간 위험도 예측 ---
with tab3:
    st.subheader("사용자 입력 기반 위험도 예측해보기")
    
    st.write("기상 조건 변수를 설정하고 현재 환경의 위험도를 예측해 보세요.")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        input_temp = st.slider("기온 (°C)", min_value=-10.0, max_value=40.0, value=28.0, step=0.5)
        input_hum = st.slider("습도 (%)", min_value=0.0, max_value=100.0, value=65.0, step=1.0)
    with col_input2:
        input_rain = st.slider("강수량 (mm)", min_value=0.0, max_value=150.0, value=20.0, step=1.0)
        input_wind = st.slider("풍속 (m/s)", min_value=0.0, max_value=30.0, value=3.5, step=0.5)
        
    if st.button("위험도 예측 실행 🚀", use_container_width=True):
        input_data = np.array([[input_temp, input_hum, input_rain, input_wind]])
        prediction = model.predict(input_data)[0]
        
        st.markdown("---")
        st.markdown("### 📋 예측 결과")
        
        if prediction == 0:
            st.success("🟢 **[안전]** 현재 기상 조건에서의 위험도가 낮습니다.")
        elif prediction == 1:
            st.warning("🟡 **[주의]** 야외 활동 시 기상 변화에 주의하세요.")
        else:
            st.error("🔴 **[위험]** 높은 위험도가 감지되었습니다. 안전에 유의하세요!")
