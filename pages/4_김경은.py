import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import math
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="국가유산 데이터 수집",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
* {
    font-family: 'Noto Sans KR', sans-serif;
}
.stApp {
    background: #f4f7f6;
}
.block-container {
    max-width: 1400px;
    padding: 2rem 3rem 3rem 3rem;
}
.header {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #173f35 0%, #246b5a 55%, #3b8c75 100%);
    padding: 48px 52px;
    border-radius: 28px;
    margin-bottom: 28px;
    color: white;
    box-shadow: 0 15px 40px rgba(23,63,53,0.18);
}
.header:after {
    content: "🏛";
    position: absolute;
    right: 55px;
    top: 20px;
    font-size: 130px;
    opacity: 0.10;
}
.title {
    position: relative;
    z-index: 2;
    font-size: 40px;
    font-weight: 800;
    letter-spacing: -1.5px;
}
.subtitle {
    position: relative;
    z-index: 2;
    font-size: 16px;
    color: rgba(255,255,255,0.78);
    margin-top: 12px;
}
.section-title {
    font-size: 22px;
    font-weight: 800;
    color: #173f35;
    margin: 34px 0 16px 2px;
    letter-spacing: -0.5px;
}
.card {
    background: #ffffff;
    padding: 25px 28px;
    border-radius: 20px;
    border: 1px solid #e5ebe8;
    margin-bottom: 18px;
    box-shadow: 0 5px 18px rgba(30,60,50,0.05);
}
.card h3 {
    margin: 0 0 8px 0;
    color: #173f35;
    font-size: 19px;
    font-weight: 800;
}
.card p {
    margin: 0;
    color: #68746f;
    font-size: 14px;
    line-height: 1.7;
}
.metric {
    background: #ffffff;
    padding: 25px 20px;
    border-radius: 20px;
    border: 1px solid #e5ebe8;
    box-shadow: 0 5px 18px rgba(30,60,50,0.05);
    position: relative;
    overflow: hidden;
}
.metric:before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 5px;
    height: 100%;
    background: #2d806a;
}
.metric-title {
    color: #78837f;
    font-size: 13px;
    font-weight: 600;
    margin-left: 5px;
}
.metric-value {
    color: #173f35;
    font-size: 31px;
    font-weight: 800;
    margin-top: 6px;
    letter-spacing: -1px;
    margin-left: 5px;
}
.rank {
    background: #ffffff;
    padding: 17px 20px;
    border-radius: 15px;
    margin-bottom: 9px;
    border: 1px solid #e7ecea;
    box-shadow: 0 3px 12px rgba(30,60,50,0.035);
    transition: 0.2s;
}
.rank:hover {
    transform: translateY(-2px);
    box-shadow: 0 7px 20px rgba(30,60,50,0.08);
}
.rank-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    font-weight: 700;
    color: #34443e;
    margin-bottom: 10px;
}
.rank-top span:last-child {
    color: #2d806a;
}
.bar-bg {
    width: 100%;
    height: 9px;
    background: #e9efec;
    border-radius: 20px;
    overflow: hidden;
}
.bar {
    height: 100%;
    background: linear-gradient(90deg, #246b5a, #55a88d);
    border-radius: 20px;
}
.top-card {
    background: white;
    border: 1px solid #e5ebe8;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 12px;
    box-shadow: 0 4px 15px rgba(30,60,50,0.05);
}
.top-number {
    font-size: 25px;
    font-weight: 800;
    color: #246b5a;
}
.top-name {
    font-size: 17px;
    font-weight: 700;
    color: #263b34;
    margin-top: 5px;
}
.top-count {
    font-size: 13px;
    color: #7b8782;
    margin-top: 3px;
}
.filter-box {
    background: #f8faf9;
    border: 1px solid #e1e9e5;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 20px;
}
.footer {
    text-align: center;
    color: #9aa7a2;
    padding: 35px 0 10px 0;
    font-size: 13px;
}
.stButton > button {
    background: linear-gradient(135deg, #173f35, #2d806a);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 13px 20px;
    font-size: 15px;
    font-weight: 700;
    box-shadow: 0 7px 18px rgba(45,128,106,0.20);
    transition: 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #12352d, #246b5a);
    transform: translateY(-1px);
}
.stDownloadButton > button {
    background: #eef7f3;
    color: #246b5a;
    border: 1px solid #cce4db;
    border-radius: 13px;
    font-weight: 700;
    padding: 12px 18px;
}
.stDownloadButton > button:hover {
    background: #e0f0ea;
    border-color: #a9d1c2;
}
.stTextInput > div > div > input {
    border-radius: 13px;
    border: 1px solid #d8e1dd;
    padding: 12px 15px;
    background: white;
}
.stTextInput > div > div > input:focus {
    border-color: #3b8c75;
    box-shadow: 0 0 0 2px rgba(59,140,117,0.12);
}
[data-testid="stDataFrame"] {
    border-radius: 15px;
    overflow: hidden;
    border: 1px solid #e1e8e5;
}
.stAlert {
    border-radius: 14px;
}
@media (max-width: 768px) {
    .block-container {
        padding: 1rem;
    }
    .header {
        padding: 32px 25px;
        border-radius: 22px;
    }
    .title {
        font-size: 29px;
    }
    .subtitle {
        font-size: 14px;
    }
    .header:after {
        font-size: 80px;
        right: 20px;
    }
    .metric-value {
        font-size: 25px;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <div class="title">🏛️ 국가유산 데이터 수집</div>
    <div class="subtitle">
        국가유산 API를 이용하여 전국 국가유산 데이터를 수집하고 분석할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

BASE_URL = "https://www.khs.go.kr"
LIST_URL = BASE_URL + "/cha/SearchKindOpenapiList.do"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def safe_request(url, params=None, retry=5):
    for _ in range(retry):
        try:
            response = session.get(url, params=params, timeout=20)
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
    response = safe_request(LIST_URL, params)
    if response is None:
        return pd.DataFrame()
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        return pd.DataFrame()
    total_text = root.findtext("totalCnt")
    page_unit_text = root.findtext("pageUnit")
    if not total_text:
        return pd.DataFrame()
    total_cnt = int(total_text)
    page_unit = int(page_unit_text) if page_unit_text else 300
    total_pages = math.ceil(total_cnt / page_unit)
    all_data = []
    progress = st.progress(0)
    status = st.empty()

    for page in range(1, total_pages + 1):
        params["pageIndex"] = str(page)
        response = safe_request(LIST_URL, params)
        if response is None:
            continue
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            continue
        items = list(root.iter("item"))
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
        progress.progress(page / total_pages)
        status.info(f"전국 국가유산 데이터 수집 중... {page} / {total_pages} 페이지")
        time.sleep(0.3)

    progress.empty()
    status.empty()
    return pd.DataFrame(all_data)

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

st.markdown('<div class="section-title">📥 데이터 수집</div>', unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <h3>🌐 전국 국가유산 데이터 수집</h3>
    <p>
        아래 버튼을 누르면 국가유산 API에서 전국 데이터를 직접 가져옵니다.
        수집이 완료되면 CSV 파일로 바로 다운로드할 수 있습니다.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🌐 전국 국가유산 데이터 수집 시작", use_container_width=True):
    with st.spinner("전국 국가유산 데이터를 수집하고 있습니다..."):
        df = collect_heritage_data()
    if not df.empty:
        st.session_state.df = df
        st.success(f"데이터 수집 완료! 총 {len(df):,}건")
    else:
        st.error("데이터를 가져오지 못했습니다. API 상태를 확인해주세요.")

df = st.session_state.df

if not df.empty:
    st.markdown('<div class="section-title">📊 수집 데이터 현황</div>', unsafe_allow_html=True)

    total_count = len(df)
    type_count = df["국가유산종목"].fillna("").replace("", pd.NA).nunique()
    sido_count = df["시도명"].fillna("").replace("", pd.NA).nunique()
    sigungu_count = df["시군구명"].fillna("").replace("", pd.NA).nunique()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">전체 국가유산</div>
            <div class="metric-value">{total_count:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">국가유산 종목</div>
            <div class="metric-value">{type_count:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">시도</div>
            <div class="metric-value">{sido_count:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">시군구</div>
            <div class="metric-value">{sigungu_count:,}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🗺️ 국가유산 분포 지도</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>📍 전국 국가유산 위치</h3>
        <p>위도와 경도 정보가 있는 국가유산을 지도에서 확인할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    map_df = df.copy()
    map_df["위도"] = pd.to_numeric(map_df["위도"], errors="coerce")
    map_df["경도"] = pd.to_numeric(map_df["경도"], errors="coerce")
    map_df = map_df.dropna(subset=["위도", "경도"])

    if not map_df.empty:
        center_lat = map_df["위도"].mean()
        center_lon = map_df["경도"].mean()

        heritage_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles="CartoDB positron"
        )

        for _, row in map_df.iterrows():
            name = row["문화재명(국문)"] if pd.notna(row["문화재명(국문)"]) else "문화재명 없음"
            heritage_type = row["국가유산종목"] if pd.notna(row["국가유산종목"]) else "종목 없음"
            sido = row["시도명"] if pd.notna(row["시도명"]) else "지역 정보 없음"
            sigungu = row["시군구명"] if pd.notna(row["시군구명"]) else ""

            popup_html = f"""
            <div style="font-family:Arial,sans-serif;width:220px;">
                <h4 style="margin-bottom:8px;">🏛️ {name}</h4>
                <p style="margin:4px 0;"><b>종목</b> : {heritage_type}</p>
                <p style="margin:4px 0;"><b>지역</b> : {sido} {sigungu}</p>
            </div>
            """

            folium.CircleMarker(
                location=[row["위도"], row["경도"]],
                radius=5,
                color="#246b5a",
                fill=True,
                fill_color="#3b8c75",
                fill_opacity=0.75,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(heritage_map)

        st_folium(
            heritage_map,
            use_container_width=True,
            height=600
        )
    else:
        st.warning("지도에 표시할 위치 정보가 없습니다.")

    st.markdown('<div class="section-title">🔎 국가유산 상세 필터</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>🎯 원하는 국가유산 찾기</h3>
        <p>지역과 국가유산 종목을 선택하여 원하는 데이터를 확인할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)

    with f1:
        sido_options = ["전체"] + sorted(
            df["시도명"].dropna().astype(str).unique().tolist()
        )
        selected_sido = st.selectbox("시도", sido_options)

    filtered_df = df.copy()

    if selected_sido != "전체":
        filtered_df = filtered_df[
            filtered_df["시도명"].fillna("") == selected_sido
        ]

    with f2:
        sigungu_options = ["전체"] + sorted(
            filtered_df["시군구명"].dropna().astype(str).unique().tolist()
        )
        selected_sigungu = st.selectbox("시군구", sigungu_options)

    if selected_sigungu != "전체":
        filtered_df = filtered_df[
            filtered_df["시군구명"].fillna("") == selected_sigungu
        ]

    with f3:
        type_options = ["전체"] + sorted(
            filtered_df["국가유산종목"].dropna().astype(str).unique().tolist()
        )
        selected_type = st.selectbox("국가유산종목", type_options)

    if selected_type != "전체":
        filtered_df = filtered_df[
            filtered_df["국가유산종목"].fillna("") == selected_type
        ]

    st.markdown(
        f'<div class="card"><h3>🔍 필터 결과</h3><p>선택한 조건에 해당하는 국가유산은 <b>{len(filtered_df):,}건</b>입니다.</p></div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400
    )

    st.markdown('<div class="section-title">📊 시도별 국가유산 통계</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>📈 지역별 국가유산 분포</h3>
        <p>각 시도에 얼마나 많은 국가유산이 분포되어 있는지 확인할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    sido_count_df = (
        df["시도명"]
        .fillna("")
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    if not sido_count_df.empty:
        max_sido = sido_count_df.max()

        for sido, count in sido_count_df.items():
            percentage = count / max_sido * 100
            st.markdown(f"""
            <div class="rank">
                <div class="rank-top">
                    <span>{sido}</span>
                    <span>{count:,}건</span>
                </div>
                <div class="bar-bg">
                    <div class="bar" style="width:{percentage}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🏆 국가유산이 많은 지역 TOP 5</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>🥇 지역별 국가유산 TOP 5</h3>
        <p>국가유산 데이터가 가장 많이 분포한 지역을 확인할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    top5 = sido_count_df.head(5)

    top_columns = st.columns(5)

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    for i, (sido, count) in enumerate(top5.items()):
        with top_columns[i]:
            st.markdown(f"""
            <div class="top-card">
                <div class="top-number">{medals[i]}</div>
                <div class="top-name">{sido}</div>
                <div class="top-count">{count:,}건</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">💾 데이터 다운로드</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>📦 CSV 파일 저장</h3>
        <p>
            API에서 수집한 전국 국가유산 데이터를 CSV 파일로 저장할 수 있습니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    csv_data = df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="⬇️ 국가유산 전체 데이터 CSV 다운로드",
        data=csv_data,
        file_name="국가유산_전체데이터.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.markdown('<div class="section-title">🏛️ 국가유산 종목별 현황</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>📈 국가유산 종목 분포</h3>
        <p>국가유산 종목별 데이터 수를 비교할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    nation_count = (
        df["국가유산종목"]
        .fillna("")
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    if not nation_count.empty:
        max_value = nation_count.max()

        for name, value in nation_count.items():
            percentage = value / max_value * 100
            st.markdown(f"""
            <div class="rank">
                <div class="rank-top">
                    <span>{name}</span>
                    <span>{value:,}건</span>
                </div>
                <div class="bar-bg">
                    <div class="bar" style="width:{percentage}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📋 데이터 미리보기</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>🗂️ 수집 데이터 미리보기</h3>
        <p>수집된 데이터 중 최대 100개의 항목을 확인할 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(
        df.head(100),
        use_container_width=True,
        height=500
    )

    st.markdown('<div class="section-title">🔍 국가유산 검색</div>', unsafe_allow_html=True)

    search_word = st.text_input(
        "문화재 이름 검색",
        placeholder="예: 은해사",
        label_visibility="collapsed"
    )

    if search_word:
        result = df[
            df["문화재명(국문)"]
            .fillna("")
            .str.contains(search_word, case=False, na=False)
        ]

        st.markdown(
            f'<div class="card"><h3>🔍 검색 결과</h3><p><b>{len(result):,}건</b>의 국가유산이 검색되었습니다.</p></div>',
            unsafe_allow_html=True
        )

        if not result.empty:
            st.dataframe(
                result,
                use_container_width=True,
                height=400
            )
        else:
            st.warning("검색 결과가 없습니다.")
else:
    st.info("위의 **전국 국가유산 데이터 수집 시작** 버튼을 눌러 데이터를 가져오세요.")

st.markdown(
    '<div class="footer">국가유산 API 기반 데이터 수집 서비스 · Yeongcheon Heritage Data Project</div>',
    unsafe_allow_html=True
)
