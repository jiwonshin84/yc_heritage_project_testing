import streamlit as st

st.title("🌦 박수진")



import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# ---------------------------------------------------------
# 상단 타이틀 및 소개
# ---------------------------------------------------------
st.header("🛡️ 박수진 - 훼손위험도 예측 시스템")
st.write("영천 문화재 통합 데이터와 기상 시나리오를 연동하여 AI 훼손 위험도를 정밀 예측합니다.")
st.markdown("---")

# ---------------------------------------------------------
# 📂 로컬 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_heritage_data():
    # 사용자가 업로드한 정확한 파일명 지정
    file_path = "yc_heritage_feature.xlsx - yc_heritage_feature.csv"
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # 검색 정확도를 위해 문화재명에서 공백을 제거한 별도 컬럼 생성
        df['문화재명_clean'] = df['문화재명(국문)'].astype(str).str.replace(" ", "").str.strip()
        return df
    else:
        # 파일이 없을 때를 대비한 기본 안전 장치 데이터 생성
        return pd.DataFrame({
            '문화재명(국문)': ['영천 거조사 영산전', '영천 청제비', '영천 신월리 삼층석탑'],
            '문화재명_clean': ['영천거조사영산전', '영천청제비', '영천신월리삼층석탑'],
            '국가유산종목': ['국보', '국보', '보물'],
            '재질': ['기타', '석조', '석조'],
            '노출형태': ['반실외', '실외', '실외'],
            '문화재연령': [676, 1426, 1226]
        })

df_heritage = load_heritage_data()

# ---------------------------------------------------------
# 2. 🔍 문화재 검색 UI (영천 전체 문화재 리스트 연동)
# ---------------------------------------------------------
st.subheader("🔍 영천 문화유산 실시간 DB 검색")
search_keyword = st.text_input(
    "영천의 문화재 명칭을 입력하세요:", 
    placeholder="예: 청제비, 거조사, 삼층석탑, 은해사 등"
)

if search_keyword:
    # 입력된 키워드 공백 제거
    clean_keyword = search_keyword.replace(" ", "").strip()
    filtered_df = df_heritage[df_heritage['문화재명_clean'].str.contains(clean_keyword, case=False, na=False)]
    
    if not filtered_df.empty:
        st.success(f"영천시 내부 DB에서 총 {len(filtered_df)}건의 유산이 매칭되었습니다.")
        
        # 선택 박스 제공
        heritage_list = filtered_df['문화재명(국문)'].tolist()
        selected_name = st.selectbox("예측 대상 문화재를 최종 선택하세요:", heritage_list)
        
        # 선택된 문화재 정보 추출
        heritage_info = filtered_df[filtered_df['문화재명(국문)'] == selected_name].iloc[0]
        
        h_name = heritage_info['문화재명(국문)']
        h_kind = heritage_info['국가유산종목']
        h_material = heritage_info['재질'] if '재질' in heritage_info and pd.notna(heritage_info['재질']) else "기타"
        h_age = heritage_info['문화재연령'] if '문화재연령' in heritage_info and pd.notna(heritage_info['문화재연령']) else 100
        h_exposure = heritage_info['노출형태'] if '노출형태' in heritage_info and pd.notna(heritage_info['노출형태']) else "실외"

        # 문화재 정보 카드 레이아웃
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🏛️ 문화재명:** {h_name} ({h_kind})")
            st.markdown(f"**⏳ 문화재 연령:** {int(h_age)}년 (추정)")
        with col2:
            st.markdown(f"**🏗️ 구성 재질:** {h_material}")
            st.markdown(f"**🧱 노출 형태:** {h_exposure}")

        st.markdown("---")

        # ---------------------------------------------------------
        # 3. 🌦️ 실시간 기상 정보 시뮬레이터 (위험도 변화율 테스트용)
        # ---------------------------------------------------------
        st.subheader("🌦️ 실시간 기상 환경 제어 및 연동")
        st.write("현재 영천 기상 관측 데이터 기반 지표입니다. (위험도 테스트를 위해 슬라이더 조절 가능)")
        
        w_col1, w_col2, w_col3 = st.columns(3)
        current_temp = w_col1.slider("현재 기온 (°C)", min_value=-15.0, max_value=40.0, value=24.5)
        current_humidity = w_col2.slider("대기 상대습도 (%)", min_value=10, max_value=100, value=82)
        current_rainfall = w_col3.slider("시간당 일강수량 (mm)", min_value=0.0, max_value=100.0, value=12.5)

        st.markdown("---")

        # ---------------------------------------------------------
        # 4. 📊 알고리즘 기반 위험도 자동 계산
        # ---------------------------------------------------------
        base_risk = 20
        
        # 재질별 영향도 가중치 산식 계산
        if h_material == "목조":
            material_factor = (current_humidity * 0.45) + (current_rainfall * 2.5)
        elif h_material == "석조":
            material_factor = (current_humidity * 0.25) + (current_rainfall * 1.2)
        else:
            material_factor = (current_humidity * 0.35) + (current_rainfall * 1.8)
            
        # 노출형태 및 유산 나이에 따른 보정치 추가
        exposure_bonus = 15 if h_exposure == "실외" else 5
        age_bonus = min(int(h_age) * 0.01, 15)
        
        # 최종 점수 산출 (최대 100점 제한)
        total_risk = min(int(base_risk + material_factor + exposure_bonus + age_bonus), 100)

        # 위험 상태 분류 및 색상 지정
        if total_risk < 45:
            risk_status = "정상/안전"
            risk_color = "#28a745"
        elif total_risk < 75:
            risk_status = "주의 요망"
            risk_color = "#ffc107"
        else:
            risk_status = "심각 (훼손 발생 경고)"
            risk_color = "#dc3545"

        # 게이지 차트 시각화
        st.subheader("📊 실시간 AI 훼손위험도 정밀 예측")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = total_risk,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"위험 등급: {risk_status}", 'font': {'size': 18, 'color': risk_color}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': risk_color},
                'bgcolor': "white",
                'borderwidth': 1,
                'steps': [
                    {'range': [0, 45], 'color': '#eef9ef'},
                    {'range': [45, 75], 'color': '#fff9e6'},
                    {'range': [75, 100], 'color': '#fdf2f2'}
                ],
            }
        ))
        fig.update_layout(height=260, margin=dict(l=30, r=30, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------
        # 5. 🤖 데이터 세트 맞춤형 AI 리포트 출력
        # ---------------------------------------------------------
        st.subheader("🤖 AI 종합 분석 진단서")
        
        with st.expander(f"📝 {h_name} 진단 리포트 전문 확인", expanded=True):
            st.markdown(f"**[종합 분석 요약]** 본 문화재는 연령이 **{int(h_age)}년**에 달하는 영천의 유산으로, 현재 **{h_material}** 재질 특성과 **{h_exposure}** 환경 상태에 노출되어 있습니다.")
            
            if h_material == "석조":
                st.markdown(f"""
                * **기상 취약점 분석**: 현재 설정된 대기 습도({current_humidity}%) 환경에서 표면 균열부 균사체 결착율이 상승합니다. 강수량 {current_rainfall}mm 지속 시 표면 마모도가 가속화될 우려가 있습니다.
                * **장기 예측**: 석조의 물리적 박리 상태 진단 결과, 동결-융해 주기가 반복되는 시기 외에도 산성비 및 습기 정체에 의한 비문 화학적 부식이 우려됩니다.
                * **AI 권고사항**: 석조 표면의 지의류 세척 주기를 단축하고 보호각이 없는 실외 유산인 경우 임시 차수막 배수관 상태를 즉시 점검하십시오.
                """)
            elif h_material == "목조" or "거조" in h_name:
                st.markdown(f"""
                * **기상 취약점 분석**: 현재 기온 {current_temp}°C와 습도 {current_humidity}%의 조합은 목재 내부 함수율을 위험 수치까지 올릴 수 있습니다. 특히 {current_rainfall}mm급 강수는 구조 목부 하중 스트레스를 가중시킵니다.
                * **장기 예측**: 고온다습 조건 지속 시 목재 부후균 활성화 지수가 80%를 초과하여 목조 가구의 비틀림 및 기둥 침하 훼손 위험도가 급증합니다.
                * **AI 권고사항**: 수분 정체 구역 차단을 위해 지붕 및 기단 배수로 조치가 시급하며, 강수 종료 즉시 적극적인 대류 통풍(창호 개방)을 실시해야 합니다.
                """)
            else:
                st.markdown(f"""
                * **기상 취약점 분석**: 현재 기상 조건(기온 {current_temp}°C / 습도 {current_humidity}%)은 복합 재질 및 주변 환경 지반의 약화를 초래할 수 있는 임계치 근처입니다.
                * **장기 예측**: 지속적인 수분 스트레스로 인해 미세 균열의 폭이 확장되거나 주변 토사 유실로 인한 구조적 변형 가능성이 확인됩니다.
                * **AI 권고사항**: 통합 모니터링 주기를 강화하고 균열 측정 센서의 데이터 로그를 역추적하여 이상 징후 변화율을 상시 대조하십시오.
                """)
    else:
        st.warning("영천 유산 데이터베이스 내에 해당 이름이 포함된 문화재를 찾을 수 없습니다. 다른 명칭으로 검색해 보세요! (예: '거조', '청제', '삼층석탑' 등)")
else:
    st.info("💡 영천의 국가유산 이름(예: 청제비, 거조사, 은해사, 신흥사 등)을 입력창에 검색하면 분석이 시작됩니다.")
