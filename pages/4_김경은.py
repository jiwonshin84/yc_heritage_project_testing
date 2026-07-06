import streamlit as st
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import plotly.express as px

st.set_page_config(page_title="환경 군집분석", layout="wide")

st.title("🤖 영천 환경 군집분석 (AI)")

# ======================
# 데이터 불러오기
# ======================

weather = pd.read_csv("data/processed/[2016_2025] yeongcheon_weather_daily.csv")
air = pd.read_csv("data/processed/[2019_2025] air_quality.csv")

weather["date"] = pd.to_datetime(weather["date"])
air["date"] = pd.to_datetime(air["date"])

df = pd.merge(weather, air, on="date", how="inner")

# 결측치 제거
df = df.dropna()

# ======================
# 군집 분석 변수 선택
# ======================

features = [
    "avg_temperature_c",
    "avg_relative_humidity_pct",
    "daily_precipitation_mm",
    "avg_wind_speed_ms",
    "pm10",
    "pm25",
    "o3"
]

X = df[features]

# 표준화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ======================
# KMeans 군집분석
# ======================

k = 3
kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X_scaled)

# ======================
# PCA 2D 시각화
# ======================

pca = PCA(n_components=2)
components = pca.fit_transform(X_scaled)

df["pc1"] = components[:, 0]
df["pc2"] = components[:, 1]

fig = px.scatter(
    df,
    x="pc1",
    y="pc2",
    color="cluster",
    title="환경 군집 PCA 시각화",
    hover_data=["date"]
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ======================
# 군집별 평균 특징
# ======================

st.subheader("📊 군집별 평균 환경 특징")

cluster_summary = df.groupby("cluster")[features].mean().round(2)

st.dataframe(cluster_summary)

# ======================
# 군집 개수
# ======================

st.subheader("📌 군집별 데이터 개수")

st.bar_chart(df["cluster"].value_counts().sort_index())

# ======================
# 선택 날짜 분석
# ======================

st.divider()

st.subheader("📅 특정 날짜 군집 분석")

selected_date = st.date_input(
    "날짜 선택",
    value=df["date"].max().date()
)

row = df[df["date"].dt.date == selected_date]

if row.empty:
    st.warning("데이터 없음")
    st.stop()

cluster = int(row["cluster"].values[0])

st.success(f"해당 날짜의 군집: Cluster {cluster}")

# 군집 해석
if cluster == 0:
    st.info("🌿 상대적으로 안정적인 환경 (저오염/보통 기후)")
elif cluster == 1:
    st.warning("💧 고습 또는 강수 영향 환경 (곰팡이 위험 증가)")
else:
    st.error("🏭 대기오염 영향이 큰 환경 (문화재 오염 위험)")
