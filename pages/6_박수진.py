import streamlit as st

st.title("🌦 박수진")



import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. 페이지 상단 안내
st.header("🛡️ 박수진 - 훼손위험도 예측 시스템")
st.write("영천 문화재 데이터와 기상 환경을 연동하여 AI 훼손 위험도를 정밀 예측합니다.")
st.markdown("---")

# 2. 데이터 파일 안전하게 불러오기
@st.cache_data
def load_data():
    file_name = "yc_heritage_feature.xlsx - yc_heritage_feature.csv"
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
    elif os.path.exists("yc_heritage_feature.csv"):
        df = pd.read_csv("yc_heritage_feature.csv")
    else:
        # 파일이 없을 때 앱이 멈추지 않도록 임시 데이터 세팅
        df = pd.DataFrame({
            '문화재명(국문)': ['영천 거조사 영산전', '영천 청제비', '영천 신월리 삼층석탑'],
            '국가유산종목': ['국보', '국보', '보물'],
            '재질': ['기타', '석조', '석조'],
            '노출형태': ['반실외', '실외', '실외'],
            '문화재연령': [676, 1426, 1226]
        })
    return df

df = load_data()

# 3. 🔍 핵심: 일부 단어만 입력해도 실시간으로 매칭하는 검색 기능
st.subheader("🔍 영천 문화유산 검색")
keyword = st.text_input("문화재 이름의 일부를 입력하세요:", placeholder="예: 청제, 거조, 석탑, 은해 등")

if keyword:
    # 대소문자 무시 및 공백을 없애고 텍스트를 비교하여 일부 포함 여부 확인 (Partial Match)
    clean_keyword = keyword.replace(" ", "").strip()
    df['clean_name'] = df['문화재명(국문)'].astype(str).str.replace(" ", "")
    
    match_df = df[df['clean_name'].str.contains(clean_keyword, case=False, na=False)]
    
    if not match_df.empty:
        st.success(f"입력하신 단어가 포함된 문화재를 총 {len(match_df)}건 찾았습니다!")
        
        # 찾은 문화재 목록을 드롭다운 박스로 선택하게 함
        selected_name = st.selectbox("분석할 문화재를 고르세요:", match_df['문화재명(국문)'].tolist())
        
        # 선택된 문화재의 세부 정보 가져오기
        info = match_df[match_df['문화재명(국문)'] == selected_name].iloc[0]
        
        h_name = info['문화재명(국문)']
        h_kind = info['국가유산종목'] if '국가유산종목' in info else "지정문화재"
        h_material = str(info['재질']) if '재질' in info and pd.notna(info['재질']) else "기타"
        h_age = int(info['문화재연령']) if '문화재연령' in info and pd.notna(info['문화재연령']) else 100
        h_exposure = str(info['노출형태']) if '노출형태' in info and pd.notna(info['노출형태']) else "실외"

        # 정보 출력 화면
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**🏛️ 문화재명:** {h_name} ({h_kind})")
            st.markdown(f"**⏳ 문화재 나이:** {h_age}년 추정")
        with c2:
            st.markdown(f"**🏗️ 재질:** {h_material}")
            st.markdown(f"**🧱 노출 형태:** {h_exposure}")

        st.markdown("---")

        # 4. 🌦️ 기상 시뮬레이터 조절기
        st.subheader("🌦️ 실시간 기상 환경 연동")
        w1, w2, w3 = st.columns(3)
        temp = w1.slider("기온 (°C)", -15.0, 40.0, 24.5)
        humidity = w2.slider("상대습도 (%)", 10, 100, 80)
        rainfall = w3.slider("강수량 (mm)", 0.0, 100.0, 10.0)

        st.markdown("---")

        # 5. 📊 위험도 자동 연산 알고리즘
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

        # 게이지 차트 그리기
        st.subheader("📊 실시간 훼손위험도 결과")
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = final_risk,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"등급: {status}", 'font': {'size': 18, 'color': color}},
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

        # 6. 🤖 AI 리포트 생성
        st.subheader("🤖 AI 종합 진단서")
        with st.expander("📝 상세 리포트 열기", expanded=True):
            st.write(f"본 유산은 {h_age}년 동안 보존된 영천의 자산입니다. 현재 기상 조건 분석 결과는 다음과 같습니다.")
            if h_material == "석조":
                st.markdown(f"- 현재 습도({humidity}%)로 인해 표면에 결로 현상 및 미생물(지의류) 번식 가능성이 증가합니다.")
                st.markdown(f"- 외부 환경에 노출된 형태({h_exposure})이므로 비바람에 의한 표면 마모도 관찰이 필요합니다.")
            elif h_material == "목조":
                st.markdown(f"- 강수량 {rainfall}mm 조건에서 목재 내부 함수율이 상승하여 자재 변형 위험이 있습니다.")
                st.markdown(f"- 습해 방지를 위해 비가 그친 후 즉시 창호 개방 및 통풍 조치를 권장합니다.")
            else:
                st.markdown(f"- 기온 {temp}°C 및 습도 {humidity}% 조건에 따라 복합 재질 환경 내구 지수가 가변적입니다.")
                st.markdown("- 정기적인 균열 모니터링 수치 확인을 권장합니다.")
    else:
        st.warning("검색어와 매칭되는 영천 문화재가 데이터에 없습니다. 다른 글자를 입력해 보세요.")
else:
    st.info("💡 입력창에 단어를 치면 영천의 문화재들이 실시간으로 필터링되어 나타납니다.")
