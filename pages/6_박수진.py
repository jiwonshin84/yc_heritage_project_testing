import os
import pandas as pd
import streamlit as st

# ==========================================================
# 1. 페이지 설정
# ==========================================================
st.set_page_config(page_title="영천 국가유산 지도", layout="wide")
st.title("📍 영천 국가유산 지도")

# ==========================================================
# 2. CSV 파일 불러오기 (캐싱 적용으로 빠른 로딩)
# ==========================================================
@st.cache_data
def load_data():
    file_path = "pages/영천_국가유산_상세.csv"
    
    # pages 폴더에 없을 경우 루트 경로 확인
    if not os.path.exists(file_path):
        file_path = "영천_국가유산_상세.csv"

    if not os.path.exists(file_path):
        return None

    return pd.read_csv(file_path, encoding="utf-8-sig")

df = load_data()

if df is None:
    st.error("❌ CSV 파일을 찾을 수 없습니다. '영천_국가유산_상세.csv' 파일을 올바른 위치에 업로드해주세요.")
    st.stop()

st.write(f"총 **{len(df)}**건의 데이터가 로드되었습니다.")

# ==========================================================
# 3. 지도 표출용 데이터 전처리
# ==========================================================
# 위도, 경도 열을 숫자형으로 변환
df["latitude"] = pd.to_numeric(df["위도"], errors="coerce")
df["longitude"] = pd.to_numeric(df["경도"], errors="coerce")

# 좌표가 존재하는 데이터만 추출 (유효한 위도, 경도)
map_data = df.dropna(subset=["latitude", "longitude"]).copy()
map_data = map_data[(map_data["latitude"] != 0) & (map_data["longitude"] != 0)]

# ==========================================================
# 4. 지도 및 데이터 표출
# ==========================================================
if not map_data.empty:
    # 지도 표출
    st.map(map_data[["latitude", "longitude"]])
else:
    st.warning("⚠️ 표시할 좌표 데이터가 없습니다. CSV 파일의 위도/경도 값을 확인해주세요.")

# 데이터 테이블 표출
st.subheader("📋 국가유산 목록")
st.dataframe(df, use_container_width=True)
