import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import math

st.set_page_config(
    page_title="국가유산 데이터 수집",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #f5f7fa;
}
.header {
    background: white;
    padding: 30px;
    border-radius: 18px;
    margin-bottom: 25px;
    border: 1px solid #e5e7eb;
}
.title {
    font-size: 36px;
    font-weight: 800;
    color: #111827;
}
.subtitle {
    font-size: 16px;
    color: #6b7280;
    margin-top: 8px;
}
.card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #e5e7eb;
    margin-bottom: 20px;
}
.metric {
    background: white;
    padding: 25px 15px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    text-align: center;
}
.metric-title {
    color: #6b7280;
    font-size: 14px;
}
.metric-value {
    color: #111827;
    font-size: 28px;
    font-weight: 800;
    margin-top: 5px;
}
.rank {
    background: white;
    padding: 15px 18px;
    border-radius: 12px;
    margin-bottom: 10px;
    border: 1px solid #e5e7eb;
}
.rank-top {
    display: flex;
    justify-content: space-between;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 8px;
}
.bar-bg {
    width: 100%;
    height: 12px;
    background: #e5e7eb;
    border-radius: 10px;
}
.bar {
    height: 12px;
    background: #4f46e5;
    border-radius: 10px;
}
.footer {
    text-align: center;
    color: #9ca3af;
    padding: 30px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <div class="title">🏛️ 국가유산 데이터 수집</div>
    <div class="subtitle">
        국가유산 API를 이용하여 전국 국가유산 데이터를 수집하고 다운로드할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

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

    if page_unit_text:
        page_unit = int(page_unit_text)
    else:
        page_unit = 300

    total_pages = math.ceil(
        total_cnt / page_unit
    )

    all_data = []

    progress = st.progress(0)
    status = st.empty()

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

        status.info(
            f"전국 국가유산 데이터 수집 중... "
            f"{page} / {total_pages} 페이지"
        )

        time.sleep(0.3)

    progress.empty()
    status.empty()

    return pd.DataFrame(
        all_data
    )

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

st.markdown("""
<div class="card">
<h3>📥 전국 국가유산 데이터 수집</h3>
<p>
아래 버튼을 누르면 국가유산 API에서 전국 데이터를 직접 가져옵니다.
</p>
</div>
""", unsafe_allow_html=True)

if st.button(
    "🌐 전국 국가유산 데이터 수집 시작",
    use_container_width=True
):
    with st.spinner(
        "전국 국가유산 데이터를 수집하고 있습니다..."
    ):
        df = collect_heritage_data()

    if not df.empty:
        st.session_state.df = df

        st.success(
            f"데이터 수집 완료! 총 {len(df):,}건"
        )

    else:
        st.error(
            "데이터를 가져오지 못했습니다. API 상태를 확인해주세요."
        )

df = st.session_state.df

if not df.empty:

    st.markdown(
        '<div class="section-title">📊 수집 데이터 현황</div>',
        unsafe_allow_html=True
    )

    total_count = len(df)

    type_count = (
        df["국가유산종목"]
        .fillna("")
        .replace("", pd.NA)
        .nunique()
    )

    sido_count = (
        df["시도명"]
        .fillna("")
        .replace("", pd.NA)
        .nunique()
    )

    sigungu_count = (
        df["시군구명"]
        .fillna("")
        .replace("", pd.NA)
        .nunique()
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-title">전체 국가유산</div>
                <div class="metric-value">{total_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-title">국가유산 종목</div>
                <div class="metric-value">{type_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-title">시도</div>
                <div class="metric-value">{sido_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-title">시군구</div>
                <div class="metric-value">{sigungu_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    st.markdown("""
    <div class="card">
        <h3>💾 데이터 다운로드</h3>
        <p>
        API에서 수집한 전국 국가유산 데이터를 CSV 파일로 저장할 수 있습니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    csv_data = df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="⬇️ 국가유산 전체 데이터 CSV 다운로드",
        data=csv_data,
        file_name="국가유산_전체데이터.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.markdown("""
    <div class="card">
        <h3>🏆 국가유산 종목별 현황</h3>
    </div>
    """, unsafe_allow_html=True)

    nation_count = (
        df["국가유산종목"]
        .fillna("")
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    max_value = nation_count.max()

    for name, value in nation_count.items():

        percentage = (
            value / max_value * 100
        )

        st.markdown(
            f"""
            <div class="rank">
                <div class="rank-top">
                    <span>{name}</span>
                    <span>{value:,}건</span>
                </div>
                <div class="bar-bg">
                    <div class="bar"
                         style="width:{percentage}%;">
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="card">
        <h3>📋 수집 데이터 미리보기</h3>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(
        df.head(100),
        use_container_width=True,
        height=500
    )

    st.markdown("""
    <div class="card">
        <h3>🔎 국가유산 검색</h3>
    </div>
    """, unsafe_allow_html=True)

    search_word = st.text_input(
        "문화재 이름 검색",
        placeholder="예: 은해사"
    )

    if search_word:

        result = df[
            df["문화재명(국문)"]
            .fillna("")
            .str.contains(
                search_word,
                case=False,
                na=False
            )
        ]

        st.write(
            f"검색 결과: **{len(result):,}건**"
        )

        if not result.empty:

            st.dataframe(
                result,
                use_container_width=True,
                height=400
            )

        else:

            st.warning(
                "검색 결과가 없습니다."
            )

else:

    st.info(
        "위의 **전국 국가유산 데이터 수집 시작** 버튼을 눌러 데이터를 가져오세요."
    )

st.markdown(
    '<div class="footer">국가유산 API 기반 데이터 수집 서비스</div>',
    unsafe_allow_html=True
)
