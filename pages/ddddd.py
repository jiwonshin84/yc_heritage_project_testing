# ============================================================
# 0. 라이브러리
# ============================================================

import os
import time
import requests
import pandas as pd
import streamlit as st  # Streamlit 라이브러리 추가

# 화면 타이틀 설정
st.title("☀️ 영천 기상 & 미세먼지 데이터 수집기")


# ============================================================
# 1. 기상청 ASOS API 설정
# ============================================================

# GitHub Secrets에 등록한 API 키 불러오기
ASOS_SERVICE_KEY = os.getenv("ASOS_SERVICE_KEY")

if not ASOS_SERVICE_KEY:
    ASOS_SERVICE_KEY = "feb2bfabd299d5d05e89c7aec49ba7e706112603e76549a92e868bd86ec60323"

ASOS_URL = (
    "http://apis.data.go.kr/"
    "1360000/AsosDalyInfoService/getWthrDataList"
)

# 영천 관측소
STN_ID = "281"


# ============================================================
# 2. 연도별 기상 데이터 수집 함수
# ============================================================

def fetch_asos_year(year):

    start_dt = f"{year}0101"
    end_dt = f"{year}1231"

    params = {
        "serviceKey": ASOS_SERVICE_KEY,

        "numOfRows": "400",
        "pageNo": "1",

        "dataType": "JSON",

        "dataCd": "ASOS",
        "dateCd": "DAY",

        "startDt": start_dt,
        "endDt": end_dt,

        "stnIds": STN_ID
    }

    try:

        response = requests.get(
            ASOS_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        items = result["response"]["body"]["items"]["item"]

        df = pd.DataFrame(items)

        print(
            f"{year}년 수집 완료 : "
            f"{len(df)}건"
        )

        return df

    except Exception as e:

        print(
            f"{year}년 수집 실패 : {e}"
        )

        return pd.DataFrame()


# ============================================================
# 3. 전체 기상 데이터 수집
# ============================================================

st.subheader("1. 기상 데이터 수집 중...")
progress_bar = st.progress(0)
status_text = st.empty()

all_years = []
years = list(range(2016, 2026))

for idx, year in enumerate(years):

    status_text.text(f"⏳ {year}년 기상 데이터 수집 중...")
    df_year = fetch_asos_year(year)

    if not df_year.empty:
        all_years.append(df_year)

    # 진행 바 업데이트
    progress_bar.progress((idx + 1) / len(years))

    # API 과부하 방지
    time.sleep(0.5)

status_text.text("✅ 연도별 기상 데이터 수집 완료!")


# 데이터가 하나도 없는 경우
if not all_years:

    st.error("기상 데이터를 하나도 가져오지 못했습니다.")
    raise ValueError(
        "기상 데이터를 하나도 가져오지 못했습니다."
    )


weather_raw = pd.concat(
    all_years,
    ignore_index=True
)


# ============================================================
# 4. 필요한 컬럼 추출
# ============================================================

weather = weather_raw[
    [
        "tm",

        # 기온
        "avgTa",
        "maxTa",
        "minTa",

        # 습도
        "avgRhm",

        # 강수량
        "sumRn",

        # 풍속
        "avgWs",

        # 일사량
        "sumSsHr",

        # 지면온도
        "avgTs"
    ]
].copy()


# ============================================================
# 5. 컬럼명 변경
# ============================================================

weather.columns = [

    "date",

    # 기온
    "temp_avg",
    "temp_max",
    "temp_min",

    # 습도
    "humidity",

    # 강수량
    "rainfall",

    # 풍속
    "wind_speed",

    # 일사량
    "solar_radiation",

    # 지면온도
    "ground_temp"
]


# ============================================================
# 6. 날짜 및 숫자 데이터 타입 변환
# ============================================================

weather["date"] = pd.to_datetime(
    weather["date"],
    errors="coerce"
)


numeric_cols = [

    "temp_avg",
    "temp_max",
    "temp_min",

    "humidity",

    "rainfall",

    "wind_speed",

    "solar_radiation",

    "ground_temp"
]


for col in numeric_cols:

    weather[col] = pd.to_numeric(
        weather[col],
        errors="coerce"
    )


# ============================================================
# 7. 강수량 결측값 처리
# ============================================================

weather["rainfall"] = (
    weather["rainfall"]
    .fillna(0)
)


# ============================================================
# 8. 정렬 및 결측 제거
# ============================================================

weather = (
    weather
    .dropna(subset=["date"])
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# 9. 미세먼지 데이터 불러오기
# ============================================================

st.subheader("2. 미세먼지 데이터 불러오기")

air_url = (
    "https://docs.google.com/spreadsheets/d/"
    "1fBEnheVOP-23Hmv_5ZJZVy6m9VmNkpVd2XutOdmlYc8/"
    "export?format=csv&gid=700055413"
)


try:

    air = pd.read_csv(
        air_url
    )

except Exception as e:

    st.error(f"미세먼지 데이터를 불러오지 못했습니다 : {e}")
    raise ValueError(
        f"미세먼지 데이터를 불러오지 못했습니다 : {e}"
    )


air["date"] = pd.to_datetime(
    air["date"],
    errors="coerce"
)


# ============================================================
# 10. 기상 + 미세먼지 데이터 병합
# ============================================================

df = pd.merge(

    weather,

    air,

    on="date",

    how="left"
)


# ============================================================
# 12. 데이터 저장
# ============================================================

# GitHub 프로젝트 내부에 data 폴더 생성
os.makedirs(
    "data",
    exist_ok=True
)


save_path = (
    "data/"
    "yeongcheon_2016_2025.csv"
)


df.to_csv(

    save_path,

    index=False,

    encoding="utf-8-sig"
)


# ============================================================
# 13. 완료 및 Streamlit 화면 출력
# ============================================================

st.success(f"🎉 데이터 수집 및 저장 완료! (총 {len(df)}건)")

# 요약 정보 표
col1, col2 = st.columns(2)
col1.metric("최종 행 수", f"{df.shape[0]} 행")
col2.metric("최종 열 수", f"{df.shape[1]} 열")

st.subheader("📊 최종 데이터 미리보기")
st.dataframe(df.head(10), use_container_width=True)

# 결측치 정보 보여주기
with st.expander("🔍 컬럼별 결측치(Null) 개수 확인"):
    st.dataframe(df.isna().sum().to_frame(name="결측치 수"))

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



# ============================================================
# 14. 변수 중요도 분석 (재질·노출 제외)
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.ensemble import RandomForestClassifier


best_model = trained_models[best_model_name]

# 재질·노출 관련 컬럼 제거
feature_cols = [
    c for c in X_train.columns
    if not c.startswith("material_")
    and not c.startswith("exposure_")
    and c != "material"
    and c != "exposure"
]

# 중요도 계산
if best_model_name == "LogisticRegression":

    lr_model, scaler = best_model

    importance_df = pd.DataFrame({
        "Feature": X_train.columns,
        "Importance": np.mean(
            np.abs(lr_model.coef_),
            axis=0
        )
    })

else:

    importance_df = pd.DataFrame({
        "Feature": X_train.columns,
        "Importance": best_model.feature_importances_
    })

# 재질·노출 제거
importance_df = importance_df[
    importance_df["Feature"].isin(feature_cols)
]

# 중요도 순으로 정렬
importance_df = importance_df.sort_values(
    "Importance",
    ascending=False
)

# 상위 10개
top10 = importance_df.head(10)

st.subheader("🌦️ 환경 요인 중요도 TOP 10")

st.dataframe(
    top10,
    use_container_width=True
)

fig, ax = plt.subplots(figsize=(8, 5))

ax.barh(
    top10["Feature"],
    top10["Importance"]
)

ax.invert_yaxis()
ax.set_xlabel("Importance")
ax.set_title("Environmental Feature Importance")

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)


# ============================================================
# 15. 재질별 환경요인 중요도 분석
# ============================================================

env_features = [
    "temp_avg",
    "temp_max",
    "temp_min",
    "humidity",
    "rainfall",
    "wind_speed",
    "solar_radiation",
    "ground_temp",
    "pm10",
    "pm25",
    "o3",
    "no2",
    "co",
    "so2",
    "temp_range",
    "humidity_std3",
    "rainfall_7d",
    "high_humidity_risk",
    "weathering_risk",
    "mold_risk",
    "pm_load",
    "acid_risk",
    "oxidation_risk",
    "corrosion_risk"
]

materials = [
    "석조",
    "목조",
    "금속",
    "회화"
]

st.header("🧱 재질별 환경요인 중요도 분석")

for material in materials:

    st.subheader(f"📌 {material} 문화재")

    # 해당 재질만 추출
    sub_df = dataset[
        dataset["material"] == material
    ].copy()

    # 데이터가 너무 적으면 건너뜀
    if len(sub_df) < 30:

        st.warning(
            f"{material} 문화재는 데이터가 부족합니다."
        )

        continue

    X_sub = sub_df[env_features]
    y_sub = sub_df["target"]

    # Random Forest 모델 학습
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42
    )

    model.fit(
        X_sub,
        y_sub
    )

    # 중요도 계산
    material_importance_df = pd.DataFrame({
        "Feature": env_features,
        "Importance": model.feature_importances_
    })

    material_importance_df = (
        material_importance_df
        .sort_values(
            "Importance",
            ascending=False
        )
    )

    # 상위 10개
    material_top10 = material_importance_df.head(10)

    st.dataframe(
        material_top10,
        use_container_width=True
    )

    # 시각화
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.barh(
        material_top10["Feature"][::-1],
        material_top10["Importance"][::-1]
    )

    ax.set_title(
        f"{material} 문화재 위험요인 TOP 10"
    )

    ax.set_xlabel("Importance")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
