import streamlit as st

st.title("🌦 박수진")



import streamlit as st
import plotly.graph_objects as go
import requests
import xml.etree.ElementTree as ET

# ---------------------------------------------------------
# 상단 타이틀 및 소개
# ---------------------------------------------------------
st.header("🛡️ 박수진 - 훼손위험도 예측 시스템")
st.write("국가유산청 오픈 API를 통해 영천의 모든 문화유산을 실시간 검색하고 위험도를 예측합니다.")
st.markdown("---")

# ---------------------------------------------------------
# 1. 🔍 국가유산청 API 연동 함수 (영천 지역 한정 검색)
# ---------------------------------------------------------
def search_heritage(ccbaMnm):
    # 국가유산청 문화재 검색 API URL (시도코드 37 = 경북, 시군구코드 23 = 영천시)
    url = "http://www.cha.go.kr/cha/SearchKindOpenapiList.do"
    params = {
        "ccbaCtcd": "37",   # 경상북도
        "ccbaMnm": ccbaMnm  # 사용자가 입력한 검색어
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            result_list = []
            for item in items:
                # 영천시 데이터만 필터링 (주소에 '영천'이 포함되어 있는지 확인)
                ccbaLcto = item.find("ccbaLcto").text if item.find("ccbaLcto") is not None else ""
                if "영천" in ccbaLcto:
                    result_list.append({
                        "name": item.find("ccbaMnm1").text,    # 문화재 국문명
                        "status": item.find("ccmaName").text,   # 문화재 종목 (보물, 국보 등)
                        "location": ccbaLcto,                  # 주소
                        "ccbaKdcd": item.find("ccbaKdcd").text, # 종목코드
                        "ccbaAsno": item.find("ccbaAsno").text, # 지정번호
                        "ccbaCncl": item.find("ccbaCncl").text  # 지정해제여부
                    })
            return result_list
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return []

# ---------------------------------------------------------
# 2. 🔍 문화재 검색 UI
# ---------------------------------------------------------
st.subheader("🔍 영천 문화유산 검색")
search_keyword = st.text_input(
    "영천의 문화재 명칭을 입력하세요:", 
    placeholder="예: 청제비, 거조암, 신
