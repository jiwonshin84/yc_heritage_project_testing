import streamlit as st

st.title("🌦 박수진")



import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------
# 상단 타이틀 및 소개
# ---------------------------------------------------------
st.header("🛡️ 박수진 - 훼손위험도 예측 시스템")
st.write("국가유산 검색 정보와 실시간 기상 데이터를 기반으로 AI가 훼손 위험도를 자동 예측합니다.")
st.markdown("---")

# ---------------------------------------------------------
# 1. 🔍 문화재 검색 기능
# ---------------------------------------------------------
st.subheader("🔍 문화재 검색 및 정보 조회")
search_keyword = st.text_input(
    "문화재 명칭을 입력하세요:", 
    placeholder="예: 청제비 또는 은해사"
)

# 사용자가 검색어를 입력했을 때만 아래 기능들이 활성화됩니다.
if search_keyword:
    st.info(f"'{search_keyword}'(으)로 데이터를 조회 중입니다...")
    
    # 🌐 [데이터 분기] 실제 API 연동 전까지 검색어에 따라 모크(Mock) 데이터 매핑
    if "청제" in search_keyword or "청제비" in search_keyword:
        name = "영천 청제비 (永川 菁堤碑)"
        status = "보물"
        location = "경북 영천시 도동 221"
        structure = "석조 (비석)"
        manager = "영천시"
        
        # 청제비(석조) 기준 날씨 및 가상 위험도 세팅
        current_temp = 28.0
        current_humidity = 92.0  # 고습도 상황 가정
        current_rainfall = 5.0
        
        # 위험도 계산 산식 (석조물: 습도와 강수량 영향 반영)
        base_risk = 20
        weather_factor = (current_humidity * 0.3) + (current_rainfall * 1.5)
        total_risk = min(int(base_risk + weather_factor), 100)
        
        heritage_type = "석조"
        
    else:
        # 기본값 또는 '은해사' 입력 시 목조건물 데이터 세팅
        name = "영천 은해사 거조암 영산전"
        status = "국보 제14호"
        location = "경북 영천시 청통면 청통로 951-81"
        structure = "목조 건축물"
        manager = "은해사"
        
        # 은해사(목조) 기준 날씨 및 가상 위험도 세팅
        current_temp = 32.5
        current_humidity = 85.0  # 고온다습 폭우 상황 가정
        current_rainfall = 25.0
        
        # 위험도 계산 산식 (목조건물: 폭우 시 위험도 급증)
        base_risk = 35
        weather_factor = (current_humidity * 0.4) + (current_rainfall * 2.0)
        total_risk = min(int(base_risk + weather_factor), 100)
        
        heritage_type = "목조"

    # 문화재 정보 출력 UI
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**🏛️ 문화재명:** {name} ({status})")
        st.markdown(f"**📍 소재지:** {location}")
    with col2:
        st.markdown(f"**🏗️ 구조:** {structure}")
        st.markdown(f"**🏢 관리단체:** {manager}")

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. 🌦️ 날씨 데이터 연동 영역
    # ---------------------------------------------------------
    st.subheader("🌦️ 실시간 기상 정보 현황")
    w_col1, w_col2, w_col3 = st.columns(3)
    
    w_col1.metric(label="현재 기온", value=f"{current_temp} °C")
    w_col2.metric(label="대기 습도", value=f"{current_humidity} %")
    w_col3.metric(label="시간당 강수량", value=f"{current_rainfall} mm")

    st.markdown("---")

    # ---------------------------------------------------------
    # 3. 📊 위험도 자동 계산 및 🎯 게이지 차트 표시
    # ---------------------------------------------------------
    st.subheader("📊 실시간 훼손위험도 예측 결과")
    
    # 위험도 점수에 따른 상태 및 색상 판정
    if total_risk < 40:
        risk_status = "안전"
        risk_color = "#28a745"  # 초록색
    elif total_risk < 70:
        risk_status = "주의"
        risk_color = "#ffc107"  # 노란색
    else:
        risk_status = "경고 (훼손 위험 높음)"
        risk_color = "#dc3545"  # 빨간색

    # Plotly를 이용한 게이지 차트 그리기
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = total_risk,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"현재 위험 상태: {risk_status}", 'font': {'size': 18, 'color': risk_color}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': risk_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#dddddd",
            'steps': [
                {'range': [0, 40], 'color': '#eef9ef'},  # 안전 구간 배경
                {'range': [40, 70], 'color': '#fff9e6'},  # 주의 구간 배경
                {'range': [70, 100], 'color': '#fdf2f2'}  # 경고 구간 배경
            ],
        }
    ))
    
    fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 5. 🤖 AI 분석 리포트 생성
    # ---------------------------------------------------------
    st.subheader("🤖 AI 훼손위험 분석 리포트")
    
    with st.expander("📝 리포트 상세 진단 보기", expanded=True):
        if heritage_type == "석조":
            st.markdown(f"""
            ### [AI종합진단] 석조문화재 표면 박리 및 생물 미생물 고착 위험
            1. **기상 영향성 분석**: 현재 대기 습도가 **{current_humidity}%**로 매우 높아 비석 표면에 결로 현상이 지속될 수 있습니다.
            2. **취약점 경고**: 석조문화재(비석)는 고습 환경이 장기화될 경우 표면에 이끼, 지의류 등 생물학적 훼손 요인이 증식하여 비문 마모를 촉진할 수 있습니다.
            3. **대응 가이드라인**: 
                * 비석 주위의 배수 상태를 점검하여 수분 정체를 방지하십시오.
                * 강수 종료 후 표면 건조 상태와 이끼 발생 여부를 상시 모니터링하세요.
            """)
        else:
            st.markdown(f"""
            ### [AI종합진단] 목조문화재 습해 및 구조 변형 가능성 진단
            1. **기상 영향성 분석**: 현재 **{current_rainfall}mm**의 강수와 **{current_humidity}%**의 높은 습도로 인해 목재 내부의 함수율이 급격히 상승하고 있습니다.
            2. **취약점 경고**: 목조건축물은 수분에 지속적으로 노출될 경우 기둥 하부 부후(썩음) 현상이나 흰개미 활동 활성화 조건이 충족되어 구조 안정성에 치명적일 수 있습니다.
            3. **대응 가이드라인**: 
                * 연경 및 지붕 누수 여부를 실시간으로 긴급 점검하십시오.
                * 비가 그친 직후 창호를 개방하여 내부 통풍 및 자연 건조 조치를 취할 것을 권장합니다.
            """)
else:
    # 아무것도 입력하지 않았을 때 나오는 기본 안내 멘트
    st.info("💡 위의 입력창에 문화재 이름을 입력하시면 실시간 예측이 시작됩니다.")
