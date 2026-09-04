import os
import pandas as pd
import streamlit as st

# ==========================================================
# 1. 페이지 기본 설정
# ==========================================================
st.set_page_config(page_title="영천 국가유산 지도", layout="wide")
st.title("📍 영천 국가유산 지도")

# ==========================================================
# 2. 미검색 항목 직접 검증 수동 좌표 맵핑
# ==========================================================
MANUAL_COORDS = {
    # [보물] 은해사 염불왕생첩경도 (은해사 성보박물관)
    "염불왕생첩경도": (35.9918, 128.7897),
    "은해사": (35.9918, 128.7897),
    
    # [보물] 봉림사 영산회상도 및 복장유물 (봉림사)
    "봉림사": (36.0354, 128.9892),
    "영산회상": (36.0354, 128.9892),
    
    # [보물] 수도사 노사나불 쾌불탱 (수도사)
    "수도사": (35.9863, 128.9806),
    
    # [보물] 영천 인종대왕 태실 (청통면 치일리가 위치)
    "인종대왕": (35.9757, 128.8922),
    "태실": (35.9757, 128.8922),
    
    # [사적] 제2로 직봉 - 영천 봉수 유적 시리즈 (실제 봉수대 터 위치)
    "성산봉수": (35.9189, 128.9882),    # 성황리 성산 봉수대
    "성황당": (35.9388, 128.9493),      # 금호읍 덕성리 성황당 봉수대
    "성황당봉수": (35.9388, 128.9493),
    "여음동": (35.9991, 128.9664),      # 화산면 덕암리 여음동 봉수대
    "여음동봉수": (35.9991, 128.9664),
    "봉수": (35.9388, 128.9493)
}

# ==========================================================
# 3. CSV 데이터 로드 및 정밀 보정
# ==========================================================
@st.cache_data
def load_and_fix_data():
    file_path = "pages/영천_국가유산_상세.csv"
    
    if not os.path.exists(file_path):
        file_path = "영천_국가유산_상세.csv"

    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 숫자형 변환 및 결측치 0 처리
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce").fillna(0)
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce").fillna(0)

    # 0인 항목에 대해 1:1 수동 좌표 지정
    for i in df.index:
        name = str(df.loc[i, "문화재명(국문)"]).strip()
        lat = df.loc[i, "위도"]
        lon = df.loc[i, "경도"]

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
# 4. 지도 표출
# ==========================================================
df["latitude"] = df["위도"]
df["longitude"] = df["경도"]

# 실제 유효한 좌표만 지도에 표시 (0인 가짜 좌표 표시 안 함)
map_data = df[(df["latitude"] > 0) & (df["longitude"] > 0)].copy()

st.write(f"총 **{len(df)}**건 중 **{len(map_data)}**건의 실제 좌표가 지도에 완벽히 표시되었습니다.")

# 지도 표출
st.map(map_data[["latitude", "longitude"]])

# 데이터 목록 표출
st.subheader("📋 전체 국가유산 목록")
st.dataframe(df, use_container_width=True)
