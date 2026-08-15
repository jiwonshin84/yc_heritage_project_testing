import numpy as np
import pandas as pd

# ============================================================
# 1. 데이터프레임(df) 생성 및 확인
# ============================================================
# 기존 코드에서 df를 불러오는 부분이 있다면 이 자리에 위치해야 합니다.
# 만약 df가 정의되어 있지 않다면 에러 방지를 위해 예시 데이터를 생성합니다.

try:
    df  # df 변수 존재 여부 확인
except NameError:
    # df가 없을 경우 테스트용 더미 데이터 세트 생성
    dates = pd.date_range(start="2026-08-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "temp_max": [30, 32, 31, 29, 28, 33, 34, 31, 30, 29],
            "temp_min": [20, 22, 21, 19, 18, 23, 24, 21, 20, 19],
            "humidity": [70, 78, 80, 65, 76, 82, 74, 70, 68, 77],
            "rainfall": [0, 5, 12, 0, 0, 25, 2, 0, 0, 1],
            "wind_speed": [1.5, 2.0, 1.8, 2.2, 1.1, 3.0, 2.5, 1.7, 1.2, 1.9],
            "ground_temp": [16, 18, 17, 14, 15, 20, 19, 16, 15, 17],
            "pm10": [35, 40, 50, 20, 30, 45, 60, 30, 25, 35],
            "pm25": [15, 20, 25, 10, 15, 22, 30, 15, 12, 18],
            "so2": [0.003, 0.004, 0.003, 0.002, 0.003, 0.005, 0.004, 0.003, 0.002, 0.003],
            "no2": [0.015, 0.020, 0.018, 0.012, 0.015, 0.025, 0.022, 0.016, 0.014, 0.017],
            "o3": [0.030, 0.035, 0.040, 0.025, 0.030, 0.045, 0.050, 0.032, 0.028, 0.033],
        },
        index=dates,
    )

# ============================================================
# 2. 파생변수 생성 (안전한 계산 방식)
# ============================================================

# 일교차
df["temp_range"] = df["temp_max"] - df["temp_min"]

# 습도 3일 이동 표준편차 (첫 행 NaN 방지 처리)
df["humidity_std3"] = df["humidity"].rolling(3, min_periods=1).std().fillna(0)

# 7일 누적 강수량
df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()

# 고습도 위험 (75% 이상) 3일 누적 횟수
df["high_humidity_risk"] = (
    (df["humidity"] >= 75).astype(int).rolling(3, min_periods=1).sum()
)

# 풍화 위험도
df["weathering_risk"] = (
    df["temp_range"] * 0.4 + df["humidity_std3"] * 0.3 + df["wind_speed"] * 0.3
)

# 곰팡이 발생 위험 (조건 충족 시 1, 미충족 시 0)
df["mold_risk"] = (
    (df["humidity"] >= 75) & (df["ground_temp"] >= 15)
).astype(int)

# 미세먼지 부하량 (PM2.5 기준 3일 이동합)
df["pm_load"] = df["pm25"].rolling(3, min_periods=1).sum()

# 환경 가스 및 위험도 지수
df["acid_risk"] = df["so2"] * 0.6 + df["no2"] * 0.4
df["oxidation_risk"] = df["o3"] * 0.7 + df["pm25"] * 0.3
df["corrosion_risk"] = df["humidity"] * 0.5 + df["so2"] * 0.5

# 최종 결측치 0으로 채우기
df = df.fillna(0)
