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
import os
import matplotlib.font_manager as fm

# ==========================================================
# 1. 페이지 기본 설정 & 세션 상태 안전 초기화
# ==========================================================
st.set_page_config(
    page_title="국가유산 데이터 수집 및 분석 시스템",
    page_icon="🏛️",
    layout="wide"
)

# 세션 상태 변수 초기화 (메뉴 이동 시 데이터 유지)
if "df_nation" not in st.session_state:
    st.session_state["df_nation"] = pd.DataFrame()
if "df_yc" not in st.session_state:
    st.session_state["df_yc"] = pd.DataFrame()
if "df_detail" not in st.session_state:
    st.session_state["df_detail"] = pd.DataFrame()

# ==========================================================
# 2. 한글 폰트 자동 설정 (Streamlit Cloud 대응)
# ==========================================================
@st.cache_resource
def set_korean_font():
    font_file = "NanumGothic.ttf"
    if not os.path.exists(font_file):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            r = requests.get(url, timeout=10)
            with open(font_file, "wb") as f:
                f.write(r.content)
        except Exception:
            pass
            
    if os.path.exists(font_file):
        fm.fontManager.addfont(font_file)
        font_prop = fm.FontProperties(fname=font_file)
        plt.rc('font', family=font_prop.get_name())
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

# ==========================================================
# 3. API 요청 및 수집 함수
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
            time.sleep(1)
    return None

# [전국] 목록 수집 함수
def fetch_national_heritage_list():
    params = {"pageUnit": "300", "pageIndex": "1", "ccbaCncl": "N"}
    response = safe_request(LIST_URL, params)
    if not response:
        return pd.DataFrame()

    root = ET.fromstring(response.content)
    totalCnt = int(root.findtext("totalCnt", "0"))
    pageUnit = int(root.findtext("pageUnit", "300"))
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
                    "국가유산종목": item.findtext("ccmaName", ""),
                    "문화재명(국문)": item.findtext("ccbaMnm1", ""),
                    "문화재명(한자)": item.findtext("ccbaMnm2", ""),
                    "시도명": item.findtext("ccbaCtcdNm", ""),
                    "시군구명": item.findtext("ccsiName", ""),
                    "관리자": item.findtext("ccbaAdmin", ""),
                    "종목코드": str(item.findtext("ccbaKdcd", "")),
                    "시도코드": str(item.findtext("ccbaCtcd", "")),
                    "관리번호": str(item.findtext("ccbaAsno", "")),
                    "경도": item.findtext("longitude", ""),
                    "위도": item.findtext("latitude", "")
                })
        progress = page / total_pages
        progress_bar.progress(progress)
        status_text.text(f"전국 데이터 수집 중: {page}/{total_pages} 페이지 완료")
        time.sleep(0.02)

    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(all_data)

# [영천 전용] 빠른 직접 API 수집 함수
def fetch_yeongcheon_direct():
    params = {"pageUnit": "200", "pageIndex": "1", "ccbaCncl": "N", "ccbaCtcd": "37"} # 37: 경상북도
    response = safe_request(LIST_URL, params)
    if not response:
        return pd.DataFrame()

    root = ET.fromstring(response.content)
    totalCnt = int(root.findtext("totalCnt", "0"))
    pageUnit = int(root.findtext("pageUnit", "200"))
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
                ccsi = item.findtext("ccsiName", "")
                if "영천" in str(ccsi):
                    all_data.append({
                        "국가유산종목": item.findtext("ccmaName", ""),
                        "문화재명(국문)": item.findtext("ccbaMnm1", ""),
                        "문화재명(한자)": item.findtext("ccbaMnm2", ""),
                        "시도명": item.findtext("ccbaCtcdNm", ""),
                        "시군구명": ccsi,
                        "관리자": item.findtext("ccbaAdmin", ""),
                        "종목코드": str(item.findtext("ccbaKdcd", "")),
                        "시도코드": str(item.findtext("ccbaCtcd", "")),
                        "관리번호": str(item.findtext("ccbaAsno", "")),
                        "경도": item.findtext("longitude", ""),
                        "위도": item.findtext("latitude", "")
                    })
        progress_bar.progress(page / total_pages)
        status_text.text(f"영천 데이터 검색 중: {page}/{total_pages}")

    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(all_data)

# 상세 정보 조회 함수
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
            "종목코드": root.findtext("ccbaKdcd", ""),
            "관리번호": root.findtext("ccbaAsno", ""),
            "시도코드": root.findtext("ccbaCtcd", ""),
            "국가유산연계번호": root.findtext("ccbaCpno", ""),
            "경도": root.findtext("longitude", ""),
            "위도": root.findtext("latitude", ""),
            "국가유산종목": item.findtext("ccmaName", ""),
            "국가유산분류": item.findtext("gcodeName", ""),
            "국가유산분류2": item.findtext("bcodeName", ""),
            "국가유산분류3": item.findtext("mcodeName", ""),
            "국가유산분류4": item.findtext("scodeName", ""),
            "문화재명(국문)": item.findtext("ccbaMnm1", ""),
            "문화재명(한자)": item.findtext("ccbaMnm2", ""),
            "수량": item.findtext("ccbaQuan", ""),
            "지정일": item.findtext("ccbaAsdt", ""),
            "시도명": item.findtext("ccbaCtcdNm", ""),
            "시군구명": item.findtext("ccsiName", ""),
            "소재지상세": item.findtext("ccbaLcad", ""),
            "시대": item.findtext("ccceName", ""),
            "소유자": item.findtext("ccbaPoss", ""),
            "관리자": item.findtext("ccbaAdmin", ""),
            "지정해제여부": item.findtext("ccbaCncl", ""),
            "이미지URL": item.findtext("imageUrl", ""),
            "내용": item.findtext("content", "")
        }
    except Exception:
        return None

# ==========================================================
# 4. Streamlit UI 메인 화면
# ==========================================================
st.title("🏛️ 국가유산 데이터 수집 및 분석 시스템")

st.sidebar.header("📌 메뉴 선택")
menu = st.sidebar.radio(
    "원하는 작업을 선택하세요",
    ["메뉴 1: 전국 데이터 수집 및 분석", "메뉴 2: 영천 지역 데이터 분석 및 상세조회"]
)

# ----------------------------------------------------------
# 메뉴 1: 전국 데이터 수집 및 분석
# ----------------------------------------------------------
if menu == "메뉴 1: 전국 데이터 수집 및 분석":
    st.header("1. 전국 국가유산 데이터 수집")
    
    if st.button("🚀 전국 전체 데이터 수집 시작 (전체 API)"):
        with st.spinner("전국 데이터를 API로부터 수집 중입니다..."):
            df_nation = fetch_national_heritage_list()
            st.session_state["df_nation"] = df_nation
            
            # 영천 데이터 자동 추출 및 세션 저장
            if not df_nation.empty:
                yc_df = df_nation[df_nation["시군구명"].astype(str).str.contains("영천", na=False)].copy()
                st.session_state["df_yc"] = yc_df
            st.success(f"수집 완료! 총 {len(df_nation)}건 수집됨")

    if not st.session_state["df_nation"].empty:
        df_nation = st.session_state["df_nation"]
        st.subheader("📋 전국 수집 목록")
        st.dataframe(df_nation, use_container_width=True)

        # CSV 다운로드
        csv_data = df_nation.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("💾 전국 데이터 CSV 다운로드", data=csv_data, file_name="국가유산_전체데이터.csv", mime="text/csv")

        # 시각화
        st.subheader("📊 전국 종목별 현황")
        nation_count = df_nation["국가유산종목"].value_counts()
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=nation_count.values, y=nation_count.index, palette="viridis", ax=ax)
        ax.set_title(f"전국 국가유산 종목별 현황 ({len(df_nation)}건)", fontsize=13)
        for i, v in enumerate(nation_count.values):
            ax.text(v + 1, i, f"{v}건", va="center", fontsize=9, weight="bold")
        st.pyplot(fig)

# ----------------------------------------------------------
# 메뉴 2: 영천 지역 데이터 분석 및 상세조회
# ----------------------------------------------------------
elif menu == "메뉴 2: 영천 지역 데이터 분석 및 상세조회":
    st.header("2. 영천 지역 데이터 분석 및 상세조회")

    # 데이터가 없을 때 사용자 선택 옵션 상자
    if st.session_state["df_yc"].empty:
        st.info("💡 영천 데이터가 세션에 없습니다. 아래 3가지 방법 중 하나로 데이터를 불러오세요.")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 영천 데이터만 즉시 API 수집 (추천)"):
                with st.spinner("영천 지역 국가유산을 API에서 바로 조회 중입니다..."):
                    df_yc = fetch_yeongcheon_direct()
                    st.session_state["df_yc"] = df_yc
                    st.rerun()
        
        with c2:
            uploaded_file = st.file_uploader("📂 기존 '국가유산_전체데이터.csv' 업로드", type=["csv"])
            if uploaded_file is not None:
                df_loaded = pd.read_csv(uploaded_file, dtype={"종목코드": str, "관리번호": str, "시도코드": str})
                st.session_state["df_nation"] = df_loaded
                st.session_state["df_yc"] = df_loaded[df_loaded["시군구명"].astype(str).str.contains("영천", na=False)].copy()
                st.rerun()

    # 데이터가 존재하는 경우 탭 메뉴 생성
    if not st.session_state["df_yc"].empty:
        df_yc = st.session_state["df_yc"]
        
        tab1, tab2, tab3 = st.tabs(["📊 1. 목록 및 분포 분석", "🔍 2. 상세정보 수집", "🗺️ 3. 지도 시각화"])

        # ------------------------------------------------------
        # Tab 1: 목록 및 분포 분석
        # ------------------------------------------------------
        with tab1:
            st.metric(label="📍 영천시 수집 지정 문화재 수", value=f"{len(df_yc)} 건")
            st.dataframe(df_yc[["문화재명(국문)", "국가유산종목", "시군구명", "종목코드", "관리번호"]], use_container_width=True)

            st.subheader("📊 영천 종목별 분포 그래프")
            yc_count = df_yc["국가유산종목"].value_counts()
            fig, ax = plt.subplots(figsize=(10, 4.5))
            sns.barplot(x=yc_count.values, y=yc_count.index, palette="Set2", ax=ax)
            ax.set_title(f"영천 국가유산 종목 분포 ({len(df_yc)}건)")
            for i, v in enumerate(yc_count.values):
                ax.text(v + 0.1, i, f"{v}건", va="center", fontsize=10, weight="bold")
            plt.tight_layout()
            st.pyplot(fig)

        # ------------------------------------------------------
        # Tab 2: 상세정보 수집
        # ------------------------------------------------------
        with tab2:
            st.subheader("🔍 영천 국가유산 상세 API 수집")
            if st.button("⚡ 영천 상세 정보 수집 실행"):
                detail_list = []
                prog = st.progress(0)
                stat = st.empty()
                total = len(df_yc)

                for idx, (_, row) in enumerate(df_yc.iterrows()):
                    detail = get_detail(row["종목코드"], row["관리번호"], row["시도코드"])
                    if detail:
                        detail_list.append(detail)
                    prog.progress((idx + 1) / total)
                    stat.text(f"상세 정보 수집 중: {idx+1}/{total}")
                    time.sleep(0.1)

                prog.empty()
                stat.empty()

                df_detail = pd.DataFrame(detail_list)
                st.session_state["df_detail"] = df_detail
                st.success("영천 상세 정보 수집 완료!")

            if not st.session_state["df_detail"].empty:
                df_detail = st.session_state["df_detail"]
                st.dataframe(df_detail, use_container_width=True)
                
                csv_detail = df_detail.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("💾 영천 상세 데이터 CSV 다운로드", data=csv_detail, file_name="영천_국가유산_상세.csv", mime="text/csv")

        # ------------------------------------------------------
        # Tab 3: 지도 시각화
        # ------------------------------------------------------
        with tab3:
            st.subheader("🗺️ 영천 국가유산 위치 지도")
            target_df = st.session_state["df_detail"] if not st.session_state["df_detail"].empty else df_yc
            
            if "위도" in target_df.columns and "경도" in target_df.columns:
                valid_geo = target_df.dropna(subset=["위도", "경도"]).copy()
                valid_geo["위도"] = pd.to_numeric(valid_geo["위도"], errors="coerce")
                valid_geo["경도"] = pd.to_numeric(valid_geo["경도"], errors="coerce")
                valid_geo = valid_geo.dropna(subset=["위도", "경도"])

                if not valid_geo.empty:
                    m = folium.Map(location=[valid_geo["위도"].mean(), valid_geo["경도"].mean()], zoom_start=11)
                    for _, r in valid_geo.iterrows():
                        folium.Marker(
                            location=[r["위도"], r["경도"]],
                            popup=f"<b>{r['문화재명(국문)']}</b>",
                            tooltip=r["문화재명(국문)"]
                        ).add_to(m)
                    st_folium(m, width=900, height=500)
                else:
                    st.warning("위도/경도 좌표 데이터가 올바르지 않습니다.")
