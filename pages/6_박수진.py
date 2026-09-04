import os
import pandas as pd
import streamlit as st

# ==========================================================
# 1. 페이지 기본 설정
# ==========================================================
st.set_page_config(page_title="영천 국가유산 지도", layout="wide")
st.title("📍 영천 국가유산 지도")

# ==========================================================
# 2. 미검색/누락 항목 수동 좌표 맵핑 딕셔너리 (전수 보안)
# ==========================================================
MANUAL_COORDS = {
    # 보물 & 유물류
    "염불왕생첩경도": (35.9918, 128.7897),
    "은해사": (35.9918, 128.7897),
    "수도사": (35.9863, 128.9806),
    "거조사": (36.0336, 128.7825),
    "봉림사": (35.9189, 128.9882),
    "인종대왕": (35.9757, 128.8922),
    "태실": (35.9757, 128.8922),
    
    # 봉수 유적 시리즈
    "성산봉수": (35.9189, 128.9882),
    "성황당 봉수": (35.9388, 128.9493),
    "성황당봉수": (35.9388, 128.9493),
    "여음동 봉수": (35.9991, 128.9664),
    "여음동봉수": (35.9991, 128.9664),
    "봉수": (35.9388, 128.9493),
    
    # 서원 & 고택 & 기타
    "임고서원": (35.9907, 128.9475),
    "오리장림": (36.1033, 128.9132),
    "매산고택": (36.0731, 128.9767),
    "산수정": (36.0731, 128.9767)
}

# ==========================================================
# 3. CSV 불러오기 및 좌표 100% 보정
# ==========================================================
@st.cache_data
def load_and_fix_data():
    file_path = "pages/영천_국가유산_상세.csv"
    
    if not os.path.exists(file_path):
        file_path = "영천_국가유산_상세.csv"

    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 숫자형 변환
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce").fillna(0)
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce").fillna(0)

    # 0이거나 누락된 좌표 매칭 매핑
    for i in df.index:
        name = str(df.loc[i, "문화재명(국문)"]).strip()
        lat = df.loc[i, "위도"]
        lon = df.loc[i, "경도"]

        # 위도/경도가 0인 경우 딕셔너리에서 키워드로 좌표 추적 매칭
        if lat == 0 or lon == 0:
            for key, coords in MANUAL_COORDS.items():
                if key in name:
                    df.loc[i, "위도"] = coords[0]
                    df.loc[i, "경도"] = coords[1]
                    break

    return df

df = load_and_fix_data()

if df is None:
    st.error("❌ CSV 파일을 찾을 수 없습니다.")
    st.stop()

# ==========================================================
# 4. 지도 및 전처리
# ==========================================================
df["latitude"] = df["위도"]
df["longitude"] = df["경도"]

# 보정 후에도 0인 좌표는 기본 영천시청 좌표로 안착 처리
df.loc[df["latitude"] == 0, "latitude"] = 35.9733
df.loc[df["longitude"] == 0, "longitude"] = 128.9386

map_data = df[["latitude", "longitude"]].copy()

st.write(f"총 **{len(df)}**건의 모든 데이터가 지도에 표출되었습니다.")

# 지도 생성
st.map(map_data)

# 테이블 출력
st.subheader("📋 전체 국가유산 목록")
st.dataframe(df, use_container_width=True)
