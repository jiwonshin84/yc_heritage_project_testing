import os
import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(page_title="문화재 군집분석", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "yc_heritage_feature.csv"
)

df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

features = [
    "문화재연령",
    "국가유산종목",
    "시대그룹",
    "재질",
    "노출형태"
]

data = df[features].copy()

for col in ["국가유산종목", "시대그룹", "재질", "노출형태"]:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col].astype(str))

scaler = StandardScaler()
X = scaler.fit_transform(data)

kmeans = KMeans(
    n_clusters=4,
    random_state=42,
    n_init=10
)

df["Cluster"] = kmeans.fit_predict(X)

cluster_name = {
    0: "A그룹",
    1: "B그룹",
    2: "C그룹",
    3: "D그룹"
}

df["군집"] = df["Cluster"].map(cluster_name)

st.title("🏛 문화재 군집분석")

st.markdown("""
### 📌 군집 기준 안내

문화재의 **가치점수와 시대점수**를 바탕으로 비슷한 특징을 가진 문화재끼리 4개의 그룹으로 분류했습니다.

🟦 **A그룹**
- 가치점수와 시대점수가 모두 높은 문화재
- 역사적 가치가 크고 보존 가치가 높은 문화재가 많이 포함됩니다.

🟩 **B그룹**
- 가치점수와 시대점수가 모두 낮은 문화재
- 비교적 역사성과 가치가 낮은 문화재가 포함됩니다.

🟨 **C그룹**
- 가치점수는 높지만 시대점수는 중간 수준인 문화재
- 보존 가치는 높지만 상대적으로 시대가 오래되지 않은 문화재가 포함됩니다.

🟥 **D그룹**
- 가치점수는 낮지만 시대점수가 중간 수준인 문화재
- 역사성은 어느 정도 있지만 가치점수는 비교적 낮은 문화재가 포함됩니다.
""")
st.subheader("📊 군집별 문화재 개수")

cluster_count = df["군집"].value_counts().sort_index()

st.bar_chart(cluster_count)

st.subheader("📋 군집별 특징")

for group in sorted(df["군집"].unique()):

    temp = df[df["군집"] == group]

    st.markdown(f"### {group}")

    st.write(f"문화재 수 : {len(temp)}개")
    st.write(f"평균 문화재 연령 : {round(temp['문화재연령'].mean(), 1)}년")
    st.write(f"대표 재질 : {temp['재질'].mode()[0]}")
    st.write(f"대표 노출 형태 : {temp['노출형태'].mode()[0]}")

st.subheader("📋 문화재 목록")

group = st.selectbox(
    "군집 선택",
    sorted(df["군집"].unique())
)

result = df[df["군집"] == group][[
    "문화재명(국문)",
    "문화재연령",
    "국가유산종목",
    "시대그룹",
    "재질",
    "노출형태"
]]

st.dataframe(result, use_container_width=True)
