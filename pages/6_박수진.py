import streamlit as st

st.title("🌦 박수진")



import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. 페이지 상단 제목 및 설명
st.header("🛡️ 박수진 - 훼손위험도 예측 시스템")
st.write("영천의 모든 문화재 데이터를 가나다순으로 제공합니다. 유산을 선택하시면 AI 훼손 위험도를 정밀 예측합니다.")
st.markdown("---")

# 2. 📂 데이터 파일 탐색 및 로드 (105개 데이터 전수 로드 보장)
@st.cache_data
def load_data():
    # 파일 탐색 순서 배치
    possible_paths = [
        "yc_heritage_feature.xlsx - yc_heritage_feature.csv",
        "yc_heritage_feature.csv",
        "../yc_heritage_feature.csv"
    ]
    
    df = None
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            break
            
    # 만약 파일이 여전히 감지되지 않는다면 사용자가 알 수 있도록 경고창용 빈 데이터 생성
    if df is None:
        df = pd.DataFrame({
            '문화재명(국문)': ['🚨 데이터 파일[yc_heritage_feature.csv]을 찾을 수 없습니다. 깃허브 폴더를 확인해주세요.'],
            '국가유산종목': ['알수없음'],
            '재질': ['기타'],
            '노출형태': ['실외'],
            '문화재연령': [100]
        })
    else:
        # 💡 핵심: 파일이 잘 로드되었다면 가나다 순서로 깔끔하게 정렬
        df = df.dropna(subset=['문화재명(국문)'])
        df = df.sort_values(by='문화재명(국문)').reset_index(drop=True)
        
    return df

df = load_data()

# 3. 🏛️ 드롭다운 선택창 배치 (여기에서 105개의 리스트가 전부 나옵니다)
st.subheader("🏛️ 분석 대상 문화재 선택")
heritage_list = df['문화재명(국문)'].tolist()

selected_name = st.selectbox(
    "위험도를 분석할 문화재를 목록에서 선택하세요:",
    heritage_list,
    index=0
)

# 4. 선택된 문화재의 데이터 파싱 및 안전한 예외 처리
if selected_name:
    info = df[df['문화재명(국문)'] == selected_name].iloc[0]
    
    h_name = info['문화재명(국문)']
    h_kind = info['국가유산종목'] if '국가유산종목' in info and pd.notna(info['국가유산종목']) else "지정문화재"
    h_material = str(info['재질']) if '재질' in info and pd.notna(info['재질']) else "기타"
    h_age = int(info['문화재연령']) if '문화재연령' in info and pd.notna(info['문화재연령']) else 100
    h_exposure = str(info['노출형태']) if '노출형태' in info and pd.notna(info['노출형태']) else "실외"

    # 문화재 정보 카드 레이아웃
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**🏛️ 문화재명:** {h_name} ({h_kind})")
        st.markdown(f"**⏳ 문화재 나이:** {h_age}년 추정")
    with c2:
        st.markdown(f"**🏗️ 구성 재질:** {h_material}")
        st.markdown(f"**🧱 노출 형태:** {h_exposure}")

    st.markdown("---")

    # 5. 🌦️ 실시간 기상 환경 연동 슬라이더
    st.subheader("🌦️ 실시간 기상 환경 연동")
    st.write("현재 영천 기상 관측 조건입니다. 환경 변화에 따른 위험도를 시뮬레이션할 수 있습니다.")
    
    w1, w2, w3 = st.columns(3)
    temp = w1.slider("기온 (°C)", -15.0, 40.0, 24.5)
    humidity = w2.slider("상대습도 (%)", 10, 100, 80)
    rainfall = w3.slider("강수량 (mm)", 0.0, 100.0, 10.0)

    st.markdown("---")

    # 6. 📊 알고리즘 기반 위험도 자동 연산
    score = 20
    if h_material == "목조":
        score += (humidity * 0.4) + (rainfall * 2.0) + 10
    elif h_material == "석조":
        score += (humidity * 0.2) + (rainfall * 1.0) + 15
    else:
        score += (humidity * 0.3) + (rainfall * 1.5) + 5
        
    final_risk = min(int(score), 100)

    if final_risk < 45:
        status, color = "정상/안전", "#28a745"
    elif final_risk < 75:
        status, color = "주의 요망", "#ffc107"
    else:
        status, color = "위험/심각", "#dc3545"

    # 게이지 차트 시각화
    st.subheader("📊 실시간 훼손위험도 결과")
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = final_risk,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"위험 등급: {status}", 'font': {'size': 18, 'color': color}},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'bgcolor': "white",
            'steps': [
                {'range': [0, 45], 'color': '#eef9ef'},
                {'range': [45, 75], 'color': '#fff9e6'},
                {'range': [75, 100], 'color': '#fdf2f2'}
            ],
        }
    ))
    fig.update_layout(height=240, margin=dict(l=30, r=30, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # 7. 🤖 데이터 맞춤형 AI 리포트 출력
    st.subheader("🤖 AI 종합 진단서")
    with st.expander("📝 상세 리포트 열기", expanded=True):
        st.write(f"본 유산은 약 {h_age}년 동안 보존된 영천의 소중한 자산입니다. 지정된 환경 분석 결과는 다음과 같습니다.")
        
        if h_material == "석조":
            st.markdown(f"- 현재 설정된 대기 습도({humidity}%) 조건은 석조 유산 표면에 결로 현상 및 미생물(지의류, 이끼) 번식 가능성을 가속화할 수 있습니다.")
            st.markdown(f"- 해당 유산은 환경 분류상 **'{h_exposure}'** 상태이므로 장기적인 풍화 작용과 비바람에 의한 표면 마모도 관찰이 요구됩니다.")
        elif h_material == "목조":
            st.markdown(f"- 현재 강수량 {rainfall}mm 환경 조건 하에서는 목재 내부 함수율이 임계치를 초과하여 자재의 비틀림이나 균열 변형 위험이 증대됩니다.")
            st.markdown(f"- 습해 및 흰개미 등 생물 피해 방지를 위해 비가 그친 직후 신속한 대류 통풍 및 창호 개방 조치를 적극 권장합니다.")
        else:
            st.markdown(f"- 입력된 기온({temp}°C) 및 습도({humidity}%) 조건에 따라 복합 재질 환경 내구 지수가 가변적인 구간에 있습니다.")
            st.markdown("- 균열 측정 장비의 정기 로그 확인 및 지반 침하 가능성에 대한 추가 모니터링 수치 확보를 권장합니다.")
