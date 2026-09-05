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
    page_title="영천 국가유산 좌표 보완",
    layout="wide"
)

st.title("📍 영천 국가유산 좌표 보완")


# ==========================================================
# 2. 카카오 REST API KEY
# ==========================================================

# .streamlit/secrets.toml
#
# KAKAO_API_KEY = "1020a7ea45a4af35228dbb6933477869"

KAKAO_API_KEY = st.secrets.get(
    "KAKAO_API_KEY",
    ""
)

HEADERS = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}


# ==========================================================
# 3. 데이터 파일
# ==========================================================

FILE_PATH = "pages/영천_국가유산_상세.csv"

if not os.path.exists(FILE_PATH):

    FILE_PATH = "영천_국가유산_상세.csv"


# ==========================================================
# 4. 수동 좌표
# ==========================================================
#
# 3단계 수동 검증에서 최종적으로 확인된 좌표를
# 여기에 추가할 수 있음
#
# 형식:
#
# "문화재명": (위도, 경도)
#
# ==========================================================

MANUAL_COORDS = {

    # 예시
    # "임고서원 은행나무": (
    #     35.9907,
    #     128.9475
    # ),

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

    # 대한민국 범위
    return (
        33 <= lat <= 39
        and
        124 <= lon <= 132
    )


# ==========================================================
# 6. 카카오 API 공통 요청
# ==========================================================

def kakao_request(endpoint, query):

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
# 7. 카카오 키워드 검색
# ==========================================================
#
# [1단계]
# 국가유산명 그대로 검색
#
# ==========================================================

def search_by_name(name):

    documents = kakao_request(
        "keyword",
        name
    )

    if not documents:
        return None, None


    # ------------------------------------------------------
    # 영천 지역 결과 우선
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

            except:

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

    except:

        pass


    return None, None


# ==========================================================
# 8. 명칭 정제
# ==========================================================
#
# [2단계]
# 카카오에서 검색이 안 될 경우
# 문화재명을 검색하기 쉬운 형태로 정제
#
# ==========================================================

def refine_name(name):

    if pd.isna(name):
        return ""

    name = str(name).strip()


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
# 9. 주소 정제
# ==========================================================
#
# [2단계]
# 지번 / 도로명 주소 기반 검색을 위한 주소 정제
#
# ==========================================================

def clean_address(address):

    if pd.isna(address):
        return ""

    address = str(address).strip()


    # 괄호 제거
    address = re.sub(
        r"\(.*?\)",
        "",
        address
    )


    # 검색 방해 단어 제거
    for word in [

        "외",
        "일원",
        "필지",
        "번지"

    ]:

        address = address.replace(
            word,
            ""
        )


    return " ".join(
        address.split()
    ).strip()


# ==========================================================
# 10. 카카오 주소 검색
# ==========================================================
#
# [2단계]
# 지번 / 도로명 주소를 이용한 검색
#
# ==========================================================

def search_by_address(address):

    documents = kakao_request(
        "address",
        address
    )

    if not documents:
        return None, None


    for doc in documents:

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

        except:

            continue


    return None, None


# ==========================================================
# 11. 문화재 하나의 좌표 검색
# ==========================================================
#
# 프로젝트 계획
#
# 1단계
# 국가유산명 기반 자동검색
#
# 2단계
# 명칭 정제 + 주소 기반 재검색
#
# 3단계
# 수동 좌표 보완
#
# ==========================================================

def find_coordinate(
    name,
    address
):


    # ======================================================
    # 1단계
    # 국가유산명 기반 검색
    # ======================================================

    lat, lon = search_by_name(
        name
    )

    if lat is not None:

        return (
            lat,
            lon,
            "1단계 - 국가유산명 검색"
        )


    # ======================================================
    # 2단계
    # 명칭 정제 후 검색
    # ======================================================

    refined_name = refine_name(
        name
    )


    if (
        refined_name
        and
        refined_name != name
    ):

        lat, lon = search_by_name(
            refined_name
        )

        if lat is not None:

            return (
                lat,
                lon,
                "2단계 - 명칭 정제 검색"
            )


    # ======================================================
    # 2단계
    # 영천 + 정제명 검색
    # ======================================================

    if refined_name:

        lat, lon = search_by_name(
            f"영천 {refined_name}"
        )

        if lat is not None:

            return (
                lat,
                lon,
                "2단계 - 영천 + 정제명 검색"
            )


    # ======================================================
    # 2단계
    # 지번 / 도로명 주소 검색
    # ======================================================

    cleaned_address = clean_address(
        address
    )


    if cleaned_address:

        lat, lon = search_by_address(
            cleaned_address
        )

        if lat is not None:

            return (
                lat,
                lon,
                "2단계 - 지번/도로명 주소 검색"
            )


    # ======================================================
    # 3단계
    # 자동 검색 실패
    #
    # 여기서는 좌표를 억지로 만들지 않음
    #
    # → 수동 검증 대상으로 넘김
    # ======================================================

    return (
        None,
        None,
        "3단계 - 수동 좌표 보완 필요"
    )


# ==========================================================
# 12. 데이터 불러오기
# ==========================================================

@st.cache_data
def load_data():

    if not os.path.exists(
        FILE_PATH
    ):

        return None


    df = pd.read_csv(
        FILE_PATH,
        encoding="utf-8-sig"
    )


    # ------------------------------------------------------
    # 필요한 컬럼 확인
    # ------------------------------------------------------

    if "문화재명(국문)" not in df.columns:

        return None


    if "소재지상세" not in df.columns:

        df["소재지상세"] = ""


    if "위도" not in df.columns:

        df["위도"] = None


    if "경도" not in df.columns:

        df["경도"] = None


    # 숫자형 변환
    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )

    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )


    if "좌표보정방법" not in df.columns:

        df["좌표보정방법"] = ""


    return df


# ==========================================================
# 13. 1~2단계 자동 좌표 보완
# ==========================================================

def auto_fix_coordinates(df):

    df = df.copy()


    # 좌표가 없는 데이터만 대상
    missing_indices = []


    for i in df.index:

        if not valid_coordinate(
            df.at[i, "위도"],
            df.at[i, "경도"]
        ):

            missing_indices.append(i)


    total = len(
        missing_indices
    )


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
            f"🔍 자동 좌표 검색 "
            f"{number}/{total} : {name}"
        )


        lat, lon, method = find_coordinate(
            name,
            address
        )


        if lat is not None:

            df.at[i, "위도"] = lat

            df.at[i, "경도"] = lon

            df.at[i, "좌표보정방법"] = method

            success += 1


        else:

            df.at[i, "좌표보정방법"] = method

            fail += 1


        progress.progress(
            number / total
        )


        # API 과부하 방지
        time.sleep(0.3)


    status.empty()

    progress.empty()


    st.success(
        f"자동 좌표 검색 완료 "
        f"· 성공 {success}건 "
        f"· 수동 보완 필요 {fail}건"
    )


    return df


# ==========================================================
# 14. 데이터 로드
# ==========================================================

df = load_data()


if df is None:

    st.error(
        "❌ 국가유산 CSV 파일을 찾을 수 없습니다."
    )

    st.stop()


# ==========================================================
# 15. 현재 좌표 현황
# ==========================================================

df["좌표확보"] = df.apply(
    lambda row:
        valid_coordinate(
            row["위도"],
            row["경도"]
        ),
    axis=1
)


total_count = len(df)

coordinate_count = int(
    df["좌표확보"].sum()
)

missing_count = (
    total_count
    -
    coordinate_count
)


# ==========================================================
# 16. 통계
# ==========================================================

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "전체 국가유산",
        total_count
    )


with col2:

    st.metric(
        "좌표 확보",
        coordinate_count
    )


with col3:

    st.metric(
        "좌표 미확인",
        missing_count
    )


st.divider()


# ==========================================================
# 17. 1~2단계 자동검색 버튼
# ==========================================================

st.subheader(
    "🔍 1~2단계 자동 좌표 검색"
)

st.caption(
    "국가유산명 → 명칭 정제 → "
    "지번/도로명 주소 순서로 검색합니다."
)


if st.button(
    "🚀 1~2단계 자동 좌표 검색",
    type="primary"
):

    df = auto_fix_coordinates(
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
# 19. 3단계 수동 보완 대상
# ==========================================================

df["좌표확보"] = df.apply(
    lambda row:
        valid_coordinate(
            row["위도"],
            row["경도"]
        ),
    axis=1
)


missing_data = df[
    ~df["좌표확보"]
].copy()


# ==========================================================
# 20. 3단계 수동 검증
# ==========================================================

if len(missing_data) > 0:

    st.divider()

    st.subheader(
        "🛰️ 3단계 수동 좌표 보완"
    )

    st.info(
        "자동 검색에 실패한 국가유산입니다. "
        "위성지도 및 문헌자료를 대조하여 "
        "좌표를 직접 확인한 후 입력합니다."
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


    st.warning(
        f"⚠️ 수동 검증이 필요한 "
        f"국가유산: {len(missing_data)}건"
    )


else:

    st.success(
        "🎉 모든 국가유산의 좌표가 확보되었습니다."
    )


# ==========================================================
# 21. 지도용 데이터
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
].copy()


# ==========================================================
# 22. 지도
# ==========================================================

st.divider()

st.subheader(
    "🗺️ 영천 국가유산 위치"
)


if len(map_data) > 0:

    st.map(
        map_data[
            [
                "latitude",
                "longitude"
            ]
        ]
    )

else:

    st.info(
        "표시할 좌표가 없습니다."
    )


# ==========================================================
# 23. 전체 국가유산 목록
# ==========================================================

st.divider()

st.subheader(
    "📋 전체 국가유산 목록"
)


st.dataframe(
    df,
    use_container_width=True
)
