import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import xml.etree.ElementTree as ET
import math
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

# ==========================================================
# 페이지 기본 설정 & 한글 폰트 (Streamlit Cloud 환경 대응)
# ==========================================================
st.set_page_config(
    page_title="국가유산 데이터 수집 및 분석",
    page_icon="🏛️",
    layout="wide"
)

# Matplotlib 한글 폰트 설정 (OS별 자동 매핑)
import platform
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rcParams["axes.unicode_minus"] = False

# ==========================================================
# API 관련 공통 함수
# ==========================================================
BASE_URL = "https://www.khs.go.kr"
LIST_URL = BASE_URL + "/cha/SearchKindOpenapiList.do"
DETAIL_URL = BASE_URL + "/cha/SearchKindOpenapiDt.do"

@st.cache_resource
def get_session():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session

session = get_session()

def safe_request(url, params=None, retry=5):
    for i in range(retry):
        try:
            response = session.get(url, params=params, timeout=20)
            if response.status_code == 200:
                return response
        except Exception:
            time.sleep(2)
    return None

# 목록 수집 함수 (캐싱 적용)
@st.cache_data(show_spinner=False)
def fetch_national_heritage_list():
    params = {"pageUnit": "300", "pageIndex": "1", "ccbaCncl": "N"}
    response = safe_request(LIST_URL, params)
    
    if not response:
        return pd.DataFrame()

    root = ET.fromstring(response.content)
    totalCnt = int(root.findtext("totalCnt"))
    pageUnit = int(root.findtext("pageUnit"))
    total_pages = math.ceil(totalCnt / pageUnit)

    all_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for page in range(1, total_pages + 1):
        params["pageIndex"] = str(page)
        res = safe_request(LIST_URL, params)
        
        if res is not None:
            p_root = ET.fromstring(res.content)
            for item in p_root.iter("item"):
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
        
        progress = page / total_pages
        progress_bar.progress(progress)
        status_text.text(f"목록 수집 진행 중: {page}/{total_pages} 페이지 완료")
        time.sleep(0.1)

    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(all_data)

# 상세 정보 수집 함수
def get_detail(ccbaKdcd, ccbaAsno, ccbaCtcd):
    params = {
        "ccbaKdcd": str(ccbaKdcd).zfill(2),
        "ccbaAsno": str(ccbaAsno),
        "ccbaCtcd": str(ccbaCtcd).zfill(2)
    }
    response = safe_request(DETAIL_URL, params)
    if response is None:
        return None

    try:
        root = ET.fromstring(response.content)
        item = root.find("item")
        if item is None:
            return None

        return {
            "종목코드": root.findtext("ccbaKdcd"),
            "관리번호": root.findtext("ccbaAsno"),
            "시도코드": root.findtext("ccbaCtcd"),
            "국가유산연계번호": root.findtext("ccbaCpno"),
            "경도": root.findtext("longitude"),
            "위도": root.findtext("latitude"),
            "국가유산종목": item.findtext("ccmaName"),
            "국가유산분류": item.findtext("gcodeName"),
            "국가유산분류2": item.findtext("bcodeName"),
            "국가유산분류3": item.findtext("mcodeName"),
            "국가유산분류4": item.findtext("scodeName"),
            "문화재명(국문)": item.findtext("ccbaMnm1"),
            "문화재명(한자)": item.findtext("ccbaMnm2"),
            "수량": item.findtext("ccbaQuan"),
            "지정일": item.findtext("ccbaAsdt"),
            "시도명": item.findtext("ccbaCtcdNm"),
            "시군구명": item.findtext("ccsiName"),
            "소재지상세": item.findtext("ccbaLcad"),
            "시대": item.findtext("ccceName"),
            "소유자": item.findtext("ccbaPoss"),
            "관리자": item.findtext("ccbaAdmin"),
            "지정해제여부": item.findtext("ccbaCncl"),
            "이미지URL": item.findtext("imageUrl"),
            "내용": item.findtext("content")
        }
    except Exception:
        return None

# ==========================================================
# Streamlit 대시보드 UI
# ==========================================================
st.title("🏛️ 전국 및 지역별 국가유산 데이터 수집 & 분석")

st.sidebar.header("📌 메뉴")
menu = st.sidebar.radio("원하는 작업을 선택하세요", ["전국 데이터 수집 및 분석", "영천 지역 데이터 분석 및 상세조회"])

# ----------------------------------------------------------
# 메뉴 1: 전국 데이터 수집 및 분석
# ----------------------------------------------------------
if menu == "전국 데이터 수집 및 분석":
    st.header("1. 전국 국가유산 데이터 목록 수집")
    
    if st.button("🚀 전국 데이터 수집 시작"):
        with st.spinner("공공 API로부터 전체 데이터를 수집하고 있습니다..."):
            df_nation = fetch_national_heritage_list()
            st.session_state["df_nation"] = df_nation
            st.success(f"수집 완료! 총 {len(df_nation)}건의 데이터를 불러왔습니다.")

    if "df_nation" in st.session_state and not st.session_state["df_nation"].empty:
        df_nation = st.session_state["df_nation"]
        
        st.subheader("📊 전국 국가유산 목록 미리보기")
        st.dataframe(df_nation.head(10))

        # CSV 다운로드 버튼
        csv_data = df_nation.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="💾 전국 데이터 CSV 다운로드",
            data=csv_data,
            file_name="국가유산_전체데이터.csv",
            mime="text/csv"
        )

        st.subheader("📈 전국 국가유산 종목별 현황")
        nation_count = df_nation["국가유산종목"].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x=nation_count.values,
            y=nation_count.index,
            hue=nation_count.index,
            palette="viridis",
            legend=False,
            ax=ax
        )
        ax.set_title(f"전국 국가유산 종목별 현황 (총 {len(df_nation)}건)", fontsize=14, weight="bold")
        ax.set_xlabel("개수")
        ax.set_ylabel("종목")

        for i, v in enumerate(nation_count.values):
            ax.text(v + 1, i, f"{v}건", va="center", fontsize=9, weight="bold")

        plt.tight_layout()
        st.pyplot(fig)

# ----------------------------------------------------------
# 메뉴 2: 영천 지역 데이터 분석 및 상세조회
# ----------------------------------------------------------
elif menu == "영천 지역 데이터 분석 및 상세조회":
    st.header("2. 영천 국가유산 데이터 추출 및 상세조회")

    # 기존 수집 데이터가 없는 경우를 위한 처리
    if "df_nation" not in st.session_state:
        st.warning("먼저 '전국 데이터 수집 및 분석' 메뉴에서 데이터를 수집하거나, 기존 CSV 파일을 업로드해 주세요.")
        uploaded_file = st.file_uploader("기존 '국가유산_전체데이터.csv' 파일 업로드", type=["csv"])
        if uploaded_file is not None:
            df_nation = pd.read_csv(uploaded_file, dtype={"종목코드": str, "관리번호": str, "시도코드": str})
            st.session_state["df_nation"] = df_nation
            st.success("CSV 파일 업로드 완료!")
    
    if "df_nation" in st.session_state:
        df_nation = st.session_state["df_nation"]
        
        # 영천 데이터 추출
        yc_df = df_nation[df_nation["시군구명"].astype(str).str.contains("영천", na=False)].copy()
        
        st.metric(label="📍 영천시 수집 문화재 수", value=f"{len(yc_df)} 건")
        st.dataframe(yc_df[["문화재명(국문)", "국가유산종목", "종목코드", "관리번호"]].head())

        # 종목별 시각화
        st.subheader("📊 영천 국가유산 종목 분포")
        yc_count = yc_df["국가유산종목"].value_counts()

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(
            x=yc_count.values,
            y=yc_count.index,
            hue=yc_count.index,
            palette="Set2",
            legend=False,
            ax=ax
        )
        ax.set_title(f"영천 국가유산 종목 분포 ({len(yc_df)}건)")
        ax.set_xlabel("개수")
        ax.set_ylabel("종목")

        for i, v in enumerate(yc_count.values):
            ax.text(v + 0.2, i, f"{v}건", va="center", fontsize=10, weight="bold")

        plt.tight_layout()
        st.pyplot(fig)

        # 상세정보 수집
        st.subheader("🔍 영천 국가유산 상세조회 진행")
        if st.button("⚡ 영천 상세데이터 수집 실행"):
            detail_list = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            total_items = len(yc_df)

            for idx, (_, row) in enumerate(yc_df.iterrows()):
                detail = get_detail(row["종목코드"], row["관리번호"], row["시도코드"])
                if detail:
                    detail_list.append(detail)

                progress = (idx + 1) / total_items
                progress_bar.progress(progress)
                status_text.text(f"상세조회 진행 중: {idx+1}/{total_items}")
                time.sleep(0.3)

            progress_bar.empty()
            status_text.empty()

            df_detail = pd.DataFrame(detail_list)
            st.session_state["df_detail"] = df_detail
            st.success("영천 국가유산 상세 정보 수집 완료!")

        if "df_detail" in st.session_state and not st.session_state["df_detail"].empty:
            df_detail = st.session_state["df_detail"]
            st.subheader("📋 영천 국가유산 상세 데이터 미리보기")
            st.dataframe(df_detail.head())

            # 상세 데이터 CSV 다운로드
            csv_detail_data = df_detail.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="💾 영천 상세 데이터 CSV 다운로드",
                data=csv_detail_data,
                file_name="영천_국가유산_상세.csv",
                mime="text/csv"
            )

            # 지도 시각화 (위도/경도 데이터 존재 시)
            if "위도" in df_detail.columns and "경도" in df_detail.columns:
                st.subheader("🗺️ 영천 국가유산 지도 위치")
                valid_geo = df_detail.dropna(subset=["위도", "경도"]).copy()
                valid_geo["위도"] = pd.to_numeric(valid_geo["위도"], errors="coerce")
                valid_geo["경도"] = pd.to_numeric(valid_geo["경도"], errors="coerce")
                valid_geo = valid_geo.dropna(subset=["위도", "경도"])

                if not valid_geo.empty:
                    m = folium.Map(location=[valid_geo["위도"].mean(), valid_geo["경도"].mean()], zoom_start=11)
                    for _, r in valid_geo.iterrows():
                        folium.Marker(
                            location=[r["위도"], r["경도"]],
                            popup=f"<b>{r['문화재명(국문)']}</b><br>{r['소재지상세']}",
                            tooltip=r["문화재명(국문)"]
                        ).add_to(m)
                    st_folium(m, width=800, height=500)
