


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

import streamlit as st
import pandas as pd
import itertools

# 조합 및 병합 연산을 안전하게 처리하는 함수
@st.cache_data(show_spinner="재질 및 노출 조건별 격자 데이터(Cross Product)를 생성 중입니다...")
def generate_material_exposure_combinations(dataframe):
    """
    원본 데이터프레임과 재질(5종) x 노출(3종) 조합을 곱하여 
    분석용 데이터셋(기존 데이터 크기 x 15배)을 안전하게 생성합니다.
    """
    # 1. 원본 데이터 보호를 위해 사본 생성
    df = dataframe.copy()
    
    # 2. 기준 리스트 정의
    materials = ["석조", "목조", "금속", "회화", "기타"]
    exposures = ["실외", "반실외", "실내"]
    
    # 3. 데이터 폭발 방지를 위한 안전장치 (행이 너무 많으면 스트림릿 다운 가능성 존재)
    # 데이터 행 수 * 15가 너무 크면 유저에게 미리 알려주는 것이 안전합니다.
    expected_rows = len(df) * len(materials) * len(exposures)
    if expected_rows > 3000000: # 대략 300만 행 이상일 때 경고
        st.warning(f"⚠️ 생성될 데이터가 총 {expected_rows:,}행으로 매우 큽니다. 브라우저가 일시적으로 느려질 수 있습니다.")

    try:
        # 4. itertools를 활용한 조합 데이터프레임 생성
        comb = pd.DataFrame(
            list(itertools.product(materials, exposures)),
            columns=["material", "exposure"]
        )
        
        # 5. Cross Join (데카르트 곱) 수행
        df["key"] = 1
        comb["key"] = 1
        
        dataset = pd.merge(df, comb, on="key").drop("key", axis=1)
        
        # 원본 데이터프레임에 임시로 만들었던 'key' 컬럼 제거 (Side effect 방지)
        if "key" in df.columns:
            df.drop("key", axis=1, inplace=True)
            
        return dataset

    except Exception as e:
        st.error(f"⚠️ 조합 생성 중 오류가 발생했습니다: {e}")
        return None

# ------------------------------------------------------------
# 스트림릿 UI 연동 예시 (이전 processed_df를 받아서 처리한다고 가정)
# ------------------------------------------------------------
# (기존 코드 생략...)

# processed_df가 성공적으로 만들어진 상태에서 실행
if 'processed_df' in locals() and processed_df is not None:
    st.markdown("---")
    st.subheader("🧱 3. 재질 × 노출 조합 데이터셋 생성")
    
    if st.button("🚀 재질 및 노출 조합 반영한 최종 데이터셋 만들기"):
        # 함수 실행
        final_dataset = generate_material_exposure_combinations(processed_df)
        
        if final_dataset is not None:
            st.success(f"✅ 조합 완료! 데이터가 {processed_df.shape[0]:,}행에서 {final_dataset.shape[0]:,}행으로 확장되었습니다.")
            
            # 결과 확인
            st.subheader("📋 최종 데이터셋 미리보기 (상위 15행)")
            st.dataframe(final_dataset.head(15), use_container_width=True)
            
            # 최종 파일 다운로드
            final_csv = final_dataset.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 최종 조합 데이터(CSV) 다운로드",
                data=final_csv,
                file_name="final_material_exposure_dataset.csv",
                mime="text/csv"
            )
