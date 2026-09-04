import os
import pandas as pd
import streamlit as st

# ==========================================================
# 1. 페이지 기본 설정
# ==========================================================
st.set_page_config(page_title="영천 국가유산 지도", layout="wide")
st.title("📍 영천 국가유산 지도")

# ==========================================================
# 2. 영천시 주요 읍·면·동/리 및 주요 지점 좌표 사전
# ==========================================================
LOCATION_COORDS = {
    # 주요 지역/사찰/유적
    "은해사": (35.9918, 128.7897),
    "수도사": (35.9863, 128.9806),
    "거조사": (36.0336, 128.7825),
    "봉림사": (36.0354, 128.9892),
    "임고서원": (35.9907, 128.9475),
    "인종대왕": (35.9757, 128.8922),
    
    # 영천시 읍·면·동 중심 좌표 (소재지 기준 2차 보정용)
    "청통면": (35.9836, 128.8351),
    "신령면": (36.0392, 128.7958),
    "화산면": (36.0247, 128.9221),
    "화북면": (36.1264, 128.9719),
    "화남면": (36.0719, 128.9739),
    "자양면": (36.0592, 129.0411),
    "임고면": (35.9958, 128.9897),
    "고경면": (35.9619, 129.0478),
    "북안면": (35.8894, 128.9958),
    "대창면": (35.8647, 128.8953),
    "금호읍": (35.9189, 128.8586),
    "동부동": (35.9767, 128.9567),
    "중앙동": (35.9686, 128.9372),
    "서부동": (35.9653, 128.9231),
    "완산동": (35.9583, 128.9358),
    "남부동": (35.9412, 128.9317)
}

# ==========================================================
# 3. CSV 데이터 로드 및 누락 좌표 2단계 완전 보정
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

    # 보정 진행
    for i in df.index:
        lat = df.loc[i, "위도"]
        lon = df.loc[i, "경도"]

        if lat == 0 or lon == 0:
            name = str(df.loc[i, "문화재명(국문)"]).strip()
            addr = str(df.loc[i, "소재지상세"]).strip() if "소재지상세" in df.columns else ""

            matched = False
            # 1단계: 문화재명 키워드 매칭
            for key, coords in LOCATION_COORDS.items():
                if key in name:
                    df.loc[i, "위도"] = coords[0]
                    df.loc[i, "경도"] = coords[1]
                    matched = True
                    break
            
            # 2단계: 소재지 주소(읍/면/동) 매칭
            if not matched and addr:
                for key, coords in LOCATION_COORDS.items():
                    if key in addr:
                        df.loc[i, "위도"] = coords[0]
                        df.loc[i, "경도"] = coords[1]
                        break

    return df

df = load_and_fix_data()

if df is None:
    st.error("❌ CSV 파일을 찾을 수 없습니다.")
    st.stop()

# ==========================================================
# 4. 지도 표출 및 누락 현황 출력
# ==========================================================
df["latitude"] = df["위도"]
df["longitude"] = df["경도"]

map_data = df[(df["latitude"] > 0) & (df["longitude"] > 0)].copy()

zero_count = len(df) - len(map_data)

if zero_count > 0:
    st.warning(f"⚠️ 현재 {zero_count}건의 좌표가 누락되어 있습니다.")
else:
    st.success(f"🎉 총 {len(df)}건의 모든 문화재 좌표가 100% 정상 표출되었습니다!")

# 지도 생성
st.map(map_data[["latitude", "longitude"]])

# 테이블 출력
st.subheader("📋 전체 국가유산 목록")
st.dataframe(df, use_container_width=True)
