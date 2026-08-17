import streamlit as st
import pandas as pd
import numpy as np
import itertools

# 페이지 기본 설정 (멀티페이지 안에서 개별 레이아웃 설정)
st.set_page_config(page_title="환경 파생변수 및 조합 생성기", layout="wide")

# ============================================================
# 1. 파생변수 생성 함수 (캐싱 적용)
# ============================================================
@st.cache_data(show_spinner="파생변수를 계산하고 있습니다...")
def create_derived_features(dataframe):
    df = dataframe.copy()
    
    required_cols = [
        "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", 
        "ground_temp", "pm10", "pm25", "so2", "no2", "o3"
    ]
    
    # 필수 컬럼 존재 여부 체크
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"⚠️ **오류:** 업로드된 데이터에 다음 필수 컬럼이 누락되었습니다: `{missing_cols}`")
        return None

    # 데이터 타입 숫자형 강제 변환 및 결측치 1차 처리
    try:
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df[required_cols] = df[required_cols].fillna(0)
    except Exception as e:
        st.error(f"⚠️ **오류:** 데이터를 숫자로 변환하는 중 문제가 발생했습니다: {e}")
        return None

    try:
        # 파생변수 연산
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

        # 최종 결측치 처리
        df = df.fillna(0)
        return df
    except Exception as e:
        st.error(f"⚠️ **연산 오류:** 파생변수 계산 도중 오류가 발생했습니다: {e}")
        return None

# ============================================================
# 2. 재질 × 노출 조합 생성 함수 (캐싱 적용)
# ============================================================
@st.cache_data(show_spinner="재질 및 노출 조건별 조합 데이터셋을 생성 중입니다...")
def generate_material_exposure_combinations(dataframe):
    df = dataframe.copy()
    
    materials = ["석조", "목조", "금속", "회화", "기타"]
    exposures = ["실외", "반실외", "실내"]
    
    expected_rows = len(df) * len(materials) * len(exposures)
    if expected_rows > 3000000:
        st.warning(f"⚠️ 생성될 데이터가 총 {expected_rows:,}행으로 매우 큽니다. 브라우저가 일시적으로 느려질 수 있습니다.")

    try:
        comb = pd.DataFrame(
            list(itertools.product(materials, exposures)),
            columns=["material", "exposure"]
        )
        
        df["key"] = 1
        comb["key"] = 1
        
        dataset = pd.merge(df, comb, on="key").drop("key", axis=1)
        return dataset
    except Exception as e:
        st.error(f"⚠️ **조합 오류:** 조합 생성 중 오류가 발생했습니다: {e}")
        return None


# ============================================================
# 스트림릿 UI 메인 레이아웃
# ============================================================
st.title("📊 날씨 및 환경 파생변수 생성 프로그램")
st.markdown("업로드한 기상/대기 데이터셋에 파생변수 10종 및 재질×노출 조합을 자동으로 생성합니다.")

# 1. 파일 업로드
uploaded_file = st.file_uploader("CSV 파일을 업로드해주세요.", type=["csv"])

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 1. 원본 데이터 미리보기")
        st.caption(f"행: {raw_df.shape[0]:,}개 / 열: {raw_df.shape[1]:,}개")
        st.dataframe(raw_df.head(10), use_container_width=True)
    
    # 1단계: 파생변수 생성
    processed_df = create_derived_features(raw_df)
    
    if processed_df is not None:
        with col2:
            st.subheader("🚀 2. 파생변수 생성 완료")
            st.caption(f"행: {processed_df.shape[0]:,}개 / 열: {processed_df.shape[1]:,}개")
            st.dataframe(processed_df.head(10), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🧱 3. 재질 × 노출 조합 최종 결합")
        st.info("아래 버튼을 누르면 [재질 5종 × 노출 3종]이 결합되어 데이터가 15배 확장됩니다.")
        
        # 2단계: 조합 결합 버튼 클릭 시 실행
        if st.button("🔥 최종 조합 데이터셋 생성하기"):
            final_dataset = generate_material_exposure_combinations(processed_df)
            
            if final_dataset is not None:
                st.success(f"✅ 최종 완료! 데이터가 총 {final_dataset.shape[0]:,}행으로 확장되었습니다.")
                st.dataframe(final_dataset.head(15), use_container_width=True)
                
                # 다운로드 버튼 (한글 깨짐 방지 인코딩 적용)
                final_csv = final_dataset.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 최종 조합 데이터(CSV) 다운로드",
                    data=final_csv,
                    file_name="final_environment_combination_data.csv",
                    mime="text/csv"
                )
else:
    st.info("💡 시작하려면 상단의 업로드 창에 기상/대기 데이터가 포함된 CSV 파일을 넣어주세요.")
    st.markdown("""
    **필수 포함 컬럼 리스트:**  
    `temp_max`, `temp_min`, `humidity`, `rainfall`, `wind_speed`, `ground_temp`, `pm10`, `pm25`, `so2`, `no2`, `o3`
    """)
