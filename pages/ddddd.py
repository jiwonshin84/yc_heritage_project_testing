import streamlit as st

# ============================================================
# 0. Streamlit 레이아웃 설정
# ============================================================
st.set_page_config(
    page_title="영천 문화재 위험도 예측 시스템",
    layout="wide"
)

import itertools
import os
import platform
import subprocess
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import requests

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


# ============================================================
# 1. Matplotlib 한글 폰트 설정
# ============================================================
def set_korean_font():

    system_name = platform.system()

    if system_name == "Windows":

        plt.rc("font", family="Malgun Gothic")

    elif system_name == "Darwin":

        plt.rc("font", family="AppleGothic")

    else:

        # Streamlit Cloud / Linux
        font_path = (
            "/usr/share/fonts/truetype/nanum/"
            "NanumGothic.ttf"
        )

        if not os.path.exists(font_path):

            try:
                subprocess.run(
                    ["apt-get", "update"],
                    check=False
                )

                subprocess.run(
                    ["apt-get", "install", "-y", "fonts-nanum"],
                    check=False
                )

            except Exception:
                pass

        if os.path.exists(font_path):

            font_prop = fm.FontProperties(
                fname=font_path
            )

            fm.fontManager.addfont(
                font_path
            )

            plt.rc(
                "font",
                family=font_prop.get_name()
            )

        else:

            plt.rc(
                "font",
                family="DejaVu Sans"
            )

    plt.rc(
        "axes",
        unicode_minus=False
    )


set_korean_font()


# ============================================================
# 2. 제목
# ============================================================
st.title(
    "🏛️ 영천시 문화재 환경 위험도 실시간 예측 시스템"
)


# ============================================================
# 3. 기상청 ASOS API 설정
# ============================================================
#
# Streamlit Cloud의 Secrets에 아래와 같이 등록해야 합니다.
#
# SERVICE_KEY = "기상청_API_인증키"
#
# 코드에 API 키를 직접 넣지 않습니다.
# ============================================================

try:

    ASOS_SERVICE_KEY = st.secrets["SERVICE_KEY"]

except Exception:

    ASOS_SERVICE_KEY = ""


if not ASOS_SERVICE_KEY:

    st.error(
        "SERVICE_KEY가 설정되지 않았습니다."
    )

    st.info(
        "Streamlit Cloud → Manage app → Settings → Secrets에서 "
        "SERVICE_KEY를 등록해주세요."
    )

    st.code(
        'SERVICE_KEY = "feb2bfabd299d5d05e89c7aec49ba7e706112603e76549a92e868bd86ec60323"',
        language="toml"
    )

    st.stop()


ASOS_URL = (
    "http://apis.data.go.kr/1360000/"
    "AsosDalyInfoService/getWthrDataList"
)

STN_ID = "281"  # 영천 관측소


# ============================================================
# 4. 연도별 기상 데이터 가져오기
# ============================================================
def fetch_asos_year(year):

    current_year = datetime.now().year

    start_dt = f"{year}0101"

    if year == current_year:

        end_dt = (
            datetime.now()
            - timedelta(days=1)
        ).strftime("%Y%m%d")

    else:

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
        "stnIds": STN_ID,
    }


    try:

        response = requests.get(
            ASOS_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        result = response.json()

        items = (
            result
            ["response"]
            ["body"]
            ["items"]
            ["item"]
        )

        return pd.DataFrame(items)

    except Exception:

        return pd.DataFrame()


# ============================================================
# 5. 전체 기상 + 대기 데이터 처리
# ============================================================
@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def load_and_process_data():

    all_years = []

    current_year = datetime.now().year

    years = list(
        range(
            2016,
            current_year + 1
        )
    )


    # --------------------------------------------------------
    # 기상청 데이터 수집
    # --------------------------------------------------------
    progress_bar = st.progress(
        0,
        text="기상청 과거 데이터 수집 중..."
    )


    for idx, year in enumerate(years):

        df_year = fetch_asos_year(
            year
        )

        if not df_year.empty:

            all_years.append(
                df_year
            )


        progress = int(
            (idx + 1)
            / len(years)
            * 100
        )

        progress_bar.progress(
            progress,
            text=(
                f"기상 데이터 수집 중... "
                f"({year}년)"
            )
        )


    progress_bar.empty()


    # --------------------------------------------------------
    # 데이터가 하나도 없으면 종료
    # --------------------------------------------------------
    if not all_years:

        return (
            pd.DataFrame(),
            ""
        )


    weather_raw = pd.concat(
        all_years,
        ignore_index=True
    )


    # --------------------------------------------------------
    # 필요한 기상 변수
    # --------------------------------------------------------
    required_weather_columns = [
        "tm",
        "avgTa",
        "maxTa",
        "minTa",
        "avgRhm",
        "sumRn",
        "avgWs",
        "sumSsHr",
        "avgTs"
    ]


    missing_columns = [
        col
        for col in required_weather_columns
        if col not in weather_raw.columns
    ]


    if missing_columns:

        return (
            pd.DataFrame(),
            ""
        )


    weather = weather_raw[
        required_weather_columns
    ].copy()


    weather.columns = [
        "date",
        "temp_avg",
        "temp_max",
        "temp_min",
        "humidity",
        "rainfall",
        "wind_speed",
        "solar_radiation",
        "ground_temp"
    ]


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


    weather["rainfall"] = (
        weather["rainfall"]
        .fillna(0)
    )


    weather = (
        weather
        .dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )


    # ========================================================
    # 6. 대기오염 데이터
    # ========================================================
    air_url = (
        "https://docs.google.com/spreadsheets/d/"
        "1fBEnheVOP-23Hmv_5ZJZVy6m9VmNkpVd2XutOdmlYc8/"
        "export?format=csv&gid=700055413"
    )


    try:

        air = pd.read_csv(
            air_url
        )

        air["date"] = pd.to_datetime(
            air["date"],
            errors="coerce"
        )

    except Exception:

        air = pd.DataFrame(
            columns=[
                "date",
                "pm10",
                "pm25",
                "o3",
                "no2",
                "co",
                "so2"
            ]
        )


    air_cols = [
        "pm10",
        "pm25",
        "o3",
        "no2",
        "co",
        "so2"
    ]


    for col in air_cols:

        if col not in air.columns:

            air[col] = 0.0


        air[col] = pd.to_numeric(
            air[col],
            errors="coerce"
        )


    # ========================================================
    # 7. 기상 + 대기 병합
    # ========================================================
    df = pd.merge(
        weather,
        air,
        on="date",
        how="left"
    )


    for col in air_cols:

        if col not in df.columns:

            df[col] = 0.0


        df[col] = (
            df[col]
            .fillna(0)
        )


    # ========================================================
    # 8. 환경 위험 파생변수
    # ========================================================
    df["temp_range"] = (
        df["temp_max"]
        - df["temp_min"]
    )


    df["humidity_std3"] = (
        df["humidity"]
        .rolling(
            3,
            min_periods=1
        )
        .std()
        .fillna(0)
    )


    df["rainfall_7d"] = (
        df["rainfall"]
        .rolling(
            7,
            min_periods=1
        )
        .sum()
    )


    df["high_humidity_risk"] = (
        (
            df["humidity"] >= 75
        )
        .rolling(
            3,
            min_periods=1
        )
        .sum()
    )


    df["weathering_risk"] = (
        df["temp_range"] * 0.4
        + df["humidity_std3"] * 0.3
        + df["wind_speed"] * 0.3
    )


    df["mold_risk"] = (
        (
            (df["humidity"] >= 75)
            &
            (df["ground_temp"] >= 15)
        )
        .astype(int)
    )


    df["pm_load"] = (
        (
            df["pm10"]
            + df["pm25"]
        )
        .rolling(
            3,
            min_periods=1
        )
        .sum()
    )


    df["acid_risk"] = (
        df["so2"] * 0.6
        + df["no2"] * 0.4
    )


    df["oxidation_risk"] = (
        df["o3"] * 0.7
        + df["pm25"] * 0.3
    )


    df["corrosion_risk"] = (
        df["humidity"] * 0.5
        + df["so2"] * 0.5
    )


    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )


    df = df.fillna(0)


    # ========================================================
    # 9. 재질 × 노출형태 조합
    # ========================================================
    materials = [
        "석조",
        "목조",
        "금속",
        "회화",
        "기타"
    ]


    exposures = [
        "실외",
        "반실외",
        "실내"
    ]


    comb = pd.DataFrame(
        list(
            itertools.product(
                materials,
                exposures
            )
        ),
        columns=[
            "material",
            "exposure"
        ]
    )


    df["key"] = 1
    comb["key"] = 1


    dataset = pd.merge(
        df,
        comb,
        on="key"
    ).drop(
        "key",
        axis=1
    )


    # ========================================================
    # 10. 위험요인 정규화
    # ========================================================
    norm_targets = [
        "weathering_risk",
        "acid_risk",
        "rainfall_7d",
        "temp_range",
        "pm_load",
        "corrosion_risk",
        "mold_risk",
        "humidity_std3",
        "high_humidity_risk",
        "oxidation_risk"
    ]


    for target in norm_targets:

        min_v = dataset[
            target
        ].min()

        max_v = dataset[
            target
        ].max()


        if max_v - min_v == 0:

            dataset[
                f"{target}_norm"
            ] = 0

        else:

            dataset[
                f"{target}_norm"
            ] = (
                dataset[target] - min_v
            ) / (
                max_v - min_v
            )


    # ========================================================
    # 11. 재질별 위험도 계산
    # ========================================================
    def calc_risk(row):

        material = row["material"]

        exposure = row["exposure"]


        if material == "석조":

            risk = (
                row["weathering_risk_norm"] * 0.25
                + row["acid_risk_norm"] * 0.20
                + row["rainfall_7d_norm"] * 0.18
                + row["temp_range_norm"] * 0.15
                + row["pm_load_norm"] * 0.12
                + row["corrosion_risk_norm"] * 0.10
            )


        elif material == "목조":

            risk = (
                row["mold_risk_norm"] * 0.25
                + row["humidity_std3_norm"] * 0.20
                + row["high_humidity_risk_norm"] * 0.18
                + row["rainfall_7d_norm"] * 0.15
                + row["oxidation_risk_norm"] * 0.12
                + row["pm_load_norm"] * 0.10
            )


        elif material == "금속":

            risk = (
                row["corrosion_risk_norm"] * 0.30
                + row["acid_risk_norm"] * 0.22
                + row["high_humidity_risk_norm"] * 0.18
                + row["humidity_std3_norm"] * 0.12
                + row["pm_load_norm"] * 0.10
                + row["weathering_risk_norm"] * 0.08
            )


        elif material == "회화":

            risk = (
                row["oxidation_risk_norm"] * 0.28
                + row["pm_load_norm"] * 0.20
                + row["humidity_std3_norm"] * 0.18
                + row["high_humidity_risk_norm"] * 0.14
                + row["temp_range_norm"] * 0.10
                + row["weathering_risk_norm"] * 0.10
            )


        else:

            risk = (
                row["weathering_risk_norm"] * 0.20
                + row["acid_risk_norm"] * 0.20
                + row["oxidation_risk_norm"] * 0.20
                + row["corrosion_risk_norm"] * 0.20
                + row["pm_load_norm"] * 0.20
            )


        # 노출형태 반영
        if exposure == "실외":

            risk *= 1.3

        elif exposure == "반실외":

            risk *= 1.1

        else:

            risk *= 0.85


        return min(
            risk * 100,
            100
        )


    dataset["material_risk"] = (
        dataset.apply(
            calc_risk,
            axis=1
        )
    )


    # ========================================================
    # 12. 위험등급 생성
    # ========================================================
    q75 = dataset[
        "material_risk"
    ].quantile(0.75)


    q40 = dataset[
        "material_risk"
    ].quantile(0.40)


    def label(x):

        if x >= q75:

            return "위험"

        elif x >= q40:

            return "주의"

        else:

            return "안전"


    dataset["target"] = (
        dataset["material_risk"]
        .apply(label)
    )


    return dataset, air_url


# ============================================================
# 13. 데이터 불러오기
# ============================================================
dataset, air_url = (
    load_and_process_data()
)


# ============================================================
# 14. 데이터 수집 실패 확인
# ============================================================
if dataset.empty:

    st.error(
        "기상청 데이터를 불러오지 못했습니다."
    )

    st.warning(
        "기상청 API 인증키 또는 API 응답 상태를 확인해주세요."
    )

    st.stop()


# ============================================================
# 15. 머신러닝 데이터 생성
# ============================================================
X = dataset[
    [
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
        "corrosion_risk",
        "material",
        "exposure"
    ]
].copy()


y = dataset[
    "target"
].copy()


# ============================================================
# 16. One-Hot Encoding
# ============================================================
X = pd.get_dummies(
    X,
    columns=[
        "material",
        "exposure"
    ]
)


# 결측값 처리
X = X.replace(
    [np.inf, -np.inf],
    np.nan
)

X = X.fillna(0)


# ============================================================
# 17. 위험등급 분포 확인
# ============================================================
class_counts = (
    y.value_counts()
)


if len(class_counts) < 2:

    st.error(
        "위험등급이 2개 미만이라 "
        "머신러닝 학습을 진행할 수 없습니다."
    )

    st.write(
        "현재 위험등급 분포:"
    )

    st.dataframe(
        class_counts
    )

    st.stop()


# ============================================================
# 18. Train / Test 데이터 분할
# ============================================================
#
# 기존 코드:
#
# train_test_split(
#     X,
#     y,
#     test_size=0.2,
#     random_state=42,
#     stratify=y
# )
#
# 데이터가 적거나 클래스 수가 많으면
# ValueError가 발생할 수 있으므로
# 조건을 확인해서 stratify를 적용합니다.
# ============================================================

test_count = max(
    1,
    int(
        np.ceil(
            len(X) * 0.2
        )
    )
)


num_classes = len(
    class_counts
)


min_class_count = class_counts.min()


if (
    min_class_count >= 2
    and test_count >= num_classes
):

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y
        )
    )

    split_method = (
        "층화 추출(stratify) 적용"
    )

else:

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )
    )

    split_method = (
        "일반 무작위 분할 적용"
    )


# ============================================================
# 19. Random Forest 학습
# ============================================================
rf_model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)


rf_model.fit(
    X_train,
    y_train
)


# ============================================================
# 20. 모델 평가
# ============================================================
y_pred = rf_model.predict(
    X_test
)


acc = accuracy_score(
    y_test,
    y_pred
)


st.sidebar.subheader(
    "🤖 모델 성능"
)


st.sidebar.text(
    f"RandomForest 정확도: {acc:.4f}"
)


st.sidebar.text(
    f"학습 데이터: {len(X_train):,}개"
)


st.sidebar.text(
    f"테스트 데이터: {len(X_test):,}개"
)


st.sidebar.text(
    f"분할 방법: {split_method}"
)


# ============================================================
# 21. 전체 환경 요인 중요도 TOP 10
# ============================================================
feature_cols = [
    c
    for c in X_train.columns
    if not c.startswith(
        "material_"
    )
    and not c.startswith(
        "exposure_"
    )
]


importance_df = pd.DataFrame(
    {
        "Feature": X_train.columns,
        "Importance":
            rf_model.feature_importances_
    }
)


importance_df = (
    importance_df[
        importance_df["Feature"].isin(
            feature_cols
        )
    ]
    .sort_values(
        "Importance",
        ascending=False
    )
    .head(10)
    .reset_index(drop=True)
)


st.subheader(
    "🌲 전체 환경 요인 중요도 TOP 10"
)


st.dataframe(
    importance_df,
    use_container_width=True
)


# ============================================================
# 22. 재질별 환경 요인 중요도
# ============================================================
st.header(
    "📊 재질별 주요 환경 위험요인 TOP 10"
)


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


materials_list = [
    "석조",
    "목조",
    "금속",
    "회화"
]


cols = st.columns(2)


for idx, material in enumerate(
    materials_list
):

    sub_df = dataset[
        dataset["material"] == material
    ]


    if len(sub_df) >= 30:

        X_sub = sub_df[
            env_features
        ].copy()


        y_sub = sub_df[
            "target"
        ]


        if len(
            y_sub.unique()
        ) > 1:

            try:

                rf_sub = RandomForestClassifier(
                    n_estimators=300,
                    random_state=42
                )


                rf_sub.fit(
                    X_sub,
                    y_sub
                )


                imp_df = pd.DataFrame(
                    {
                        "Feature":
                            env_features,

                        "Importance":
                            rf_sub.feature_importances_
                    }
                )


                imp_df = (
                    imp_df
                    .sort_values(
                        "Importance",
                        ascending=False
                    )
                    .head(10)
                )


                fig, ax = plt.subplots(
                    figsize=(6, 3.5)
                )


                ax.barh(
                    imp_df["Feature"][::-1],
                    imp_df["Importance"][::-1],
                    color="#2b5c8f"
                )


                ax.set_title(
                    f"[{material}] 문화재 위험요인 TOP 10",
                    fontsize=11
                )


                ax.set_xlabel(
                    "Importance"
                )


                plt.tight_layout()


                with cols[idx % 2]:

                    st.pyplot(fig)

                    plt.close(fig)


            except Exception:

                pass


# ============================================================
# 23. 영천시 문화재 데이터
# ============================================================
st.header(
    "🔍 영천시 문화재 실시간 위험등급 예측"
)


heritage_path = (
    "영천_문화재_특성데이터셋.csv"
)


try:

    heritage_df = pd.read_csv(
        heritage_path
    )


except FileNotFoundError:

    heritage_path_colab = (
        "/content/drive/MyDrive/"
        "00. 2026학년도 인재양성프로젝트/"
        "공공데이터 기반 프로젝트/"
        "dataset/"
        "영천_문화재_특성데이터셋.csv"
    )


    try:

        heritage_df = pd.read_csv(
            heritage_path_colab
        )


    except FileNotFoundError:

        heritage_df = pd.DataFrame(
            {
                "문화재명(국문)": [
                    "영천 은해사 거조암 영산전",
                    "영천 청제비",
                    "영천 신월리 삼층석탑"
                ],

                "재질": [
                    "목조",
                    "석조",
                    "석조"
                ],

                "노출형태": [
                    "반실외",
                    "실외",
                    "실외"
                ]
            }
        )


# ============================================================
# 24. 최근 7일 기상 데이터
# ============================================================
end_date = (
    datetime.now()
    - timedelta(days=1)
)


start_date = (
    end_date
    - timedelta(days=6)
)


params = {
    "serviceKey": ASOS_SERVICE_KEY,
    "numOfRows": "20",
    "pageNo": "1",
    "dataType": "JSON",
    "dataCd": "ASOS",
    "dateCd": "DAY",
    "startDt": start_date.strftime(
        "%Y%m%d"
    ),
    "endDt": end_date.strftime(
        "%Y%m%d"
    ),
    "stnIds": STN_ID,
}


# ============================================================
# 25. 실시간 예측
# ============================================================
try:

    response = requests.get(
        ASOS_URL,
        params=params,
        timeout=10
    )


    response.raise_for_status()


    result = response.json()


    items = (
        result
        ["response"]
        ["body"]
        ["items"]
        ["item"]
    )


    weather_recent = pd.DataFrame(
        items
    )


    required_columns = [
        "tm",
        "avgTa",
        "maxTa",
        "minTa",
        "avgRhm",
        "sumRn",
        "avgWs",
        "sumSsHr",
        "avgTs"
    ]


    weather_recent = weather_recent[
        required_columns
    ].copy()


    weather_recent.columns = [
        "date",
        "temp_avg",
        "temp_max",
        "temp_min",
        "humidity",
        "rainfall",
        "wind_speed",
        "solar_radiation",
        "ground_temp"
    ]


    weather_recent["date"] = pd.to_datetime(
        weather_recent["date"],
        errors="coerce"
    )


    for col in weather_recent.columns[1:]:

        weather_recent[col] = pd.to_numeric(
            weather_recent[col],
            errors="coerce"
        )


    weather_recent = (
        weather_recent
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )


    # ========================================================
    # 26. 최근 대기 데이터
    # ========================================================
    air_recent = pd.read_csv(
        air_url
    )


    air_recent["date"] = pd.to_datetime(
        air_recent["date"],
        errors="coerce"
    )


    for col in [
        "pm10",
        "pm25",
        "o3",
        "no2",
        "co",
        "so2"
    ]:

        if col not in air_recent.columns:

            air_recent[col] = 0


        air_recent[col] = pd.to_numeric(
            air_recent[col],
            errors="coerce"
        )


    air_recent = air_recent[
        air_recent["date"].between(
            start_date,
            end_date
        )
    ]


    # ========================================================
    # 27. 최근 기상 + 대기 병합
    # ========================================================
    recent_df = pd.merge(
        weather_recent,
        air_recent,
        on="date",
        how="left"
    )


    recent_df = (
        recent_df
        .sort_values("date")
        .ffill()
        .fillna(0)
    )


    if recent_df.empty:

        raise ValueError(
            "최근 기상 데이터를 불러오지 못했습니다."
        )


    latest = recent_df.iloc[-1]


    # ========================================================
    # 28. 실시간 위험요인 계산
    # ========================================================
    temp_range = (
        latest["temp_max"]
        - latest["temp_min"]
    )


    humidity_std3 = (
        recent_df[
            "humidity"
        ]
        .tail(3)
        .std()
    )


    if pd.isna(
        humidity_std3
    ):

        humidity_std3 = 0


    rainfall_7d = (
        recent_df[
            "rainfall"
        ]
        .sum()
    )


    high_humidity_risk = int(
        latest["humidity"] >= 75
    )


    weathering_risk = (
        temp_range * 0.4
        + humidity_std3 * 0.3
        + latest["wind_speed"] * 0.3
    )


    mold_risk = int(
        (
            latest["humidity"] >= 75
        )
        and
        (
            latest["ground_temp"] >= 15
        )
    )


    pm_load = (
        latest["pm10"]
        + latest["pm25"]
    )


    acid_risk = (
        latest["so2"] * 0.6
        + latest["no2"] * 0.4
    )


    oxidation_risk = (
        latest["o3"] * 0.7
        + latest["pm25"] * 0.3
    )


    corrosion_risk = (
        latest["humidity"] * 0.5
        + latest["so2"] * 0.5
    )


    # ========================================================
    # 29. 실시간 환경 요약
    # ========================================================
    st.subheader(
        "📌 실시간 수집 기상/대기 요약"
    )


    env_df = pd.DataFrame(
        [
            {
                "기준일자":
                    latest["date"].strftime(
                        "%Y-%m-%d"
                    ),

                "평균기온(℃)":
                    latest["temp_avg"],

                "습도(%)":
                    latest["humidity"],

                "강수량(mm)":
                    latest["rainfall"],

                "미세먼지(PM10)":
                    latest["pm10"],

                "초미세먼지(PM2.5)":
                    latest["pm25"]
            }
        ]
    )


    st.dataframe(
        env_df,
        use_container_width=True
    )


    # ========================================================
    # 30. 문화재별 위험등급 예측
    # ========================================================
    results = []


    for _, heritage in heritage_df.iterrows():

        material = heritage[
            "재질"
        ]

        exposure = heritage[
            "노출형태"
        ]


        # ----------------------------------------------------
        # 예상하지 못한 재질/노출형태 처리
        # ----------------------------------------------------
        if material not in [
            "석조",
            "목조",
            "금속",
            "회화",
            "기타"
        ]:

            material = "기타"


        if exposure not in [
            "실외",
            "반실외",
            "실내"
        ]:

            exposure = "실내"


        # ----------------------------------------------------
        # 예측용 데이터
        # ----------------------------------------------------
        predict_df = pd.DataFrame(
            [
                {
                    "temp_avg":
                        latest["temp_avg"],

                    "temp_max":
                        latest["temp_max"],

                    "temp_min":
                        latest["temp_min"],

                    "humidity":
                        latest["humidity"],

                    "rainfall":
                        latest["rainfall"],

                    "wind_speed":
                        latest["wind_speed"],

                    "solar_radiation":
                        latest["solar_radiation"],

                    "ground_temp":
                        latest["ground_temp"],

                    "pm10":
                        latest["pm10"],

                    "pm25":
                        latest["pm25"],

                    "o3":
                        latest["o3"],

                    "no2":
                        latest["no2"],

                    "co":
                        latest["co"],

                    "so2":
                        latest["so2"],

                    "temp_range":
                        temp_range,

                    "humidity_std3":
                        humidity_std3,

                    "rainfall_7d":
                        rainfall_7d,

                    "high_humidity_risk":
                        high_humidity_risk,

                    "weathering_risk":
                        weathering_risk,

                    "mold_risk":
                        mold_risk,

                    "pm_load":
                        pm_load,

                    "acid_risk":
                        acid_risk,

                    "oxidation_risk":
                        oxidation_risk,

                    "corrosion_risk":
                        corrosion_risk,

                    "material":
                        material,

                    "exposure":
                        exposure
                }
            ]
        )


        # ----------------------------------------------------
        # One-Hot Encoding
        # ----------------------------------------------------
        predict_df = pd.get_dummies(
            predict_df,
            columns=[
                "material",
                "exposure"
            ]
        )


        # 학습 때 사용했던 컬럼과 동일하게 맞춤
        predict_df = predict_df.reindex(
            columns=X_train.columns,
            fill_value=0
        )


        # ----------------------------------------------------
        # 예측
        # ----------------------------------------------------
        prediction = rf_model.predict(
            predict_df
        )[0]


        results.append(
            [
                heritage[
                    "문화재명(국문)"
                ],

                heritage[
                    "재질"
                ],

                heritage[
                    "노출형태"
                ],

                prediction
            ]
        )


    # ========================================================
    # 31. 결과 DataFrame
    # ========================================================
    result_df = pd.DataFrame(
        results,
        columns=[
            "문화재명",
            "재질",
            "노출형태",
            "예측위험등급"
        ]
    )


    # ========================================================
    # 32. 위험등급 분포
    # ========================================================
    st.subheader(
        "📊 예측 위험등급 분포"
    )


    counts = (
        result_df[
            "예측위험등급"
        ]
        .value_counts()
        .reindex(
            [
                "위험",
                "주의",
                "안전"
            ],
            fill_value=0
        )
    )


    fig, ax = plt.subplots(
        figsize=(7, 3.5)
    )


    chart_colors = {
        "위험": "#d9534f",
        "주의": "#f0ad4e",
        "안전": "#5cb85c"
    }


    bar_colors = [
        chart_colors[x]
        for x in counts.index
    ]


    bars = ax.bar(
        counts.index,
        counts.values,
        color=bar_colors,
        edgecolor="black",
        width=0.4
    )


    ax.set_title(
        "영천시 문화재 위험등급별 수량",
        fontsize=12,
        pad=10
    )


    ax.set_ylabel(
        "수량 (개)",
        fontsize=10
    )


    for bar in bars:

        height = bar.get_height()

        ax.annotate(
            f"{height}",
            xy=(
                bar.get_x()
                + bar.get_width() / 2,
                height
            ),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10
        )


    plt.tight_layout()


    st.pyplot(fig)


    plt.close(fig)


    # ========================================================
    # 33. 등급별 문화재 목록
    # ========================================================
    st.markdown("---")


    for level in [
        "위험",
        "주의",
        "안전"
    ]:

        sub_df = result_df[
            result_df[
                "예측위험등급"
            ] == level
        ].copy()


        if level == "위험":

            icon = "🚨"

        elif level == "주의":

            icon = "⚠️"

        else:

            icon = "✅"


        st.subheader(
            f"{icon} [{level} 등급] "
            f"문화재 목록 "
            f"(총 {len(sub_df)}건)"
        )


        if len(sub_df) > 0:

            display_df = (
                sub_df[
                    [
                        "문화재명",
                        "재질",
                        "노출형태"
                    ]
                ]
                .reset_index(
                    drop=True
                )
            )


            display_df.index = (
                display_df.index + 1
            )


            display_df.index.name = (
                "번호"
            )


            st.dataframe(
                display_df,
                use_container_width=True
            )


        else:

            st.info(
                f"현재 기상 조건상 "
                f"'{level}' 등급에 해당되는 "
                f"문화재가 없습니다."
            )


# ============================================================
# 34. 실시간 예측 오류 처리
# ============================================================
except Exception as e:

    st.error(
        "실시간 위험도 예측 중 오류가 발생했습니다."
    )

    st.exception(e)
