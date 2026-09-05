```python
import os
import re
import time
import pandas as pd
import requests
import streamlit as st


# =========================================================
# 0. 기본 설정
# =========================================================

st.set_page_config(
    page_title="영천 국가유산 좌표 보완",
    page_icon="📍",
    layout="wide"
)

st.title("📍 영천 국가유산 좌표 자동 보완")
st.caption(
    "1단계 국가유산명 검색 → "
    "2단계 명칭·주소 재검색 → "
    "3단계 다중 후보 자동 탐색"
)


# =========================================================
# 1. Kakao API 설정
# =========================================================

KAKAO_API_KEY = st.secrets.get("KAKAO_API_KEY", "")

HEADERS = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}

KAKAO_KEYWORD_URL = (
    "https://dapi.kakao.com/v2/local/search/keyword.json"
)

KAKAO_ADDRESS_URL = (
    "https://dapi.kakao.com/v2/local/search/address.json"
)


# =========================================================
# 2. CSV 파일 경로
# =========================================================

FILE_PATH = "pages/영천_국가유산_상세.csv"

if not os.path.exists(FILE_PATH):
    FILE_PATH = "영천_국가유산_상세.csv"


# =========================================================
# 3. 좌표 유효성 검사
# =========================================================

def valid_coordinate(lat, lon):

    try:
        lat = float(lat)
        lon = float(lon)

        if 33 <= lat <= 39 and 124 <= lon <= 132:
            return True

    except:
        pass

    return False


# =========================================================
# 4. 텍스트 정리
# =========================================================

def normalize_text(text):

    if pd.isna(text):
        return ""

    text = str(text)

    text = re.sub(r"\([^)]*\)", "", text)

    text = re.sub(r"[,·ㆍ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# 5. 국가유산명 정제
# =========================================================

def refine_name(name):

    name = normalize_text(name)

    if not name:
        return ""

    remove_words = [
        "탱화",
        "유물",
        "일괄",
        "및",
        "구 "
    ]

    refined = name

    for word in remove_words:
        refined = refined.replace(word, " ")

    refined = re.sub(r"\s+", " ", refined)

    return refined.strip()


# =========================================================
# 6. 주소 정리
# =========================================================

def clean_address(address):

    address = normalize_text(address)

    if not address:
        return ""

    remove_words = [
        "외",
        "일원",
        "필지",
        "번지"
    ]

    for word in remove_words:
        address = address.replace(word, " ")

    address = re.sub(r"\s+", " ", address)

    return address.strip()


# =========================================================
# 7. Kakao 키워드 검색
# =========================================================

def kakao_keyword_search(query):

    if not query:
        return []

    try:

        response = requests.get(
            KAKAO_KEYWORD_URL,
            headers=HEADERS,
            params={
                "query": query,
                "size": 15
            },
            timeout=10
        )

        if response.status_code != 200:
            return []

        return response.json().get(
            "documents",
            []
        )

    except:

        return []


# =========================================================
# 8. Kakao 주소 검색
# =========================================================

def kakao_address_search(query):

    if not query:
        return []

    try:

        response = requests.get(
            KAKAO_ADDRESS_URL,
            headers=HEADERS,
            params={
                "query": query,
                "size": 15
            },
            timeout=10
        )

        if response.status_code != 200:
            return []

        return response.json().get(
            "documents",
            []
        )

    except:

        return []


# =========================================================
# 9. 검색 결과에서 좌표 후보 추출
# =========================================================

def document_to_candidate(doc):

    try:

        lat = float(doc.get("y"))
        lon = float(doc.get("x"))

    except:

        return None

    if not valid_coordinate(lat, lon):
        return None

    return {
        "lat": lat,
        "lon": lon,
        "place_name": doc.get(
            "place_name",
            ""
        ),
        "address_name": doc.get(
            "address_name",
            ""
        ),
        "road_address_name": doc.get(
            "road_address_name",
            ""
        ),
        "category_name": doc.get(
            "category_name",
            ""
        )
    }


# =========================================================
# 10. 문자열 유사도
# =========================================================

def text_similarity(target, candidate):

    target = normalize_text(
        target
    ).lower()

    candidate = normalize_text(
        candidate
    ).lower()

    if not target or not candidate:
        return 0

    if target == candidate:
        return 100

    if target in candidate:
        return 80

    if candidate in target:
        return 70

    target_words = set(
        target.split()
    )

    candidate_words = set(
        candidate.split()
    )

    if not target_words:
        return 0

    overlap = len(
        target_words & candidate_words
    )

    return min(
        60,
        int(
            overlap
            / len(target_words)
            * 60
        )
    )


# =========================================================
# 11. 후보 점수 계산
# =========================================================

def calculate_score(
    heritage_name,
    heritage_address,
    candidate
):

    score = 0

    refined_name = refine_name(
        heritage_name
    )

    address = clean_address(
        heritage_address
    )

    place_name = candidate[
        "place_name"
    ]

    address_name = candidate[
        "address_name"
    ]

    road_address = candidate[
        "road_address_name"
    ]

    category_name = candidate[
        "category_name"
    ]

    # 영천 포함 여부
    all_text = (
        place_name
        + " "
        + address_name
        + " "
        + road_address
        + " "
        + category_name
    )

    if "영천" in all_text:
        score += 40

    # 국가유산명과 장소명 비교
    name_score = text_similarity(
        refined_name,
        place_name
    )

    score += int(
        name_score * 0.35
    )

    # 주소 비교
    address_score = text_similarity(
        address,
        address_name
    )

    score += int(
        address_score * 0.20
    )

    # 도로명 주소 비교
    road_score = text_similarity(
        address,
        road_address
    )

    score += int(
        road_score * 0.15
    )

    # 핵심 단어가 검색 결과에 있는지 확인
    if refined_name:

        name_words = [
            word
            for word in refined_name.split()
            if len(word) >= 2
        ]

        for word in name_words:

            if word in all_text:
                score += 5

    return score


# =========================================================
# 12. 가장 높은 점수의 후보 선택
# =========================================================

def choose_best_candidate(
    heritage_name,
    heritage_address,
    candidates
):

    if not candidates:
        return None

    scored = []

    for candidate in candidates:

        score = calculate_score(
            heritage_name,
            heritage_address,
            candidate
        )

        candidate_copy = candidate.copy()

        candidate_copy["score"] = score

        scored.append(
            candidate_copy
        )

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return scored[0]


# =========================================================
# 13. 1단계
# 국가유산명 그대로 검색
# =========================================================

def stage1_search(name):

    if not name:
        return None

    docs = kakao_keyword_search(
        name
    )

    candidates = []

    for doc in docs:

        candidate = document_to_candidate(
            doc
        )

        if candidate:
            candidates.append(
                candidate
            )

    if not candidates:
        return None

    # 영천 결과 우선
    yeongcheon_candidates = [
        c
        for c in candidates
        if "영천" in (
            c["place_name"]
            + c["address_name"]
            + c["road_address_name"]
        )
    ]

    if yeongcheon_candidates:
        candidates = (
            yeongcheon_candidates
        )

    best = choose_best_candidate(
        name,
        "",
        candidates
    )

    if best:

        return {
            "lat": best["lat"],
            "lon": best["lon"],
            "method": (
                "1단계 - 국가유산명 검색"
            ),
            "score": best["score"],
            "place_name": best[
                "place_name"
            ]
        }

    return None


# =========================================================
# 14. 2단계
# 명칭 정제 + 주소 검색
# =========================================================

def stage2_search(
    name,
    address
):

    refined_name = refine_name(
        name
    )

    cleaned_address = clean_address(
        address
    )

    candidates = []

    # -----------------------------------------
    # 정제된 국가유산명
    # -----------------------------------------

    if refined_name:

        docs = kakao_keyword_search(
            refined_name
        )

        for doc in docs:

            candidate = document_to_candidate(
                doc
            )

            if candidate:
                candidates.append(
                    candidate
                )

    # -----------------------------------------
    # 영천 + 정제된 이름
    # -----------------------------------------

    if refined_name:

        docs = kakao_keyword_search(
            f"영천 {refined_name}"
        )

        for doc in docs:

            candidate = document_to_candidate(
                doc
            )

            if candidate:
                candidates.append(
                    candidate
                )

    # -----------------------------------------
    # 주소 검색
    # -----------------------------------------

    if cleaned_address:

        docs = kakao_address_search(
            cleaned_address
        )

        for doc in docs:

            candidate = document_to_candidate(
                doc
            )

            if candidate:
                candidates.append(
                    candidate
                )

    # 중복 제거
    unique = {}

    for candidate in candidates:

        key = (
            round(
                candidate["lat"],
                6
            ),
            round(
                candidate["lon"],
                6
            )
        )

        unique[key] = candidate

    candidates = list(
        unique.values()
    )

    if not candidates:
        return None

    best = choose_best_candidate(
        name,
        address,
        candidates
    )

    if best:

        return {
            "lat": best["lat"],
            "lon": best["lon"],
            "method": (
                "2단계 - 명칭 정제 + 주소 검색"
            ),
            "score": best["score"],
            "place_name": best[
                "place_name"
            ]
        }

    return None


# =========================================================
# 15. 3단계
# 다중 검색 자동 보완
# =========================================================

def stage3_search(
    name,
    address
):

    refined_name = refine_name(
        name
    )

    cleaned_address = clean_address(
        address
    )

    candidates = []

    # -----------------------------------------
    # 여러 검색어 자동 생성
    # -----------------------------------------

    queries = []

    if name:
        queries.append(name)

    if refined_name:

        queries.append(
            refined_name
        )

        queries.append(
            f"영천 {refined_name}"
        )

    if cleaned_address:

        queries.append(
            cleaned_address
        )

        queries.append(
            f"영천 {cleaned_address}"
        )

    # -----------------------------------------
    # 핵심 단어 추출
    # -----------------------------------------

    if refined_name:

        words = [
            word
            for word in refined_name.split()
            if len(word) >= 2
        ]

        if len(words) >= 2:

            queries.append(
                " ".join(words[:2])
            )

            queries.append(
                f"영천 {' '.join(words[:2])}"
            )

        if words:

            queries.append(
                words[0]
            )

            queries.append(
                f"영천 {words[0]}"
            )

    # 중복 검색어 제거
    queries = list(
        dict.fromkeys(
            [
                q.strip()
                for q in queries
                if q and q.strip()
            ]
        )
    )

    # -----------------------------------------
    # 모든 검색어 검색
    # -----------------------------------------

    for query in queries:

        docs = kakao_keyword_search(
            query
        )

        for doc in docs:

            candidate = document_to_candidate(
                doc
            )

            if candidate:
                candidates.append(
                    candidate
                )

        time.sleep(0.15)

    # -----------------------------------------
    # 주소 API 추가 검색
    # -----------------------------------------

    if cleaned_address:

        docs = kakao_address_search(
            cleaned_address
        )

        for doc in docs:

            candidate = document_to_candidate(
                doc
            )

            if candidate:
                candidates.append(
                    candidate
                )

    # -----------------------------------------
    # 좌표 중복 제거
    # -----------------------------------------

    unique = {}

    for candidate in candidates:

        key = (
            round(
                candidate["lat"],
                6
            ),
            round(
                candidate["lon"],
                6
            )
        )

        unique[key] = candidate

    candidates = list(
        unique.values()
    )

    if not candidates:
        return None

    # -----------------------------------------
    # 점수 계산
    # -----------------------------------------

    scored = []

    for candidate in candidates:

        score = calculate_score(
            name,
            address,
            candidate
        )

        candidate_copy = candidate.copy()

        candidate_copy["score"] = score

        scored.append(
            candidate_copy
        )

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best = scored[0]

    # 40점 이상만 자동 채택
    if best["score"] < 40:
        return None

    return {
        "lat": best["lat"],
        "lon": best["lon"],
        "method": (
            "3단계 - 다중 검색 자동 보완"
        ),
        "score": best["score"],
        "place_name": best[
            "place_name"
        ]
    }


# =========================================================
# 16. 최종 좌표 찾기
# =========================================================

def find_coordinate(
    name,
    address
):

    # 1단계
    result = stage1_search(
        name
    )

    if result:
        return result

    # 2단계
    result = stage2_search(
        name,
        address
    )

    if result:
        return result

    # 3단계
    result = stage3_search(
        name,
        address
    )

    if result:
        return result

    # 최종 실패
    return {
        "lat": None,
        "lon": None,
        "method": "수동 검증 필요",
        "score": 0,
        "place_name": ""
    }


# =========================================================
# 17. CSV 불러오기
# =========================================================

@st.cache_data
def load_data():

    if not os.path.exists(
        FILE_PATH
    ):

        st.error(
            f"CSV 파일을 찾을 수 없습니다: "
            f"{FILE_PATH}"
        )

        return pd.DataFrame()

    df = pd.read_csv(
        FILE_PATH,
        encoding="utf-8-sig"
    )

    # 필수 컬럼
    if "문화재명(국문)" not in df.columns:

        st.error(
            "'문화재명(국문)' 컬럼이 없습니다."
        )

        return pd.DataFrame()

    if "소재지상세" not in df.columns:
        df["소재지상세"] = ""

    if "위도" not in df.columns:
        df["위도"] = None

    if "경도" not in df.columns:
        df["경도"] = None

    if "좌표보정방법" not in df.columns:
        df["좌표보정방법"] = ""

    if "3단계신뢰도" not in df.columns:
        df["3단계신뢰도"] = None

    if "검색결과명" not in df.columns:
        df["검색결과명"] = ""

    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )

    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )

    return df


# =========================================================
# 18. 1~3단계 자동 좌표 보완
# =========================================================

def auto_fix_coordinates(df):

    df = df.copy()

    total = len(df)

    progress = st.progress(0)

    status = st.empty()

    success_count = 0

    for i, row in df.iterrows():

        name = row.get(
            "문화재명(국문)",
            ""
        )

        address = row.get(
            "소재지상세",
            ""
        )

        # 이미 좌표가 있으면 건너뜀
        if valid_coordinate(
            row.get("위도"),
            row.get("경도")
        ):

            if not row.get(
                "좌표보정방법"
            ):

                df.at[
                    i,
                    "좌표보정방법"
                ] = "기존 좌표 유지"

            continue

        status.write(
            f"🔎 {i + 1}/{total} : {name}"
        )

        result = find_coordinate(
            name,
            address
        )

        if result["lat"] is not None:

            df.at[
                i,
                "위도"
            ] = result["lat"]

            df.at[
                i,
                "경도"
            ] = result["lon"]

            df.at[
                i,
                "좌표보정방법"
            ] = result["method"]

            df.at[
                i,
                "3단계신뢰도"
            ] = result["score"]

            df.at[
                i,
                "검색결과명"
            ] = result["place_name"]

            success_count += 1

        else:

            df.at[
                i,
                "좌표보정방법"
            ] = "수동 검증 필요"

        progress.progress(
            int(
                ((i + 1) / total)
                * 100
            )
        )

        time.sleep(0.3)

    status.success(
        f"자동 좌표 보완 완료: "
        f"{success_count}건 처리"
    )

    return df


# =========================================================
# 19. 데이터 불러오기
# =========================================================

df = load_data()

if df.empty:
    st.stop()


# =========================================================
# 20. 현재 좌표 상태
# =========================================================

total_count = len(df)

coordinate_count = sum(
    valid_coordinate(
        lat,
        lon
    )
    for lat, lon in zip(
        df["위도"],
        df["경도"]
    )
)

missing_count = (
    total_count
    - coordinate_count
)


# =========================================================
# 21. 통계
# =========================================================

col1, col2, col3 = st.columns(3)

col1.metric(
    "전체 국가유산",
    f"{total_count}건"
)

col2.metric(
    "좌표 확보",
    f"{coordinate_count}건"
)

col3.metric(
    "좌표 미확보",
    f"{missing_count}건"
)

st.divider()


# =========================================================
# 22. 자동 좌표 보완 버튼
# =========================================================

if st.button(
    "🚀 1~3단계 자동 좌표 보완 시작",
    type="primary",
    use_container_width=True
):

    if not KAKAO_API_KEY:

        st.error(
            "KAKAO_API_KEY가 설정되어 있지 않습니다."
        )

        st.stop()

    with st.spinner(
        "1~3단계 좌표 자동 검색 중입니다..."
    ):

        fixed_df = auto_fix_coordinates(
            df
        )

    st.session_state[
        "fixed_df"
    ] = fixed_df

    st.cache_data.clear()

    st.rerun()


# =========================================================
# 23. 자동 처리 결과
# =========================================================

if "fixed_df" in st.session_state:

    df = st.session_state[
        "fixed_df"
    ]


# =========================================================
# 24. 처리 결과 통계
# =========================================================

st.subheader(
    "📊 좌표 보완 결과"
)

method_counts = (
    df["좌표보정방법"]
    .fillna("")
    .value_counts()
)

for method, count in method_counts.items():

    if method:

        st.write(
            f"**{method}** : {count}건"
        )


# =========================================================
# 25. 3단계 자동 보완 결과
# =========================================================

st.divider()

st.subheader(
    "🤖 3단계 자동 좌표 보완 결과"
)

stage3_df = df[
    df["좌표보정방법"]
    == "3단계 - 다중 검색 자동 보완"
].copy()

if not stage3_df.empty:

    st.success(
        f"3단계에서 자동으로 좌표를 확보한 "
        f"{len(stage3_df)}건이 있습니다."
    )

    display_columns = [
        "문화재명(국문)",
        "소재지상세",
        "위도",
        "경도",
        "3단계신뢰도",
        "검색결과명"
    ]

    display_columns = [
        col
        for col in display_columns
        if col in stage3_df.columns
    ]

    st.dataframe(
        stage3_df[
            display_columns
        ],
        use_container_width=True
    )

else:

    st.info(
        "3단계 자동 보완으로 새롭게 "
        "확보된 좌표가 없습니다."
    )


# =========================================================
# 26. 최종 수동 검증 대상
# =========================================================

st.divider()

st.subheader(
    "⚠️ 최종 수동 검증이 필요한 국가유산"
)

manual_df = df[
    df["좌표보정방법"]
    == "수동 검증 필요"
].copy()

if not manual_df.empty:

    st.warning(
        f"자동 검색으로 좌표를 확정하지 못한 "
        f"{len(manual_df)}건입니다."
    )

    display_columns = [
        "문화재명(국문)",
        "소재지상세",
        "위도",
        "경도",
        "좌표보정방법"
    ]

    display_columns = [
        col
        for col in display_columns
        if col in manual_df.columns
    ]

    st.dataframe(
        manual_df[
            display_columns
        ],
        use_container_width=True
    )

else:

    st.success(
        "🎉 모든 국가유산의 좌표가 "
        "자동으로 확보되었습니다!"
    )


# =========================================================
# 27. 지도
# =========================================================

st.divider()

st.subheader(
    "🗺️ 좌표 확보 국가유산 지도"
)

map_df = df[
    df.apply(
        lambda row: valid_coordinate(
            row["위도"],
            row["경도"]
        ),
        axis=1
    )
].copy()

if not map_df.empty:

    map_data = map_df[
        ["위도", "경도"]
    ].rename(
        columns={
            "위도": "latitude",
            "경도": "longitude"
        }
    )

    st.map(
        map_data
    )

else:

    st.info(
        "표시할 좌표가 없습니다."
    )


# =========================================================
# 28. 최종 데이터
# =========================================================

st.divider()

st.subheader(
    "📋 최종 데이터"
)

st.dataframe(
    df,
    use_container_width=True,
    height=500
)


# =========================================================
# 29. CSV 다운로드
# =========================================================

st.divider()

st.subheader(
    "💾 최종 좌표 데이터 저장"
)

csv_data = df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="⬇️ 최종 좌표 CSV 다운로드",
    data=csv_data,
    file_name=(
        "영천_국가유산_좌표보완_최종.csv"
    ),
    mime="text/csv",
    use_container_width=True
)
```
