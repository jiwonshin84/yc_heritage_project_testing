import streamlit as st
import pandas as pd
import numpy as np
import itertools

# 페이지 기본 설정
st.set_page_config(page_title="영천 기상 데이터 전처리", layout="wide")

# ============================================================
# 1. 파생변수 생성 함수 (업로드된 파일 맞춤형 수정)
# ============================================================
@st.cache_data(show_spinner="1단계: 파생변수를 계산하고 있습니다...")
def create_derived_features(dataframe):
    df = dataframe.copy()
    
    # 영천 기상 데이터의 실제 컬럼명 맵핑 (코드가 인식하기 쉽게 영문 별칭으로 변경)
    rename_dict = {
        "avg_temperature_c": "temp_avg",
        "daily_precipitation_mm": "rainfall",
        "avg_wind_speed_ms": "wind_speed",
        "avg_relative_humidity_pct": "humidity"
    }
    
    # 컬럼명이 존재하는지 확인 후 변경
    df = df.rename(columns=rename_dict)
    
    # 데이터 타입 숫자형 강제 변환 및 결측치(NaN)를 0으로 처리
    calc_cols = ["temp_avg", "rainfall", "wind_speed", "humidity"]
    for col in calc_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            st.error(f"⚠️ **오류:** 필수 컬럼이 없습니다. 현재 컬럼: {df.columns.tolist()}")
            return None

    try:
        # 7. 현재 데이터로 계산 가능한 파생변수만 생성
        # (주의: 원본에 temp_max, temp_min이 없으므로 temp_range 대신 temp_avg를 활용하거나 기본값 처리)
        df["temp_range"] = df["temp_avg"] * 0.2  # 일교차 대용 임시 산식 (또는 0 처리)
        df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std()
        df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()
        df["high_humidity_risk"] = (df["humidity"] >= 75).rolling(3, min_periods=1).sum()
        
        # 풍화 위험도 (존재하는 기상 변수로만 재구성)
        df["weathering_risk"] = (
            df["temp_range"] * 0.4 +
            df["humidity_std3"] * 0.3 +
            df["wind_speed"] * 0.3
        )
        
        # 데이터가 없는 리스크들은 0으로 기본값 처리하여 에러 방지
        df["mold_risk"] = ((df["humidity"] >= 75) & (df["temp_avg"] >= 15)).astype(int)
        df["pm_load"] = 0
        df["acid_risk"] = 0
        df["oxidation_risk"] = 0
        df["corrosion_risk"] = df["humidity"] * 0.5

        # 최종 결측치 처리
        df = df.fillna(0)
        return df
    except Exception as e:
        st.error(f"⚠️ **연산 오류(파생변수):** {e}")
        return None

# ============================================================
# 2. 재질 × 노출 조합 & 3. 정규화 통합 연산 함수
# ============================================================
@st.cache_data(show_spinner="2~3단계: 조합 생성 및 0~100 정규화를 진행 중입니다...")
def generate_combinations_and_normalize(dataframe):
    df = dataframe.copy()
    
    # [8. 재질 x 노출 조합 생성]
    materials = ["석조", "목조", "금속", "회화", "기타"]
    exposures = ["실외", "반실외", "실내"]
    
    try:
        comb = pd.DataFrame(
            list(itertools.product(materials, exposures)),
            columns=["material", "exposure"]
        )
        df["key"] = 1
        comb["key"] = 1
        dataset = pd.merge(df, comb, on="key").drop("key", axis=1)
        
    except Exception as e:
        st.error(f"⚠️ **조합 오류:** {e}")
        return None

    # [9. 정규화 연산]
    risk_cols = [
        "weathering_risk", "acid_risk", "rainfall_7d",
        "temp_range", "pm_load", "corrosion_risk",
        "mold_risk", "humidity_std3", "oxidation_risk",
        "high_humidity_risk"
    ]
    
    try:
        for col in risk_cols:
            col_min = dataset[col].min()
            col_max = dataset[col].max()
            
            if col_max - col_min == 0:
                dataset[col+"_norm"] = 0.0
            else:
                dataset[col+"_norm"] = (
                    (dataset[col] - col_min) /
                    (col_max - col_min + 1e-6)
                ) * 100
                
        return dataset
    except Exception as e:
        st.error(f"⚠️ **정규화 오류:** {e}")
        return None


# ============================================================
# 스트림릿 웹 화면 UI
# ============================================================
st.title("📊 영천 대기/환경 데이터 맞춤형 전처리 프로그램")
st.markdown("하나의 파일로 **파생변수 생성 ➡️ 재질·노출 조합 확장 ➡️ 0~100 정규화**까지 원스톱으로 처리합니다.")

uploaded_file = st.file_uploader("CSV 파일을 업로드해주세요.", type=["csv"])

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 1. 원본 데이터")
        st.caption(f"행: {raw_df.shape[0]:,}개 / 열: {raw_df.shape[1]:,}개")
        st.dataframe(raw_df.head(5), use_container_width=True)
    
    # 1단계 파생변수 작동 (자동)
    processed_df = create_derived_features(raw_df)
    
    if processed_df is not None:
        with col2:
            st.subheader("🚀 2. 파생변수 생성 완료 (미리보기)")
            st.caption(f"행: {processed_df.shape[0]:,}개 / 열: {processed_df.shape[1]:,}개")
            st.dataframe(processed_df.head(5), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🧱 3. 최종 데이터셋 변환 (조합 + 정규화 100)")
        st.info("아래 버튼을 누르면 재질×노출 조건이 결합되고, 리스크 지표가 **0~100 사이로 정규화(`_norm`)**됩니다.")
        
        if st.button("🔥 최종 통합 데이터셋 생성하기"):
            final_dataset = generate_combinations_and_normalize(processed_df)
            
            if final_dataset is not None:
                st.success(f"✅ 전처리 완료! 최종 데이터가 총 {final_dataset.shape[0]:,}행으로 생성되었습니다.")
                st.dataframe(final_dataset.head(10), use_container_width=True)
                
                final_csv = final_dataset.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 최종 전처리 완료 데이터(CSV) 다운로드",
                    data=final_csv,
                    file_name="final_processed_normalized_data.csv",
                    mime="text/csv"
                )
else:
    st.info("💡 시작하려면 영천 기상 데이터 CSV 파일을 업로드해 주세요.")
