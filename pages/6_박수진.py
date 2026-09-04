import os
import re
import pandas as pd
import streamlit as st

# ==========================================================
# 1. 페이지 설정
# ==========================================================
st.set_page_config(page_title="영천 국가유산 지도", layout="wide")
st.title("📍 영천 국가유산 지도")


# ==========================================================
# 2. 지역별 중심 좌표
# ==========================================================
LOCATION_COORDS = {
    "은해사": (35.9918, 128.7897),
    "수도사": (35.9863, 128.9806),
    "거조사": (36.0336, 128.7825),
    "봉림사": (36.0354, 128.9892),
    "임고서원": (35.9907, 128.9475),
    "인종대왕": (35.9757, 128.8922),

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
    "남부동": (35.9412, 128.9317),
}


# ==========================================================
# 3. 좌표가 유효한지 검사
# ==========================================================
def valid_coordinate(lat, lon):
    if pd.isna(lat) or pd.isna(lon):
        return False

    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return False

    # 대한민국 범위에 대략 맞는지 검사
    if not (33 <= lat <= 39):
        return False

    if not (124 <= lon <= 132):
        return False

    return True


# ==========================================================
# 4. 문화재명으로 좌표 찾기
# ==========================================================
def find_by_name(name):
    name = str(name).strip()

    # 긴 이름부터 검색
    for key in sorted(LOCATION_COORDS.keys(), key=len, reverse=True):
        if key in name:
            return LOCATION_COORDS[key], f"문화재명 매칭: {key}"

    return None, None


# ==========================================================
# 5. 주소로 좌표 찾기
# ==========================================================
def find_by_address(address):
    address = str(address).strip()

    # 긴 이름부터 검색
    for key in sorted(LOCATION_COORDS.keys(), key=len, reverse=True):
        if key in address:
            return LOCATION_COORDS[key], f"주소 매칭: {key}"

    return None, None


# ==========================================================
# 6. CSV 로드 + 좌표 자동 보정
# ==========================================================
@st.cache_data
def load_and_fix_data():

    file_path = "pages/영천_국가유산_상세.csv"

    if not os.path.exists(file_path):
        file_path = "영천_국가유산_상세.csv"

    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(
        file_path,
        encoding="utf-8-sig"
    )

    # ------------------------------------------------------
    # 필요한 컬럼 존재 여부 확인
    # ------------------------------------------------------
    required_columns = ["문화재명(국문)"]

    for col in required_columns:
        if col not in df.columns:
            st.error(f"❌ CSV에 '{col}' 컬럼이 없습니다.")
            st.stop()

    # 위도/경도 컬럼이 없으면 생성
    if "위도" not in df.columns:
        df["위도"] = None

    if "경도" not in df.columns:
        df["경도"] = None

    # 문자열 주소 컬럼
    if "소재지상세" not in df.columns:
        df["소재지상세"] = ""

    # 숫자로 변환
    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )

    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )

    # ------------------------------------------------------
    # 좌표 보정 결과 기록용 컬럼
    # ------------------------------------------------------
    df["좌표보정방법"] = ""

    # ------------------------------------------------------
    # 좌표 보정
    # ------------------------------------------------------
    for i in df.index:

        lat = df.at[i, "위도"]
        lon = df.at[i, "경도"]

        # 이미 정상 좌표가 있으면 그대로 사용
        if valid_coordinate(lat, lon):
            df.at[i, "좌표보정방법"] = "기존 좌표"
            continue

        name = str(
            df.at[i, "문화재명(국문)"]
        ).strip()

        address = str(
            df.at[i, "소재지상세"]
        ).strip()

        # ==================================================
        # 1단계: 문화재명
        # ==================================================
        result, method = find_by_name(name)

        if result:
            df.at[i, "위도"] = result[0]
            df.at[i, "경도"] = result[1]
            df.at[i, "좌표보정방법"] = method
            continue

        # ==================================================
        # 2단계: 주소
        # ==================================================
        result, method = find_by_address(address)

        if result:
            df.at[i, "위도"] = result[0]
            df.at[i, "경도"] = result[1]
            df.at[i, "좌표보정방법"] = method
            continue

        # ==================================================
        # 3단계: 영천시라는 주소만 있는 경우
        # ==================================================
        if "영천시" in address:
            # 도시 중심부 임시 좌표
            df.at[i, "위도"] = 35.9733
            df.at[i, "경도"] = 128.9386
            df.at[i, "좌표보정방법"] = "영천시 중심 임시좌표"

    return df


# ==========================================================
# 7. 데이터 불러오기
# ==========================================================
df = load_and_fix_data()

if df is None:
    st.error("❌ CSV 파일을 찾을 수 없습니다.")
    st.stop()


# ==========================================================
# 8. 지도용 데이터 생성
# ==========================================================
df["latitude"] = pd.to_numeric(
    df["위도"],
    errors="coerce"
)

df["longitude"] = pd.to_numeric(
    df["경도"],
    errors="coerce"
)

map_data = df[
    df["latitude"].notna()
    & df["longitude"].notna()
    & (df["latitude"] > 0)
    & (df["longitude"] > 0)
].copy()


# ==========================================================
# 9. 누락 데이터 확인
# ==========================================================
missing_data = df[
    df["latitude"].isna()
    | df["longitude"].isna()
    | (df["latitude"] <= 0)
    | (df["longitude"] <= 0)
].copy()


if len(missing_data) > 0:

    st.warning(
        f"⚠️ 총 {len(missing_data)}건의 좌표를 찾지 못했습니다."
    )

    st.subheader("🔎 좌표가 없는 문화재")

    columns_to_show = [
        "문화재명(국문)",
        "소재지상세",
        "위도",
        "경도",
        "좌표보정방법"
    ]

    columns_to_show = [
        c for c in columns_to_show
        if c in missing_data.columns
    ]

    st.dataframe(
        missing_data[columns_to_show],
        use_container_width=True
    )

else:

    st.success(
        f"🎉 총 {len(df)}건의 모든 문화재 좌표가 정상입니다!"
    )


# ==========================================================
# 10. 지도
# ==========================================================
st.subheader("🗺️ 국가유산 위치")

st.map(
    map_data[
        ["latitude", "longitude"]
    ]
)


# ==========================================================
# 11. 전체 데이터
# ==========================================================
st.subheader("📋 전체 국가유산 목록")

st.dataframe(
    df,
    use_container_width=True
)
