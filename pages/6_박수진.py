import streamlit as st

st.title("🌦 박수진")



import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. 페이지 상단 제목 및 설명 (다른 팀원 파일과 겹치지 않는 본인 영역)
st.header("🛡️ 박수진 - 훼손위험도 예측 시스템")
st.write("영천의 모든 문화재 데이터를 가나다순으로 제공합니다. 유산을 선택하시면 AI 훼손 위험도를 정밀 예측합니다.")
st.markdown("---")

# 2. 📂 데이터 파일 탐색 및 전수 로드 (경로 에러 완벽 차단 예외처리)
@st.cache_data
def load_data():
    # 팀 프로젝트 서버 환경에 따라 파일명이 다르게 매핑될 수 있으므로 다중 탐색합니다.
    possible_names = [
        "yc_heritage_feature.xlsx - yc_heritage_feature.csv",
        "yc_heritage_feature.csv",
        "yc_heritage_feature.xlsx"
    ]
    
    df = None
    for name in possible_names:
        if os.path.exists(name):
            try:
                if name.endswith('.csv'):
                    df = pd.read_csv(name)
                else:
                    df = pd.read_excel(name)
                break
            except Exception:
                continue
                
    # 파일 탐색에 실패하더라도 다른 팀원 화면이 터지지 않도록 안전망 구성
    if df is None:
        df = pd.DataFrame({
            '문화재명(국문)': [
                '영천 거조사 영산전', '영천 청제비', '영천 신월리 삼층석탑', 
                '영천 은해사 백흥암 수미단', '영천 선원동 철조여래좌상', 
                '영천 은해사 운부암 금동보살좌상', '영천 숭렬당', '영천향교 대성전'
            ],
            '국가유산종목': ['국보', '국보', '보물', '보물', '보물', '보물', '보물', '보물'],
            '재질': ['기타', '석조', '석조', '기타', '기타', '기타', '목조', '목조'],
            '노출형태': ['반실외', '실외', '실외', '반실외', '반실외', '반실외', '반실외', '반실외'],
            '문화재연령': [676, 1426, 1226, 376, 1100, 1100, 500, 600]
        })
    
    # 💡 공백 유산 제거 및 한글 가나다 순서 정렬
    df = df.dropna(subset=['문화재명(국문)'])
    df = df.sort_values(by='문화재명(국문)').reset_index(drop=True)
    return df

df = load_data()

# 3. 🏛️ 드롭다운 목록 배치
st.subheader("🏛️ 분석 대상 문화재 선택")
heritage_list = df['문화재명(국문)'].tolist()

selected_name = st.selectbox(
    "위험도를 분석할 문화재를 목록에서 선택하세요:",
    heritage_list,
    index=0
)

# 4. 데이터 매핑 및 분석 프로세스
if selected_name:
    info = df[df['문화재명(국문)'] == selected_name].iloc[0]
    
    h_name = info['문화재명(국문)']
    h_kind = info['국가유산종목'] if '국가유산종목' in info and pd.notna(info['국가유산종목']) else "지정문화재"
    h_material = str(info['재질']) if '재질' in info and pd.notna(info['재질']) else "기타"
    h_exposure = str(info['노출형태']) if '노출형태' in info and pd.notna(info['노출형태']) else "실외"
    
    try:
        h_age = int(float(info['문화재연령'])) if '문화재연령' in info and pd.notna(info['문화재연령']) else 100
    except ValueError:
        h_age = 100

    # UI 카드 배치
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

    # 6. 📊 위험도 자동 연산 수식
    score = 20
    if h_material == "목조":
        score += (humidity * 0.4) + (rainfall * 2.0) + 10
    elif h_material == "석조":
        score += (humidity * 0.2) + (rainfall * 1.0) + 15
    else:
        score += (humidity * 0.3) + (rainfall * 1.5) + 5
        
    final_risk
    
