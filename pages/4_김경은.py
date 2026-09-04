import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import math
import os
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="전국 국가유산 데이터", page_icon="🏛️", layout="wide")

st.title("🏛️ 전국 국가유산 데이터 수집 및 분석")
st.markdown("국가유산 API를 이용하여 전국 국가유산 데이터를 수집하고 종목별 현황을 확인할 수 있습니다.")

BASE_URL = "https://www.khs.go.kr"
LIST_URL = BASE_URL + "/cha/SearchKindOpenapiList.do"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def safe_request(url, params=None, retry=5):
    for i in range(retry):
        try:
            response = session.get(url, params=params, timeout=20)
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
    status_text = st.empty()
    for page in range(1, total_pages + 1):
        params["pageIndex"] = str(page)
        response = safe_request(LIST_URL, params)
        if response is None:
            status_text.warning(f"{page}페이지 요청 실패")
            continue
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            status_text.warning(f"{page}페이지 XML 오류")
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
        status_text.info(f"데이터 수집 중... {page} / {total_pages} 페이지")
        time.sleep(0.3)
    progress.empty()
    status_text.empty()
    return pd.DataFrame(all_data)

DATA_PATH = os.path.join("data", "국가유산_전체데이터.csv")

if os.path.exists(DATA_PATH):
    try:
        df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
        st.success("GitHub에 저장된 CSV 데이터를 불러왔습니다.")
    except Exception as e:
        st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다.\n\n{e}")
        df = pd.DataFrame()
else:
    st.info("저장된 CSV 파일이 없습니다. 아래 버튼을 눌러 API에서 데이터를 가져올 수 있습니다.")
    df = pd.DataFrame()

st.subheader("📥 데이터 수집")

if st.button("🌐 API에서 전국 국가유산 데이터 가져오기", use_container_width=True):
    with st.spinner("전국 국가유산 데이터를 수집하고 있습니다..."):
        new_df = collect_heritage_data()
    if not new_df.empty:
        df = new_df
        st.success(f"총 {len(df):,}건의 데이터를 수집했습니다.")
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="⬇️ CSV 파일 다운로드",
            data=csv_data,
            file_name="국가유산_전체데이터.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.error("데이터를 가져오지 못했습니다.")

if df.empty:
    st.warning("현재 표시할 데이터가 없습니다.")
    st.stop()

df = df.copy()

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
        df[col] = df[col].fillna("").astype(str).str.strip()

if "위도" in df.columns:
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")

if "경도" in df.columns:
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

st.divider()
st.subheader("📊 데이터 기본 정보")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("전체 국가유산", f"{len(df):,}건")

with col2:
    category_count = df["국가유산종목"].replace("", pd.NA).nunique() if "국가유산종목" in df.columns else 0
    st.metric("국가유산 종목", f"{category_count:,}개")

with col3:
    sido_count = df["시도명"].replace("", pd.NA).nunique() if "시도명" in df.columns else 0
    st.metric("시도", f"{sido_count:,}개")

with col4:
    sigungu_count = df["시군구명"].replace("", pd.NA).nunique() if "시군구명" in df.columns else 0
    st.metric("시군구", f"{sigungu_count:,}개")

st.divider()
st.subheader("📋 국가유산 데이터")

st.dataframe(
    df,
    use_container_width=True,
    height=450
)

st.divider()
st.subheader("📈 전국 국가유산 종목별 현황")

if "국가유산종목" in df.columns:
    nation_count = df["국가유산종목"].replace("", pd.NA).dropna().value_counts()
    if not nation_count.empty:
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.barplot(
            x=nation_count.values,
            y=nation_count.index,
            hue=nation_count.index,
            palette="viridis",
            legend=False,
            ax=ax
        )
        ax.set_title(
            f"전국 국가유산 종목별 현황 (총 {len(df):,}건)",
            fontsize=18,
            fontweight="bold"
        )
        ax.set_xlabel("개수", fontsize=13)
        ax.set_ylabel("국가유산종목", fontsize=13)
        for i, value in enumerate(nation_count.values):
            ax.text(
                value + max(nation_count.values) * 0.01,
                i,
                f"{value:,}건",
                va="center",
                fontsize=10,
                fontweight="bold"
            )
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.warning("국가유산종목 데이터가 없습니다.")

st.divider()
st.subheader("🗺️ 시도별 국가유산 현황")

if "시도명" in df.columns:
    sido_count = df["시도명"].replace("", pd.NA).dropna().value_counts()
    if not sido_count.empty:
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.barplot(
            x=sido_count.values,
            y=sido_count.index,
            hue=sido_count.index,
            palette="magma",
            legend=False,
            ax=ax
        )
        ax.set_title("시도별 국가유산 개수", fontsize=18, fontweight="bold")
        ax.set_xlabel("개수")
        ax.set_ylabel("시도")
        for i, value in enumerate(sido_count.values):
            ax.text(
                value + max(sido_count.values) * 0.01,
                i,
                f"{value:,}",
                va="center"
            )
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

st.divider()
st.subheader("🔎 국가유산 검색")

search_word = st.text_input(
    "문화재 이름을 입력하세요",
    placeholder="예: 은해사"
)

if search_word:
    search_result = df[
        df["문화재명(국문)"].str.contains(
            search_word,
            case=False,
            na=False
        )
    ]
    st.write(f"검색 결과: **{len(search_result):,}건**")
    if not search_result.empty:
        st.dataframe(
            search_result,
            use_container_width=True,
            height=400
        )
    else:
        st.warning("검색 결과가 없습니다.")

st.divider()
st.subheader("💾 데이터 다운로드")

csv_data = df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="⬇️ 국가유산 전체 CSV 다운로드",
    data=csv_data,
    file_name="국가유산_전체데이터.csv",
    mime="text/csv",
    use_container_width=True
)

st.divider()
st.caption("국가유산 API를 활용한 전국 국가유산 데이터 수집 및 분석")
