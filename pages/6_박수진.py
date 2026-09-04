import os
import pandas as pd
import requests
import streamlit as st

# ==========================================================
# 1. 페이지 설정
# ==========================================================
st.set_page_config(
    page_title="영천 국가유산 지도",
    layout="wide"
)

st.title("📍 영천 국가유산 지도")


# ==========================================================
# 2. 카카오 REST API 키
# ==========================================================
# .streamlit/secrets.toml에 저장하는 것을 권장
#
# KAKAO_API_KEY = "발급받은 REST API 키"
#
KAKAO_API_KEY = st.secrets.get("KAKAO_API_KEY", "")


# ==========================================================
# 3. 지역별 보정 좌표
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
# 4. 좌표 유효성 검사
# ==========================================================
def valid_coordinate(lat, lon):

    if pd.isna(lat) or pd.isna(lon):
        return False

    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return False

    # 대한민국 대략적인 범위
    return (
        33 <= lat <= 39
        and
        124 <= lon <= 132
    )


# ==========================================================
# 5. 카카오 주소 검색 API
# ==========================================================
@st.cache_data(show_spinner=False)
def kakao_address_search(address):

    if not KAKAO_API_KEY:
        return None, None, "카카오 API 키 없음"

    if not address:
        return None, None, "주소 없음"

    url = "https://dapi.kakao.com/v2/local/search/address.json"

    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }

    params = {
        "query": address
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=5
        )

        if response.status_code != 200:
            return (
                None,
                None,
                f"카카오 API 오류: {response.status_code}"
            )

        data = response.json()

        documents = data.get("documents", [])

        if not documents:
            return None, None, "카카오 주소 검색 결과 없음"

        # 첫 번째 검색 결과 사용
        document = documents[0]

        longitude = float(document["x"])
        latitude = float(document["y"])

        return (
            latitude,
            longitude,
            "카카오 주소 검색 성공"
        )

    except Exception as e:

        return (
            None,
            None,
            f"카카오 API 오류: {str(e)}"
        )


# ==========================================================
# 6. 주소 fallback 검색
# ==========================================================
def find_by_address(address):

    address = str(address).strip()

    if not address:
        return None, None

    # 긴 키워드부터 검사
    for key in sorted(
        LOCATION_COORDS.keys(),
        key=len,
        reverse=True
    ):

        if key in address:

            lat, lon = LOCATION_COORDS[key]

            return (
                (lat, lon),
                f"주소 fallback: {key}"
            )

    return None, None


# ==========================================================
# 7. 문화재명 fallback 검색
# ==========================================================
def find_by_name(name):

    name = str(name).strip()

    if not name:
        return None, None

    for key in sorted(
        LOCATION_COORDS.keys(),
        key=len,
        reverse=True
    ):

        if key in name:

            lat, lon = LOCATION_COORDS[key]

            return (
                (lat, lon),
                f"문화재명 fallback: {key}"
            )

    return None, None


# ==========================================================
# 8. CSV 로드 + 좌표 자동 보정
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
    # 필요한 컬럼 확인
    # ------------------------------------------------------
    if "문화재명(국문)" not in df.columns:

        st.error(
            "❌ CSV에 '문화재명(국문)' 컬럼이 없습니다."
        )

        st.stop()

    if "소재지상세" not in df.columns:
        df["소재지상세"] = ""

    if "위도" not in df.columns:
        df["위도"] = None

    if "경도" not in df.columns:
        df["경도"] = None

    # 숫자 변환
    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )

    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )

    # 보정 방법 기록
    df["좌표보정방법"] = ""

    # ======================================================
    # 좌표 보정
    # ======================================================
    for i in df.index:

        name = str(
            df.at[i, "문화재명(국문)"]
        ).strip()

        address = str(
            df.at[i, "소재지상세"]
        ).strip()

        # --------------------------------------------------
        # 0순위
        # 기존 CSV 좌표가 정상이라면 그대로 사용
        # --------------------------------------------------
        if valid_coordinate(
            df.at[i, "위도"],
            df.at[i, "경도"]
        ):

            df.at[i, "좌표보정방법"] = "기존 CSV 좌표"

            continue


        # ==================================================
        # 1순위 ★ 카카오 API
        # ==================================================
        lat, lon, message = kakao_address_search(
            address
        )

        if lat is not None and lon is not None:

            df.at[i, "위도"] = lat
            df.at[i, "경도"] = lon
            df.at[i, "좌표보정방법"] = message

            continue


        # ==================================================
        # 2순위 ★ 주소 fallback
        # ==================================================
        result, method = find_by_address(
            address
        )

        if result:

            df.at[i, "위도"] = result[0]
            df.at[i, "경도"] = result[1]
            df.at[i, "좌표보정방법"] = method

            continue


        # ==================================================
        # 3순위 ★ 문화재명 fallback
        # ==================================================
        result, method = find_by_name(
            name
        )

        if result:

            df.at[i, "위도"] = result[0]
            df.at[i, "경도"] = result[1]
            df.at[i, "좌표보정방법"] = method

            continue


        # ==================================================
        # 최종 실패
        # ==================================================
        df.at[i, "좌표보정방법"] = (
            "❌ 좌표 확인 실패"
        )

    return df


# ==========================================================
# 9. 데이터 불러오기
# ==========================================================
df = load_and_fix_data()

if df is None:

    st.error(
        "❌ CSV 파일을 찾을 수 없습니다."
    )

    st.stop()


# ==========================================================
# 10. 지도 데이터
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
    &
    df["longitude"].notna()
    &
    (df["latitude"] > 0)
    &
    (df["longitude"] > 0)
].copy()


# ==========================================================
# 11. 누락 좌표
# ==========================================================
missing_data = df[
    df["latitude"].isna()
    |
    df["longitude"].isna()
    |
    (df["latitude"] <= 0)
    |
    (df["longitude"] <= 0)
].copy()


# ==========================================================
# 12. 결과 표시
# ==========================================================
if len(missing_data) > 0:

    st.warning(
        f"⚠️ 아직 좌표를 찾지 못한 문화재가 "
        f"{len(missing_data)}건 있습니다."
    )

    st.subheader(
        "🔎 좌표 확인이 필요한 문화재"
    )

    show_columns = [
        "문화재명(국문)",
        "소재지상세",
        "위도",
        "경도",
        "좌표보정방법"
    ]

    show_columns = [
        c for c in show_columns
        if c in missing_data.columns
    ]

    st.dataframe(
        missing_data[show_columns],
        use_container_width=True
    )

else:

    st.success(
        f"🎉 총 {len(df)}건의 모든 문화재 좌표가 정상적으로 확보되었습니다!"
    )


# ==========================================================
# 13. 지도
# ==========================================================
st.subheader("🗺️ 국가유산 위치")

st.map(
    map_data[
        ["latitude", "longitude"]
    ]
)


# ==========================================================
# 14. 전체 목록
# ==========================================================
st.subheader(
    "📋 전체 국가유산 목록"
)

st.dataframe(
    df,
    use_container_width=True
)
