import os
import re
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
# 2. 카카오 REST API KEY
# ==========================================================
# .streamlit/secrets.toml
#
# KAKAO_API_KEY = "새로 발급받은 REST API KEY"
#
KAKAO_API_KEY = st.secrets.get(
    "KAKAO_API_KEY",
    ""
)

HEADERS = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}


# ==========================================================
# 3. 기존 수동 좌표
# ==========================================================
LOCATION_COORDS = {

    # 주요 문화유산
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
# 4. 수동 좌표
# ==========================================================
MANUAL_COORDS = {

    # 실제 검색 실패했던 문화재
    "임고서원은행나무": (
        35.9907,
        128.9475
    ),

    "임고서원 은행나무": (
        35.9907,
        128.9475
    ),
}


# ==========================================================
# 5. 좌표 유효성 검사
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
# 6. 주소 정제
# ==========================================================
def clean_address(addr):

    if pd.isna(addr):
        return None

    addr = str(addr)

    # 괄호 제거
    addr = re.sub(
        r"\(.*?\)",
        "",
        addr
    )

    # 검색 방해 단어 제거
    for word in [
        "외",
        "일원",
        "필지",
        "번지"
    ]:

        addr = addr.replace(
            word,
            ""
        )

    return " ".join(
        addr.split()
    ).strip()


# ==========================================================
# 7. 문화재명 정제
# ==========================================================
def refine_name(name):

    if pd.isna(name):
        return None

    name = str(name)

    # 검색 방해 단어
    remove_words = [
        "탱화",
        "유물",
        "일괄",
        "및",
        "구 "
    ]

    for word in remove_words:

        name = name.replace(
            word,
            ""
        )

    return " ".join(
        name.split()
    ).strip()


# ==========================================================
# 8. 카카오 API 공통 요청
# ==========================================================
def kakao_request(
    endpoint,
    query
):

    if not KAKAO_API_KEY:
        return []

    if not query:
        return []

    url = (
        "https://dapi.kakao.com/"
        f"v2/local/search/{endpoint}.json"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            params={
                "query": query,
                "size": 15
            },
            timeout=10
        )

        if response.status_code != 200:
            return []

        data = response.json()

        return data.get(
            "documents",
            []
        )

    except Exception:
        return []


# ==========================================================
# 9. 카카오 주소 검색
# ==========================================================
def get_coord_address(query):

    documents = kakao_request(
        "address",
        query
    )

    if not documents:
        return None, None

    # 첫 번째 결과
    doc = documents[0]

    try:

        lon = float(
            doc["x"]
        )

        lat = float(
            doc["y"]
        )

        if valid_coordinate(
            lat,
            lon
        ):

            return lat, lon

    except Exception:
        pass

    return None, None


# ==========================================================
# 10. 카카오 키워드 검색
# ==========================================================
def get_coord_keyword(query):

    documents = kakao_request(
        "keyword",
        query
    )

    if not documents:
        return None, None

    # ------------------------------------------------------
    # 영천 결과 우선
    # ------------------------------------------------------
    for doc in documents:

        address_name = str(
            doc.get(
                "address_name",
                ""
            )
        )

        road_address = str(
            doc.get(
                "road_address_name",
                ""
            )
        )

        combined = (
            address_name
            + " "
            + road_address
        )

        if "영천" in combined:

            try:

                lon = float(
                    doc["x"]
                )

                lat = float(
                    doc["y"]
                )

                if valid_coordinate(
                    lat,
                    lon
                ):

                    return lat, lon

            except Exception:
                continue

    # ------------------------------------------------------
    # 영천 결과가 없으면 첫 결과
    # ------------------------------------------------------
    try:

        doc = documents[0]

        lon = float(
            doc["x"]
        )

        lat = float(
            doc["y"]
        )

        if valid_coordinate(
            lat,
            lon
        ):

            return lat, lon

    except Exception:
        pass

    return None, None


# ==========================================================
# 11. 기존 주소 좌표 검색
# ==========================================================
def find_by_address(address):

    if not address:
        return None, None

    for key in sorted(
        LOCATION_COORDS.keys(),
        key=len,
        reverse=True
    ):

        if key in address:

            lat, lon = (
                LOCATION_COORDS[key]
            )

            return (
                lat,
                lon
            )

    return None, None


# ==========================================================
# 12. 기존 문화재명 좌표 검색
# ==========================================================
def find_by_name(name):

    if not name:
        return None, None

    for key in sorted(
        LOCATION_COORDS.keys(),
        key=len,
        reverse=True
    ):

        if key in name:

            lat, lon = (
                LOCATION_COORDS[key]
            )

            return (
                lat,
                lon
            )

    return None, None


# ==========================================================
# 13. 한 문화재 좌표 찾기
# ==========================================================
def find_coordinate(
    name,
    address
):

    # ======================================================
    # ① 수동 좌표
    # ======================================================
    if name in MANUAL_COORDS:

        lat, lon = MANUAL_COORDS[name]

        return (
            lat,
            lon,
            "① 수동 좌표"
        )


    # ======================================================
    # ② 카카오 문화재명
    # ======================================================
    lat, lon = get_coord_keyword(
        name
    )

    if lat is not None:

        return (
            lat,
            lon,
            "② 카카오 문화재명 검색"
        )


    # ======================================================
    # ③ 카카오 정제 문화재명
    # ======================================================
    refined_name = refine_name(
        name
    )

    if (
        refined_name
        and
        refined_name != name
    ):

        lat, lon = get_coord_keyword(
            refined_name
        )

        if lat is not None:

            return (
                lat,
                lon,
                "③ 카카오 정제명 검색"
            )


    # ======================================================
    # ④ 카카오 주소 검색
    # ======================================================
    cleaned_address = clean_address(
        address
    )

    if cleaned_address:

        lat, lon = get_coord_address(
            cleaned_address
        )

        if lat is not None:

            return (
                lat,
                lon,
                "④ 카카오 주소 검색"
            )


    # ======================================================
    # ⑤ 영천 + 문화재명
    # ======================================================
    lat, lon = get_coord_keyword(
        f"영천 {name}"
    )

    if lat is not None:

        return (
            lat,
            lon,
            "⑤ 카카오 영천+문화재명"
        )


    # ======================================================
    # ⑥ 영천 + 정제된 문화재명
    # ======================================================
    if refined_name:

        lat, lon = get_coord_keyword(
            f"영천 {refined_name}"
        )

        if lat is not None:

            return (
                lat,
                lon,
                "⑥ 카카오 영천+정제명"
            )


    # ======================================================
    # ⑦ 기존 주소 좌표
    # ======================================================
    result = find_by_address(
        address
    )

    if result:

        return (
            result[0],
            result[1],
            "⑦ 기존 주소 좌표"
        )


    # ======================================================
    # ⑧ 기존 문화재명 좌표
    # ======================================================
    result = find_by_name(
        name
    )

    if result:

        return (
            result[0],
            result[1],
            "⑧ 기존 문화재명 좌표"
        )


    # ======================================================
    # 최종 실패
    # ======================================================
    return (
        None,
        None,
        "❌ 좌표 확인 실패"
    )


# ==========================================================
# 14. CSV 불러오기
# ==========================================================
@st.cache_data
def load_data():

    file_path = (
        "pages/"
        "영천_국가유산_상세.csv"
    )

    if not os.path.exists(
        file_path
    ):

        file_path = (
            "영천_국가유산_상세.csv"
        )

    if not os.path.exists(
        file_path
    ):

        return None

    df = pd.read_csv(
        file_path,
        encoding="utf-8-sig"
    )

    # 필요한 컬럼
    if "문화재명(국문)" not in df.columns:

        st.error(
            "❌ 문화재명(국문) 컬럼이 없습니다."
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
# 15. 전체 좌표 보완
# ==========================================================
def fix_coordinates(df):

    df = df.copy()

    missing_indices = []

    # 먼저 누락된 것만 찾기
    for i in df.index:

        if not valid_coordinate(
            df.at[i, "위도"],
            df.at[i, "경도"]
        ):

            missing_indices.append(i)

    total = len(missing_indices)

    if total == 0:
        return df

    progress = st.progress(0)

    status = st.empty()

    success = 0
    fail = 0

    for number, i in enumerate(
        missing_indices,
        start=1
    ):

        name = str(
            df.at[i, "문화재명(국문)"]
        ).strip()

        address = str(
            df.at[i, "소재지상세"]
        ).strip()

        status.write(
            f"🔍 좌표 검색 중 "
            f"{number}/{total} : {name}"
        )

        lat, lon, method = (
            find_coordinate(
                name,
                address
            )
        )

        if lat is not None:

            df.at[i, "위도"] = lat
            df.at[i, "경도"] = lon
            df.at[i, "좌표보정방법"] = method

            success += 1

        else:

            df.at[i, "좌표보정방법"] = (
                "❌ 좌표 확인 실패"
            )

            fail += 1

        progress.progress(
            number / total
        )

        # API 과부하 방지
        time.sleep(0.3)

    status.empty()
    progress.empty()

    st.success(
        f"좌표 보완 완료! "
        f"성공 {success}건 / "
        f"실패 {fail}건"
    )

    return df


# ==========================================================
# 16. 데이터 로드
# ==========================================================
df = load_data()

if df is None:

    st.error(
        "❌ CSV 파일을 찾을 수 없습니다."
    )

    st.stop()


# ==========================================================
# 17. 좌표 보완 버튼
# ==========================================================
if st.button(
    "🔄 누락 좌표 자동 보완",
    type="primary"
):

    df = fix_coordinates(
        df
    )

    st.session_state[
        "fixed_df"
    ] = df


# ==========================================================
# 18. 보완된 데이터 사용
# ==========================================================
if (
    "fixed_df"
    in st.session_state
):

    df = st.session_state[
        "fixed_df"
    ]


# ==========================================================
# 19. 지도용 좌표
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
# 20. 실패 목록
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
# 21. 통계
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


# ==========================================================
# 22. 실패 목록 표시
# ==========================================================
if len(missing_data) > 0:

    st.warning(
        f"⚠️ 아직 {len(missing_data)}건의 "
        "좌표를 확인하지 못했습니다."
    )

    st.subheader(
        "🔎 좌표 확인 실패 목록"
    )

    columns = [
        "문화재명(국문)",
        "소재지상세",
        "위도",
        "경도",
        "좌표보정방법"
    ]

    columns = [
        c
        for c in columns
        if c in missing_data.columns
    ]

    st.dataframe(
        missing_data[columns],
        use_container_width=True
    )

else:

    st.success(
        f"🎉 총 {len(df)}건의 "
        "모든 국가유산 좌표 확보!"
    )


# ==========================================================
# 23. 지도
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
# 24. 전체 데이터
# ==========================================================
st.subheader(
    "📋 전체 국가유산 목록"
)

st.dataframe(
    df,
    use_container_width=True
)
