import streamlit as st
import pandas as pd
import numpy as np
import itertools

# 1. 페이지 레이아웃 및 테마 설정
st.set_page_config(
    page_title="영천 기상 데이터 전처리 마스터", 
    page_icon="🌤️",
    layout="wide"
)

# 기본 타이틀 및 디자인
st.title("🌤️ 대기/환경 데이터 통합 전처리 파이프라인")
st.markdown("---")

# 사이드바에 가이드라인 배치하여 메인 화면을 깔끔하게 유지
with st.sidebar:
    st.header("⚙️ 데이터 가이드")
    st.info("영천 기상 데이터(`.csv`)를 업로드하면 자동으로 파생변수 생성, 재질/노출 조합 확장, 0~100 정규화까지 한 번에 수행됩니다.")
    st.markdown("""
    **자동 인식 컬럼:**
    * `avg_temperature_c` ➡️ 기온
    * `daily_precipitation_mm` ➡️ 강수량
    * `avg_wind_speed_ms` ➡️ 풍속
    * `avg_relative_humidity_pct` ➡️ 습도
    """)

# ============================================================
# 코어 연산 함수 (하나로 합쳐서 한 번에 처리)
# ============================================================
@st.cache_data(show_spinner="데이터 변환 3단계 파이프라인을 가동 중입니다...")
def run_total_preprocessing(dataframe):
    df = dataframe.copy()
    
    # [단계 1] 컬럼명 변환 및 숫자형 변환
    rename_dict = {
        "avg_temperature_c": "temp_avg",
        "daily_precipitation_mm": "rainfall",
        "avg_wind_speed_ms": "wind_speed",
        "avg_relative_humidity_pct": "humidity"
    }
    df = df.rename(columns=rename_dict)
    
    calc_cols = ["temp_avg", "rainfall", "wind_speed", "humidity"]
    for col in calc_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            return None, None, None

    # [단계 2] 7. 파생변수 생성
    df["temp_range"] = df["temp_avg"] * 0.2  
    df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std()
    df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()
    df["high_humidity_risk"] = (df["humidity"] >= 75).rolling(3, min_periods=1).sum()
    
    df["weathering_risk"] = (df["temp_range"] * 0.4 + df["humidity_std3"] * 0.3 + df["wind_speed"] * 0.3)
    df["mold_risk"] = ((df["humidity"] >= 75) & (df["temp_avg"] >= 15)).astype(int)
    df["pm_load"] = 0
    df["acid_risk"] = 0
    df["oxidation_risk"] = 0
    df["corrosion_risk"] = df["humidity"] * 0.5
    df = df.fillna(0)
    
    derived_df = df.copy() # 파생변수까지만 완료된 데이터 보관

    # [단계 3] 8. 재질 x 노출 조합 생성 (15배 확장)
    materials = ["석조", "목조", "금속", "회화", "기타"]
    exposures = ["실외", "반실외", "실내"]
    
    comb = pd.DataFrame(list(itertools.product(materials, exposures)), columns=["material", "exposure"])
    df["key"] = 1
    comb["key"] = 1
    dataset = pd.merge(df, comb, on="key").drop("key", axis=1)

    # [단계 4] 9. 0~100 정규화 연산
    risk_cols = [
        "weathering_risk", "acid_risk", "rainfall_7d", "temp_range", 
        "pm_load", "corrosion_risk", "mold_risk", "humidity_std3", 
        "oxidation_risk", "high_humidity_risk"
    ]
    
    for col in risk_cols:
        col_min = dataset[col].min()
        col_max = dataset[col].max()
        if col_max - col_min == 0:
            dataset[col+"_norm"] = 0.0
        else:
            dataset[col+"_norm"] = ((dataset[col] - col_min) / (col_max - col_min + 1e-6)) * 100
            
    return dataframe, derived_df, dataset


# ============================================================
# 메인 UI 레이아웃
# ============================================================
uploaded_file = st.file_uploader("📂 전처리할 영천 기상 데이터 CSV 파일을 업로드하세요.", type=["csv"])

if uploaded_file is not None:
    raw_data = pd.read_csv(uploaded_file)
    
    # 데이터 파이프라인 가동
    raw_df, derived_df, final_df = run_total_preprocessing(raw_data)
    
    if final_df is not None:
        # 1. 상단에 성공 스태터스 및 메트릭 대시보드 배치
        st.success("🎉 데이터 파이프라인이 성공적으로 가동되었습니다! 아래 탭에서 결과를 확인하세요.")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric(label="원본 데이터 행 수", value=f"{raw_df.shape[0]:,} 개")
        with m_col2:
            st.metric(label="최종 데이터 행 수 (15배 확장)", value=f"{final_df.shape[0]:,} 개")
        with m_col3:
            st.metric(label="생성된 총 컬럼 수", value=f"{final_df.shape[1]} 개")
            
        st.markdown("### 🗂️ 전처리 단계별 데이터 확인")
        
        # 2. 탭 인터페이스를 사용하여 깔끔하게 분리
        tab1, tab2, tab3 = st.tabs(["📋 1. 원본 데이터", "🚀 2. 파생변수 생성 완료", "🧱 3. 최종 본 (조합+정규화 완료)"])
        
        with tab1:
            st.caption("업로드된 원래 데이터의 형태입니다.")
            st.dataframe(raw_df.head(10), use_container_width=True)
            
        with tab2:
            st.caption("기존 컬럼들을 조합하여 10종의 환경 리스크 파생변수를 추가한 상태입니다.")
            st.dataframe(derived_df.head(10), use_container_width=True)
            
        with tab3:
            st.caption("재질 5종 × 노출 3종 격자가 융합되고, 모든 리스크 지표가 0~100 범위(`_norm`)로 정규화된 최종본입니다.")
            
            # 다운로드 영역을 눈에 띄게 이쁘게 배치
            st.markdown("#### ⬇️ 최종 결과물 저장")
            final_csv = final_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 최종 전처리 완료 데이터(CSV) 다운로드",
                data=final_csv,
                file_name="final_processed_normalized_data.csv",
                mime="text/csv"
            )
            st.markdown("---")
            st.dataframe(final_df.head(15), use_container_width=True)
            
    else:
        st.error("⚠️ 파일의 컬럼명이 올바르지 않습니다. 왼쪽 사이드바의 자동 인식 컬럼 가이드를 확인해 주세요.")
else:
    # 파일 미업로드 시 예쁜 대기 화면 블록
    st.subheader("📥 파일을 기다리는 중입니다...")
    st.help("영천 기상 데이터셋 파일을 드래그 앤 드롭 하거나 파일 찾아보기를 클릭해 주세요.")
