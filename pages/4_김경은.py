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
### 📌 군집 기준

문화재를 **연령, 국가유산종목, 시대, 재질, 노출 형태**를 기준으로
비슷한 특성을 가진 문화재끼리 자동으로 분류했습니다.

- 🟦 A그룹 : 비슷한 특징을 가진 문화재 그룹
- 🟩 B그룹 : 비슷한 특징을 가진 문화재 그룹
- 🟨 C그룹 : 비슷한 특징을 가진 문화재 그룹
- 🟥 D그룹 : 비슷한 특징을 가진 문화재 그룹

아래에서 각 군집의 특징과 문화재 목록을 확인할 수 있습니다.
""")

st.subheader("📊 군집별 문화재 개수")

cluster_count = df["군집"].value_counts().sort_index()

st.bar_chart(cluster_count)

st.subheader("📈 군집별 평균 문화재 연령")

cluster_age = df.groupby("군집")["문화재연령"].mean()

st.bar_chart(cluster_age)

st.subheader("📋 군집별 특징")

for group in sorted(df["군집"].unique()):

    temp = df[df["군집"] == group]

    st.markdown(f"### {group}")

    st.write(f"문화재 수 : {len(temp)}개")
    st.write(f"평균 문화재 연령 : {round(temp['문화재연령'].mean(),1)}년")
    st.write(f"대표 재질 : {temp['재질'].mode()[0]}")
    st.write(f"대표 노출 형태 : {temp['노출형태'].mode()[0]}")

st.subheader("🔍 군집별 문화재 검색")

group = st.selectbox(
    "군집 선택",
    sorted(df["군집"].unique())
)

st.dataframe(
    df[df["군집"] == group][
        [
            "문화재명(국문)",
            "문화재연령",
            "국가유산종목",
            "시대그룹",
            "재질",
            "노출형태"
        ]
    ],
    use_container_width=True
)
