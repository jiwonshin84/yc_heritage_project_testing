import streamlit as st
import pandas as pd
import numpy as np

# 페이지 기본 설정
st.set_page_config(page_title="환경 파생변수 생성기", layout="wide")

# ============================================================
# 데이터 처리 함수 (스트림릿 최적화 및 오류 방안 완벽 보완)
# ============================================================
@st.cache_data(show_spinner="파생변수를 계산하고 있습니다...")
def create_derived_features(dataframe):
    """
    스트림릿 캐싱을 적용하고, 데이터 훼손 방지를 위해 복사본(copy)을 사용합니다.
    데이터 검증 로직을 거쳐 안전하게 파생변수를 생성합니다.
    """
    # 1. 원본 데이터 보호를 위해 사본 생성
    df = dataframe.copy()
    
    # 2. 필수 컬럼 및 데이터 타입 체크
    required_cols = [
        "temp_max", "temp_min", "humidity", "rainfall", "wind_speed", 
        "ground_temp", "pm10", "pm25", "so2", "no2", "o3"
    ]
    
    # 누락된 컬럼 확인
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"⚠️ **오류:** 데이터에 다음 필수 컬럼이 누락되었습니다: `{missing_cols}`")
        return None

    # 데이터 타입 검증 (숫자형이 아닌 문자열이 섞여있으면 계산 오류가 발생하므로 강제 형변환)
    try:
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    except Exception as e:
        st.error(f"⚠️ **오류:** 데이터를 숫자로 변환하는 중 문제가 발생했습니다: {e}")
        return None

    # 계산 전 데이터에 존재할 수 있는 빈 값(NaN)을 0으로 1차 방어
    df[required_cols] = df[required_cols].fillna(0)

    try:
        # ============================================================
        # 7. 파생변수 생성 (원본 로직 유지)
        # ============================================================
        df["temp_range"] = df["temp_max"] - df["temp_min"]

        # rolling().std()의 경우 데이터가 1개일 때 NaN이 발생하므로 확실한 방어 필요
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

        # 3. 계산 과정(rolling 연산 등)에서 발생한 최종 결측치 처리 (0으로 대체)
        df = df.fillna(0)
        
        return df

    except Exception as e:
        st.error(f"⚠️ **연산 오류:** 파생변수 계산 도중 오류가 발생했습니다: {e}")
        return None


# ============================================================
# 스트림릿 웹 화면 UI 구성
# ============================================================
st.title("📊 날씨 및 환경 파생변수 생성 프로그램")
st.markdown("업로드한 기상/대기 데이터셋에 분석용 파생변수 10종을 자동으로 추가해 줍니다.")

# 1. 파일 업로드 섹션
uploaded_file = st.file_uploader("CSV 파일을 업로드해주세요.", type=["csv"])

if uploaded_file is not None:
    # 데이터 로드
    raw_df = pd.read_csv(uploaded_file)
    
    # 화면을 좌우 2분할하여 보기 좋게 배치
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 1. 원본 데이터 미리보기")
        st.caption(f"총 행 수: {raw_df.shape[0]}개 / 총 열 수: {raw_df.shape[1]}개")
        st.dataframe(raw_df.head(10), use_container_width=True)
    
    # 파생변수 변환 실행
    processed_df = create_derived_features(raw_df)
    
    # 성공적으로 변환되었을 때만 결과 표출
    if processed_df is not None:
        with col2:
            st.subheader("🚀 2. 파생변수 생성 결과")
            st.caption(f"총 행 수: {processed_df.shape[0]}개 / 총 열 수: {processed_df.shape[1]}개 (파생변수 추가 완료)")
            st.dataframe(processed_df.head(10), use_container_width=True)
        
        # 파일 다운로드 영역
        st.success("✅ 모든 파생변수가 오류 없이 성공적으로 연산되었습니다!")
        
        # CSV 변환 시 한글 깨짐 방지를 위해 utf-8-sig 사용
        csv_data = processed_df.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📥 변환된 결과 데이터(CSV) 다운로드",
            data=csv_data,
            file_name="environment_derived_data.csv",
            mime="text/csv",
        )
else:
    # 파일이 업로드되지 않았을 때 안내 안내 가이드
    st.info("💡 시작하려면 상단의 업로드 창에 기상/대기 데이터가 포함된 CSV 파일을 넣어주세요.")
    st.markdown("""
    **필요한 데이터 컬럼 목록:**
    `temp_max`, `temp_min`, `humidity`, `rainfall`, `wind_speed`, `ground_temp`, `pm10`, `pm25`, `so2`, `no2`, `o3`
    """)
