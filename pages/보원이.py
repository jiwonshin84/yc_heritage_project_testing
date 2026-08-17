import streamlit as st
import pandas as pd
import numpy as np
import itertools

# 페이지 기본 설정
st.set_page_config(page_title="환경 데이터 전처리 마스터", layout="wide")

# ============================================================
# 1. 파생변수 생성 함수
# ============================================================
@st.cache_data(show_spinner="1단계: 파생변수를 계산하고 있습니다...")
def create_derived_features(dataframe):
    df = dataframe.copy()
    required_cols = [
        "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", 
        "ground_temp", "pm10", "pm25", "so2", "no2", "o3"
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"⚠️ **오류:** 데이터에 다음 필수 컬럼이 누락되었습니다: `{missing_cols}`")
        return None

    try:
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df[required_cols] = df[required_cols].fillna(0)

        # 7. 파생변수 생성
        df["temp_range"] = df["temp_max"] - df["temp_min"]
        df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std()
        df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()
        df["high_humidity_risk"] = (df["humidity"] >= 75).rolling(3, min_periods=1).sum()
        
        df["weathering_risk"] = (
            df["temp_range"] * 0.4 +
            df["humidity_std3"] * 0.3 +
            df["wind_speed"] * 0.3
        )
        
        df["mold_risk"] = ((df["humidity"] >= 75) & (df["ground_temp"] >= 15)).astype(int)
        df["pm_load"] = (df["pm10"] + df["pm25"]).rolling(3, min_periods=1).sum()
        df["acid_risk"] = df["so2"] * 0.6 + df["no2"] * 0.4
        df["oxidation_risk"] = df["o3"] * 0.7 + df["pm25"] * 0.3
        df["corrosion_risk"] = df["humidity"] * 0.5 + df["so2"] * 0.5

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

    # [9. 정규화 연산 (Min-Max 후 100 곱하기)]
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
            
            # 모든 값이 같아서 분모가 0이 되는 현상 방지하기 (안전장치 추가)
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
st.title("📊 통합 대기/환경 데이터 전처리 프로그램")
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
            # 새로 추가된 변수 위주로 보이게 끝부분 살짝 노출
            st.dataframe(processed_df.head(5), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🧱 3. 최종 데이터셋 변환 (조합 + 정규화 100)")
        st.info("아래 버튼을 누르면 재질×노출 조건이 결합되고, 모든 리스크 지표가 **0~100 사이로 정규화(`_norm`)**됩니다.")
        
        if st.button("🔥 최종 통합 데이터셋 생성하기"):
            # 2단계 & 3단계 결합 함수 호출
            final_dataset = generate_combinations_and_normalize(processed_df)
            
            if final_dataset is not None:
                st.success(f"✅ 전처리 완료! 최종 데이터가 총 {final_dataset.shape[0]:,}행으로 생성되었습니다.")
                
                # 결과 테이블 보여주기
                st.dataframe(final_dataset.head(10), use_container_width=True)
                
                # 다운로드 버튼 (한글 깨짐 방지 utf-8-sig)
                final_csv = final_dataset.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 최종 전처리 완료 데이터(CSV) 다운로드",
                    data=final_csv,
                    file_name="final_processed_normalized_data.csv",
                    mime="text/csv"
                )
else:
    st.info("💡 시작하려면 기상/대기 데이터 CSV 파일을 업로드해 주세요.")
