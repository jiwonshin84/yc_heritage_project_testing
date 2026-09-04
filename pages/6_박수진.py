import os
import pandas as pd
import streamlit as st

# ==========================================================
# 1. 페이지 기본 설정
# ==========================================================
st.set_page_config(page_title="영천 국가유산 지도", layout="wide")
st.title("📍 영천 국가유산 지도")

# ==========================================================
# 2. 검색 안 되는 항목 수동 좌표 맵핑 딕셔너리
# ==========================================================
MANUAL_COORDS = {
    "영천 은해사 염불왕생첩경도": (35.9918, 128.7897),
    "영천 인종대왕 태실": (35.9757, 128.8922),
    "제2로 직봉 - 영천 성산봉수 유적": (35.9189, 128.9882),
    "제2로 직봉 - 영천 성황당 봉수 유적": (35.9388, 128.9493),
    "제2로 직봉 - 영천 여음동 봉수 유적": (35.9991, 128.9664)
}

# ==========================================================
# 3. CSV 불러오기 및 좌표 자동 보정
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

    # 누락된 0값 데이터 수동 보정 적용
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

st.write(f"총 **{len(df)}**건의 데이터가 로드되었습니다.")

# ==========================================================
# 4. 지도용 좌표 전처리
# ==========================================================
df["latitude"] = df["위도"]
df["longitude"] = df["경도"]

# 좌표가 정상인 데이터만 추출
map_data = df[(df["latitude"] > 0) & (df["longitude"] > 0)].copy()

# ==========================================================
# 5. 지도 및 데이터 표출
# ==========================================================
if not map_data.empty:
    st.map(map_data[["latitude", "longitude"]])
else:
    st.warning("⚠️ 표시할 좌표 데이터가 없습니다.")

st.subheader("📋 국가유산 목록")
st.dataframe(df, use_container_width=True)
