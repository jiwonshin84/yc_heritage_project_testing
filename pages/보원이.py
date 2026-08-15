# ============================================================
# 7. 파생변수 생성 (보완본)
# ============================================================

# 일교차
df["temp_range"] = df["temp_max"] - df["temp_min"]

# 습도 변동성 (첫 행 NaN 발생 대비 fillna 처리)
df["humidity_std3"] = (
    df["humidity"].rolling(3, min_periods=1).std().fillna(0)
)

# 7일 누적 강수량
df["rainfall_7d"] = df["rainfall"].rolling(7, min_periods=1).sum()

# 고습도 위험 지속일수
df["high_humidity_risk"] = (
    (df["humidity"] >= 75).astype(int).rolling(3, min_periods=1).sum()
)

# 풍화 위험도 (가중치 적용)
df["weathering_risk"] = (
    df["temp_range"] * 0.4 + df["humidity_std3"] * 0.3 + df["wind_speed"] * 0.3
)

# 곰팡이 발생 위험 조건 (1 또는 0)
df["mold_risk"] = (
    (df["humidity"] >= 75) & (df["ground_temp"] >= 15)
).astype(int)

# 미세먼지 부하량 (PM2.5 기준 3일 이동합 - 중복 합산 방지)
df["pm_load"] = df["pm25"].rolling(3, min_periods=1).sum()

# 가스 및 환경 위험도 (단위 차이에 유의하여 활용)
df["acid_risk"] = df["so2"] * 0.6 + df["no2"] * 0.4
df["oxidation_risk"] = df["o3"] * 0.7 + df["pm25"] * 0.3
df["corrosion_risk"] = df["humidity"] * 0.5 + df["so2"] * 0.5

# 결측치 최종 0으로 채우기
df = df.fillna(0)
