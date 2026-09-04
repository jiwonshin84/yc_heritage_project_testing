import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import math
import os

st.set_page_config(
    page_title="전국 국가유산 데이터",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background-color: #f5f7fa;
}
.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #1f2937;
    margin-bottom: 5px;
}
.sub-title {
    font-size: 17px;
    color: #6b7280;
    margin-bottom: 30px;
}
.card {
    background-color: white;
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 3px 12px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
.metric-card {
    background-color: white;
    padding: 22px;
    border-radius: 15px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
    text-align: center;
}
.metric-title {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #111827;
}
.section-title {
    font-size: 25px;
    font-weight: 750;
    color: #1f2937;
    margin-top: 15px;
    margin-bottom: 18px;
}
.rank-row {
    margin-bottom: 17px;
}
.rank-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    font-size: 15px;
    font-weight: 600;
    color: #374151;
}
.bar-background {
    width: 100%;
    height: 14px;
    background-color: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
}
.bar-fill {
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #4f46e5, #6366f1);
}
.search-card {
    background-color: white;
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 3px 12px rgba(0,0,0,0.05);
}
.info-box {
    background-color: #eef2ff;
    border-left: 5px solid #4f46e5;
    padding: 15px 18px;
    border-radius: 8px;
    color: #3730a3;
    margin-bottom: 20px;
}
.footer {
    text-align: center;
    color: #9ca3af;
    padding: 25px;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title">🏛️ 전국 국가유산 데이터</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">국가유산 API를 활용한 전국 국가유산 데이터 수집 및 분석</div>',
    unsafe_allow_html=True
)

BASE_URL = "https://www.khs.go.kr"
LIST_URL = BASE_URL + "/cha/SearchKindOpenapiList.do"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

def safe_request(url, params=None, retry=5):
    for i in range(retry):
        try:
            response = session.get(
                url,
                params=params,
                timeout=20
            )
            if response.status_code == 200:
                return response
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None

@st.cache_data(ttl=3600)
def collect_heritage_data():
    params = {
        "pageUnit": "300",
        "pageIndex": "1",
        "ccbaCncl": "N"
    }

    response = safe_request(
        LIST_URL,
        params
    )

    if response is None:
        return pd.DataFrame()

    try:
        root = ET.fromstring(
            response.content
        )
    except ET.ParseError:
        return pd.DataFrame()

    total_text = root.findtext("totalCnt")
    page_unit_text = root.findtext("pageUnit")

    if not total_text:
        return pd.DataFrame()

    total_cnt = int(total_text)

    page_unit = (
        int(page_unit_text)
        if page_unit_text
        else 300
    )

    total_pages = math.ceil(
        total_cnt / page_unit
    )

    all_data = []

    progress = st.progress(0)
    status_text = st.empty()

    for page in range(
        1,
        total_pages + 1
    ):
        params["pageIndex"] = str(page)

        response = safe_request(
            LIST_URL,
            params
        )

        if response is None:
            continue

        try:
            root = ET.fromstring(
                response.content
            )
        except ET.ParseError:
            continue

        items = list(
            root.iter("item")
        )

        for item in items:
            all_data.append({
                "국가유산종목": item.findtext("ccmaName"),
                "문화재명(국문)": item.findtext("ccbaMnm1"),
                "문화재명(한자)": item.findtext("ccbaMnm2"),
                "시도명": item.findtext("ccbaCtcdNm"),
                "시군구명": item.findtext("ccsiName"),
                "관리자": item.findtext("ccbaAdmin"),
                "종목코드": item.findtext("ccbaKdcd"),
                "시도코드": item.findtext("ccbaCtcd"),
                "관리번호": item.findtext("ccbaAsno"),
                "경도": item.findtext("longitude"),
                "위도": item.findtext("latitude")
            })

        progress.progress(
            page / total_pages
        )

        status_text.info(
            f"데이터 수집 중... {page} / {total_pages} 페이지"
        )

        time.sleep(0.3)

    progress.empty()
    status_text.empty()

    return pd.DataFrame(
        all_data
    )

DATA_PATH = os.path.join(
    "data",
    "국가유산_전체데이터.csv"
)

if os.path.exists(DATA_PATH):
    try:
        df = pd.read_csv(
            DATA_PATH,
            encoding="utf-8-sig"
        )

        st.success(
            "GitHub에 저장된 국가유산 데이터를 불러왔습니다."
        )

    except Exception as e:
        st.error(
            f"CSV 파일을 읽을 수 없습니다.\n\n{e}"
        )
        df = pd.DataFrame()

else:
    df = pd.DataFrame()

if "df" not in st.session_state:
    st.session_state.df = df

st.sidebar.title("🏛️ 메뉴")

menu = st.sidebar.radio(
    "페이지 선택",
    [
        "📊 데이터 현황",
        "📋 국가유산 목록",
        "🔎 국가유산 검색",
        "📥 데이터 수집"
    ]
)

if menu == "📥 데이터 수집":

    st.markdown(
        '<div class="section-title">📥 국가유산 데이터 수집</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card">'
        '<b>국가유산 API</b><br>'
        '국가유산 API를 이용하여 전국 데이터를 새롭게 수집할 수 있습니다.'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🌐 API에서 데이터 가져오기",
        use_container_width=True
    ):

        with st.spinner(
            "전국 국가유산 데이터를 수집하고 있습니다..."
        ):

            new_df = collect_heritage_data()

        if not new_df.empty:

            st.session_state.df = new_df

            csv_data = new_df.to_csv(
                index=False,
                encoding="utf-8-sig"
            )

            st.success(
                f"총 {len(new_df):,}건의 데이터를 수집했습니다."
            )

            st.download_button(
                "⬇️ CSV 다운로드",
                data=csv_data,
                file_name="국가유산_전체데이터.csv",
                mime="text/csv",
                use_container_width=True
            )

        else:
            st.error(
                "데이터를 가져오지 못했습니다."
            )

    st.stop()

df = st.session_state.df

if df.empty:

    st.warning(
        "데이터가 없습니다. 먼저 데이터를 수집해주세요."
    )

    st.stop()

text_columns = [
    "국가유산종목",
    "문화재명(국문)",
    "문화재명(한자)",
    "시도명",
    "시군구명",
    "관리자",
    "종목코드",
    "시도코드",
    "관리번호"
]

for col in text_columns:
    if col in df.columns:
        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

if "위도" in df.columns:
    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )

if "경도" in df.columns:
    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )

if menu == "📊 데이터 현황":

    st.markdown(
        '<div class="section-title">📊 전국 국가유산 현황</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="info-box">'
        '전국에 등록된 국가유산의 기본적인 현황을 확인할 수 있습니다.'
        '</div>',
        unsafe_allow_html=True
    )

    total_count = len(df)

    category_count = (
        df["국가유산종목"]
        .replace("", pd.NA)
        .nunique()
    )

    sido_count = (
        df["시도명"]
        .replace("", pd.NA)
        .nunique()
    )

    sigungu_count = (
        df["시군구명"]
        .replace("", pd.NA)
        .nunique()
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">전체 국가유산</div>
                <div class="metric-value">{total_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">국가유산 종목</div>
                <div class="metric-value">{category_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">시도</div>
                <div class="metric-value">{sido_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">시군구</div>
                <div class="metric-value">{sigungu_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    st.markdown(
        '<div class="section-title">🏆 국가유산 종목별 현황</div>',
        unsafe_allow_html=True
    )

    nation_count = (
        df["국가유산종목"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    max_value = nation_count.max()

    top_count = min(
        len(nation_count),
        15
    )

    for name, value in nation_count.head(
        top_count
    ).items():

        percentage = (
            value / max_value * 100
        )

        st.markdown(
            f"""
            <div class="rank-row">
                <div class="rank-header">
                    <span>{name}</span>
                    <span>{value:,}건</span>
                </div>
                <div class="bar-background">
                    <div class="bar-fill"
                         style="width:{percentage}%;">
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.caption(
        f"※ 상위 {top_count}개 종목을 표시했습니다."
    )

    st.write("")

    st.markdown(
        '<div class="section-title">🗺️ 시도별 국가유산 현황</div>',
        unsafe_allow_html=True
    )

    sido_count_data = (
        df["시도명"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    max_sido = sido_count_data.max()

    for name, value in sido_count_data.items():

        percentage = (
            value / max_sido * 100
        )

        st.markdown(
            f"""
            <div class="rank-row">
                <div class="rank-header">
                    <span>{name}</span>
                    <span>{value:,}건</span>
                </div>
                <div class="bar-background">
                    <div class="bar-fill"
                         style="width:{percentage}%;">
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

elif menu == "📋 국가유산 목록":

    st.markdown(
        '<div class="section-title">📋 국가유산 목록</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card">'
        '전국 국가유산 데이터를 표 형태로 확인할 수 있습니다.'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        selected_sido = st.selectbox(
            "시도 선택",
            ["전체"] +
            sorted(
                df["시도명"]
                .replace("", pd.NA)
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col2:
        selected_type = st.selectbox(
            "국가유산 종목",
            ["전체"] +
            sorted(
                df["국가유산종목"]
                .replace("", pd.NA)
                .dropna()
                .unique()
                .tolist()
            )
        )

    filtered_df = df.copy()

    if selected_sido != "전체":
        filtered_df = filtered_df[
            filtered_df["시도명"] == selected_sido
        ]

    if selected_type != "전체":
        filtered_df = filtered_df[
            filtered_df["국가유산종목"] == selected_type
        ]

    st.write(
        f"검색된 데이터: **{len(filtered_df):,}건**"
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=550
    )

elif menu == "🔎 국가유산 검색":

    st.markdown(
        '<div class="section-title">🔎 국가유산 검색</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="search-card">'
        '<b>문화재 이름 검색</b><br>'
        '<span style="color:#6b7280;">'
        '찾고 싶은 국가유산의 이름을 입력하세요.'
        '</span>'
        '</div>',
        unsafe_allow_html=True
    )

    search_word = st.text_input(
        "문화재 이름",
        placeholder="예: 은해사, 불국사, 석굴암"
    )

    if search_word:

        search_result = df[
            df["문화재명(국문)"]
            .str.contains(
                search_word,
                case=False,
                na=False
            )
        ]

        st.write(
            f"검색 결과 **{len(search_result):,}건**"
        )

        if not search_result.empty:

            for _, row in search_result.head(
                20
            ).iterrows():

                name = row.get(
                    "문화재명(국문)",
                    ""
                )

                heritage_type = row.get(
                    "국가유산종목",
                    ""
                )

                sido = row.get(
                    "시도명",
                    ""
                )

                sigungu = row.get(
                    "시군구명",
                    ""
                )

                st.markdown(
                    f"""
                    <div class="card">
                        <div style="
                            font-size:20px;
                            font-weight:700;
                            color:#111827;
                            margin-bottom:8px;">
                            🏛️ {name}
                        </div>
                        <div style="
                            color:#6b7280;
                            line-height:1.8;">
                            <b>종목:</b> {heritage_type}<br>
                            <b>지역:</b> {sido} {sigungu}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.warning(
                "검색 결과가 없습니다."
            )

else:

    st.error(
        "잘못된 메뉴입니다."
    )

st.markdown(
    '<div class="footer">'
    '국가유산 API 기반 데이터 수집 및 분석 서비스'
    '</div>',
    unsafe_allow_html=True
)
