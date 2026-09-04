import os
import time
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
# .streamlit/secrets.toml
#
# KAKAO_API_KEY = "카카오 REST API 키"
#
KAKAO_API_KEY = st.secrets.get("KAKAO_API_KEY", "")


# ==========================================================
# 3. 기존 보정용 좌표
# ==========================================================
LOCATION_COORDS = {

    # 주요 사찰 / 문화유산
    "은해사": (35.9918, 128.7897),
    "수도사": (35.9863, 128.9806),
    "거조사": (36.0336, 128.7825),
    "봉림사": (36.0354, 128.9892),
    "임고서원": (35.9907, 128.9475),
    "인종대왕": (35.9757, 128.8922),

    # 읍 / 면
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

    # 동
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

    return (
        33 <= lat <= 39
        and
        124 <= lon <= 132
    )


# ==========================================================
# 5. 카카오 주소 검색
# ==========================================================
@st.cache_data(show_spinner=False)
def kakao_address_search(address):

    if not KAKAO_API_KEY:
        return None, None, "카카오 API 키 없음"

    if not address:
        return None, None, "주소 없음"

    url = (
        "https://dapi.kakao.com/"
        "v2/local/search/address.json"
    )

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
                f"카카오 주소 API 오류 {response.status_code}"
            )

        data = response.json()

        documents = data.get(
            "documents",
            []
        )

        if not documents:

            return (
                None,
                None,
                "카카오 주소 검색 결과 없음"
            )

        doc = documents[0]

        lat = float(doc["y"])
        lon = float(doc["x"])

        return (
            lat,
            lon,
            "① 카카오 주소 검색"
        )

    except Exception as e:

        return (
            None,
            None,
            f"카카오 주소 검색 오류: {e}"
        )


# ==========================================================
# 6. 카카오 키워드 검색
# ==========================================================
@st.cache_data(show_spinner=False)
def kakao_keyword_search(name):

    if not KAKAO_API_KEY:
        return None, None, "카카오 API 키 없음"

    if not name:
        return None, None, "문화재명 없음"

    url = (
        "https://dapi.kakao.com/"
        "v2/local/search/keyword.json"
    )

    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }

    # 영천시 범위로 검색
    query = f"영천시 {name}"

    params = {
        "query": query,
        "size": 15
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
                f"카카오 키워드 API 오류 {response.status_code}"
            )

        data = response.json()

        documents = data.get(
            "documents",
            []
        )

        if not documents:

            return (
                None,
                None,
                "카카오 키워드 검색 결과 없음"
            )

        # --------------------------------------------------
        # 영천시 결과 우선
        # --------------------------------------------------
        for doc in documents:

            address_name = str(
                doc.get("address_name", "")
            )

            road_address = str(
                doc.get("road_address_name", "")
            )

            place_name = str(
                doc.get("place_name", "")
            )

            combined = (
                address_name
                + " "
                + road_address
                + " "
                + place_name
            )

            if "영천" in combined:

                lat = float(doc["y"])
                lon = float(doc["x"])

                return (
                    lat,
                    lon,
                    f"② 카카오 키워드 검색: {place_name}"
                )

        # 영천 결과가 없어도 첫 번째 결과 사용
        doc = documents[0]

        lat = float(doc["y"])
        lon = float(doc["x"])

        return (
            lat,
            lon,
            f"② 카카오 키워드 검색: "
            f"{doc.get('place_name', '')}"
        )

    except Exception as e:

        return (
            None,
            None,
            f"카카오 키워드 검색 오류: {e}"
        )


# ==========================================================
# 7. 기존 주소 좌표 검색
# ==========================================================
def find_by_address(address):

    address = str(address).strip()

    if not address:
        return None, None

    # 긴 키워드부터
    for key in sorted(
        LOCATION_COORDS.keys(),
        key=len,
        reverse=True
    ):

        if key in address:

            lat, lon = LOCATION_COORDS[key]

            return (
                (lat, lon),
                f"③ 기존 주소 좌표: {key}"
            )

    return None, None


# ==========================================================
# 8. 기존 문화재명 좌표 검색
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
                f"④ 기존 문화재명 좌표: {key}"
            )

    return None, None


# ==========================================================
# 9. CSV 로드
# ==========================================================
@st.cache_data
def load_data():

    file_path = (
        "pages/영천_국가유산_상세.csv"
    )

    if not os.path.exists(file_path):

        file_path = (
            "영천_국가유산_상세.csv"
        )

    if not os.path.exists(file_path):

        return None

    df = pd.read_csv(
        file_path,
        encoding="utf-8-sig"
    )

    # ------------------------------------------------------
    # 컬럼 생성
    # ------------------------------------------------------
    if "문화재명(국문)" not in df.columns:

        st.error(
            "❌ '문화재명(국문)' 컬럼이 없습니다."
        )

        st.stop()

    if "소재지상세" not in df.columns:
        df["소재지상세"] = ""

    if "위도" not in df.columns:
        df["위도"] = None

    if "경도" not in df.columns:
        df["경도"] = None

    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )

    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )

    df["좌표보정방법"] = ""

    return df


# ==========================================================
# 10. 좌표 자동 보정
# ==========================================================
def fix_coordinates(df):

    total = len(df)

    progress = st.progress(0)

    status = st.empty()

    for number, i in enumerate(df.index):

        # --------------------------------------------------
        # 이미 좌표가 있는 경우
        # --------------------------------------------------
        if valid_coordinate(
            df.at[i, "위도"],
            df.at[i, "경도"]
        ):

            df.at[i, "좌표보정방법"] = (
                "기존 CSV 좌표"
            )

            continue

        name = str(
            df.at[i, "문화재명(국문)"]
        ).strip()

        address = str(
            df.at[i, "소재지상세"]
        ).strip()


        # ==================================================
        # ① 카카오 주소 검색
        # ==================================================
        lat, lon, method = (
            kakao_address_search(address)
        )

        if lat is not None:

            df.at[i, "위도"] = lat
            df.at[i, "경도"] = lon
            df.at[i, "좌표보정방법"] = method

            continue


        # ==================================================
        # ② 카카오 문화재명 키워드 검색
        # ==================================================
        lat, lon, method = (
            kakao_keyword_search(name)
        )

        if lat is not None:

            df.at[i, "위도"] = lat
            df.at[i, "경도"] = lon
            df.at[i, "좌표보정방법"] = method

            continue


        # ==================================================
        # ③ 기존 주소 좌표
        # ==================================================
        result, method = (
            find_by_address(address)
        )

        if result:

            df.at[i, "위도"] = result[0]
            df.at[i, "경도"] = result[1]
            df.at[i, "좌표보정방법"] = method

            continue


        # ==================================================
        # ④ 기존 문화재명 좌표
        # ==================================================
        result, method = (
            find_by_name(name)
        )

        if result:

            df.at[i, "위도"] = result[0]
            df.at[i, "경도"] = result[1]
            df.at[i, "좌표보정방법"] = method

            continue


        # ==================================================
        # ⑤ 최종 실패
        # ==================================================
        df.at[i, "좌표보정방법"] = (
            "❌ 좌표 확인 실패"
        )

        progress.progress(
            (number + 1) / total
        )

        status.write(
            f"좌표 확인 중... "
            f"{number + 1}/{total}"
        )

        # API 과도한 호출 방지
        time.sleep(0.05)

    progress.empty()
    status.empty()

    return df


# ==========================================================
# 11. 데이터 불러오기
# ==========================================================
df = load_data()

if df is None:

    st.error(
        "❌ CSV 파일을 찾을 수 없습니다."
    )

    st.stop()


# ==========================================================
# 12. 좌표 보정 실행
# ==========================================================
if st.button(
    "🔄 누락 좌표 자동 보완",
    type="primary"
):

    # 캐시된 함수 결과를 초기화
    kakao_address_search.clear()
    kakao_keyword_search.clear()

    df = fix_coordinates(df)

    # 세션에 저장
    st.session_state["fixed_df"] = df


# 보정된 데이터가 있으면 사용
if "fixed_df" in st.session_state:

    df = st.session_state["fixed_df"]


# ==========================================================
# 13. 지도용 데이터
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
# 14. 누락 좌표
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
# 15. 결과 표시
# ==========================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "전체 국가유산",
        len(df)
    )

with col2:
    st.metric(
        "지도 표시",
        len(map_data)
    )

with col3:
    st.metric(
        "좌표 미확인",
        len(missing_data)
    )


if len(missing_data) > 0:

    st.warning(
        f"⚠️ 아직 {len(missing_data)}건의 "
        "좌표를 찾지 못했습니다."
    )

    st.subheader(
        "🔎 좌표 확인이 필요한 문화재"
    )

    columns = [
        "문화재명(국문)",
        "소재지상세",
        "위도",
        "경도",
        "좌표보정방법"
    ]

    columns = [
        c for c in columns
        if c in missing_data.columns
    ]

    st.dataframe(
        missing_data[columns],
        use_container_width=True
    )

else:

    st.success(
        f"🎉 총 {len(df)}건의 모든 "
        "국가유산 좌표가 확보되었습니다!"
    )


# ==========================================================
# 16. 지도
# ==========================================================
st.subheader(
    "🗺️ 국가유산 위치"
)

if len(map_data) > 0:

    st.map(
        map_data[
            ["latitude", "longitude"]
        ]
    )

else:

    st.info(
        "표시할 좌표가 없습니다."
    )


# ==========================================================
# 17. 전체 목록
# ==========================================================
st.subheader(
    "📋 전체 국가유산 목록"
)

st.dataframe(
    df,
    use_container_width=True
)
